import os
from contextlib import contextmanager

import psycopg2


def get_db_conn() -> psycopg2.extensions.connection:
    host   = os.getenv("DB_HOST", "localhost")
    port   = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "comedor_uni")
    user   = os.getenv("DB_USER", "postgres")
    print(f"[DB] Conectando a {host}:{port}/{dbname} como {user}")
    return psycopg2.connect(host=host, port=port, dbname=dbname, user=user,
                            password=os.getenv("DB_PASSWORD", "postgres"))


@contextmanager
def db_conn():
    """Conexión única reutilizable dentro de un bloque with. Uso:
        with db_conn() as conn:
            resultado_a = funcion_a(conn=conn)
            resultado_b = funcion_b(conn=conn)
    """
    conn = get_db_conn()
    try:
        yield conn
    finally:
        conn.close()
