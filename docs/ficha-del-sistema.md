# Ficha del sistema: ComedorUNI

## 1. Identificación

- **Nombre:** ComedorUNI — gestión de turnos del comedor mediante colas virtuales.
- **Curso actual:** Construcción de Software II (SW707).
- **Origen:** prototipo desarrollado previamente para el dominio del comedor
  universitario y retomado como producto incremental.
- **Repositorio:** [francito69/SW707U-CS2-ComedorUni](https://github.com/francito69/SW707U-CS2-ComedorUni).
- **Equipo SW707:** Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas.
- **Estado:** prototipo existente en diagnóstico; la línea base `v1.0` parcial debe
  cerrarse con pruebas de negocio, concurrencia y fallos.

## 2. Problema y objetivo

El sistema busca ordenar la atención del comedor mediante turnos virtuales, reducir
la dependencia de filas físicas y permitir que estudiantes y administradores
consulten el estado operativo de la cola. No se dispone en este repositorio de
mediciones que permitan afirmar una reducción cuantificada de tiempos o filas.

## 3. Usuarios y alcance observado

- **Estudiante:** inicia sesión desde la aplicación, consulta opciones del comedor,
  solicita/consulta un turno y confirma o cancela según el estado permitido.
- **Administrador del comedor:** configura opciones operativas y menú.
- **Portal Alumnos UNI:** fuente externa utilizada por el flujo móvil de acceso y
  lectura de datos académicos.
- **Expo Push Notification Service:** proveedor externo de notificaciones push.

El prototipo contiene una app Expo, API FastAPI, gestión de autenticación y sesiones,
turnos/colas, menú/configuración, PostgreSQL, Redis, RabbitMQ, WebSockets y tareas
asíncronas dentro del proceso backend.

## 4. Reglas de negocio a verificar

1. Un estudiante no debe conservar más de un turno activo para el mismo turno diario.
2. La cantidad de asignaciones no debe superar la capacidad configurada.
3. Un turno llamado que no se confirma dentro del plazo de negocio debe expirar y
   liberar capacidad conforme a la política vigente.

Las invariantes de unicidad tienen soporte en restricciones de base de datos. La
capacidad bajo concurrencia y la política completa de transición/expiración todavía
requieren pruebas reproducibles; no se consideran demostradas solo por estar
documentadas.

## 5. Stack y ejecución

- **Backend:** Python, FastAPI y Uvicorn.
- **Frontend:** TypeScript, React Native y Expo Router.
- **Datos:** PostgreSQL; Redis para sesiones.
- **Mensajería:** RabbitMQ.
- **Desarrollo local:** Docker Compose para PostgreSQL/Redis/RabbitMQ; Python/pip
  para backend y npm/Expo para cliente.

Las instrucciones vigentes están en el [README principal](../README.md). Los
ejemplos de entorno son `.env.example` y `frontend/src/.env.example`.

## 6. Riesgos de construcción identificados

- El puerto PostgreSQL publicado por Compose y el puerto por defecto del cliente
  backend difieren.
- La comprobación de capacidad y la reserva/numeración aún requieren una misma
  frontera transaccional y pruebas concurrentes.
- El control WebSocket y los workers viven en el proceso local; no se ha demostrado
  coordinación entre réplicas.
- El reintento de RabbitMQ al iniciar no demuestra entrega sin pérdida ni
  recuperación durante la operación.
- La capa de dependencias frontend reportó alertas de auditoría en el corte actual;
  deben revisarse sin aplicar actualizaciones automáticas sin evaluación.
- No existe aún una suite de pruebas automatizadas de negocio en `tests/`;
  tampoco hay pruebas automatizadas frontend.

Consulta el [avance SW707 hasta el parcial](avance-parcial-sw707.md) y el
[documento técnico parcial](DocumentoTecnicoParcial.docx) para la evidencia y los
criterios de cierre.
