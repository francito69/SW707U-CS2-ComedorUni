"""
Concurrencia (rúbrica: 15 %), contra PostgreSQL real.

1. Reproduce la sobreventa que aparece si el chequeo de raciones queda fuera de
   la sección crítica (lo que hacía /join antes de esta versión).
2. Verifica que crear_turno, con el chequeo bajo SELECT ... FOR UPDATE, nunca
   sobrevende ni repite números aunque muchos hilos pidan turno a la vez.
3. Verifica que un mismo estudiante no obtiene dos turnos con peticiones simultáneas.
4. Verifica que el pool de conexiones hace esperar en vez de fallar cuando se llena.
"""
import os
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import psycopg2
import psycopg2.pool
import pytest

from backend.src.modules.queues.service import crear_turno
from backend.src.shared import db
from backend.src.shared.errores import TurnoDuplicado

PG_PARAMS = dict(host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]),
                 dbname="comedor_uni", user="postgres", password="postgres")


def _en_paralelo(funciones):
    """Lanza todas las funciones a la vez (barrera) y devuelve sus resultados o excepciones."""
    barrera = threading.Barrier(len(funciones))

    def correr(f):
        barrera.wait()
        try:
            return f()
        except Exception as e:  # se devuelve para poder contarlas
            return e

    with ThreadPoolExecutor(max_workers=len(funciones)) as ex:
        return list(ex.map(correr, funciones))


def test_reproduce_sobreventa_si_el_chequeo_queda_fuera_del_candado(pg, turno_dia_prueba, estudiantes):
    raciones_max, hilos = 1, 5
    ids = estudiantes(hilos)
    leyeron = threading.Barrier(hilos)

    def reservar_sin_candado(estudiante_id, numero):
        conn = psycopg2.connect(**PG_PARAMS)
        try:
            with conn, conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM turnos WHERE turno_dia_id = %s AND estado != 'CANCELADO'",
                            (turno_dia_prueba,))
                quedan = raciones_max - cur.fetchone()[0]
                leyeron.wait()  # fuerza el intercalado: todos leen antes de que alguien inserte
                if quedan > 0:
                    cur.execute("INSERT INTO turnos (estudiante_id, turno_dia_id, numero_turno) VALUES (%s, %s, %s)",
                                (estudiante_id, turno_dia_prueba, numero))
        finally:
            conn.close()

    _en_paralelo([lambda i=i, n=n: reservar_sin_candado(i, n) for n, i in enumerate(ids, 1)])

    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM turnos WHERE turno_dia_id = %s", (turno_dia_prueba,))
        asignados = cur.fetchone()[0]
    assert asignados == hilos > raciones_max  # 5 turnos para 1 ración: la carrera es real


def test_crear_turno_no_sobrevende_con_40_hilos_por_10_raciones(pg, turno_dia_prueba, estudiantes):
    ids = estudiantes(40)

    resultados = _en_paralelo([lambda i=i: crear_turno(i, turno_dia_prueba, raciones_max=10) for i in ids])

    tipos = Counter(type(r).__name__ for r in resultados)
    assert tipos == {"TurnoCreado": 10, "SinRaciones": 30}
    numeros = sorted(r.numero for r in resultados if not isinstance(r, Exception))
    assert numeros == list(range(1, 11))  # sin duplicados ni huecos
    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM turnos WHERE turno_dia_id = %s", (turno_dia_prueba,))
        assert cur.fetchone()[0] == 10


def test_mismo_estudiante_en_paralelo_obtiene_un_solo_turno(turno_dia_prueba, estudiantes):
    (unico,) = estudiantes(1)

    resultados = _en_paralelo([lambda: crear_turno(unico, turno_dia_prueba, raciones_max=100)] * 10)

    assert sum(not isinstance(r, Exception) for r in resultados) == 1
    assert all(isinstance(r, TurnoDuplicado) for r in resultados if isinstance(r, Exception))


class _PoolFalso:
    def getconn(self):
        return type("Conn", (), {"closed": False})()

    def putconn(self, conn, close=False):
        pass


def test_pool_lleno_hace_esperar_y_falla_solo_tras_el_timeout(monkeypatch):
    monkeypatch.setattr(db, "_pool", _PoolFalso())
    monkeypatch.setattr(db, "_slots", threading.BoundedSemaphore(1))
    monkeypatch.setattr(db, "_SLOT_TIMEOUT", 0.2)

    ocupada = db.get_db_conn()
    with pytest.raises(psycopg2.pool.PoolError, match="sin conexión libre"):
        db.get_db_conn()

    # Si la conexión se libera mientras otro espera, ese otro la recibe.
    liberador = threading.Timer(0.05, ocupada.close)
    liberador.start()
    monkeypatch.setattr(db, "_SLOT_TIMEOUT", 2)
    segunda = db.get_db_conn()
    segunda.close()
    liberador.join()


def test_cerrar_dos_veces_no_libera_dos_cupos(monkeypatch):
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(db, "_pool", _PoolFalso())
    monkeypatch.setattr(db, "_slots", slots)

    conn = db.get_db_conn()
    conn.close()
    conn.close()  # BoundedSemaphore lanzaría ValueError si se liberara de más
    assert slots.acquire(blocking=False)
