# Prompts para Figma Make — exposición técnica ComedorUNI

## Cómo usar estos prompts

1. Ejecuta cada prompt en un proyecto separado o en páginas separadas del mismo
   archivo de Figma.
2. El prototipo es una **representación visual para la exposición**, no una app
   conectada al backend. Usa datos ficticios y no copies credenciales, fotos,
   códigos ni datos reales de estudiantes.
3. Mantén visibles los nombres de estado y endpoints que existen en el código. No
   inventes que una pantalla o un mecanismo futuro ya está implementado.
4. El prototipo debe caber en una presentación técnica de 40 minutos: usa los
   flujos para explicar qué código se ejecuta, no para reemplazar el recorrido del
   código.

## Prompt 1 — Flujo móvil completo del estudiante

```text
Diseña en Figma Make un prototipo móvil interactivo, en español, para ComedorUNI,
un sistema universitario de turnos virtuales. Es una maqueta para exponer un flujo
de código existente; NO lo conectes a una API y NO afirmes que el prototipo visual
es funcional contra backend. Usa exclusivamente datos ficticios.

Estilo: aplicación universitaria sobria y accesible; fondo claro, granate/burdeos
como color institucional, tipografía legible, estados diferenciados también por
texto/icono (no solo color), botones táctiles grandes y jerarquía visual clara.
Diseña para teléfono Android/iPhone, una pantalla por frame, con navegación
prototipada y componentes reutilizables.

Construye este recorrido con enlaces entre pantallas:
1. Inicio/autenticación: botón “Iniciar sesión con Portal UNI”; representa el
   acceso institucional en un WebView, sin imitar ni pedir credenciales reales.
2. Sincronización: estado “Datos académicos sincronizados” y acción para continuar.
3. Verificación de identidad: pantalla de cámara, explicación de consentimiento y
   vista de resultado ficticio (verificado/no verificado); no guardes ni solicites
   imágenes reales.
4. Inicio: saludo ficticio, créditos ficticios, menú del día (desayuno/almuerzo/cena),
   aviso del servicio activo y acción “Solicitar turno”.
5. Ticket en ESPERANDO: número ficticio, posición, servicio, turno actual, indicador
   WebSocket conectado y acción “Salir de la cola”.
6. Notificación LLAMADO: modal “¿Sigues en la cola?” y cuenta regresiva visual de
   tres minutos; botones “Confirmar presencia” y “Salir”.
7. Ticket ATENDIDO: mostrar número de grupo/turno asignado y confirmación de acudir
   al comedor.
8. Alternativa CANCELADO: mostrar motivo y acción para volver al inicio/solicitar
   otro turno.

Añade estados de carga, error de conexión, sesión expirada y capacidad agotada.
La navegación debe permitir presentar el camino feliz y una rama de cancelación.
Incluye en el prototipo una etiqueta discreta “Mockup de exposición — datos
simulados; no conectado al backend”.

No inventes una pantalla de administración: el frontend inspeccionado es cliente
estudiante. No agregues pagos, pedidos, inventario, QR, JWT ni escalamiento
horizontal. Mantén la secuencia consistente con los endpoints actuales:
/parse-data, /verify-biometric, /queue/active-service, /queue/join, /queue/status,
/queue/confirm y /queue/leave.
```

## Prompt 2 — Estados de cola y actualización en tiempo real

```text
En el mismo lenguaje visual de ComedorUNI, crea un prototipo interactivo centrado
en una pantalla de ticket que muestre claramente la máquina de estados del turno:
ESPERANDO → LLAMADO → ATENDIDO, con CANCELADO como salida alternativa.

Usa datos completamente ficticios. En ESPERANDO presenta posición y conexión
WebSocket; en LLAMADO, modal de confirmación de presencia con plazo de 3 minutos;
en ATENDIDO, turno/grupo asignado; en CANCELADO, explicación y retorno al inicio.
Permite avanzar entre estados con controles etiquetados “Simular evento WebSocket”
para que quede claro que el cambio es una simulación del prototipo, no un evento
emitido por el backend.

Incluye una vista de anotación para cada transición con: evento visual mostrado,
acción del estudiante y punto de código que se explicará:
- frontend/src/app/ticket.tsx: handleWsMessage y handleConfirm
- backend/src/modules/queues/router.py: /queue/ws/{sid} y /queue/confirm
- backend/src/modules/queues/worker.py: expiración y llamado

No dibujes coordinación entre réplicas, Redis Pub/Sub ni entrega garantizada: los
WebSockets y worker actuales viven en el proceso del backend. No prometas que las
transiciones están cubiertas por pruebas automatizadas.
```

## Prompt 3 — Diagrama visual del flujo de negocio para una diapositiva

```text
Genera una sola lámina horizontal 16:9 titulada “De la identidad al turno
atendido — flujo de ComedorUNI”. Es un diagrama de secuencia para exposición de
software, no una interfaz de producto.

Usa cinco carriles: Estudiante/App Expo, Portal Alumnos UNI, API FastAPI, PostgreSQL
y Redis/RabbitMQ + servicios consumidores. Muestra, de izquierda a derecha:
1. login Portal en WebView y lectura HTML;
2. POST /parse-data, parseo/upsert estudiante y sesión sid en Redis;
3. POST /verify-biometric y comparación contra foto de referencia de sesión;
4. GET /queue/active-service, POST /queue/join y validaciones antes de crear turno;
5. insert de turno en PostgreSQL, respuesta con número/posición;
6. WebSocket de cola, evento LLAMADO, confirmación HTTP/WebSocket;
7. transición a ATENDIDO, publicación RabbitMQ y consumer M4/M5 cuando aplique.

Distingue con línea continua los pasos implementados observados y con borde
discontinuo/nota las garantías pendientes. Agrega dos advertencias legibles:
“La comprobación de capacidad ocurre antes de la transacción de creación: riesgo de
carrera” y “El publish actual registra el error, pero no lo devuelve al llamador”.
No muestres JWT, microservicios, outbox, Pub/Sub, resiliencia garantizada ni
pruebas concurrentes aprobadas: no son capacidades demostradas por el código actual.
Usa nombres de endpoints/componentes reales y evita datos personales.
```

## Prompt 4 — Lámina breve de deuda técnica/evidencia

```text
Crea una diapositiva 16:9 para una defensa universitaria titulada “Qué funciona,
qué sabemos y qué falta demostrar”. Organiza tres columnas:

FUNCIONA / OBSERVADO:
- backend FastAPI inicia con Compose;
- GET /ping devolvió HTTP 200;
- frontend TypeScript compila y Expo exporta web;
- existen flujos de login, cola y ticket en el código.

RIESGOS EN EL CÓDIGO:
- capacidad y creación de turno no comparten una sola transacción;
- secuencia COUNT excluye estados terminales y puede chocar con unicidad histórica;
- publish RabbitMQ captura el error y no lo propaga;
- worker se ejecuta localmente y maneja excepción amplia con print.

PENDIENTE:
- pruebas automatizadas de contratos, concurrencia y fallos;
- inventario transitivo/licencias y versiones backend reproducibles;
- revisión de alertas npm reportadas en el corte;
- evidencia de flujo completo real en entorno integrado.

Pie obligatorio: “El smoke test prueba arranque/conectividad, no corrección bajo
carga. No declarar v1.0 aprobada sin pruebas reproducibles.” Usa diseño claro,
sin iconos de escudos/medallas que sugieran seguridad o aprobación no demostradas.
```
