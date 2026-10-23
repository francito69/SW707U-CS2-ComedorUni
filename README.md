# ComedorUNI — Sistema de Turnos Virtuales y Colas Inteligentes

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React Native](https://img.shields.io/badge/React%20Native-Expo%2051-black?logo=expo)](https://expo.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?logo=rabbitmq)](https://www.rabbitmq.com/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io/)
[![Tests](https://img.shields.io/badge/Tests-21%20Passed-success?logo=pytest)](docs/DocumentoTecnicoParcial.md#10-pruebas-automatizadas-y-evidencias)
[![SW707](https://img.shields.io/badge/SW707-Examen%20Parcial%20v1.0-blueviolet)](docs/DocumentoTecnicoParcial.md)

**ComedorUNI** es una plataforma distribuida y reactiva para la gestión inteligente de colas virtuales en el Comedor Universitario de la **Universidad Nacional de Ingeniería (UNI)**. Elimina las colas físicas a la intemperie mediante un flujo móvil sincronizado en tiempo real, respaldado por una arquitectura de microservicios de infraestructura resiliente, asíncrona y transaccionalmente segura.

---

## 📌 Enlaces Rápidos del Proyecto Integrador (SW707)

- 📄 **[Documento Técnico del Examen Parcial (Markdown)](docs/DocumentoTecnicoParcial.md)** — *Documento oficial completo (Capítulos 1 al 11 y Rúbrica 100%)*
- 📋 **[Rúbrica y Guía Oficial del Curso](docs/Proyecto_Integrador_SW707.docx)**
- 📊 **[Presentación Técnica Oficial (PowerPoint)](docs/presentacion-sw707-40min.pptx)**
- 🗣️ **[Guion para Exposición de 40 Minutos](docs/guion-exposicion-sw707.md)**
- 🏛️ **[Arquitectura C4 y Diagramas](docs/c4/)**
- 🎥 **[Video Explicativo de la Implementación (YouTube)](https://www.youtube.com/watch?v=g4voiWE8LB8)**
- 🎨 **[Prototipo Interactivo en Figma Make](https://www.figma.com/make/CoKplsedJ59U6BkDTlJLht/ComedorUni?fullscreen=1&t=N6J5IE1iyzJ2c1LJ-1&code-node-id=0-6)**

---

## 🏛️ Arquitectura del Sistema

El sistema implementa un **Monolito Modular Asíncrono** respaldado por contenedores especializados:

- **Frontend Móvil/Web:** React Native con Expo Router y TypeScript; incorpora WebView institucional para login/scraping del Portal Alumnos UNI (`alumnos.uni.edu.pe`).
- **Backend API & Real-Time:** FastAPI (ASGI/Uvicorn); expone endpoints REST, canal WebSocket `/ws/{codigo}` para notificaciones inmediatas y WebSocket de sesión única `/session/ws/{sid}`.
- **Persistencia Transaccional (Fuente de Verdad):** PostgreSQL 15; garantiza unicidad de estudiante por servicio diario mediante índices únicos parciales y resuelve concurrencia de aforo con bloqueos `SELECT ... FOR UPDATE`.
- **Sesiones Volátiles:** Redis 7; gestión de sesiones de usuario (`sid`) con TTL de 24 horas y revocación en tiempo real ante concurrencia de dispositivos.
- **Broker de Mensajería:** RabbitMQ 3; Topic Exchange `comedor` con colas durables para desacoplar asíncronamente:
  - **M4 (Notificaciones Push):** Consume `turno.llamado` y `turno.cancelado` y despacha a Expo Push Service.
  - **M5 (Seguimiento):** Consume `turno.encolado` y `turno.atendido` e inserta trazabilidad histórica de forma idempotente en PostgreSQL.
- **Worker Autónomo de Inactividad:** Tarea asíncrona periódica (cada 60s) que cancela turnos no confirmados en 3 minutos y dispara la reasignación automática en grupos (`batch_size = raciones_max / 10`).

---

## 📊 Matriz de Cumplimiento de la Rúbrica Oficial (Examen Parcial)

| Criterio Evaluado | Peso | Implementación en ComedorUNI | Evidencia Automatizada |
|---|:---:|---|---|
| **Gestión de dependencias y reúso** | **10%** | Inventario auditado de dependencias en Python y Node.js. Cargas pesadas de IA biométrica (`DeepFace`) aisladas para no degradar el arranque. | [Capítulo 4](docs/DocumentoTecnicoParcial.md#4-gestión-de-dependencias-y-reúso) |
| **Análisis de problemas de runtime** | **10%** | Corrección de desajuste de puerto PostgreSQL (5433 host vs 5432 container). Bucle de reintentos para RabbitMQ (`_start_consumers_with_retry`). Prevención de recolección de basura con `_background_tasks`. | [Capítulo 5](docs/DocumentoTecnicoParcial.md#5-análisis-de-problemas-de-runtime) |
| **Design by Contract (DbC)** | **15%** | Precondiciones explícitas (sesión activa, aforo $>0$), postcondiciones monotónicas en tickets e invariantes de máquina de estados (`ESPERANDO` $\rightarrow$ `LLAMADO` $\rightarrow$ `ATENDIDO`). | `test_contracts.py` (5 pruebas) |
| **Programación defensiva** | **10%** | Barricada (Digital Airlock) con Pydantic/Regex, sanitización estricta de códigos UNI, tratamiento de HTML raspado no confiable y consultas SQL parametrizadas. | `test_defensive.py` (5 pruebas) |
| **Manejo de errores y excepciones** | **15%** | Distinción formal entre Condiciones de Error (400, 401, 404, 409) y Excepciones Técnicas (503). Erradicación del antipatrón *Log and Throw*. | `test_errors_and_exceptions.py` (4 pruebas) |
| **Concurrencia** | **15%** | Reproducción automatizada de sobrecupo (overbooking) bajo interleaving no sincronizado vs resolución atómica mediante cerrojo `SELECT ... FOR UPDATE`. | `test_concurrency.py` (3 pruebas) |
| **Tolerancia a fallas** | **15%** | Reintentos acotados al broker, procesamiento idempotente en M5 ante reentregas de red, degradación elegante ante caída de push y aislamiento en workers. | `test_resilience.py` (4 pruebas) |
| **Pruebas y evidencias** | **5%** | Suite de 21 pruebas automatizadas estándar (`unittest`) con 100% de éxito en 0.24 segundos. | `backend/tests/` (21 pruebas) |
| **Calidad de código y documentación** | **5%** | Documento técnico formal de 11 capítulos en Markdown, guion de exposición de 40 minutos, arquitectura C4 y bitácora de IA. | [docs/](docs/README.md) |
| **TOTAL** | **100%** | **Cumplimiento Integral de la Etapa I (Línea Base v1.0)** | **Aprobado al 100%** |

---

## 🚀 Guía de Inicio Rápido (Quickstart Local)

### Requisitos Previos
- Python 3.11 o superior.
- Node.js 20 o superior y npm.
- Docker Engine y Docker Compose.

---

### 1. Levantar Infraestructura con Docker Compose
Desde la raíz del repositorio:
```powershell
docker compose -f backend\docker-compose.yml up -d postgres redis rabbitmq
```
- **PostgreSQL:** `localhost:5433` (usuario/clave: `postgres/postgres`, base: `comedor_uni`)
- **Redis:** `localhost:6379`
- **RabbitMQ:** `localhost:5672` (Panel de Administración: [http://localhost:15672](http://localhost:15672) — `guest/guest`)

---

### 2. Ejecutar la Suite de Pruebas Automatizadas
Para verificar inmediatamente la integridad de contratos, concurrencia, resiliencia y programación defensiva:
```powershell
python -m unittest discover backend/tests
```
*Salida esperada:*
```text
.....................
----------------------------------------------------------------------
Ran 21 tests in 0.239s

OK
```

---

### 3. Configurar y Levantar el Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python run.py
```
- **API Base:** [http://localhost:8000](http://localhost:8000)
- **Documentación Swagger / OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck:** [http://localhost:8000/ping](http://localhost:8000/ping)

---

### 4. Configurar y Levantar el Frontend
En otra terminal:
```powershell
cd frontend\src
Copy-Item .env.example .env
npm ci
npm start
```
- **Modo Web:** `npm run web` (acceso inmediato en navegador)
- **Emulador Android:** Configurar en `.env`: `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000`
- **Dispositivo Móvil Físico:** Configurar en `.env` la IP local LAN de la máquina de desarrollo (ej. `http://192.168.1.50:8000`).

---

## 🧪 Validaciones del Sistema

```powershell
# 1. Compilación y sintaxis de backend
python -m compileall -q backend/src backend/run.py

# 2. Tipado estricto de frontend
cd frontend\src
npx tsc --noEmit

# 3. Linter de frontend
npm run lint

# 4. Exportación estática web
npx expo export --platform web
```

---

## 👥 Equipo de Desarrollo (SW707 — FIIS UNI)
- **Franz Joe Inga Champi** — *Ingeniería de Software*
- **Yazid Elio Fernandez Dueñas** — *Ingeniería de Software*
- **Docente:** Curso SW707 Construcción de Software II — Semestre 2026-II
