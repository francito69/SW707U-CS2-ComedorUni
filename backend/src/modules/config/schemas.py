from datetime import time
from typing import Optional

from pydantic import BaseModel


class TurnoConfigResponse(BaseModel):
    id: int
    tipo: str
    hora_apertura: time
    hora_inicio: time
    hora_cierre: time
    raciones_max: int
    activo: bool


class TurnoConfigUpdateRequest(BaseModel):
    """Actualización parcial: solo se modifican los campos enviados."""
    hora_apertura: Optional[time] = None
    hora_inicio: Optional[time] = None
    hora_cierre: Optional[time] = None
    raciones_max: Optional[int] = None
    activo: Optional[bool] = None
