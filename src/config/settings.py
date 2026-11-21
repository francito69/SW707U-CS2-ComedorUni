"""Configuración centralizada externalizada vía variables de entorno."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    tolerancia_llamado_seconds: int = int(os.getenv("TOLERANCIA_LLAMADO_SECONDS", "180"))
    inactivity_interval_seconds: int = int(os.getenv("INACTIVITY_INTERVAL_SECONDS", "60"))
    active_service_poll_seconds: int = int(os.getenv("ACTIVE_SERVICE_POLL_SECONDS", "15"))
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", str(8 * 3600)))
    grupo_divisor: int = int(os.getenv("GRUPO_DIVISOR", "10"))
    log_format: str = os.getenv("LOG_FORMAT", "text").lower()
    biometric_model: str = os.getenv("BIOMETRIC_MODEL", "Facenet")
    biometric_threshold: float = float(os.getenv("BIOMETRIC_THRESHOLD", "2.99"))


settings = Settings()
