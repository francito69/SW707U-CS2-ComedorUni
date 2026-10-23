"""
Manejo de errores y excepciones (rúbrica: 15 %).

- Condición de error (regla de negocio): 4xx con un `codigo` estable, sin traza.
- Falla de infraestructura (Postgres, Redis): 503 sin filtrar detalles internos.
- Error inesperado: 500 genérico, registrado UNA sola vez (sin log-and-throw).
Cada respuesta lleva el id del request para cruzarla con el log.
"""
import logging
import re
import uuid
from unittest.mock import Mock

import psycopg2
import psycopg2.pool
import pytest
import redis

from src.modules.queues import router
from src.shared import http_errores
from src.shared.logs import _RequestIdFilter
from src.shared.errores import (
    EstudianteNoRegistrado, SinRaciones, TurnoDuplicado, TurnoNoActivo, TurnoNoHabilitado,
)

SID = str(uuid.uuid4())
SESION = {"codigo": "20224085D"}


def _join(client, **headers):
    return client.post("/queue/join", json={"sid": SID, "tipo": "ALMUERZO"}, headers=headers)


def test_sesion_inexistente_es_401_con_codigo_estable(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", lambda sid: None)
    r = _join(client)
    assert r.status_code == 401
    assert r.json()["codigo"] == "sesion_invalida"


@pytest.mark.parametrize("error, status, codigo", [
    (TurnoNoActivo("No hay turno 'ALMUERZO' activo"), 400, "turno_no_activo"),
    (EstudianteNoRegistrado(), 404, "estudiante_no_registrado"),
    (TurnoDuplicado("Ya tienes el turno #3"), 409, "turno_duplicado"),
    (TurnoNoHabilitado(), 409, "turno_no_habilitado"),
    (SinRaciones(), 400, "sin_raciones"),
])
def test_condiciones_de_negocio_se_traducen_a_su_4xx(client, monkeypatch, error, status, codigo):
    monkeypatch.setattr(router, "_reservar_turno", Mock(side_effect=error))
    r = _join(client)
    assert r.status_code == status
    cuerpo = r.json()
    assert cuerpo["codigo"] == codigo
    assert cuerpo["detail"] == error.mensaje


def test_regla_real_turno_duplicado_llega_como_409(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", lambda sid: SESION)
    monkeypatch.setattr(router, "get_turno_dia_activo_por_tipo",
                        lambda tipo: {"tipo": "ALMUERZO", "config_id": 1, "raciones_max": 100})
    monkeypatch.setattr(router, "get_estudiante_id", lambda codigo: 10)
    monkeypatch.setattr(router, "get_turno_dia_id", lambda config_id: 5)
    monkeypatch.setattr(router, "turno_existente", lambda e, t: {"numero_turno": 3, "estado": "ESPERANDO"})
    monkeypatch.setattr(router, "crear_turno", Mock(side_effect=AssertionError("no debe crear")))

    r = _join(client)

    assert r.status_code == 409
    assert r.json()["detail"] == "Ya tienes el turno #3 (ESPERANDO)"


@pytest.mark.parametrize("falla", [
    psycopg2.OperationalError('connection to server at "10.0.0.5", port 5432 failed: '
                              'password authentication failed for user "postgres"'),
    psycopg2.pool.PoolError("sin conexión libre a la base de datos tras 10s"),
])
def test_postgres_caido_responde_503_sin_filtrar_detalles(client, monkeypatch, falla):
    monkeypatch.setattr(router, "get_session", lambda sid: SESION)
    monkeypatch.setattr(router, "get_turno_dia_activo_por_tipo", Mock(side_effect=falla))

    r = _join(client)

    assert r.status_code == 503
    assert r.json()["codigo"] == "servicio_no_disponible"
    for secreto in ("10.0.0.5", "password", "postgres", "5432", "Traceback"):
        assert secreto not in r.text


def test_redis_caido_responde_503(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", Mock(side_effect=redis.exceptions.ConnectionError("redis:6379")))
    r = client.get("/queue/status", params={"sid": SID})
    assert r.status_code == 503
    assert "6379" not in r.text


def test_error_inesperado_es_500_generico_y_se_registra_una_sola_vez(client, monkeypatch, caplog):
    monkeypatch.setattr(router, "_reservar_turno", Mock(side_effect=ZeroDivisionError("detalle interno")))

    with caplog.at_level(logging.INFO):
        r = _join(client)

    assert r.status_code == 500
    assert r.json()["codigo"] == "error_interno"
    assert "detalle interno" not in r.text
    con_traza = [rec for rec in caplog.records if rec.exc_info]
    assert len(con_traza) == 1, "la excepción debe registrarse exactamente una vez"


def test_condicion_de_negocio_no_se_registra_como_error(client, monkeypatch, caplog):
    monkeypatch.setattr(router, "_reservar_turno", Mock(side_effect=SinRaciones()))
    with caplog.at_level(logging.INFO):
        _join(client)
    assert not [rec for rec in caplog.records if rec.levelno >= logging.ERROR]


def test_cada_respuesta_lleva_request_id_y_respeta_el_del_cliente(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", lambda sid: None)

    propio = _join(client, **{"X-Request-ID": "abc123"})
    assert propio.headers["X-Request-ID"] == "abc123"
    assert propio.json()["request_id"] == "abc123"

    generado = _join(client)
    assert re.fullmatch(r"[0-9a-f]{12}", generado.headers["X-Request-ID"])


def test_el_log_del_request_lleva_su_request_id(client, monkeypatch):
    vistos = []

    class Captura(logging.Handler):
        def emit(self, record):
            vistos.append(record.request_id)

    handler = Captura()
    handler.addFilter(_RequestIdFilter())  # el mismo filtro que usa el handler real
    http_errores.log.addHandler(handler)
    nivel_previo = http_errores.log.level
    http_errores.log.setLevel(logging.INFO)
    monkeypatch.setattr(router, "_reservar_turno", Mock(side_effect=SinRaciones()))
    try:
        _join(client, **{"X-Request-ID": "traza42"})
    finally:
        http_errores.log.removeHandler(handler)
        http_errores.log.setLevel(nivel_previo)

    assert vistos == ["traza42"]
