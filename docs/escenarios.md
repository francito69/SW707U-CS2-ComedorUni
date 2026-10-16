Este documento define los escenarios de calidad para el sistema ComedorUNI, estructurados según la norma **ISO/IEC 25010:2023**, especificando de forma explícita las seis partes requeridas para cada atributo crítico del sistema.

Se escribieron cinco escenarios a propósito de que no todos apunten a lo mismo: el sistema no solo tiene que responder rápido, también tiene que no perder cupos, no dejar que un estudiante se cuele con dos turnos, no perder eventos si algo se cae, y no arrastrar hoyos de seguridad en la configuración.

> Estos escenarios son objetivos de aceptación, no resultados ya alcanzados. El estado
> actual no incluye pruebas de carga, tolerancia a fallos ni despliegue con varias
> réplicas; los componentes Redis Pub/Sub, outbox y mecanismos de recuperación se
> consideran opciones de evolución que deben justificarse e implementarse antes de
> presentarlos como capacidades reales.

---

# Escenarios de Calidad — ComedorUNI

## 1. Adecuación Funcional (Corrección Funcional)

### Escenario 1: Asignación atómica de cupos en concurrencia masiva

* **Fuente:** Estudiantes concurrentes.
* **Estímulo:** 100 estudiantes envían una solicitud de turno simultáneamente cuando solo resta 1 ración disponible en el bloque actual.
* **Artefacto:** Módulo de asignación de turnos (`router.py`, `service.py`) y base de datos PostgreSQL.
* **Entorno:** Operación normal en hora pico durante la apertura del proceso de reserva de raciones.
* **Respuesta:** El sistema ejecuta la validación de capacidad y la reserva dentro de una transacción atómica con bloqueo de filas (`FOR UPDATE`), asignando el último turno a exactamente una solicitud y rechazando las 99 restantes con un código de estado HTTP `409 Conflict` o `422 Unprocessable Entity`.
* **Medida:** Exactamente 0 raciones asignadas por encima del límite máximo del servicio y 0 números de turno duplicados generados en la base de datos.
* **Instrumento:** Script de carga con `k6` o Locust que envía las 100 solicitudes simultáneas, seguido de una consulta SQL sobre PostgreSQL que verifica que solo se asignó una ración y que no hay turnos duplicados. Lo ejecuta el equipo de QA o el responsable de pruebas de rendimiento.


---

## 2. Seguridad (Integridad y Autenticación)

### Escenario 2: Prevención de turnos duplicados por un mismo estudiante

* **Fuente:** Estudiante autenticado o script malicioso.
* **Estímulo:** Envío de dos o más peticiones HTTP POST simultáneas usando el mismo `sid` de sesión activa para solicitar un turno en el mismo turno diario.
* **Artefacto:** Base de datos PostgreSQL (índice único parcial sobre `estudiante_id` y `turno_dia_id`).
* **Entorno:** Sesión activa con credenciales válidas.
* **Respuesta:** La capa de persistencia intercepta el intento de inserción redundante mediante la restricción del índice único parcial, aborta la transacción secundaria y la API responde con un error explícito HTTP `409 Conflict`.
* **Medida:** 0 estudiantes registrados con más de 1 turno en estado activo (`ESPERANDO` o `LLAMADO`) para un mismo bloque diario.
* **Instrumento:** Colección de Postman ejecutada con Newman, o script `pytest`/`httpx`, que envía peticiones simultáneas con el mismo `sid` y verifica la respuesta HTTP `409` y el estado final en PostgreSQL. Lo ejecuta el equipo de QA o el responsable de pruebas de seguridad.


---

## 3. Fiabilidad (Tolerancia a Fallos)

### Escenario 3: Resiliencia del worker ante fallos en el broker de mensajería

* **Fuente:** Interrupción de infraestructura de red o caída del servicio RabbitMQ.
* **Estímulo:** RabbitMQ se detiene o pierde conexión en el instante en que el worker de inactividad intenta publicar un evento de cancelación por turno expirado.
* **Artefacto:** Worker de inactividad (`worker.py`) y componente de publicación de eventos (`publish()`).
* **Entorno:** Sistema en ejecución continua con base de datos PostgreSQL operativa y RabbitMQ no disponible.
* **Respuesta:** El backend no pierde el estado procesado en la base de datos, captura la excepción de red, registra el evento en una tabla de persistencia temporal (o cola local en memoria) y reintenta la publicación con un patrón de reintento exponencial hasta restablecer la comunicación.
* **Medida:** 0% de eventos de cancelación perdidos y reconexión automática garantizada en menos de 10 segundos tras la disponibilidad de RabbitMQ.
* **Instrumento:** Prueba de caos con Toxiproxy (o deteniendo el contenedor de RabbitMQ en Docker Compose) mientras un script de verificación revisa la tabla de auditoría de eventos en PostgreSQL contra los mensajes efectivamente entregados en RabbitMQ. La ejecuta el equipo de QA o el responsable de fiabilidad/DevOps.


---

## 4. Eficiencia de Desempeño (Escalabilidad y Comportamiento Temporal)

### Escenario 4: Propagación de notificaciones en tiempo real bajo escalamiento horizontal

* **Fuente:** Clientes móviles en espera de actualización del estado de la cola.
* **Estímulo:** 500 conexiones WebSocket concurrentes solicitan el estado del turno mientras el backend escala a 3 réplicas en paralelo.
* **Artefacto:** Administrador de WebSockets del backend y mecanismo de distribución entre réplicas, si se implementa.
* **Entorno:** Backend distribuido tras un balanceador de carga durante el despacho activo de turnos.
* **Respuesta:** Si se decide implementar escalamiento horizontal, el evento de cambio de estado se distribuye a la réplica que sostiene la conexión del cliente; el mecanismo (por ejemplo, Redis Pub/Sub) debe implementarse y validarse antes de aceptar el escenario.
* **Medida:** Latencia de entrega de la notificación WebSocket a los clientes móviles menor a 500 ms desde el cambio de estado en la base de datos, con una tasa de éxito del 100%.
* **Instrumento:** Script de carga para WebSocket con `k6` o Artillery contra tres réplicas del backend y el mecanismo de distribución implementado, registrando el tiempo entre el cambio en la base de datos y la recepción del evento en el cliente. Lo ejecuta el equipo de QA o el responsable de rendimiento.


---

## 5. Mantenibilidad (Modificabilidad y Seguridad Operativa)

### Escenario 5: Endurecimiento de la configuración de red y gestión de dependencias

* **Fuente:** Auditoría de seguridad o pipeline de Integración Continua (CI/CD).
* **Estímulo:** Ejecución de escáneres estáticos de vulnerabilidades (`pip-audit`, `npm audit`) y pruebas de origen de solicitudes HTTP.
* **Artefacto:** Archivos `requirements.txt`, `package.json` y configuración CORS en `main.py`.
* **Entorno:** Entorno de staging/pre-producción.
* **Respuesta:** El backend restringe la política CORS especificando orígenes permitidos explícitos (eliminando `allow_origins=["*"]`), fija las versiones exactas de las librerías en `requirements.txt` y mantiene las URL del cliente en variables de entorno Expo como `EXPO_PUBLIC_API_URL` y `EXPO_PUBLIC_WS_URL`.
* **Medida:** 0 vulnerabilidades de severidad Alta o Crítica detectadas en dependencias y 100% de la configuración de red gestionada por variables de entorno.
* **Instrumento:** `pip-audit` y `npm audit` corriendo en el pipeline de CI/CD, más una prueba automatizada con `pytest` o una colección de Postman/Newman que comprueba que solo se aceptan los orígenes permitidos y que no queda una URL temporal fija en el código. La ejecución corresponde al responsable de CI/CD o DevSecOps.


---

## Priorización

| # | Escenario | Impacto (qué pasa si no se cumple) | Dificultad (cuánto cuesta lograrlo) | Prioridad |
|---|-----------|-------------------------------------|--------------------------------------|-----------|
| 1 | Asignación atómica de cupos (Adecuación Funcional) | Alto — se rompe la regla de negocio central: se sirven más raciones de las que hay o se duplican turnos. Afecta a todos los estudiantes en la cola, no a uno solo. | Media — ya existe un camino conocido (transacción con `FOR UPDATE`), falta implementarlo bien. | **1** |
| 2 | Prevención de turnos duplicados (Seguridad) | Alto — un estudiante con dos turnos activos le quita el cupo a otro y rompe la misma regla de raciones, solo que por la puerta de atrás. | Baja — es una restricción a nivel de base de datos (índice único parcial), no requiere tocar arquitectura. | **2** |
| 3 | Resiliencia del worker ante caída de RabbitMQ (Fiabilidad) | Alto — un turno cancelado que no se propaga deja a otro estudiante esperando un cupo que ya no existe. | Alta — requiere manejo de reintentos y una tabla de auditoría que hoy no existe. | **3** |
| 4 | Notificaciones en tiempo real bajo escalamiento (Eficiencia) | Medio — si falla, el estudiante ve el estado desactualizado pero puede refrescar o preguntar en el módulo. No rompe la asignación en sí. | Alta — implica coordinar WebSockets entre réplicas vía Redis Pub/Sub, algo que hoy vive solo en memoria local. | **4** |
| 5 | Endurecimiento de CORS y dependencias (Mantenibilidad) | Medio — es un riesgo de seguridad real, pero no tumba el sistema en producción de un día para otro. | Baja — son cambios de configuración puntuales (variables de entorno, pinning de versiones). | **5** |

**Por qué el primero es el primero:** la asignación atómica de cupos es la regla de negocio que le da sentido al sistema — si el comedor sirve más raciones de las que tiene, ComedorUNI deja de cumplir su propósito, sin importar qué tan rápido notifique o qué tan segura sea la configuración. El segundo lugar (prevención de turnos duplicados) casi empata en impacto porque ataca la misma regla de negocio desde otro ángulo, pero se prioriza justo después del primero porque es mucho más barato de resolver: es una restricción en la base de datos, no una reescritura de la lógica de asignación. Los siguientes dos (fiabilidad y eficiencia) importan porque afectan la experiencia del estudiante mientras espera su turno, y el último es una mejora de seguridad operativa importante pero que no rompe el uso diario del sistema si se pospone una semana más.

# Revisión de escenarios de calidad — ComedorUNI

*Equipo que revisa:* Equipo N.° 1

La revisión aplica una sola pregunta a cada escenario: *¿Con qué instrumento concreto se mide esto, y quién lo va a correr?*

## Observación 1 — Adecuación funcional: asignación atómica de cupos

El escenario define correctamente el resultado esperado, pero no identifica el instrumento de medición ni quién ejecutará la prueba. Debe indicarse, por ejemplo, un *script de carga con k6 o Locust* que envíe las 100 solicitudes simultáneas y luego consulte PostgreSQL para verificar que solo se asignó una ración y que no existen turnos duplicados. La prueba debe ejecutarla el *equipo de QA o el responsable de pruebas de rendimiento*.


## Observación 2 — Seguridad: prevención de turnos duplicados

El escenario menciona el índice único parcial, pero no señala la herramienta que comprobará el comportamiento ante solicitudes simultáneas ni quién será responsable de ejecutarla. Debe utilizarse, por ejemplo, una *colección de Postman ejecutada con Newman o un script automatizado con pytest/httpx, usando el mismo `sid` y verificando las respuestas HTTP 409 y el estado final en PostgreSQL. La prueba debe ejecutarla el **equipo de QA o el responsable de pruebas de seguridad*.


## Observación 3 — Fiabilidad: fallos del broker RabbitMQ

El escenario plantea reintentos y persistencia temporal, pero no concreta el instrumento para provocar la caída de RabbitMQ, medir la reconexión y comprobar que no se pierden eventos. Debe indicarse, por ejemplo, un *prueba de caos con Toxiproxy o Docker Compose, junto con un **script de verificación de eventos en PostgreSQL y RabbitMQ. La prueba debe ejecutarla el **equipo de QA o el responsable de fiabilidad/DevOps*.


## Observación 4 — Eficiencia de desempeño: notificaciones WebSocket

El escenario establece 500 conexiones y una latencia menor a 500 ms, pero no especifica con qué herramienta se abrirán las conexiones, se medirá la latencia ni quién realizará la ejecución. Debe utilizarse, por ejemplo, un *script de carga para WebSocket con k6 o Artillery, con tres réplicas del backend y Redis, registrando el tiempo entre el cambio en la base de datos y la recepción del evento. La prueba debe ejecutarla el **equipo de QA o el responsable de rendimiento*.


## Observación 5 — Mantenibilidad y seguridad operativa: dependencias y CORS

El escenario nombra pip-audit y npm audit, pero no indica quién ejecutará los escáneres ni con qué instrumento se verificará la configuración CORS y el uso de variables de entorno. Debe especificarse que el *pipeline de CI/CD* ejecutará pip-audit y npm audit, mientras una *prueba automatizada con pytest o una colección de Postman/Newman* comprobará que solo se aceptan orígenes permitidos y que no existe una URL ngrok fija. La ejecución corresponde al *responsable de CI/CD o DevSecOps*.


## Veredicto de la revisión

Los cinco escenarios describen medidas verificables, pero no todos identifican de forma completa el instrumento y el responsable de ejecución. Por ese motivo, *ningún escenario pasa todavía sin una aclaración explícita* de ambos elementos. La corrección mínima es agregar el instrumento concreto y el equipo o rol responsable dentro de cada escenario.

**Corrección aplicada:** se agregó una línea `Instrumento` a cada uno de los cinco escenarios (arriba), con la herramienta concreta y el rol responsable, tomando lo ya acordado en las Observaciones 1–5 de esta revisión. Los cinco pasan.