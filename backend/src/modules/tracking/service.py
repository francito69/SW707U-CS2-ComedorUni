from ...shared.db import get_db_conn


def registrar_asistencia(estudiante_id: int, turno_dia_id: int, numero_turno: int, tipo_comida: str) -> None:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO historial_asistencia
                    (estudiante_id, turno_dia_id, numero_turno, tipo_comida)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (estudiante_id, turno_dia_id, numero_turno, tipo_comida),
            )
        conn.commit()
    finally:
        conn.close()


def registrar_encolamiento(estudiante_id: int, turno_dia_id: int, numero_turno: int, tipo_comida: str) -> None:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO historial_encolamiento
                    (estudiante_id, turno_dia_id, numero_turno, tipo_comida)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (estudiante_id, turno_dia_id, numero_turno, tipo_comida),
            )
        conn.commit()
    finally:
        conn.close()
