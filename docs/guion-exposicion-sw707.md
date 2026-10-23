# ComedorUNI — Guion para exposición técnica SW707

**Duración total:** 40 minutos**Exposición:** 35 minutos**Preguntas y defensa:** 5 minutos**Corte técnico utilizado:** validaciones registradas el 15 de octubre de 2026**Equipo SW707:** Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas

> Este guion describe el código observado y separa sus capacidades actuales de las
> pruebas y mejoras pendientes. No afirmar que `v1.0` está lista: aún faltan pruebas
> automatizadas de negocio, concurrencia y tolerancia a fallos.

## 1. Objetivo y dos partes de la exposición

La exposición no es un recorrido pantalla por pantalla ni una lista de tecnologías.
La idea central es demostrar cómo fluye una operación desde la app hasta la base de
datos y qué garantías da realmente cada capa.

### Parte I — Introducción del proyecto y flujo de negocio (8 minutos)

Presentar el problema, quiénes usan el sistema, el flujo completo del estudiante y
la arquitectura. Aquí el profesor debe entender qué hace ComedorUNI, cuál es el
alcance real del prototipo y por qué hay retos de construcción no triviales.

### Parte II — Recorrido a nivel de código (27 minutos)

Seguir el mismo flujo en frontend, API, servicios, persistencia y eventos; explicar
contratos, entradas no confiables, problemas de runtime, dependencias, concurrencia,
resiliencia y evidencia. El recorrido no debe esconder las limitaciones.

### Defensa / preguntas (5 minutos)

Responder desde el código y distinguir siempre entre “existe”, “se ejecutó”,
“pasó una prueba” y “todavía es una propuesta”.

## 2. Cronograma exacto (40 minutos)

| Tiempo       | Parte / diapositiva               | Enfoque                                           |
| ------------ | --------------------------------- | ------------------------------------------------- |
| 00:00–00:30 | 1. Portada                        | Producto, integrantes y objetivo                  |
| 00:30–02:00 | 2. Problema y objetivo            | Necesidad, resultado y reto de construcción      |
| 02:00–03:30 | 3. Actores y alcance              | Estudiante, administrador y límites              |
| 03:30–06:00 | 4. Flujo completo                 | Identidad → turno → llamado → atención        |
| 06:00–08:00 | 5. Arquitectura real              | App, API, PostgreSQL, Redis, RabbitMQ             |
| 08:00–10:00 | 6. Mapa del código               | Rutas del repositorio y entrada de FastAPI        |
| 10:00–13:00 | 7. Identidad y sesión            | WebView, scraping, parseo, sesión y biometría   |
| 13:00–16:00 | 8. Solicitud de turno en frontend | Pantalla, estado y llamada HTTP                   |
| 16:00–19:00 | 9. Endpoint y contratos           | Validación, errores HTTP y postcondición        |
| 19:00–23:00 | 10. Persistencia y concurrencia   | Bloqueo, restricción, carrera y prueba necesaria |
| 23:00–26:30 | 11. Estados y tiempo real         | WebSocket, worker y llamado por grupos            |
| 26:30–29:00 | 12. Errores y resiliencia         | RabbitMQ, reintentos y límites                   |
| 29:00–31:00 | 13. Dependencias y runtime        | Transitivas, portabilidad y riesgos de arranque   |
| 31:00–33:00 | 14. Pruebas y evidencia           | Qué se probó y qué no                          |
| 33:00–35:00 | 15. Demo breve y cierre           | Smoke test, transición de vuelta al flujo        |
| 35:00–40:00 | 16. Preguntas                     | Defensa del diseño y limitaciones                |

## 3. Mensaje que debe quedar al final

> ComedorUNI es un prototipo modular que lleva el flujo de turnos desde una app Expo
> hasta FastAPI, PostgreSQL, Redis y RabbitMQ. El código ofrece endpoints, estado
> persistido, comunicación en tiempo real y consumidores asíncronos. Ya comprobamos
> arranque, compilación del cliente y salud HTTP; no hemos demostrado todavía con
> pruebas automatizadas la corrección bajo concurrencia ni la recuperación ante
> fallos. La siguiente prioridad para una línea base parcial defendible es probar y
> corregir capacidad, numeración, errores de publicación y contratos.

## 4. Guion por diapositiva

### Diapositiva 1 | ComedorUNI: de la cola al código | 0:30 | Parte I

**Idea clave:** Vamos a recorrer un sistema existente desde la necesidad del comedor
hasta las decisiones reales de implementación.

**En pantalla**

- Construcción de Software II — SW707
- Gestión de turnos virtuales del comedor universitario
- Integrantes: Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas

**Qué decir**

“Vamos a explicar ComedorUNI en dos partes. Primero, qué problema resuelve y cuál
es el flujo de negocio. Después vamos a seguir ese flujo por el código y revisar
qué garantías están implementadas y cuáles todavía necesitan pruebas. No vamos a
presentar como terminadas capacidades que no hemos validado.”

### Diapositiva 2 | Problema, objetivo y reto técnico | 1:30 | Parte I

**Idea clave:** La dificultad del producto no es mostrar un número; es asignar y
actualizar turnos de manera consistente cuando hay sesiones, capacidad y fallos.

**En pantalla**

- Problema: organizar solicitudes y llamados del comedor sin depender únicamente
  de una fila física.
- Objetivo: registrar turnos y permitir seguimiento del estado.
- Reto SW707: unicidad, límite de raciones, concurrencia, dependencias y recuperación.
- No hay medición disponible para afirmar cuánto redujo esperas o filas.

**Qué decir**

“El sistema busca ordenar la atención con una cola virtual. El reto de software está
en que la reserva tiene que respetar la capacidad incluso con solicitudes
simultáneas; además, la sesión y el estado tienen que seguir coherentes mientras la
app recibe llamados. No tenemos mediciones de operación real, así que hablamos del
objetivo del sistema, no de una mejora cuantificada.”

### Diapositiva 3 | Actores y límites del producto | 1:30 | Parte I

**Idea clave:** La experiencia implementada que vamos a seguir es la del estudiante;
la infraestructura y el portal son dependencias del flujo.

**En pantalla**

- Estudiante: acceso, menú, solicitar turno, ver estado, confirmar o salir.
- Administrador: configuración de turnos y menú expuesta en endpoints backend.
- Portal Alumnos UNI: sistema externo usado desde un WebView de la app.
- PostgreSQL: datos operativos; Redis: sesiones; RabbitMQ: eventos.
- Alcance del cliente actual: app móvil/web para estudiante; no se observó una
  interfaz administrativa completa en el frontend.

**Qué decir**

“El flujo que presentaremos es el del estudiante. Hay endpoints de configuración y
menú para administración en el backend, pero no vamos a inventar una consola
administrativa que no encontramos en la aplicación actual. Portal Alumnos, Expo
Push, base de datos, Redis y RabbitMQ aparecen como sistemas o servicios externos al
caso de uso del estudiante.”

### Diapositiva 4 | Flujo de negocio completo | 2:30 | Parte I

**Idea clave:** La pantalla es solo el comienzo: cada paso activa una operación
distinta en el cliente y el backend.

**En pantalla**

1. El estudiante abre el Portal UNI en WebView e inicia sesión allí.
2. La app lee HTML del portal y envía `/parse-data`.
3. El backend extrae datos, registra al estudiante y crea sesión `sid` en Redis.
4. La app solicita foto y envía `/verify-biometric`.
5. La app obtiene servicio activo y llama `POST /queue/join`.
6. La app muestra ticket; WebSocket recibe `LLAMADO` o cancelación.
7. El estudiante confirma; backend persiste estado y emite eventos.
8. Worker/consumers hacen seguimiento y notifican cuando corresponde.

**Qué decir**

“Primero hay autenticación institucional en un WebView; el backend no hace OAuth
directo con Google. Luego la app envía fragmentos HTML para que el backend los
interprete. Después hay verificación biométrica con foto de referencia guardada en
la sesión. Ya autenticado, el estudiante solicita turno. La cola se actualiza
mediante WebSocket, y la confirmación cambia el estado. Algunos pasos laterales se
publican por RabbitMQ. Este flujo está representado en el prototipo visual de Figma,
pero ese mockup no está conectado al backend.”

**Transición:** “Ahora sigamos la solicitud de turno hasta las funciones que la
atienden.”

### Diapositiva 5 | Arquitectura que existe en el repositorio | 2:00 | Parte I

**Idea clave:** La arquitectura actual es un monolito modular con infraestructura
externa, no microservicios.

**En pantalla**

- Frontend: React Native + Expo Router + TypeScript.
- Backend: FastAPI/Uvicorn, routers por módulo y tareas de fondo en el mismo proceso.
- PostgreSQL: estudiantes, turnos, configuración y menú.
- Redis: sesiones temporales identificadas por `sid`.
- RabbitMQ: eventos; consumers M4 (push) y M5 (seguimiento).
- Worker de inactividad y WebSockets viven dentro del proceso backend.

**Qué decir**

“`main.py` registra los routers y en el lifespan lanza el worker y el intento de
conexión de los consumers. Eso significa que son procesos/tareas del mismo backend,
no despliegues separados. Redis guarda sesiones; no se encontró coordinación de
WebSockets entre réplicas. RabbitMQ separa algunas tareas, pero el hecho de
publicar un evento no basta para decir que tenemos entrega garantizada.”

### Diapositiva 6 | Mapa del código: dónde comienza cada capa | 2:00 | Parte II

**Idea clave:** Para explicar el sistema, saltar desde la app hacia el router,
servicio y persistencia siguiendo una operación concreta.

**En pantalla**

- Inicio FastAPI: `backend/src/main.py`.
- Autenticación: `backend/src/modules/auth/`.
- Cola: `backend/src/modules/queues/router.py` y `service.py`.
- Persistencia SQL: `backend/src/shared/db.py`; esquema en
  `backend/migrations/001_init.sql`.
- Frontend: `frontend/src/app/index.tsx`, `home.tsx`, `ticket.tsx`.
- Eventos: `shared/rabbitmq.py`, consumers `notifications/` y `tracking/`.

**Qué decir**

“El punto de entrada es `main.py`. La app no llama SQL: envía HTTP o WebSocket.
El router recibe el request, consulta sesión y delega operaciones a servicios. El
servicio usa PostgreSQL a través de `get_db_conn`. Abran primero
`home.tsx::handleJoinQueue`, luego `queues/router.py::join_queue`, y por último
`queues/service.py::crear_turno`; así se ve la cadena completa en pocos minutos.”

**Código a abrir**

- `backend/src/main.py:52` — lifespan; `:74` — health; routers registrados al final.
- `frontend/src/app/home.tsx:95` — `handleJoinQueue`.
- `backend/src/modules/queues/router.py:85` — `join_queue`.
- `backend/src/modules/queues/service.py:255` — `crear_turno`.

### Diapositiva 7 | Acceso: Portal, parseo, sesión y biometría | 3:00 | Parte II

**Idea clave:** Los datos del portal y la foto llegan desde el cliente; deben
tratarse como entrada externa y explicarse junto con su manejo de privacidad.

**En pantalla**

- `index.tsx`: WebView hacia Portal Alumnos, extracción de HTML y POST `/parse-data`.
- `auth/router.py::parse_data`: parsea, persiste estudiante y genera `sid`.
- `auth/service.py::parse_student_data`: BeautifulSoup extrae perfil y créditos.
- `auth/redis_store.py`: sesión por `sid`; no JWT.
- `auth/router.py::verify_biometric`: valida sesión/foto y llama a DeepFace.
- `biometric.py::compare_faces`: compara imagen de referencia y captura.

**Qué decir**

“El cliente abre el portal, detecta que ya llegó a `/home` y ejecuta el scraper.
El backend recibe el HTML; `parse_student_data` busca selectores y tabla de cursos.
Luego `upsert_estudiante` persiste el registro y Redis mantiene una sesión con
`sid`. La app manda la foto capturada a `/verify-biometric`; el endpoint exige
sesión y foto de referencia antes de comparar. En esta frontera aún hay riesgos:
los campos pueden venir incompletos, el HTML del portal puede cambiar y el coste
de DeepFace/OpenCV/TensorFlow puede afectar instalación, memoria y arranque.
Presenten la foto como dato sensible y no usen imágenes reales en la demo.”

**Contrato a explicar**

- Pre: HTML recibido y sesión válida para biometría; foto de referencia disponible.
- Post: perfil persistido y `sid` creado; biometría responde verificado/no verificado.
- Límite: `ParseDataRequest` tiene campos con valores vacíos por defecto; hace falta
  comprobar casos inválidos y la estructura cambiante del portal.

**Código a abrir**

- `frontend/src/app/index.tsx:96` — script WebView; `:126` — `onMessage`;
  `:292` — `verifyBiometric`.
- `backend/src/modules/auth/router.py:22` — `/parse-data`;
  `:91` — `/verify-biometric`.
- `backend/src/modules/auth/service.py:8` — parseo.
- `backend/src/modules/auth/biometric.py:16` — comparación.

### Diapositiva 8 | Solicitar un turno: estado del cliente | 3:00 | Parte II

**Idea clave:** El frontend protege la interacción de UX; la regla de negocio debe
volver a validarse en backend.

**En pantalla**

- `home.tsx` carga menú, servicio activo y estado de cola.
- `handleJoinQueue` exige usuario y servicio activo antes del request.
- Envía `sid` y `tipo` por `POST /queue/join`.
- En éxito actualiza `UserContext` y navega a `/ticket`.
- En error muestra `detail`; fallo de red muestra alerta.
- Las URL vienen de `EXPO_PUBLIC_API_URL` / `EXPO_PUBLIC_WS_URL`.

**Qué decir**

“En Home se consulta el servicio activo y el menú. Al presionar solicitar turno,
`handleJoinQueue` impide el doble clic con `joiningQueue`, verifica que haya una
sesión local y que el servicio esté activo, y envía `sid` y tipo. Si el backend
acepta, actualiza el contexto del usuario y abre el ticket. Estas validaciones son
útiles para la experiencia, pero un cliente no es una barrera de seguridad: los
checks de identidad, duplicado y capacidad tienen que ser autoritativos en
backend.”

**Código a abrir**

- `frontend/src/app/home.tsx:39` — estado/componente; `:95` — solicitud.
- `frontend/src/constants/UserContext.tsx:8` — modelo `QueueInfo`.
- `frontend/src/constants/api.ts:1` — configuración de URL.

### Diapositiva 9 | Endpoint de cola: precondiciones y errores | 3:00 | Parte II

**Idea clave:** Un contrato sirve para acordar qué tiene que ser cierto antes y
después de llamar al endpoint, no solo documentar el nombre de la ruta.

**En pantalla**

- `JoinQueueRequest`: `sid` y `tipo`.
- `_require_session`: 401 si la sesión es inexistente o expirada.
- `/queue/join`: comprueba turno activo, estudiante, turno diario, duplicado y cupo.
- `/queue/status`: devuelve estado, posición, turno actual y grupo si fue atendido.
- `/queue/confirm`: espera turno activo; cambia y produce efectos laterales.
- Los códigos actuales no son perfectamente uniformes: capacidad agotada da 400;
  conflictos y faltantes usan 409/404 según condición.

**Qué decir**

“En el router se ve el contrato observable. La sesión debe ser válida; debe existir
servicio activo y estudiante registrado; no debe haber un turno anterior conflictivo.
Si está lleno, no se debe crear el turno. Si la solicitud prospera, se crea un único
turno y se devuelve su número y posición. En código actual, algunas fallas se
representan con 400, 404, 409 o 503. Antes de presentar, tengan claro que los códigos
de capacidad y conflicto deben uniformarse y probarse.”

**Tres contratos concretos**

1. `join_queue`: pre: sesión vigente, turno diario abierto, alumno existente,
   sin duplicado y capacidad disponible; post: un turno persistido y respuesta
   consistente. **Hoy la capacidad no está en la misma transacción que el insert.**
2. `confirm_presence`: pre: sesión y turno en estado que permite confirmar; post:
   estado `ATENDIDO` o renovación de presencia, con respuesta y eventos esperados.
3. `parse_data`: pre: HTML del portal parseable con identificadores mínimos; post:
   alumno upsert y sesión creada. **Las validaciones de campos vacíos todavía deben
   endurecerse.**

**Código a abrir**

- `backend/src/modules/queues/router.py:40` — `_require_session`.
- `backend/src/modules/queues/router.py:85` — `join_queue`;
  `:137` — status; `:163` — confirm.
- `backend/src/modules/queues/schemas.py:5` — request/response de cola.

### Diapositiva 10 | Base de datos y carrera de concurrencia | 4:00 | Parte II

**Idea clave:** Existe serialización parcial para numerar, pero el límite de cupos
se calcula fuera de ella; no presentar como resuelto el escenario de concurrencia.

**En pantalla**

- `raciones_usadas()` hace un COUNT de turnos no cancelados.
- El endpoint calcula `restantes` antes de invocar `crear_turno()`.
- `crear_turno()` bloquea la fila diaria con `SELECT ... FOR UPDATE`.
- La numeración usa `COUNT(*) + 1` excluyendo cancelados y atendidos.
- Índice único `(turno_dia_id, numero_turno)` y unicidad parcial por estudiante.
- Riesgos: sobrecupo entre transacciones y reutilización de número histórico.

**Qué decir**

“Aquí está el punto más importante para SW707. El router lee capacidad usando una
conexión y después `crear_turno` abre otra. El bloqueo `FOR UPDATE` serializa el
cálculo e inserción de número entre quienes llegan a esa función, pero no protege
la lectura anterior de raciones. Si quedan una ración y dos requests leen el mismo
contador antes de serializarse, ambos podrían pasar la validación. Además, el
COUNT del número excluye `CANCELADO` y `ATENDIDO`, mientras el índice único
histórico sigue reservando números. Hay que mover chequeo de cupo, numeración e
inserción a una transacción común y probarla con PostgreSQL real.”

**Prueba concurrente reproducible propuesta — aún no implementada**

1. Crear turno diario de prueba con capacidad restante exactamente 1.
2. Preparar N estudiantes/sesiones válidas y lanzar N solicitudes simultáneas a
   `POST /queue/join`.
3. Consultar PostgreSQL, no confiar solo en las respuestas HTTP.
4. Aceptar solo si hay exactamente una asignación nueva, el aforo no se excede y no
   hay números duplicados; las otras solicitudes reciben conflicto/cupo agotado.
5. Repetir con el mismo estudiante concurrente y comprobar como máximo un turno
   activo.

No decir que esta prueba pasó. En `backend/tests/` solo está `.gitkeep`.

**Código a abrir**

- `backend/src/modules/queues/router.py:102` — duplicado; `:109` — lectura de cupo;
  `:114` — llamada a crear.
- `backend/src/modules/queues/service.py:149` — conteo;
  `:255` — bloqueo y numeración.
- `backend/migrations/001_init.sql:80` — índices únicos.

### Diapositiva 11 | Máquina de estados y tiempo real | 3:30 | Parte II

**Idea clave:** WebSocket da notificaciones a clientes conectados; la persistencia
SQL sigue siendo la fuente del estado.

**En pantalla**

- Estados observados: `ESPERANDO`, `LLAMADO`, `ATENDIDO`, `CANCELADO`.
- Ticket solicita estado inicial y abre `/queue/ws/{sid}`.
- `manager` es local al proceso.
- Worker se despierta cada 60 s y procesa pings, cancelaciones y siguiente grupo.
- `llamar_siguiente` elige grupo según `ceil(raciones_max / 10)`.
- WebSocket no es un bus entre varias réplicas.

**Qué decir**

“El ticket establece WebSocket y traduce mensajes a UI. El backend verifica el `sid`
y asocia la conexión en memoria. El worker corre cada minuto: detecta falta de
respuesta, cancela llamados vencidos y llama al siguiente grupo. `llamar_siguiente`
usa una operación SQL para actualizar de ESPERANDO a LLAMADO. Al confirmar, la UI
actualiza estado y libera siguiente grupo. Si se escala a dos procesos, cada uno
tendría su propio manager; actualmente no hay Redis Pub/Sub ni mecanismo distribuido
en ese código.”

**Código a abrir**

- `frontend/src/app/ticket.tsx:35` — pantalla; `:65` — WebSocket;
  `:130` — confirmar.
- `backend/src/modules/queues/router.py:241` — WebSocket servidor.
- `backend/src/modules/queues/worker.py:21` — worker.
- `backend/src/modules/reassignment/service.py:7` — siguiente grupo.

### Diapositiva 12 | Errores, eventos y resiliencia real | 2:30 | Parte II

**Idea clave:** Hay mecanismos de resiliencia, pero cada uno tiene límites que deben
explicarse.

**En pantalla**

- Reintentos iniciales de consumers: hasta 30 intentos separados 3 s (~90 s).
- Exchange/colas durables y mensajes persistentes en publicación.
- Cliente vuelve a conectar sesión WebSocket tras fallo de red.
- `publish()` captura excepción y solo hace `print`: el request puede continuar.
- Consumers capturan excepciones dentro del contexto de procesamiento; revisar ack,
  retry e idempotencia.
- Worker captura excepción amplia; se registra en consola.

**Qué decir**

“Hay al menos dos mecanismos que vale la pena explicar: reintento de conexión al
arranque y colas/mensajes persistentes; además, el cliente de sesión reconecta su
WebSocket. Sin embargo, eso no prueba entrega de negocio. `publish` absorbe la
excepción, así que un endpoint puede continuar y parecer exitoso aunque no publique.
Los consumidores atrapan errores dentro de `message.process`; hay que probar la
política de ack/nack y evitar confirmar mensajes no procesados. No hay evidencia de
outbox, DLQ o idempotencia completa.”

**Política que se propone completar**

- Validación: 422 en cuerpo inválido; 401/403 para identidad/autorización; 404 para
  recurso ausente; 409 para conflicto; 503 cuando la dependencia crítica no permite
  cumplir.
- SQL: rollback al fallar; no responder éxito antes del commit necesario.
- Eventos: timeout, ack/nack explícito, reintento acotado, idempotencia y registro.
- Logs: reemplazar `print` por logs estructurados, sin foto, HTML, token, contraseña
  ni datos personales innecesarios.

### Diapositiva 13 | Dependencias y problemas de runtime | 2:00 | Parte II

**Idea clave:** El lockfile frontend hace reproducible el árbol Node instalado; el
backend no fija versiones y carga librerías nativas pesadas.

**En pantalla**

- Backend `requirements.txt`: dependencias directas sin versiones exactas ni lock
  del grafo transitivo.
- Frontend `package.json`: rangos; `package-lock.json` fija resolución para `npm ci`.
- Transitivas observadas: Expo → Metro/config; `expo-router` → runtime/CLI;
  `expo-notifications` → utilidades adicionales.
- Riesgo de runtime 1: Compose publica PostgreSQL `5433:5432`; backend por defecto
  busca `5432`.
- Riesgo de runtime 2: DeepFace/OpenCV/TensorFlow pueden aumentar instalación,
  memoria y arranque.
- Auditoría npm del corte 15/10/2026: 53 alertas (17 moderadas, 35 altas, 1 crítica).

**Qué decir**

“En el cliente tenemos lockfile y `npm ci`; eso fija versiones directas y
transitivas para el equipo. El manifiesto solo no basta porque contiene rangos.
En backend, `requirements.txt` lista paquetes directos sin pins; no podemos
reproducir exactamente el entorno ni decir que hicimos inventario completo de
transitivas. Dos problemas concretos de runtime: el puerto local de PostgreSQL y
el coste de las dependencias de visión. En la auditoría npm del 15 de octubre se
reportaron alertas; no aplicamos `audit fix` automáticamente porque podía cambiar
el grafo. Hay que volver a auditar antes de entrega.”

### Diapositiva 14 | Qué está probado | 2:00 | Parte II

**Idea clave:** La evidencia de infraestructura y compilación no sustituye pruebas
de comportamiento.

**En pantalla**

- `compileall`: sintaxis Python sin errores.
- Compose `config -q` y servicios PostgreSQL, Redis, RabbitMQ levantados.
- API inició; consumers M4/M5 conectados.
- `GET /ping`: HTTP 200; `/openapi.json` disponible.
- Frontend: `npx tsc --noEmit`, lint sin errores (13 warnings) y export web OK.
- No hay tests de cola, contratos, concurrencia o fallos; no hay suite frontend.

**Qué decir**

“Lo aprobado por la evidencia es arranque y calidad estática: Python compila,
Compose valida, servicios arrancan, la API responde y el frontend compila/exporta.
Lint tuvo cero errores pero 13 advertencias. npm reportó 53 alertas. No hay pruebas
automatizadas de negocio, así que no voy a decir que el flujo completo, el límite
de raciones o la recuperación ante RabbitMQ están comprobados. El smoke test solo
prueba conectividad básica.”

### Diapositiva 15 | Demo de 2 minutos y cierre | 2:00 | Parte II

**Idea clave:** La demo sirve para confirmar conectividad, no para declarar aprobada
la cola.

**En pantalla**

- Mostrar diagrama/flujo interactivo de Figma (datos ficticios).
- Mostrar comando de salud del backend y respuesta.
- Abrir una llamada de frontend y el handler backend correspondiente.
- Cerrar con brecha de concurrencia y próximo paso verificable.

**Demo sugerida**

1. Mostrar en Figma el camino login → Home → solicitar turno → llamado → confirmar.
   Indicar: “Esta maqueta es simulada; no realiza llamadas al backend”.
2. Si el entorno ya está preparado, mostrar respuesta de `GET /ping`:
   `Invoke-RestMethod http://localhost:8000/ping`.
3. Abrir `home.tsx::handleJoinQueue` y seguir a `queues/router.py::join_queue`.
4. Detenerse antes de crear datos reales. No usar una cuenta real, foto real,
   credenciales del portal ni forzar concurrencia sobre datos de producción.
5. Cerrar: “La siguiente prueba a implementar es N solicitudes simultáneas con un
   cupo restante, midiendo el estado final en PostgreSQL.”

### Diapositiva 16 | Preguntas y defensa | 5:00 | Q&A

**Idea clave:** Contestar con el código y evidencia; nombrar expresamente lo pendiente.

**Preguntas probables y respuesta sugerida**

**¿La concurrencia ya está resuelta por `FOR UPDATE`?**
No por completo. El bloqueo serializa el cálculo/inserción en `crear_turno`, pero la
lectura de capacidad está antes y usa otra conexión. Además, el cálculo de número
excluye estados que siguen sujetos al índice único histórico. Falta una transacción
que coordine capacidad, numeración e insert, y una prueba paralela con PostgreSQL.

**¿Qué evidencia confirma el funcionamiento?**
La API respondió `/ping`, servicios arrancaron y los consumers conectaron. Frontend
pasó TypeScript/export; lint tuvo 0 errores y 13 advertencias. Eso prueba arranque y
empaquetado, no un flujo real de reserva ni rendimiento.

**¿Cómo se autentica? ¿Hay JWT?**
La sesión es un `sid` temporal en Redis. La app navega al Portal Alumnos con WebView,
scrapea información y solicita verificación biométrica. No se encontró JWT en este
flujo.

**¿Qué hacen ante caída de RabbitMQ?**
Al arranque se reintenta conectar hasta 30 veces con pausas de 3 s. La publicación
usa conexión robusta y mensaje persistente, pero `publish` captura la excepción sin
propagarla. No podemos garantizar entrega sin pérdida; falta prueba de caída,
ack/retry/idempotencia y política operativa.

**¿Por qué no microservicios?**
El código observado es un monolito modular y no hay métricas que justifiquen separar
procesos. El worker y consumers viven en el mismo backend. Separarlos sin requisito
o evidencia agregaría complejidad; por ahora se prioriza corregir contratos y datos.

**¿Qué cambiarían primero?**
Agregar prueba concurrente, mover control de capacidad y numeración a transacción
común, definir errores uniformes y asegurar que fallos de publicación no se oculten.

**Frase de cierre**

“Tenemos un flujo de producto y una arquitectura identificable; también sabemos
dónde no podemos prometer una garantía todavía. El valor del parcial es demostrar
el código y cerrar esas brechas con pruebas reproducibles.”

## 5. Rúbrica SW707: cómo cubrir cada punto durante la exposición

| Criterio                | Qué mostrar o decir                                                                             | Estado honesto                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Funcionalidad           | Recorrer login/sesión, solicitar turno, ticket y confirmación                                  | Código de flujo existe; end-to-end automatizado no probado                             |
| Dependencias            | `requirements.txt`, `package.json`, `package-lock.json`, ejemplos transitivos y auditoría | Lock cliente sí; backend sin pins/lock; análisis transitivo incompleto                |
| Runtime                 | Puerto Compose/backend; coste de DeepFace/OpenCV/TensorFlow; dependencia del HTML institucional  | Analizado; falta prueba medida de todos los escenarios                                  |
| Contratos               | `parse_data`, `join_queue`, `confirm_presence`; pre/post/invariantes                       | Contratos descritos; cobertura automatizada ausente                                     |
| Programación defensiva | Validaciones de `sid`, tipo de turno, estado, campos recibidos                                 | Hay validaciones en rutas; falta revisión y prueba sistemática de entradas inválidas |
| Errores/excepciones     | HTTPException y respuestas del frontend; capturas `print` en worker/publish                    | Manejo parcial e inconsistente; logs estructurados pendientes                           |
| Concurrencia            | `FOR UPDATE`, índice parcial, carrera de capacidad fuera del bloqueo                          | Protección parcial; sin prueba reproducible                                            |
| Resiliencia             | Reintentos startup, durable/persistent RabbitMQ, reconexión cliente WebSocket                   | Mecanismos existentes; entrega/recuperación no demostradas                             |
| Pruebas                 | `compileall`, Compose, `/ping`, TypeScript, lint, export web                                 | Smoke/estático ejecutados; sin tests negocio/concurrencia/fallos                       |
| Documentación          | README, documento técnico y cronograma hasta parcial                                            | En `docs/`; presentar junto con límites del corte                                    |

## 6. Mapa técnico de lectura previa

Antes de exponer, marcar estos archivos y practicar saltos rápidos en VS Code:

| Orden | Archivo / símbolo                                                                                     | Qué explicar                                 |
| ----- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------- |
| 1     | `backend/src/main.py` — `lifespan`, `ping`, `include_router`                                  | Arranque, healthcheck, worker y consumers     |
| 2     | `frontend/src/app/index.tsx` — WebView, `onMessage`, `verifyBiometric`                          | Login institucional, entrada HTML, biometría |
| 3     | `backend/src/modules/auth/router.py` — `parse_data`, `verify_biometric`, `get_me`             | Persistencia y sesión                        |
| 4     | `backend/src/modules/auth/service.py` — `parse_student_data`                                      | Parseo por selectores y cursos                |
| 5     | `frontend/src/app/home.tsx` — `handleJoinQueue`                                                   | Solicitud del cliente                         |
| 6     | `backend/src/modules/queues/router.py` — `join_queue`, `queue_status`, `confirm_presence`     | Contrato, validación y side effects          |
| 7     | `backend/src/modules/queues/service.py` — `raciones_usadas`, `crear_turno`, `confirmar_turno` | SQL, transacción y riesgo de carrera         |
| 8     | `backend/migrations/001_init.sql` — `turnos`, índices                                            | Estados e integridad en DB                    |
| 9     | `frontend/src/app/ticket.tsx` — `connectWS`, `handleWsMessage`, `handleConfirm`               | Actualización de ticket                      |
| 10    | `backend/src/modules/queues/worker.py` y `reassignment/service.py`                                 | Expiración y llamado de grupos               |
| 11    | `backend/src/shared/rabbitmq.py` y consumers M4/M5                                                   | Publicación, ack y manejo de errores         |
| 12    | `backend/requirements.txt`, `frontend/src/package.json` y lockfile                                 | Dependencias y reproducibilidad               |

## 7. Reglas para la defensa

- No decir “pruebas completas”: decir cuáles comandos corrieron y qué verificó cada uno.
- No afirmar “no hay errores” usando solo `/ping`: ese endpoint no ejercita reservas.
- No llamar “resiliencia garantizada” a un bucle de reintento de arranque.
- No asegurar “no hay duplicados” sin distinguir índice único de regla de capacidad.
- No exponer HTML institucional, foto facial, `sid`, token push, correo o credenciales.
- No presentar el prototipo de Figma como producto conectado; todo dato visual debe ser
  ficticio y toda transición simulada debe identificarse.
- Si el profesor pregunta por una carencia, nombrarla y explicar prueba/cambio concreto
  que la cerraría.

## 8. Preparación antes de la exposición

- Instalar dependencias y arrancar PostgreSQL/Redis/RabbitMQ con anticipación; evitar
  instalar DeepFace/TensorFlow por primera vez frente al profesor.
- Dejar VS Code abierto en el repositorio y abrir las doce ubicaciones de la tabla.
- Tener lista la respuesta `/ping` o una captura del smoke test fechada; no depender de
  conectividad institucional durante la presentación.
- Abrir el prototipo Figma con datos ficticios y probar todos los enlaces, incluidos
  error, agotado y cancelado.
- Reservar cinco minutos para preguntas; si el tiempo se acorta, reducir la demo, no
  eliminar el bloque de concurrencia/limitaciones.

## 9. Guion para explicar las capturas y los diagramas

La presentación incluye seis láminas visuales. Señala cada caja en el orden numerado
y explica qué componente envía la información, qué recibe y dónde se procesa. Las
cifras y los identificadores de ejemplo son ficticios.

| Diapositiva | Recurso visual                                       | Punto que debe quedar claro                                                     |
| ----------- | ---------------------------------------------------- | ------------------------------------------------------------------------------- |
| 4           | `resources/img/exposicion-flujo-general.png`       | Recorrido del estudiante y captura real de la pantalla inicial de Figma Make.   |
| 7           | `resources/img/exposicion-identidad-sesion.png`    | HTML scrapeado, datos enviados a `/parse-data`, persistencia y sesión Redis. |
| 9           | `resources/img/exposicion-contrato-cola.png`       | Cuerpo JSON, validaciones del endpoint, respuesta y códigos de error.          |
| 10          | `resources/img/exposicion-concurrencia.png`        | Por qué el bloqueo actual no protege la lectura previa de capacidad.           |
| 11          | `resources/img/exposicion-estados-tiempo-real.png` | Estados del turno, eventos WebSocket y trabajo del worker.                      |
| 15          | `resources/img/exposicion-demo.png`                | Cómo enseñar el prototipo y el código sin crear datos reales.                |

### Diapositiva 4 — Pantalla Figma frente al sistema conectado

**Señalar:** primero la captura del teléfono y luego las seis etapas del flujo.

**Decir:** “Esta es una captura de la pantalla de acceso que vemos en Figma Make.
Sirve para explicar la experiencia, pero no es una captura de una sesión real ni una
prueba de conexión al backend. En el sistema, la app abre el Portal UNI en WebView,
lee HTML, y luego hace solicitudes a FastAPI. El ticket usa HTTP para crear y
consultar el turno y WebSocket para recibir cambios.”

No pedir al público que ingrese credenciales ni afirmar que el prototipo mostrado
ejecuta las llamadas descritas.

### Diapositiva 7 — Qué datos se envían en el acceso

**Señalar:** del WebView al frontend, luego `/parse-data`, PostgreSQL y Redis.

**Decir:** “El WebView obtiene tres páginas HTML —inicio, cursos y datos personales—.
`onMessage` las recibe y el frontend envía `home_html`, `cursos_html`, `datos_html`
y `device_id` a `POST /parse-data`. El backend extrae los campos, hace upsert del
estudiante y crea una sesión `sid` en Redis. `ParseDataResponse` incluye
`sid`, `nombre`, `codigo`, `email`, `creditos_llevados` y `session_conflict`; no es
un JWT. Después, `POST /verify-biometric` recibe `sid` y `photo_base64` y responde
con `verified`, `distance` y `message`.”

**Código a mostrar:** `frontend/src/app/index.tsx::onMessage`,
`backend/src/modules/auth/router.py::parse_data` y `verify_biometric`,
`backend/src/modules/auth/service.py::parse_student_data` y
`backend/src/modules/auth/redis_store.py`.

### Diapositiva 9 — Request y response de una solicitud de turno

**Señalar:** el JSON que sale de la app, las validaciones del router y el response
model.

**Decir:** “Al pulsar solicitar turno, `handleJoinQueue` envía este cuerpo a
`POST /queue/join`: `{"sid":"sid-ficticio","tipo":"ALMUERZO"}`. El endpoint valida
la sesión, el servicio activo, que el estudiante exista, que no tenga un turno
conflictivo y que haya capacidad. Si se acepta, `JoinQueueResponse` devuelve
`numero_turno`, `tipo`, `posicion`, `raciones_restantes` y `mensaje`. Por ejemplo,
el 409 representa un conflicto y el 503 que el turno diario todavía no está
habilitado. Los códigos del comportamiento actual no están completamente
uniformados.”

Aclara que el frontend usa la respuesta para actualizar `UserContext` y navegar a
`/ticket`; no calcula ni autoriza por sí mismo el cupo. El agotamiento actualmente
responde 400.

### Diapositiva 10 — Qué protege y qué no protege `FOR UPDATE`

**Señalar:** los dos `COUNT` concurrentes y después el bloqueo en
`crear_turno()`.

**Decir:** “Dos requests pueden leer que queda una ración antes de que cualquiera
entre a `crear_turno()`. Luego `FOR UPDATE` serializa la numeración e inserción,
pero la decisión de aceptar ya se tomó. Por eso no concluimos que la capacidad esté
protegida. La corrección debe hacer que validar cupo, numerar e insertar compartan
una operación transaccional, y se debe demostrar con requests simultáneos contra
PostgreSQL.”

Indica expresamente que el diagrama explica un riesgo inferido del orden del código;
no muestra una prueba de sobrecupo que se haya ejecutado.

### Diapositiva 11 — Eventos, estado y confirmación

**Señalar:** `ESPERANDO -> LLAMADO -> ATENDIDO` y la salida a `CANCELADO`.

**Decir:** “Al entrar al ticket, el cliente consulta `GET /queue/status` y abre
`/queue/ws/{sid}`. El cliente recibe mensajes como `llamado`, `estado` o
`cancelado`, y actualiza la pantalla. Cuando confirma, envía
`POST /queue/confirm` con `{"sid":"sid-ficticio"}`; el backend devuelve el estado
y, cuando aplica, `turno_asignado`. El worker revisa inactividad cada 60 segundos.
El manager de WebSocket vive en memoria en el proceso actual; no afirmamos
coordinación entre réplicas.”

La cifra de tres minutos representa el plazo de confirmación explicado por el flujo;
no la presentes como garantía de entrega ni como resultado de una prueba automática.
El Figma puede simular la transición; el evento real procede del backend.

### Diapositiva 15 — Demo segura de cierre

**Señalar:** la captura y luego el recorrido del request en VS Code.

1. Muestra la pantalla de Figma y di: “Es un mockup visual, no está conectado”.
2. Si el backend está preparado, ejecuta `Invoke-RestMethod http://localhost:8000/ping` y explica que solo confirma salud HTTP.
3. Abre `home.tsx::handleJoinQueue`, sigue `POST /queue/join` hasta
   `queues/router.py::join_queue` y enseña `JoinQueueResponse`.
4. Cierra mencionando la carrera de capacidad y la prueba concurrente pendiente.

No uses una cuenta del Portal UNI, fotos faciales, un `sid` real ni datos de
estudiantes en la exposición.
