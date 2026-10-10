from fastapi import WebSocket


class SessionConnectionManager:
    """
    Conexiones de sesión indexadas por `sid` (una por dispositivo).
    A diferencia del manager de cola (indexado por `codigo`), aquí cada
    dispositivo tiene su propia entrada, lo que permite expulsar a uno en
    concreto cuando otro toma la sesión.
    """
    def __init__(self):
        self._by_sid: dict[str, WebSocket] = {}

    async def connect(self, sid: str, ws: WebSocket) -> None:
        await ws.accept()
        self._by_sid[sid] = ws
        print(f"[Session] {sid[:8]}… conectado — {len(self._by_sid)} sesión(es) activa(s)")

    def disconnect(self, sid: str) -> None:
        self._by_sid.pop(sid, None)

    async def revoke(self, sid: str, mensaje: str = "Tu sesión se cerró porque iniciaste en otro dispositivo.") -> None:
        """Notifica al dispositivo viejo que fue expulsado y cierra su conexión."""
        ws = self._by_sid.pop(sid, None)
        if ws:
            try:
                await ws.send_json({"type": "session_revoked", "mensaje": mensaje})
                await ws.close(code=4002)
            except Exception:
                pass


session_manager = SessionConnectionManager()
