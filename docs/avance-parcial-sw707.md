# Avance de ComedorUNI y Cierre de Línea Base v1.0 (Examen Parcial)

- **Corte de Línea Base:** 23 de octubre de 2026  
- **Curso:** Construcción de Software II (SW707) — Semestre 2026-II  
- **Institución:** Universidad Nacional de Ingeniería (UNI) — FIIS  
- **Docente:** Ing. Aníbal Javier Guillén Vásquez  
- **Equipo SW707:** Franz Joe Inga Champi & Yazid Elio Fernandez Dueñas  
- **Estado Global:** **Línea Base v1.0 Completada, Auditada y Verificada al 100%**  

Este registro consolida la evolución del proyecto ComedorUNI según el cronograma oficial del curso y formaliza el congelamiento de la **Línea Base v1.0** para el Examen Parcial.

---

## 📅 Seguimiento por Semana (Cronograma Oficial SW707)

| Semana | Resultado Esperado | Evidencia Técnica Implementada | Estado |
|:---:|---|---|:---:|
| **1** | Alinear problema, equipo, alcance y propuesta. | [Ficha del sistema](ficha-del-sistema.md), justificación del problema real de colas en la UNI y delimitación del alcance en el [Documento Técnico](DocumentoTecnicoParcial.md#1-contexto-y-alcance-del-sistema). | **Completado y Aprobado** |
| **2** | Contrastar arquitectura, repositorio, runtimes y dependencias. | [Modelo C4 en 4 Niveles](c4/README.md), [ADR-001](adr/ADR-001-backend-url-configuration.md), auditoría con `pip-audit` y remediación de dependencias (Pillow 13.0.0, cero CVEs). | **Completado y Verificado** |
| **3** | Identificar fallos de runtime y definir contratos (DbC). | Corrección del puerto PostgreSQL (5433), implementación de contratos en `src/shared/contratos.py` (`@requiere`, `@asegura`) y 15 pruebas en `tests/test_contracts.py`. | **Completado y Verificado** |
| **4** | Añadir validación defensiva y comprobar entradas inválidas. | Barricadas con Pydantic, validación de UUID v4 en `sid`, sanitización de HTML del portal UNI y 23 pruebas en `tests/test_defensive.py`. | **Completado y Verificado** |
| **5** | Unificar errores, excepciones y logging estructurado. | Catálogo estructurado en `src/shared/errores.py`, mapeo a HTTP en `src/shared/http_errores.py`, logging con `request_id` (`src/shared/logs.py`) y 14 pruebas en `tests/test_errors_and_exceptions.py`. | **Completado y Verificado** |
| **6** | Corregir capacidad/numeración y demostrar concurrencia. | Bloqueo pesimista `SELECT ... FOR UPDATE` en `src/modules/queues/service.py`, eliminación de sobreventa y 5 pruebas concurrentes en `tests/test_concurrency.py` + Locust con 2000 usuarios en `benchmarks/`. | **Completado y Verificado** |
| **7** | Verificar recuperación ante fallos y preparar línea base. | Publicación desacoplada en RabbitMQ con timeouts y fallback, idempotencia en M5 (seguimiento), worker tolerante a caídas y 7 pruebas en `tests/test_resilience.py`. | **Completado y Verificado** |
| **8** | Presentar `v1.0` parcial funcional, verificable y auditada. | Integración a `main`, suite de 76 pruebas en `pytest` aprobadas (100%), C4 completo, modelo 4+1, estructura Sección 16 y etiquetado Git `v1.0`. | **Línea Base v1.0 Declarada** |

---

## 🧪 Resumen de Verificaciones Ejecutadas en esta Línea Base

- **Suite de Pruebas Automatizadas:** `python -m pytest tests` ejecutó **76 pruebas automatizadas** resultando en `76 passed` en 14.82 segundos.
  - 15 pruebas de Contratos (DbC).
  - 23 pruebas de Programación Defensiva.
  - 14 pruebas de Errores y Excepciones de Dominio.
  - 5 pruebas de Concurrencia y Bloqueo Pesimista (contra PostgreSQL real).
  - 7 pruebas de Resiliencia y Tolerancia a Fallos.
  - 7 pruebas de Reasignación y Flujo de Cola en Tiempo Real.
  - 5 pruebas de Caracterización y Asignación de Turnos.
- **Análisis Estático de Sintaxis:** `python -m compileall -q src run.py tests scripts benchmarks` finalizó con **0 errores**.
- **Acoplamiento Arquitectónico:** `python scripts/medir_acoplamiento.py` analizó el AST demostrando que no existen dependencias circulares y que los módulos mantienen una inestabilidad controlada ($I \le 0.5$).
- **Tipado Estricto de Frontend:** `cd frontend/src ; npx tsc --noEmit` completó con **0 errores de TypeScript**.
- **Linter de Frontend:** `npm run lint` validado para el core de la interfaz móvil.
- **Exportación Web:** `npx expo export --platform web` generó los bundles web estáticos sin advertencias bloqueantes.
- **Auditoría de Seguridad de Dependencias:** `pip-audit` confirmó **0 vulnerabilidades de severidad alta o crítica** tras la actualización de Pillow a la versión `13.0.0`.
- **Arquitectura Multi-Worker en Producción:** `run.py` inicializa 6 workers concurrentes de Uvicorn comunicados por el bus distribuido Redis Pub/Sub (`src/shared/ws_bus.py`) y lock distribuido con TTL (`src/shared/leader_lock.py`).

---

## ✅ Checklist de Cierre Oficial para Línea Base `v1.0`

Todos los criterios exigidos para la congelación de la línea base han sido verificados:

- [x] **Arranque reproducible:** Instrucciones claras en `README.md`, configuración unificada mediante `.env.example` y despliegue rápido con `docker compose up -d postgres redis rabbitmq`.
- [x] **Flujo de negocio de extremo a extremo:** Autenticación institucional simulada/WebView, reserva de turno, confirmación, cola inteligente y despacho por turnos.
- [x] **Contratos DbC formales:** Precondiciones y postcondiciones verificadas con `@requiere` y `@asegura` en operaciones críticas (`crear_turno`).
- [x] **Frontera transaccional atómica:** Conteo de raciones y reserva protegidos bajo `SELECT ... FOR UPDATE` dentro de la misma transacción PostgreSQL.
- [x] **Prueba de concurrencia y sobreventa:** Evidencia automatizada en `tests/test_concurrency.py` demostrando cero números duplicados, cero huecos y cero sobreventa cuando la capacidad restante es de una sola ración.
- [x] **Tolerancia a fallos:** Verificación de comportamiento ante caída de RabbitMQ y degradación controlada de la base de datos (HTTP 503 sin fuga de detalles internos en `tests/test_resilience.py`).
- [x] **Suite de pruebas automatizadas reproducibles:** 76 pruebas cubriendo la totalidad de los criterios evaluados.
- [x] **Registro y trazabilidad en Git:** Repositorio organizado según la Sección 16, Pull Request documentado, historial formal en `CHANGELOG.md` y etiquetado `v1.0` / `v1.0.0`.

---

## 🛡️ Mitigación Definitiva de Riesgos Identificados

| Riesgo Inicial (Semana 2) | Solución Implementada en Línea Base v1.0 | Estado |
|---|---|:---:|
| 1. Desajuste de puerto PostgreSQL (5432 vs 5433). | Estandarizado en `src/shared/db.py` leyendo `DB_PORT` desde `.env` (puerto 5433 en desarrollo y 5432 en Docker prod). | **Mitigado** |
| 2. Condición de carrera por sobreventa de raciones. | Se encerró el conteo de raciones dentro del bloqueo `SELECT ... FOR UPDATE` en `src/modules/queues/service.py`. | **Mitigado** |
| 3. Falta de pruebas automatizadas en el repositorio. | Se construyó una suite de 76 pruebas unitarias y de integración en `tests/`. | **Mitigado** |
| 4. Desacoplamiento y entrega en RabbitMQ. | Implementado con Topic Exchange, colas durables y publicación protegida con timeout sin revertir transacciones locales. | **Mitigado** |
| 5. WebSockets aislados a un solo proceso. | Desarrollado bus distribuido sobre Redis Pub/Sub (`src/shared/ws_bus.py`) soportando 6 workers concurrentes. | **Mitigado** |
| 6. Vulnerabilidades en dependencias. | Dependencias fijadas y auditadas con `pip-audit`. Pillow actualizado a versión 13.0.0. | **Mitigado** |
