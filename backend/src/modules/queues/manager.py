from fastapi import WebSocket


class QueueConnectionManager:
    def __init__(self):
        # codigo -> WebSocket
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, codigo: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[codigo] = ws
        print(f"[WS] {codigo} conectado — {len(self._connections)} conexión(es) activa(s)")

    def disconnect(self, codigo: str) -> None:
        self._connections.pop(codigo, None)
        print(f"[WS] {codigo} desconectado")

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
        print(f"[WS] active-service conectado — {len(self._connections)} conexión(es) activa(s)")

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        print(f"[WS] active-service desconectado — {len(self._connections)} conexión(es) activa(s)")

    async def broadcast(self, message: dict) -> None:
        for ws in list(self._connections):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)


active_service_manager = ActiveServiceConnectionManager()
