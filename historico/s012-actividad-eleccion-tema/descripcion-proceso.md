# Sistema de Gestión de Colas Virtuales para el Comedor Universitario

---
## Contexto del Proceso
El proceso de gestión de turnos para el comedor universitario se desarrolla dentro del servicio de alimentación de la Universidad Nacional de Ingeniería, el cual forma parte de la Dirección de Bienestar Universitario.

Este servicio tiene como función principal brindar alimentación diaria a los estudiantes, atendiendo una alta demanda en horarios específicos, especialmente durante el almuerzo.

Dentro de este contexto, el proceso analizado corresponde a la organización del acceso de los estudiantes al comedor, específicamente en la asignación de turnos previos al ingreso.

Actualmente, esta actividad se realiza mediante mecanismos poco automatizados, esto genera dificultades para manejar grandes volúmenes de estudiantes de manera ordenada.

El rol de este proceso dentro del servicio es crítico, ya que actúa como el punto de control previo al uso del comedor, influyendo direcamente en la distribución de estudiantes, el uso de recursos y la experiencia general del servicio.


---
---
## Propósito del Proceso
El proceso de gestión de turnos para el comedor universitario tiene como propósito organizar y controlar el acceso de los estudiantes al servicio de alimentación, asegurando una distribución ordenada de la demanda en función de la capacidad disponible.

Este proceso busca resolver el problema de la alta concentración de estudiantes en horarios específicos, lo cual actualmente genera colas prolongadas, desorden en el acceso y pérdida de tiempo.

A través de la asignación previa de turnos, el proceso permite:
- Distribuir a los estudiantes en intervalos de tiempos definidos
- Evitar la saturación del servicio en momentos críticos
- Reducir tiempos de espera
- Mejorar la experiencia del usuario

En ese sentido, el valor que genera el proceso es una gestión más eficiente del flujo de estudiantes, lo que permite un mejor uso de los recursos del comedor y un acceso más organizado al servicio.


---
---
## Alcance del Proceso
El proceso de gestión de colas virtuales para el comedor universitario comprende todas las actibidades relacionadas con la solicitud, asignación y confirmación de turnos por parte de los estudiantes, previas al ingreso al comedor.

- <i><b>Inicio del proceso</b></i>
El estudiante solicita un turno para acceder al servicio del comedor.

- <i><b>Fin del proceso</b></i>
El estudiante obtiene un turno asignado y, en caso corresponda, confirma su asistencia dentro del tiempo establecido.

<b>Actividades Incluidas:</b>
- Validación del estudiante
- Registro de solicitud de turno
- Asignación automática a una cola virtual
- Notificación del turno asignado
- Confirmación de asistencia por parte del estudiante
- Liberación y reasignación de cupos en caso de inactividad

<b>Límites del Proceso (fuera de alcance):</b>
- Control físico de ingreso al comedor
- Verificación presencial del turno dentro del comedor
- Preparación y distribución de alimentos
- Gestión operativa interna del comedor

El proceso definido no reemplaza el sistema de ingreso físico al comedor, sino que funciona como un mecanismo previo de organización.

Sin embargo, ambos procesos están relacionados, ya que "<i>la posesión de un turno válido es condición necesaria para que el estudiante pueda acceder al comedor</i>".


---
---
## Entradas y Salidas del Proceso

### Entradas

| Categoría               | Elemento             | Descripción                                                   |
| ----------------------- | -------------------- | ------------------------------------------------------------- |
| Datos del estudiante    | Código universitario | Identificador único del estudiante                            |
|                         | Nombres              | Nombre completo del estudiante                                |
|                         | Estado académico     | Indica si el estudiante es alumno activo                      |
|                         | Foto de carné        | Imagen asociada al estudiante para validación                 |
| Solicitud de turno      | Petición de turno    | Solicitud realizada por el estudiante para acceder al comedor |
| Parámetros del servicio | Cantidad de raciones | Número total de raciones disponibles por día                  |
|                         | Capacidad por turno  | Número máximo de estudiantes por cola virtual                 |
|                         | Duración del turno   | Tiempo asignado a cada cola virtual                           |
|                         | Horarios de atención | Intervalos de tiempo en los que opera el comedor              |

### Salidas

| Categoría            | Elemento                | Descripción                                                        |
| -------------------- | ----------------------- | ------------------------------------------------------------------ |
| Turno asignado       | Hora de atención        | Hora específica en la que el estudiante debe acudir                |
|                      | Cola virtual            | Identificación de la cola asignada                                 |
| Confirmación         | Notificación de turno   | Mensaje enviado al estudiante con los detalles de su reserva       |
| Estado del turno     | Confirmado              | Indica que el estudiante validó su asistencia                      |
|                      | Perdido por inactividad | Indica que el estudiante no confirmó dentro del tiempo establecido |
| Registro del proceso | Historial de turnos     | Registro de todos los turnos asignados                             |
|                      | Asistencia/Inasistencia | Registro del comportamiento del estudiante respecto a su turno     |


---
---
## Actores del Proceso

| Actor         | Tipo    | Descripción                                                        | Responsabilidades principales                                                               |
| ------------- | ------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| Estudiante    | Usuario | Alumno de la universidad que utiliza el servicio de comedor        | - Solicitar turno<br>- Consultar información<br>- Confirmar asistencia                      |
| Administrador | Interno | Personal encargado de configurar y supervisar el sistema de turnos | - Definir capacidad de colas<br>- Configurar horarios<br>- Gestionar parámetros del sistema |
| Sistema       | Sistema | Plataforma encargada de gestionar la lógica del proceso            | - Validar estudiante<br>- Asignar turnos<br>- Gestionar colas<br>- Enviar notificaciones    |


El Sistema se considera actor porque ejecuta automáticamente las reglas del proceso y coordina la interacción entre los demás actores.


---
---
## Reglas de Negocio
El proceso de gestión de colas virtuales para el comedor universitario se rige por las siguientes reglas:

- Solo pueden acceder al sistema los estudiantes que se encuentren en condición de alumnos activos, previamente validados mediante sus credenciales institucionales.
- Cada estudiante puede registrar como máximo un turno por servicio (almuerzo o cena), evitando la acumulación de múltiples reservas.
- Los turnos son asignados de manera automática y en orden de llegada, garantizando equidad en el acceso al servicio.
- Las colas virtuales tienen una capacidad limitada, definida en función de la cantidad de raciones disponibles y la planificación del servicio.
- Las colas se organizan en bloques de tiempo. donde cada bloque representa un turno con horario de inicio y duración establecidos.
- El estudiante debe confirmar su asistencia cuando su turno se encuentre activo.
- Existe un tiempo máximo de confirmación de x minuto(s); si el estudiante no confirma dentro de ese periodo, pierde automáticamente su turno.
- Los turnos liberados por inasistencia deben de ser reasignados a otros estudiantes, asegurando el aprovechamiento de los cupos disponibles.
- No está permitido que un estudiante tenga más de un turno activo simultáneamente.
- La posesión de un turno válido es una condición necesaria para acceder al comedor, aunque el control de ingreso físico pertenece a un proceso externo.

---
---
## Problemas Actuales y Oportunidades de Mejora

### Problemas Actuales
El proceso actual para la obtención de turnos del comedor universitario en la Universidad Nacional de Ingeniería presenta diversas limitaciones que afectan directamente a los estudiantes:

- <u>Formación de largas colas físicas</u>:
Los estudiantes deben asistir presencialmente en horarios específicos (mañana y tarde) para solicitar un turno, lo que genera filas extensas dentro del campus y largos tiempos de espera.
- <u>Limitación en el acceso al servicio</u>:
Solo los estudiantes que lograron llegar temprano y permanecer en la cola pueden obtener un turno, dejando fuera a aquellos que, por distintos motivos, no pueden asistir en dichos horarios.
- <u>Incertidumbre en la obtención de turnos</u>:
Aun después de haber esperado largos periodos en la cola, no existe garantía de obtener un turno, lo que genera frustración y pérdida de tiempo.
- <u>Impacto en el bienestar del estudiante</u>:
La necesidad de acudir temprano para obtener un turno puede afectar el descanso y generar desgaste físico, especialmente en estudiantes que tienen actividades académicas posteriores.
- <u>Dependencia del "turno carroña"</u>:
Los estudiantes que no logran obtener turno deben recurrir a esperar durante el horario de atención del comedor, hasta que se liberen cupos, lo cual implica largas horas de espera e incertidumbre sobre si podrán acceder al servicio.

### Oportunidades de Mejora
A partir de los problemas identificados, se presentan las siguientes oportunidades:

- <u>Digitalización del proceso de obtención de turnos</u>:
Permitir que los estudiantes soliciten turnos de manera remota, eliminando la necesidad de relizar colas físicas.
- <u>Acceso más equitativo al servicio</u>:
Brindar la posibilidad de obtener turnos sin depender de la presencia física temprana, beneficiando a estudiantes con diferentes horarios y condiciones.
- <u>Reducción de tiempos de espera innecesarios</u>:
Evitar que los estudiantes tengan que permanecer largos periodos en cola sin garantía de atención.
- <u>Eliminación o reducción del "turno carroña"</u>:
Disminuir la necesidad de esperar durante el horario de atención del comedor para obtener un cupo.
- <u>Mejora en la planificación del estudiante</u>:
Permitir que el usuario conozca con anticipación si cuenta con un turno, facilitando la organización de su tiempo.
- <u>Optimización del uso de cupos disponibles</u>:
Gestionar de manera más eficiente la asignación de turnos y la redistribución de cupos no utilizados.


---
---
## Indicadores del Proceso (KPIs)
Para evaluar el desempeño del proceso de gestión de turnos del comedor, se proponen los siguientes indicadores:

- <b>Tiempo promedio para obtener turno</b>:
Mide el tiempo que le toma a un estudiante conseguir un turno desde que inicia el proceso.<br>
Objetivo -> Reducir el tiempo que actualmente se invierte en hacer colas físicas

- <b>Tasa de obtención de turnos</b>:
Porcentaje de estudiantes que logran obtener un turno respecto al total que lo intentan.<br>
Objetivo -> Aumentar la cantidad de estudiantes que accedan al servicio sin quedar excluídos.

- <b>Tasa de estudiantes sin turno</b>:
Porcentaje de estudiantes que no logran obtener turno.<br>
Objetivo -> Disminuir la dependencia del "turno carroña".

- <b>Tasa de reasignación de turnos</b>:
Porcentaje de turnos que son liberados y reasignados a otros estudiantes.<br>
Objetivo -> Asegurar que los cupos no se desperdicien.

- <b>Tiempo de espera para obtener turno (cola física vs virtual)</b>:
Comparación entre:
    - tiempo en cola física (actual)
    - tiempo en sistema virtual

    Objetivo -> Evidenciar la mejora del proceso.

- <b>Nivel de ocupación de turnos</b>:
Porcentaje de turnos utilizados respecto a los disponibles.<br>
Objetivo -> Maximizar el uso de las raciones disponibles.

- <b>Tasa de inasistencia a turnos</b>:
Porcentaje de estudiantes que obtienen turno pero no lo utilizan.<br>
Objetivo -> Identificar pérdidas de cupos y justificar mejoras (sanciones futuras).

- <b>Cantidad de turnos gestionados por día</b>:
Número total de turnos asignados diariamente.<br>
Objetivo -> Medir la capacidad operativa del sistema.