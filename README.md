# ComedorUNI

ComedorUNI gestiona turnos virtuales para el comedor universitario. Este repositorio
continúa el prototipo desarrollado previamente y lo evoluciona para el curso
Construcción de Software II (SW707).

## Estructura del repositorio

```text
.
├── backend/       API FastAPI, migraciones y servicios de infraestructura
├── docs/          Entregables SW707, arquitectura y archivo histórico
├── frontend/      Aplicación móvil/web React Native + Expo
├── resources/     Imágenes y otros recursos compartidos
├── .gitignore
└── README.md
```

- [Documentación y entregables](docs/README.md)
- [Proyecto Integrador SW707](docs/Proyecto_Integrador_SW707.docx)
- [Documento técnico parcial](docs/DocumentoTecnicoParcial.docx)
- [Avance semanal hasta el parcial](docs/avance-parcial-sw707.md)
- [Archivo histórico del proyecto previo](docs/historico/)

## Arquitectura actual

- **Frontend:** React Native, Expo Router y TypeScript.
- **Backend:** FastAPI/Uvicorn; expone HTTP y WebSocket.
- **Persistencia:** PostgreSQL; Redis guarda sesiones.
- **Mensajería:** RabbitMQ; los consumers y el worker de inactividad corren como
  tareas del proceso del backend.
- **Cliente institucional:** la app utiliza un WebView para el Portal Alumnos UNI.

La arquitectura desplegada es un monolito modular; no se asume escalamiento horizontal
ni coordinación de WebSockets entre réplicas. Las limitaciones y riesgos pendientes
están en el [documento técnico parcial](docs/DocumentoTecnicoParcial.docx).

## Requisitos

- Python 3.11 o posterior.
- Node.js 20 o posterior y npm.
- Docker Desktop/Docker Engine con Docker Compose.

## Flujo local de trabajo

### 1. Levantar PostgreSQL, Redis y RabbitMQ

Desde la raíz del repositorio:

```powershell
docker compose -f backend\docker-compose.yml up -d postgres redis rabbitmq
```

Los puertos del host son PostgreSQL `5433`, Redis `6379` y RabbitMQ `5672`
(consola de administración `15672`). El esquema inicial de PostgreSQL se carga al
crear el volumen por primera vez.

### 2. Configurar y ejecutar el backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python run.py
```

En Linux/macOS, activa el entorno con `source .venv/bin/activate`. El backend lee
su `.env` desde `backend/`; la plantilla establece `DB_PORT=5433` para conectar con
el mapeo local de Compose.

- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- Verificación: <http://localhost:8000/ping>

### 3. Configurar y ejecutar el frontend

En otra terminal:

```powershell
cd frontend\src
Copy-Item .env.example .env
npm ci
npm start
```

Para navegador, ejecuta `npm run web`. Expo toma las URL de `frontend/src/.env`.
`localhost` sirve para web y simuladores locales; en un emulador Android usa
`http://10.0.2.2:8000` y `ws://10.0.2.2:8000`. En un teléfono físico usa la IP LAN
del equipo que ejecuta el backend.

### 4. Validaciones disponibles

Desde `backend/`, valida sintaxis con:

```powershell
python -m compileall -q src run.py
```

Con el backend levantado, comprueba el endpoint de salud:

```powershell
Invoke-RestMethod http://localhost:8000/ping
```

Desde `frontend/src/`:

```powershell
npx tsc --noEmit
npm run lint
npx expo export --platform web
```

El frontend todavía no tiene suite automatizada. El directorio
`backend/tests/` tampoco contiene casos automatizados: la compilación y el smoke
test no sustituyen pruebas unitarias, de integración o de concurrencia. El estado
y los pendientes para llegar a una línea base parcial verificable se registran en
[avance-parcial-sw707.md](docs/avance-parcial-sw707.md).

## Flujo de trabajo del equipo

1. Trabajar en una rama por cambio y mantener `main` ejecutable.
2. Antes de cambiar reglas de negocio, revisar el contrato, el esquema de datos y
   el impacto en frontend/backend.
3. Hacer cambios pequeños; acompañar cada corrección con pruebas reproducibles y
   actualizar la documentación relacionada.
4. No subir archivos `.env`, credenciales ni datos personales. Los ejemplos de
   configuración no contienen secretos de entornos reales.
5. Abrir un pull request con resumen, validaciones ejecutadas y limitaciones.
   Ambos integrantes revisan y pueden explicar los cambios.
6. Mantener el avance semanal y la evidencia del curso en `docs/`; conservar el
   trabajo previo sin mezclarlo con los entregables actuales en `docs/historico/`.

## Situación SW707

El proyecto está en diagnóstico y preparación de la línea base parcial. Ya se
revisaron la estructura, el código y la arquitectura; las pruebas ejecutadas en este
checkout y las brechas todavía abiertas están detalladas en el
[registro de avance hasta el parcial](docs/avance-parcial-sw707.md). No se declara
la versión `v1.0` lista hasta cerrar las pruebas de flujo, concurrencia y fallos
exigidas por el curso.
