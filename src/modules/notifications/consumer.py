import json
import logging

import aio_pika

from ...shared.push import send_push
from ...shared.rabbitmq import start_consumer

log = logging.getLogger(__name__)

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

            log.debug("M4 recibió evento=%s numero=%s", evento, numero)
            if not push_token or not evento:
                log.info("M4 descarta evento=%s: falta push_token o evento", evento)
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
        except Exception:
            # Se confirma el mensaje igual (message.process): una push perdida no
            # debe reintentarse en bucle ni frenar a los demás estudiantes.
            log.exception("M4 no pudo procesar el mensaje")


async def start() -> None:
    await start_consumer(QUEUE_NAME, ROUTING_KEYS, _handle)
