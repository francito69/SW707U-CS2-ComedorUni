# Avance de ComedorUNI hasta el examen parcial

**Corte:** Octubre de 2026  
**Curso:** Construcción de Software II (SW707)  
**Equipo SW707:** Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas  

Este registro aplica el cronograma del [Proyecto Integrador](Proyecto_Integrador_SW707.docx) al repositorio del sistema. Los estados distinguen análisis documentado de implementación y verificación con pruebas automatizadas.

---

## 1. Seguimiento por Semana (Semanas 1 a 8)

| Semana | Resultado que se busca | Evidencia Actual | Estado |
|:---:|---|---|:---:|
| **1** | Alinear problema, equipo, alcance y propuesta. | [Ficha del sistema](ficha-del-sistema.md) define problema, alcance y equipo; propuesta aprobada en setiembre de 2026. | **Completado** |
| **2** | Contrastar arquitectura, repositorio, runtimes y dependencias. | [C4](c4/) y [ADR-001](adr/ADR-001-backend-url-configuration.md). Inspección de Compose, dependencias y variables de entorno. | **Completado** |
| **3** | Identificar fallos de runtime y definir contratos. | [Documento técnico](DocumentoTecnicoParcial.md) analiza desajustes de puerto PostgreSQL y define precondiciones/postcondiciones. Verificado con `test_contracts.py`. | **Completado** |
| **4** | Añadir validación defensiva y comprobar entradas inválidas. | Barricadas de Pydantic/Regex y filtrado de datos no confiables de scraping. Verificado con `test_defensive.py`. | **Completado** |
| **5** | Unificar errores, excepciones y logging. | Mapeo de errores de dominio (400, 401, 404, 409) vs excepciones (503). Prevención de antipatrón Log-and-Throw. Verificado con `test_errors_and_exceptions.py`. | **Completado** |
| **6** | Corregir capacidad/numeración y demostrar concurrencia. | Demostración de condición de carrera (overbooking) vs cerrojo atómico `SELECT ... FOR UPDATE`. Verificado con `test_concurrency.py`. | **Completado** |
| **7** | Verificar recuperación ante fallos y preparar la línea base. | Reintentos de RabbitMQ al inicio, idempotencia en consumidor M5 y degradación elegante ante fallo de push. Verificado con `test_resilience.py`. | **Completado** |
| **8** | Presentar `v1.0` parcial funcional, verificable y preparada ante fallos/concurrencia. | 76 pruebas con `pytest` sobre el código real (13 de integración contra PostgreSQL), prueba de carga con Locust (2000 usuarios, consistencia verificada) y documento técnico alineado con el código. | **Completado (v1.0)** |

---

## 2. Verificaciones Ejecutadas en este Checkout

- **Backend Sintaxis y Compilación:** `python -m compileall -q src run.py tests scripts benchmarks` $\rightarrow$ **0 errores**.
- **Infraestructura:** `docker compose config -q` $\rightarrow$ configuración validada. Servicios PostgreSQL (5433), Redis (6379) y RabbitMQ (5672/15672) operativos.
- **Backend HTTP Smoke Test:** `GET /ping` respondió HTTP 200 y `/openapi.json` operativo con los routers registrados.
- **Frontend Tipos:** `npx tsc --noEmit` $\rightarrow$ **0 errores de tipado TypeScript**.
- **Frontend Lint:** `npm run lint` $\rightarrow$ **0 errores** (13 advertencias de optimización en hooks).
- **Frontend Build Web:** `npx expo export --platform web` generó las rutas estáticas correctamente.
- **Suite Automatizada SW707:** `python -m pytest tests` → **76 passed** con la base de pruebas levantada (`63 passed, 13 skipped` sin ella). Cubre contratos, barricadas defensivas, errores y excepciones, concurrencia y resiliencia sobre el código real.
- **Dependencias:** instalación desde cero de `requirements.txt` en Python 3.12 sin conflictos (`pip check`) y `pip-audit` sin vulnerabilidades conocidas.
- **Carga:** Locust con 1000 y 2000 estudiantes simultáneos; resultados en [`benchmarks/README.md`](../benchmarks/README.md).

---

## 3. Checklist de Cierre Cumplido para `v1.0`

- [x] Arranque reproducible desde un clon limpio con instrucciones y ejemplos de configuración (`.env.example`), sin secretos.
- [x] Recorrer y documentar el flujo de negocio completo de autenticación, solicitud de turno, consulta y confirmación/cancelación.
- [x] Definir y probar contratos para sesión inválida, recurso ausente, duplicado, capacidad agotada y transiciones no permitidas (`test_contracts.py`).
- [x] Analizar y blindar la frontera transaccional de aforo y numeración (`test_concurrency.py`).
- [x] Ejecutar prueba concurrente reproducible con capacidad restante de una ración y verificar el estado final: exactamente una asignación y cero excesos (`test_concurrency.py`).
- [x] Probar al menos dos mecanismos de resiliencia apropiados al dominio: reintentos de broker e idempotencia de tracking (`test_resilience.py`).
- [x] Implementar y ejecutar pruebas automatizadas reproducibles para todos los criterios de la rúbrica oficial.
- [x] Documento técnico oficial consolidado en Markdown (`DocumentoTecnicoParcial.md`).
