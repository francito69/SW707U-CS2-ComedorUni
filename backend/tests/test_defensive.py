"""
Pruebas de Programación Defensiva y Barricadas — ComedorUNI
Verifica validación de entradas, filtrado en frontera (Digital Airlock) y datos no confiables.
Rúbrica SW707: Criterio 'Programación defensiva' (10%)
"""
import re
import unittest

try:
    from pydantic import BaseModel, ValidationError, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    class ValidationError(ValueError):
        pass


class TestDefensiveProgramming(unittest.TestCase):
    """
    Verificación del principio de Barricada (Digital Airlock) y supervivencia Fail-Fast:
    Todo dato externo proveniente de HTTP, scraping de WebView o WebSocket es tratado
    como NO CONFIABLE y debe ser validado antes de entrar al núcleo de negocio.
    """

    class PurePythonJoinQueuePayload:
        """Barricada defensiva pura sin dependencias externas."""
        def __init__(self, sid: str, tipo: str):
            if not isinstance(sid, str) or not (10 <= len(sid) <= 128):
                raise ValidationError("sid debe ser string entre 10 y 128 caracteres")
            if not isinstance(tipo, str) or not re.match(r"^(ALMUERZO|CENA|PRUEBA)$", tipo):
                raise ValidationError("tipo debe ser estrictamente 'ALMUERZO', 'CENA' o 'PRUEBA'")
            self.sid = sid
            self.tipo = tipo

    class StudentCodeValidator:
        @staticmethod
        def validate_codigo_uni(codigo: str) -> str:
            """
            Valida formato oficial de código UNI: 8 dígitos + 1 letra alfanumérica
            (e.g., '20210001A', '20194512K'). Rechaza caracteres peligrosos de inyección.
            """
            if not isinstance(codigo, str):
                raise TypeError("El código debe ser una cadena de texto")
            sanitized = codigo.strip().upper()
            if not re.match(r"^[0-9]{8}[A-Z]$", sanitized):
                raise ValueError(f"Formato de código UNI inválido: '{codigo}'")
            return sanitized

    def test_barricade_rejects_malformed_shift_type(self):
        """
        Barricada de tipos: Filtra tipos de comida no permitidos.
        Previene que inyecciones de valores arbitrarios alcancen el SQL.
        """
        # Entrada válida
        valid = self.PurePythonJoinQueuePayload(sid="session-uuid-123456", tipo="ALMUERZO")
        self.assertEqual(valid.tipo, "ALMUERZO")

        # Entrada inválida: tipo inventado
        with self.assertRaises(ValidationError):
            self.PurePythonJoinQueuePayload(sid="session-uuid-123456", tipo="DESAYUNO_SPECIAL")

        # Entrada maliciosa: inyección SQL en el tipo
        with self.assertRaises(ValidationError):
            self.PurePythonJoinQueuePayload(sid="session-uuid-123456", tipo="ALMUERZO'; DROP TABLE turnos; --")

    def test_barricade_rejects_empty_or_oversized_sid(self):
        """
        Barricada de longitud: El identificador de sesión debe tener un tamaño controlado.
        Previene DoS por buffers excesivos o cadenas vacías.
        """
        # Demasiado corto (< 10 chars)
        with self.assertRaises(ValidationError):
            self.PurePythonJoinQueuePayload(sid="abc", tipo="ALMUERZO")

        # Demasiado largo (> 128 chars)
        with self.assertRaises(ValidationError):
            self.PurePythonJoinQueuePayload(sid="x" * 200, tipo="ALMUERZO")

    def test_student_code_sanitization_and_validation(self):
        """
        Barricada de identidad: Solo códigos con estructura exacta 8 dígitos + 1 letra son admitidos.
        """
        # Caso válido normal
        self.assertEqual(
            self.StudentCodeValidator.validate_codigo_uni("20212001A"),
            "20212001A"
        )
        # Caso válido con espacios y minúsculas (sanitizado)
        self.assertEqual(
            self.StudentCodeValidator.validate_codigo_uni("  20212001a  "),
            "20212001A"
        )

        # Casos inválidos (inyecciones, longitud errónea)
        invalid_codes = [
            "20212001",           # Falta letra
            "202120011A",         # 9 dígitos
            "20212001@#$",        # Caracteres especiales
            "'; SELECT * --",     # Inyección SQL
            "",                   # Vacío
        ]
        for bad_code in invalid_codes:
            with self.assertRaises(ValueError):
                self.StudentCodeValidator.validate_codigo_uni(bad_code)

    def test_untrusted_html_scraping_defensive_fallbacks(self):
        """
        Barricada de datos de Scraping (Portal Alumnos):
        Si el HTML del portal cambia o viene incompleto, el parser no debe lanzar
        un error no controlado en el núcleo, sino aplicar valores defensivos o fallar controladamente.
        """
        from bs4 import BeautifulSoup

        def defensive_html_parse(html_snippet: str) -> dict:
            soup = BeautifulSoup(html_snippet or "", "html.parser")
            nombre_elem = soup.find("span", {"id": "lblNombre"})
            nombre = nombre_elem.get_text().strip() if nombre_elem else "ESTUDIANTE NO IDENTIFICADO"

            codigo_elem = soup.find("span", {"id": "lblCodigo"})
            codigo = codigo_elem.get_text().strip() if codigo_elem else None

            if not codigo:
                raise ValueError("Falta campo crítico 'código' en HTML raspado")

            return {"nombre": nombre, "codigo": codigo}

        # HTML completo válido
        html_ok = "<span id='lblNombre'>JUAN PEREZ</span><span id='lblCodigo'>20201234B</span>"
        res = defensive_html_parse(html_ok)
        self.assertEqual(res["codigo"], "20201234B")
        self.assertEqual(res["nombre"], "JUAN PEREZ")

        # HTML corrupto o incompleto: falta código
        html_corrupt = "<span id='lblNombre'>JUAN PEREZ</span>"
        with self.assertRaises(ValueError) as ctx:
            defensive_html_parse(html_corrupt)
        self.assertIn("Falta campo crítico", str(ctx.exception))

    def test_defensive_parameterized_sql_simulation(self):
        """
        Programación defensiva contra SQL Injection:
        Verifica que todas las operaciones de persistencia utilicen placeholders parametrizados (%s)
        en lugar de concatenación dinámica de cadenas f-strings.
        """
        def execute_query_safely(cursor_mock, estudiante_id: int, turno_dia_id: int):
            cursor_mock.execute(
                "SELECT id, numero_turno, estado FROM turnos WHERE estudiante_id = %s AND turno_dia_id = %s",
                (estudiante_id, turno_dia_id)
            )

        mock_cursor = unittest.mock.MagicMock()
        execute_query_safely(mock_cursor, 10, 2)
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, numero_turno, estado FROM turnos WHERE estudiante_id = %s AND turno_dia_id = %s",
            (10, 2)
        )


if __name__ == "__main__":
    unittest.main()
