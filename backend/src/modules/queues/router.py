from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ...shared.db import db_conn
from ...shared.rabbitmq import publish
from ..auth.redis_store import get_session
from ..reassignment.service import llamar_siguiente
from .manager import manager
from .schemas import (
    ConfirmRequest, ConfirmResponse,
    JoinQueueRequest, JoinQueueResponse,
    TurnoStatusResponse,
)
from .service import (
    calcular_turno_asignado,
    cancelar_turno,
    confirmar_turno,
    get_raciones_max_turno_dia,
    get_turno_activo_por_codigo,
    crear_turno,
    get_estudiante_id,
    get_turno_dia_id,
    get_turno_actual,
    get_turno_by_codigo,
    get_turno_dia_activo,
    get_turno_dia_activo_por_tipo,
    get_turnos_dia_activos,
    get_turno_hoy_por_codigo,
    posicion_en_cola,
    raciones_usadas,
    save_push_token,
    turno_existente,
)

router = APIRouter(prefix="/queue", tags=["queue"])


def _require_session(sid: str) -> dict:
    session = get_session(sid)
    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    return session


def _now() -> str:
    return datetime.now().isoformat()


# ── Push token ───────────────────────────────────────────────────────────────

class PushTokenRequest(BaseModel):
    sid: str
    push_token: str

@router.get("/active-service")
def active_service():
    """Retorna todos los turnos activos en este momento (público, sin autenticación)."""
    turnos = get_turnos_dia_activos()
    if not turnos:
        return {"activo": False, "turnos": []}
    return {
        "activo": True,
        "turnos": [
            {
                "tipo":        t["tipo"],
                "hora_inicio": str(t["hora_inicio"]),
                "hora_cierre": str(t["hora_cierre"]),
            }
            for t in turnos
        ],
    }


@router.post("/register-push-token")
def register_push_token(data: PushTokenRequest = Body(...)):
    session = _require_session(data.sid)
    save_push_token(session["codigo"], data.push_token)
    return {"status": "ok"}


# ── Cola ─────────────────────────────────────────────────────────────────────

@router.post("/join", response_model=JoinQueueResponse)
async def join_queue(data: JoinQueueRequest = Body(...)):
    session  = _require_session(data.sid)
    codigo   = session["codigo"]

    turno_dia = get_turno_dia_activo_por_tipo(data.tipo)
    if not turno_dia:
        raise HTTPException(status_code=400, detail=f"No hay turno '{data.tipo}' activo en este horario")

    estudiante_id = get_estudiante_id(codigo)
    if not estudiante_id:
        raise HTTPException(status_code=404, detail="Estudiante no registrado en la base de datos")

    turno_dia_id = get_turno_dia_id(turno_dia["config_id"])
    if not turno_dia_id:
        raise HTTPException(status_code=503, detail="El turno de hoy aún no fue habilitado por el administrador")

    existente = turno_existente(estudiante_id, turno_dia_id)
    if existente:
        raise HTTPException(
            status_code=409,
            detail=f"Ya tienes el turno #{existente['numero_turno']} ({existente['estado']})"
        )

    restantes = turno_dia["raciones_max"] - raciones_usadas(turno_dia_id)
    if restantes <= 0:
        raise HTTPException(status_code=400, detail="Se agotaron las raciones para este turno")


    numero = crear_turno(estudiante_id, turno_dia_id)
    posicion = posicion_en_cola(turno_dia_id, numero)

    # M5: registrar encolamiento
    await publish("turno.encolado", {
        "evento":        "turno.encolado",
        "codigo":        codigo,
        "estudiante_id": estudiante_id,
        "turno_dia_id":  turno_dia_id,
        "numero_turno":  numero,
        "tipo_comida":   turno_dia["tipo"],
        "timestamp":     _now(),
    })

    return JoinQueueResponse(
        numero_turno=numero,
        tipo=turno_dia["tipo"],
        posicion=posicion,
        raciones_restantes=restantes - 1,
        mensaje=f"Eres el número {numero} en la cola de {turno_dia['tipo'].lower()}",
    )


@router.get("/status", response_model=TurnoStatusResponse)
def queue_status(sid: str):
    session = _require_session(sid)
    codigo  = session["codigo"]

    turno = get_turno_hoy_por_codigo(codigo)
    if not turno:
        raise HTTPException(status_code=404, detail="No tienes turno activo hoy")

    turno_dia_id  = turno["turno_dia_id"]
    raciones_max  = get_raciones_max_turno_dia(turno_dia_id)
    turno_asignado = (
        calcular_turno_asignado(turno["numero_turno"], raciones_max)
        if turno["estado"] == "ATENDIDO" else None
    )
    return TurnoStatusResponse(
        numero_turno=turno["numero_turno"],
        estado=turno["estado"],
        tipo=turno["tipo"],
        posicion=posicion_en_cola(turno_dia_id, turno["numero_turno"]),
        turno_actual=get_turno_actual(turno_dia_id),
        turno_asignado=turno_asignado,
        llamado_at=turno["llamado_at"],
    )


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_presence(data: ConfirmRequest = Body(...)):
    session  = _require_session(data.sid)
    codigo   = session["codigo"]

    turno = get_turno_activo_por_codigo(codigo)
    if not turno:
        raise HTTPException(status_code=404, detail="No tienes turno activo")
    if turno["estado"] in ("ATENDIDO", "CANCELADO"):
        raise HTTPException(status_code=400, detail=f"Tu turno está {turno['estado']}")

    turno_dia_id = turno["turno_dia_id"]
    tipo_comida  = turno["tipo"]
    nuevo_estado = confirmar_turno(turno["id"], turno["estado"])

    if nuevo_estado == "ATENDIDO":
        estudiante_id = get_estudiante_id(codigo)
        # M5: registrar asistencia
        await publish("turno.atendido", {
            "evento":        "turno.atendido",
            "codigo":        codigo,
            "estudiante_id": estudiante_id,
            "turno_dia_id":  turno_dia_id,
            "numero_turno":  turno["numero_turno"],
            "tipo_comida":   tipo_comida,
            "timestamp":     _now(),
        })
        # Llamar al siguiente turno (grupo completo)
        for sig in llamar_siguiente(turno_dia_id):
            if manager.is_connected(sig["codigo"]):
                await manager.send(sig["codigo"], {
                    "type":    "llamado",
                    "turno":   sig["numero_turno"],
                    "mensaje": "¡Es tu turno! Confirma en los próximos 3 minutos.",
                })
            await publish("turno.llamado", {
                "evento":       "turno.llamado",
                "codigo":       sig["codigo"],
                "numero_turno": sig["numero_turno"],
                "tipo_comida":  tipo_comida,
                "push_token":   sig["push_token"],
                "turno_dia_id": turno_dia_id,
                "timestamp":    _now(),
            })

    raciones_max  = get_raciones_max_turno_dia(turno_dia_id)
    turno_asignado = (
        calcular_turno_asignado(turno["numero_turno"], raciones_max)
        if nuevo_estado == "ATENDIDO" else None
    )
    mensajes = {
        "ATENDIDO":  "Turno confirmado. Dirígete al comedor.",
        "ESPERANDO": "Presencia confirmada. Sigue esperando tu turno.",
    }
    return ConfirmResponse(
        estado=nuevo_estado,
        mensaje=mensajes[nuevo_estado],
        turno_asignado=turno_asignado,
    )


@router.post("/leave")
def leave_queue(data: ConfirmRequest = Body(...)):
    session = _require_session(data.sid)
    codigo  = session["codigo"]

    turno = get_turno_activo_por_codigo(codigo)
    if not turno:
        return {"status": "ok", "mensaje": "No había turno activo"}
    if turno["estado"] in ("ATENDIDO", "CANCELADO"):
        return {"status": "ok", "mensaje": "Turno ya finalizado"}

    cancelar_turno(turno["id"])
    return {"status": "ok", "mensaje": "Saliste de la cola"}


# ── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/ws/{sid}")
async def queue_websocket(ws: WebSocket, sid: str):
    session = get_session(sid)
    if not session:
        await ws.close(code=4001)
        return

    codigo = session["codigo"]
    await manager.connect(codigo, ws)

    try:
        while True:
            msg = await ws.receive_json()

            if msg.get("type") == "ping":
                with db_conn() as conn:
                    turno = get_turno_activo_por_codigo(codigo, conn)
                    if turno and turno["estado"] in ("ESPERANDO", "LLAMADO"):
                        confirmar_turno(turno["id"], "ESPERANDO", conn)
                await manager.send(codigo, {"type": "pong"})

            elif msg.get("type") == "confirmar":
                with db_conn() as conn:
                    turno = get_turno_activo_por_codigo(codigo, conn)
                    if not turno or turno["estado"] != "LLAMADO":
                        continue
                    turno_dia_id  = turno["turno_dia_id"]
                    tipo_comida   = turno["tipo"]
                    confirmar_turno(turno["id"], "LLAMADO", conn)
                    estudiante_id = get_estudiante_id(codigo, conn)
                    siguientes    = llamar_siguiente(turno_dia_id, conn)

                await publish("turno.atendido", {
                    "evento":        "turno.atendido",
                    "codigo":        codigo,
                    "estudiante_id": estudiante_id,
                    "turno_dia_id":  turno_dia_id,
                    "numero_turno":  turno["numero_turno"],
                    "tipo_comida":   tipo_comida,
                    "timestamp":     _now(),
                })
                await manager.send(codigo, {
                    "type":    "estado",
                    "estado":  "ATENDIDO",
                    "mensaje": "Turno confirmado. Dirígete al comedor.",
                })
                for sig in siguientes:
                    if manager.is_connected(sig["codigo"]):
                        await manager.send(sig["codigo"], {
                            "type":    "llamado",
                            "turno":   sig["numero_turno"],
                            "mensaje": "¡Es tu turno! Confirma en los próximos 3 minutos.",
                        })
                    await publish("turno.llamado", {
                        "evento":       "turno.llamado",
                        "codigo":       sig["codigo"],
                        "numero_turno": sig["numero_turno"],
                        "tipo_comida":  tipo_comida,
                        "push_token":   sig["push_token"],
                        "turno_dia_id": turno_dia_id,
                        "timestamp":    _now(),
                    })

    except WebSocketDisconnect:
        manager.disconnect(codigo)
