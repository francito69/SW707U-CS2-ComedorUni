workspace "ComedorUNI" "Gestión de turnos del comedor universitario mediante colas virtuales" {

    model {
        estudiante = person "Estudiante" "Solicita turno para el comedor y hace seguimiento de su cola"
        administrador = person "Administrador del comedor" "Configura bloques horarios, raciones y menú; supervisa la cola"

        portalAlumnos = softwareSystem "Portal Alumnos UNI" "alumnos.uni.edu.pe — login institucional y fuente de identidad: datos personales, cursos y foto vigente del estudiante" "Externo"
        expoPush = softwareSystem "Expo Push Notification Service" "exp.host — entrega push notifications a los celulares de los estudiantes" "Externo"

        comedoruni = softwareSystem "ComedorUNI" "Gestión de turnos del comedor universitario mediante colas virtuales" {
            app_movil = container "Aplicación móvil" "Solicita turnos, confirma o cancela, verifica identidad por rostro y muestra el estado de la cola en tiempo real. Incluye un WebView embebido que navega Portal Alumnos UNI y extrae (scrapea) el HTML de login, cursos y datos personales" "TypeScript, React Native, Expo Router"

            backend = container "Backend (API + Workers)" "Expone los casos de uso de sesión, verificación biométrica, colas, turnos, menú y configuración. El worker de expiración y los consumers de notificaciones/seguimiento corren como tareas asíncronas dentro de este mismo proceso, no como servicios aparte" "Python, FastAPI, Uvicorn" {
                auth_comp = component "Autenticación y Sesión" "Recibe el HTML scrapeado del Portal Alumnos, lo parsea, valida identidad por rostro (DeepFace/Facenet) y administra la sesión por sid en Redis (no JWT)" "auth/router.py, service.py, redis_store.py, biometric.py"
                turnos_comp = component "Router y Servicio de Turnos" "Encolar, confirmar, cancelar y consultar turnos (reglas FIFO, unicidad, raciones); gestiona las conexiones WebSocket en tiempo real" "queues/router.py, service.py, manager.py"
                config_comp = component "Router de Configuración y Menú" "Endpoints de administrador: horarios y raciones por tipo de turno, alta/edición del menú del día" "config/router.py, menu/router.py, service.py"
                worker_comp = component "Worker de Inactividad" "Tarea de fondo (asyncio, cada 60s) dentro del mismo proceso: avisa a los que no responden, cancela turnos LLAMADO sin confirmar en 3 min y dispara el auto-llamado del siguiente grupo" "queues/worker.py"
                reasignacion_comp = component "Reasignación" "Calcula y llama al siguiente grupo de turnos en espera (FIFO por lotes) cuando se libera un cupo" "reassignment/service.py"
                notificaciones_comp = component "Notificaciones (M4)" "Consume turno.llamado y turno.cancelado desde RabbitMQ y envía la push al estudiante" "notifications/consumer.py, shared/push.py"
                seguimiento_comp = component "Seguimiento (M5)" "Consume turno.encolado y turno.atendido desde RabbitMQ y registra el historial/auditoría en PostgreSQL" "tracking/consumer.py, service.py"
            }

            base_datos = container "Base de datos" "Estudiantes, turnos, bloques horarios, raciones y menú" "PostgreSQL 15" "Base de datos"
            cache_sesiones = container "Caché y sesiones" "Almacena sesiones temporales por sid (no JWT). No coordina WebSockets entre réplicas en la implementación actual" "Redis 7" "Base de datos"
            bus_eventos = container "Bus de eventos" "Transporta eventos de encolado, atención, llamado y cancelación de forma asíncrona" "RabbitMQ 3"
        }

        # Nivel 1 — contexto
        estudiante -> comedoruni "Solicita turno, confirma o cancela, consulta el estado de su cola" "HTTPS / WebSocket"
        administrador -> comedoruni "Configura bloques, raciones y menú; supervisa la cola del servicio" "HTTPS"
        comedoruni -> portalAlumnos "El estudiante inicia sesión en un WebView embebido; la app extrae identidad, cursos y foto" "WebView / HTTPS"
        comedoruni -> expoPush "Envía eventos de turno (llamado / cancelado)" "API REST / HTTPS"
        expoPush -> estudiante "Entrega la notificación push" "Push"

        # Nivel 2 — contenedores
        estudiante -> app_movil "Usa" "App móvil"
        administrador -> app_movil "Usa" "App móvil"
        app_movil -> backend "Solicita turno, confirma, cancela, consulta estado, envía HTML scrapeado y foto para verificación biométrica" "JSON / HTTPS + WebSocket"
        app_movil -> portalAlumnos "Login del estudiante y lectura de su portal académico" "WebView / HTTPS"
        backend -> base_datos "Lee y escribe turnos, bloques, raciones y menú" "SQL"
        backend -> cache_sesiones "Guarda y lee la sesión por sid" "Redis"
        backend -> bus_eventos "Publica y consume eventos de turno" "AMQP"
        backend -> expoPush "Envía la notificación push cuando procesa un evento de turno" "API REST / HTTPS"

        # Nivel 3 — componentes del Backend
        app_movil -> auth_comp "Envía HTML scrapeado del portal y foto para verificación biométrica" "JSON / HTTPS"
        app_movil -> turnos_comp "Solicita, confirma, cancela y consulta turnos" "JSON / HTTPS + WebSocket"
        app_movil -> config_comp "Consulta el menú del día" "JSON / HTTPS"

        auth_comp -> cache_sesiones "Crea y valida la sesión por sid" "Redis"
        auth_comp -> base_datos "Registra al estudiante (upsert)" "SQL"

        turnos_comp -> base_datos "Lee y escribe turnos, cola y raciones" "SQL"
        turnos_comp -> cache_sesiones "Valida sid de cada petición" "Redis"
        turnos_comp -> bus_eventos "Publica turno.encolado / turno.atendido / turno.llamado" "AMQP"
        turnos_comp -> reasignacion_comp "Invoca tras confirmar asistencia" "función interna"

        config_comp -> base_datos "Lee y escribe horarios, raciones y menú" "SQL"

        worker_comp -> base_datos "Lee turnos LLAMADO/ESPERANDO y cancela por inactividad" "SQL"
        worker_comp -> bus_eventos "Publica turno.cancelado / turno.llamado" "AMQP"
        worker_comp -> reasignacion_comp "Invoca cada ciclo (60s) para auto-llamar al siguiente grupo" "función interna"

        reasignacion_comp -> base_datos "Actualiza turnos ESPERANDO → LLAMADO por lote" "SQL"

        bus_eventos -> notificaciones_comp "Entrega turno.llamado / turno.cancelado" "AMQP"
        notificaciones_comp -> expoPush "Envía la notificación push" "API REST / HTTPS"

        bus_eventos -> seguimiento_comp "Entrega turno.encolado / turno.atendido" "AMQP"
        seguimiento_comp -> base_datos "Registra el historial de eventos" "SQL"
    }

    views {
        systemContext comedoruni "Contexto" {
            include *
            autoLayout lr
        }

        container comedoruni "Contenedores" {
            include *
            autoLayout lr
        }

        component backend "Componentes" {
            include *
            autoLayout tb
        }

        styles {
            element "Externo" {
                background #999999
                color #ffffff
            }
            element "Base de datos" {
                shape Cylinder
            }
        }
    }
}
