from pydantic import BaseModel


class ParseDataRequest(BaseModel):
    home_html: str = ""
    cursos_html: str = ""
    datos_html: str = ""
    device_id: str = ""            # identificador estable del dispositivo


class ParseDataResponse(BaseModel):
    sid: str
    nombre: str
    codigo: str
    email: str
    creditos_llevados: int
    session_conflict: bool = False  # ya hay una sesión activa en OTRO dispositivo


class TakeoverRequest(BaseModel):
    sid: str


class BiometricVerifyRequest(BaseModel):
    sid: str
    photo_base64: str


class BiometricVerifyResponse(BaseModel):
    verified: bool
    distance: float
    message: str


class LogoutRequest(BaseModel):
    sid: str
