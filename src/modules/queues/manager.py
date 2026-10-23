import logging

from fastapi import WebSocket

log = logging.getLogger(__name__)


class QueueConnectionManager:
    def __init__(self):
        # codigo -> WebSocket
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, codigo: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[codigo] = ws
        log.debug("WS de cola: %s conectado, %d en este worker", codigo, len(self._connections))

    def disconnect(self, codigo: str) -> None:
        self._connections.pop(codigo, None)
        log.debug("WS de cola: %s desconectado", codigo)

    def is_connected(self, codigo: str) -> bool:
        return codigo in self._connections

    async def send(self, codigo: str, message: dict) -> None:
        ws = self._connections.get(codigo)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(codigo)


manager = QueueConnectionManager()


class ActiveServiceConnectionManager:
    """
    Conexiones públicas (sin sesión) al estado de turnos activos.
    A diferencia de QueueConnectionManager, aquí no hay `codigo` — cualquiera
    que abra la pantalla de inicio se suscribe para enterarse en vivo cuando
    se abre/cierra el almuerzo o la cena.
    """

    def __init__(self):
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        log.debug("WS active-service conectado, %d en este worker", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        log.debug("WS active-service desconectado, %d en este worker", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        for ws in list(self._connections):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)


active_service_manager = ActiveServiceConnectionManager()
