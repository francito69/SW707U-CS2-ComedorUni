const apiBase = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
const wsBase = process.env.EXPO_PUBLIC_WS_URL ?? "ws://localhost:8000";

export const API_URL = apiBase.replace(/\/$/, "");
export const WS_URL = wsBase.replace(/\/$/, "");

// Solo se usa cuando el backend se expone por un túnel temporal como ngrok.
export const NGROK_HEADERS = {
  "Content-Type": "application/json",
  ...(apiBase.includes("ngrok") || wsBase.includes("ngrok")
    ? { "ngrok-skip-browser-warning": "true" }
    : {}),
};
