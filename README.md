# ComedorUNI

Sistema de gestión y cola del comedor universitario para agilizar la atención de estudiantes, controlar turnos, confirmar asistencia y coordinar la atención en tiempo real.

## ¿Qué hace ComedorUNI?

ComedorUNI permite a la universidad:

- registrar estudiantes y asignar turnos por tipo de servicio
- generar una cola ordenada por número de turno
- consultar el estado real de cada estudiante en la fila
- confirmar presencia y atender turnos desde el backend en tiempo real
- notificar llamados y cambios de estado mediante eventos y WebSockets
- llevar control de raciones, inactividad y reasignación de turnos

Es una solución enfocada en la operación del comedor: orden, trazabilidad y atención más ágil para estudiantes y personal administrativo.

## Stack tecnológico

- Backend: Python + FastAPI
- Base de datos: PostgreSQL
- Cache y sesiones: Redis
- Mensajería/colas: RabbitMQ
- Frontend móvil: React Native + Expo
- Contenedores: Docker + Docker Compose
- Infraestructura de eventos: WebSockets + eventos asincrónicos

## Cómo se levanta el proyecto

### 1) Requisitos

- Python 3.11+
- Node.js 18+
- Docker Desktop / Docker Engine
- Git

### 2) Servicios base

Los servicios de infraestructura del proyecto están definidos en:

- [historico/s111-actividad-bosquejo-implementacion/docker-compose.yml](historico/s111-actividad-bosquejo-implementacion/docker-compose.yml)

Este compose levanta:

- PostgreSQL en puerto 5433
- Redis en puerto 6379
- RabbitMQ en puerto 5672 y su UI en 15672

Ejecuta:

```bash
docker compose -f historico/s111-actividad-bosquejo-implementacion/docker-compose.yml up -d
```

### 3) Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

El backend queda disponible en:

- API: http://localhost:8000
- Docs Swagger: http://localhost:8000/docs

### 4) Frontend

```bash
cd frontend/src
cp .env.example .env
npm install
npx expo start
```

> Convención única: Expo lee variables desde `frontend/src/.env`. El template es `frontend/src/.env.example`. No se debe crear un `.env` en la raíz del repositorio para la app móvil/web.

Desde la app móvil/web se consume la API del backend para iniciar sesión, unirse a la cola, confirmar presencia y consultar estado del turno.

## Estructura del repositorio

- [backend](backend): API, lógica de negocio, migraciones y servicios del sistema
- [frontend](frontend): aplicación móvil/web del cliente
- [docs](docs): documentación de arquitectura y soporte
- [resources](resources): recursos visuales e imágenes
- [historico](historico): artefactos históricos y versiones previas del proyecto
- [0](0), [1](1), [2](2), ... [17](17): documentación académica del proyecto grupal por capítulos

## ¿Dónde está la documentación académica?

Este repositorio combina dos cosas:

1. Una solución funcional de software para ComedorUNI.
2. La documentación del proyecto de diseño de software, organizada por secciones del 0 al 17.

La documentación de arquitectura, requisitos, decisiones de diseño y prototipos está en la estructura de carpetas numeradas del repositorio.

## Documentación SW707

- [Ficha inicial de propuesta corregida](fichainicialpropuestaComedorUni.md)
- [Documento técnico parcial](DocumentoTecnicoParcial.md)
- [Escenarios de calidad actuales](docs/escenarios.md)
- [Modelo C4](docs/c4/)

## Cronograma SW707 semana a semana

El integrador oficial define 16 semanas. La semana 1 aparece sin resultado esperado; aquí se propone usarla para organizar el equipo y presentar/validar la propuesta, sin atribuir esa actividad al texto oficial. Las semanas 2 a 16 siguen sus resultados previstos y los convierten en entregables verificables para ComedorUNI. Las tareas se realizan sobre el prototipo existente.

| Semana | Enfoque y trabajo de ComedorUNI | Evidencia o resultado esperado | Responsable de coordinación* |
|---|---|---|---|
| 1 | Alinear problema, integrantes, alcance, repositorio y propuesta SW707 con el docente. | Ficha corregida y alcance aprobado o con observaciones registradas. | Franz y Yazid |
| 2 | Revisar arquitectura, repositorio y dependencias existentes; identificar versiones, licencias, configuración y cómo levantar cada componente. | C4 contrastado con el código, ADRs pertinentes e inventario de dependencias/runtime. | Franz |
| 3 | Reproducir problemas de runtime y especificar contratos de las operaciones críticas: login/sesión, solicitud, confirmación y configuración. | Pasos de reproducción, pre/postcondiciones, respuestas esperadas y riesgos documentados. | Yazid |
| 4 | Añadir programación defensiva para entradas, estados, configuración y respuestas de dependencias. | Validaciones y pruebas de entradas inválidas, sin mutaciones parciales. | Franz |
| 5 | Unificar errores y excepciones de API, persistencia y consumers; evitar filtración de datos sensibles. | Tabla de errores/códigos, logs accionables y pruebas de fallos controlados. | Yazid |
| 6 | Corregir la atomicidad de capacidad y numeración; comprobar unicidad de turno ante concurrencia. | Pruebas paralelas con inspección de PostgreSQL: límite respetado, sin duplicados y conflicto controlado. | Franz y Yazid |
| 7 | Diseñar y probar recuperación ante caída de RabbitMQ/Redis/DB según el flujo; preparar cierre de alcance parcial. | Política documentada de reintento/idempotencia, resultados de fallo y checklist v1.0. | Franz |
| 8 | Presentar el examen parcial: versión v1.0 funcional, verificable y preparada para fallos y concurrencia. | Tag/commit identificable de v1.0, instrucciones de ejecución y evidencia de pruebas. | Franz y Yazid |
| 9 | Modelar estados/transiciones de turnos y externalizar configuración; incorporar feature flag solo si el caso lo justifica. | Tabla de transiciones, reglas probadas y configuración de ejemplo sin secretos. | Yazid |
| 10 | Agregar logs estructurados y métricas pertinentes; medir baseline y perfilar el punto crítico de cola. | Métricas, procedimiento y baseline reproducible; no solo cifras aisladas. | Franz |
| 11 | Revisar contratos REST/WebSocket, integración con RabbitMQ y contenedores; completar Dockerfiles/Compose si resulta útil. | Contratos versionados, servicios que levantan reproduciblemente y prueba de integración. | Franz y Yazid |
| 12 | Identificar code smells y refactorizar el módulo seleccionado con pruebas de regresión. | Cambio pequeño justificado, pruebas antes/después y comportamiento preservado. | Yazid |
| 13 | Clasificar cambios correctivos, adaptativos, perfectivos o preventivos y analizar impacto. | Registro de al menos cuatro cambios, dependencias afectadas y trazabilidad en Git. | Franz |
| 14 | Seleccionar un componente legacy/versionado y escribir pruebas de caracterización antes de modificarlo. | Comportamiento actual capturado y límites conocidos del componente. | Franz y Yazid |
| 15 | Recuperar arquitectura/dependencias desde el código y modernizar incrementalmente un componente propio. | Informe de ingeniería reversa, decisión de reingeniería y comparación sustentada por pruebas. | Yazid |
| 16 | Presentar el examen final y la evolución desde v1.0. | Versión v2.0, métricas antes/después, pruebas de regresión, historial Git y conclusiones. | Franz y Yazid |

\* Responsable de coordinación no significa autor exclusivo: ambos integrantes revisan, comprenden y pueden defender cualquier parte del sistema. Los commits deben reflejar contribuciones identificables de Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas. El equipo actualizará este cronograma si el docente modifica fechas o alcance.

### Estado documental al iniciar SW707

El equipo ya cuenta con una ficha del sistema en [docs/ficha-del-sistema.md](docs/ficha-del-sistema.md), escenarios de calidad en [docs/escenarios.md](docs/escenarios.md) y diagramas C4/leyenda en [docs/c4/](docs/c4/). Son insumos de partida: hay que verificar su correspondencia con el código y corregir supuestos antes de presentarlos como resultados. La ficha y el documento técnico nuevos explican esos ajustes.

## Índice del proyecto grupal

## Tabla de Contenido

- [0. Acerca del Grupo](./0/0.md)
  - [0.1. Integrante 1](./0/0.1/0.1.md)
  - [0.2. Integrante 2](./0/0.2/0.2.md)
  - [0.3. Integrante 3](./0/0.3/0.3.md)
  - [0.4. Integrante 4](./0/0.4/0.4.md)
  - [0.5. Temas Individuales](./0/0.5/0.5.md)
    - [0.5.1. PC 1](./0/0.5/0.5.1/0.5.1.md)
      - [0.5.1.1. Integrante 1](./0/0.5/0.5.1/0.5.1.1/0.5.1.1.md)
      - [0.5.1.2. Integrante 2](./0/0.5/0.5.1/0.5.1.2/0.5.1.2.md)
      - [0.5.1.3. Integrante 3](./0/0.5/0.5.1/0.5.1.3/0.5.1.3.md)
      - [0.5.1.4. Integrante 4](./0/0.5/0.5.1/0.5.1.4/0.5.1.4.md)
    - [0.5.2. PC 2](./0/0.5/0.5.2/0.5.2.md)
      - [0.5.2.1. Integrante 1](./0/0.5/0.5.2/0.5.2.1/0.5.2.1.md)
      - [0.5.2.2. Integrante 2](./0/0.5/0.5.2/0.5.2.2/0.5.2.2.md)
      - [0.5.2.3. Integrante 3](./0/0.5/0.5.2/0.5.2.3/0.5.2.3.md)
      - [0.5.2.4. Integrante 4](./0/0.5/0.5.2/0.5.2.4/0.5.2.4.md)
    - [0.5.3. PC 3](./0/0.5/0.5.3/0.5.3.md)
      - [0.5.3.1. Integrante 1](./0/0.5/0.5.3/0.5.3.1/0.5.3.1.md)
      - [0.5.3.2. Integrante 2](./0/0.5/0.5.3/0.5.3.2/0.5.3.2.md)
      - [0.5.3.3. Integrante 3](./0/0.5/0.5.3/0.5.3.3/0.5.3.3.md)
      - [0.5.3.4. Integrante 4](./0/0.5/0.5.3/0.5.3.4/0.5.3.4.md)
    - [0.5.4. PC 4](./0/0.5/0.5.4/0.5.4.md)
      - [0.5.4.1. Integrante 1](./0/0.5/0.5.4/0.5.4.1/0.5.4.1.md)
      - [0.5.4.2. Integrante 2](./0/0.5/0.5.4/0.5.4.2/0.5.4.2.md)
      - [0.5.4.3. Integrante 3](./0/0.5/0.5.4/0.5.4.3/0.5.4.3.md)
      - [0.5.4.4. Integrante 4](./0/0.5/0.5.4/0.5.4.4/0.5.4.4.md)
- [1. Desarrollo del Tema Elegido](./1/1.md)
  - [1.1. Contexto](./1/1.1/1.1.md)
  - [1.2. Lista de Actores y Roles](./1/1.2/1.2.md)
  - [1.3. Lista de Reglas de Negocio](./1/1.3/1.3.md)
  - [1.4. Problemas y Oportunidades de Mejora](./1/1.4/1.4.md)
- [2. Especificación del Proceso de Negocio](./2/2.md)
  - [2.1. Diagrama del Proceso (TO-BE)](./2/2.1/2.1.md)
  - [2.2. Descripción de Actividades](./2/2.2/2.2.md)
  - [2.3. Glosario de Términos](./2/2.3/2.3.md)
- [3. Requisitos del Sistema](./3/3.md)
  - [3.1. Requisitos Funcionales por Módulo](./3/3.1/3.1.md)
    - [3.1.0. Listado de Módulos](./3/3.1/3.1.0/3.1.0.md)
    - [3.1.1. Módulo 1 / Integrante 1](./3/3.1/3.1.1/3.1.1.md)
    - [3.1.2. Módulo 2 / Integrante 2](./3/3.1/3.1.2/3.1.2.md)
    - [3.1.3. Módulo 3 / Integrante 3](./3/3.1/3.1.3/3.1.3.md)
    - [3.1.4. Módulo 4 / Integrante 4](./3/3.1/3.1.4/3.1.4.md)
    - [3.1.5. Listado Consolidado](./3/3.1/3.1.5/3.1.5.md)
    - [3.1.6. Prototipos de Interfaz](./3/3.1/3.1.6/3.1.6.md)
  - [3.2. Requisitos de Atributos de Calidad (Escenarios)](./3/3.2/3.2.md)
    - [3.2.1. Módulo 1 / Integrante 1](./3/3.2/3.2.1/3.2.1.md)
    - [3.2.2. Módulo 2 / Integrante 2](./3/3.2/3.2.2/3.2.2.md)
    - [3.2.3. Módulo 3 / Integrante 3](./3/3.2/3.2.3/3.2.3.md)
    - [3.2.4. Módulo 4 / Integrante 4](./3/3.2/3.2.4/3.2.4.md)
    - [3.2.5. Listado Consolidado](./3/3.2/3.2.5/3.2.5.md)
- [4. Documentación de Arquitectura (Modelo C4)](./4/4.md)
  - [4.1. Módulo 1 / Integrante 1](./4/4.1/4.1.md)
  - [4.2. Módulo 2 / Integrante 2](./4/4.2/4.2.md)
  - [4.3. Módulo 3 / Integrante 3](./4/4.3/4.3.md)
  - [4.4. Módulo 4 / Integrante 4](./4/4.4/4.4.md)
  - [4.5. Documentación Consolidada](./4/4.5/4.5.md)
    - [4.5.1. Contexto](./4/4.5/4.5.1/4.5.1.md)
    - [4.5.2. Contenedores](./4/4.5/4.5.2/4.5.2.md)
    - [4.5.3. Componentes](./4/4.5/4.5.3/4.5.3.md)
- [5. Decisiones de Diseño](./5/5.md)
  - [5.1. Módulo 1 / Integrante 1](./5/5.1/5.1.md)
  - [5.2. Módulo 2 / Integrante 2](./5/5.2/5.2.md)
  - [5.3. Módulo 3 / Integrante 3](./5/5.3/5.3.md)
  - [5.4. Módulo 4 / Integrante 4](./5/5.4/5.4.md)
  - [5.5. Listado Consolidado](./5/5.5/5.5.md)
- [6. Patrones de Arquitectura](./6/6.md)
  - [6.1. Módulo 1 / Integrante 1](./6/6.1/6.1.md)
  - [6.2. Módulo 2 / Integrante 2](./6/6.2/6.2.md)
  - [6.3. Módulo 3 / Integrante 3](./6/6.3/6.3.md)
  - [6.4. Módulo 4 / Integrante 4](./6/6.4/6.4.md)
  - [6.5. Listado Consolidado](./6/6.5/6.5.md)
- [7. Documentación de Arquitectura - Versión 2](./7/7.md)
  - [7.1. Módulo 1 / Integrante 1](./7/7.1/7.1.md)
  - [7.2. Módulo 2 / Integrante 2](./7/7.2/7.2.md)
  - [7.3. Módulo 3 / Integrante 3](./7/7.3/7.3.md)
  - [7.4. Módulo 4 / Integrante 4](./7/7.4/7.4.md)
  - [7.5. Documentación Consolidada](./7/7.5/7.5.md)
    - [7.5.1. Contexto](./7/7.5/7.5.1/7.5.1.md)
    - [7.5.2. Contenedores](./7/7.5/7.5.2/7.5.2.md)
    - [7.5.3. Componentes](./7/7.5/7.5.3/7.5.3.md)
- [8. Modelo de Dominio](./8/8.md)
  - [8.1. Módulo 1 / Integrante 1](./8/8.1/8.1.md)
  - [8.2. Módulo 2 / Integrante 2](./8/8.2/8.2.md)
  - [8.3. Módulo 3 / Integrante 3](./8/8.3/8.3.md)
  - [8.4. Módulo 4 / Integrante 4](./8/8.4/8.4.md)
  - [8.5. Diagrama Consolidado y Especificación](./8/8.5/8.5.md)
- [9. Decisiones de Modelo de Datos (Motores de Persistencia)](./9/9.md)
  - [9.1. Módulo 1 / Integrante 1](./9/9.1/9.1.md)
  - [9.2. Módulo 2 / Integrante 2](./9/9.2/9.2.md)
  - [9.3. Módulo 3 / Integrante 3](./9/9.3/9.3.md)
  - [9.4. Módulo 4 / Integrante 4](./9/9.4/9.4.md)
  - [9.5. Lista Consolidada de Decisiones](./9/9.5/9.5.md)
- [10. Modelo de Datos por Motor](./10/10.md)
  - [10.1. Módulo 1 / Integrante 1](./10/10.1/10.1.md)
  - [10.2. Módulo 2 / Integrante 2](./10/10.2/10.2.md)
  - [10.3. Módulo 3 / Integrante 3](./10/10.3/10.3.md)
  - [10.4. Módulo 4 / Integrante 4](./10/10.4/10.4.md)
  - [10.5. Diccionario de Datos Consolidado](./10/10.5/10.5.md)
  - [10.6. Estrategia de Poblamiento de Datos](./10/10.6/10.6.md)
- [11. Patrones de Diseño (GoF)](./11/11.md)
  - [11.1. Módulo 1 / Integrante 1](./11/11.1/11.1.md)
  - [11.2. Módulo 2 / Integrante 2](./11/11.2/11.2.md)
  - [11.3. Módulo 3 / Integrante 3](./11/11.3/11.3.md)
  - [11.4. Módulo 4 / Integrante 4](./11/11.4/11.4.md)
  - [11.5. Listado Consolidado](./11/11.5/11.5.md)
- [12. Diseño Orientado a Aspectos (AOP)](./12/12.md)
  - [12.1. Módulo 1 / Integrante 1](./12/12.1/12.1.md)
  - [12.2. Módulo 2 / Integrante 2](./12/12.2/12.2.md)
  - [12.3. Módulo 3 / Integrante 3](./12/12.3/12.3.md)
  - [12.4. Módulo 4 / Integrante 4](./12/12.4/12.4.md)
  - [12.5. Desarrollo Consolidado de Aspectos](./12/12.5/12.5.md)
- [13. Especificación de APIs](./13/13.md)
  - [13.1. Módulo 1 / Integrante 1](./13/13.1/13.1.md)
  - [13.2. Módulo 2 / Integrante 2](./13/13.2/13.2.md)
  - [13.3. Módulo 3 / Integrante 3](./13/13.3/13.3.md)
  - [13.4. Módulo 4 / Integrante 4](./13/13.4/13.4.md)
  - [13.5. Especificación OpenAPI Consolidada](./13/13.5/13.5.md)
- [14. Diseño para la Estabilidad y Continuidad](./14/14.md)
  - [14.1. Módulo 1 / Integrante 1](./14/14.1/14.1.md)
  - [14.2. Módulo 2 / Integrante 2](./14/14.2/14.2.md)
  - [14.3. Módulo 3 / Integrante 3](./14/14.3/14.3.md)
  - [14.4. Módulo 4 / Integrante 4](./14/14.4/14.4.md)
  - [14.5. Propuesta Consolidada](./14/14.5/14.5.md)
    - [14.5.1. Continuidad y Recuperación](./14/14.5/14.5.1/14.5.1.md)
    - [14.5.2. Escalabilidad, Rendimiento y Coordinación](./14/14.5/14.5.2/14.5.2.md)
    - [14.5.3. Seguridad, Control de Acceso y Protección de Datos](./14/14.5/14.5.3/14.5.3.md)
- [15. Documentación de Arquitectura C4 - Actualización y Despliegue](./15/15.md)
  - [15.1. Módulo 1 / Integrante 1](./15/15.1/15.1.md)
  - [15.2. Módulo 2 / Integrante 2](./15/15.2/15.2.md)
  - [15.3. Módulo 3 / Integrante 3](./15/15.3/15.3.md)
  - [15.4. Módulo 4 / Integrante 4](./15/15.4/15.4.md)
  - [15.5. Documentación Consolidada](./15/15.5/15.5.md)
    - [15.5.1. Contexto](./15/15.5/15.5.1/15.5.1.md)
    - [15.5.2. Contenedores](./15/15.5/15.5.2/15.5.2.md)
    - [15.5.3. Componentes](./15/15.5/15.5.3/15.5.3.md)
    - [15.5.4. Despliegue](./15/15.5/15.5.4/15.5.4.md)
- [16. Prototipo Ejecutable - Flujo Principal por Módulo](./16/16.md)
  - [16.1. Módulo 1 / Integrante 1](./16/16.1/16.1.md)
  - [16.2. Módulo 2 / Integrante 2](./16/16.2/16.2.md)
  - [16.3. Módulo 3 / Integrante 3](./16/16.3/16.3.md)
  - [16.4. Módulo 4 / Integrante 4](./16/16.4/16.4.md)
- [17. Prototipo Ejecutable - Escenarios de Calidad Abordados](./17/17.md)
  - [17.1. Módulo 1 / Integrante 1](./17/17.1/17.1.md)
  - [17.2. Módulo 2 / Integrante 2](./17/17.2/17.2.md)
  - [17.3. Módulo 3 / Integrante 3](./17/17.3/17.3.md)
  - [17.4. Módulo 4 / Integrante 4](./17/17.4/17.4.md)
