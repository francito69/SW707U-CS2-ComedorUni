import asyncio
import json
import logging
import os
from typing import Callable

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode

log = logging.getLogger(__name__)

RABBITMQ_URL  = (
    f"amqp://{os.getenv('RABBITMQ_USER', 'guest')}:"
    f"{os.getenv('RABBITMQ_PASS', 'guest')}@"
    f"{os.getenv('RABBITMQ_HOST', 'localhost')}:"
    f"{os.getenv('RABBITMQ_PORT', '5672')}/"
)
EXCHANGE_NAME = "comedor"
PUBLISH_TIMEOUT_SECONDS = float(os.getenv("RABBITMQ_PUBLISH_TIMEOUT", "3"))

_connection: aio_pika.RobustConnection | None = None
_publish_channel: aio_pika.abc.AbstractChannel | None = None
_publish_exchange: aio_pika.abc.AbstractExchange | None = None


async def get_connection() -> aio_pika.RobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
    return _connection


async def _exchange_para_publicar() -> aio_pika.abc.AbstractExchange:
    global _publish_channel, _publish_exchange
    if _publish_channel is None or _publish_channel.is_closed:
        conn = await get_connection()
        _publish_channel = await conn.channel()
        _publish_exchange = await _publish_channel.declare_exchange(
            EXCHANGE_NAME, ExchangeType.TOPIC, durable=True
        )
    return _publish_exchange


async def _publicar(routing_key: str, payload: dict) -> None:
    exchange = await _exchange_para_publicar()
    await exchange.publish(
        Message(body=json.dumps(payload).encode(), delivery_mode=DeliveryMode.PERSISTENT),
        routing_key=routing_key,
    )


async def publish(routing_key: str, payload: dict) -> None:
    """
    Publica un evento de dominio. Es best-effort a propósito: el turno ya quedó
    en Postgres, así que si RabbitMQ está caído o lento se registra y se sigue
    (degradación elegante) en vez de hacer fallar o colgar el request.
    """
    global _publish_channel
    try:
        await asyncio.wait_for(_publicar(routing_key, payload), timeout=PUBLISH_TIMEOUT_SECONDS)
    except Exception as e:
        _publish_channel = None  # el próximo publish reabre el canal
        log.warning("Evento '%s' no publicado en RabbitMQ: %s", routing_key, e or type(e).__name__)


async def start_consumer(
    queue_name:   str,
    routing_keys: list[str],
    handler:      Callable,
) -> None:
    conn    = await get_connection()
    channel = await conn.channel()
    await channel.set_qos(prefetch_count=10)
    exchange = await channel.declare_exchange(EXCHANGE_NAME, ExchangeType.TOPIC, durable=True)
    queue    = await channel.declare_queue(queue_name, durable=True)
    for key in routing_keys:
        await queue.bind(exchange, key)
    await queue.consume(handler)
    log.info("Cola '%s' escuchando %s", queue_name, routing_keys)
