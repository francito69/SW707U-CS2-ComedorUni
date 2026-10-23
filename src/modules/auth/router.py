import logging
import uuid

from fastapi import APIRouter, Body, HTTPException, Query, WebSocket, WebSocketDisconnect

from ...shared.errores import SesionInvalida
from ...shared.validacion import UUID4_PATTERN

from .biometric import compare_faces
from .estudiante_repo import upsert_estudiante
from .redis_store import create_session, delete_session, get_session, takeover_session
from .session_manager import session_manager
from .schemas import (
    BiometricVerifyRequest,
    BiometricVerifyResponse,
    LogoutRequest,
    ParseDataRequest,
    ParseDataResponse,
    TakeoverRequest,
)
from .service import parse_student_data

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/parse-data", response_model=ParseDataResponse)
def parse_data(data: ParseDataRequest = Body(...)):
    result = parse_student_data(data.home_html, data.cursos_html, data.datos_html)

    # Persiste en DB — obligatorio: sin registro en estudiantes el encolamiento falla por FK
    upsert_estudiante(
        codigo=result["codigo"],
        nombres=result["nombres"],
        apellido_paterno=result["apellido_paterno"],
        apellido_materno=result["apellido_materno"],
        email=result["email"],
    )
    log.info("Estudiante %s guardado en la base", result["codigo"])

    sid = str(uuid.uuid4())
    old_sid = create_session(
        sid=sid,
        codigo=result["codigo"],
        email=result["email"],
        nombre=result["nombre"],
        creditos=result["creditos_llevados"],
        foto_base64=result["foto_base64"],   # foto vigente de ORCE, no se persiste en DB
        device_id=data.device_id,
    )

    return ParseDataResponse(
        sid=sid,
        nombre=result["nombre"],
        codigo=result["codigo"],
        email=result["email"],
        creditos_llevados=result["creditos_llevados"],
        session_conflict=bool(old_sid),   # hay sesión activa en otro dispositivo
    )


@router.post("/session/takeover")
async def session_takeover(data: TakeoverRequest = Body(...)):
    """
    El dispositivo actual (data.sid) se queda como la sesión activa y expulsa a la
    anterior en tiempo real (WebSocket). Se usa cuando el usuario elige "continuar aquí".
    """
    if not get_session(data.sid):
        raise SesionInvalida()
    old_sid = takeover_session(data.sid)
    if old_sid:
        await session_manager.revoke(old_sid)
    return {"status": "ok"}


@router.websocket("/session/ws/{sid}")
async def session_ws(ws: WebSocket, sid: str):
    """
    Conexión permanente de sesión (una por dispositivo). Mientras el usuario esté
    logueado, el dispositivo mantiene este socket; si otro dispositivo toma la
    sesión, aquí recibe `session_revoked` y se cierra.
    """
    if not get_session(sid):
        await ws.close(code=4001)
        return
    await session_manager.connect(sid, ws)
    try:
        while True:
            await ws.receive_text()   # mantiene viva la conexión; el contenido se ignora
    except WebSocketDisconnect:
        session_manager.disconnect(sid)
    except Exception:
        session_manager.disconnect(sid)


@router.post("/verify-biometric", response_model=BiometricVerifyResponse)
def verify_biometric(data: BiometricVerifyRequest = Body(...)):
    session = get_session(data.sid)
    if not session:
        raise SesionInvalida()

    foto_ref = session.get("foto_base64")
    if not foto_ref:
        raise HTTPException(status_code=404, detail="No hay foto de referencia en sesión")

    try:
        verified, distance = compare_faces(foto_ref, data.photo_base64)
    except Exception:
        # Foto corrupta o fallo del modelo: se registra aquí (frontera) y el
        # cliente recibe un mensaje sin detalles internos.
        log.exception("Falló la comparación biométrica")
        raise HTTPException(status_code=500, detail="Error al procesar la comparación de rostros")

    return BiometricVerifyResponse(
        verified=verified,
        distance=distance,
        message="Identidad verificada correctamente" if verified else "La foto no coincide con el registro",
    )


@router.get("/me")
def get_me(sid: str = Query(pattern=UUID4_PATTERN)):
    """Valida el sid y devuelve los datos de sesión. Usado al reabrir la app."""
    session = get_session(sid)
    if not session:
        raise SesionInvalida("Sesión expirada")
    return {
        "sid":               sid,
        "codigo":            session["codigo"],
        "nombre":            session["nombre"],
        "email":             session["email"],
        "creditos_llevados": session["creditos"],
    }


@router.post("/logout")
def logout(data: LogoutRequest = Body(...)):
    if not get_session(data.sid):
        raise HTTPException(status_code=400, detail="Sesión no encontrada o ya expirada")
    delete_session(data.sid)
    return {"status": "success", "message": "Sesión cerrada correctamente"}
