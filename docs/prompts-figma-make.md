# Prompts Maestros para Figma Make — Sistema ComedorUNI

Este documento contiene los **prompts de ingeniería de interfaz y diseño de interacción** listos para ser utilizados directamente en **Figma Make**, **Figma AI**, **v0.dev**, o herramientas equivalentes de prototipado generativo. Permite generar el prototipo móvil completo, la máquina de estados reactiva y las láminas técnicas de arquitectura para la sustentación del Examen Parcial de **Construcción de Software II (SW707)**.

---

## 🎨 Sistema de Diseño y Tokens Globales (Design Tokens)

Antes de generar las pantallas individuales, proporcione a Figma Make las siguientes directrices de estilo para mantener coherencia visual institucional:

### 1. Paleta de Colores Institucional y Semántica

```json
{
  "colors": {
    "primary": {
      "default": "#8A1538",      /* Granate institucional UNI */
      "dark": "#5C0E26",         /* Granate oscuro para encabezados y hover */
      "light": "#FDF2F4",        /* Fondo sutil granate para alertas y badges */
      "accent": "#C92A54"        /* Granate vibrante para llamadas a la acción */
    },
    "surface": {
      "canvas": "#F8FAFC",       /* Fondo general gris cálido neutro */
      "card": "#FFFFFF",         /* Superficie de tarjetas y modales */
      "card_hover": "#F1F5F9",   /* Estado hover/táctil de elementos */
      "ticket_bg": "#FFFFFF",    /* Fondo del ticket virtual */
      "backdrop": "rgba(15, 23, 42, 0.65)" /* Desenfoque de modales (Backdrop Blur 8px) */
    },
    "text": {
      "primary": "#0F172A",      /* Slate oscuro de alto contraste */
      "secondary": "#64748B",    /* Slate neutro para subtítulos y metadatos */
      "muted": "#94A3B8",        /* Gris suave para placeholders e inactivos */
      "on_primary": "#FFFFFF"    /* Texto blanco sobre fondo granate */
    },
    "states": {
      "esperando": {
        "text": "#0369A1", "badge_bg": "#E0F2FE", "border": "#BAE6FD", "glow": "#38BDF8"
      },
      "llamado": {
        "text": "#B45309", "badge_bg": "#FEF3C7", "border": "#FDE68A", "glow": "#F59E0B"
      },
      "atendido": {
        "text": "#047857", "badge_bg": "#D1FAE5", "border": "#A7F3D0", "glow": "#10B981"
      },
      "cancelado": {
        "text": "#BE123C", "badge_bg": "#FFE4E6", "border": "#FECDD3", "glow": "#F43F5E"
      }
    },
    "borders": {
      "subtle": "#E2E8F0",
      "divider": "#CBD5E1"
    }
  }
}
```

### 2. Tipografía y Escala Jerárquica (Inter / Roboto)
- **Display (Número de Turno en Ticket):** 44px, Bold, tabular nums (ej. `#142`).
- **H1 (Títulos de Pantalla):** 22px, Bold, tracking -0.02em.
- **H2 (Encabezados de Sección y Modal):** 18px, Semi-Bold.
- **Body 1 (Lectura Principal):** 15px, Regular, interlineado 1.5.
- **Body 2 (Detalles y Menú):** 13px, Medium.
- **Caption / Metadata:** 11px, Semi-Bold, uppercase (ej. badges de estado).

### 3. Elevación, Bordes y Perforaciones de Ticket
- **Radio de Tarjetas:** `20px` esquinas redondeadas.
- **Radio de Botones e Inputs:** `12px`.
- **Radio de Badges:** `9999px` (Pill completo).
- **Sombra Suave (Card Elevation):** `box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.06), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`.
- **Efecto Ticket Perforado:** Muescas semicirculares de 16px en ambos laterales con línea punteada horizontal divisoria (`border-style: dashed`).

---

## 📱 Prompt Maestro 1: Flujo Móvil Completo de Extremo a Extremo (Mobile 390 × 844 px)

Copie y pegue este prompt en Figma Make para construir el flujo navegable completo de la aplicación estudiantil:

```text
Actúa como un diseñador UI/UX líder especializado en aplicaciones móviles universitarias de alta fidelidad. Diseña en Figma Make un prototipo móvil interactivo de 9 pantallas (frame iPhone 15 / Android, 390x844px) para "ComedorUNI", el sistema oficial de gestión de turnos virtuales del Comedor Universitario de la UNI.

El estilo visual debe ser moderno, sobrio, accesible y altamente profesional:
- Paleta: Granate institucional UNI (#8A1538), fondo canvas gris cálido (#F8FAFC), tarjetas blancas con sombras suaves (#FFFFFF) y acentos semánticos según estado.
- Tipografía: Inter o Roboto. Jerarquía tipográfica estricta, botones táctiles grandes (mínimo 48px de altura) y micro-badges informativos.
- Todas las pantallas deben lucir datos ficticios de demostración académica (estudiante simulado "Franz Inga", código "20210001A"). No uses datos reales.

Genera las siguientes 9 pantallas conectadas en un flujo coherente:

PANTALLA 1: Login Institucional (Ruta: /login)
- Header superior con imagotipo estilizado de ComedorUNI y escudo institucional de la Universidad Nacional de Ingeniería.
- Ilustración vectorial limpia de comensales universitarios organizados.
- Título: "Bienvenido al Comedor UNI". Subtítulo: "Gestiona tu turno diario de forma virtual sin filas físicas a la intemperie".
- Botón principal de acceso de ancho completo (Fondo Granate #8A1538, texto blanco): "Iniciar sesión con Portal Alumnos".
- Vista previa modal deslizante (bottom sheet) que representa el WebView hacia alumnos.uni.edu.pe con candado HTTPS y barra de navegación institucional simulada.
- Pie de página: "Dirección de Bienestar Universitario — FIIS UNI".

PANTALLA 2: Sincronización de Identidad y Créditos (Ruta: /sync)
- Estado de carga y confirmación de datos extraídos del scraping del portal estudiantil.
- Tarjeta de identidad del estudiante con foto de carné simulada, código "20210001A", nombres "Franz Joe Inga Champi", carrera "Ingeniería de Software".
- Indicadores en píldoras: "Matrícula Regular 2026-II" (Verde), "22 Créditos" (Azul).
- Indicador de seguridad: "Sesión activa (Token sid con TTL de 8 horas en Redis)".
- Botón primario: "Continuar a Verificación Biométrica".

PANTALLA 3: Verificación Facial 1:1 (Ruta: /verify-biometric)
- Encabezado: "Validación Biométrica Facial". Subtítulo: "Comprobación de identidad para prevenir suplantación en el acceso".
- Viewfinder central de cámara con guía oval punteada en verde esmeralda.
- Indicador de estado: "Rostro detectado — Alineando con foto oficial de ORCE".
- Tarjeta de telemetría de inferencia: "Algoritmo DeepFace / Facenet | Similitud: 98.4% | Verificación Exitosa".
- Botón primario: "Ingresar al Sistema".

PANTALLA 4: Dashboard Principal / Home (Ruta: /home)
- Barra superior con saludo: "¡Hola, Franz!", foto de perfil miniatura y botón de cerrar sesión.
- Banner del Servicio Activo (Granate con degradado): "Almuerzo de Hoy" | Horario: "11:30 - 13:30".
- Tarjeta de Aforo en tiempo real: Barra de progreso indicando "320 / 500 raciones disponibles" (64% disponible).
- Sección colapsable "Menú Nutricional del Día":
  * Entrada: Sopa de fideos con verduras.
  * Segundo: Arroz chaufa de cerdo con plátano frito.
  * Bebida: Refresco de chicha morada natural.
  * Postre: Fruta fresca (mandarina).
  * Ficha de nutrientes: 1,332 kcal | 43g Proteínas | 171g Carbohidratos | 51g Lípidos.
- Botón flotante prominente (CTA): "Solicitar Turno para Almuerzo".

PANTALLA 5: Ticket Virtual en Cola (Ruta: /ticket — Estado ESPERANDO)
- Tarjeta de Ticket estilo "Boarding Pass" con muescas circulares laterales y línea divisoria troquelada:
  * Encabezado: "TICKET VIRTUAL · ALMUERZO".
  * Número de Turno gigante centrado: "#142" en 48px bold.
  * Fila con 3 métricas clave:
    1. "Tu posición en cola": #18 estudiantes adelante.
    2. "Atención actual": Turno #124 en mostrador.
    3. "Tiempo estimado": ~12 minutos.
  * Indicador en vivo: Punto verde pulsante con texto "WebSocket conectado en tiempo real (/ws/20210001A)".
- Botón secundario outline abajo: "Abandonar cola".

PANTALLA 6: Notificación de Llamado en Tiempo Real (Ruta: /ticket — Estado LLAMADO)
- Notificación push emergente en la parte superior: "Comedor UNI: ¡Es tu turno! Confirma tu asistencia en 3 minutos".
- Modal centrado con fondo desenfocado (Backdrop Blur):
  * Icono animado de campana/alerta vibrante en ámbar (#F59E0B).
  * Título urgente: "¡Turno #142 Llamado!".
  * Temporizador radial circular con cuenta regresiva regresando desde "02:59" minutos.
  * Texto explicativo: "Acércate inmediatamente a la puerta de ingreso del comedor y pulsa el botón para confirmar tu presencia física."
  * Botón de acción principal (Verde Esmeralda #059669): "¡Confirmar Presencia Ahora!".
  * Botón secundario texto: "No podré llegar (Liberar ración)".

PANTALLA 7: Ticket Confirmado y Asignado (Ruta: /ticket — Estado ATENDIDO)
- Pantalla festiva y limpia con fondo de cabecera verde esmeralda suave.
- Icono de check gigante animado.
- Título: "¡Asistencia Confirmada!". Subtítulo: "Tu ración está reservada y lista para entrega".
- Tarjeta de Acceso:
  * Turno: "#142".
  * Asignación de Grupo: "GRUPO 2 — MESA B".
  * Puerta de ingreso: "Puerta Principal (Acceso Rápido)".
  * Timestamp: "Confirmado a las 12:45:12".
- Mensaje: "Muestra esta pantalla al personal de control en el mostrador."

PANTALLA 8: Turno Cancelado / Expirado (Ruta: /ticket — Estado CANCELADO)
- Estado alternativo de salida.
- Icono de reloj con alerta en carmesí suave (#E11D48).
- Título: "Turno Expirado por Inactividad".
- Explicación: "No se registró confirmación en el plazo de 3 minutos. Tu ración fue reasignada automáticamente al siguiente estudiante en espera para evitar desperdicio de comida."
- Botón primario outline: "Volver a Inicio / Solicitar Otro Servicio".

PANTALLA 9: Estados de Contingencia y Barricadas de Error (Modales de Apoyo)
- Modal A: "Aforo Agotado" (HTTP 400) — "Se han agotado las 500 raciones configuradas para el almuerzo. Intenta en el turno de cena."
- Modal B: "Conflicto de Turno" (HTTP 409) — "Ya posees un turno activo (#142). No es posible solicitar dos turnos para el mismo servicio diario."
- Toast inferior: "Reconectando WebSocket con el servidor..." (con spinner ámbar).
```

---

## ⚡ Prompt Maestro 2: Prototipado Interactivo y Máquina de Estados (Micro-interactions)

Utilice este prompt para configurar las conexiones interactivas automáticas en Figma:

```text
En el archivo de prototipo móvil de ComedorUNI generado previamente, configura las conexiones de interacción (Interactions / Prototype) para simular el comportamiento reactivo de la máquina de estados del backend:

1. Transición de Login a Sincronización:
   - Trigger: On Click en botón "Iniciar sesión con Portal Alumnos".
   - Acción: Open Overlay del WebView modal con animación "Slide in from bottom" (300ms, ease-out).
   - Desde el WebView: After Delay de 2000ms -> Navigate to Screen 2 (/sync) con Smart Animate (250ms).

2. Transición de Sincronización a Biometría:
   - Trigger: On Click en "Continuar a Verificación Biométrica".
   - Acción: Navigate to Screen 3 (/verify-biometric) con "Push" horizontal.

3. Transición de Biometría a Home:
   - Trigger: On Click en "Ingresar al Sistema".
   - Acción: Navigate to Screen 4 (/home) con Smart Animate.

4. Transición de Home a Solicitud de Turno (Encolamiento):
   - Trigger: On Click en CTA "Solicitar Turno para Almuerzo".
   - Acción: Navigate to Screen 5 (/ticket - ESPERANDO) con animación "Slide in from right".

5. Simulación de Evento WebSocket (Paso de ESPERANDO a LLAMADO):
   - Trigger: After Delay de 4000ms en la Screen 5 (simulando que el worker de fondo llamó al turno).
   - Acción: Open Overlay de la Screen 6 (Modal de Llamado con Timer circular de 3 min) con animación "Fade in" + escala elástica (350ms, ease-out).

6. Bifurcación A (Camino Feliz — Confirmación de Asistencia):
   - Trigger: On Click en botón verde "¡Confirmar Presencia Ahora!".
   - Acción: Close Overlay y Navigate to Screen 7 (/ticket - ATENDIDO) con Smart Animate.

7. Bifurcación B (Camino Alternativo — Expiración o Cancelación):
   - Trigger: On Click en botón "No podré llegar" o After Delay de 6000ms en el modal de timer.
   - Acción: Close Overlay y Navigate to Screen 8 (/ticket - CANCELADO) con animación "Dissolve".
   - Desde Screen 8: On Click en "Volver a Inicio" -> Navigate to Screen 4 (/home).

Añade anotaciones visuales flotantes tipo sticker para la defensa técnica indicando qué archivo del código fuente respalda cada interacción:
- Transición 1 y 2: auth/service.py y auth/redis_store.py
- Transición 3: auth/biometric.py (DeepFace)
- Transición 4: queues/router.py (/queue/join) y queues/service.py (SELECT FOR UPDATE)
- Transición 5: queues/worker.py (inactivity_worker) y shared/rabbitmq.py (evento turno.llamado)
- Transición 6: queues/service.py (confirmar_turno) y tracking/consumer.py (M5)
```

---

## 🏛️ Prompt Maestro 3: Lámina de Arquitectura y Secuencia de Extremo a Extremo (16:9 Desktop — 1920 × 1080 px)

Copie este prompt para generar la diapositiva técnica de sustentación arquitectónica:

```text
Diseña en Figma Make una lámina de presentación técnica horizontal 16:9 (1920x1080px) titulada: "ComedorUNI: Flujo Transaccional de Extremo a Extremo — De la Identidad a la Ración Atendida".

La lámina debe tener un aspecto de diagrama de ingeniería de software de alto impacto (estilo Stripe / AWS Architecture Diagram), con fondo oscuro tipo Slate (#0F172A), tarjetas semitransparentes con bordes iluminados (Glassmorphism sutil) y líneas de conexión vectoriales con flechas de dirección.

Organiza la lámina en 5 columnas o carriles verticales de izquierda a derecha:
1. Carril 1: Cliente Móvil (App React Native + Expo Router + WebView)
2. Carril 2: Fuente Externa (Portal Alumnos UNI: alumnos.uni.edu.pe)
3. Carril 3: Backend FastAPI (API Gateway HTTP, WebSockets, Worker Async)
4. Carril 4: Persistencia y Cache (PostgreSQL 15 Fuente de Verdad + Redis 7 Sesiones)
5. Carril 5: Mensajería Asíncrona (RabbitMQ Topic Exchange 'comedor' + Consumers M4 y M5)

Dibuja y enumera paso a paso las 7 etapas del flujo con cajas interconectadas:
- Paso 1: Autenticación en WebView institucional y extracción de HTML DOM.
- Paso 2: POST /parse-data -> Parseo, Upsert en tabla 'estudiantes' y generación de sid en Redis con TTL de 24h.
- Paso 3: POST /verify-biometric -> Comparación facial 1:1 con DeepFace contra foto de sesión.
- Paso 4: POST /queue/join -> Barricada Pydantic, verificación de horario y cerrojo SELECT ... FOR UPDATE en PostgreSQL.
- Paso 5: Canal WebSocket bidireccional permanente (/ws/codigo) emitiendo telemetría de cola en tiempo real.
- Paso 6: Worker de inactividad ejecutándose cada 60s -> Detección de timeout (3 min), llamado de grupos y publicación AMQP.
- Paso 7: Consumo asíncrono desacoplado:
  * M4 Consumer despacha Push Notification vía Expo Push Service (exp.host).
  * M5 Consumer persiste registro de asistencia en historial_asistencia con clave UNIQUE (estudiante_id, turno_dia_id) garantizando idempotencia.

Incluye dos cajas de llamada (Callout Badges) destacando las fortalezas de construcción:
- Callout 1 (Verde Esmeralda): "Garantía de Aforo: La reserva atómica bajo cerrojo FOR UPDATE impide sobreventas aún con N solicitudes concurrentes para la última ración."
- Callout 2 (Azul Cyan): "Desacoplamiento Resiliente: Si el broker o el servicio push experimentan latencia, la transacción de turno en PostgreSQL ya quedó confirmada y segura."
```

---

## 🔬 Prompt Maestro 4: Lámina Comparativa de Concurrencia y Condiciones de Carrera (16:9)

Copie este prompt para generar la diapositiva específica para defender el criterio de **Concurrencia (15%)**:

```text
Diseña en Figma Make una infografía técnica comparativa 16:9 (1920x1080px) titulada: "Análisis y Demostración de Concurrencia: Condición de Carrera en Aforo vs. Bloqueo Transaccional Atómico".

Divide la lámina en dos secciones contrastadas: LADO IZQUIERDO (Falla / Interleaving Vulnerable) vs. LADO DERECHO (Solución / Atomicidad con Mutex FOR UPDATE).

ESCENARIO COMÚN: Queda exactamente 1 ración disponible (Capacidad: 500, Asignadas: 499). Dos alumnos (A y B) solicitan turno en el mismo milisegundo (T=0).

LADO IZQUIERDO: "Sin Sincronización (Condición de Carrera y Sobreventa)"
- Fondo sutilmente teñido de rojo oscuro (#450A0A) con acentos de advertencia (#EF4444).
- Diagrama de secuencia temporal:
  * T1: Petición Alumno A lee vacantes: 500 - 499 = 1 vacante (Válido).
  * T2: Petición Alumno B lee vacantes antes del commit: 500 - 499 = 1 vacante (Válido).
  * T3: Alumno A ejecuta INSERT y confirma Turno #500.
  * T4: Alumno B ejecuta INSERT y confirma Turno #501.
- Resultado en rojo: "¡FALLA DE RUNTIME! 501 raciones asignadas. Sobreventa (Overbooking) y corrupción de la regla de aforo máximo."

LADO DERECHO: "Con Cerrojo SELECT ... FOR UPDATE (Transacción Atómica)"
- Fondo sutilmente teñido de verde oscuro (#064E3B) con acentos esmeralda (#10B981).
- Diagrama de secuencia temporal:
  * T1: Petición Alumno A abre transacción y ejecuta: SELECT id FROM turno_dia FOR UPDATE.
  * T2: Cerrojo exclusivo adquirido. Petición Alumno B llega y queda en cola (bloqueada esperando liberación del cerrojo).
  * T3: Alumno A verifica vacantes (1), inserta Turno #500 y hace COMMIT (Cerrojo liberado).
  * T4: Alumno B se desbloquea, entra a la sección crítica y lee el aforo actualizado: 500 - 500 = 0 vacantes restantes.
  * T5: Petición Alumno B es rechazada elegantemente con HTTP 400 ("Se agotaron las raciones").
- Resultado en verde: "¡INVARIANTE PRESERVADA! Exactamente 500 raciones asignadas. Cero sobreventas y respuesta de error controlada."

Pie de página: "Verificado y reproducido en test automatizado: backend/tests/test_concurrency.py (Aprobado en 0.05s)".
```

---

## 🚀 Instrucciones de Exportación y Uso en la Exposición

1. Abra [Figma](https://www.figma.com/) o [Figma Make](https://www.figma.com/make).
2. Cree un nuevo archivo y pegue el **Prompt Maestro 1** para generar las pantallas de la aplicación móvil.
3. Utilice el **Prompt Maestro 2** para generar el enlace interactivo y simular el flujo en vivo durante los 40 minutos de la exposición.
4. Genere las láminas técnicas de los **Prompts 3 y 4** e insértelas en la presentación de diapositivas para defender la arquitectura y la concurrencia ante las preguntas del docente.
