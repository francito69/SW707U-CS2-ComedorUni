from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .shared.logs import configurar_logging

configurar_logging()

from .modules.auth.router import router as auth_router
from .modules.menu.router import router as menu_router
from .modules.queues.router import router as queue_router
from .modules.config.router import router as config_router
from .modules.queues.worker import active_service_worker, inactivity_worker
from .modules.queues.manager import active_service_manager, manager as queue_manager
from .modules.queues.service import ensure_turno_dia_hoy
from .modules.notifications.consumer import start as start_m4
from .modules.tracking.consumer import start as start_m5
from .shared.http_errores import registrar_manejo_de_errores
from .shared.ws_bus import start_ws_bus_listener

log = logging.getLogger(__name__)


async def _start_consumers_with_retry(max_attempts: int = 30, delay: int = 3) -> bool:
    """
    Arranca los consumers M4/M5 reintentando hasta que RabbitMQ esté disponible.
    Evita que un fallo de arranque (backend inicia antes que RabbitMQ) deje los
    consumers apagados de forma silenciosa — sin ellos no se envían las push.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            await start_m4()
            await start_m5()
            log.info("Consumers RabbitMQ iniciados (intento %d)", attempt)
            return True
        except Exception as e:
            log.warning("Intento %d/%d: RabbitMQ no disponible (%s); reintento en %ss",
                        attempt, max_attempts, e, delay)
            await asyncio.sleep(delay)
    log.error("No se pudieron iniciar los consumers tras %d intentos: no habrá push ni seguimiento",
              max_attempts)
    return False


# Referencias fuertes a los tasks de fondo: si no se guardan, el event loop solo
# mantiene referencias débiles y el garbage collector puede matarlos (el worker
# de inactividad dejaría de llamar turnos sin ningún error visible).
_background_tasks: set = set()


def _spawn(coro):
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_turno_dia_hoy()
    except Exception:
        log.exception("No se pudo crear el turno_dia de hoy")
    # Cada worker de uvicorn necesita esta tarea corriendo para poder entregar
    # mensajes a estudiantes conectados a OTRO worker (ver shared/ws_bus.py).
    _spawn(start_ws_bus_listener(queue_manager, active_service_manager))
    _spawn(inactivity_worker())
    _spawn(active_service_worker())
    _spawn(_start_consumers_with_retry())
    log.info("Tareas de fondo iniciadas: bus de WebSockets, worker de inactividad, active-service, consumers")
    yield


app = FastAPI(title="SW603 — Sistema de Comedor UNI", lifespan=lifespan)
registrar_manejo_de_errores(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend SW603 conectado correctamente"}


app.include_router(auth_router)
app.include_router(menu_router)
app.include_router(queue_router)
app.include_router(config_router)
