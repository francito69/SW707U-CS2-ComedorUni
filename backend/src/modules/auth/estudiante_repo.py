from ...shared.db import get_db_conn


def upsert_estudiante(
    codigo: str,
    nombres: str,
    apellido_paterno: str,
    apellido_materno: str,
    email: str,
) -> None:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO estudiantes
                    (codigo, nombres, apellido_paterno, apellido_materno, email)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (codigo, nombres, apellido_paterno, apellido_materno, email),
            )
        conn.commit()
    finally:
        conn.close()
