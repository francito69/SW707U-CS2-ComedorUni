# ADR-001 — Configuración del backend del frontend mediante variables de entorno

- Estado: Aceptado
- Fecha: 2026-09-20

## Contexto

El frontend tenía la URL del backend hardcodeada en `frontend/src/constants/api.ts` usando un dominio de ngrok. Ese valor era útil para pruebas temporales, pero quedaba fijo en el código y no podía cambiarse sin editar el código fuente.

Esto generaba varios problemas:

- el proyecto no era portable entre entornos locales, de pruebas y producción
- la URL quedaba acoplada a un túnel temporal y podía romperse sin aviso
- la configuración operativa dependía del desarrollador que editaba la misma línea manualmente
- la documentación de arquitectura ya lo había identificado como un punto pendiente

## Decisión

Se elimina la URL fija del backend del código fuente y se resuelve en tiempo de ejecución con variables de entorno de Expo:

- `EXPO_PUBLIC_API_URL`
- `EXPO_PUBLIC_WS_URL`

La constante del frontend usa esos valores con un fallback seguro a `localhost` para desarrollo local. Cuando la URL apunta a ngrok, solo entonces se agrega el header `ngrok-skip-browser-warning`.

## Consecuencias

### Positivas

- el frontend funciona sin tocar código para cambiar de entorno
- es fácil alternar entre local, túnel temporal y entorno real
- se evita depender de un dominio de ngrok fijo en la base del repo
- la decisión queda explícita y documentada como elección de configuración operativa

### Negativas

- cada entorno necesita un `.env` válido
- si el equipo olvida configurar la variable, el sistema usa `localhost` por defecto

## Implementación

Archivo de configuración recomendado para Expo:

- `frontend/src/.env.example`
- copia ese archivo a `frontend/src/.env` para usarlo en local

Variables utilizadas por el frontend:

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_WS_URL=ws://localhost:8000
```

> Convención única: el archivo `.env` del frontend live en `frontend/src/.env`. No se usa un `.env` en la raíz del repositorio para la app Expo.

## Justificación final

La URL del backend no es una pieza del modelo de dominio ni de la arquitectura del sistema; es una configuración dinámica de entorno. Por eso la decisión se documenta como ADR y no como un componente de la arquitectura C4.
