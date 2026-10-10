# Bitácora de uso de IA — Semana 02

Registro del uso de IA en el paso 5 del laboratorio ("Corregir y priorizar"), donde se usó como abogada del diablo sobre los cinco escenarios de `docs/escenarios.md`. La regla del curso es escribir los escenarios a mano primero y recién en este paso pasarlos por la IA, así que este documento cubre solo esa parte final.

**Herramienta usada:** Claude (Claude Code).
**Fecha:** 16 de setiembre de 2026.

## Qué se le pidió

Se le pasó cada uno de los cinco escenarios (ya corregidos con las observaciones de la crítica cruzada) y se le pidió, uno por uno, que hiciera la misma pregunta que usó el equipo revisor: **¿con qué instrumento concreto se mide esto, y quién lo va a correr?** También se le pidió construir la tabla de priorización con impacto y dificultad, y ordenar los escenarios con una justificación escrita.

## Qué preguntó / qué encontró

- **Escenario 1 (asignación atómica):** confirmó que el instrumento ya estaba nombrado (script de carga tipo `k6`/`locust` + conteo en PostgreSQL). No pidió cambios.
- **Escenario 2 (prevención de turnos duplicados):** confirmó que el instrumento (consulta SQL de conteo agrupada) era suficiente y verificable sin ambigüedad. No pidió cambios.
- **Escenario 3 (resiliencia RabbitMQ):** señaló que "0% de eventos perdidos" no decía cómo se comprobaba eso ni contra qué se compara. Propuso `toxiproxy` (o simplemente parar el contenedor) más una tabla de auditoría de eventos.
- **Escenario 4 (WebSockets a escala):** confirmó que el instrumento (prueba de carga con timestamps) era suficiente. No pidió cambios.
- **Escenario 5 (CORS y dependencias):** confirmó que `pip-audit` y `npm audit` corriendo en CI eran instrumento suficiente. No pidió cambios.
- **Sobre tener seis escenarios en vez de cinco:** al revisar el set completo, hizo notar que el escenario de Portabilidad (despliegue con Docker Compose) era el de menor impacto real frente a los otros cinco, mientras que Seguridad (turnos duplicados) ataca la misma regla de negocio central que Adecuación Funcional. Se decidió mantener Seguridad y sacar Portabilidad para quedar en los cinco que pide la guía.
- **Priorización:** al pedirle que ordenara los cinco, insistió en separar impacto de dificultad en columnas distintas en vez de mezclar ambos criterios en una sola frase, y en escribir explícitamente por qué el primero es el primero, no solo la tabla.

## Qué se aceptó

- El ajuste de instrumento de medición del Escenario 3 (resiliencia RabbitMQ): se incorporó tal cual a `docs/escenarios.md`, porque era una pregunta real que el equipo tampoco supo responder de inmediato.
- El cambio de Portabilidad por Seguridad para quedar en cinco escenarios, por el argumento de impacto vs. costo de arreglo.
- La estructura de la tabla de priorización (impacto | dificultad | prioridad) y el párrafo de justificación del orden.

## Qué se descartó

- Ninguna sugerencia se descartó por completo; en los escenarios 1, 2, 4 y 5 la IA no encontró nada que corregir y el equipo no le pidió alternativas para algo que ya funcionaba.
- No se le pidió que redactara los escenarios desde cero ni que opinara sobre qué sistema elegir: esa parte, según la regla del laboratorio, se hizo a mano y sin IA.

## Corrección del 19 de setiembre: el instrumento no había quedado en `docs/escenarios.md`

Al verificar el repositorio contra la guía se encontró que el instrumento y el responsable
discutidos en esta sesión (arriba) solo quedaron escritos en las Observaciones de la
revisión cruzada y en esta bitácora, pero nunca se copiaron a los cinco bloques
`Escenario 1`–`Escenario 5` del archivo, que es donde la guía y la rúbrica los buscan. Se
agregó una línea `Instrumento` a cada escenario con el mismo texto ya acordado aquí (no se
inventó nada nuevo), y se marcó el veredicto de la revisión como resuelto.

# Bitácora de uso de IA — Semana 03

Registro del laboratorio "Tu sistema en C4, como código" (paso 2: pasar el dibujo a texto
versionado y agregar contenedores y componentes).

**Herramienta usada:** Claude (Claude Code).
**Fecha:** 19 de setiembre de 2026.

## Qué se le pidió

Traducir el modelo de contexto, contenedores y componentes de ComedorUNI a sintaxis
PlantUML + C4-PlantUML, a partir de `docs/ficha-del-sistema.md` y `docs/escenarios.md`
(no se le pidió inventar el sistema ni elegir qué cajas existen: eso ya estaba decidido en
la ficha aprobada la semana 2). También se le pidió generar los PNG desde la fuente y
escribir `docs/c4/leyenda.md`.

## Qué encontró / qué propuso

- Detectó que `s031-actividad-documentacion-arquitectura/c4.md` (carpeta ya existente en el
  repositorio) describe un sistema distinto al real: menciona Spring Boot, Firebase y
  sistemas duplicados ("copia") que no aparecen en la ficha del sistema ni en el stack real
  (FastAPI + PostgreSQL + Redis + RabbitMQ). No se reutilizó ese contenido.
- Al no tener acceso al repositorio de código (privado), señaló dos cajas del modelo que son
  inferencia del texto y no verificación de código: el "Sistema de Autenticación
  Institucional" como sistema externo, y el "Worker de expiración" como contenedor separado
  de la API. Ambas quedaron documentadas en `docs/c4/leyenda.md` como pendientes de
  confirmar contra el código antes de la revisión cruzada.
- No propuso ninguna caché, cola o balanceador adicional a los que ya existían en la ficha
  del sistema (Redis y RabbitMQ ya estaban documentados como reales desde la semana 2).

## Qué se aceptó

- La estructura de los tres archivos `.puml` y el agrupamiento de seis componentes por
  responsabilidad (Router, Autenticación, Servicio de Turnos, Repositorio, Publicador de
  Eventos, Gestor de WebSockets) dentro del rango de 4 a 8 que pide la guía.
- Vendorizar la librería C4-PlantUML en `docs/c4/lib/` en vez de depender de un `!include`
  a una URL externa, para que el build no dependa de que GitHub esté disponible.

## Qué se corrigió / qué queda pendiente

- Los dos supuestos de la sección anterior (autenticación externa vs. interna; worker
  separado vs. tarea en el mismo proceso) no se pueden cerrar sin leer el código del
  repositorio del proyecto. Se dejaron explícitos en `docs/c4/leyenda.md` en vez de
  resolverlos a adivinanza, para que el paso 4 (revisión cruzada) los confirme o los tumbe.

# Bitácora de uso de IA — Semana 03 (continuación)

Registro de la corrección de los tres `.puml` contra el código real del repositorio
(`s111-actividad-bosquejo-implementacion/backend/src`), ya accesible esta sesión. Se partió
de un resumen previo (`benja.pdf`, transcripción de una sesión de Gemini de un compañero de
equipo) que replanteaba el mismo modelo de contexto sin haber leído el código tampoco.

**Herramienta usada:** Claude (Claude Code).
**Fecha:** 19 de setiembre de 2026.

## Qué se le pidió

Leer el código real del backend y corregir `docs/c4/{contexto,contenedores,componentes}.puml`
y `docs/c4/leyenda.md` contra lo que el código realmente hace, regenerar los PNG y dejar
registro de qué cambió y por qué.

## Qué encontró (grep + lectura directa, no inferencia)

- El supuesto 1 de la semana pasada estaba **mal**: no hay OAuth desde el backend. El login
  es un WebView de la app hacia `alumnos.uni.edu.pe/redirect-google`; la app scrapea el HTML
  y se lo manda al backend por `POST /parse-data`. La caja externa correcta es **Portal
  Alumnos UNI**, y la relación sale de la app móvil (que embebe el WebView), no del backend.
- El supuesto 2 estaba **bien**: `main.py` confirma que el worker de inactividad y los
  consumers M4/M5 corren como `asyncio.create_task()` dentro del mismo proceso FastAPI, no
  como contenedores separados.
- Faltaba por completo el **Expo Push Notification Service** (`shared/push.py`,
  `exp.host`) en los tres niveles, pese a que el código ya lo tenía implementado.
- La autenticación **no usa JWT** (lo que decía el `componentes.puml` anterior) sino sesión
  por `sid` en Redis (`auth/redis_store.py`), más un segundo factor no documentado antes:
  verificación biométrica facial con DeepFace/Facenet.
- Existe un módulo `menu` (alta/edición del menú del día) que no aparece en la lista de
  módulos de `3.1.0` ni en los actores de `1.2` — se dejó como pendiente para que el equipo
  decida si se documenta como parte de M7 o aparte.

## Qué se aceptó

- Renombrar el sistema externo de autenticación a "Portal Alumnos UNI" y mover la relación de
  login a la app móvil (no al backend), agregar "Expo Push Notification Service" en los tres
  niveles, fusionar el worker en el contenedor del backend y corregir "JWT" → "sesión por sid
  (Redis)" en el componente de autenticación.
- Expandir de seis a siete componentes para reflejar Notificaciones (M4) y Seguimiento (M5)
  como consumers reales de RabbitMQ, en vez de un solo "Publicador de Eventos" genérico.

## Qué se corrigió / qué queda pendiente

- El módulo `menu` sigue sin encajar en la documentación de requisitos (`1.2`, `3.1.0`); no se
  tocó esa parte porque no fue pedida en este paso y corregirla implica decidir si es un
  módulo nuevo o parte de Configuración — decisión del equipo, no de la IA.
- Pendiente correr el paso 4 (revisión cruzada) sobre esta versión corregida.

# Bitácora de uso de IA — Semana 03 (workspace.dsl)

La guía pide `docs/c4/workspace.dsl` como entregable con ese nombre exacto aunque el equipo
trabaje con PlantUML (la rúbrica acepta los `.puml` como equivalentes, pero faltaba el
archivo que la guía nombra explícitamente).

**Herramienta usada:** Claude (Claude Code).
**Fecha:** 19 de setiembre de 2026.

## Qué se le pidió

Traducir el modelo ya verificado contra el código (los tres `.puml` + `leyenda.md`) a
Structurizr DSL, sin cambiar ninguna caja, flecha o descripción — una traducción de
sintaxis, no un rediseño.

## Qué se aceptó

- La traducción completa: mismas personas, mismos dos sistemas externos, mismos cinco
  contenedores y los mismos siete componentes del Backend, con las mismas relaciones y
  protocolos ya validados contra `s111-actividad-bosquejo-implementacion/backend/src`.

## Qué se corrigió / cómo se verificó

- No se confió en que el DSL "se veía bien": se validó exportándolo con `structurizr-cli`
  (`export -format plantuml`, sin necesidad de Docker) y renderizando el resultado. Las tres
  vistas (Contexto, Contenedores, Componentes) compilaron sin errores y muestran las mismas
  cajas y relaciones que los `.puml` ya usados para las imágenes subidas.
- Las imágenes que se suben siguen siendo las generadas desde PlantUML (`img/*.png`);
  `workspace.dsl` queda como fuente adicional documentada en `docs/c4/README.md`, no como
  origen de las imágenes — evita mantener dos generadores de PNG en paralelo.

