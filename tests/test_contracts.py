"""
Design by Contract (rúbrica: 15 %).

Verifica las precondiciones, postcondiciones e invariantes que el código
declara con shared/contratos.py, sobre las funciones reales del sistema.
"""
import uuid

import pytest

from src.modules.queues import router, service
from src.modules.queues.service import calcular_turno_asignado, crear_turno
from src.shared.contratos import asegura, requiere
from src.shared.errores import ContratoViolado, SinRaciones


def nuevo_sid() -> str:
    return str(uuid.uuid4())


def test_requiere_y_asegura_lanzan_contrato_violado_con_el_motivo():
    requiere(True, "nunca falla")
    asegura(True, "nunca falla")
    with pytest.raises(ContratoViolado, match="Precondición violada: x > 0"):
        requiere(False, "x > 0")
    with pytest.raises(ContratoViolado, match="Postcondición violada: total cuadra"):
        asegura(False, "total cuadra")


@pytest.mark.parametrize("estudiante_id, turno_dia_id, raciones_max", [
    (0, 1, 10), (-5, 1, 10), (1, 0, 10), (1, 1, 0),
])
def test_precondicion_crear_turno_rechaza_argumentos_invalidos_sin_tocar_la_base(
        monkeypatch, estudiante_id, turno_dia_id, raciones_max):
    monkeypatch.setattr(service, "get_db_conn", lambda: pytest.fail("no debe abrir conexión"))
    with pytest.raises(ContratoViolado, match="Precondición"):
        crear_turno(estudiante_id, turno_dia_id, raciones_max)


def test_postcondicion_numeros_consecutivos_y_raciones_restantes(turno_dia_prueba, estudiantes):
    ids = estudiantes(3)
    creados = [crear_turno(i, turno_dia_prueba, raciones_max=10) for i in ids]
    assert [c.numero for c in creados] == [1, 2, 3]
    assert [c.raciones_restantes for c in creados] == [9, 8, 7]


def test_invariante_de_aforo_nunca_se_supera(pg, turno_dia_prueba, estudiantes):
    a, b, c = estudiantes(3)
    crear_turno(a, turno_dia_prueba, raciones_max=2)
    crear_turno(b, turno_dia_prueba, raciones_max=2)
    with pytest.raises(SinRaciones):
        crear_turno(c, turno_dia_prueba, raciones_max=2)
    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM turnos WHERE turno_dia_id = %s AND estado != 'CANCELADO'",
                    (turno_dia_prueba,))
        assert cur.fetchone()[0] == 2


def test_un_turno_cancelado_libera_su_racion(pg, turno_dia_prueba, estudiantes):
    a, b = estudiantes(2)
    primero = crear_turno(a, turno_dia_prueba, raciones_max=1)
    with pg.cursor() as cur:
        cur.execute("UPDATE turnos SET estado = 'CANCELADO' WHERE turno_dia_id = %s AND numero_turno = %s",
                    (turno_dia_prueba, primero.numero))
    segundo = crear_turno(b, turno_dia_prueba, raciones_max=1)
    assert segundo.numero == primero.numero + 1  # los números no se reciclan


@pytest.mark.parametrize("raciones_max", [1, 7, 10, 95, 5000])
def test_invariante_turno_asignado_siempre_entre_1_y_10(raciones_max):
    grupos = {calcular_turno_asignado(n, raciones_max) for n in range(1, raciones_max + 1)}
    assert min(grupos) == 1
    assert max(grupos) <= 10


def test_contrato_confirm_rechaza_turno_ya_finalizado(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", lambda sid: {"codigo": "20224085D"})
    monkeypatch.setattr(router, "get_turno_activo_por_codigo",
                        lambda codigo: {"id": 7, "estado": "CANCELADO", "turno_dia_id": 1,
                                        "numero_turno": 3, "tipo": "ALMUERZO"})
    monkeypatch.setattr(router, "confirmar_turno",
                        lambda *a: pytest.fail("no debe confirmar un turno cancelado"))

    r = client.post("/queue/confirm", json={"sid": nuevo_sid()})

    assert r.status_code == 400
    assert r.json()["codigo"] == "turno_finalizado"


def test_contrato_confirm_sin_turno_responde_404(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", lambda sid: {"codigo": "20224085D"})
    monkeypatch.setattr(router, "get_turno_activo_por_codigo", lambda codigo: None)

    r = client.post("/queue/confirm", json={"sid": nuevo_sid()})

    assert r.status_code == 404
    assert r.json()["codigo"] == "sin_turno_activo"
