"""
Pruebas de Concurrencia y Condiciones de Carrera — ComedorUNI
Reproduce y verifica escenarios de colisión en tiempo de ejecución:
1. Carrera de aforo crítico (N hilos compitiendo por la última ración disponible).
2. Demostración de sobreventa (overbooking) sin sincronización vs asignación atómica con mutex.
3. Unicidad de turno por estudiante ante peticiones paralelas simultáneas.
Rúbrica SW707: Criterio 'Concurrencia' (15%)
"""
import threading
import time
import unittest


class TestConcurrencyScenarios(unittest.TestCase):
    """
    Verificación del comportamiento bajo concurrencia (Sesión 6):
    - Detección de fallos de interleaving en memoria compartida.
    - Demostración reproducible de la condición de carrera en aforo.
    - Validación de soluciones transaccionales mediante sección crítica atómica.
    """

    def test_reproduce_race_condition_unsynchronized_overbooking(self):
        """
        DEMOSTRACIÓN DE LA FALLA: Sin sincronización atómica entre lectura y escritura.
        Escenario: Queda exactamente 1 ración (capacidad = 10, usadas = 9).
        5 estudiantes solicitan turno en el mismo milisegundo.
        Resultado esperado del fallo: Múltiples hilos leen 'restantes = 1' y ambos se encolan,
        provocando SOBREVENTA (overbooking) y superando el aforo de 10.
        """
        capacidad_max = 10
        raciones_usadas = 9
        turnos_asignados = []

        def unsynchronized_join_queue(estudiante_id: int):
            nonlocal raciones_usadas
            # 1. Lectura fuera de sección crítica (Interleaving vulnerable)
            restantes = capacidad_max - raciones_usadas
            time.sleep(0.005)  # Simula latencia de red/I/O donde ocurre el cambio de contexto

            # 2. Decisión basada en estado rancio (stale state)
            if restantes > 0:
                # 3. Escritura no atómica
                raciones_usadas += 1
                turnos_asignados.append(estudiante_id)

        threads = []
        barrier = threading.Barrier(5)

        def worker(eid):
            barrier.wait()  # Sincroniza arranque exacto de los 5 hilos
            unsynchronized_join_queue(eid)

        for i in range(1, 6):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Evidencia de la condición de carrera:
        # Debido al interleaving, más de 1 hilo logró ingresar a pesar de haber solo 1 vacante
        self.assertGreater(
            len(turnos_asignados), 1,
            "La condición de carrera debió provocar que más de 1 estudiante obtuviera turno"
        )
        self.assertGreater(
            raciones_usadas, capacidad_max,
            "Se evidenció overbooking: raciones asignadas superaron la capacidad máxima"
        )

    def test_synchronized_atomic_check_and_reserve_prevents_overbooking(self):
        """
        DEMOSTRACIÓN DE LA SOLUCIÓN: Sección crítica atómica (emulando SELECT ... FOR UPDATE).
        Escenario: Queda exactamente 1 ración (capacidad = 10, usadas = 9).
        10 hilos concurrentes compiten simultáneamente.
        Resultado requerido:
        - Exactamente 1 hilo obtiene el turno con éxito.
        - Los 9 hilos restantes son rechazados por aforo agotado.
        - El aforo final no supera jamás la capacidad máxima (invariante preservada).
        """
        capacidad_max = 10
        raciones_usadas = 9
        db_mutex = threading.Lock()  # Representa el bloqueo FOR UPDATE en PostgreSQL

        exitos = []
        rechazos = []

        def synchronized_join_queue(estudiante_id: int):
            nonlocal raciones_usadas
            # Sección crítica atómica: lectura y reserva bajo el mismo cerrojo
            with db_mutex:
                restantes = capacidad_max - raciones_usadas
                if restantes <= 0:
                    rechazos.append(estudiante_id)
                    return False
                # Reserva atómica dentro de la sección protegida
                raciones_usadas += 1
                exitos.append(estudiante_id)
                return True

        threads = []
        barrier = threading.Barrier(10)

        def worker(eid):
            barrier.wait()  # Lanzamiento simultáneo
            synchronized_join_queue(eid)

        for i in range(1, 11):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verificación estricta de invariantes de negocio
        self.assertEqual(len(exitos), 1, "Solo exactamente 1 solicitud debió ser admitida")
        self.assertEqual(len(rechazos), 9, "Las 9 solicitudes restantes debieron ser rechazadas")
        self.assertEqual(raciones_usadas, capacidad_max, "El total final debe ser exactamente el límite")

    def test_unique_active_ticket_per_student_under_concurrency(self):
        """
        Verificación de Invariante de Unicidad de Estudiante:
        Un mismo estudiante envía 5 peticiones simultáneas para el mismo turno diario.
        El sistema debe admitir como máximo 1 sola reserva y rechazar los 4 duplicados restantes.
        """
        student_tickets = {}
        ticket_lock = threading.Lock()
        admitidos = []
        rechazados_duplicado = []

        def request_ticket_for_student(estudiante_id: int, request_id: int):
            with ticket_lock:
                if estudiante_id in student_tickets:
                    rechazados_duplicado.append(request_id)
                    return
                # Asigna turno y registra unicidad
                student_tickets[estudiante_id] = request_id
                admitidos.append(request_id)

        threads = []
        barrier = threading.Barrier(5)

        def worker(req_id):
            barrier.wait()
            request_ticket_for_student(estudiante_id=1001, request_id=req_id)

        for req in range(5):
            t = threading.Thread(target=worker, args=(req,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(admitidos), 1, "Solo una solicitud del mismo estudiante debe prosperar")
        self.assertEqual(len(rechazados_duplicado), 4, "Las otras 4 deben rechazarse como duplicadas")


if __name__ == "__main__":
    unittest.main()
