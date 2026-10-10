import math
from typing import Optional

from ...shared.db import get_db_conn


def llamar_siguiente(turno_dia_id: int, conn=None) -> list[dict]:
    """
    Llama a todos los alumnos del siguiente turno-grupo (M6 — Reasignación).
    El grupo se determina por la posición mínima ESPERANDO y el batch_size
    (raciones_max / 10). Solo actúa si no hay nadie en LLAMADO.
    """
    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM turnos WHERE turno_dia_id=%s AND estado='LLAMADO'",
                (turno_dia_id,),
            )
            if cur.fetchone()[0] > 0:
                return []

            cur.execute(
                """
                SELECT COALESCE(td.raciones_max, tc.raciones_max)
                FROM turno_dia td
                JOIN turnos_config tc ON tc.id = td.config_id
                WHERE td.id = %s
                """,
                (turno_dia_id,),
            )
            raciones_max = (cur.fetchone() or [100])[0]
            batch_size = max(1, math.ceil(raciones_max / 10))

            cur.execute(
                "SELECT MIN(numero_turno) FROM turnos WHERE turno_dia_id=%s AND estado='ESPERANDO'",
                (turno_dia_id,),
            )
            row = cur.fetchone()
            if not row or row[0] is None:
                return []
            min_pos = row[0]

            turno_grupo = math.ceil(min_pos / batch_size)
            pos_inicio  = (turno_grupo - 1) * batch_size + 1
            pos_fin     = turno_grupo * batch_size

            cur.execute(
                """
                UPDATE turnos t SET estado='LLAMADO', llamado_at=NOW(), ultimo_ping=NOW()
                FROM estudiantes e
                WHERE t.estudiante_id = e.id
                  AND t.turno_dia_id = %s
                  AND t.numero_turno BETWEEN %s AND %s
                  AND t.estado = 'ESPERANDO'
                RETURNING t.id, t.numero_turno, e.codigo, e.push_token
                """,
                (turno_dia_id, pos_inicio, pos_fin),
            )
            llamados = [
                {"turno_id": r[0], "numero_turno": r[1], "codigo": r[2], "push_token": r[3],
                 "turno_grupo": turno_grupo}
                for r in cur.fetchall()
            ]
        _conn.commit()
        return llamados
    finally:
        if conn is None:
            _conn.close()
