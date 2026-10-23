"""
Configuración común de las pruebas.

- Unitarias: corren sin infraestructura (TestClient sin lifespan, dependencias
  externas reemplazadas con monkeypatch).
- Integración (fixture `pg`): usan el Postgres aislado de tests/carga
  (puerto 5434). Si no está levantado, se saltan con el comando para levantarlo.
  Cada prueba crea su propio turno y sus estudiantes y los borra al terminar.
"""
import os
import sys
import types
import uuid

import psycopg2
import pytest

# La base de pruebas se fija ANTES de importar la app: el pool lee el entorno
# al crearse y load_dotenv() no pisa variables ya definidas.
os.environ["DB_HOST"] = os.getenv("TEST_DB_HOST", "localhost")
os.environ["DB_PORT"] = os.getenv("TEST_DB_PORT", "5434")
os.environ["DB_NAME"] = "comedor_uni"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "postgres"

# DeepFace importa TensorFlow (varios segundos y GB de RAM); ninguna prueba lo necesita.
if "deepface" not in sys.modules:
    _fake = types.ModuleType("deepface")

    class _DeepFace:
        @staticmethod
        def verify(**_):
            return {"verified": True, "distance": 0.1, "threshold": 0.8}

    _fake.DeepFace = _DeepFace
    sys.modules["deepface"] = _fake

from fastapi.testclient import TestClient  # noqa: E402

from backend.src.main import app  # noqa: E402

PG_PARAMS = dict(host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]),
                 dbname="comedor_uni", user="postgres", password="postgres")


@pytest.fixture
def client():
    # Sin `with`: no corre el lifespan (workers, consumers), solo las rutas.
    return TestClient(app)


@pytest.fixture(scope="session")
def pg():
    try:
        conn = psycopg2.connect(connect_timeout=2, **PG_PARAMS)
    except psycopg2.OperationalError:
        pytest.skip("Postgres de pruebas no disponible: "
                    "docker compose -f backend/tests/carga/docker-compose.carga.yml up -d")
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture
def turno_dia_prueba(pg):
    """Crea un turno propio (config + turno_dia de hoy) y lo borra al terminar."""
    tipo = f"T{uuid.uuid4().hex[:10]}"
    with pg.cursor() as cur:
        cur.execute(
            """INSERT INTO turnos_config (tipo, hora_apertura, hora_inicio, hora_cierre, raciones_max)
               VALUES (%s, '00:00', '00:00', '23:59', 1000) RETURNING id""", (tipo,))
        config_id = cur.fetchone()[0]
        cur.execute("INSERT INTO turno_dia (config_id, raciones_max) VALUES (%s, 1000) RETURNING id",
                    (config_id,))
        turno_dia_id = cur.fetchone()[0]
    yield turno_dia_id
    with pg.cursor() as cur:
        for tabla in ("historial_encolamiento", "historial_asistencia", "turnos"):
            cur.execute(f"DELETE FROM {tabla} WHERE turno_dia_id = %s", (turno_dia_id,))
        cur.execute("DELETE FROM turno_dia WHERE id = %s", (turno_dia_id,))
        cur.execute("DELETE FROM turnos_config WHERE id = %s", (config_id,))


@pytest.fixture
def estudiantes(pg):
    """Fábrica: estudiantes(n) inserta n estudiantes y devuelve sus ids."""
    creados = []

    def crear(n: int) -> list[int]:
        ids = []
        with pg.cursor() as cur:
            for _ in range(n):
                codigo = f"TEST{uuid.uuid4().hex[:12]}"
                cur.execute(
                    """INSERT INTO estudiantes (codigo, nombres, apellido_paterno)
                       VALUES (%s, 'Prueba', 'Test') RETURNING id""", (codigo,))
                ids.append(cur.fetchone()[0])
        creados.extend(ids)
        return ids

    yield crear
    if creados:
        with pg.cursor() as cur:
            for tabla in ("historial_encolamiento", "historial_asistencia", "turnos"):
                cur.execute(f"DELETE FROM {tabla} WHERE estudiante_id = ANY(%s)", (creados,))
            cur.execute("DELETE FROM estudiantes WHERE id = ANY(%s)", (creados,))
