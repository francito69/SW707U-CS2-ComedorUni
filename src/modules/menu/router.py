from datetime import date
from typing import Optional

from fastapi import APIRouter, status

from .schemas import MenuDiaCreateRequest, MenuDiaResponse, MenuDiaUpdateRequest
from .service import create_menu_dia, fecha_peru, get_menu, update_menu_dia

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=MenuDiaResponse)
def get_menu_dia(fecha: Optional[date] = None):
    """
    Retorna el menú del día.
    Si no se pasa fecha, usa la fecha actual en hora de Perú (UTC-5).
    """
    fecha_consulta = fecha or fecha_peru()
    comidas = get_menu(fecha_consulta)
    return MenuDiaResponse(fecha=fecha_consulta, comidas=comidas)


@router.post("", response_model=MenuDiaResponse, status_code=status.HTTP_201_CREATED)
def create_menu_dia_endpoint(payload: MenuDiaCreateRequest):
    comidas = create_menu_dia(payload.fecha, [item.model_dump() for item in payload.comidas])
    return MenuDiaResponse(fecha=payload.fecha, comidas=comidas)


@router.put("", response_model=MenuDiaResponse)
def update_menu_dia_endpoint(fecha: date, payload: MenuDiaUpdateRequest):
    comidas = update_menu_dia(fecha, [item.model_dump() for item in payload.comidas])
    return MenuDiaResponse(fecha=fecha, comidas=comidas)
