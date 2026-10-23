"""
Bus de mensajes entre procesos para los WebSockets de /queue.

Por qué existe: con --workers > 1, uvicorn levanta varios procesos
independientes. Cada uno tiene su PROPIO QueueConnectionManager y
ActiveServiceConnectionManager en memoria (ver queues/manager.py) — un
estudiante conectado al worker A es invisible para el worker B. Si el
turno de ese estudiante se llama desde un endpoint que atendió el worker
B (o desde inactivity_worker corriendo en B), un manager.send() local en
B nunca llegaría al socket que vive en A: el mensaje se perdería en
silencio.

La solución: en vez de enviar directo al manager local, se publica el
mensaje a un canal de Redis. TODOS los workers están suscritos a ese
canal (start_ws_bus_listener corre en cada uno vía el lifespan de
main.py); cada uno recibe la publicación y solo la entrega si tiene esa
conexión conectada localmente. Así no importa en qué worker esté el
estudiante — el mensaje siempre le llega.
"""
import asyncio
import json
import logging
import os

import redis.asyncio as aioredis

log = logging.getLogger(__name__)

CHANNEL_SESSION   = "ws:session"     # mensajes dirigidos a un `codigo` de estudiante
CHANNEL_BROADCAST = "ws:broadcast"   # mensajes para todos (estado de turnos activos)

_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True,
        )
    return _redis


async def publish_to_session(codigo: str, message: dict) -> None:
    """
    Manda `message` al estudiante `codigo`, esté conectado al worker que esté.
    Es un aviso en tiempo real, no la fuente de verdad: si Redis no responde se
    registra y se sigue (el estado ya quedó en Postgres y la app lo consulta
    con /queue/status), en vez de hacer fallar una operación ya confirmada.
    """
    try:
        await _get_redis().publish(CHANNEL_SESSION, json.dumps({"codigo": codigo, "message": message}))
    except Exception as e:
        log.warning("No se pudo publicar aviso a %s por el bus de WebSockets: %s", codigo, e)


async def publish_broadcast(message: dict) -> None:
    """Manda `message` a todos los conectados a /queue/ws/active-service en todos los workers."""
    try:
        await _get_redis().publish(CHANNEL_BROADCAST, json.dumps(message))
    except Exception as e:
        log.warning("No se pudo publicar el broadcast de turnos activos: %s", e)


async def start_ws_bus_listener(manager, active_service_manager) -> None:
    """
    Tarea de fondo — una instancia por worker. Escucha los canales y entrega
    cada mensaje solo a las conexiones que este proceso tiene localmente.
    Se reconecta solo si la suscripción a Redis se cae.
    """
    while True:
        try:
            pubsub = _get_redis().pubsub()
            await pubsub.subscribe(CHANNEL_SESSION, CHANNEL_BROADCAST)
            log.info("Bus de WebSockets suscrito a Redis pub/sub")
            async for raw in pubsub.listen():
                if raw.get("type") != "message":
                    continue
                try:
                    channel = raw["channel"]
                    data = json.loads(raw["data"])
                except Exception:
                    continue

                if channel == CHANNEL_SESSION:
                    codigo = data.get("codigo")
                    if codigo and manager.is_connected(codigo):
                        await manager.send(codigo, data["message"])
                elif channel == CHANNEL_BROADCAST:
                    await active_service_manager.broadcast(data)
        except Exception as e:
            log.warning("Listener del bus de WebSockets caído, reintento en 3s: %s", e)
            await asyncio.sleep(3)
