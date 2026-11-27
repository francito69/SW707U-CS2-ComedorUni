import logging
from datetime import date, datetime
from typing import NamedTuple, Optional
from zoneinfo import ZoneInfo

import psycopg2.errors

from ...shared.contratos import asegura, requiere
from ...shared.db import get_db_conn
from ...shared.errores import SinRaciones, TurnoDuplicado
from .turno_dia_repo import (
    LIMA_TZ,
    active_service_payload,
    ensure_turno_dia_hoy,
    fecha_lima,
    get_turno_dia_activo,
    get_turno_dia_activo_por_tipo,
    get_turno_dia_id,
    get_turnos_dia_activos,
    servicio_iniciado,
)

log = logging.getLogger(__name__)

TOLERANCIA_LLAMADO_SECONDS = 180  # plazo para confirmar desde que te llaman


# ── turnos ───────────────────────────────────────────────────────────────────

def get_estudiante_id(codigo: str, conn=None) -> Optional[int]:
    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            cur.execute("SELECT id FROM estudiantes WHERE codigo = %s", (codigo,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        if conn is None:
            _conn.close()


def get_push_token(codigo: str) -> Optional[str]:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT push_token FROM estudiantes WHERE codigo = %s", (codigo,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def save_push_token(codigo: str, token: str) -> None:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE estudiantes SET push_token = %s WHERE codigo = %s",
                (token, codigo),
            )
        conn.commit()
    finally:
        conn.close()


def raciones_usadas(turno_dia_id: int) -> int:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM turnos
                WHERE turno_dia_id = %s AND estado != 'CANCELADO'
                """,
                (turno_dia_id,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_turno_activo_por_codigo(codigo: str, conn=None) -> Optional[dict]:
    """Busca el turno activo del estudiante en el día de hoy sin importar el horario."""
    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, t.numero_turno, t.estado, t.turno_dia_id, tc.tipo
                FROM turnos t
                JOIN turno_dia td ON td.id = t.turno_dia_id
                JOIN turnos_config tc ON tc.id = td.config_id
                JOIN estudiantes e ON e.id = t.estudiante_id
                WHERE e.codigo = %s
                  AND td.fecha = %s
                  AND t.estado NOT IN ('CANCELADO', 'ATENDIDO')
                LIMIT 1
                """,
                (codigo, fecha_lima()),
            )
            row = cur.fetchone()
            return {
                "id": row[0], "numero_turno": row[1], "estado": row[2],
                "turno_dia_id": row[3], "tipo": row[4],
            } if row else None
    finally:
        if conn is None:
            _conn.close()


def cancelar_turno(turno_id: int) -> None:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE turnos SET estado='CANCELADO', cancelado_at=NOW()
                WHERE id = %s AND estado NOT IN ('ATENDIDO', 'CANCELADO')
                """,
                (turno_id,),
            )
        conn.commit()
    finally:
        conn.close()


def turno_existente(estudiante_id: int, turno_dia_id: int) -> Optional[dict]:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, numero_turno, estado FROM turnos
                WHERE estudiante_id = %s AND turno_dia_id = %s
                  AND estado != 'CANCELADO'
                """,
                (estudiante_id, turno_dia_id),
            )
            row = cur.fetchone()
            return {"id": row[0], "numero_turno": row[1], "estado": row[2]} if row else None
    finally:
        conn.close()


import math

def calcular_turno_asignado(posicion: int, raciones_max: int) -> int:
    """Turno grupo (1–10) que corresponde a una posición de llegada."""
    batch_size = max(1, math.ceil(raciones_max / 10))
    return math.ceil(posicion / batch_size)


def turno_asignado_de(turno_id: int, raciones_max: int, conn=None) -> int:
    """
    Grupo de comedor de un turno ATENDIDO según el ORDEN EN QUE CONFIRMÓ, no su
    número de cola: quien confirma tarde (lo pasaron mientras no respondía)
    entra al grupo que se está atendiendo en ese momento, sin recuperar su
    lugar original ni desplazar a quienes ya confirmaron.
    """
    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM turnos t
                JOIN turnos yo ON yo.id = %s
                WHERE t.turno_dia_id = yo.turno_dia_id
                  AND t.estado = 'ATENDIDO'
                  AND (t.confirmado_at, t.id) <= (yo.confirmado_at, yo.id)
                """,
                (turno_id,),
            )
            orden = cur.fetchone()[0]
        requiere(orden >= 1, f"el turno {turno_id} está ATENDIDO")
        return calcular_turno_asignado(orden, raciones_max)
    finally:
        if conn is None:
            _conn.close()


def get_raciones_max_turno_dia(turno_dia_id: int) -> int:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(td.raciones_max, tc.raciones_max)
                FROM turno_dia td
                JOIN turnos_config tc ON tc.id = td.config_id
                WHERE td.id = %s
                """,
                (turno_dia_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 100
    finally:
        conn.close()


class TurnoCreado(NamedTuple):
    numero: int
    raciones_restantes: int


def crear_turno(estudiante_id: int, turno_dia_id: int, raciones_max: int, conn=None) -> TurnoCreado:
    """
    Asigna el siguiente número de turno en una sección crítica sobre turno_dia.

    Precondiciones: ids y raciones_max positivos; el turno_dia existe.
    Postcondiciones: el número es exactamente el máximo previo + 1 (sin contar los
    CANCELADOS: quien sale y vuelve a entrar sin que nadie más haya entrado
    recupera el mismo número, y siempre queda detrás de los activos) y los turnos
    activos del día no superan raciones_max (invariante de aforo).
    Errores de negocio: SinRaciones si ya no quedan cupos; TurnoDuplicado si el
    estudiante ya tiene un turno activo (lo garantiza idx_turnos_activo).
    """
    requiere(estudiante_id > 0, "estudiante_id debe ser positivo")
    requiere(turno_dia_id > 0, "turno_dia_id debe ser positivo")
    requiere(raciones_max > 0, "raciones_max debe ser positivo")

    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            # FOR UPDATE serializa a todos los que piden turno en este turno_dia:
            # el conteo de raciones y el INSERT ocurren sin que nadie se intercale.
            cur.execute("SELECT id FROM turno_dia WHERE id = %s FOR UPDATE", (turno_dia_id,))
            requiere(cur.fetchone() is not None, f"turno_dia {turno_dia_id} existe")

            cur.execute(
                """
                SELECT COUNT(*) FILTER (WHERE estado != 'CANCELADO'),
                       COALESCE(MAX(numero_turno) FILTER (WHERE estado != 'CANCELADO'), 0)
                FROM turnos
                WHERE turno_dia_id = %s
                """,
                (turno_dia_id,),
            )
            activos, ultimo_numero = cur.fetchone()
            if activos >= raciones_max:
                _conn.rollback()
                raise SinRaciones()

            try:
                cur.execute(
                    """
                    INSERT INTO turnos (estudiante_id, turno_dia_id, numero_turno)
                    VALUES (%s, %s, %s) RETURNING numero_turno
                    """,
                    (estudiante_id, turno_dia_id, ultimo_numero + 1),
                )
            except psycopg2.errors.UniqueViolation as e:
                _conn.rollback()
                if e.diag.constraint_name == "idx_turnos_activo":
                    raise TurnoDuplicado("Ya tienes un turno activo en este servicio") from e
                raise
            numero = cur.fetchone()[0]

        asegura(numero == ultimo_numero + 1, "el número de turno es el máximo no cancelado + 1")
        asegura(activos + 1 <= raciones_max, "los turnos activos no superan raciones_max")
        _conn.commit()
        return TurnoCreado(numero=numero, raciones_restantes=raciones_max - activos - 1)
    finally:
        if conn is None:
            _conn.close()


def posicion_en_cola(turno_dia_id: int, numero_turno: int) -> int:
    """Cuántas personas están adelante en la cola (aún ESPERANDO)."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM turnos
                WHERE turno_dia_id = %s AND estado = 'ESPERANDO'
                  AND numero_turno < %s
                """,
                (turno_dia_id, numero_turno),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_turno_actual(turno_dia_id: int) -> int:
    """Último número ATENDIDO."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(MAX(numero_turno), 0) FROM turnos
                WHERE turno_dia_id = %s AND estado = 'ATENDIDO'
                """,
                (turno_dia_id,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_turno_by_codigo(codigo: str, turno_dia_id: int, conn=None) -> Optional[dict]:
    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, t.numero_turno, t.estado, t.llamado_at, tc.tipo
                FROM turnos t
                JOIN turno_dia td ON td.id = t.turno_dia_id
                JOIN turnos_config tc ON tc.id = td.config_id
                JOIN estudiantes e ON e.id = t.estudiante_id
                WHERE e.codigo = %s AND t.turno_dia_id = %s
                  AND t.estado != 'CANCELADO'
                """,
                (codigo, turno_dia_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {"id": row[0], "numero_turno": row[1], "estado": row[2],
                    "llamado_at": row[3], "tipo": row[4]}
    finally:
        if conn is None:
            _conn.close()


def confirmar_turno(turno_id: int, estado_actual: str, conn=None) -> str:
    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            if estado_actual == "LLAMADO":
                cur.execute(
                    "UPDATE turnos SET estado='ATENDIDO', confirmado_at=NOW() WHERE id=%s",
                    (turno_id,),
                )
                nuevo = "ATENDIDO"
            else:
                cur.execute(
                    "UPDATE turnos SET ultimo_ping=NOW() WHERE id=%s",
                    (turno_id,),
                )
                nuevo = "ESPERANDO"
        _conn.commit()
        return nuevo
    finally:
        if conn is None:
            _conn.close()


# ── inactividad ──────────────────────────────────────────────────────────────

def get_turno_hoy_por_codigo(codigo: str) -> Optional[dict]:
    """
    Busca el turno activo (ESPERANDO o LLAMADO) del estudiante para hoy,
    sin requerir que haya una ventana de servicio activa en este momento.
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, t.numero_turno, t.estado, t.llamado_at,
                       tc.tipo, td.id AS turno_dia_id
                FROM turnos t
                JOIN turno_dia td ON td.id = t.turno_dia_id
                JOIN turnos_config tc ON tc.id = td.config_id
                JOIN estudiantes e ON e.id = t.estudiante_id
                WHERE e.codigo = %s
                  AND td.fecha = %s
                  AND t.estado != 'CANCELADO'
                ORDER BY t.numero_turno ASC
                LIMIT 1
                """,
                (codigo, fecha_lima()),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0], "numero_turno": row[1], "estado": row[2],
                "llamado_at": row[3], "tipo": row[4], "turno_dia_id": row[5],
            }
    finally:
        conn.close()


def cancelar_inactivos() -> list[dict]:
    """
    Cancela los turnos LLAMADO que no confirmaron dentro de los 3 minutos
    contados desde que fueron llamados. El plazo es fijo: los pings de la app
    no lo extienden (solo "Confirmar presencia" salva el turno).
    Los turnos ESPERANDO no se cancelan: su lugar se mantiene aunque la app
    esté en segundo plano.
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE turnos t SET estado='CANCELADO', cancelado_at=NOW()
                FROM estudiantes e
                WHERE t.estudiante_id = e.id
                  AND t.estado = 'LLAMADO'
                  AND t.llamado_at < NOW() - make_interval(secs => %s)
                RETURNING e.codigo, t.turno_dia_id, e.push_token
                """,
                (TOLERANCIA_LLAMADO_SECONDS,),
            )
            rows = cur.fetchall()
        conn.commit()
        return [{"codigo": r[0], "turno_dia_id": r[1], "push_token": r[2]} for r in rows]
    finally:
        conn.close()


def get_turno_dias_en_servicio() -> list[int]:
    """turno_dia IDs donde ya empezó la atención (hora_inicio <= ahora <= hora_cierre)."""
    ahora = datetime.now().time()
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT td.id FROM turno_dia td
                JOIN turnos_config tc ON tc.id = td.config_id
                WHERE td.fecha   = %s
                  AND td.abierto = TRUE
                  AND tc.hora_inicio <= %s
                  AND COALESCE(td.hora_cierre, tc.hora_cierre) >= %s
                """,
                (fecha_lima(), ahora, ahora),
            )
            return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
