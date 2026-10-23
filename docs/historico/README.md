# Archivo Histórico del Proyecto ComedorUNI

Este directorio conserva la documentación y los antecedentes del prototipo previo desarrollado para el dominio del comedor universitario, antes de su evolución e integración en el curso **Construcción de Software II (SW707 - 2026-II)**.

---

## 1. Contexto de la Transición a SW707
El sistema original nació como una propuesta para resolver las extensas colas físicas en el Comedor Universitario de la UNI mediante un prototipo de cola virtual. Al ingresar al curso SW707, el proyecto fue sometido a una auditoría técnica profunda y a una reingeniería de calidad, orientada no solo a "hacer que funcione", sino a cumplir rigurosamente con los principios de construcción avanzada:

1. **Gestión de dependencias y reúso responsable:** Auditoría de vulnerabilidades y portabilidad.
2. **Análisis de problemas de runtime:** Resincronización de configuraciones, variables de entorno y ciclo de vida de procesos.
3. **Design by Contract (DbC):** Formalización de precondiciones, postcondiciones e invariantes en API y persistencia.
4. **Programación defensiva:** Barricadas y filtrado de datos no confiables provenientes de scraping y clientes móviles.
5. **Manejo de errores y excepciones:** Supresión de antipatrones (*log and throw*, capturas genéricas silenciosas) y adopción de contratos HTTP estándar.
6. **Concurrencia:** Protección estricta contra condiciones de carrera en aforo y numeración mediante transacciones y bloqueos de fila (`SELECT ... FOR UPDATE`).
7. **Tolerancia a fallas:** Desacoplamiento asíncrono con RabbitMQ (Topic Exchange), reconexión robusta e idempotencia.

---

## 2. Contenido del Archivo Histórico

- **[s012-actividad-eleccion-tema/](s012-actividad-eleccion-tema/):**
  - `descripcion-proceso.md`: Descripción original del proceso de atención y negocio del comedor UNI.
  - `diagramacion-proceso.md`: Diagramas de flujo originales del negocio.
  - `especificacion-requisitos-funcionales.md`: Especificación funcional inicial del estudiante y administración.
- **[s031-actividad-documentacion-arquitectura/](s031-actividad-documentacion-arquitectura/):**
  - `c4.md`: Primer borrador del modelo C4 inicial antes de las correcciones de SW707.
- **[prototipos.md](prototipos.md):**
  - Capturas y esquemas de los prototipos iniciales de interfaz de usuario.

---

## 3. Documentación Vigente para SW707
Para consultar la arquitectura vigente, los entregables oficiales y el documento técnico del Examen Parcial de SW707, remítase a:
- [Documento Técnico Parcial SW707](../DocumentoTecnicoParcial.md)
- [README de Documentación](../README.md)
- [README Principal del Repositorio](../../README.md)
