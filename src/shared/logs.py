import logging
import os
import sys
from contextvars import ContextVar

# Id del request en curso; el middleware de main.py lo fija y cada línea de log
# lo incluye, así se puede seguir un request de punta a punta en el log.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configurar_logging() -> None:
    raiz = logging.getLogger()
    if any(getattr(h, "_comedor", False) for h in raiz.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler._comedor = True
    handler.addFilter(_RequestIdFilter())
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-7s [pid %(process)d] [req %(request_id)s] %(name)s: %(message)s"
    ))
    raiz.addHandler(handler)
    raiz.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
