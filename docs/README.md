# Documentación Oficial de ComedorUNI — SW707

Este directorio contiene los entregables técnicos y de presentación para la **Etapa I (Examen Parcial — v1.0)** del curso **Construcción de Software II (SW707 - 2026-II)** de la Universidad Nacional de Ingeniería (UNI).

---

## 1. Entregable Técnico Principal

- 📄 **[Documento Técnico del Examen Parcial (Markdown)](DocumentoTecnicoParcial.md)**  
  Documento técnico oficial y completo para la entrega de la Etapa I. Cumple al 100% con los 11 puntos de la guía y los 9 criterios de la rúbrica oficial (100% de la calificación):
  1. Descripción del problema y usuarios.
  2. Alcance y requisitos principales.
  3. Arquitectura y decisiones técnicas.
  4. Gestión de dependencias y reúso (10%).
  5. Análisis de problemas de runtime (10%).
  6. Design by Contract (15%) y Programación defensiva (10%).
  7. Estrategia de errores y excepciones (15%).
  8. Concurrencia y condiciones de carrera (15%).
  9. Tolerancia a fallas y resiliencia (15%).
  10. Pruebas automatizadas y evidencias (5%).
  11. Limitaciones y evolución hacia el Examen Final (v2.0).

---

## 2. Preparación de la Defensa y Exposición Técnica

- 🗣️ **[Guion para Exposición Técnica de 40 Minutos](guion-exposicion-sw707.md)**  
  Estructura de sustentación minuto a minuto (35 min de exposición + 5 min de preguntas y defensa), con recorrido detallado a nivel de código fuente en frontend y backend.
- 🎨 **[Prompts Maestros para Figma Make](prompts-figma-make.md)**  
  Guía y prompts de ingeniería de interfaz con especificación completa de tokens (colores institucionales UNI, tipografía, radios, estados), pantallas del flujo de estudiante y micro-interacciones interactivas.
- 📈 **[Avance Semanal hasta el Parcial](avance-parcial-sw707.md)**  
  Bitácora de avance semanal (semanas 1 a 8), checklist de cierre de la línea base v1.0 y resumen de validaciones de compilación, linters y tests.

---

## 3. Arquitectura y Modelado de Software

- 🏛️ **[Modelo C4 en 4 Niveles](c4/README.md)**  
  Documentación gráfica y técnica completa en cuatro niveles: Contexto del Sistema (Nivel 1), Contenedores de Infraestructura (Nivel 2), Componentes por Módulo M1 a M7 y Consolidado (Nivel 3), y Despliegue / Código (Nivel 4).
- 📐 **[Modelo de Vistas Arquitectónicas 4+1 de Kruchten](arquitectura-4plus1.md)**  
  Articulación integral entre Vista Lógica (Dominio), Vista de Procesos (Concurrencia y WebSockets), Vista de Desarrollo (Estructura Sección 16 y Contratos DbC), Vista Física (Multi-worker Uvicorn y puertos) y Vista de Escenarios (+1).
- 📑 **[Registro de Decisiones de Arquitectura (ADRs)](adr/)**  
  Decisiones de configuración de URLs, sesión y persistencia.

---

## 4. Especificación del Sistema

- 📋 **[Ficha del Sistema](ficha-del-sistema.md)**  
  Identificación del dominio, reglas de negocio esenciales, stack tecnológico y delimitación del alcance.
- 🎯 **[Escenarios de Calidad](escenarios.md)**  
  Definición de atributos de calidad para disponibilidad, latencia, integridad y concurrencia.
