# Documento técnico parcial — ComedorUNI

**Curso:** Construcción de Software II (SW707)
**Integrantes:** Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas
**Versión de referencia:** prototipo existente del repositorio, previo a la línea base v1.0 de SW707
**Estado:** diagnóstico inicial para orientar el trabajo; las pruebas y mejoras propuestas no se consideran implementadas hasta registrar su evidencia.

## 1. Descripción del problema y usuarios

ComedorUNI organiza solicitudes de turnos del comedor universitario mediante colas virtuales. El problema de construcción relevante es mantener capacidad, orden, unicidad y estado correcto cuando hay solicitudes simultáneas, abandono, expiración y dependencias externas que pueden fallar. No se dispone aquí de mediciones oficiales de filas o demanda; esas necesidades se presentan como el problema que el prototipo busca atender, no como estadísticas verificadas.

Los usuarios del prototipo son el estudiante y el administrador del comedor. El estudiante inicia sesión desde la aplicación móvil, solicita/consulta/abandona su turno y responde al llamado. El administrador gestiona opciones operativas disponibles. El Portal Alumnos UNI forma parte del flujo de autenticación descrito por C4, y Expo Push Notification Service entrega avisos push. PostgreSQL, Redis y RabbitMQ son dependencias de infraestructura, no actores humanos.

## 2. Alcance y requisitos principales

El alcance actual incluye una aplicación React Native/Expo, una API FastAPI, configuración y menú, gestión de cola/turnos, sesiones Redis, persistencia PostgreSQL, eventos RabbitMQ, WebSocket y tareas consumidoras/worker iniciadas por el backend.

Requisitos que la versión SW707 debe verificar:

1. Solicitud autorizada de un turno y respuesta controlada ante sesión ausente o inválida.
2. Un turno activo por estudiante y turno diario, con FIFO y numeración única.
3. Capacidad nunca superior al límite configurado bajo concurrencia.
4. Transiciones válidas entre `ESPERANDO`, `LLAMADO`, `ATENDIDO` y `CANCELADO`.
5. Expiración y reasignación repetibles sin llamadas duplicadas ni eventos de negocio perdidos.
6. Validación de configuración, entradas y límites antes de persistir.
7. Pruebas reproducibles de reglas y fallos con resultados trazables.

Fuera del alcance parcial: control físico de acceso, inventario de alimentos, reemplazo de los sistemas académicos, despliegue multi-región y conversión del monolito en microservicios.

## 3. Arquitectura y decisiones técnicas

La arquitectura observada es un monolito modular. `backend/src/main.py` registra routers de autenticación, menú, colas y configuración. En el ciclo de vida de FastAPI inicia como tareas del mismo proceso el worker de inactividad y los consumers M4/M5. PostgreSQL almacena los datos transaccionales, Redis sesiones temporales por `sid`, y RabbitMQ intercambia eventos asíncronos. La app móvil consume HTTP y WebSocket. La autenticación institucional se realiza desde el flujo móvil con WebView hacia el Portal Alumnos UNI y posterior parsing de datos; el backend no implementa un cliente OAuth directo con Google.

Decisiones para la línea base parcial:

- Conservar PostgreSQL como fuente de verdad de la cola y usar sus restricciones como defensa final de integridad.
- Conservar el monolito modular mientras no haya mediciones que justifiquen servicios separados.
- Mantener configuración externa para las URL de cliente ya resueltas por `EXPO_PUBLIC_API_URL` y `EXPO_PUBLIC_WS_URL` (ADR-001); externalizar y validar también la configuración del backend.
- Tratar Redis como almacenamiento temporal de sesiones, no como sustituto de transacciones de turnos.
- Registrar explícitamente límites del prototipo: conexiones WebSocket y tareas de fondo son locales al proceso; no se afirma escalamiento horizontal.

Diagramas y precisiones arquitectónicas: [`docs/c4/`](docs/c4/). Decisión sobre URL del backend: [`docs/adr/ADR-001-backend-url-configuration.md`](docs/adr/ADR-001-backend-url-configuration.md).

## 4. Dependencias y reúso

El backend declara FastAPI/Uvicorn, `python-dotenv`, `psycopg2-binary`, `redis`, `aio-pika`, `httpx`, `requests`, BeautifulSoup, DeepFace, OpenCV, Pillow y `tf-keras`. Sus responsabilidades abarcan API/WebSocket, PostgreSQL, sesiones, mensajería, scraping HTML y análisis biométrico. El cliente usa Expo/React Native, Expo Router, WebView, Secure Store, cámara y notificaciones push.

El reúso de estas bibliotecas evita implementar protocolos, acceso a datos y capacidades de plataforma desde cero. Antes de fijar la versión parcial se debe documentar para cada dependencia directa su uso, versión instalada/resuelta, licencia y alternativa; el `requirements.txt` actual no fija versiones exactas. `package.json` usa rangos semver para varias dependencias. Los resultados de `pip-audit`/`npm audit` deben adjuntarse cuando se ejecuten, no anticiparse.

## 5. Problemas de runtime observados o por reproducir

- **Puerto de PostgreSQL:** Compose publica el puerto del host `5433` hacia el puerto del contenedor `5432`, mientras `shared/db.py` usa `DB_PORT=5432` por defecto. Una ejecución local sin `.env` puede intentar conectarse al puerto incorrecto; documentar `DB_PORT=5433` o unificar la configuración.
- **Arranque parcial:** `lifespan` captura y solo imprime una excepción de `ensure_turno_dia_hoy`; la API puede iniciar aunque no se haya preparado el turno diario.
- **RabbitMQ:** el arranque de consumers reintenta 30 veces con pausas de 3 segundos. Al agotar los intentos se registra el fallo y el proceso sigue; no se acredita recuperación automática posterior ni entrega durable garantizada.
- **Concurrencia/capacidad:** el servicio consulta el número de raciones antes de llamar a `crear_turno`. Aunque la creación bloquea la fila `turno_dia` con `FOR UPDATE`, el control de capacidad no está dentro del mismo tramo protegido; dos solicitudes pueden pasar la comprobación y superar el aforo.
- **Numeración:** `crear_turno` calcula `COUNT(*) + 1` excluyendo turnos cancelados y atendidos, pero existe un índice único por `(turno_dia_id, numero_turno)` que conserva también esos registros. Luego de estados terminales el número calculado puede repetirse y causar un conflicto de integridad.
- **CORS:** `main.py` admite `allow_origins=["*"]` junto con credenciales. Debe restringirse por entorno antes de un despliegue accesible externamente.
- **Carga de dependencias biométricas:** DeepFace/OpenCV/TensorFlow pueden tener un coste de instalación, memoria y arranque superior al resto del backend; medir instalación y primera inferencia en el entorno objetivo.
- **Logs:** el backend usa `print` en rutas de arranque y conexión. No hay evidencia en este baseline de logs estructurados o métricas operativas centralizadas.

## 6. Contratos y programación defensiva

Los contratos deben documentar precondiciones, postcondiciones, invariantes, estados permitidos, errores HTTP y efectos persistidos de cada operación crítica. Como mínimo:

| Operación                   | Precondiciones/invariantes                                                                                                         | Resultado esperado ante incumplimiento                                                                                                 |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Unirse a cola                | Sesión válida; estudiante persistido; turno diario abierto; servicio elegible; sin turno activo duplicado; capacidad disponible. | `401` para sesión inválida, `404` para recurso inexistente y `409` para duplicado/capacidad agotada, según contrato uniforme. |
| Confirmar o abandonar        | Turno propiedad del estudiante y en un estado que admita la transición.                                                           | Rechazo controlado sin mutación cuando el estado no lo permite; operaciones repetidas con semántica idempotente documentada.         |
| Configurar horario/capacidad | Administrador autorizado; tipo permitido; horarios y valores dentro de límites.                                                   | Error de validación sin escritura parcial.                                                                                            |
| Consumir evento              | Payload parseable y con campos obligatorios; identificador de evento si se incorpora idempotencia.                                 | Mensaje inválido aislado, registrado y tratado según política de ack/reintento/DLQ.                                                 |

La validación de entrada debe ocurrir en el límite HTTP y las invariantes deben repetirse en el servicio/persistencia cuando sea necesario. No confiar en valores por defecto silenciosos para ocultar recursos inexistentes; distinguir “sin configuración” de un límite real.

## 7. Estrategia de errores y excepciones

La API debe conservar códigos HTTP coherentes y mensajes útiles, pero sin devolver secretos, credenciales, HTML institucional, fotos ni tracebacks. Se propone clasificar errores de validación, autenticación/autorización, conflicto de negocio, recurso ausente, indisponibilidad externa y error interno; registrar contexto correlacionable sin datos personales.

Las operaciones SQL deben tener una frontera transaccional clara, confirmar solo tras completar la operación, ejecutar rollback ante excepción y cerrar conexiones siempre. Los workers deben aislar fallos por mensaje/iteración para no detenerse por un payload inválido. Se evitará capturar `Exception` y continuar silenciosamente sin métrica o resultado observable. La política exacta de respuesta por endpoint se cerrará junto con sus pruebas.

## 8. Concurrencia

Existe una protección parcial: `crear_turno()` ejecuta `SELECT ... FOR UPDATE` sobre la fila de `turno_dia` antes de calcular e insertar el número. La base de datos también define índices únicos para número de turno y para `(estudiante_id, turno_dia_id)` cuando el estado no es `CANCELADO`.

La protección no basta para garantizar capacidad porque el conteo de raciones está separado de la transacción bloqueada. La corrección de SW707 debe colocar la lectura de capacidad, validación de duplicado y reserva/numeración bajo una misma transacción serializada, manejar colisiones como conflicto de negocio y probarlo con solicitudes paralelas. La estrategia debe impedir la reutilización de números históricos, por ejemplo mediante un contador monotónico por turno diario actualizado bajo el mismo bloqueo.

**Criterio de aceptación propuesto:** con capacidad restante de una ración y N solicitudes concurrentes, exactamente una reserva nueva; con el mismo estudiante y N solicitudes, como máximo una reserva no cancelada; cero números duplicados y respuestas definidas para las demás peticiones. El N, entorno y comando se fijarán al preparar la prueba.

## 9. Tolerancia a fallas

El prototipo ya intenta iniciar los consumers M4/M5 con reintentos acotados al arranque y usa RabbitMQ para eventos. Eso no equivale a garantía de entrega frente a caída durante procesamiento. Se debe definir ack/nack, reintentos con límite, cola de mensajes fallidos si se justifica, idempotencia del consumer, timeouts de dependencias y comportamiento de degradación de la API. Una estrategia tipo outbox solo se añadirá si la consistencia entre commit de PostgreSQL y publicación del evento lo requiere y se puede probar.

Para Redis y PostgreSQL se definirán fallos visibles y recuperación; no se debe reportar éxito de una operación crítica que no pudo persistirse. El worker de inactividad local al proceso requiere evitar ejecuciones duplicadas si se inicia más de una instancia.

## 10. Pruebas y resultados

En el checkout revisado, `backend/tests/` contiene únicamente `.gitkeep`; no hay suite automatizada ni resultados de ejecución que se puedan declarar como aprobados. [`docs/escenarios.md`](docs/escenarios.md) contiene objetivos medibles propuestos, pero varios detalles no describen el baseline real (por ejemplo, token JWT y escalamiento Redis Pub/Sub); deben reconciliarse con la arquitectura vigente antes de usarlos como evidencia.

Plan de verificación para v1.0:

- Pruebas unitarias de transiciones y validaciones de horarios/capacidad.
- Pruebas de API con `pytest`/`httpx` para sesión inválida, duplicado, turno inexistente, capacidad agotada y acciones fuera de estado.
- Pruebas de integración con PostgreSQL para índices, transacciones, rollback y numeración tras estados terminales.
- Prueba concurrente reproducible que inspeccione el estado final de la base de datos, no solo códigos HTTP.
- Prueba de fallo de RabbitMQ durante arranque y procesamiento; verificar logs, recuperación y no pérdida/duplicación según el contrato adoptado.
- Guardar comandos, entorno, salida y limitaciones en el repositorio. Pruebas de carga con k6/Locust se reservarán para requisitos de rendimiento y entorno controlado.

**Resultados disponibles en esta versión del documento:** no se han ejecutado ni adjuntado estas pruebas; por tanto no se atribuyen porcentajes, latencias ni tolerancia lograda.

## 11. Limitaciones y trabajo futuro

- No hay pruebas automatizadas en la carpeta de pruebas del backend.
- Las dependencias del backend carecen de versiones fijadas; no hay informe actualizado de auditoría de vulnerabilidades en la evidencia revisada.
- Hay discrepancias entre el puerto publicado por Compose y el puerto por defecto del cliente PostgreSQL.
- Capacidad y numeración necesitan una frontera transaccional coherente; las restricciones actuales pueden revelar conflictos, pero no sustituyen una respuesta API deliberada.
- CORS es permisivo; la configuración de backend requiere externalización y validación.
- Workers y WebSockets son locales al proceso y no coordinan varias réplicas.
- Los reintentos de RabbitMQ se limitan al inicio de consumers; falta política de recuperación durante la operación y evidencia sobre entrega.
- El scraping depende del HTML del Portal Alumnos y la biometría de imágenes y bibliotecas nativas; son riesgos de disponibilidad, privacidad y runtime.
- La fecha oficial de expiración, el alcance de autorización administrativa y algunos detalles de comportamiento deben quedar fijados como reglas verificables.

El trabajo se realizará incrementalmente: primero pruebas y correcciones de la línea base parcial; luego estados/configuración, observabilidad, medición, refactorización y evolución para v2.0. No se reiniciará el producto ni se presentará una arquitectura futura como si ya estuviera desplegada.
