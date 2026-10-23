# Línea Base de Configuración: Versión 1.0 (Examen Parcial)

| Metadato | Detalle Oficial |
|---|---|
| **Identificador de Línea Base** | `LB-PARCIAL-v1.0` |
| **Etiqueta Git (Tag)** | [`v1.0`](https://github.com/francito69/SW707U-CS2-ComedorUni/releases/tag/v1.0) / `v1.0.0` |
| **Rama Principal de Integración** | `main` |
| **Rama de Desarrollo / Origen** | `franz-branche` |
| **Fecha de Congelamiento (Baseline Freeze)** | 23 de octubre de 2026 |
| **Curso / Semestre** | SW707 Construcción de Software II — Semestre 2026-II |
| **Institución** | Universidad Nacional de Ingeniería (UNI) — Facultad de Ingeniería Industrial y de Sistemas (FIIS) |
| **Docente** | Ing. Aníbal Javier Guillén Vásquez |
| **Equipo de Desarrollo** | Franz Joe Inga Champi & Yazid Elio Fernandez Dueñas |
| **Estado de Auditoría** | **Aprobado / Auditado (100% Rúbrica Parcial)** |

---

## 1. Definición y Propósito de la Línea Base

En Gestión de Configuración del Software (**SCM** según estándar **IEEE 828** y **CMMI**), una **Línea Base (Baseline)** es una especificación o producto que ha sido formalmente revisado y acordado en un hito del ciclo de vida, que sirve como base para el desarrollo posterior, y que solo puede modificarse mediante procedimientos formales de control de cambios.

La **Línea Base v1.0** formaliza el cierre del hito del **Examen Parcial (Semanas 1 a 8)** del sistema **ComedorUNI**. Esta línea base congela el diseño arquitectónico, el código fuente funcional del backend y frontend, el esquema transaccional de base de datos, la suite completa de 76 pruebas automatizadas y el cuerpo documental de arquitectura (C4 y 4+1).

---

## 2. Elementos de Configuración de Software (ECS / Configuration Items)

Los siguientes Elementos de Configuración de Software (ECS) quedan formalmente congelados e inventariados bajo la Línea Base `v1.0`:

| Código ECS | Elemento de Configuración | Ubicación en el Repositorio | Descripción y Rol en la Línea Base |
|---|---|---|---|
| **ECS-01** | Backend Modular Asíncrono | `src/`, `run.py` | API FastAPI con arquitectura multi-worker (6 procesos concurrentes), bus WebSocket distribuido sobre Redis (`src/shared/ws_bus.py`) y lock distribuido con TTL (`src/shared/leader_lock.py`). |
| **ECS-02** | Frontend Móvil y Web | `frontend/` | Aplicación React Native con Expo Router 54 y TypeScript estricto. Incluye integración con WebView del Portal Alumnos UNI y sincronización en tiempo real por WebSockets. |
| **ECS-03** | Persistencia Transaccional | `config/001_init.sql`, `src/shared/db.py` | Esquema relacional en PostgreSQL 15. Incluye índices únicos parciales contra turnos duplicados y aislamiento transaccional pesimista `SELECT ... FOR UPDATE` para evitar sobreventa de raciones. |
| **ECS-04** | Broker de Mensajería | `src/shared/rabbitmq.py`, `src/modules/notifications/`, `src/modules/tracking/` | RabbitMQ 3 con Topic Exchange `comedor` y colas durables para despacho desacoplado de notificaciones (M4) y seguimiento histórico idempotente (M5). |
| **ECS-05** | Coordinación y Sesiones | `src/modules/auth/redis_store.py` | Redis 7 como almacén de sesiones de usuario (`sid`) con TTL de 8 horas, invalidación concurrente entre dispositivos y bus Pub/Sub. |
| **ECS-06** | Suite de Pruebas Automatizadas | `tests/` | 76 pruebas automatizadas en `pytest` cubriendo Design by Contract, programación defensiva, excepciones de negocio, concurrencia y resiliencia ante caídas de infraestructura. |
| **ECS-07** | Banco de Carga y Rendimiento | `benchmarks/` | Suite con Locust para pruebas de sobrecarga con 1000 y 2000 usuarios concurrentes, junto con scripts de validación post-ejecución (`benchmarks/preparar_datos.py`). |
| **ECS-08** | Modelos de Arquitectura C4 | `docs/c4/` | Especificación C4 en Structurizr DSL (`workspace.dsl`) y diagramas generados para Niveles 1 (Contexto), 2 (Contenedores), 3 (Componentes M1 a M7) y 4 (Despliegue/Código). |
| **ECS-09** | Modelo de Vistas 4+1 | `docs/arquitectura-4plus1.md` | Documentación formal bajo el modelo de Philippe Kruchten: Vista Lógica, Vista de Procesos, Vista de Desarrollo, Vista Física y Escenarios. |
| **ECS-10** | Documento Técnico Oficial | `docs/DocumentoTecnicoParcial.md` | Documento de 11 capítulos que cubre los 8 criterios de la rúbrica oficial al 100%, problemas de runtime, dependencias auditadas y métricas. |
| **ECS-11** | Infraestructura como Código | `deployment/`, `docker-compose.yml`, `Dockerfile` | Configuración de Docker Compose para entornos de desarrollo local y de producción multi-worker aislados en red interna. |
| **ECS-12** | Scripts de Métricas y Acoplamiento | `scripts/` | Medición estática de acoplamiento eferente ($C_e$), aferente ($C_a$) e inestabilidad ($I$) mediante análisis AST de Python (`medir_acoplamiento.py`). |

---

## 3. Matriz de Cumplimiento y Auditoría de la Rúbrica (100%)

| Criterio Evaluado | Ponderación | Estado en Línea Base v1.0 | Evidencia Técnica Comprobable |
|---|:---:|:---:|---|
| **Gestión de dependencias y reúso** | **10%** | **Auditado y Cumplido** | `requirements.txt` con versiones fijadas; auditado con `pip-audit` (0 vulnerabilidades, Pillow 13.0.0 remediado); librería sin uso removida. |
| **Análisis de problemas de runtime** | **10%** | **Auditado y Cumplido** | 7 problemas diagnosticados y corregidos (puerto 5433, event loop síncrono, OpenCV, agotamiento de conexiones DB con semáforo). Logs unificados con `request_id`. |
| **Design by Contract (DbC)** | **15%** | **Auditado y Cumplido** | Precondiciones y postcondiciones con decoradores `@requiere` y `@asegura` en `src/shared/contratos.py`. 15 pruebas unitarias en `tests/test_contracts.py`. |
| **Programación defensiva** | **10%** | **Auditado y Cumplido** | Barricadas con Pydantic, validación de UUID v4 en `sid`, lista cerrada de tipos de turno, límites de payload y sanitización de HTML del portal UNI. 23 pruebas en `tests/test_defensive.py`. |
| **Manejo de errores y excepciones** | **15%** | **Auditado y Cumplido** | Catálogo unificado de excepciones de dominio (`src/shared/errores.py`) mapeadas limpiamente a códigos HTTP en `src/shared/http_errores.py`. Errores 503 ante fallos de infraestructura sin filtrar datos sensibles. 14 pruebas en `tests/test_errors_and_exceptions.py`. |
| **Concurrencia** | **15%** | **Auditado y Cumplido** | Cerrojo pesimista transaccional `SELECT ... FOR UPDATE` en `src/modules/queues/service.py` con conteo de raciones atómico. 5 pruebas en `tests/test_concurrency.py` + prueba Locust con 2000 usuarios en `benchmarks/`. |
| **Tolerancia a fallas** | **15%** | **Auditado y Cumplido** | Publicación RabbitMQ desacoplada sin revertir transacción principal, reintentos con backoff, idempotencia en M5 (Seguimiento), worker autónomo tolerante a fallos. 7 pruebas en `tests/test_resilience.py`. |
| **Pruebas y evidencias** | **5%** | **Auditado y Cumplido** | 76 pruebas automatizadas en `pytest` (13 de integración contra PostgreSQL real). 0 fallos. |
| **Calidad de código y documentación** | **5%** | **Auditado y Cumplido** | Cumplimiento estricto de la Sección 16 del repositorio, Documento Técnico de 11 capítulos, modelo C4 en 4 niveles, modelo 4+1 y guiones de sustentación. |
| **TOTAL** | **100%** | **LÍNEA BASE APROBADA** | **76/76 Tests Passed — 100% Rúbrica Oficial** |

---

## 4. Ejecución de la Línea Base en Git

Para registrar formalmente esta línea base en el sistema de control de versiones Git, se ejecutó el siguiente procedimiento:

### A. Fusión controlada hacia `main` (Merge via Pull Request)
1. Integración de la rama de trabajo `franz-branche` en la rama principal `main` mediante un Pull Request formal con evidencias de prueba y checklist de aceptación.
2. Verificación de que no existan conflictos ni divergencias entre ramas.

### B. Etiquetado Anotado en Git (Annotated Tagging)
Se generó la etiqueta anotada e inmutable `v1.0` (y el alias SemVer `v1.0.0`) sobre el commit de cierre en la rama `main`:
```powershell
git tag -a v1.0 -m "Línea Base v1.0: Examen Parcial SW707 ComedorUNI - Versión congelada y auditada"
git tag -a v1.0.0 -m "Release v1.0.0: Línea Base del Examen Parcial ComedorUNI"
git push origin v1.0
git push origin v1.0.0
```

### C. Verificación de Integridad por Terceros
Cualquier evaluador o integrante del equipo puede situarse de forma determinística en el estado exacto de esta línea base ejecutando:
```powershell
git checkout v1.0
```
Y para verificar las 76 pruebas de la línea base:
```powershell
python -m pytest tests
```

---

## 5. Procedimiento de Control de Cambios Post-Línea Base (Hacia la Entrega Final v2.0)

A partir de la declaración de la Línea Base `v1.0`:

1. **Inmutabilidad de `main` en `v1.0`:** No se permiten commits directos sobre la etiqueta `v1.0`.
2. **Nuevas Funcionalidades:** Todo desarrollo hacia la entrega final (reconocimiento facial con DeepFace en producción, panel administrativo web, integración física con torniquetes IoT) debe iniciarse en ramas derivadas del tipo `feat/...` o `release/v2.0`.
3. **Solicitudes de Cambio (RFC / PR):** Cualquier modificación requerirá la creación obligatoria de un Pull Request con descripción de impacto, pruebas automatizadas correspondientes y revisión técnica antes de su integración a `main`.
