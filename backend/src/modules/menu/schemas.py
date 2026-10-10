from pydantic import BaseModel
from datetime import date
from typing import Optional


class PlatoInput(BaseModel):
    nombre: str


class MenuComidaInput(BaseModel):
    tipo_comida: str
    energia_kcal: Optional[float] = None
    lipidos_g: Optional[float] = None
    proteinas_g: Optional[float] = None
    carbohidratos_g: Optional[float] = None
    platos: list[PlatoInput] = []


class MenuDiaCreateRequest(BaseModel):
    fecha: date
    comidas: list[MenuComidaInput]


class MenuDiaUpdateRequest(BaseModel):
    comidas: list[MenuComidaInput]


class PlatoResponse(BaseModel):
    id: int
    nombre: str


class MenuComidaResponse(BaseModel):
    id: int
    tipo_comida: str
    energia_kcal: Optional[float] = None
    lipidos_g: Optional[float] = None
    proteinas_g: Optional[float] = None
    carbohidratos_g: Optional[float] = None
    platos: list[PlatoResponse] = []


class MenuDiaResponse(BaseModel):
    fecha: date
    comidas: list[MenuComidaResponse]
