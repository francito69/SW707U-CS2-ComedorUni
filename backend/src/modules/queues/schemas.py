from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from ...shared.validacion import Sid, TipoTurno


class JoinQueueRequest(BaseModel):
    sid: Sid
    tipo: TipoTurno


class PushTokenRequest(BaseModel):
    sid: Sid
    push_token: str = Field(min_length=1, max_length=255)  # estudiantes.push_token es VARCHAR(255)


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
    sid: Sid


class ConfirmResponse(BaseModel):
    estado: str
    mensaje: str
    turno_asignado: Optional[int] = None   # turno grupo asignado al confirmar
