from datetime import time
from typing import Optional

from fastapi import HTTPException, status

from ...shared.db import get_db_conn

# Tipos que el admin puede configurar. 'PRUEBA' queda fuera (solo para testing).
CONFIGURABLE_TIPOS = {"ALMUERZO", "CENA"}


def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "tipo": row[1],
        "hora_apertura": row[2],
        "hora_inicio": row[3],
        "hora_cierre": row[4],
        "raciones_max": row[5],
        "activo": row[6],
    }


def _validate_tipo(tipo: str) -> str:
    tipo = tipo.upper()
    if tipo not in CONFIGURABLE_TIPOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo no configurable: {tipo}. Solo se permiten {sorted(CONFIGURABLE_TIPOS)}.",
        )
    return tipo


def _validate_horas(apertura: time, inicio: time, cierre: time) -> None:
    if not (apertura <= inicio <= cierre):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las horas deben cumplir: hora_apertura <= hora_inicio <= hora_cierre.",
        )


def list_turnos_config() -> list[dict]:
    """Lista las plantillas configurables (ALMUERZO y CENA), ordenadas por tipo."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tipo, hora_apertura, hora_inicio, hora_cierre, raciones_max, activo
                FROM turnos_config
                WHERE tipo = ANY(%s)
                ORDER BY tipo
                """,
                (list(CONFIGURABLE_TIPOS),),
            )
            return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_turno_config(tipo: str) -> dict:
    tipo = _validate_tipo(tipo)
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tipo, hora_apertura, hora_inicio, hora_cierre, raciones_max, activo
                FROM turnos_config
                WHERE tipo = %s
                """,
                (tipo,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No existe configuración para el turno {tipo}.",
                )
            return _row_to_dict(row)
    finally:
        conn.close()


def update_turno_config(tipo: str, cambios: dict) -> dict:
    """
    Actualización parcial de la plantilla de un turno (ALMUERZO o CENA).
    Solo se modifican los campos presentes en `cambios` (no None).
    """
    tipo = _validate_tipo(tipo)

    actual = get_turno_config(tipo)

    # Merge: lo enviado sobreescribe lo actual.
    nuevos = {
        "hora_apertura": cambios.get("hora_apertura") or actual["hora_apertura"],
        "hora_inicio": cambios.get("hora_inicio") or actual["hora_inicio"],
        "hora_cierre": cambios.get("hora_cierre") or actual["hora_cierre"],
        "raciones_max": cambios["raciones_max"] if cambios.get("raciones_max") is not None else actual["raciones_max"],
        "activo": cambios["activo"] if cambios.get("activo") is not None else actual["activo"],
    }

    if nuevos["raciones_max"] is not None and nuevos["raciones_max"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="raciones_max debe ser mayor a 0.",
        )

    _validate_horas(nuevos["hora_apertura"], nuevos["hora_inicio"], nuevos["hora_cierre"])

    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE turnos_config
                SET hora_apertura = %s,
                    hora_inicio   = %s,
                    hora_cierre   = %s,
                    raciones_max  = %s,
                    activo        = %s
                WHERE tipo = %s
                RETURNING id, tipo, hora_apertura, hora_inicio, hora_cierre, raciones_max, activo
                """,
                (
                    nuevos["hora_apertura"],
                    nuevos["hora_inicio"],
                    nuevos["hora_cierre"],
                    nuevos["raciones_max"],
                    nuevos["activo"],
                    tipo,
                ),
            )
            row = cur.fetchone()
        conn.commit()
        return _row_to_dict(row)
    finally:
        conn.close()
