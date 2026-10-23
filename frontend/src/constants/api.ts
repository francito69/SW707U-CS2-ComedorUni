import * as SecureStore from "expo-secure-store";

const FALLBACK_API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
const FALLBACK_WS_URL  = process.env.EXPO_PUBLIC_WS_URL ?? "ws://localhost:8000";

// URL fija (nunca cambia) de un Gist de GitHub con la URL ACTUAL del túnel
// de Cloudflare en texto plano. Reemplaza esto por el "raw" del tuyo — ver
// backend/scripts/publish_tunnel_url.ps1 para cómo se actualiza sola.
// Así, cuando el túnel cambia de URL, solo editás el Gist (10s) en vez de
// recompilar la app: initRemoteConfig() la relee cada vez que la app arranca.
const REMOTE_CONFIG_URL =
  "https://gist.githubusercontent.com/Y2605/40ed787a81026b1792e11b6879b238b6/raw/backend_url.txt";

const CACHE_KEY = "cached_backend_base_url";

// `let`, no `const`: initRemoteConfig() reasigna estos valores en runtime, y
// como son ES module live bindings, cualquier archivo que los importe ve el
// valor actualizado en su próximo uso — sin tener que tocar cada callsite.
export let API_URL = FALLBACK_API_URL.replace(/\/$/, "");
export let WS_URL  = FALLBACK_WS_URL.replace(/\/$/, "");

function applyBaseUrl(rawUrl: string): boolean {
  const clean = rawUrl.trim().replace(/\/$/, "");
  if (!clean || !/^https?:\/\//.test(clean)) return false;
  API_URL = clean;
  WS_URL = clean.replace(/^http/, "ws");
  return true;
}

/**
 * Se llama una vez al arrancar la app (ver app/_layout.tsx), ANTES de que
 * cualquier pantalla se monte — así ningún WebSocket ni fetch alcanza a
 * salir con la URL vieja mientras esto resuelve.
 *
 * Orden: 1) lo último cacheado (rápido, funciona sin internet),
 *        2) lo que diga el Gist ahora mismo (se vuelve a cachear si cambió).
 * Si ambos fallan, se queda con el fallback de compilación (EXPO_PUBLIC_*).
 */
export async function initRemoteConfig(): Promise<void> {
  try {
    const cached = await SecureStore.getItemAsync(CACHE_KEY);
    if (cached) applyBaseUrl(cached);
  } catch {}

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);
    const res = await fetch(`${REMOTE_CONFIG_URL}?t=${Date.now()}`, {
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (res.ok) {
      const text = await res.text();
      if (applyBaseUrl(text)) {
        await SecureStore.setItemAsync(CACHE_KEY, text.trim());
      }
    }
  } catch {
    // Sin internet o el Gist no respondió a tiempo: se queda con lo cacheado.
  }
}

// Solo se usa cuando el backend se expone por un túnel temporal como ngrok
// (no aplica a Cloudflare Tunnel, que no necesita este header).
export const NGROK_HEADERS = {
  "Content-Type": "application/json",
  ...(API_URL.includes("ngrok") || WS_URL.includes("ngrok")
    ? { "ngrok-skip-browser-warning": "true" }
    : {}),
};
