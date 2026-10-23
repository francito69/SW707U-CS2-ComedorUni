"""
Programación defensiva (rúbrica: 10 %).

Todo dato externo (cuerpo HTTP, query string, HTML del Portal UNI) se valida en
la frontera antes de llegar a la lógica de negocio o a la base de datos.
"""
import pathlib
import re
import uuid
from unittest.mock import Mock

import pytest

from backend.src.modules.auth import router as auth_router
from backend.src.modules.auth.service import parse_student_data
from backend.src.modules.queues import router
from backend.src.shared.errores import DatosPortalInvalidos
from backend.src.shared.validacion import MAX_FOTO_BASE64

SID = str(uuid.uuid4())


@pytest.fixture
def reservar(monkeypatch):
    """Espía de la lógica de /join: si la barricada funciona, nunca se llama."""
    espia = Mock(side_effect=AssertionError("la petición inválida llegó al servicio"))
    monkeypatch.setattr(router, "_reservar_turno", espia)
    return espia


@pytest.mark.parametrize("tipo", [
    "DESAYUNO_SPECIAL",
    "ALMUERZO'; DROP TABLE turnos; --",
    "almuerzo",
    "",
])
def test_join_rechaza_tipos_fuera_de_la_lista_blanca(client, reservar, tipo):
    r = client.post("/queue/join", json={"sid": SID, "tipo": tipo})
    assert r.status_code == 422
    reservar.assert_not_called()


@pytest.mark.parametrize("sid", [
    "abc",
    "x" * 200,
    "carga-CARGA00001",
    "' OR 1=1 --",
    "00000000-0000-1000-8000-000000000000",  # UUID, pero no v4: no lo genera /parse-data
])
def test_join_rechaza_sid_que_no_es_uuid4(client, reservar, sid):
    r = client.post("/queue/join", json={"sid": sid, "tipo": "ALMUERZO"})
    assert r.status_code == 422
    reservar.assert_not_called()


def test_status_rechaza_sid_malformado_en_query_string(client, monkeypatch):
    monkeypatch.setattr(router, "get_session", Mock(side_effect=AssertionError("no debe consultar Redis")))
    r = client.get("/queue/status", params={"sid": "' OR 1=1 --"})
    assert r.status_code == 422


@pytest.mark.parametrize("largo", [0, MAX_FOTO_BASE64 + 1], ids=["vacia", "mayor_al_tope"])
def test_biometrico_rechaza_foto_vacia_o_demasiado_grande(client, monkeypatch, largo):
    monkeypatch.setattr(auth_router, "compare_faces", Mock(side_effect=AssertionError("no debe comparar")))
    r = client.post("/verify-biometric", json={"sid": SID, "photo_base64": "A" * largo})
    assert r.status_code == 422


def test_push_token_no_puede_exceder_la_columna_de_la_base(client, monkeypatch):
    monkeypatch.setattr(router, "save_push_token", Mock(side_effect=AssertionError("no debe guardar")))
    r = client.post("/queue/register-push-token", json={"sid": SID, "push_token": "x" * 256})
    assert r.status_code == 422


def _html_datos(codigo: str) -> str:
    return f"<input id='txt-codigo' value='{codigo}'><input id='txt-mail-uni' value='a@uni.pe'>"


@pytest.mark.parametrize("datos_html", [
    "",                                   # el portal no devolvió la página
    "<html><body>Mantenimiento</body></html>",
    _html_datos(""),
    _html_datos("No encontrado"),
    _html_datos("2022408D"),              # 7 dígitos
    _html_datos("20224085D OR 1=1"),
    _html_datos("20224085D<script>"),
])
def test_parser_rechaza_html_sin_codigo_uni_valido(datos_html):
    with pytest.raises(DatosPortalInvalidos):
        parse_student_data("", "", datos_html)


def test_parser_normaliza_un_codigo_valido():
    assert parse_student_data("", "", _html_datos("  20224085d "))["codigo"] == "20224085D"


def test_parse_data_con_html_roto_no_crea_estudiante_ni_sesion(client, monkeypatch):
    monkeypatch.setattr(auth_router, "upsert_estudiante", Mock(side_effect=AssertionError("no debe guardar")))
    monkeypatch.setattr(auth_router, "create_session", Mock(side_effect=AssertionError("no debe crear sesión")))

    r = client.post("/parse-data", json={"home_html": "", "cursos_html": "", "datos_html": "<p>error</p>"})

    assert r.status_code == 422
    assert r.json()["codigo"] == "datos_portal_invalidos"


def test_ninguna_consulta_sql_se_arma_concatenando_texto():
    """Toda consulta usa parámetros (%s); armar SQL con f-strings o % abre la puerta a inyección."""
    src = pathlib.Path(__file__).resolve().parents[1] / "src"
    peligrosas = re.compile(r"""execute\(\s*(f["']|["'][^"']*["']\s*(%|\.format))""")
    hallazgos = [
        f"{p.relative_to(src)}:{n}"
        for p in src.rglob("*.py")
        for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if peligrosas.search(linea)
    ]
    assert hallazgos == []
