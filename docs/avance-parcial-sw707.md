# Avance de ComedorUNI hasta el examen parcial

**Corte:** 15 de octubre de 2026  
**Curso:** Construcción de Software II (SW707)  
**Equipo SW707:** Franz Joe Inga Champi y Yazid Elio Fernandez Dueñas

Este registro aplica el cronograma del [Proyecto Integrador](Proyecto_Integrador_SW707.docx)
al repositorio existente. Los estados distinguen documentos de análisis de
implementación probada: escribir un riesgo o un criterio de aceptación no significa
que el sistema ya lo cumpla.

## Seguimiento por semana

| Semana | Resultado que se busca | Evidencia actual | Estado |
|---|---|---|---|
| 1 | Alinear problema, equipo, alcance y propuesta. | La [ficha del sistema](ficha-del-sistema.md) identifica el dominio, alcance y equipo; registra una aprobación de propuesta fechada el 11 de setiembre de 2026. | Documentado |
| 2 | Contrastar arquitectura, repositorio, runtimes y dependencias. | [C4](c4/) y [ADR-001](adr/ADR-001-backend-url-configuration.md) describen la arquitectura observada. Se inspeccionaron manifiestos, Compose y configuración. Falta inventario completo de dependencias transitivas/licencias. | Parcial |
| 3 | Identificar fallos de runtime y definir contratos. | El [documento técnico](DocumentoTecnicoParcial.docx) registra el desajuste del puerto PostgreSQL local, el control no atómico de capacidad/numeración y contratos propuestos para cola, confirmación y configuración. | Diagnóstico documentado; faltan pruebas de reproducción |
| 4 | Añadir validación defensiva y comprobar entradas inválidas. | Se anotaron precondiciones y respuestas esperadas en el documento técnico. No hay evidencia de una revisión completa de validaciones ni de pruebas de entradas inválidas. | Pendiente |
| 5 | Unificar errores, excepciones y logging. | Hay una política propuesta, pero los registros observados siguen usando `print` y no hay evidencia de una política implementada y probada de extremo a extremo. | Pendiente |
| 6 | Corregir capacidad/numeración y demostrar concurrencia. | El servicio usa un bloqueo de fila y existen restricciones únicas, pero el documento técnico detecta que la lectura de capacidad no está dentro de la misma sección crítica. No hay prueba concurrente automatizada. | Pendiente crítico |
| 7 | Verificar recuperación ante fallos y preparar la línea base. | El backend tiene reintentos acotados de conexión a RabbitMQ durante el arranque. No se verificaron fallos durante operación, recuperación de PostgreSQL/Redis ni entrega/idempotencia de eventos. | Parcial; falta evidencia |
| 8 | Presentar `v1.0` parcial funcional, verificable y preparada ante fallos/concurrencia. | Se está consolidando la documentación y la validación inicial. La versión no debe etiquetarse como `v1.0` hasta cerrar el checklist de aceptación de abajo. | En preparación |

## Verificaciones ejecutadas en este checkout

- **Backend:** `python -m compileall -q backend/src backend/run.py` terminó sin
  errores de sintaxis.
- **Infraestructura:** `docker compose -f backend/docker-compose.yml config -q`
  validó la configuración de Compose. PostgreSQL, Redis y RabbitMQ se levantaron
  para el smoke test; el backend creó los turnos diarios y conectó ambos consumers
  RabbitMQ durante el arranque.
- **Backend HTTP:** `GET /ping` devolvió HTTP 200 y `/openapi.json` estuvo
  disponible con los routers registrados.
- **Frontend:** `npm ci` instaló las dependencias del lockfile.
- **Frontend tipos:** `npx tsc --noEmit` pasó después de corregir el contrato de
  notificaciones Expo y una rama condicional inalcanzable para `ATENDIDO`.
- **Frontend lint:** `npm run lint` terminó con **0 errores y 13 advertencias**
  preexistentes en `_layout.tsx`, `home.tsx`, `index.tsx` y `ticket.tsx`.
- **Frontend web:** `npx expo export --platform web` generó las rutas estáticas. Expo
  avisó que la escucha de cambios de tokens push no está soportada en web.
- **Dependencias frontend:** `npm ci` reportó 53 avisos de auditoría (17 moderados,
  35 altos y 1 crítico). No se ejecutó `npm audit fix` porque podría cambiar
  versiones y comportamiento sin una revisión del impacto.
- **Pruebas automatizadas:** no hay casos en `backend/tests/` ni una suite de pruebas
  del frontend. La compilación/lint/exportación no prueban las reglas de negocio.
- **Alcance del smoke test:** confirma arranque, conectividad local y salud HTTP; no
  sustituye pruebas de autenticación, persistencia, reglas de negocio, concurrencia
  o fallos.

## Checklist de cierre para `v1.0`

- [ ] Arranque reproducible desde un clon limpio con instrucciones y ejemplos de
  configuración, sin secretos.
- [ ] Recorrer un flujo de negocio completo de autenticación, solicitud de turno,
  consulta y confirmación/cancelación.
- [ ] Definir y probar contratos para sesión inválida, recurso ausente, duplicado,
  capacidad agotada y transiciones no permitidas.
- [ ] Mover validación de capacidad, reserva y numeración a una operación
  transaccional coherente; conservar la regla de no duplicar turnos.
- [ ] Ejecutar prueba concurrente con capacidad restante de una ración y verificar
  el estado final en PostgreSQL: una sola asignación, cero excesos y cero números
  duplicados.
- [ ] Probar al menos dos fallas/degradaciones apropiadas (por ejemplo, broker no
  disponible y base de datos no disponible) y documentar respuestas/logs observados.
- [ ] Añadir y ejecutar pruebas automatizadas reproducibles para los contratos y
  casos de concurrencia/fallo.
- [ ] Guardar comandos, entorno, resultados, limitaciones y versión parcial
  identificable en Git. No afirmar métricas que no se hayan medido.

## Riesgos que no deben ocultarse en la presentación

1. El Compose publica PostgreSQL en el host `5433`, pero el valor por defecto del
   cliente backend es `5432`; `backend/.env.example` alinea el entorno local.
2. La asignación de capacidad y la numeración aún requieren una frontera
   transaccional y una prueba concurrente.
3. El backend carece de una suite automatizada en el repositorio.
4. Los reintentos de RabbitMQ observados son de arranque; no acreditan entrega
   garantizada o recuperación durante la operación.
5. WebSockets y workers son locales al proceso. No se debe presentar el proyecto
   actual como escalado horizontal.
6. La instalación de dependencias frontend produjo avisos de vulnerabilidades que
   deben revisarse de forma controlada.
