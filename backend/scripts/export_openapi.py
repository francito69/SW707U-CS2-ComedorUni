"""Exporta el esquema OpenAPI de la app a backend/openapi.yaml.

Funciona tanto como módulo (`python -m scripts.export_openapi` desde backend/)
como ejecutando el archivo directo (`python scripts/export_openapi.py`).
"""
import sys
from pathlib import Path

import yaml

# Asegura que la carpeta backend/ (que contiene el paquete `src`) esté en el path,
# sin importar desde dónde se ejecute el script.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.main import app

OUTPUT = BACKEND_DIR / "openapi.yaml"


def main() -> None:
    schema = app.openapi()
    with OUTPUT.open("w", encoding="utf-8") as f:
        yaml.safe_dump(schema, f, sort_keys=False, allow_unicode=True)
    print(f"OpenAPI exportado a {OUTPUT}")


if __name__ == "__main__":
    main()
