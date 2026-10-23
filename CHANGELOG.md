# Changelog — ComedorUNI

Todas las modificaciones notables de este proyecto se documentan en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere al cronograma de versiones del curso Construcción de Software II (SW707 - FIIS UNI).

## [1.0.0] — 2026-10-23 (Línea Base del Examen Parcial)

### Añadido
- **Estructura Estándar del Repositorio:** Reorganización integral en cumplimiento estricto con la **Sección 16 del Proyecto Integrador**: `src/`, `tests/`, `docs/`, `config/`, `deployment/`, `scripts/`, `benchmarks/`, `legacy/`, `Dockerfile`, `docker-compose.yml`, `README.md`, `CHANGELOG.md`, `.env.example`, `.gitignore`.
- **Arquitectura Multi-Worker (6 procesos):**
  - Soporte de 6 workers concurrentes en `run.py` y `deployment/docker-compose.prod.yml`.
  - Bus de WebSockets distribuido sobre Redis Pub/Sub (`src/shared/ws_bus.py`) para entrega de notificaciones en tiempo real independientemente del proceso Uvicorn al que esté conectado el cliente.
  - Lock distribuido con TTL (`src/shared/leader_lock.py`) para garantizar ejecución exactamente una vez de tareas periódicas (`inactivity_worker` y `active_service_worker`).
- **Modelo Arquitectónico Integral en Documentación:**
  - **Modelo C4 Completo (Niveles 1 al 4):** Diagramas y fichas técnicas para Contexto (Nivel 1), Contenedores (Nivel 2), Componentes por módulo M1 a M7 y consolidado (Nivel 3), y Despliegue/Código (Nivel 4).
  - **Modelo de Vistas 4+1 (Philippe Kruchten):** Documento formal [`docs/arquitectura-4plus1.md`](docs/arquitectura-4plus1.md) que articula Vista Lógica, Vista de Procesos, Vista de Desarrollo, Vista Física y Vista de Escenarios.
- **Suite de Pruebas Automatizadas (76 pruebas en pytest):**
  - Design by Contract (15%): `tests/test_contracts.py` (15 pruebas).
  - Programación Defensiva (10%): `tests/test_defensive.py` (23 pruebas).
  - Manejo de Errores y Excepciones (15%): `tests/test_errors_and_exceptions.py` (14 pruebas).
  - Concurrencia y Bloqueo Atómico (15%): `tests/test_concurrency.py` (5 pruebas).
  - Tolerancia a Fallas y Resiliencia (15%): `tests/test_resilience.py` (7 pruebas).
  - Reasignación y Flujo de Cola (15%): `tests/test_reasignacion.py` (7 pruebas).
  - Casos de Uso y Caracterización: `tests/test_asignar_turno.py` y `tests/test_caracterizacion_queues.py` (5 pruebas).
- **Pruebas de Carga y Rendimiento (`benchmarks/`):**
  - Entorno de benchmarks con Locust para 1000 y 2000 usuarios concurrentes (`benchmarks/locustfile.py`, `benchmarks/docker-compose.carga.yml`).
  - Verificación formal de consistencia post-carga (`benchmarks/preparar_datos.py`): cero números de turnos duplicados, cero huecos, límite estricto de raciones.

### Modificado
- **Regla de Liberación de Cola:** Quien no confirma dentro de los 3 minutos desde su llamado no frena el avance de los siguientes compañeros. Si confirma tarde pero dentro del margen, se le asigna cupo en el grupo del momento sin desplazar a quienes confirmaron a tiempo.
- **Pool de Conexiones PostgreSQL:** Configurado con `minconn = maxconn` en `src/shared/db.py` para evitar reaperturas continuas de conexiones TCP y saturación de puertos efímeros en Windows.
- **Validación de Identidad:** Verificación biométrica facial mediante DeepFace/Facenet integrada con datos institucionales extraídos del Portal Alumnos UNI.

### Corregido
- Condición de carrera por sobreventa bajo alta concurrencia mediante cerrojo transaccional estricto `SELECT ... FOR UPDATE` en `src/modules/queues/service.py`.
- Bloqueo del Event Loop de `asyncio` por operaciones síncronas de base de datos trasladando llamadas pesadas a hilos de trabajo independientes (`run_in_threadpool`).
- Agotamiento del pool de conexiones ante sobrecarga: incorporación de semáforo con tiempo de espera configurable (`DB_POOL_TIMEOUT`).
- Vulnerabilidades CVE en librerías de procesamiento de imágenes actualizando Pillow a versión 13.0.0.

---

## [0.8.0] — 2026-10-18 (Semana 6: Concurrencia y Manejo Defensivo)
- Demostración y reproducción de condición de carrera de sobreventa de raciones.
- Implementación de barricadas defensivas con Pydantic y expresiones regulares para IDs, tokens push y sanitización de HTML.
- Unificación del catálogo de excepciones de negocio (`src/shared/errores.py`) y mapeo a códigos HTTP limpios (`src/shared/http_errores.py`).

## [0.5.0] — 2026-10-11 (Semana 4: Sesión y Contratos DbC)
- Implementación de precondiciones, postcondiciones e invariantes con `shared/contratos.py` (`requiere`, `asegura`).
- Almacenamiento seguro de sesiones estudiantiles en Redis con TTL de 8 horas.
- Integración de WebView institucional para extracción de datos académicos del estudiante.

## [0.1.0] — 2026-09-20 (Semana 1: Concepción y Ficha Inicial)
- Propuesta del sistema de turnos virtuales y colas inteligentes ComedorUNI.
- Definición de problema, usuarios, actores y alcance para la UNI.
- Arquitectura inicial basada en Monolito Modular con FastAPI, PostgreSQL, Redis y RabbitMQ.
