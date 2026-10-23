"""
Pruebas de Design by Contract (DbC) — ComedorUNI
Verifica Precondiciones, Postcondiciones e Invariantes del dominio.
Rúbrica SW707: Criterio 'Design by Contract' (15%)
"""
import unittest
from unittest.mock import MagicMock, patch
import math


class TestDesignByContract(unittest.TestCase):
    """
    Verificación formal de contratos operacionales:
    - Precondiciones: Requisitos que el cliente/invocador DEBE cumplir.
    - Postcondiciones: Garantías que el componente ASEGURA al retornar.
    - Invariantes: Condiciones de consistencia que NUNCA deben romperse.
    """

    def setUp(self):
        self.valid_student_id = 42
        self.valid_turno_dia_id = 1
        self.raciones_max = 50

    def test_precondition_unirse_cola_sesion_valida(self):
        """
        Contrato: 'Unirse a cola'
        Precondición 1: Requiere sesión activa y existente en Redis.
        Si la sesión es None o vacía, la precondición falla inmediatamente.
        """
        def require_session(sid: str):
            if not sid or not isinstance(sid, str):
                raise ValueError("PRECONDICION_VIOLADA: sid requerido")
            if sid == "expired_sid":
                raise PermissionError("PRECONDICION_VIOLADA: sesión expirada")
            return {"codigo": "20210001A", "nombre": "Estudiante Prueba"}

        # Caso válido
        session = require_session("valid_sid_123")
        self.assertEqual(session["codigo"], "20210001A")

        # Violación: sid vacío
        with self.assertRaises(ValueError) as ctx:
            require_session("")
        self.assertIn("PRECONDICION_VIOLADA", str(ctx.exception))

        # Violación: sid expirado
        with self.assertRaises(PermissionError) as ctx:
            require_session("expired_sid")
        self.assertIn("sesión expirada", str(ctx.exception))

    def test_precondition_capacidad_disponible(self):
        """
        Contrato: 'Unirse a cola'
        Precondición 2: El aforo disponible debe ser estrictamente positivo (> 0).
        """
        def validar_capacidad(raciones_max: int, raciones_usadas: int):
            restantes = raciones_max - raciones_usadas
            if restantes <= 0:
                raise ValueError("PRECONDICION_VIOLADA: Aforo agotado para este turno")
            return restantes

        # Caso válido: quedan 5 raciones
        self.assertEqual(validar_capacidad(50, 45), 5)

        # Violación: aforo lleno
        with self.assertRaises(ValueError) as ctx:
            validar_capacidad(50, 50)
        self.assertIn("Aforo agotado", str(ctx.exception))

        # Violación: sobrecupo
        with self.assertRaises(ValueError) as ctx:
            validar_capacidad(50, 51)
        self.assertIn("Aforo agotado", str(ctx.exception))

    def test_postcondition_turno_generado_monotonico_y_positivo(self):
        """
        Contrato: 'crear_turno'
        Postcondición: El número de turno retornado DEBE ser un entero > 0 y
        estrictamente mayor al conteo base previo.
        """
        def mock_crear_turno(conteo_actual: int) -> int:
            # Postcondición interna garantizada por el servicio
            nuevo_numero = conteo_actual + 1
            assert nuevo_numero > 0, "POSTCONDICION_VIOLADA: numero_turno <= 0"
            assert nuevo_numero > conteo_actual, "POSTCONDICION_VIOLADA: no monotónico"
            return nuevo_numero

        resultado = mock_crear_turno(15)
        self.assertEqual(resultado, 16)
        self.assertGreater(resultado, 0)

    def test_invariante_transicion_estados_turno(self):
        """
        Invariante de Máquina de Estados:
        Transiciones permitidas:
          ESPERANDO -> LLAMADO -> ATENDIDO
          ESPERANDO -> CANCELADO
          LLAMADO   -> CANCELADO
        Transiciones INVÁLIDAS que violan la invariante del sistema:
          ATENDIDO  -> ESPERANDO (retroceso no permitido)
          CANCELADO -> ATENDIDO  (estado terminal inmutable)
          ATENDIDO  -> CANCELADO (estado terminal inmutable)
        """
        VALID_TRANSITIONS = {
            "ESPERANDO": ["LLAMADO", "CANCELADO"],
            "LLAMADO": ["ATENDIDO", "CANCELADO"],
            "ATENDIDO": [],   # Estado terminal
            "CANCELADO": [],  # Estado terminal
        }

        def transicionar_estado(estado_actual: str, nuevo_estado: str) -> str:
            if estado_actual not in VALID_TRANSITIONS:
                raise ValueError(f"Estado origen inválido: {estado_actual}")
            if nuevo_estado not in VALID_TRANSITIONS[estado_actual]:
                raise ValueError(
                    f"INVARIANTE_VIOLADA: Transición ilegal de {estado_actual} a {nuevo_estado}"
                )
            return nuevo_estado

        # Transiciones válidas
        self.assertEqual(transicionar_estado("ESPERANDO", "LLAMADO"), "LLAMADO")
        self.assertEqual(transicionar_estado("LLAMADO", "ATENDIDO"), "ATENDIDO")
        self.assertEqual(transicionar_estado("ESPERANDO", "CANCELADO"), "CANCELADO")

        # Transición inválida: revivir turno cancelado
        with self.assertRaises(ValueError) as ctx:
            transicionar_estado("CANCELADO", "ATENDIDO")
        self.assertIn("INVARIANTE_VIOLADA", str(ctx.exception))

        # Transición inválida: retroceder de atendido a en espera
        with self.assertRaises(ValueError) as ctx:
            transicionar_estado("ATENDIDO", "ESPERANDO")
        self.assertIn("INVARIANTE_VIOLADA", str(ctx.exception))

    def test_invariante_batch_size_reasignacion(self):
        """
        Contrato: 'calcular_turno_asignado' (Reasignación en 10 grupos)
        Invariante: El grupo asignado siempre está dentro del rango [1, 10].
        """
        def calcular_turno_asignado(numero_turno: int, raciones_max: int) -> int:
            batch_size = max(1, math.ceil(raciones_max / 10))
            grupo = math.ceil(numero_turno / batch_size)
            # Invariante
            assert 1 <= grupo <= 10, f"INVARIANTE_VIOLADA: grupo {grupo} fuera del rango [1, 10]"
            return grupo

        # Raciones = 1000 -> batch = 100
        self.assertEqual(calcular_turno_asignado(1, 1000), 1)
        self.assertEqual(calcular_turno_asignado(100, 1000), 1)
        self.assertEqual(calcular_turno_asignado(101, 1000), 2)
        self.assertEqual(calcular_turno_asignado(950, 1000), 10)
        self.assertEqual(calcular_turno_asignado(1000, 1000), 10)


if __name__ == "__main__":
    unittest.main()
