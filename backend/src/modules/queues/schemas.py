from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JoinQueueRequest(BaseModel):
    sid: str
    tipo: str  # 'ALMUERZO' | 'CENA' | 'PRUEBA'


class JoinQueueResponse(BaseModel):
    numero_turno: int       # posición de llegada (1, 2, 3, ...)
    tipo: str
    posicion: int
    raciones_restantes: int
    mensaje: str


class TurnoStatusResponse(BaseModel):
    numero_turno: int               # posición de llegada
    estado: str
    tipo: str
    posicion: int                   # personas adelante aún esperando
    turno_actual: int               # turno grupo siendo atendido ahora
    turno_asignado: Optional[int] = None   # turno grupo (solo si ATENDIDO)
    llamado_at: Optional[datetime] = None


class ConfirmRequest(BaseModel):
    sid: str


class ConfirmResponse(BaseModel):
    estado: str
    mensaje: str
    turno_asignado: Optional[int] = None   # turno grupo asignado al confirmar
