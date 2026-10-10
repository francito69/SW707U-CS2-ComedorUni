from datetime import date
from typing import Optional

from fastapi import APIRouter, status

from .schemas import TurnoConfigResponse, TurnoConfigUpdateRequest
from .service import get_turno_config, list_turnos_config, update_turno_config

# Reutilizamos el módulo menu para registrar el almuerzo/cena con sus comidas.
# No se duplica lógica de BD: estos endpoints solo agrupan lo de admin bajo /config.
from ..menu.schemas import MenuDiaCreateRequest, MenuDiaResponse, MenuDiaUpdateRequest
from ..menu.service import create_menu_dia, fecha_peru, get_menu, update_menu_dia

router = APIRouter(prefix="/config", tags=["config"])


# ── Plantillas de turno (ALMUERZO / CENA) ─────────────────────────────────────

@router.get("/turnos", response_model=list[TurnoConfigResponse])
def list_turnos_config_endpoint():
    """Lista las plantillas de turno configurables (ALMUERZO y CENA)."""
    return list_turnos_config()


@router.get("/turnos/{tipo}", response_model=TurnoConfigResponse)
def get_turno_config_endpoint(tipo: str):
    """Retorna la plantilla de un turno (ALMUERZO o CENA)."""
    return get_turno_config(tipo)


@router.put("/turnos/{tipo}", response_model=TurnoConfigResponse)
def update_turno_config_endpoint(tipo: str, payload: TurnoConfigUpdateRequest):
    """
    Actualiza la plantilla de un turno (ALMUERZO o CENA).
    Solo se modifican los campos enviados (horarios, raciones_max, activo).
    """
    return update_turno_config(tipo, payload.model_dump(exclude_unset=True))


# ── Menú del día (almuerzo/cena con sus comidas) ──────────────────────────────
# Reutiliza el service del módulo menu. Lo que se registra aquí lo ven los
# alumnos vía GET /menu.

@router.get("/menu", response_model=MenuDiaResponse)
def get_menu_dia_endpoint(fecha: Optional[date] = None):
    """Retorna el menú de una fecha (por defecto, hoy en hora Perú)."""
    fecha_consulta = fecha or fecha_peru()
    comidas = get_menu(fecha_consulta)
    return MenuDiaResponse(fecha=fecha_consulta, comidas=comidas)


@router.post("/menu", response_model=MenuDiaResponse, status_code=status.HTTP_201_CREATED)
def create_menu_dia_endpoint(payload: MenuDiaCreateRequest):
    """Registra el menú de una fecha (almuerzo/cena con sus platos)."""
    comidas = create_menu_dia(payload.fecha, [item.model_dump() for item in payload.comidas])
    return MenuDiaResponse(fecha=payload.fecha, comidas=comidas)


@router.put("/menu", response_model=MenuDiaResponse)
def update_menu_dia_endpoint(fecha: date, payload: MenuDiaUpdateRequest):
    """Edita el menú ya registrado de una fecha."""
    comidas = update_menu_dia(fecha, [item.model_dump() for item in payload.comidas])
    return MenuDiaResponse(fecha=fecha, comidas=comidas)
