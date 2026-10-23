# Directorio de Componentes Legados y Prototipos Anteriores (`legacy/`)

Este directorio documenta los artefactos, bosquejos previos y decisiones superadas a lo largo de las 8 semanas de la Etapa I del proyecto ComedorUNI (Sección 16 del Proyecto Integrador SW707).

## Historial de Decisiones y Prototipos Superados

1. **Sesión por JWT vs. Sesión por `sid` en Redis**:
   - *Supuesto inicial (Semana 1-2):* Se planteó la emisión de tokens JWT firmados para autenticar cada petición.
   - *Evolución a v1.0:* El código real adoptó **sesión única por `sid` en Redis** (`src/modules/auth/redis_store.py`). Permite revocación instantánea en tiempo real al detectar un nuevo login en otro dispositivo, impidiendo doble cola simultánea con la misma cuenta.

2. **Proceso único vs. Multi-worker con Bus Distribuido**:
   - *Prototipo inicial (Semana 3-6):* El backend operaba en un solo proceso Uvicorn con `manager.py` manteniendo conexiones WebSocket en memoria local.
   - *Evolución a v1.0:* Se introdujo arquitectura de 6 workers concurrentes coordinados por Redis Pub/Sub (`src/shared/ws_bus.py`) y lock de líder distribuido (`src/shared/leader_lock.py`), permitiendo escalar a más de 700 peticiones por segundo sin pérdida de mensajes WebSocket.

3. **Autenticación Externa Genérica vs. Scraping de Portal Alumnos**:
   - *Supuesto inicial:* Se asumió la existencia de un endpoint OAuth/OpenID oficial de la UNI.
   - *Evolución a v1.0:* Se implementó el flujo con WebView embebido en la aplicación móvil que autentica en `alumnos.uni.edu.pe`, extrae HTML oficial de cursos y matrícula, y valida biometría facial contrastando contra la fotografía institucional.
