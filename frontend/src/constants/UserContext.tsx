import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { Alert } from 'react-native';
import { router } from 'expo-router';
import * as SecureStore from 'expo-secure-store';
import { WS_URL } from './api';

export interface QueueInfo {
  numero_turno: number;           // posición de llegada
  tipo: string;
  posicion: number;
  estado: 'ESPERANDO' | 'LLAMADO' | 'ATENDIDO' | 'CANCELADO';
  turno_asignado?: number;        // turno grupo (solo disponible tras ATENDIDO)
  raciones_restantes?: number;
}

export interface UserData {
  sid: string;
  codigo: string;
  nombre: string;
  email: string;
  creditos_llevados: number;
  queue: QueueInfo | null;
}

interface UserContextType {
  user: UserData | null;
  setUser: (user: UserData | null) => void;
  setQueue: (queue: QueueInfo | null) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<UserData | null>(null);

  const setUser = (u: UserData | null) => setUserState(u);

  const setQueue = (queue: QueueInfo | null) => {
    setUserState(prev => prev ? { ...prev, queue } : prev);
  };

  // ── Conexión de sesión permanente ──────────────────────────────────────────
  // Mientras haya sesión (user.sid), este dispositivo mantiene un WebSocket con
  // el backend. Si otro dispositivo toma la sesión, aquí llega `session_revoked`
  // y se cierra la sesión al instante desde cualquier pantalla.
  const sid = user?.sid ?? null;

  useEffect(() => {
    if (!sid) return;

    let ws: WebSocket | null = null;
    let ping: ReturnType<typeof setInterval> | null = null;
    let reconnect: ReturnType<typeof setTimeout> | null = null;
    let revoked = false;
    let closedByCleanup = false;

    const clearTimers = () => {
      if (ping) { clearInterval(ping); ping = null; }
      if (reconnect) { clearTimeout(reconnect); reconnect = null; }
    };

    const handleRevoked = async (mensaje?: string) => {
      revoked = true;
      clearTimers();
      try { ws?.close(); } catch {}
      try { await SecureStore.deleteItemAsync('sid'); } catch {}
      setUserState(null);
      Alert.alert(
        'Sesión cerrada',
        mensaje || 'Tu sesión se cerró porque iniciaste en otro dispositivo.',
      );
      router.replace('/');
    };

    const connect = () => {
      const socket = new WebSocket(`${WS_URL}/session/ws/${sid}`);
      ws = socket;

      socket.onopen = () => {
        // heartbeat para mantener viva la conexión a través del proxy
        ping = setInterval(() => {
          try { socket.send(JSON.stringify({ type: 'ping' })); } catch {}
        }, 150_000);
      };

      socket.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'session_revoked') handleRevoked(msg.mensaje);
        } catch {}
      };

      socket.onclose = (ev: any) => {
        clearTimers();
        if (revoked || closedByCleanup) return;
        // 4001 = sesión inválida en el servidor, 4002 = revocada → cerrar sesión local
        if (ev?.code === 4001 || ev?.code === 4002) {
          handleRevoked();
          return;
        }
        // caída por red → reconectar
        reconnect = setTimeout(connect, 3000);
      };

      socket.onerror = () => { try { socket.close(); } catch {} };
    };

    connect();

    return () => {
      closedByCleanup = true;
      clearTimers();
      try { ws?.close(); } catch {}
    };
  }, [sid]);

  return (
    <UserContext.Provider value={{ user, setUser, setQueue }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUser must be used within a UserProvider');
  return ctx;
}
