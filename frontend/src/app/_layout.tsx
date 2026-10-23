import { Stack, router } from 'expo-router';
export { ErrorBoundary } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import * as SplashScreen from 'expo-splash-screen';
import * as Notifications from 'expo-notifications';
import { useEffect } from 'react';
import { UserProvider } from '../constants/UserContext';
import { initRemoteConfig } from '../constants/api';

SplashScreen.preventAutoHideAsync();

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export default function RootLayout() {
  useEffect(() => {
    const hideSplash = async () => {
      // Resuelve la URL real del backend (Gist -> cache -> fallback) ANTES
      // de mostrar cualquier pantalla, para que ningún WebSocket ni fetch
      // salga con una URL vieja mientras esto todavía está resolviendo.
      await initRemoteConfig();
      await SplashScreen.hideAsync();
    };
    hideSplash();

    // Cuando el usuario toca una notificación con la app cerrada/background
    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as any;
      if (data?.type === 'ping_request' || data?.type === 'llamado') {
        router.push('/ticket');
      }
    });

    return () => sub.remove();
  }, []);

  return (
    <UserProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="home" />
        <Stack.Screen name="ticket" />
        <Stack.Screen name="denied" />
        <Stack.Screen name="registered" />
      </Stack>
      <StatusBar style="dark" />
    </UserProvider>
  );
}
