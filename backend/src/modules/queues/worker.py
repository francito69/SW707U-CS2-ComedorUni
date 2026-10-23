import asyncio

from ...shared.leader_lock import try_acquire
from ...shared.push import send_push
from ...shared.rabbitmq import publish
from ...shared.ws_bus import publish_broadcast, publish_to_session
from ..reassignment.service import llamar_siguiente
from .service import (
    active_service_payload,
    cancelar_inactivos,
    get_turno_dias_en_servicio,
    get_turnos_a_notificar,
)

INTERVAL_SECONDS = 60
ACTIVE_SERVICE_POLL_SECONDS = 15


def _evento_base(payload: dict) -> dict:
    from datetime import datetime
    return {**payload, "timestamp": datetime.now().isoformat()}


async def inactivity_worker():
    while True:
        await asyncio.sleep(INTERVAL_SECONDS)
        # Con --workers > 1 cada proceso corre su propia copia de este loop.
        # Solo el que gane el lock ejecuta este ciclo — si no, cancelaría y
        # llamaría turnos por duplicado (uno por worker). TTL algo menor al
        # intervalo para que, si el ganador muere, el lock ya haya expirado
        # y cualquier otro pueda tomarlo en el siguiente ciclo.
        if not await try_acquire("inactivity_worker", INTERVAL_SECONDS - 5):
            continue
        try:
            # ── Ping a los que llevan 3 min sin responder ──────────────────
            for t in get_turnos_a_notificar():
                await publish_to_session(t["codigo"], {
                    "type":    "ping_request",
                    "mensaje": "¿Sigues en la cola? Confirma tu presencia.",
                    "turno":   t["numero_turno"],
                })
                # Push se delega a M4 vía RabbitMQ (turno.llamado ya lo publicó antes)

            # ── Cancelar inactivos ─────────────────────────────────────────
            cancelados = cancelar_inactivos()
            for c in cancelados:
                codigo       = c["codigo"]
                turno_dia_id = c["turno_dia_id"]
                print(f"[Queue] Turno cancelado por inactividad: {codigo}")
                await publish_to_session(codigo, {
                    "type":    "cancelado",
                    "mensaje": "Tu turno fue cancelado por inactividad.",
                })
                await publish("turno.cancelado", _evento_base({
                    "evento":      "turno.cancelado",
                    "codigo":      codigo,
                    "push_token":  c.get("push_token"),
                    "turno_dia_id": turno_dia_id,
                }))

            # ── Auto-llamar siguiente turno (grupo completo) ───────────────
            for turno_dia_id in get_turno_dias_en_servicio():
                for llamado in llamar_siguiente(turno_dia_id):
                    codigo     = llamado["codigo"]
                    numero     = llamado["numero_turno"]
                    push_token = llamado["push_token"]
                    print(f"[Queue] Llamando turno #{numero} — alumno {codigo} — push_token: {push_token}")

                    await publish_to_session(codigo, {
                        "type":    "llamado",
                        "turno":   numero,
                        "mensaje": "¡Es tu turno! Confirma en los próximos 3 minutos.",
                    })

                    await publish("turno.llamado", _evento_base({
                        "evento":       "turno.llamado",
                        "codigo":       codigo,
                        "numero_turno": numero,
                        "push_token":   push_token,
                        "turno_dia_id": turno_dia_id,
                    }))

        except Exception as e:
            print(f"[Queue] Error en worker: {e}")


async def active_service_worker():
    """
    Revisa cada ACTIVE_SERVICE_POLL_SECONDS el estado de turnos activos y lo
    manda a todos los WebSocket conectados a /queue/ws/active-service (en
    cualquier worker, vía Redis pub/sub — ver ws_bus.py). Así la pantalla de
    inicio se actualiza sola, sin que el usuario reingrese.

    No compara contra el último valor conocido antes de avisar: qué worker
    gana el lock varía de ciclo a ciclo, y ese "último valor" viviría en
    memoria de un solo proceso — comparar así generaría un broadcast
    redundante cada vez que el lock rota a un worker distinto. Mandar el
    snapshot siempre es más simple y correcto aquí; el costo es un mensaje
    pequeño cada ACTIVE_SERVICE_POLL_SECONDS por cliente conectado.
    """
    while True:
        await asyncio.sleep(ACTIVE_SERVICE_POLL_SECONDS)
        if not await try_acquire("active_service_worker", ACTIVE_SERVICE_POLL_SECONDS - 3):
            continue
        try:
            await publish_broadcast(active_service_payload())
        except Exception as e:
            print(f"[Queue] Error en active_service_worker: {e}")
