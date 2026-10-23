from dotenv import load_dotenv
load_dotenv()

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .modules.auth.router import router as auth_router
from .modules.menu.router import router as menu_router
from .modules.queues.router import router as queue_router
from .modules.config.router import router as config_router
from .modules.queues.worker import active_service_worker, inactivity_worker
from .modules.queues.manager import active_service_manager, manager as queue_manager
from .modules.queues.service import ensure_turno_dia_hoy
from .modules.notifications.consumer import start as start_m4
from .modules.tracking.consumer import start as start_m5
from .shared.ws_bus import start_ws_bus_listener


async def _start_consumers_with_retry(max_attempts: int = 30, delay: int = 3):
    """
    Arranca los consumers M4/M5 reintentando hasta que RabbitMQ esté disponible.
    Evita que un fallo de arranque (backend inicia antes que RabbitMQ) deje los
    consumers apagados de forma silenciosa — sin ellos no se envían las push.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            await start_m4()
            await start_m5()
            print("[App] Consumers RabbitMQ iniciados")
            return
        except Exception as e:
            print(f"[App] Intento {attempt}/{max_attempts}: RabbitMQ no disponible ({e}); reintento en {delay}s")
            await asyncio.sleep(delay)
    print("[App] No se pudieron iniciar los consumers tras varios intentos")


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
    except Exception as e:
        print(f"[Setup] Error creando turno_dia: {e}")
    # Cada worker de uvicorn necesita esta tarea corriendo para poder entregar
    # mensajes a estudiantes conectados a OTRO worker (ver shared/ws_bus.py).
    _spawn(start_ws_bus_listener(queue_manager, active_service_manager))
    print("[App] Listener del bus de WebSockets iniciado")
    _spawn(inactivity_worker())
    print("[App] Worker de inactividad iniciado")
    _spawn(active_service_worker())
    print("[App] Worker de active-service iniciado")
    _spawn(_start_consumers_with_retry())
    yield


app = FastAPI(title="SW603 — Sistema de Comedor UNI", lifespan=lifespan)

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
