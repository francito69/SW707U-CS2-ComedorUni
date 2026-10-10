import asyncio

from ...shared.push import send_push
from ...shared.rabbitmq import publish
from ..reassignment.service import llamar_siguiente
from .manager import manager
from .service import (
    cancelar_inactivos,
    get_turno_dias_en_servicio,
    get_turnos_a_notificar,
)

INTERVAL_SECONDS = 60


def _evento_base(payload: dict) -> dict:
    from datetime import datetime
    return {**payload, "timestamp": datetime.now().isoformat()}


async def inactivity_worker():
    while True:
        await asyncio.sleep(INTERVAL_SECONDS)
        try:
            # ── Ping a los que llevan 3 min sin responder ──────────────────
            for t in get_turnos_a_notificar():
                codigo = t["codigo"]
                numero = t["numero_turno"]
                if manager.is_connected(codigo):
                    await manager.send(codigo, {
                        "type":    "ping_request",
                        "mensaje": "¿Sigues en la cola? Confirma tu presencia.",
                        "turno":   numero,
                    })
                # Push se delega a M4 vía RabbitMQ (turno.llamado ya lo publicó antes)

            # ── Cancelar inactivos ─────────────────────────────────────────
            cancelados = cancelar_inactivos()
            for c in cancelados:
                codigo       = c["codigo"]
                turno_dia_id = c["turno_dia_id"]
                print(f"[Queue] Turno cancelado por inactividad: {codigo}")
                if manager.is_connected(codigo):
                    await manager.send(codigo, {
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

                    if manager.is_connected(codigo):
                        await manager.send(codigo, {
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
