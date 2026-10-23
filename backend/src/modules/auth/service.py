import logging
import re

from bs4 import BeautifulSoup

from ...shared.errores import DatosPortalInvalidos
from ...shared.validacion import CODIGO_UNI_PATTERN

BASE_URL = "https://alumnos.uni.edu.pe"
log = logging.getLogger(__name__)


def parse_student_data(home_html: str, cursos_html: str, datos_html: str = "") -> dict:
    """
    Extrae los datos del estudiante del HTML del Portal Alumnos (dato no confiable).
    Los campos cosméticos (nombre, créditos) tienen valor por defecto; el código de
    alumno no: sin un código UNI válido no hay identidad y se rechaza el login.
    """
    log.info("/parse-data: home=%d, cursos=%d, datos=%d caracteres",
             len(home_html), len(cursos_html), len(datos_html))

    # Nombre desde home
    soup_home = BeautifulSoup(home_html, "html.parser")
    apellidos_el = soup_home.select_one(".user-status")
    nombres_el = soup_home.select_one(".user-name.fw-bolder")
    apellidos_raw    = apellidos_el.get_text(strip=True).title() if apellidos_el else ""
    nombres          = nombres_el.get_text(strip=True).title()   if nombres_el   else ""
    partes           = apellidos_raw.split()
    apellido_paterno = partes[0]              if len(partes) >= 1 else "No encontrado"
    apellido_materno = " ".join(partes[1:])   if len(partes) >= 2 else ""
    nombre           = f"{nombres} {apellidos_raw}".strip() or "No encontrado"

    # Código, email y foto desde datos personales
    soup_datos = BeautifulSoup(datos_html, "html.parser")
    codigo_input = soup_datos.find("input", {"id": "txt-codigo"})
    email_input = soup_datos.find("input", {"id": "txt-mail-uni"})
    codigo = (codigo_input.get("value") or "").strip().upper() if codigo_input else ""
    if not re.fullmatch(CODIGO_UNI_PATTERN, codigo):
        # Antes se guardaba "No encontrado" como código: todos los logins con HTML
        # roto terminaban compartiendo la misma identidad y la misma sesión.
        raise DatosPortalInvalidos(
            "No se pudo leer tu código de alumno desde el Portal UNI. Vuelve a iniciar sesión."
        )
    email = email_input.get("value", "No encontrado") if email_input else "No encontrado"

    foto_base64 = _extract_profile_photo(soup_datos)

    log.info("Datos del portal leídos: código %s, foto %s", codigo, "sí" if foto_base64 else "no")

    # Créditos desde cursos: suma de la tabla, solo cursos con Condición "Normal"
    soup_cursos = BeautifulSoup(cursos_html, "html.parser")
    creditos = _sum_creditos_normales(soup_cursos)

    return {
        "nombre": nombre,
        "nombres": nombres,
        "apellido_paterno": apellido_paterno,
        "apellido_materno": apellido_materno,
        "codigo": codigo,
        "email": email,
        "creditos_llevados": creditos,
        "foto_base64": foto_base64,
    }


def _sum_creditos_normales(soup: BeautifulSoup) -> int:
    """
    Recorre la tabla de cursos y suma los créditos de los cursos cuya
    Condición es "Normal" (excluye Retiro parcial, etc.). Localiza las columnas
    de Créditos y Condición por el encabezado, para no depender del orden fijo.
    """
    total = 0
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.select("thead th")]
        if not headers:
            continue

        def _col(substr: str) -> int:
            for i, h in enumerate(headers):
                if substr in h:
                    return i
            return -1

        i_cred = _col("dit")     # "créditos" / "creditos"
        i_cond = _col("condic")  # "condición" / "condicion"
        if i_cred == -1 or i_cond == -1:
            continue  # no es la tabla de cursos

        for tr in table.select("tbody tr"):
            tds = tr.find_all("td")
            if len(tds) <= max(i_cred, i_cond):
                continue
            condicion = tds[i_cond].get_text(strip=True).lower()
            if "normal" not in condicion:
                continue
            try:
                total += int(tds[i_cred].get_text(strip=True))
            except ValueError:
                pass
        return total  # tabla de cursos encontrada y procesada

    log.warning("No se encontró la tabla de cursos para sumar créditos")
    return total


def _extract_profile_photo(soup: BeautifulSoup) -> str:
    """Extrae el base64 de la foto de perfil del HTML de datos-personales."""
    img = soup.select_one("img.img-fluid.rounded")
    if img:
        src = img.get("src", "")
        if src.startswith("data:image") and "," in src:
            return src.split(",", 1)[1]
    return ""
