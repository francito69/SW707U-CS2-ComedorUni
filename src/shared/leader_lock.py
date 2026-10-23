"""
Lock distribuido simple sobre Redis para jobs periódicos.

Por qué existe: con --workers > 1, uvicorn levanta varios procesos
independientes, y cada uno ejecuta su propia copia de inactivity_worker()
y active_service_worker() (arrancan en el lifespan de main.py, que corre
por proceso). Sin esto, un ciclo de "llamar siguiente turno" se ejecutaría
N veces en paralelo — turnos llamados/cancelados por duplicado y eventos
repetidos hacia RabbitMQ. El lock asegura que un solo worker gane cada
ciclo; los demás lo ven ocupado y se saltan esa vuelta.
"""
import os

import redis.asyncio as aioredis

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


async def try_acquire(name: str, ttl_seconds: int) -> bool:
    """
    True solo para el worker que gana el lock `name` en este ciclo. El TTL
    debe ser un poco menor al intervalo del job, para que el lock ya haya
    expirado (y cualquier worker pueda tomarlo de nuevo) en el siguiente
    ciclo, incluso si el worker que lo tomó antes murió sin liberarlo.
    """
    got = await _get_redis().set(f"lock:{name}", "1", nx=True, ex=ttl_seconds)
    return bool(got)
