"""
Frontera de errores HTTP: el único lugar donde una excepción se registra y se
convierte en respuesta. Las capas de abajo solo lanzan; aquí se loguea una vez.

- ErrorDeDominio           -> su status 4xx, sin traza (es un flujo esperado)
- Postgres / Redis caídos  -> 503, traza en el log, mensaje genérico al cliente
- Cualquier otra excepción -> 500, traza en el log, mensaje genérico al cliente
"""
import logging
import uuid

import psycopg2
import psycopg2.pool
import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .errores import ErrorDeDominio
from .logs import request_id_var

log = logging.getLogger(__name__)

ERRORES_DE_INFRAESTRUCTURA = (
    psycopg2.OperationalError,
    psycopg2.InterfaceError,
    psycopg2.pool.PoolError,
    redis.exceptions.ConnectionError,
    redis.exceptions.TimeoutError,
)


def _respuesta(status: int, detalle: str, codigo: str) -> JSONResponse:
    rid = request_id_var.get()
    return JSONResponse(
        status_code=status,
        content={"detail": detalle, "codigo": codigo, "request_id": rid},
        headers={"X-Request-ID": rid},
    )


async def _error_de_dominio(request: Request, exc: ErrorDeDominio) -> JSONResponse:
    log.info("%s %s -> %s (%s)", request.method, request.url.path, exc.status_code, exc.codigo)
    return _respuesta(exc.status_code, exc.mensaje, exc.codigo)


async def _error_de_infraestructura(request: Request, exc: Exception) -> JSONResponse:
    log.error("%s %s -> 503, dependencia no disponible", request.method, request.url.path, exc_info=exc)
    return _respuesta(503, "Servicio temporalmente no disponible, intenta en unos segundos",
                      "servicio_no_disponible")


def registrar_manejo_de_errores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorDeDominio, _error_de_dominio)
    for tipo in ERRORES_DE_INFRAESTRUCTURA:
        app.add_exception_handler(tipo, _error_de_infraestructura)

    @app.middleware("http")
    async def request_id_y_errores_inesperados(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        except Exception:
            # Un handler de Starlette para Exception re-lanza la excepción y el
            # servidor la vuelve a imprimir; aquí se registra una sola vez.
            log.exception("%s %s -> 500, error no controlado", request.method, request.url.path)
            response = _respuesta(500, "Error interno del servidor", "error_interno")
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response
