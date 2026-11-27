"""Feature flags en tiempo de ejecución (con overrides por entorno y API)."""
import os

_DEFAULT_FLAGS: dict[str, bool] = {
    "enable_turno_prueba": os.getenv("FLAG_ENABLE_TURNO_PRUEBA", "true").lower() == "true",
    "enable_biometric_verify": os.getenv("FLAG_ENABLE_BIOMETRIC_VERIFY", "true").lower() == "true",
    "enable_push_notifications": os.getenv("FLAG_ENABLE_PUSH_NOTIFICATIONS", "true").lower() == "true",
    "enable_inactivity_auto_cancel": os.getenv("FLAG_ENABLE_INACTIVITY_AUTO_CANCEL", "true").lower() == "true",
}

_runtime_flags: dict[str, bool] = dict(_DEFAULT_FLAGS)


def is_enabled(flag_name: str) -> bool:
    """Devuelve True si el feature flag está activo."""
    return _runtime_flags.get(flag_name, False)


def set_flag(flag_name: str, enabled: bool) -> dict[str, bool]:
    """Actualiza un feature flag en runtime y devuelve el estado completo."""
    if flag_name not in _runtime_flags:
        raise KeyError(f"Feature flag desconocido: {flag_name}")
    _runtime_flags[flag_name] = bool(enabled)
    return dict(_runtime_flags)


def get_all_flags() -> dict[str, bool]:
    """Devuelve una copia de todos los feature flags actuales."""
    return dict(_runtime_flags)
