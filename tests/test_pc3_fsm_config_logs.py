"""Pruebas unitarias para los componentes agregados en PC3 (FSM, Config/Flags, Logs JSON)."""
import json
import logging

import pytest

from src.config import get_all_flags, is_enabled, set_flag, settings
from src.modules.queues.domain.fsm import (
    TRANSICIONES,
    EstadoTurno,
    EventoTurno,
    TransicionInvalidaError,
    transicionar,
)
from src.shared.logs import JsonFormatter, request_id_var


def test_fsm_transiciones_validas():
    assert len(TRANSICIONES) == 7
    assert transicionar(EstadoTurno.ESPERANDO, EventoTurno.LLAMAR).nuevo_estado == EstadoTurno.LLAMADO
    assert transicionar(EstadoTurno.ESPERANDO, EventoTurno.PING).actualizar_ping is True
    assert transicionar(EstadoTurno.LLAMADO, EventoTurno.CONFIRMAR_PRESENCIA).nuevo_estado == EstadoTurno.ATENDIDO
    assert transicionar(EstadoTurno.LLAMADO, EventoTurno.EXPIRAR_INACTIVIDAD).nuevo_estado == EstadoTurno.CANCELADO


@pytest.mark.parametrize(
    "estado,evento",
    [
        (EstadoTurno.ESPERANDO, EventoTurno.CONFIRMAR_PRESENCIA),
        (EstadoTurno.ATENDIDO, EventoTurno.SALIR),
        (EstadoTurno.CANCELADO, EventoTurno.LLAMAR),
        ("DESCONOCIDO", EventoTurno.PING),
    ],
)
def test_fsm_transiciones_invalidas(estado, evento):
    with pytest.raises(TransicionInvalidaError):
        transicionar(estado, evento)


def test_config_y_feature_flags():
    assert settings.tolerancia_llamado_seconds > 0
    assert settings.grupo_divisor == 10
    flags = get_all_flags()
    assert "enable_biometric_verify" in flags
    set_flag("enable_biometric_verify", False)
    assert is_enabled("enable_biometric_verify") is False
    set_flag("enable_biometric_verify", True)
    assert is_enabled("enable_biometric_verify") is True


def test_json_formatter_incluye_request_id():
    token = request_id_var.set("req-pc3-123")
    try:
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="comedor.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="evento de prueba",
            args=(),
            exc_info=None,
        )
        record.request_id = request_id_var.get()
        data = json.loads(formatter.format(record))
        assert data["level"] == "INFO"
        assert data["request_id"] == "req-pc3-123"
        assert data["msg"] == "evento de prueba"
    finally:
        request_id_var.reset(token)
