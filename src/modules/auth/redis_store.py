import json
import os

import redis

SESSION_TTL = 8 * 3600  # 8 horas

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True,
        )
    return _client


def create_session(sid: str, codigo: str, email: str, nombre: str, creditos: int,
                   foto_base64: str = "", device_id: str = "") -> str | None:
    """
    Crea la sesión del dispositivo. NO expulsa la sesión previa automáticamente:
    si ya hay otra sesión activa del mismo código en OTRO dispositivo, se marca
    conflicto y la resolución (mantener la vieja o quedarse con la nueva) la decide
    el usuario vía /session/takeover.

    Retorna el `sid` de la sesión previa en conflicto (otro dispositivo), o None.
    """
    r = get_redis()

    old_sid = r.get(f"user_session:{codigo}")
    conflicto = False
    if old_sid and old_sid != sid and r.exists(f"session:{old_sid}"):
        raw_old = r.get(f"session:{old_sid}")
        old_device = json.loads(raw_old).get("device_id", "") if raw_old else ""
        # Solo es conflicto si la sesión previa es de OTRO dispositivo.
        conflicto = not device_id or old_device != device_id

    payload = json.dumps({
        "codigo": codigo, "email": email, "nombre": nombre,
        "creditos": creditos, "foto_base64": foto_base64, "device_id": device_id,
    })
    r.setex(f"session:{sid}", SESSION_TTL, payload)

    if not conflicto:
        # Sin conflicto (o mismo dispositivo): esta sesión pasa a ser la activa
        # y se expulsa cualquier sesión previa del mismo dispositivo.
        if old_sid and old_sid != sid:
            r.delete(f"session:{old_sid}")
        r.setex(f"user_session:{codigo}", SESSION_TTL, sid)
        return None

    # Hay conflicto: dejamos la sesión vieja intacta hasta que el usuario decida.
    return old_sid


def takeover_session(sid: str) -> str | None:
    """
    El `sid` dado se queda como la sesión activa y expulsa a la anterior (otro
    dispositivo). Retorna el `sid` expulsado, o None si no había otro.
    """
    r = get_redis()
    raw = r.get(f"session:{sid}")
    if not raw:
        return None
    codigo = json.loads(raw).get("codigo")
    old_sid = r.get(f"user_session:{codigo}")
    r.setex(f"user_session:{codigo}", SESSION_TTL, sid)
    if old_sid and old_sid != sid:
        r.delete(f"session:{old_sid}")
        return old_sid
    return None


def get_session(sid: str) -> dict | None:
    raw = get_redis().get(f"session:{sid}")
    return json.loads(raw) if raw else None


def delete_session(sid: str) -> None:
    r = get_redis()
    raw = r.get(f"session:{sid}")
    if raw:
        codigo = json.loads(raw).get("codigo")
        # Solo limpiar el puntero si apunta a ESTA sesión (no pisar la de otro dispositivo).
        if codigo and r.get(f"user_session:{codigo}") == sid:
            r.delete(f"user_session:{codigo}")
    r.delete(f"session:{sid}")
