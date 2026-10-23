import math

from ...shared.db import get_db_conn


def llamar_siguiente(turno_dia_id: int, conn=None) -> list[dict]:
    """
    Llama a las siguientes personas de la cola (M6 — Reasignación).

    Hay como máximo `cupos` personas LLAMADO a la vez (raciones_max / 10). Cada
    vez que alguien confirma, sale o vence, se libera su cupo y se llama a la
    siguiente persona en orden. Quien fue llamado y no responde ocupa solo su
    propio cupo hasta que vence a los 3 minutos (cancelar_inactivos): la cola
    sigue avanzando por los demás cupos, no espera por esa persona.
    """
    _conn = conn or get_db_conn()
    try:
        with _conn.cursor() as cur:
            # Mismo candado que crear_turno: dos confirmaciones simultáneas no
            # pueden calcular los mismos cupos libres y llamar de más.
            cur.execute(
                """
                SELECT COALESCE(td.raciones_max, tc.raciones_max)
                FROM turno_dia td
                JOIN turnos_config tc ON tc.id = td.config_id
                WHERE td.id = %s
                FOR UPDATE OF td
                """,
                (turno_dia_id,),
            )
            fila = cur.fetchone()
            if fila is None:
                _conn.rollback()
                return []
            cupos = max(1, math.ceil(fila[0] / 10))

            cur.execute(
                "SELECT COUNT(*) FROM turnos WHERE turno_dia_id = %s AND estado = 'LLAMADO'",
                (turno_dia_id,),
            )
            libres = cupos - cur.fetchone()[0]
            if libres <= 0:
                _conn.rollback()
                return []

            cur.execute(
                """
                UPDATE turnos t SET estado = 'LLAMADO', llamado_at = NOW(), ultimo_ping = NOW()
                FROM estudiantes e
                WHERE t.estudiante_id = e.id
                  AND t.id IN (
                      SELECT id FROM turnos
                      WHERE turno_dia_id = %s AND estado = 'ESPERANDO'
                      ORDER BY numero_turno
                      LIMIT %s
                  )
                RETURNING t.id, t.numero_turno, e.codigo, e.push_token
                """,
                (turno_dia_id, libres),
            )
            llamados = sorted(
                ({"turno_id": r[0], "numero_turno": r[1], "codigo": r[2], "push_token": r[3]}
                 for r in cur.fetchall()),
                key=lambda t: t["numero_turno"],
            )
        _conn.commit()
        return llamados
    finally:
        if conn is None:
            _conn.close()
