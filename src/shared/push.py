import logging

import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
log = logging.getLogger(__name__)


async def send_push(token: str, title: str, body: str, data: dict = None) -> None:
    if not token or not token.startswith("ExponentPushToken"):
        log.warning("Push descartada: token inválido")
        return
    payload = {"to": token, "title": title, "body": body, "data": data or {}, "sound": "default"}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(EXPO_PUSH_URL, json=payload, timeout=5)
            log.info("Push enviada a %s…: Expo respondió %s", token[:22], r.status_code)
        except Exception as e:
            # Degradación elegante: sin push el turno sigue válido y la app lo ve por WebSocket.
            log.warning("No se pudo enviar la push a Expo: %s", e)
