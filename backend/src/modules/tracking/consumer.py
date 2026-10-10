import json

import aio_pika

from ...shared.rabbitmq import start_consumer
from .service import registrar_asistencia, registrar_encolamiento

QUEUE_NAME   = "m5.seguimiento"
ROUTING_KEYS = ["turno.atendido", "turno.encolado"]


async def _handle(message: aio_pika.IncomingMessage) -> None:
    async with message.process():
        try:
            payload      = json.loads(message.body)
            evento       = payload.get("evento")
            est_id       = payload.get("estudiante_id")
            td_id        = payload.get("turno_dia_id")
            numero_turno = payload.get("numero_turno")
            tipo_comida  = payload.get("tipo_comida", "")

            if not all([est_id, td_id, numero_turno]):
                return

            if evento == "turno.atendido":
                registrar_asistencia(est_id, td_id, numero_turno, tipo_comida)
                print(f"[M5] Asistencia registrada — turno #{numero_turno} ({tipo_comida})")

            elif evento == "turno.encolado":
                registrar_encolamiento(est_id, td_id, numero_turno, tipo_comida)
                print(f"[M5] Encolamiento registrado — turno #{numero_turno} ({tipo_comida})")

        except Exception as e:
            print(f"[M5] Error procesando mensaje: {e}")


async def start() -> None:
    await start_consumer(QUEUE_NAME, ROUTING_KEYS, _handle)
