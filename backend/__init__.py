"""
Capa de compatibilidad retroactiva para scripts o imports que utilicen backend.src
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import src  # noqa: F401
