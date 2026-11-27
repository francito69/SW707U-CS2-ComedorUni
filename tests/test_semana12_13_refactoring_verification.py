"""Pruebas de verificación para la refactorización de Semana 12 y análisis de impacto de Semana 13."""

from datetime import time
from unittest.mock import MagicMock, patch

from src.modules.queues import service as queues_service
from src.modules.queues import turno_dia_repo
from src.shared.db import use_conn


def test_use_conn_reuses_provided_connection_without_closing():
    existing_conn = MagicMock()
    with use_conn(existing_conn) as conn:
        assert conn is existing_conn
    existing_conn.close.assert_not_called()


def test_use_conn_opens_and_closes_when_none():
    pooled_conn = MagicMock()
    with patch("src.shared.db.get_db_conn", return_value=pooled_conn) as mock_get:
        with use_conn(None) as conn:
            assert conn is pooled_conn
    mock_get.assert_called_once()
    pooled_conn.close.assert_called_once()


def test_queues_service_reexports_turno_dia_repo():
    exported = [
        "fecha_lima",
        "ensure_turno_dia_hoy",
        "get_turnos_dia_activos",
        "get_turno_dia_activo",
        "active_service_payload",
        "get_turno_dia_activo_por_tipo",
        "get_turno_dia_id",
        "servicio_iniciado",
    ]
    for name in exported:
        assert getattr(queues_service, name) is getattr(turno_dia_repo, name)


def test_active_service_payload_empty_and_active():
    with patch("src.modules.queues.turno_dia_repo.get_turnos_dia_activos", return_value=[]):
        assert turno_dia_repo.active_service_payload() == {"activo": False, "turnos": []}

    sample = [
        {
            "id": 1,
            "config_id": 2,
            "tipo": "almuerzo",
            "hora_apertura": time(11, 0),
            "hora_inicio": time(12, 0),
            "hora_cierre": time(14, 30),
            "raciones_max": 500,
        }
    ]
    with patch("src.modules.queues.turno_dia_repo.get_turnos_dia_activos", return_value=sample):
        payload = turno_dia_repo.active_service_payload()
        assert payload == {
            "activo": True,
            "turnos": [
                {
                    "tipo": "almuerzo",
                    "hora_inicio": "12:00:00",
                    "hora_cierre": "14:30:00",
                }
            ],
        }
