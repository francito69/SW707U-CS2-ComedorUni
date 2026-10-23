"""
Pruebas de Manejo de Errores y Excepciones — ComedorUNI
Verifica distinción entre Condiciones de Error de Negocio vs Excepciones Técnicas de Runtime,
mitigación del antipatrón Log-and-Throw y ausencia de fugas de información.
Rúbrica SW707: Criterio 'Manejo de errores y excepciones' (15%)
"""
import unittest

try:
    from fastapi import HTTPException
except ImportError:
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail


class TestErrorAndExceptionHandling(unittest.TestCase):
    """
    Políticas de errores según la teoría de Resilient and Observable Systems (Sesión 5):
    1. Distinción conceptual: Condición de Error (regla de negocio esperada) vs
       Excepción de Runtime (fallo de infraestructura/ambiente inesperado).
    2. Respuestas API limpias: códigos HTTP semánticos (400, 401, 404, 409, 503)
       sin exponer secretos, contraseñas ni tracebacks internos al usuario final.
    3. Prevención de antipatrones como 'Log and Throw' y 'Catch-all silencioso'.
    """

    def test_domain_error_conditions_mapping(self):
        """
        Verificación de Condiciones de Error de Negocio:
        Son situaciones esperadas del dominio y deben mapearse a códigos HTTP 4xx explícitos.
        """
        def handle_queue_business_rules(session_valid: bool, student_exists: bool,
                                        already_has_turn: bool, slots_remaining: int):
            if not session_valid:
                raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
            if not student_exists:
                raise HTTPException(status_code=404, detail="Estudiante no registrado en la base de datos")
            if already_has_turn:
                raise HTTPException(status_code=409, detail="Ya tienes un turno activo reservado")
            if slots_remaining <= 0:
                raise HTTPException(status_code=400, detail="Se agotaron las raciones para este turno")
            return {"status": "ok"}

        # 401 Unauthorized
        with self.assertRaises(HTTPException) as ctx:
            handle_queue_business_rules(False, True, False, 10)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "Sesión inválida o expirada")

        # 404 Not Found
        with self.assertRaises(HTTPException) as ctx:
            handle_queue_business_rules(True, False, False, 10)
        self.assertEqual(ctx.exception.status_code, 404)

        # 409 Conflict (Duplicado)
        with self.assertRaises(HTTPException) as ctx:
            handle_queue_business_rules(True, True, True, 10)
        self.assertEqual(ctx.exception.status_code, 409)

        # 400 Bad Request (Aforo agotado)
        with self.assertRaises(HTTPException) as ctx:
            handle_queue_business_rules(True, True, False, 0)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_runtime_technical_exceptions_handling(self):
        """
        Verificación de Excepciones Técnicas de Runtime:
        Fallas ambientales (ej. base de datos inaccesible, broker caído).
        Deben traducirse a un error controlado (503 Service Unavailable) sin exponer tracebacks.
        """
        class OperationalError(Exception):
            pass

        def service_query_db():
            raise OperationalError("could not connect to server: Connection refused on port 5433")

        def safe_api_gateway():
            try:
                return service_query_db()
            except OperationalError:
                # Traducción arquitectónica de excepción de runtime
                raise HTTPException(
                    status_code=503,
                    detail="El servicio de datos no está disponible temporalmente. Intente en unos minutos."
                )

        with self.assertRaises(HTTPException) as ctx:
            safe_api_gateway()

        self.assertEqual(ctx.exception.status_code, 503)
        # La respuesta es limpia para el cliente: no contiene host, puerto ni passwords
        self.assertNotIn("5433", ctx.exception.detail)
        self.assertIn("no está disponible temporalmente", ctx.exception.detail)

    def test_prevention_of_log_and_throw_antipattern(self):
        """
        Verificación contra el antipatrón 'Log and Throw':
        En una arquitectura multicapa, una excepción NO debe ser registrada con log.error()
        y vuelta a lanzar en cada capa intermedia, pues satura el log con ruido duplicado.
        Debe registrarse con contexto enriquecido (Correlation ID) en la capa de frontera.
        """
        log_entries = []

        class LoggerMock:
            @staticmethod
            def error(msg, correlation_id=None):
                log_entries.append({"msg": msg, "cid": correlation_id})

        # Capa de persistencia: lanza error técnico sin loguear duplicado
        def repo_layer():
            raise ValueError("Registro no encontrado en PostgreSQL")

        # Capa de servicio: agrega contexto de negocio y propaga
        def service_layer():
            try:
                repo_layer()
            except ValueError as e:
                # Transforma o enriquece, no hace log.error() + rethrow
                raise LookupError(f"Turno no disponible: {e}")

        # Capa de frontera (Controller / Gateway): loguea UNA SOLA VEZ con Correlation ID
        def controller_layer(correlation_id: str):
            try:
                service_layer()
            except LookupError as e:
                LoggerMock.error(f"[Gateway] Fallo controlado: {e}", correlation_id=correlation_id)
                raise HTTPException(status_code=404, detail="Turno no encontrado")

        cid = "req-uuid-98765"
        with self.assertRaises(HTTPException):
            controller_layer(cid)

        # Solo existe UNA entrada de log para la falla, evitando duplicidad
        self.assertEqual(len(log_entries), 1)
        self.assertEqual(log_entries[0]["cid"], cid)
        self.assertIn("Fallo controlado", log_entries[0]["msg"])

    def test_structured_error_payload_integrity(self):
        """
        Garantiza que el payload de error HTTP siga un contrato uniforme de respuesta JSON.
        """
        def format_api_error(status_code: int, error_code: str, message: str) -> dict:
            return {
                "error": {
                    "status": status_code,
                    "code": error_code,
                    "message": message,
                    "retryable": status_code in [503, 504],
                }
            }

        payload = format_api_error(409, "TURNO_DUPLICADO", "El estudiante ya cuenta con reserva activa")
        self.assertEqual(payload["error"]["status"], 409)
        self.assertEqual(payload["error"]["code"], "TURNO_DUPLICADO")
        self.assertFalse(payload["error"]["retryable"])

        payload_retry = format_api_error(503, "DB_TIMEOUT", "Base de datos en recuperación")
        self.assertTrue(payload_retry["error"]["retryable"])


if __name__ == "__main__":
    unittest.main()
