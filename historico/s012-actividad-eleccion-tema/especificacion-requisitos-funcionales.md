# 3. Especificación de Requisitos Funcionales
---

## Módulos del Sistema

### Gestión de Autenticación
Este módulo se encarga de gestionar el acceso de los estudiantes al sistema, asegurando que únicamente usuarios válidos (estudiantes activos) puedan utilizar la plataforma. Para ello, realiza la validación de credenciales institucionales y verifica la información del estudiante.

Funcionalidades:

- Permitir el inicio de sesión mediante credenciales institucionales (@uni.pe)
- Validar la identidad del estudiante
- Verificar la condición de estudiante activo
- Obtener datos del estudiante (código, nombres, estado, foto)

---

### Gestión de Turnos
Este módulo constituye el núcleo del sistema y se encarga de gestionar la solicitud y asignación de turnos para el comedor. Administra la organización de los estudiantes en colas virtuales, considerando la disponibilidad y el orden de llegada.

Funcionalidades:

- Permitir al estudiante solicitar turno
- Registrar solicitudes de turno
- Verificar disponibilidad de cupos
- Asignar estudiantes a colas virtuales
- Generar turnos con horario específico

---

### Gestión de Confirmación
Este módulo gestiona la interacción posterior a la asignación del turno, asegurando que el estudiante  confirme su asistencia dentro de un tiempo determinado. Permite validar el uso efectivo de los turnos asignados.

Funcionalidades:

- Notificar al estudiante el turno asignado
- Notificar el inicio del turno
- Permitir la confirmación de asistencia
- Controlar el tiempo límite de confirmación

---

