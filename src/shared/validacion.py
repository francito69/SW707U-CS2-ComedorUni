"""Tipos validados en la frontera HTTP: todo dato externo pasa por aquí."""
from typing import Annotated, Literal

from pydantic import StringConstraints

# /parse-data entrega str(uuid.uuid4()): cualquier otra forma no es un sid nuestro.
UUID4_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
Sid = Annotated[str, StringConstraints(pattern=UUID4_PATTERN)]

TipoTurno = Literal["ALMUERZO", "CENA", "PRUEBA"]

# Código de alumno UNI: 8 dígitos y una letra (p. ej. 20224085D).
CODIGO_UNI_PATTERN = r"^[0-9]{8}[A-Z]$"

# Topes de tamaño para no aceptar cuerpos arbitrariamente grandes.
MAX_HTML_PORTAL = 5_000_000
MAX_FOTO_BASE64 = 8_000_000
