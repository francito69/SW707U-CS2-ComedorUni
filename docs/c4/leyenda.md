# Leyenda — Modelo C4 de ComedorUNI

## Qué muestra cada figura

**Contexto (`img/contexto.png`).** ComedorUNI como una sola caja, con dos roles reales —
Estudiante y Administrador del comedor— y **dos** sistemas externos reales: el Portal
Alumnos UNI (`alumnos.uni.edu.pe`, fuente de identidad y datos académicos) y el Expo Push
Notification Service (`exp.host`, entrega de push). No aparece pasarela de pago ni SMS ni
correo institucional como notificador: el único canal de notificación implementado es push.

**Contenedores (`img/contenedores.png`).** Cinco contenedores reales: la app móvil (React
Native + Expo Router, que incluye un WebView embebido para el login/scraping del Portal
Alumnos), el Backend (FastAPI/Uvicorn — API HTTP/WS + worker de inactividad + consumers M4/M5
corriendo todos como tareas `asyncio` del mismo proceso, ver `main.py`), PostgreSQL, Redis y
RabbitMQ.

**Componentes (`img/componentes.png`).** Se abrió el **Backend** completo (no solo "turnos",
porque el mismo proceso también sirve autenticación, menú y configuración). Siete
componentes, agrupados por responsabilidad: Autenticación y Sesión, Router y Servicio de
Turnos, Router de Configuración y Menú, Worker de Inactividad, Reasignación, Notificaciones
(M4) y Seguimiento (M5).

## Qué se dejó afuera a propósito

- La URL del backend ya no queda hardcodeada en `frontend/src/constants/api.ts`: se resuelve
  mediante variables de entorno (`EXPO_PUBLIC_API_URL` y `EXPO_PUBLIC_WS_URL`). Esto se
  documenta en el ADR correspondiente, porque es una decisión de configuración operativa y no
  una pieza del modelo C4.
- No se dibujó un componente de **caché de resultados** ni **balanceador de carga**: ninguno
  existe en el código.
- No se dibujó un componente de **Repositorio** genérico: solo `auth` tiene una capa
  separada (`estudiante_repo.py`); `queues`, `config` y `menu` embeben el SQL directamente en
  su `service.py`. Modelarlo como capa aparte habría sido inventar una abstracción que el
  código no tiene.

## Supuestos de la semana pasada — resueltos contra el código real

La semana 3 estos dos puntos quedaron pendientes porque el repo era inaccesible. Esta semana
se leyó `s111-actividad-bosquejo-implementacion/backend/src` directamente y ambos se
resuelven así:

1. **"Sistema de Autenticación Institucional" (genérico, OAuth/HTTPS) → estaba mal.** No hay
   ninguna llamada OAuth desde el backend. El login real es: la app abre un **WebView** hacia
   `https://alumnos.uni.edu.pe/redirect-google`, el estudiante inicia sesión ahí (Google por
   detrás, pero el sistema no llama a Google directamente), la app **scrapea** el HTML de
   `/home`, `/informacion-academica/cursos` y `/configuracion/datos-personales`, y se lo
   manda al backend por `POST /parse-data` para que lo parsee y persista. Se renombró la caja
   a **Portal Alumnos UNI** y se corrigió la relación: no es `Backend → OAuth`, es
   `Aplicación móvil → Portal Alumnos UNI` vía WebView.
2. **"Worker de expiración" como contenedor separado → estaba mal.** `main.py` arranca
   `inactivity_worker()` con `asyncio.create_task()` dentro del `lifespan` del mismo `FastAPI
   app`, junto con los consumers M4/M5. Los tres corren en el mismo proceso que la API. Se
   fusionó en el contenedor **Backend (API + Workers)** y se modeló como componente aparte en
   el nivel 3 (sí tiene su propia responsabilidad — orquesta reasignación por tiempo en vez
   de por petición — pero no es un proceso ni un deploy distinto).

## Hallazgos nuevos de esta lectura (no estaban en la ficha de la semana 2)

- **No hay JWT.** `docs/ficha-del-sistema.md` y el `componentes.puml` anterior asumían
  autenticación por JWT; el código usa **sesión por `sid` guardada en Redis**
  (`auth/redis_store.py`), sin tokens firmados. Se corrigió en el componente de
  Autenticación.
- **Verificación biométrica.** Hay un segundo factor no documentado antes: comparación facial
  con DeepFace/Facenet (`auth/biometric.py`) contra la foto vigente que trae el scraping del
  Portal Alumnos.
- **Módulo de Menú.** Existe `modules/menu` (alta/edición del menú del día, reusado por
  `config/router.py` para el flujo de administrador) — no estaba en la lista de módulos de
  `1.2` ni `3.1.0`. Falta decidir si esto se documenta como parte de M7 (Configuración) o si
  merece su propio módulo en el informe.
- **Expo Push nunca estuvo en el modelo.** Los tres `.puml` de la semana 3 no lo incluían a
  pesar de que `shared/push.py` y `notifications/consumer.py` (M4) ya existían en el código
  aprobado. Se agregó como sistema externo en los tres niveles.

## Observación propia del equipo

La duplicación de la regla de expiración que se anotó la semana pasada (Servicio de Turnos
vs. Worker) sigue existiendo, pero ahora se puede precisar: ambos caminos llaman a la misma
función `reassignment.llamar_siguiente()` — no hay lógica de reasignación duplicada, lo que
se repite es solo el disparador (confirmación de asistencia vs. ciclo de 60s del worker).

## Observaciones del equipo revisor (paso 4)

_Pendiente de completar durante la sesión del sábado 19 de setiembre — cada equipo revisor
anota aquí lo que encontró, con su nombre._

- Equipo revisor: _(nombre)_ — hallazgo:
