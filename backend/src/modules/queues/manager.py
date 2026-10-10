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
