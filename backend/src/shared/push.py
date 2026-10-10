import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_push(token: str, title: str, body: str, data: dict = None) -> None:
    print(f"[Push] Enviando a token: {token}")
    if not token or not token.startswith("ExponentPushToken"):
        print(f"[Push] Token inválido, descartando")
        return
    payload = {"to": token, "title": title, "body": body, "data": data or {}, "sound": "default"}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(EXPO_PUSH_URL, json=payload, timeout=5)
            print(f"[Push] Respuesta Expo: {r.status_code} {r.text}")
        except Exception as e:
            print(f"[Push] Error enviando notificación: {e}")
