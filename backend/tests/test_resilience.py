"""
Tolerancia a fallas (rúbrica: 15 %).

1. Los consumers reintentan hasta que RabbitMQ responde, y avisan si se rinden.
2. Publicar eventos es best-effort: RabbitMQ caído o colgado no hace fallar ni
   colgar el request (el turno ya quedó en Postgres).
3. Redis caído durante un aviso en tiempo real tampoco revierte la operación.
4. M5 es idempotente ante la reentrega de un mensaje (at-least-once).
5. Un ciclo fallido del worker de inactividad no lo mata.
"""
import asyncio
import logging
import time
import uuid
from unittest.mock import AsyncMock, Mock

import psycopg2
import pytest
import redis

from backend.src import main
from backend.src.modules.queues import router, worker
from backend.src.modules.tracking.service import registrar_encolamiento
from backend.src.shared import rabbitmq, ws_bus

SID = str(uuid.uuid4())


def test_consumers_reintentan_hasta_que_rabbitmq_responde(monkeypatch):
    start_m4 = AsyncMock(side_effect=[ConnectionRefusedError(), ConnectionRefusedError(), None])
    monkeypatch.setattr(main, "start_m4", start_m4)
    monkeypatch.setattr(main, "start_m5", AsyncMock())
    monkeypatch.setattr(main.asyncio, "sleep", AsyncMock())

    assert asyncio.run(main._start_consumers_with_retry(max_attempts=5, delay=0)) is True
    assert start_m4.await_count == 3


def test_consumers_se_rinden_y_lo_registran_como_error(monkeypatch, caplog):
    monkeypatch.setattr(main, "start_m4", AsyncMock(side_effect=ConnectionRefusedError()))
    monkeypatch.setattr(main.asyncio, "sleep", AsyncMock())

    with caplog.at_level(logging.WARNING):
        assert asyncio.run(main._start_consumers_with_retry(max_attempts=3, delay=0)) is False
    assert any(r.levelno == logging.ERROR and "consumers" in r.getMessage() for r in caplog.records)


def test_publish_no_propaga_la_caida_de_rabbitmq(monkeypatch, caplog):
    monkeypatch.setattr(rabbitmq, "get_connection", AsyncMock(side_effect=ConnectionRefusedError("5672")))
    monkeypatch.setattr(rabbitmq, "_publish_channel", None)

    with caplog.at_level(logging.WARNING):
        asyncio.run(rabbitmq.publish("turno.encolado", {"evento": "turno.encolado"}))
    assert "turno.encolado" in caplog.text


def test_publish_no_cuelga_el_request_si_rabbitmq_no_responde(monkeypatch):
    async def colgado(*_):
        await asyncio.sleep(30)

    monkeypatch.setattr(rabbitmq, "_publicar", colgado)
    monkeypatch.setattr(rabbitmq, "PUBLISH_TIMEOUT_SECONDS", 0.2)

    inicio = time.monotonic()
    asyncio.run(rabbitmq.publish("turno.encolado", {}))
    assert time.monotonic() - inicio < 2


def test_confirmar_responde_aunque_rabbitmq_y_redis_esten_caidos(client, monkeypatch):
    monkeypatch.setattr(router, "_confirmar_presencia", lambda sid: {
        "codigo": "20224085D",
        "turno": {"turno_dia_id": 1, "numero_turno": 4, "tipo": "ALMUERZO"},
        "nuevo_estado": "ATENDIDO",
        "estudiante_id": 10,
        "siguientes": [{"codigo": "20231172F", "numero_turno": 5, "push_token": None}],
        "turno_asignado": 1,
    })
    monkeypatch.setattr(rabbitmq, "get_connection", AsyncMock(side_effect=ConnectionRefusedError()))
    monkeypatch.setattr(rabbitmq, "_publish_channel", None)
    redis_caido = Mock()
    redis_caido.publish = AsyncMock(side_effect=redis.exceptions.ConnectionError("6379"))
    monkeypatch.setattr(ws_bus, "_get_redis", lambda: redis_caido)

    r = client.post("/queue/confirm", json={"sid": SID})

    assert r.status_code == 200
    assert r.json()["estado"] == "ATENDIDO"
    assert redis_caido.publish.await_count == 1  # se intentó avisar al siguiente


def test_m5_es_idempotente_ante_reentrega(pg, turno_dia_prueba, estudiantes):
    (estudiante,) = estudiantes(1)
    for _ in range(3):  # el broker puede reentregar el mismo evento
        registrar_encolamiento(estudiante, turno_dia_prueba, 1, "ALMUERZO")
    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM historial_encolamiento WHERE turno_dia_id = %s",
                    (turno_dia_prueba,))
        assert cur.fetchone()[0] == 1


def test_worker_de_inactividad_sobrevive_a_un_ciclo_fallido(monkeypatch):
    # Tercer sleep = fin de la prueba: corta el bucle infinito.
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock(side_effect=[None, None, asyncio.CancelledError()]))
    monkeypatch.setattr(worker, "try_acquire", AsyncMock(return_value=True))
    a_notificar = Mock(side_effect=[psycopg2.OperationalError("db caída"), []])
    monkeypatch.setattr(worker, "get_turnos_a_notificar", a_notificar)
    monkeypatch.setattr(worker, "cancelar_inactivos", Mock(return_value=[]))
    monkeypatch.setattr(worker, "get_turno_dias_en_servicio", Mock(return_value=[]))

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(worker.inactivity_worker())
    assert a_notificar.call_count == 2  # el segundo ciclo corrió tras el fallo del primero
