import json

import aio_pika

from ...shared.push import send_push
from ...shared.rabbitmq import start_consumer

QUEUE_NAME   = "m4.notificaciones"
ROUTING_KEYS = ["turno.llamado", "turno.cancelado"]

MENSAJES = {
    "turno.llamado":   ("¡Es tu turno!", "Confirma tu presencia en los próximos 3 minutos."),
    "turno.cancelado": ("Turno cancelado", "Tu turno fue cancelado por inactividad."),
}


async def _handle(message: aio_pika.IncomingMessage) -> None:
    async with message.process():
        try:
            payload    = json.loads(message.body)
            evento     = payload.get("evento")
            push_token = payload.get("push_token")
            numero     = payload.get("numero_turno")

            print(f"[M4] Mensaje recibido: evento={evento}, push_token={push_token}, numero={numero}")
            if not push_token or not evento:
                print(f"[M4] Descartando — falta push_token o evento")
                return

            title, body = MENSAJES.get(evento, ("Comedor UNI", "Tienes una notificación"))
            if numero:
                body = f"Turno #{numero}: {body}"

            await send_push(
                token=push_token,
                title=title,
                body=body,
                data={"type": evento.split(".")[1], "turno": numero},
            )
        except Exception as e:
            print(f"[M4] Error procesando mensaje: {e}")


async def start() -> None:
    await start_consumer(QUEUE_NAME, ROUTING_KEYS, _handle)
