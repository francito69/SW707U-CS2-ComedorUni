# Ficha del Sistema: ComedorUNI

## 1. Nombre del sistema
**ComedorUNI: Gestión de turnos con colas virtuales**. 
*(Nombre a utilizar en el informe final).*

## 2. Origen
Desarrollado originalmente en el curso **SW603 Diseño de Software**. Es un sistema propio del equipo, no un caso externo como LabUNI.

## 3. Integrantes que participaron
- Yazid Elio Fernández Dueñas
- Farid Paolo Zamudio Sanchez

## 4. Qué hace
Digitaliza la obtención de turnos del comedor universitario mediante colas virtuales para eliminar filas físicas. Asigna cupos por bloques horarios (FIFO) y valida al estudiante con credenciales institucionales. Gestiona automáticamente la confirmación, cancelación y reasignación de cupos perdidos.

## 5. Lenguaje y stack
- **Backend:** Python con FastAPI (servidor Uvicorn).
- **Frontend:** TypeScript con React Native y Expo Router.
- **Base de Datos:** PostgreSQL 15 (persistencia principal) y Redis 7 (sesiones/estado temporal).
- **Mensajería:** RabbitMQ 3 (eventos asíncronos).
- **Construcción/Ejecución:** Docker Compose (infraestructura), pip (backend), npm/Expo CLI (frontend).

## 6. Repositorio
https://github.com/francito69/ComedorUNI-GestionDeColas
*(Repositorio nuevo del proyecto, separado del de la semana 1).*

## 7. Tres reglas de negocio
1. **Unicidad de turno activo:** Un estudiante no puede tener más de un turno activo simultáneo para el mismo bloque diario (validado por índice único parcial en BD).
2. **Capacidad por raciones:** La asignación se detiene si el conteo de turnos no cancelados alcanza el máximo de raciones configuradas para el servicio (ej. ALMUERZO/CENA).
3. **Expiración de llamado:** Si un turno es `LLAMADO` y no se confirma en 3 minutos, pasa a `CANCELADO`, liberando el cupo para reasignación automática.

## 8. Cómo se levanta hoy
El proceso es manual y presenta fricciones:
1. **Infraestructura:** Ejecutar `docker compose up -d postgres redis rabbitmq` (nota: el backend/frontend NO están en el Compose).
2. **Backend:** Crear entorno virtual (`python -m venv .venv`), instalar dependencias (`pip install -r requirements.txt`) y ejecutar `python run.py`. Requiere configurar variables de entorno del backend manualmente.
3. **Frontend:** Entrar a `frontend/src`, ejecutar `npm install`, crear el archivo `.env` a partir de `.env.example` y luego iniciar con `npx expo start`.
   *Convención válida:* Expo usa `frontend/src/.env` y su plantilla es `frontend/src/.env.example`; no se usa un `.env` en la raíz del repositorio para esta app.

## 9. Qué le falta o qué le duele
- **Concurrencia Crítica:** La asignación de turnos usa "contar e insertar" sin transacciones bloqueantes. Bajo carga, dos estudiantes pueden recibir el mismo número o superar la capacidad (raciones).
- **Despliegue Frágil:** No hay contenedorización completa (Dockerfile backend vacío) ni configuración centralizada. El frontend depende de túneles manuales (ngrok).
- **Nula Cobertura de Pruebas:** El directorio `tests` está vacío. No existen pruebas automatizadas para validar la lógica de cola ni la integridad de datos.
- **Operabilidad:** Los WebSockets viven en memoria local (no escalan horizontalmente) y los eventos en RabbitMQ no tienen reintentos garantizados si falla la conexión.

# FECHA: viernes 11 de setiembre 2026
# Resultado : APROBADO