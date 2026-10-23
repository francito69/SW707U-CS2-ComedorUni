# Directorio de Configuración (`config/`)

Este directorio centraliza las configuraciones del sistema según la estructura estándar del repositorio (Sección 16 del Proyecto Integrador SW707).

## Contenido

1. **`migrations/`**: Scripts de inicialización y migración de base de datos SQL (`001_init.sql`).
   - Define el esquema relacional de PostgreSQL 15: tablas `estudiantes`, `turnos_config`, `turno_dia`, `turnos`, `registro_seguimiento`, `menu_dia`, `menu_platos`.
   - Incluye los índices condicionales y restricciones de unicidad transaccional.
2. **`alembic/`**: Configuración para migraciones evolutivas de base de datos.
3. **`openapi.yaml`**: Especificación formal OpenAPI 3.0 de los contratos de la API REST y WebSockets del backend.

## Variables de Entorno

Las variables de entorno del sistema se configuran mediante el archivo `.env` en la raíz del repositorio, tomando como plantilla [`.env.example`](../.env.example).
