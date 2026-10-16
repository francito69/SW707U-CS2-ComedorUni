# Diagramación del Proceso

## Diagrama BPMN

El proceso de gestión de turnos virtuales para el comedor universitario inicia cuando el estudiante accede al sistema con la intención de obtener un turno para un servicio de alimentación.

En primer lugar, el estudiante ingresa sus credenciales institucionales, las cuales son validadas por el sistema para verificar que se trate de un estudiante activo. En caso de que la validación falle, el proceso finaliza. Si la validación es exitosa, el estudiante puede continuar con la solicitud.

Posteriormente, el estudiante realiza la solicitud de un turno. El sistema recibe esta solicitud y verifica la disponibilidad de cupos en las colas virtuales previamente definidas. Si no existen cupos disponibles, el sistema informa esta situación y el proceso finaliza.

En caso de existir disponibilidad, el sistema asigna automáticamente al estudiante a una cola virtual, considerando la capacidad establecida y el orden de llegada. A partir de esta asignación, se genera un turno con un horario específico, el cual es notificado al estudiante.

El sistema permanece en espera hasta que se alcanza la hora de inicio del turno asignado. En ese momento, se envía una notificación al estudiante indicando que debe confirmar su asistencia.

El estudiante dispone de un tiempo limitado para confirmar su asistencia. Si el estudiante no realiza la confirmación dentro del tiempo establecido, el sistema libera el cupo asignado y lo reasigna a otro estudiante, finalizando el proceso sin éxito.

Por el contrario, si el estudiante confirma su asistencia dentro del tiempo permitido, el turno queda validado y el proceso finaliza exitosamente.

---
<img src="../../../resources/img/diagrama-proceso.png">

---
---
## Tabla de Descripción de Actividades
| Nº  | Actividad                              | Descripción                                                                                           | Responsable | Entradas                               | Salidas                         | Reglas de negocio                                          | Sistema implicado                     |
| --- | -------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------- | ------------------------------- | ---------------------------------------------------------- | ------------------------------------- |
| A1  | Ingresar credenciales institucionales  | El estudiante ingresa sus credenciales (@uni.pe) para acceder al sistema y poder solicitar un turno.  | Estudiante  | Credenciales del estudiante            | Solicitud de autenticación      | RN01: Solo estudiantes activos pueden acceder              | Sistema de Turnos                     |
| A2  | Validar condición de estudiante activo | El sistema verifica que el usuario sea un estudiante activo consultando la información institucional. | Sistema     | Credenciales del estudiante            | Validación (válido / no válido) | RN01: Solo estudiantes activos pueden continuar            | Sistema de Turnos / API institucional |
| A3  | Solicitar turno                        | El estudiante realiza la solicitud de un turno para el comedor dentro de los horarios habilitados.    | Estudiante  | Solicitud de turno                     | Solicitud registrada            | RN02: Un estudiante solo puede tener un turno por servicio | Sistema de Turnos                     |
| A4  | Verificar disponibilidad de cupos      | El sistema verifica si existen cupos disponibles en las colas virtuales.                              | Sistema     | Solicitud de turno, capacidad de colas | Disponibilidad de cupos         | RN03: Capacidad limitada por cola                          | Sistema de Turnos                     |
| A5  | Asignar cola virtual                   | El sistema asigna al estudiante a una cola virtual según disponibilidad y orden de llegada.           | Sistema     | Cupos disponibles, lista de colas      | Cola asignada                   | RN04: Asignación por orden de llegada (FIFO)               | Sistema de Turnos                     |
| A6  | Generar turno                          | El sistema crea el turno con la hora correspondiente según la cola asignada.                          | Sistema     | Cola asignada                          | Turno generado                  | RN05: Turnos organizados por bloques de tiempo             | Sistema de Turnos                     |
| A7  | Notificar turno al estudiante          | El sistema informa al estudiante el turno asignado y su horario.                                      | Sistema     | Turno generado                         | Notificación enviada            | RN05: Información clara del turno                          | Sistema de Turnos                     |
| A8  | Notificar inicio de turno              | El sistema envía una notificación al estudiante indicando que su turno está activo.                   | Sistema     | Hora de inicio del turno               | Notificación de inicio          | RN06: El estudiante debe confirmar asistencia              | Sistema de Turnos                     |
| A9  | Confirmar asistencia                   | El estudiante confirma su asistencia dentro del tiempo establecido.                                   | Estudiante  | Notificación de turno                  | Confirmación de asistencia      | RN07: Tiempo máximo de confirmación (1 minuto)             | Sistema de Turnos                     |
| A10 | Liberar cupo                           | El sistema libera el cupo cuando el estudiante no confirma asistencia dentro del tiempo establecido.  | Sistema     | Turno no confirmado                    | Cupo disponible                 | RN08: Pérdida de turno por inactividad                     | Sistema de Turnos                     |
| A11 | Reasignar turno                        | El sistema asigna el cupo liberado a otro estudiante disponible.                                      | Sistema     | Cupo liberado                          | Nuevo turno asignado            | RN09: Reasignación de cupos                                | Sistema de Turnos                     |


---
---
## Glosario de Términos del Dominio

| Término                       | Definición                                                                                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Turno                         | Asignación de un intervalo de tiempo específico otorgado a un estudiante para acceder al servicio de comedor, previa confirmación de asistencia.                               |
| Cola virtual                  | Mecanismo digital que organiza a los estudiantes en un orden de atención, sin necesidad de presencia física, en función de la disponibilidad de cupos y el orden de solicitud. |
| Cupo                          | Unidad disponible dentro de una cola virtual que representa la capacidad máxima de atención del servicio en un intervalo de tiempo determinado.                                |
| Estudiante activo             | Usuario que se encuentra matriculado y habilitado académicamente, con autorización para acceder a los servicios institucionales.                                               |
| Solicitud de turno            | Acción mediante la cual un estudiante registra su intención de obtener un turno para el servicio de comedor a través del sistema.                                              |
| Asignación de turno           | Proceso mediante el cual el sistema otorga un turno a un estudiante, en función de la disponibilidad de cupos y las reglas de negocio establecidas.                            |
| Confirmación de asistencia    | Acción realizada por el estudiante para validar que hará uso del turno asignado dentro del tiempo establecido.                                                                 |
| Tiempo límite de confirmación | Intervalo máximo permitido para que el estudiante confirme su asistencia antes de que el turno sea liberado automáticamente.                                                   |
| Reasignación de turno         | Proceso mediante el cual un cupo liberado por inasistencia es asignado a otro estudiante disponible.                                                                           |
| Disponibilidad de cupos       | Estado que indica si existen espacios disponibles dentro de las colas virtuales para la asignación de nuevos turnos.                                                           |
| Validación de usuario         | Proceso de verificación de identidad y estado académico del estudiante mediante credenciales institucionales.                                                                  |
| Notificación                  | Mensaje enviado por el sistema al estudiante para informarle sobre el estado de su turno, incluyendo asignación, inicio y confirmación.                                        |
| Orden de llegada (FIFO)       | Regla de asignación en la que los turnos se otorgan según el orden en que los estudiantes realizan la solicitud.                                                               |
| Turno no confirmado           | Estado en el cual un turno asignado es cancelado automáticamente debido a la falta de confirmación dentro del tiempo establecido.                                              |
| Sistema de turnos             | Plataforma encargada de gestionar la solicitud, asignación, confirmación y control de turnos para el comedor universitario.                                                    |

---
---
