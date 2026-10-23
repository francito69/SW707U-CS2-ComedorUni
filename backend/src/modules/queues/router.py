from datetime import datetime

from fastapi import APIRouter, Body, Query, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from ...shared.db import db_conn
from ...shared.errores import (
    EstudianteNoRegistrado,
    SesionInvalida,
    SinRaciones,
    SinTurnoActivo,
    TurnoDuplicado,
    TurnoFinalizado,
    TurnoNoActivo,
    TurnoNoHabilitado,
)
from ...shared.rabbitmq import publish
from ...shared.validacion import UUID4_PATTERN
from ...shared.ws_bus import publish_to_session
from ..auth.redis_store import get_session
from ..reassignment.service import llamar_siguiente
from .manager import active_service_manager, manager
from .schemas import (
    ConfirmRequest, ConfirmResponse,
    JoinQueueRequest, JoinQueueResponse,
    PushTokenRequest,
    TurnoStatusResponse,
)
from .service import (
    active_service_payload,
    calcular_turno_asignado,
    cancelar_turno,
    confirmar_turno,
    get_raciones_max_turno_dia,
    get_turno_activo_por_codigo,
    crear_turno,
    get_estudiante_id,
    get_turno_dia_id,
    get_turno_actual,
    get_turno_dia_activo_por_tipo,
    get_turno_hoy_por_codigo,
    posicion_en_cola,
    raciones_usadas,
    save_push_token,
    turno_existente,
)

router = APIRouter(prefix="/queue", tags=["queue"])

MENSAJE_LLAMADO = "¡Es tu turno! Confirma en los próximos 3 minutos."


def _require_session(sid: str) -> dict:
    session = get_session(sid)
    if not session:
        raise SesionInvalida()
    return session


def _now() -> str:
    return datetime.now().isoformat()


async def _avisar_llamados(siguientes: list[dict], tipo_comida: str, turno_dia_id: int) -> None:
    # Se publica al bus en vez de mandar directo al manager local: con varios
    # workers de uvicorn, ese estudiante puede estar conectado a OTRO proceso.
    for sig in siguientes:
        await publish_to_session(sig["codigo"], {
            "type": "llamado", "turno": sig["numero_turno"], "mensaje": MENSAJE_LLAMADO,
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


# ── Push token ───────────────────────────────────────────────────────────────

@router.get("/active-service")
def active_service():
    """Retorna todos los turnos activos en este momento (público, sin autenticación)."""
    return active_service_payload()


@router.post("/register-push-token")
def register_push_token(data: PushTokenRequest = Body(...)):
    session = _require_session(data.sid)
    save_push_token(session["codigo"], data.push_token)
    return {"status": "ok"}


# ── Cola ─────────────────────────────────────────────────────────────────────

def _reservar_turno(sid: str, tipo: str) -> dict:
    """Parte síncrona de /join (toda la base de datos). Corre en el threadpool."""
    codigo = _require_session(sid)["codigo"]

    turno_dia = get_turno_dia_activo_por_tipo(tipo)
    if not turno_dia:
        raise TurnoNoActivo(f"No hay turno '{tipo}' activo en este horario")

    estudiante_id = get_estudiante_id(codigo)
    if not estudiante_id:
        raise EstudianteNoRegistrado()

    turno_dia_id = get_turno_dia_id(turno_dia["config_id"])
    if not turno_dia_id:
        raise TurnoNoHabilitado()

    # Atajos sin candado para responder rápido en los casos obvios. La regla
    # autoritativa se vuelve a verificar dentro de crear_turno, bajo FOR UPDATE.
    existente = turno_existente(estudiante_id, turno_dia_id)
    if existente:
        raise TurnoDuplicado(f"Ya tienes el turno #{existente['numero_turno']} ({existente['estado']})")
    if raciones_usadas(turno_dia_id) >= turno_dia["raciones_max"]:
        raise SinRaciones()

    creado = crear_turno(estudiante_id, turno_dia_id, turno_dia["raciones_max"])
    return {
        "codigo": codigo,
        "estudiante_id": estudiante_id,
        "turno_dia_id": turno_dia_id,
        "tipo": turno_dia["tipo"],
        "numero": creado.numero,
        "raciones_restantes": creado.raciones_restantes,
        "posicion": posicion_en_cola(turno_dia_id, creado.numero),
    }


@router.post("/join", response_model=JoinQueueResponse)
async def join_queue(data: JoinQueueRequest = Body(...)):
    # crear_turno puede esperar el candado de la base: en el threadpool esa
    # espera no congela el event loop (WebSockets y otros requests siguen).
    r = await run_in_threadpool(_reservar_turno, data.sid, data.tipo)

    # M5: registrar encolamiento
    await publish("turno.encolado", {
        "evento":        "turno.encolado",
        "codigo":        r["codigo"],
        "estudiante_id": r["estudiante_id"],
        "turno_dia_id":  r["turno_dia_id"],
        "numero_turno":  r["numero"],
        "tipo_comida":   r["tipo"],
        "timestamp":     _now(),
    })

    return JoinQueueResponse(
        numero_turno=r["numero"],
        tipo=r["tipo"],
        posicion=r["posicion"],
        raciones_restantes=r["raciones_restantes"],
        mensaje=f"Eres el número {r['numero']} en la cola de {r['tipo'].lower()}",
    )


@router.get("/status", response_model=TurnoStatusResponse)
def queue_status(sid: str = Query(pattern=UUID4_PATTERN)):
    codigo = _require_session(sid)["codigo"]

    turno = get_turno_hoy_por_codigo(codigo)
    if not turno:
        raise SinTurnoActivo("No tienes turno activo hoy")

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


def _confirmar_presencia(sid: str) -> dict:
    """Parte síncrona de /confirm. Corre en el threadpool."""
    codigo = _require_session(sid)["codigo"]

    turno = get_turno_activo_por_codigo(codigo)
    if not turno:
        raise SinTurnoActivo("No tienes turno activo")
    if turno["estado"] in ("ATENDIDO", "CANCELADO"):
        raise TurnoFinalizado(f"Tu turno está {turno['estado']}")

    turno_dia_id = turno["turno_dia_id"]
    nuevo_estado = confirmar_turno(turno["id"], turno["estado"])

    estudiante_id, siguientes, turno_asignado = None, [], None
    if nuevo_estado == "ATENDIDO":
        estudiante_id = get_estudiante_id(codigo)
        siguientes = llamar_siguiente(turno_dia_id)
        turno_asignado = calcular_turno_asignado(
            turno["numero_turno"], get_raciones_max_turno_dia(turno_dia_id)
        )
    return {
        "codigo": codigo, "turno": turno, "nuevo_estado": nuevo_estado,
        "estudiante_id": estudiante_id, "siguientes": siguientes,
        "turno_asignado": turno_asignado,
    }


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_presence(data: ConfirmRequest = Body(...)):
    r = await run_in_threadpool(_confirmar_presencia, data.sid)
    turno = r["turno"]

    if r["nuevo_estado"] == "ATENDIDO":
        # M5: registrar asistencia
        await publish("turno.atendido", {
            "evento":        "turno.atendido",
            "codigo":        r["codigo"],
            "estudiante_id": r["estudiante_id"],
            "turno_dia_id":  turno["turno_dia_id"],
            "numero_turno":  turno["numero_turno"],
            "tipo_comida":   turno["tipo"],
            "timestamp":     _now(),
        })
        await _avisar_llamados(r["siguientes"], turno["tipo"], turno["turno_dia_id"])

    mensajes = {
        "ATENDIDO":  "Turno confirmado. Dirígete al comedor.",
        "ESPERANDO": "Presencia confirmada. Sigue esperando tu turno.",
    }
    return ConfirmResponse(
        estado=r["nuevo_estado"],
        mensaje=mensajes[r["nuevo_estado"]],
        turno_asignado=r["turno_asignado"],
    )


@router.post("/leave")
def leave_queue(data: ConfirmRequest = Body(...)):
    codigo = _require_session(data.sid)["codigo"]

    turno = get_turno_activo_por_codigo(codigo)
    if not turno:
        return {"status": "ok", "mensaje": "No había turno activo"}
    if turno["estado"] in ("ATENDIDO", "CANCELADO"):
        return {"status": "ok", "mensaje": "Turno ya finalizado"}

    cancelar_turno(turno["id"])
    return {"status": "ok", "mensaje": "Saliste de la cola"}


# ── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/ws/active-service")
async def active_service_ws(ws: WebSocket):
    """
    Conexión pública (sin sesión) al estado de turnos activos. Al conectar
    recibe el snapshot actual; luego recibe un mensaje nuevo cada vez que el
    servicio activo cambia (lo detecta active_service_worker en worker.py),
    para que la pantalla de inicio se actualice sin que el usuario reingrese.
    """
    await active_service_manager.connect(ws)
    try:
        await ws.send_json(await run_in_threadpool(active_service_payload))
        while True:
            await ws.receive_text()   # mantiene viva la conexión; el contenido se ignora
    except WebSocketDisconnect:
        active_service_manager.disconnect(ws)
    except Exception:
        active_service_manager.disconnect(ws)


def _registrar_ping(codigo: str) -> None:
    with db_conn() as conn:
        turno = get_turno_activo_por_codigo(codigo, conn)
        if turno and turno["estado"] in ("ESPERANDO", "LLAMADO"):
            confirmar_turno(turno["id"], "ESPERANDO", conn)


def _confirmar_por_ws(codigo: str) -> dict | None:
    with db_conn() as conn:
        turno = get_turno_activo_por_codigo(codigo, conn)
        if not turno or turno["estado"] != "LLAMADO":
            return None
        confirmar_turno(turno["id"], "LLAMADO", conn)
        return {
            "turno": turno,
            "estudiante_id": get_estudiante_id(codigo, conn),
            "siguientes": llamar_siguiente(turno["turno_dia_id"], conn),
        }


@router.websocket("/ws/{sid}")
async def queue_websocket(ws: WebSocket, sid: str):
    session = await run_in_threadpool(get_session, sid)
    if not session:
        await ws.close(code=4001)
        return

    codigo = session["codigo"]
    await manager.connect(codigo, ws)

    try:
        while True:
            msg = await ws.receive_json()

            if msg.get("type") == "ping":
                await run_in_threadpool(_registrar_ping, codigo)
                await manager.send(codigo, {"type": "pong"})

            elif msg.get("type") == "confirmar":
                r = await run_in_threadpool(_confirmar_por_ws, codigo)
                if r is None:
                    continue
                turno = r["turno"]
                await publish("turno.atendido", {
                    "evento":        "turno.atendido",
                    "codigo":        codigo,
                    "estudiante_id": r["estudiante_id"],
                    "turno_dia_id":  turno["turno_dia_id"],
                    "numero_turno":  turno["numero_turno"],
                    "tipo_comida":   turno["tipo"],
                    "timestamp":     _now(),
                })
                await publish_to_session(codigo, {
                    "type":    "estado",
                    "estado":  "ATENDIDO",
                    "mensaje": "Turno confirmado. Dirígete al comedor.",
                })
                await _avisar_llamados(r["siguientes"], turno["tipo"], turno["turno_dia_id"])

    except WebSocketDisconnect:
        manager.disconnect(codigo)
