# ComedorUNI — Sistema de Turnos Virtuales y Colas Inteligentes

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React Native](https://img.shields.io/badge/React%20Native-Expo%2054-black?logo=expo)](https://expo.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?logo=rabbitmq)](https://www.rabbitmq.com/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io/)
[![Tests](https://img.shields.io/badge/Tests-76%20Passed-success?logo=pytest)](docs/DocumentoTecnicoParcial.md#10-pruebas-automatizadas-y-evidencias)
[![SW707](https://img.shields.io/badge/SW707-Examen%20Parcial%20v1.0-blueviolet)](docs/DocumentoTecnicoParcial.md)

**ComedorUNI** es una plataforma distribuida y reactiva para la gestión inteligente de colas virtuales en el Comedor Universitario de la **Universidad Nacional de Ingeniería (UNI)**. Elimina las colas físicas a la intemperie mediante un flujo móvil sincronizado en tiempo real, respaldado por una arquitectura de microservicios de infraestructura resiliente, asíncrona y transaccionalmente segura.

---

## 📌 Enlaces Rápidos del Proyecto Integrador (SW707)

- 📄 **[Documento Técnico del Examen Parcial (Markdown)](docs/DocumentoTecnicoParcial.md)** — *Documento oficial completo (Capítulos 1 al 11 y Rúbrica 100%)*
- 🏛️ **[Modelo C4 en 4 Niveles](docs/c4/README.md)** — *Contexto (N1), Contenedores (N2), Componentes M1-M7 (N3) y Despliegue (N4)*
- 📐 **[Modelo de Vistas Arquitectónicas 4+1 de Kruchten](docs/arquitectura-4plus1.md)** — *Vistas Lógica, Procesos, Desarrollo, Física y Escenarios*
- 🗣️ **[Guion para Exposición Técnica de 40 Minutos](docs/guion-exposicion-sw707.md)** — *Sustentación y recorrido a nivel de código*
- 📋 **[Historial de Versiones (CHANGELOG.md)](CHANGELOG.md)** — *Registro formal según estándar Keep a Changelog*
- 🎨 **[Prompts Maestros para Figma Make](docs/prompts-figma-make.md)** — *Guía de prototipado interactivo y tokens de diseño*
- 📈 **[Avance Semanal hasta el Parcial](docs/avance-parcial-sw707.md)** — *Seguimiento semanal y cierre de línea base v1.0*
- 🎥 **[Video Explicativo de la Implementación (YouTube)](https://www.youtube.com/watch?v=g4voiWE8LB8)**
- 🎨 **[Prototipo Interactivo en Figma Make](https://www.figma.com/make/CoKplsedJ59U6BkDTlJLht/ComedorUni?fullscreen=1&t=N6J5IE1iyzJ2c1LJ-1&code-node-id=0-6)**

---

## 🏛️ Arquitectura del Sistema

El sistema implementa un **Monolito Modular Asíncrono** respaldado por microservicios de infraestructura:

- **Frontend Móvil/Web:** React Native con Expo Router y TypeScript; incorpora WebView institucional para login/scraping del Portal Alumnos UNI (`alumnos.uni.edu.pe`).
- **Backend API & Real-Time:** FastAPI (ASGI/Uvicorn, 6 workers concurrentes en producción); expone endpoints REST, el WebSocket de cola `/queue/ws/{sid}`, el de turnos activos `/queue/ws/active-service` y el de sesión única `/session/ws/{sid}`.
- **Persistencia Transaccional (Fuente de Verdad):** PostgreSQL 15; garantiza unicidad de estudiante por servicio diario mediante índices únicos parciales y resuelve la concurrencia de aforo contando las raciones bajo un bloqueo pesimista `SELECT ... FOR UPDATE`.
- **Sesiones y Coordinación:** Redis 7; sesiones de usuario (`sid`) con TTL de 8 horas, revocación en tiempo real entre dispositivos, bus de WebSockets entre workers (`src/shared/ws_bus.py`) y lock distribuido de líder (`src/shared/leader_lock.py`).
- **Broker de Mensajería:** RabbitMQ 3; Topic Exchange `comedor` con colas durables para desacoplar asíncronamente:
  - **M4 (Notificaciones Push):** Consume `turno.llamado` y `turno.cancelado` y despacha a Expo Push Service.
  - **M5 (Seguimiento):** Consume `turno.encolado` y `turno.atendido` e inserta trazabilidad histórica de forma idempotente en PostgreSQL.
- **Worker Autónomo de Inactividad:** Tarea asíncrona periódica (cada 60s) que cancela a quien no confirmó dentro de los 3 minutos desde que lo llamaron y llena los cupos libres con las siguientes personas de la cola (máximo `raciones_max / 10` llamadas a la vez). Quien no confirma no frena la cola.

---

## 📁 Estructura del Repositorio (Cumplimiento Sección 16)

El repositorio sigue estrictamente la **Sección 16 ("Estructura sugerida del repositorio") del Proyecto Integrador SW707**:

```text
SW707U-CS2-ComedorUni/
├── src/                  # Código fuente modular del backend FastAPI
├── tests/                # Suite de 76 pruebas automatizadas en pytest
├── docs/                 # Documentación técnica, C4, 4+1, ADRs y guion de sustentación
├── config/               # Migraciones SQL (001_init.sql), Alembic y OpenAPI
├── deployment/           # docker-compose.prod.yml (6 workers), compose local y Dockerfile
├── scripts/              # Medición de acoplamiento (ast), exportador OpenAPI, túnel
├── benchmarks/           # Pruebas de carga masiva con Locust (1000/2000 usuarios)
├── legacy/               # Registro de prototipos anteriores y decisiones superadas
├── frontend/             # Aplicación móvil / web en React Native + Expo
├── Dockerfile            # Dockerfile en la raíz para construcción del contenedor
├── docker-compose.yml    # Docker Compose de desarrollo en la raíz
├── README.md             # Guía principal de uso y arquitectura
├── CHANGELOG.md          # Bitácora de cambios (Keep a Changelog v1.0.0 Parcial)
├── .env.example          # Plantilla de variables de entorno sin secretos
└── .gitignore            # Exclusiones de Git
```

---

## 📊 Matriz de Cumplimiento de la Rúbrica Oficial (Examen Parcial)

| Criterio Evaluado | Peso | Implementación en ComedorUNI | Evidencia Automatizada |
|---|:---:|---|---|
| **Gestión de dependencias y reúso** | **10%** | Versiones exactas en `requirements.txt`, auditadas con `pip-audit` (Pillow subido a 13.0.0 por 35 CVE); dependencia sin uso eliminada. | [Capítulo 4](docs/DocumentoTecnicoParcial.md#4-gestión-de-dependencias-y-reúso) |
| **Análisis de problemas de runtime** | **10%** | Siete problemas reales con síntoma, causa y corrección (pool agotado bajo carga, opencv 5, event loop bloqueado, puerto PostgreSQL...). Logging con `request_id`. | [Capítulo 5](docs/DocumentoTecnicoParcial.md#5-análisis-de-problemas-de-runtime) |
| **Design by Contract (DbC)** | **15%** | `requiere`/`asegura` en el código (`src/shared/contratos.py`), contrato de `crear_turno` y matriz de contratos de la API. | `tests/test_contracts.py` (15 pruebas) |
| **Programación defensiva** | **10%** | Validación en la frontera: `sid` UUID v4, tipo de turno en lista cerrada, topes de tamaño y código UNI validado en el HTML del portal. SQL siempre parametrizado. | `tests/test_defensive.py` (23 pruebas) |
| **Manejo de errores y excepciones** | **15%** | Errores de dominio → 4xx con `codigo`; PostgreSQL/Redis caídos → 503 sin filtrar detalles; inesperados → 500 registrado una sola vez. | `tests/test_errors_and_exceptions.py` (14 pruebas) |
| **Concurrencia** | **15%** | Conteo de raciones dentro de `SELECT ... FOR UPDATE`, sobreventa reproducida contra PostgreSQL real y prueba de carga con Locust (2000 usuarios). | `tests/test_concurrency.py` (5 pruebas) + [`benchmarks/`](benchmarks/README.md) |
| **Tolerancia a fallas** | **15%** | Reintentos de consumers, publicación best-effort con timeout, avisos en tiempo real que no revierten la operación, idempotencia de M5, worker que sobrevive a ciclos fallidos. | `tests/test_resilience.py` (7 pruebas) |
| **Pruebas y evidencias** | **5%** | 76 pruebas con `pytest` sobre el código real (13 de integración contra PostgreSQL) y prueba de carga reproducible. | [`tests/`](tests/) |
| **Calidad de código y documentación** | **5%** | Documento técnico de 11 capítulos alineado con el código, guion de exposición, arquitectura C4 en 4 niveles y modelo 4+1. | [docs/](docs/README.md) |

---

## 🚀 Guía de Inicio Rápido (Quickstart Local)

### Requisitos Previos
- Python 3.12 (las versiones de `requirements.txt` están verificadas con 3.12).
- Node.js 20 o superior y npm.
- Docker Engine y Docker Compose.

---

### 1. Levantar Infraestructura con Docker Compose
Desde la raíz del repositorio:
```powershell
docker compose up -d postgres redis rabbitmq
```
- **PostgreSQL:** `localhost:5433` (usuario/clave: `postgres/postgres`, base: `comedor_uni`)
- **Redis:** `localhost:6379`
- **RabbitMQ:** `localhost:5672` (Panel Web: [http://localhost:15672](http://localhost:15672) — `guest/guest`)

---

### 2. Ejecutar la Suite de Pruebas Automatizadas
Con el entorno virtual creado (paso 3) e instaladas las dependencias de desarrollo (`pip install -r requirements-dev.txt`), desde la raíz del repositorio:
```powershell
# Levantar base aislada de pruebas (puerto 5434, tmpfs en memoria) para las 13 pruebas de integración
docker compose -f benchmarks/docker-compose.carga.yml up -d postgres
python -m pytest tests
```
*Salida esperada:* `76 passed`. Sin esa base, las 13 de integración se saltan (`63 passed, 13 skipped`).

La prueba de carga y benchmarks con Locust se documenta en [`benchmarks/README.md`](benchmarks/README.md).

---

### 3. Configurar y Levantar el Backend
Desde la raíz del repositorio:
```powershell
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
python -m compileall -q src run.py tests scripts benchmarks

# 2. Análisis estático de acoplamiento (Ca, Ce, I)
python scripts/medir_acoplamiento.py

# 3. Tipado estricto de frontend
cd frontend\src
npx tsc --noEmit

# 4. Linter de frontend
npm run lint

# 5. Exportación estática web
npx expo export --platform web
```

---

## 👥 Equipo de Desarrollo (SW707 — FIIS UNI)
- **Franz Joe Inga Champi** — *Ingeniería de Software*
- **Yazid Elio Fernandez Dueñas** — *Ingeniería de Software*
- **Docente:** — *ANIBAL JAVIER GUILLEN VASQUEZ*
- **Curso SW707 Construcción de Software II — Semestre 2026-II**
