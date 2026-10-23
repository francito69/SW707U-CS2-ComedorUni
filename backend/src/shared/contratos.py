"""
Design by Contract mínimo. A diferencia de `assert`, estas verificaciones no se
desactivan con `python -O`: un contrato roto en producción debe notarse.
"""
from .errores import ContratoViolado


def requiere(condicion: bool, descripcion: str) -> None:
    """Precondición: lo que el llamador debe garantizar antes de la llamada."""
    if not condicion:
        raise ContratoViolado(f"Precondición violada: {descripcion}")


def asegura(condicion: bool, descripcion: str) -> None:
    """Postcondición o invariante: lo que la función garantiza al terminar."""
    if not condicion:
        raise ContratoViolado(f"Postcondición violada: {descripcion}")
