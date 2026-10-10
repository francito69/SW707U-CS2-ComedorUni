import json
import os
from typing import Callable

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode

RABBITMQ_URL  = (
    f"amqp://{os.getenv('RABBITMQ_USER', 'guest')}:"
    f"{os.getenv('RABBITMQ_PASS', 'guest')}@"
    f"{os.getenv('RABBITMQ_HOST', 'localhost')}:"
    f"{os.getenv('RABBITMQ_PORT', '5672')}/"
)
EXCHANGE_NAME = "comedor"

_connection: aio_pika.RobustConnection | None = None


async def get_connection() -> aio_pika.RobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
    return _connection


async def publish(routing_key: str, payload: dict) -> None:
    try:
        conn    = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await conn.channel()
        exchange = await channel.declare_exchange(EXCHANGE_NAME, ExchangeType.TOPIC, durable=True)
        await exchange.publish(
            Message(
                body=json.dumps(payload).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )
        await conn.close()
    except Exception as e:
        print(f"[RabbitMQ] Error publicando '{routing_key}': {e}")


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
    print(f"[RabbitMQ] '{queue_name}' escuchando: {routing_keys}")
