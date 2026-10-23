from pydantic import BaseModel, Field

from ...shared.validacion import MAX_FOTO_BASE64, MAX_HTML_PORTAL, Sid


class ParseDataRequest(BaseModel):
    home_html: str = Field(default="", max_length=MAX_HTML_PORTAL)
    cursos_html: str = Field(default="", max_length=MAX_HTML_PORTAL)
    datos_html: str = Field(default="", max_length=MAX_HTML_PORTAL)
    device_id: str = Field(default="", max_length=128)  # identificador estable del dispositivo


class ParseDataResponse(BaseModel):
    sid: str
    nombre: str
    codigo: str
    email: str
    creditos_llevados: int
    session_conflict: bool = False  # ya hay una sesión activa en OTRO dispositivo


class TakeoverRequest(BaseModel):
    sid: Sid


class BiometricVerifyRequest(BaseModel):
    sid: Sid
    photo_base64: str = Field(min_length=1, max_length=MAX_FOTO_BASE64)


class BiometricVerifyResponse(BaseModel):
    verified: bool
    distance: float
    message: str


class LogoutRequest(BaseModel):
    sid: Sid
