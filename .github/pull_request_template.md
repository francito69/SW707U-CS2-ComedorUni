## 📌 Resumen del Pull Request

<!-- Describe de forma concisa el objetivo de los cambios introducidos en esta solicitud. -->

- **Rama origen:** 
- **Rama destino:** `main`
- **Hito asociado:** Examen Parcial / Entrega Final (Línea Base)
- **Tipo de cambio:**
  - [ ] Nueva funcionalidad (`feat`)
  - [ ] Corrección de error (`fix`)
  - [ ] Refactorización arquitectónica (`refactor`)
  - [ ] Documentación técnica (`docs`)
  - [ ] Pruebas y benchmarks (`test`)
  - [ ] Configuración / Despliegue (`chore` / `ci`)

---

## 🏛️ Motivación y Alineamiento Arquitectónico

<!-- Explica la justificación técnica de la solución adoptada y cómo cumple con los requerimientos de la asignatura SW707 y los modelos arquitectónicos. -->

---

## 📦 Componentes y Módulos Afectados

<!-- Detalla los módulos modificados (Backend, Frontend, Base de Datos, Infraestructura, Docs). -->
- [ ] Backend FastAPI (`src/`)
- [ ] Frontend React Native / Expo (`frontend/`)
- [ ] Base de Datos PostgreSQL (`config/`, migraciones)
- [ ] Broker RabbitMQ / Redis (`src/shared/`)
- [ ] Documentación / Modelos C4 / 4+1 (`docs/`)
- [ ] Pruebas automatizadas (`tests/`, `benchmarks/`)

---

## 🧪 Evidencias de Pruebas y Verificación

<!-- Lista los comandos ejecutados localmente y los resultados obtenidos. -->
```powershell
# Suite de pruebas automatizadas
python -m pytest tests

# Compilación y sintaxis
python -m compileall -q src run.py tests scripts benchmarks

# Tipado de Frontend
cd frontend/src ; npx tsc --noEmit
```

- **Resultado de pruebas:** `76 passed`
- **Pruebas de concurrencia:** Ejecutadas y verificadas contra PostgreSQL real.
- **Auditoría de dependencias:** Sin vulnerabilidades críticas (`pip-audit`).

---

## ✅ Checklist de Rúbrica y Calidad

- [ ] Código modular y sin dependencias circulares.
- [ ] Validación defensiva en la frontera (entradas sanitizadas, esquemas Pydantic).
- [ ] Manejo transaccional atómico ante concurrencia (`SELECT ... FOR UPDATE`).
- [ ] Errores tipados con catálogo de dominio y sin filtración de detalles sensibles.
- [ ] Documentación técnica y diagramas actualizados en `docs/`.
- [ ] Historial de cambios registrado en `CHANGELOG.md`.
