# Frontend de ComedorUNI

Aplicación móvil/web en React Native, Expo Router y TypeScript. La guía completa
para levantar backend y servicios está en el [README principal](../../README.md).

## Requisitos

- Node.js 20 o posterior y npm.
- Backend ComedorUNI disponible en la URL configurada.

## Configuración y ejecución

Desde `frontend/src/`:

```powershell
Copy-Item .env.example .env
npm ci
npm start
```

Para navegador ejecuta `npm run web`. Las URL se configuran mediante
`EXPO_PUBLIC_API_URL` y `EXPO_PUBLIC_WS_URL` en este directorio. Los valores
`localhost` sirven para web y simuladores locales; en emulador Android utiliza
`10.0.2.2`, y en un teléfono físico la IP LAN del equipo que ejecuta el backend.

## Validaciones

```powershell
npx tsc --noEmit
npm run lint
npx expo export --platform web
```

Actualmente no hay suite de pruebas automatizadas del frontend. Lint, chequeo de
tipos y exportación verifican calidad estática y empaquetado, no los flujos
funcionales contra la API.
