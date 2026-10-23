# Guion Maestro de Exposición Técnica (10 Minutos) y Defensa (5 Minutos)

**Curso:** Construcción de Software II (SW707) — Semestre 2026-II  
**Institución:** Universidad Nacional de Ingeniería (UNI) — FIIS  
**Proyecto:** ComedorUNI — Sistema Distribuido de Turnos Virtuales y Colas Inteligentes  
**Equipo:** Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas  
**Docente Evaluador:** Mg. Aníbal Javier Guillén Vásquez  
**Línea Base Evaluada:** Versión v1.0 (Examen Parcial)  

---

## ⏱️ Estructura Temporal y Regla de Oro

- **Exposición:** Exactamente **10 minutos** (10 diapositivas/secciones a 1 minuto por tema).
- **Defensa y Preguntas:** **5 minutos** (respuestas técnicas basadas en el código real).
- **Principio Rector:** *"No se evalúa solamente lo que el software hace; se evalúa cómo fue construido y cómo puede evolucionar."*

---

## 📑 Índice de la Presentación (10 Láminas / 10 Minutos)

| Minuto | Lámina / Tema | Elemento Visual Principal | Enfoque de Construcción de Software |
|---|---|---|---|
| **00:00–01:00** | **1. Portada, Problema y Alcance** | Diapositiva institucional + Insignias v1.0 | Dominio real, colas a la intemperie y línea base verificable. |
| **01:00–02:00** | **2. Prototipo Figma Make y Flujo Móvil** | [Prototipo Interactivo Figma](https://www.figma.com/make/CoKplsedJ59U6BkDTlJLht/ComedorUni) | Tokens de diseño, WebView institucional, biometría facial y estados. |
| **02:00–03:00** | **3. C4 Nivel 1 (Contexto) y Nivel 2 (Contenedores)** | `Nivel1_ContextoV4.png` y `Nivel2_Contenedores_V4.png` | Integraciones externas (Portal UNI, Expo Push) y stack de infraestructura. |
| **03:00–04:00** | **4. C4 Nivel 3 (Componentes) y Vista Lógica** | `Nivel3_consolidado.png` y `domain-model.png` | Monolito modular, modelo de dominio inmutable y rodaja hexagonal. |
| **04:00–05:00** | **5. C4 Nivel 4 y Vista Física (Despliegue)** | `Nivel4_Despliegue_M2_M3.png` | Topología multi-worker (6 procesos Uvicorn), Redis Pub/Sub y puertos. |
| **05:00–06:00** | **6. Vista de Procesos: Concurrencia y Aforo** | `exposicion-concurrencia.png` | Condición de carrera (overbooking), cerrojo `SELECT ... FOR UPDATE`. |
| **06:00–07:00** | **7. Flujo Asíncrono, Workers y Reasignación** | `diagrama-proceso.png` y `exposicion-estados-tiempo-real.png` | Worker de inactividad con leader lock, política de no bloqueo y RabbitMQ. |
| **07:00–08:00** | **8. Vista de Desarrollo: DbC y Barricadas** | `exposicion-contrato-cola.png` | `requiere`/`asegura` en `contratos.py`, validación Pydantic y anti-SQLi. |
| **08:00–09:00** | **9. Problemas de Runtime y Estructura Sección 16** | Tabla Sección 16 del repositorio | Puerto 5433, starvation del pool de BD, `run_in_threadpool` y carpetas. |
| **09:00–10:00** | **10. Evidencias Automatizadas y Benchmarks** | Terminal con 76 tests + Reporte Locust | 76 tests en 2.59s, 729 req/s con 2000 usuarios, 0 sobreventa. |

---

## 🎙️ Guion Paso a Paso (Minuto a Minuto)

### Minuto 00:00 – 01:00 | Lámina 1: Portada, Problema y Propuesta
- **Qué mostrar:** Diapositiva de portada con títulos oficiales, nombres del equipo, repositorio oficial y badges de 76 tests pasando.
- **Qué decir:**
  > *"Buenos días, profesor Aníbal Guillén. Presentamos la Línea Base v1.0 de **ComedorUNI**, un sistema distribuido y reactivo para la gestión inteligente de colas virtuales en el Comedor Universitario de la UNI.*  
  > *Históricamente, los estudiantes pierden horas en colas físicas a la intemperie bajo el sol o frío para alcanzar una ración de almuerzo o cena. Nuestro reto de construcción no fue hacer un simple CRUD web, sino resolver un problema altamente concurrente: garantizar equidad en la asignación de raciones limitadas, sincronización móvil en tiempo real y tolerancia absoluta ante caídas de servicios externos, respaldado por una arquitectura modular resiliente y 76 pruebas automatizadas."*

---

### Minuto 01:00 – 02:00 | Lámina 2: Prototipo Figma Make y Experiencia de Usuario
- **Qué mostrar:** Prototipo interactivo en Figma Make ([Enlace Figma](https://www.figma.com/make/CoKplsedJ59U6BkDTlJLht/ComedorUni)) o la lámina de diseño de tokens y pantallas móviles (`comedoruni-figma-acceso-recorte.png`).
- **Qué decir:**
  > *"Diseñamos la experiencia de usuario en **Figma Make** aplicando tokens institucionales con identidad UNI (granate `#8A1538` y escala tipográfica Inter).*  
  > *El flujo del estudiante resuelve la identidad sin inventar credenciales: la app embebe un WebView seguro hacia el Portal Alumnos UNI (`alumnos.uni.edu.pe`). Al autenticarse, extraemos el HTML institucional de cursos y matrícula, y validamos la identidad mediante **biometría facial con DeepFace** contrastando la cámara frontal contra la foto oficial del carné.*  
  > *Con la identidad validada, el backend emite una sesión única por `sid` en Redis con TTL de 8 horas. Esto impide que un estudiante abra doble sesión en dos dispositivos para intentar acaparar turnos."*

---

### Minuto 02:00 – 03:00 | Lámina 3: C4 Niveles 1 y 2 (Contexto y Contenedores)
- **Qué mostrar:** Diagramas `resources/img/Nivel1_ContextoV4.png` y `resources/img/Nivel2_Contenedores_V4.png`.
- **Qué decir:**
  > *"En el **Modelo C4 Nivel 1 (Contexto)** identificamos dos actores: Estudiante y Administrador, integrados con dos sistemas externos reales: el Portal Alumnos UNI como fuente de identidad y el servicio en la nube Expo Push Service (`exp.host`) para notificaciones móviles.*  
  > *En el **Nivel 2 (Contenedores)**, ComedorUNI implementa un **Monolito Modular Asíncrono** respaldado por microservicios de infraestructura:*  
  > *1. La aplicación móvil en React Native y Expo Router.*  
  > *2. El backend en FastAPI ejecutando 6 workers concurrentes sobre Uvicorn.*  
  > *3. PostgreSQL 15 como fuente única de verdad transaccional.*  
  > *4. Redis 7 para sesiones temporales, locks distribuidos y bus de WebSockets.*  
  > *5. RabbitMQ 3 como broker de mensajería con Topic Exchange `comedor`."*

---

### Minuto 03:00 – 04:00 | Lámina 4: C4 Nivel 3 (Componentes) y Vista Lógica
- **Qué mostrar:** Diagramas `resources/img/Nivel3_consolidado.png` y `resources/img/domain-model.png`.
- **Qué decir:**
  > *"En el **Nivel 3 (Componentes)** y en la **Vista Lógica del Modelo 4+1**, dividimos el backend en 7 módulos con responsabilidades aisladas:*  
  > *- **M1 (Auth):** Scraping institucional, biometría y sesión en Redis.*  
  > *- **M2 y M3 (Colas y Turnos):** Encolamiento, sincronización WebSocket y gestión de servicios activos.*  
  > *- **M4 (Notificaciones Push):** Consumidor asíncrono RabbitMQ para eventos `turno.llamado` y `turno.cancelado`.*  
  > *- **M5 (Seguimiento):** Consumidor RabbitMQ que inserta auditoría histórica de forma idempotente en PostgreSQL.*  
  > *- **M6 (Reasignación):** Cálculo de cupos libres y avance de cola.*  
  > *- **M7 (Configuración y Menú):** Horarios, límite de raciones y balance nutricional.*  
  > *Además, en `src/modules/queues/` implementamos una **rodaja de Arquitectura Hexagonal** separando el caso de uso `AsignarTurno` de los adaptadores de persistencia en memoria y PostgreSQL."*

---

### Minuto 04:00 – 05:00 | Lámina 5: C4 Nivel 4 y Vista Física (Despliegue Multi-Worker)
- **Qué mostrar:** Diagrama `resources/img/Nivel4_Despliegue_M2_M3.png` o `Nivel4_Despliegue_M1_M4_M5.png`.
- **Qué decir:**
  > *"En el **Nivel 4 y la Vista Física de Despliegue**, resolvemos un reto crítico de escalabilidad en Python:*  
  > *Un solo proceso de FastAPI no aprovecha múltiples núcleos de CPU. En producción (`deployment/docker-compose.prod.yml`), desplegamos **6 workers de Uvicorn**.*  
  > *Esto generaba un problema de tiempo de ejecución: si el Estudiante A abre su WebSocket en el Worker 1, pero su llamado lo procesa el Worker 4, ¿cómo le llega el mensaje?*  
  > *Lo resolvimos implementando un **Bus Distribuido de WebSockets (`src/shared/ws_bus.py`)** sobre Redis Pub/Sub: cualquier evento emitido por un worker viaja por Redis y es retransmitido instantáneamente por el worker que mantiene la conexión viva del estudiante."*

---

### Minuto 05:00 – 06:00 | Lámina 6: Vista de Procesos: Concurrencia y Prevención de Sobreventa
- **Qué mostrar:** Diagrama `resources/img/exposicion-concurrencia.png` y fragmento de código de `src/modules/queues/service.py`.
- **Qué decir:**
  > *"La **Vista de Procesos** ataca el problema más peligroso del comedor: la condición de carrera por sobrecupo.*  
  > *A las 12:00 en punto, 2000 estudiantes solicitan turno simultáneamente para solo 500 raciones. Una lectura simple `COUNT(*)` causaría sobreventa masiva porque múltiples hilos leen el mismo cupo libre antes de insertar.*  
  > *Nuestra solución transaccional:*  
  > *1. Bloqueo pesimista con **`SELECT ... FOR UPDATE`** sobre el registro del turno del día.*  
  > *2. Conteo de raciones reservadas dentro de la misma transacción atómica.*  
  > *3. Si se alcanza `raciones_max`, se ejecuta `rollback` y se arroja la excepción de dominio `SinRaciones` (HTTP 409).*  
  > *4. Respaldado por un **índice único condicional en PostgreSQL** `(estudiante_id, turno_dia_id) WHERE estado != 'CANCELADO'`, garantizando cero sobreventa matemáticamente."*

---

### Minuto 06:00 – 07:00 | Lámina 7: Flujo Asíncrono, Workers y Reasignación
- **Qué mostrar:** Diagramas `resources/img/diagrama-proceso.png` y `resources/img/exposicion-estados-tiempo-real.png`.
- **Qué decir:**
  > *"Para la dinámica de cola aplicamos dos decisiones clave:*  
  > *Primero, **Política de No Bloqueo**: cuando un estudiante es llamado, tiene una ventana de tolerancia de **3 minutos** para confirmar su presencia en la puerta. Si no aparece, **no frena la cola**: el worker llama de inmediato al siguiente cupo disponible.*  
  > *Si confirma tarde dentro de su ventana, entra al grupo que se atiende en ese momento sin desplazar a nadie. Pasados los 3 minutos, el turno pasa irreversiblemente a `CANCELADO`.*  
  > *Segundo, **Lock Distribuido de Líder (`src/shared/leader_lock.py`)**: con 6 workers corriendo, una tarea periódica de fondo se ejecutaría 6 veces. Implementamos un cerrojo en Redis con `SET NX PX` para que solo un worker tome el liderazgo del ciclo de inactividad cada 60 s.*  
  > *Y mediante RabbitMQ, la atención del turno publica eventos desacoplados: si Expo Push o la red externa se caen, el turno se confirma igual sin afectar al estudiante."*

---

### Minuto 07:00 – 08:00 | Lámina 8: Vista de Desarrollo: Design by Contract y Programación Defensiva
- **Qué mostrar:** Diagrama `resources/img/exposicion-contrato-cola.png` y código de `src/shared/contratos.py`.
- **Qué decir:**
  > *"En la **Vista de Desarrollo**, aplicamos los principios de construcción robusta evaluados en la rúbrica:*  
  > *1. **Design by Contract (DbC - 15%):** Implementamos `requiere()` y `asegura()` en `src/shared/contratos.py`. Por ejemplo, en `crear_turno` exigimos como precondición IDs estrictamente positivos y configuraciones válidas; y aseguramos como postcondición que el número asignado sea exactamente el correlativo siguiente y que el aforo total cuadre.*  
  > *2. **Programación Defensiva (10%):** Establecimos barricadas con esquemas Pydantic en la frontera. Sanitizamos el HTML del Portal Alumnos validando el patrón regex del código UNI (`^[0-9]{8}[A-Za-z0-9]$`), topes estrictos al tamaño de foto base64, y el 100% de consultas SQL parametrizadas para inmunidad total ante inyecciones SQL."*

---

### Minuto 08:00 – 09:00 | Lámina 9: Problemas de Runtime y Estructura Sección 16
- **Qué mostrar:** Estructura de directorios del repositorio según Sección 16.
- **Qué decir:**
  > *"En el criterio de **Problemas de Runtime (10%)**, documentamos 7 incidentes reales de ejecución:*  
  > *- Desajuste de puerto de PostgreSQL (5433 vs 5432).*  
  > *- Prevención del bug de recolección de basura en Python: si se lanza `asyncio.create_task()` sin guardar referencia en `_background_tasks`, el Garbage Collector destruye silenciosamente los workers en memoria.*  
  > *- Starvation del pool de base de datos bajo carga: psycopg2 con `minconn=1` saturaba los puertos efímeros de Windows. Lo corregimos fijando `minconn = maxconn = 15` por worker e incorporando un semáforo con timeout de 10s.*  
  > *- Bloqueo del Event Loop: trasladamos las llamadas síncronas de base de datos a hilos independientes mediante `run_in_threadpool`.*  
  > *Además, cumplimos al 100% con la **Sección 16 de la guía**: el repositorio cuenta con `src/`, `tests/`, `docs/`, `config/`, `deployment/`, `scripts/`, `benchmarks/`, `legacy/`, `Dockerfile`, `docker-compose.yml` y `CHANGELOG.md`."*

---

### Minuto 09:00 – 10:00 | Lámina 10: Evidencias Automatizadas, Benchmarks y Cierre
- **Qué mostrar:** Terminal ejecutando `pytest tests` (76 passed en 2.59s) y tabla de resultados de Locust con 2000 usuarios.
- **Qué decir:**
  > *"Para cerrar, presentamos las evidencias técnicas automatizadas de nuestra Línea Base v1.0:*  
  > *- **76 pruebas automatizadas en `pytest`** ejecutándose en solo **2.59 segundos**, cubriendo contratos DbC, barricadas defensivas, concurrencia real, tolerancia a fallas e idempotencia.*  
  > *- **Prueba de carga masiva con Locust (`benchmarks/`):** simulamos la hora punta con **2000 estudiantes concurrentes** compitiendo por 500 raciones. El sistema procesó **729 peticiones por segundo** con apenas 0.01% de errores de conexión y 0 errores 500.*  
  > *- Y la verificación post-carga (`preparar_datos.py`) demostró **consistencia matemática absoluta**: cero turnos duplicados, cero huecos correlativos y exactamente 500 raciones entregadas.*  
  > *ComedorUNI demuestra que está construido para resistir fallas, soportar concurrencia masiva y evolucionar hacia la Etapa Final. Quedamos a su disposición para las preguntas. Muchas gracias."*

---

## 🛡️ Guía para los 5 Minutos de Defensa (Banco de Preguntas del Docente)

El docente evaluará si el equipo comprende el código a profundidad. A continuación, las preguntas más probables y cómo responderlas de forma incontestable:

### Pregunta 1: ¿Dónde ocurría la condición de carrera y cómo la reprodujeron y corrigieron en código?
- **Respuesta:**
  > *"La condición de carrera ocurría en `src/modules/queues/service.py` durante la función `crear_turno`. Cuando 40 hilos concurrentes compiten por la última ración libre, una lectura no protegida de cupos permitía que varios hilos leyeran que aún quedaba 1 ración, generando sobreventa (más de 10 turnos para 10 raciones).*  
  > *La reprodujimos en `tests/test_concurrency.py` (`test_demostracion_de_la_carrera_sin_bloqueo`), donde demostramos que sin cerrojo se sobrevenden turnos.*  
  > *La corregimos aplicando un bloqueo pesimista en PostgreSQL: **`SELECT ... FOR UPDATE`** sobre la fila del `turno_dia`. Mientras un hilo cuenta y asigna el turno, los demás hilos esperan en la cola de la transacción. Además, creamos un índice único parcial en PostgreSQL `WHERE estado != 'CANCELADO'` para que la base de datos rechace a nivel de motor cualquier duplicado por hardware."*

---

### Pregunta 2: ¿Por qué eligieron sesiones por `sid` en Redis y no tokens firmados JWT?
- **Respuesta:**
  > *"Por una regla de negocio y seguridad crítica: **la revocación instantánea de sesión**.*  
  > *Con JWT, el token es autocontenido y no tiene estado en el servidor; si un estudiante inicia sesión en el teléfono de un amigo y luego en el suyo, ambos tokens seguirían siendo válidos hasta que expire su tiempo de vida, permitiendo acaparar turnos dobles. Para invalidar un JWT antes de tiempo se requiere una lista negra centralizada, lo que elimina la ventaja de no tener estado.*  
  > *Con Redis (`src/modules/auth/redis_store.py`), guardamos la sesión por `sid` (UUID v4) con TTL de 8 horas indexada por el ID del estudiante. Cuando el estudiante se autentica en un nuevo dispositivo, el backend sobreescribe el `sid` en Redis y revoca inmediatamente la sesión anterior mediante el WebSocket `/session/ws/{sid}`."*

---

### Pregunta 3: ¿Cómo escalaron el backend a 6 workers si Uvicorn corre procesos aislados? ¿Qué pasó con los WebSockets y las tareas periódicas?
- **Respuesta:**
  > *"Un proceso de Uvicorn solo usa un núcleo de CPU y queda limitado por el GIL de Python. Para la prueba de carga levantamos 6 workers (`run.py` y `deployment/docker-compose.prod.yml`). Esto nos obligó a resolver dos problemas de sistemas distribuidos:*  
  > *1. **WebSockets distribuidos:** Como cada proceso tiene su propia memoria RAM y sus sockets abiertos, creamos el bus de eventos en Redis Pub/Sub (`src/shared/ws_bus.py`). Cuando cualquier worker emite un aviso de llamado o cancelación, publica en Redis y todos los workers escuchan; el worker que tenga el socket del estudiante se encarga de enviárselo.*  
  > *2. **Tareas periódicas duplicadas:** El worker de inactividad debe correr cada 60 s. Si los 6 procesos lo ejecutaran, llamarían y cancelarían 6 veces a los mismos alumnos. Lo solucionamos implementando un **Leader Lock distribuido (`src/shared/leader_lock.py`)** con `SET leader_key worker_id NX PX 55000`. Solo el proceso que adquiere el lock ejecuta el ciclo."*

---

### Pregunta 4: ¿Qué ocurre si RabbitMQ o Expo Push fallan en plena hora punta? ¿El estudiante pierde su turno?
- **Respuesta:**
  > *"No, el sistema está diseñado bajo el principio de **degradación elegante**:*  
  > *1. En `src/shared/rabbitmq.py`, la publicación de eventos (`publish`) tiene un timeout estricto de 3 segundos y está envuelta en un bloque `try/except` de captura controlada. Si RabbitMQ se cae, se registra un `WARNING`, pero la transacción del turno en PostgreSQL ya se confirmó (`commit`). El estudiante tiene su turno asegurado.*  
  > *2. En cuanto a Expo Push (`src/shared/push.py`), si el servicio cloud de notificaciones responde 500 o tiene lentitud, no propagamos el error: el estudiante sigue viendo su llamado en vivo mediante el canal WebSocket.*  
  > *3. Y del lado de los consumidores (M5 - Seguimiento), si RabbitMQ reentrega un mensaje por falla de red (*at-least-once*), la inserción en PostgreSQL usa `ON CONFLICT DO NOTHING`, garantizando **idempotencia total** (`tests/test_resilience.py`)."*

---

### Pregunta 5: ¿Cuál es la diferencia en su código entre Design by Contract (DbC) y Programación Defensiva?
- **Respuesta:**
  > *"Cumplimos ambos criterios con propósitos y límites arquitectónicos claramente diferenciados:*  
  > *- **Programación Defensiva (en la frontera):** Protege al sistema contra entradas externas no confiables provenientes de clientes HTTP o scraping. Se implementa con esquemas Pydantic y en `src/shared/validacion.py` (validando formatos de UUID, longitud de tokens, expresiones regulares de código UNI y sanitización de HTML). Si falla, responde HTTP 422.*  
  > *- **Design by Contract (en el núcleo del dominio):** Regula las obligaciones y garantías entre componentes internos confiables mediante `requiere()` y `asegura()` en `src/shared/contratos.py`. Por ejemplo, `crear_turno` asume que los datos ya fueron saneados por la frontera, pero valida precondiciones invariantes (IDs mayores a cero) y asegura postcondiciones estrictas (que el total de turnos emitidos coincida con el correlativo y que el aforo no se haya sobrepasado). Si falla un contrato, es un defecto del software y arroja `ContratoViolado`."*

---

### Pregunta 6: ¿Qué problemas de runtime encontraron con Locust y cómo los resolvieron?
- **Respuesta:**
  > *"En la primera prueba de carga con 1000 usuarios encontramos un 11.7% de errores 500 debido a dos problemas graves de runtime:*  
  > *1. **Agotamiento del pool de conexiones:** El `ThreadedConnectionPool` de `psycopg2` lanzaba `PoolExhaustedError` de inmediato cuando las conexiones se ocupaban. Lo corregimos en `src/shared/db.py` configurando `minconn = maxconn = 15` para no pagar el costo de re-apretón TCP en Windows, y envolviendo el pool en un **semáforo con timeout de 10 segundos**. Ahora las peticiones esperan pacientemente en cola en lugar de fallar.*  
  > *2. **Bloqueo del Event Loop de asyncio:** El endpoint `/queue/join` era `async def` pero ejecutaba llamadas síncronas de base de datos dentro del hilo principal de asyncio, congelando a los demás usuarios. Lo corregimos delegando la transacción pesada al threadpool con `run_in_threadpool`. Con esto logramos subir de 305 a 729 peticiones por segundo y bajar el percentil 95 de 1.9s a 0.68s."*

---

### Pregunta 7: ¿Qué compone la Sección 16 del repositorio que se les exigió?
- **Respuesta:**
  > *"La Sección 16 del Proyecto Integrador exige una estructura estándar de repositorio profesional que superó la clásica división desordenada. Contamos con:*  
  > *- `src/`: Todo el código fuente del backend modular.*  
  > *- `tests/`: 76 pruebas automatizadas sin duplicados.*  
  > *- `docs/`: Documentación oficial, C4 en 4 niveles, vistas 4+1, ADRs y guiones.*  
  > *- `config/`: Esquema relacional SQL (`001_init.sql`), Alembic y especificación OpenAPI.*  
  > *- `deployment/`: Orquestación multi-worker en Docker Compose y Dockerfile.*  
  > *- `scripts/`: Herramientas de análisis de acoplamiento (`medir_acoplamiento.py`) y sincronización de túnel.*  
  > *- `benchmarks/`: Pruebas de carga con Locust y sembradores de datos.*  
  > *- `legacy/`: Registro de prototipos anteriores y decisiones superadas.*  
  > *- Archivos de raíz: `Dockerfile`, `docker-compose.yml`, `README.md`, `.env.example`, `.gitignore` y `CHANGELOG.md`."*
