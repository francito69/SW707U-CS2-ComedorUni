import { Ionicons, MaterialCommunityIcons } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";
import { LinearGradient } from "expo-linear-gradient";
import * as Notifications from "expo-notifications";
import { router } from "expo-router";
import * as SecureStore from "expo-secure-store";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  Image,
  Modal,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { ScrollView } from "react-native";
import { WebView } from "react-native-webview";
import { Colors } from "../constants/theme";
import { useUser } from "../constants/UserContext";

import { API_URL, NGROK_HEADERS } from "../constants/api";
const { height } = Dimensions.get("window");

export default function LoginScreen() {
  const { setUser } = useUser();
  const [checking, setChecking] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const sid = await SecureStore.getItemAsync("sid");
        if (sid) {
          const res = await fetch(`${API_URL}/me?sid=${sid}`, { headers: NGROK_HEADERS });
          if (res.ok) {
            const data = await res.json();
            // Restaurar cola activa si existe
            let queue = null;
            try {
              const qRes = await fetch(`${API_URL}/queue/status?sid=${sid}`, { headers: NGROK_HEADERS });
              if (qRes.ok) {
                const qData = await qRes.json();
                queue = {
                  numero_turno: qData.numero_turno,
                  tipo:         qData.tipo,
                  posicion:     qData.posicion,
                  estado:       qData.estado,
                };
              }
            } catch {}
            setUser({ ...data, queue });
            registerPushToken(sid);
            const hasActiveQueue = queue &&
              queue.estado !== "CANCELADO" &&
              queue.estado !== "ATENDIDO";
            router.replace(hasActiveQueue ? "/ticket" : "/home");
            return;
          } else {
            await SecureStore.deleteItemAsync("sid");
          }
        }
      } catch {}
      setChecking(false);
    };
    checkSession();
  }, []);
  const [webViewActive, setWebViewActive] = useState(false);
  const [syncStatus, setSyncStatus] = useState<
    "none" | "pending_biometric" | "verified"
  >("none");
  const [totalCredits, setTotalCredits] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<{
    sid: string;
    codigo: string;
    nombre: string;
    email: string;
    creditos_llevados: number;
  } | null>(null);
  const [webViewKey, setWebViewKey] = useState(0);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [sessionConflict, setSessionConflict] = useState(false);
  const [showTakeoverModal, setShowTakeoverModal] = useState(false);
  const [resolvingSession, setResolvingSession] = useState(false);

  const webViewRef = useRef<WebView>(null);

  const LOGIN_URL = "https://alumnos.uni.edu.pe/redirect-google";

  const runScraperScript = `
    (async function() {
      try {
        console.log('[*] Empezando scraping interno...');
        const resHome = await fetch('https://alumnos.uni.edu.pe/home');
        const htmlHome = await resHome.text();
        console.log('[*] Home HTML obtenido, longitud:', htmlHome.length);

        const resCursos = await fetch('https://alumnos.uni.edu.pe/informacion-academica/cursos');
        const htmlCursos = await resCursos.text();
        console.log('[*] Cursos HTML obtenido, longitud:', htmlCursos.length);

        const resDatos = await fetch('https://alumnos.uni.edu.pe/configuracion/datos-personales');
        const htmlDatos = await resDatos.text();
        console.log('[*] Datos personales HTML obtenido, longitud:', htmlDatos.length);

        window.ReactNativeWebView.postMessage(JSON.stringify({
          type: 'SCRAPED_DATA',
          home_html: htmlHome,
          cursos_html: htmlCursos,
          datos_html: htmlDatos
        }));
      } catch (e) {
        console.log('[!] Error en scraping:', e.message);
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'ERROR', error: e.message }));
      }
    })();
    true;
  `;

  const onMessage = async (event: any) => {
    try {
      const raw = event.nativeEvent.data;
      if (!raw || !raw.startsWith("{")) return;
      const response = JSON.parse(raw);
      console.log("[*] Mensaje recibido del WebView:", response.type);

      if (response.type === "SCRAPED_DATA") {
        console.log("[*] Enviando datos al backend para procesar...");
        const deviceId = await getDeviceId();
        const res = await fetch(`${API_URL}/parse-data`, {
          method: "POST",
          headers: NGROK_HEADERS,
          body: JSON.stringify({
            home_html: response.home_html,
            cursos_html: response.cursos_html,
            datos_html: response.datos_html,
            device_id: deviceId,
          }),
        });

        const result = await res.json();
        console.log("[*] Respuesta del backend:", result);

        if (result.sid && result.creditos_llevados !== undefined) {
          setSessionId(result.sid);
          setTotalCredits(result.creditos_llevados);
          setSessionData({
            sid: result.sid,
            codigo: result.codigo,
            nombre: result.nombre,
            email: result.email,
            creditos_llevados: result.creditos_llevados,
          });
          setSessionConflict(!!result.session_conflict);
          setSyncStatus("pending_biometric");
        } else {
          console.log("[!] Respuesta inesperada del backend:", result);
        }
        setLoading(false);
      } else if (response.type === "ERROR") {
        console.log("[!] Error recibido del WebView:", response.error);
        setLoading(false);
        setWebViewActive(false);
        Alert.alert("Portal UNI", "Ocurrió un error al sincronizar.");
      }
    } catch (e) {
      console.error("[!] Error en onMessage processing:", e);
    }
  };

  const handleNavigationStateChange = (navState: any) => {
    console.log("[*] WebView URL cambiada:", navState.url);
    if (navState.url.includes("/home") && !loading && syncStatus === "none") {
      console.log("[*] Detectado /home, inyectando script de scraping...");
      setWebViewActive(false);
      setLoading(true);
      webViewRef.current?.injectJavaScript(runScraperScript);
    }
  };

  const startLogin = () => {
    setWebViewKey((prev) => prev + 1);
    setSyncStatus("none");
    setCapturedPhoto(null);
    setWebViewActive(true);
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Alert.alert(
        "Permiso denegado",
        "Necesitamos acceso a la cámara para verificar tu identidad.",
      );
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      base64: true,
      quality: 0.7,
      cameraType: ImagePicker.CameraType.front,
      allowsEditing: true,
      aspect: [1, 1],
    });
    if (!result.canceled && result.assets[0]?.base64) {
      setCapturedPhoto(result.assets[0].base64);
    }
  };

  const getDeviceId = async (): Promise<string> => {
    let id = await SecureStore.getItemAsync("device_id");
    if (!id) {
      id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      await SecureStore.setItemAsync("device_id", id);
    }
    return id;
  };

  // Finaliza el login: guarda la sesión y entra a la app
  const finalizeLogin = async (data: NonNullable<typeof sessionData>) => {
    await SecureStore.setItemAsync("sid", data.sid);
    setUser({ ...data, queue: null });
    await registerPushToken(data.sid);
    router.replace("/home");
  };

  // "Continuar aquí": toma la sesión y expulsa al otro dispositivo
  const handleTakeover = async () => {
    if (!sessionData) return;
    setResolvingSession(true);
    try {
      await fetch(`${API_URL}/session/takeover`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid: sessionData.sid }),
      });
      setShowTakeoverModal(false);
      await finalizeLogin(sessionData);
    } catch {
      Alert.alert("Error", "No se pudo tomar la sesión. Intenta de nuevo.");
    } finally {
      setResolvingSession(false);
    }
  };

  // "Mantener la otra": descarta este login, la sesión del otro dispositivo sigue
  const handleKeepOther = async () => {
    if (!sessionData) return;
    setResolvingSession(true);
    try {
      await fetch(`${API_URL}/logout`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid: sessionData.sid }),
      });
    } catch {}
    setShowTakeoverModal(false);
    setResolvingSession(false);
    setSessionId(null);
    setSessionData(null);
    setSessionConflict(false);
    setSyncStatus("none");
    setCapturedPhoto(null);
    Alert.alert("Sesión conservada", "Se mantuvo la sesión activa en el otro dispositivo.");
  };

  const registerPushToken = async (sid: string) => {
    try {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== "granted") {
        console.warn("[!] Permiso de notificaciones denegado");
        return;
      }
      const tokenData = await Notifications.getExpoPushTokenAsync();
      const res = await fetch(`${API_URL}/queue/register-push-token`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid, push_token: tokenData.data }),
      });
      if (!res.ok) console.warn("[!] Backend rechazó el push token:", await res.text());
      else console.log("[*] Push token registrado:", tokenData.data);
    } catch (e) {
      console.warn("[!] No se pudo registrar push token:", e);
    }
  };

  const verifyBiometric = async () => {
    if (!capturedPhoto || !sessionId) return;
    setVerifying(true);
    try {
      const res = await fetch(`${API_URL}/verify-biometric`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid: sessionId, photo_base64: capturedPhoto }),
      });
      const result = await res.json();
      console.log("[*] Resultado biométrico:", result);

      if (result.verified && sessionData) {
        if (sessionConflict) {
          // Identidad verificada; hay sesión activa en otro dispositivo → decidir
          setShowTakeoverModal(true);
        } else {
          await finalizeLogin(sessionData);
        }
      } else {
        Alert.alert(
          "Verificación fallida",
          "La foto no coincide con tu registro.\nIntenta de nuevo con mejor iluminación.",
        );
        setCapturedPhoto(null);
      }
    } catch (e) {
      Alert.alert(
        "Error",
        "No se pudo verificar la identidad. Intenta de nuevo.",
      );
      setCapturedPhoto(null);
    } finally {
      setVerifying(false);
    }
  };

  const logout = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_URL}/logout`, {
          method: "POST",
          headers: NGROK_HEADERS,
          body: JSON.stringify({ sid: sessionId }),
        });
      } catch (e) {
        console.warn("[!] Error al notificar logout al backend:", e);
      }
    }
    setSessionId(null);
    setSyncStatus("none");
    setTotalCredits(null);
    setCapturedPhoto(null);
  };

  if (checking) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: Colors.light.maroon,
        }}
      >
        <ActivityIndicator size="large" color="white" />
      </View>
    );
  }

  // ── Pantalla de verificación biométrica ──────────────────────────────────────
  if (syncStatus === "pending_biometric") {
    return (
      <View style={styles.biometricContainer}>
        <MaterialCommunityIcons
          name="camera-account"
          size={60}
          color={Colors.light.maroon}
        />
        <Text style={styles.biometricTitle}>Verificación biométrica</Text>
        <Text style={styles.biometricSubtitle}>
          {capturedPhoto
            ? "Confirma que la foto es clara y muestra tu rostro."
            : "Toma una selfie para verificar tu identidad antes de continuar."}
        </Text>

        {capturedPhoto ? (
          <>
            <Image
              source={{ uri: `data:image/jpeg;base64,${capturedPhoto}` }}
              style={styles.previewImage}
            />
            {verifying ? (
              <View style={{ marginTop: 20, alignItems: "center" }}>
                <ActivityIndicator size="large" color={Colors.light.maroon} />
                <Text
                  style={{
                    marginTop: 12,
                    color: Colors.light.gray,
                    fontWeight: "600",
                  }}
                >
                  Verificando identidad...
                </Text>
              </View>
            ) : (
              <View style={{ width: "100%", marginTop: 20, gap: 12 }}>
                <TouchableOpacity
                  style={styles.primaryBtn}
                  onPress={verifyBiometric}
                >
                  <Text style={styles.primaryBtnText}>
                    Confirmar y verificar
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.secondaryBtn}
                  onPress={() => setCapturedPhoto(null)}
                >
                  <Text style={styles.secondaryBtnText}>Tomar otra foto</Text>
                </TouchableOpacity>
              </View>
            )}
          </>
        ) : (
          <TouchableOpacity
            style={[styles.primaryBtn, { marginTop: 24 }]}
            onPress={takePhoto}
          >
            <MaterialCommunityIcons name="camera" size={22} color="white" />
            <Text style={[styles.primaryBtnText, { marginLeft: 10 }]}>
              Tomar selfie
            </Text>
          </TouchableOpacity>
        )}

        <Modal
          visible={showTakeoverModal}
          transparent
          animationType="fade"
          onRequestClose={handleKeepOther}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalCard}>
              <View style={styles.modalIconWrap}>
                <MaterialCommunityIcons name="devices" size={34} color={Colors.light.maroon} />
              </View>
              <Text style={styles.modalTitle}>Sesión activa en otro dispositivo</Text>
              <Text style={styles.modalText}>
                Ya tienes una sesión abierta con esta cuenta en otro dispositivo.
                ¿Qué deseas hacer?
              </Text>

              {resolvingSession ? (
                <ActivityIndicator
                  size="large"
                  color={Colors.light.maroon}
                  style={{ marginVertical: 24 }}
                />
              ) : (
                <View style={{ width: "100%", marginTop: 20, gap: 12 }}>
                  <TouchableOpacity style={styles.primaryBtn} onPress={handleTakeover}>
                    <MaterialCommunityIcons name="cellphone-check" size={20} color="white" />
                    <Text style={[styles.primaryBtnText, { marginLeft: 10 }]}>
                      Continuar aquí
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.secondaryBtn} onPress={handleKeepOther}>
                    <Text style={styles.secondaryBtnText}>Mantener la otra sesión</Text>
                  </TouchableOpacity>
                </View>
              )}

              <Text style={styles.modalHint}>
                &quot;Continuar aquí&quot; cerrará la sesión del otro dispositivo al instante.
              </Text>
            </View>
          </View>
        </Modal>
      </View>
    );
  }

  // ── Pantalla principal ───────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1 }}>
      <ScrollView style={sc.mainContainer} bounces={false} showsVerticalScrollIndicator={false}>
        <StatusBar barStyle="light-content" />
        <LinearGradient
          colors={[Colors.light.maroon, Colors.light.maroonLight]}
          style={{ width: "100%" }}
        >
          <View style={sc.headerContent}>
            <View style={sc.logoWrapper}>
              <Image
                source={require("../assets/images/UNI.png")}
                style={{
                  width: 80,
                  height: 80,
                  resizeMode: "contain",
                  tintColor: "white",
                }}
              />
            </View>
          </View>
        </LinearGradient>

        <View style={sc.contentCard}>
          <Text style={sc.title}>COMEDOR UNIVERSITARIO</Text>
          <Text style={sc.subtitle}>VERIFICACIÓN ACADÉMICA</Text>

          {loading ? (
            <View style={{ marginTop: 40, alignItems: "center" }}>
              <ActivityIndicator size="large" color={Colors.light.maroon} />
              <Text
                style={{
                  marginTop: 20,
                  color: Colors.light.gray,
                  fontWeight: "600",
                }}
              >
                Sincronizando datos...
              </Text>
            </View>
          ) : syncStatus === "none" ? (
            <>
              <Text style={sc.description}>
                Ingresa al portal de Alumnos UNI para verificar tus créditos y
                elegibilidad.
              </Text>
              <TouchableOpacity style={sc.syncButton} onPress={startLogin}>
                <Ionicons name="logo-google" size={20} color="white" />
                <Text style={sc.syncButtonText}>Continuar con Google</Text>
              </TouchableOpacity>
            </>
          ) : (
            <>
              <View style={sc.syncCard}>
                <MaterialCommunityIcons
                  name="star-circle"
                  size={40}
                  color="white"
                />
                <Text
                  style={{
                    color: "rgba(255,255,255,0.8)",
                    fontSize: 14,
                    fontWeight: "700",
                    marginTop: 10,
                  }}
                >
                  CRÉDITOS LLEVADOS
                </Text>
                <Text style={sc.creditValue}>{totalCredits}</Text>
              </View>

              <TouchableOpacity
                onPress={() => {
                  logout();
                }}
                style={{
                  marginTop: 30,
                  flexDirection: "row",
                  alignItems: "center",
                }}
              >
                <MaterialCommunityIcons
                  name="logout"
                  size={20}
                  color={Colors.light.maroon}
                />
                <Text
                  style={{
                    color: Colors.light.maroon,
                    fontWeight: "700",
                    marginLeft: 8,
                  }}
                >
                  Cerrar Sesión
                </Text>
              </TouchableOpacity>
            </>
          )}

          <View style={{ marginTop: 40, alignItems: "center" }}>
            <Text style={{ fontSize: 11, color: Colors.light.gray }}>
              VRAD - UNI 2024
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* WebView con incognito={true} y KEY dinámica para forzar reset */}
      <View
        style={[
          styles.webViewLayer,
          {
            zIndex: webViewActive ? 1000 : -1,
            opacity: webViewActive ? 1 : 0,
            transform: [{ translateY: webViewActive ? 0 : height }],
          },
        ]}
      >
        <View style={styles.webViewHeader}>
          <TouchableOpacity onPress={() => setWebViewActive(false)}>
            <Ionicons name="close" size={30} color={Colors.light.text} />
          </TouchableOpacity>
          <Text style={styles.webViewTitle}>Portal Alumnos UNI</Text>
          <View style={{ width: 30 }} />
        </View>
        <WebView
          key={webViewKey}
          ref={webViewRef}
          source={{ uri: LOGIN_URL }}
          onNavigationStateChange={handleNavigationStateChange}
          onMessage={onMessage}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
          incognito={true}
          style={{ flex: 1 }}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  webViewLayer: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "#fff",
    paddingTop: Platform.OS === "ios" ? 40 : 0,
  },
  webViewHeader: {
    height: 60,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 15,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
    backgroundColor: "#fff",
  },
  webViewTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.light.text,
  },
  biometricContainer: {
    flex: 1,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
    padding: 30,
  },
  biometricTitle: {
    fontSize: 22,
    fontWeight: "900",
    marginTop: 20,
    textAlign: "center",
  },
  biometricSubtitle: {
    fontSize: 14,
    color: "#666",
    textAlign: "center",
    marginTop: 10,
    marginBottom: 24,
    lineHeight: 20,
  },
  camera: {
    width: 260,
    height: 320,
    borderRadius: 20,
    overflow: "hidden",
  },
  previewImage: {
    width: 260,
    height: 320,
    borderRadius: 20,
  },
  primaryBtn: {
    backgroundColor: Colors.light.maroon,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    borderRadius: 14,
    width: "100%",
  },
  primaryBtnText: {
    color: "white",
    fontWeight: "700",
    fontSize: 16,
  },
  secondaryBtn: {
    borderWidth: 1.5,
    borderColor: Colors.light.maroon,
    padding: 14,
    borderRadius: 14,
    width: "100%",
    alignItems: "center",
  },
  secondaryBtnText: {
    color: Colors.light.maroon,
    fontWeight: "700",
    fontSize: 15,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.55)",
    alignItems: "center",
    justifyContent: "center",
    padding: 28,
  },
  modalCard: {
    backgroundColor: "white",
    borderRadius: 24,
    padding: 28,
    width: "100%",
    maxWidth: 380,
    alignItems: "center",
    elevation: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
  },
  modalIconWrap: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: "rgba(128,0,32,0.08)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 14,
  },
  modalTitle: {
    fontSize: 19,
    fontWeight: "800",
    color: Colors.light.maroon,
    textAlign: "center",
  },
  modalText: {
    marginTop: 10,
    fontSize: 15,
    lineHeight: 21,
    color: Colors.light.gray,
    textAlign: "center",
  },
  modalHint: {
    marginTop: 16,
    fontSize: 12.5,
    color: Colors.light.gray,
    textAlign: "center",
    opacity: 0.8,
  },
});

const sc = StyleSheet.create({
  mainContainer: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  headerContent: {
    height: height * 0.4,
    alignItems: "center",
    justifyContent: "center",
  },
  contentCard: {
    backgroundColor: "white",
    borderTopLeftRadius: 40,
    borderTopRightRadius: 40,
    marginTop: -40,
    padding: 40,
    paddingHorizontal: 30,
    alignItems: "center",
    minHeight: height * 0.6,
    elevation: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
  },
  logoWrapper: {
    width: 120,
    height: 120,
    backgroundColor: "rgba(255, 255, 255, 0.2)",
    borderRadius: 60,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.3)",
  },
  title: {
    fontSize: 24,
    fontWeight: "900",
    color: Colors.light.text,
    textAlign: "center",
    marginTop: 20,
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.light.maroon,
    textAlign: "center",
    marginTop: 8,
    letterSpacing: 2,
    opacity: 0.8,
  },
  description: {
    fontSize: 15,
    color: Colors.light.gray,
    textAlign: "center",
    marginTop: 20,
    lineHeight: 22,
    paddingHorizontal: 10,
  },
  syncButton: {
    backgroundColor: Colors.light.maroon,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    paddingHorizontal: 20,
    borderRadius: 16,
    marginTop: 30,
    width: "100%",
    elevation: 4,
  },
  syncButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "700",
    marginLeft: 12,
  },
  syncCard: {
    width: "100%",
    backgroundColor: Colors.light.maroon,
    borderRadius: 20,
    padding: 25,
    marginTop: 30,
    alignItems: "center",
  },
  creditValue: {
    fontSize: 50,
    fontWeight: "900",
    color: "white",
    marginVertical: 10,
  },
});

