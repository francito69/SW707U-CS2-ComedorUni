from typing import Dict

# Almacén en memoria de sesiones activas: sid -> { "cookies": {...} }
sessions: Dict[str, dict] = {}
