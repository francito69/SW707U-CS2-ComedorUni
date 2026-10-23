"""
Llamado de turnos (M6): la cola avanza persona por persona.

Hay como máximo raciones_max / 10 personas LLAMADO a la vez. Quien fue
llamado y no confirma ("se quedó dormido") no frena la cola: los demás siguen
avanzando por los otros cupos. Puede confirmar hasta que se cumplan 3 minutos
desde su llamado (ahí se cancela, aunque la app siga mandando pings), y si
confirma tarde no recupera su lugar: su grupo de comedor se asigna según el
orden en que confirmó.
"""
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, Mock

import pytest

from backend.src.modules.queues import router
from backend.src.modules.queues.service import (
    cancelar_inactivos, confirmar_turno, crear_turno, turno_asignado_de,
)
from backend.src.modules.reassignment.service import llamar_siguiente


@pytest.fixture
def cola(pg, turno_dia_prueba, estudiantes):
    """Turno con 2 cupos de llamado (20 raciones / 10) y 6 personas esperando."""
    with pg.cursor() as cur:
        cur.execute("UPDATE turno_dia SET raciones_max = 20 WHERE id = %s", (turno_dia_prueba,))
    for estudiante in estudiantes(6):
        crear_turno(estudiante, turno_dia_prueba, raciones_max=20)
    return turno_dia_prueba


def _estado(pg, turno_dia_id):
    with pg.cursor() as cur:
        cur.execute("SELECT numero_turno, estado FROM turnos WHERE turno_dia_id = %s ORDER BY numero_turno",
                    (turno_dia_id,))
        return dict(cur.fetchall())


def _id(pg, turno_dia_id, numero):
    with pg.cursor() as cur:
        cur.execute("SELECT id FROM turnos WHERE turno_dia_id = %s AND numero_turno = %s", (turno_dia_id, numero))
        return cur.fetchone()[0]


def _numeros(llamados):
    return [t["numero_turno"] for t in llamados]


def test_llama_en_orden_solo_hasta_llenar_los_cupos(cola):
    assert _numeros(llamar_siguiente(cola)) == [1, 2]
    assert llamar_siguiente(cola) == []  # sin cupos libres no se llama a nadie más


def test_el_que_no_confirma_no_frena_la_cola(pg, cola):
    llamar_siguiente(cola)                                  # llama a 1 y 2
    confirmar_turno(_id(pg, cola, 2), "LLAMADO")            # 2 confirma; 1 está "dormido"
    assert _numeros(llamar_siguiente(cola)) == [3]
    confirmar_turno(_id(pg, cola, 3), "LLAMADO")
    assert _numeros(llamar_siguiente(cola)) == [4]          # la cola sigue pasando sobre 1

    estado = _estado(pg, cola)
    assert estado[1] == "LLAMADO"                           # 1 conserva su turno
    assert estado[4] == "LLAMADO"


def test_el_dormido_puede_confirmar_mientras_no_pasen_sus_3_minutos(pg, cola):
    llamar_siguiente(cola)
    confirmar_turno(_id(pg, cola, 2), "LLAMADO")
    llamar_siguiente(cola)

    assert confirmar_turno(_id(pg, cola, 1), "LLAMADO") == "ATENDIDO"


def test_quien_confirma_tarde_entra_al_grupo_del_momento_sin_mover_a_nadie(pg, cola):
    llamar_siguiente(cola)                                  # llama a 1 y 2; 1 está "dormido"
    for numero in (2, 3, 4):                                # los demás confirman y la cola avanza
        confirmar_turno(_id(pg, cola, numero), "LLAMADO")
        llamar_siguiente(cola)
    confirmar_turno(_id(pg, cola, 1), "LLAMADO")            # 1 despierta y confirma de cuarto

    grupos = {n: turno_asignado_de(_id(pg, cola, n), raciones_max=20) for n in (1, 2, 3, 4)}

    # 20 raciones -> grupos de 2: el orden de confirmación es 2, 3, 4, 1
    assert grupos == {2: 1, 3: 1, 4: 2, 1: 2}               # 1 no recupera el grupo 1


def test_a_los_3_minutos_se_cancela_aunque_la_app_mande_pings(pg, cola):
    llamar_siguiente(cola)
    with pg.cursor() as cur:
        # 1 fue llamado hace 3 min y 1 s, pero la app acaba de mandar un ping.
        cur.execute("""UPDATE turnos SET llamado_at = NOW() - INTERVAL '181 seconds', ultimo_ping = NOW()
                       WHERE turno_dia_id = %s AND numero_turno = 1""", (cola,))
        # 2 fue llamado hace 1 minuto: todavía está dentro de su plazo.
        cur.execute("""UPDATE turnos SET llamado_at = NOW() - INTERVAL '60 seconds'
                       WHERE turno_dia_id = %s AND numero_turno = 2""", (cola,))

    cancelados = [c for c in cancelar_inactivos() if c["turno_dia_id"] == cola]

    assert len(cancelados) == 1
    estado = _estado(pg, cola)
    assert estado[1] == "CANCELADO"
    assert estado[2] == "LLAMADO"
    assert _numeros(llamar_siguiente(cola)) == [3]          # su cupo pasa al siguiente


def test_llamadas_simultaneas_no_superan_los_cupos(pg, cola):
    barrera = threading.Barrier(8)

    def llamar():
        barrera.wait()
        return llamar_siguiente(cola)

    with ThreadPoolExecutor(max_workers=8) as ex:
        llamados = [t for r in ex.map(lambda _: llamar(), range(8)) for t in r]

    assert sorted(_numeros(llamados)) == [1, 2]
    assert list(_estado(pg, cola).values()).count("LLAMADO") == 2


def test_si_un_llamado_sale_de_la_cola_se_llama_al_siguiente(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", lambda sid: {"codigo": "20224085D"})
    monkeypatch.setattr(router, "get_turno_activo_por_codigo", lambda codigo: {
        "id": 7, "estado": "LLAMADO", "turno_dia_id": 1, "numero_turno": 3, "tipo": "ALMUERZO"})
    monkeypatch.setattr(router, "cancelar_turno", Mock())
    monkeypatch.setattr(router, "llamar_siguiente", Mock(return_value=[
        {"codigo": "20231172F", "numero_turno": 4, "push_token": None}]))
    aviso = AsyncMock()
    monkeypatch.setattr(router, "publish_to_session", aviso)
    monkeypatch.setattr(router, "publish", AsyncMock())

    r = client.post("/queue/leave", json={"sid": str(uuid.uuid4())})

    assert r.status_code == 200
    aviso.assert_awaited_once()
    assert aviso.await_args.args[0] == "20231172F"
