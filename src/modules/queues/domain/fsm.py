"""Máquina de estados finitos (FSM) y tabla de transiciones para el ciclo de vida de un turno."""
from dataclasses import dataclass
from enum import Enum


class EstadoTurno(str, Enum):
    ESPERANDO = "ESPERANDO"
    LLAMADO = "LLAMADO"
    ATENDIDO = "ATENDIDO"
    CANCELADO = "CANCELADO"


class EventoTurno(str, Enum):
    LLAMAR = "LLAMAR"
    CONFIRMAR_PRESENCIA = "CONFIRMAR_PRESENCIA"
    PING = "PING"
    SALIR = "SALIR"
    EXPIRAR_INACTIVIDAD = "EXPIRAR_INACTIVIDAD"


@dataclass(frozen=True)
class ReglaTransicion:
    nuevo_estado: EstadoTurno
    actualizar_ping: bool = False
    evento_dominio: str | None = None


# Construcción dirigida por tablas: (estado_actual, evento) -> ReglaTransicion
TRANSICIONES: dict[tuple[EstadoTurno, EventoTurno], ReglaTransicion] = {
    (EstadoTurno.ESPERANDO, EventoTurno.LLAMAR): ReglaTransicion(
        nuevo_estado=EstadoTurno.LLAMADO,
        evento_dominio="turno.llamado",
    ),
    (EstadoTurno.ESPERANDO, EventoTurno.PING): ReglaTransicion(
        nuevo_estado=EstadoTurno.ESPERANDO,
        actualizar_ping=True,
    ),
    (EstadoTurno.ESPERANDO, EventoTurno.SALIR): ReglaTransicion(
        nuevo_estado=EstadoTurno.CANCELADO,
        evento_dominio="turno.cancelado",
    ),
    (EstadoTurno.LLAMADO, EventoTurno.CONFIRMAR_PRESENCIA): ReglaTransicion(
        nuevo_estado=EstadoTurno.ATENDIDO,
        evento_dominio="turno.atendido",
    ),
    (EstadoTurno.LLAMADO, EventoTurno.PING): ReglaTransicion(
        nuevo_estado=EstadoTurno.LLAMADO,
        actualizar_ping=False,
    ),
    (EstadoTurno.LLAMADO, EventoTurno.SALIR): ReglaTransicion(
        nuevo_estado=EstadoTurno.CANCELADO,
        evento_dominio="turno.cancelado",
    ),
    (EstadoTurno.LLAMADO, EventoTurno.EXPIRAR_INACTIVIDAD): ReglaTransicion(
        nuevo_estado=EstadoTurno.CANCELADO,
        evento_dominio="turno.cancelado",
    ),
}


class TransicionInvalidaError(ValueError):
    """Se lanza cuando una transición (estado, evento) no está permitida en la tabla."""

    def __init__(self, estado_actual: str, evento: EventoTurno) -> None:
        self.estado_actual = estado_actual
        self.evento = evento
        super().__init__(f"Transición inválida: estado={estado_actual}, evento={evento.value}")


def transicionar(estado_actual: str | EstadoTurno, evento: EventoTurno) -> ReglaTransicion:
    """Valida y resuelve la transición usando la tabla TRANSICIONES."""
    try:
        estado = EstadoTurno(estado_actual)
    except ValueError as exc:
        raise TransicionInvalidaError(str(estado_actual), evento) from exc

    regla = TRANSICIONES.get((estado, evento))
    if regla is None:
        raise TransicionInvalidaError(estado.value, evento)
    return regla
