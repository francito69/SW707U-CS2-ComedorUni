import logging
import os
import threading
from contextlib import contextmanager

import psycopg2
import psycopg2.extensions
import psycopg2.pool

log = logging.getLogger(__name__)

_pool: psycopg2.pool.ThreadedConnectionPool | None = None
_pool_init_lock = threading.Lock()
# ThreadedConnectionPool lanza "pool exhausted" en vez de esperar cuando están
# todas en uso; el semáforo hace que el request espere una conexión libre.
_slots: threading.BoundedSemaphore | None = None
_SLOT_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "10"))


class _PooledConnectionProxy:
    """
    Envuelve una conexión real tomada del pool. Todo se delega a la conexión
    real vía __getattr__ (cursor(), commit(), rollback(), .closed, etc.);
    solo close() se comporta distinto: en vez de cerrar físicamente, la
    devuelve al pool para que otro request la reuse.

    Importante: NO se puede lograr esto subclaseando psycopg2.extensions.connection
    y sobreescribiendo close() ahí — el propio pool, al recibir una conexión
    con putconn(), a veces necesita cerrarla físicamente de verdad (p. ej. si
    ya hay suficientes conexiones libres) y para eso llama conn.close() sobre
    el objeto real; si ese objeto fuera nuestra subclase, esa llamada
    dispararía nuestro override de nuevo y putconn() se reentraría sobre un
    lock no reentrante. Por eso el wrapper vive por fuera, en un objeto que
    el pool nunca ve ni gestiona directamente.
    """

    __slots__ = ("_conn", "_liberada")

    def __init__(self, conn):
        object.__setattr__(self, "_conn", conn)
        object.__setattr__(self, "_liberada", False)

    def close(self) -> None:
        if object.__getattribute__(self, "_liberada"):
            return
        object.__setattr__(self, "_liberada", True)
        try:
            _get_pool().putconn(object.__getattribute__(self, "_conn"))
        finally:
            _slots.release()

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_conn"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_conn"), name, value)

    def __enter__(self):
        return object.__getattribute__(self, "_conn").__enter__()

    def __exit__(self, exc_type, exc, tb):
        return object.__getattribute__(self, "_conn").__exit__(exc_type, exc, tb)


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool, _slots
    if _pool is None:
        # Double-checked locking: sin esto, dos threads que llegan aquí a la
        # vez (típico en el arranque, con varios requests concurrentes en el
        # threadpool de FastAPI) verían _pool is None simultáneamente y cada
        # uno crearía su PROPIA instancia de ThreadedConnectionPool — solo la
        # última en asignar `global _pool` sobrevive, y las conexiones que el
        # otro thread ya tomó de su pool "perdedor" quedan huérfanas: al
        # cerrarlas, _get_pool() ya apunta a otro pool que nunca las registró
        # (PoolError: trying to put unkeyed connection).
        with _pool_init_lock:
            if _pool is None:
                host     = os.getenv("DB_HOST", "localhost")
                port     = int(os.getenv("DB_PORT", "5432"))
                dbname   = os.getenv("DB_NAME", "comedor_uni")
                user     = os.getenv("DB_USER", "postgres")
                password = os.getenv("DB_PASSWORD", "postgres")
                maxconn  = int(os.getenv("DB_POOL_MAX", "20"))
                # psycopg2 solo guarda una conexión devuelta si hay menos de
                # `minconn` libres; si no, la cierra. Con minconn bajo, casi
                # cada request abre y cierra una conexión TCP nueva.
                minconn  = int(os.getenv("DB_POOL_MIN", str(maxconn)))
                log.info("Creando pool (%d-%d) hacia %s:%s/%s como %s", minconn, maxconn, host, port, dbname, user)
                _slots = threading.BoundedSemaphore(maxconn)
                _pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn, maxconn,
                    host=host, port=port, dbname=dbname, user=user, password=password,
                )
    return _pool


def get_db_conn() -> psycopg2.extensions.connection:
    """
    Toma una conexión del pool singleton (mismo patrón que get_redis() en
    redis_store.py). El código llamador sigue haciendo conn.close() al
    terminar, tal como antes — eso ahora libera la conexión de vuelta al
    pool en vez de cerrarla físicamente.
    """
    pool = _get_pool()
    if not _slots.acquire(timeout=_SLOT_TIMEOUT):
        raise psycopg2.pool.PoolError(
            f"sin conexión libre a la base de datos tras {_SLOT_TIMEOUT:.0f}s"
        )
    try:
        conn = pool.getconn()
        if conn.closed:
            # El servidor pudo haber matado esta conexión (timeout, reinicio).
            # La descartamos del pool y pedimos una nueva.
            pool.putconn(conn, close=True)
            conn = pool.getconn()
    except Exception:
        _slots.release()
        raise
    return _PooledConnectionProxy(conn)


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
