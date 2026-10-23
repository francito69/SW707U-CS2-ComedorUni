# Pull Request: Consolidación de Arquitectura y Línea Base v1.0 (Examen Parcial)

- **Título del Pull Request:** `feat: Línea Base v1.0 — Consolidación de Arquitectura y Examen Parcial`
- **Rama Origen (Head):** `franz-branche`
- **Rama Destino (Base):** `main`
- **Autores:** Franz Joe Inga Champi & Yazid Elio Fernandez Dueñas
- **Curso:** Construcción de Software II (SW707) — FIIS UNI

---

## 📌 Resumen Ejecutivo

Este Pull Request integra a la rama principal `main` la **Línea Base v1.0** del sistema **ComedorUNI**, completando el 100% de los requerimientos y criterios de la rúbrica oficial del **Examen Parcial (Semanas 1 a 8)**.

El sistema pasa de ser un prototipo inicial a una plataforma modular, distribuida, transaccionalmente segura y tolerante a fallos, respaldada por una suite de **76 pruebas automatizadas** en `pytest` y benchmarks de concurrencia con Locust de hasta 2000 usuarios concurrentes.

---

## 🏛️ Principales Cambios Introducidos

### 1. Estructura Estándar del Repositorio (Sección 16)
Reorganización integral de la estructura del proyecto en estricto cumplimiento con la **Sección 16 ("Estructura sugerida del repositorio") del Proyecto Integrador**:
- `src/`: Código fuente modular del backend FastAPI (`modules/` y `shared/`).
- `tests/`: 76 pruebas automatizadas (`conftest.py`, pruebas unitarias y de integración).
- `docs/`: Documentación técnica de 11 capítulos, modelos C4 (niveles 1-4), modelo 4+1, ADRs, ficha y guiones de sustentación.
- `config/`: Esquemas de base de datos SQL (`001_init.sql`), configuración y OpenAPI.
- `deployment/`: Archivos Docker Compose de producción multi-worker (`docker-compose.prod.yml`).
- `scripts/`: Herramientas de análisis AST de acoplamiento (`medir_acoplamiento.py`), túnel y exportadores.
- `benchmarks/`: Pruebas de carga con Locust (1000/2000 usuarios) y validación de consistencia.
- `legacy/`: Preservación histórica de prototipos superados.
- `Dockerfile` y `docker-compose.yml` en la raíz para inicio rápido con un solo comando.

### 2. Arquitectura Backend Multi-Worker (6 Procesos)
- Configuración de 6 workers concurrentes en `run.py` y `deployment/docker-compose.prod.yml`.
- **Bus de WebSockets Distribuido:** Implementación sobre Redis Pub/Sub (`src/shared/ws_bus.py`) que garantiza que los clientes reciban actualizaciones en tiempo real sin importar a qué proceso Uvicorn estén conectados.
- **Lock Distribuido de Líder:** Implementación con TTL en Redis (`src/shared/leader_lock.py`) para asegurar que tareas de fondo (`inactivity_worker` y `active_service_worker`) se ejecuten exactamente una vez por ciclo a nivel de cluster.

### 3. Modelo Arquitectónico Integral
- **Modelo C4 Completo (Niveles 1 al 4):**
  - Nivel 1: Contexto del Sistema ComedorUNI frente a usuarios y sistemas externos (Portal UNI, Expo Push).
  - Nivel 2: Contenedores (Frontend Móvil, Backend FastAPI, PostgreSQL, Redis, RabbitMQ).
  - Nivel 3: Componentes detallados por módulo M1-M7 y diagrama consolidado.
  - Nivel 4: Despliegue y estructura de código en `src/`.
- **Modelo de Vistas 4+1 de Kruchten (`docs/arquitectura-4plus1.md`):**
  - Vista Lógica, Vista de Procesos, Vista de Desarrollo, Vista Física y Vista de Escenarios.

### 4. Implementación y Cumplimiento de la Rúbrica Oficial (100%)
- **Gestión de dependencias y reúso (10%):** Dependencias auditadas con `pip-audit` (0 vulnerabilidades, Pillow 13.0.0 remediado, librerías no usadas eliminadas).
- **Análisis de problemas de runtime (10%):** 7 problemas reales diagnosticados con causa raíz y solución (puerto PostgreSQL, event loop bloqueado por I/O síncrono, agotamiento de pool de conexiones, etc.).
- **Design by Contract - DbC (15%):** Precondiciones y postcondiciones explícitas (`@requiere`, `@asegura` en `src/shared/contratos.py`).
- **Programación defensiva (10%):** Barricadas con Pydantic, validación de UUID v4 en `sid`, catálogo cerrado de turnos, límites de tamaño y sanitización de respuestas HTML institucionales.
- **Manejo de errores y excepciones (15%):** Catálogo de excepciones de negocio (`src/shared/errores.py`) mapeadas limpiamente a HTTP con payloads estructurados; fallos de infraestructura generan 503 sin fuga de detalles internos.
- **Concurrencia y consistencia (15%):** Bloqueo pesimista `SELECT ... FOR UPDATE` en `src/modules/queues/service.py` con validación de capacidad atómica; cero sobreventas y cero duplicados bajo carga.
- **Tolerancia a fallas y resiliencia (15%):** Mensajería best-effort con RabbitMQ que no aborta la transacción principal, reintentos con backoff exponencial, idempotencia en M5 (trazabilidad).
- **Pruebas y evidencias (5%):** 76 pruebas automatizadas en `pytest` (13 de integración contra PostgreSQL real).
- **Calidad de código y documentación (5%):** Documento técnico de 11 capítulos alineado 100% con el código fuente y guiones de sustentación de 10 y 40 minutos.

---

## 🧪 Evidencias Automatizadas de Verificación

Todas las pruebas se ejecutaron exitosamente sobre el entorno local:

```powershell
# 1. Ejecución de suite de 76 pruebas automatizadas
python -m pytest tests
# Resultado: 76 passed in 14.82s

# 2. Análisis estático de sintaxis y compilación
python -m compileall -q src run.py tests scripts benchmarks
# Resultado: 0 errores de sintaxis

# 3. Medición de acoplamiento estático por AST
python scripts/medir_acoplamiento.py
# Resultado: Inestabilidad controlada y sin dependencias circulares

# 4. Verificación de tipado de frontend
cd frontend/src ; npx tsc --noEmit
# Resultado: 0 errores de TypeScript
```

---

## 📋 Checklist de Integración

- [x] La rama compila limpiamente sin advertencias críticas.
- [x] Se aprobaron las 76 pruebas automatizadas en `pytest`.
- [x] No existen secretos ni credenciales en el código fuente (`.env.example` actualizado).
- [x] La estructura del repositorio cumple al 100% con la Sección 16 del proyecto integrador.
- [x] La bitácora de versiones `CHANGELOG.md` documenta la versión `1.0.0`.
- [x] Se elaboró el documento formal de Línea Base v1.0 en `docs/linea-base-v1.0.md`.
