# Directorio de Scripts de Automatización (`scripts/`)

Este directorio contiene herramientas de automatización, medición y desarrollo auxiliar para el proyecto ComedorUNI (Sección 16 del Proyecto Integrador SW707).

## Scripts Disponibles

1. **`medir_acoplamiento.py`**:
   - Analizador estático de código fuente con el módulo `ast` de la biblioteca estándar de Python.
   - Mide Acoplamiento Aferente ($C_a$), Acoplamiento Eferente ($C_e$) e Inestabilidad ($I = \frac{C_e}{C_a + C_e}$) para cada paquete en `src/modules` y `src/shared`.
   - Uso:
     ```powershell
     python scripts/medir_acoplamiento.py
     ```

2. **`export_openapi.py`**:
   - Extrae el esquema formal de endpoints y contratos OpenAPI 3.0 desde la aplicación FastAPI y lo exporta a `config/openapi.yaml`.
   - Uso:
     ```powershell
     python scripts/export_openapi.py
     ```

3. **`publish_tunnel_url.ps1`**:
   - Publica automáticamente la URL pública activa del túnel de desarrollo a un Gist de GitHub para que la aplicación móvil (`frontend`) se sincronice en tiempo real sin recompilar el APK ni modificar constantes locales.
