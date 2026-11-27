"""Repositorio de `turno_dia` extraído de `queues/service.py` (Semana 12 - Refactorización)."""

import logging
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ...shared.db import use_conn

log = logging.getLogger(__name__)

LIMA_TZ = ZoneInfo("America/Lima")


def fecha_lima() -> date:
    """Retorna la fecha actual en zona horaria America/Lima."""
    return datetime.now(LIMA_TZ).date()


def ensure_turno_dia_hoy() -> None:
    """Crea los turno_dia del día Lima si no existen. Se llama al arrancar el backend."""
    hoy = fecha_lima()
    with use_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, tipo, raciones_max FROM turnos_config WHERE activo = TRUE")
            configs = cur.fetchall()
            for config_id, tipo, raciones_max in configs:
                cur.execute(
                    "INSERT INTO turno_dia (config_id, fecha, raciones_max) VALUES (%s, %s, %s) ON CONFLICT (config_id, fecha) DO NOTHING",
                    (config_id, hoy, raciones_max),
                )
                log.info("turno_dia %s %s listo", tipo, hoy)
        conn.commit()


def get_turnos_dia_activos(conn=None) -> list[dict]:
    """
    Retorna todos los turno_dia vigentes según la hora actual.
    Un turno está activo si hora_apertura <= ahora <= hora_cierre.
    """
    ahora = datetime.now().time()
    with use_conn(conn) as _conn:
        with _conn.cursor() as cur:
            cur.execute(
                """
                SELECT td.id, td.config_id, tc.tipo,
                       COALESCE(td.hora_apertura, tc.hora_apertura) AS hora_apertura,
                       tc.hora_inicio,
                       COALESCE(td.hora_cierre,   tc.hora_cierre)   AS hora_cierre,
                       COALESCE(td.raciones_max,  tc.raciones_max)  AS raciones_max
                FROM turno_dia td
                JOIN turnos_config tc ON tc.id = td.config_id
                WHERE td.fecha    = %s
                  AND td.abierto  = TRUE
                  AND tc.activo   = TRUE
                  AND COALESCE(td.hora_apertura, tc.hora_apertura) <= %s
                  AND COALESCE(td.hora_cierre,   tc.hora_cierre)   >= %s
                """,
                (fecha_lima(), ahora, ahora),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0], "config_id": r[1], "tipo": r[2],
                    "hora_apertura": r[3], "hora_inicio": r[4],
                    "hora_cierre": r[5], "raciones_max": r[6],
                }
                for r in rows
            ]


def get_turno_dia_activo(conn=None) -> Optional[dict]:
    """Compatibilidad: retorna el primer turno activo (para WS y confirm)."""
    turnos = get_turnos_dia_activos(conn)
    return turnos[0] if turnos else None


def active_service_payload(conn=None) -> dict:
    """
    Snapshot serializable de los turnos activos. Usado por GET /queue/active-service
    y por el WebSocket público /queue/ws/active-service.
    """
    turnos = get_turnos_dia_activos(conn)
    if not turnos:
        return {"activo": False, "turnos": []}
    return {
        "activo": True,
        "turnos": [
            {
                "tipo":        t["tipo"],
                "hora_inicio": str(t["hora_inicio"]),
                "hora_cierre": str(t["hora_cierre"]),
            }
            for t in turnos
        ],
    }


def get_turno_dia_activo_por_tipo(tipo: str, conn=None) -> Optional[dict]:
    """Retorna el turno_dia activo que coincide con `tipo`, o None."""
    turnos = get_turnos_dia_activos(conn)
    for t in turnos:
        if t["tipo"] == tipo:
            return t
    return None


def get_turno_dia_id(config_id: int, conn=None) -> Optional[int]:
    """Obtiene el turno_dia de hoy para el config dado. Lo crean los admins."""
    with use_conn(conn) as _conn:
        with _conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM turno_dia WHERE config_id = %s AND fecha = %s AND abierto = TRUE",
                (config_id, fecha_lima()),
            )
            row = cur.fetchone()
            return row[0] if row else None


def servicio_iniciado(turno_dia: dict) -> bool:
    """True si ya empezó la atención (hora_inicio <= ahora)."""
    return datetime.now().time() >= turno_dia["hora_inicio"]
