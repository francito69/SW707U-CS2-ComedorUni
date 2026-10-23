"""
Errores del sistema, separados en dos familias:

- ErrorDeDominio: condiciones de error esperadas por el negocio (sesión vencida,
  turno duplicado, sin raciones...). Se traducen a un 4xx con un `codigo`
  estable que el cliente puede interpretar.
- ContratoViolado: una precondición o postcondición del propio código no se
  cumplió. Es un bug, no una regla de negocio: se responde 500 y se registra.

Las fallas de infraestructura (Postgres, Redis caídos) no tienen clase propia:
se reconocen por su tipo en shared/http_errores.py y se responden con 503.
"""


class ErrorDeDominio(Exception):
    status_code = 400
    codigo = "error_de_dominio"

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class SesionInvalida(ErrorDeDominio):
    status_code = 401
    codigo = "sesion_invalida"

    def __init__(self, mensaje: str = "Sesión inválida o expirada"):
        super().__init__(mensaje)


class DatosPortalInvalidos(ErrorDeDominio):
    status_code = 422
    codigo = "datos_portal_invalidos"


class EstudianteNoRegistrado(ErrorDeDominio):
    status_code = 404
    codigo = "estudiante_no_registrado"

    def __init__(self, mensaje: str = "Estudiante no registrado en la base de datos"):
        super().__init__(mensaje)


class TurnoNoActivo(ErrorDeDominio):
    status_code = 400
    codigo = "turno_no_activo"


class TurnoNoHabilitado(ErrorDeDominio):
    status_code = 409
    codigo = "turno_no_habilitado"

    def __init__(self, mensaje: str = "El turno de hoy aún no fue habilitado por el administrador"):
        super().__init__(mensaje)


class TurnoDuplicado(ErrorDeDominio):
    status_code = 409
    codigo = "turno_duplicado"


class SinRaciones(ErrorDeDominio):
    status_code = 400
    codigo = "sin_raciones"

    def __init__(self, mensaje: str = "Se agotaron las raciones para este turno"):
        super().__init__(mensaje)


class SinTurnoActivo(ErrorDeDominio):
    status_code = 404
    codigo = "sin_turno_activo"


class TurnoFinalizado(ErrorDeDominio):
    status_code = 400
    codigo = "turno_finalizado"


class ContratoViolado(AssertionError):
    """Precondición, postcondición o invariante incumplida: indica un bug."""
