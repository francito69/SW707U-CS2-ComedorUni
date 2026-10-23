# Directorio de Despliegue (`deployment/`)

Este directorio contiene los artefactos de infraestructura y orquestación de contenedores del proyecto ComedorUNI, en cumplimiento de la Sección 16 del Proyecto Integrador SW707.

## Contenido

1. **`docker-compose.yml`**: Orquestación para el entorno de desarrollo local.
   - **PostgreSQL 15**: Puerto `5433:5432`, inicialización automática con `config/migrations/001_init.sql`.
   - **Redis 7**: Puerto `6379:6379`.
   - **RabbitMQ 3 Management**: Puertos `5672:5672` (AMQP) y `15672:15672` (Panel Web).
2. **`docker-compose.prod.yml`**: Orquestación de producción multi-worker.
   - Levanta el backend con 6 workers de Uvicorn (`WORKERS=6`), pool de conexiones de Postgres dimensionado a 300 (`max_connections=300`), Redis para coordinación de WebSockets (`ws_bus.py`) y lock distribuido (`leader_lock.py`).
3. **`Dockerfile`**: Imagen multi-etapa basada en `python:3.12-slim` con dependencias de sistema para OpenCV/DeepFace (`libgl1`, `libglib2.0-0`) y dependencias Python auditadas.

## Comandos de Despliegue

```powershell
# Levantar servicios de desarrollo desde la raíz
docker compose up -d

# Levantar infraestructura de producción multi-worker
docker compose -f deployment/docker-compose.prod.yml up -d --build
```
