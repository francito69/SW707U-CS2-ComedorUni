import { Ionicons, MaterialCommunityIcons } from "@expo/vector-icons";
import * as SecureStore from "expo-secure-store";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Colors } from "../constants/theme";
import { useUser } from "../constants/UserContext";

import { API_URL, NGROK_HEADERS } from "../constants/api";
const { height } = Dimensions.get("window");

const MEAL_ICONS: Record<string, any> = {
  DESAYUNO: "coffee",
  ALMUERZO: "food",
  CENA:     "moon-waning-crescent",
};

interface Plato { id: number; nombre: string; }
interface Comida {
  id: number; tipo_comida: string;
  energia_kcal: number | null; lipidos_g: number | null;
  proteinas_g: number | null; carbohidratos_g: number | null;
  platos: Plato[];
}
interface MenuDia { fecha: string; comidas: Comida[]; }

export default function HomeScreen() {
  const { user, setUser, setQueue } = useUser();
  const [menu, setMenu] = useState<MenuDia | null>(null);
  const [menuLoading, setMenuLoading] = useState(true);
  const [joiningQueue, setJoiningQueue] = useState(false);
  const [expandedMeal, setExpandedMeal] = useState<string | null>("ALMUERZO");
  const [activeService, setActiveService] = useState<{ tipo: string } | null>(null);

  useEffect(() => {
    fetchMenu();
    fetchActiveService();
    syncQueue();
  }, []);

  const syncQueue = async () => {
    if (!user?.sid) return;
    try {
      const res = await fetch(`${API_URL}/queue/status?sid=${user.sid}`, { headers: NGROK_HEADERS });
      if (res.ok) {
        const data = await res.json();
        setQueue({
          numero_turno:   data.numero_turno,
          tipo:           data.tipo,
          posicion:       data.posicion,
          estado:         data.estado,
          turno_asignado: data.turno_asignado ?? undefined,
        });
      } else {
        setQueue(null);
      }
    } catch {}
  };

  const fetchActiveService = async () => {
    try {
      const res = await fetch(`${API_URL}/queue/active-service`, { headers: NGROK_HEADERS });
      if (res.ok) {
        const data = await res.json();
        if (data.activo && data.turnos?.length) setActiveService({ tipo: data.turnos[0].tipo });
        else setActiveService(null);
      }
    } catch {}
  };

  const fetchMenu = async () => {
    try {
      const res = await fetch(`${API_URL}/menu`);
      const data = await res.json();
      setMenu(data);
    } catch {
      // sin menú disponible
    } finally {
      setMenuLoading(false);
    }
  };

  const handleJoinQueue = async () => {
    if (!user) return;
    if (!activeService?.tipo) {
      Alert.alert("Cola", "No hay un turno activo en este horario");
      return;
    }
    setJoiningQueue(true);
    try {
      const res = await fetch(`${API_URL}/queue/join`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid: user.sid, tipo: activeService.tipo }),
      });
      const data = await res.json();
      if (res.ok) {
        setQueue({
          numero_turno: data.numero_turno,
          tipo: data.tipo,
          posicion: data.posicion,
          estado: "ESPERANDO",
          raciones_restantes: data.raciones_restantes,
        });
        router.push("/ticket");
      } else {
        Alert.alert("Cola", data.detail || "No se pudo unirse a la cola");
      }
    } catch {
      Alert.alert("Error", "No se pudo conectar al servidor");
    } finally {
      setJoiningQueue(false);
    }
  };

  const handleViewTicket = () => router.push("/ticket");

  const handleLogout = async () => {
    if (!user) return;
    try {
      await fetch(`${API_URL}/logout`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid: user.sid }),
      });
    } catch {}
    await SecureStore.deleteItemAsync("sid");
    setUser(null);
    router.replace("/");
  };

  const primerNombre = user?.nombre.split(" ")[0] ?? "Estudiante";

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: Colors.light.background }}>
      <StatusBar barStyle="light-content" />
      <ScrollView showsVerticalScrollIndicator={false}>

        {/* Header */}
        <LinearGradient
          colors={[Colors.light.maroon, Colors.light.maroonLight]}
          style={styles.header}
        >
          <View>
            <Text style={styles.greeting}>Hola, {primerNombre} 👋</Text>
            <Text style={styles.codigo}>{user?.codigo}</Text>
          </View>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
            <MaterialCommunityIcons name="logout" size={22} color="white" />
          </TouchableOpacity>
        </LinearGradient>

        {/* Créditos */}
        <View style={styles.creditsCard}>
          <MaterialCommunityIcons name="star-circle" size={32} color={Colors.light.maroon} />
          <View style={{ marginLeft: 12 }}>
            <Text style={styles.creditsLabel}>CRÉDITOS LLEVADOS</Text>
            <Text style={styles.creditsValue}>{user?.creditos_llevados ?? "—"}</Text>
          </View>
        </View>

        {/* Botón cola */}
        <View style={styles.queueSection}>
          {user?.queue?.estado === "ATENDIDO" ? (
            <TouchableOpacity style={[styles.joinBtn, { backgroundColor: "#10B981" }]} onPress={handleViewTicket}>
              <MaterialCommunityIcons name="check-circle" size={22} color="white" />
              <Text style={styles.queueBtnText}>
                Ya fuiste atendido — {user.queue.tipo}
              </Text>
            </TouchableOpacity>
          ) : user?.queue ? (
            <TouchableOpacity style={styles.viewTicketBtn} onPress={handleViewTicket}>
              <MaterialCommunityIcons name="ticket-confirmation" size={22} color="white" />
              <Text style={styles.queueBtnText}>
                {user.queue.estado === "ATENDIDO"
                  ? `Turno #${user.queue.turno_asignado ?? "—"}`
                  : `Posición #${user.queue.numero_turno}`}
              </Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.joinBtn, joiningQueue && { opacity: 0.7 }]}
              onPress={handleJoinQueue}
              disabled={joiningQueue}
            >
              {joiningQueue ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <MaterialCommunityIcons name="silverware-fork-knife" size={22} color="white" />
                  <Text style={styles.queueBtnText}>
                    Unirse a la cola de {activeService?.tipo ?? "…"}
                  </Text>
                </>
              )}
            </TouchableOpacity>
          )}
        </View>

        {/* Menú del día */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>MENÚ DE HOY</Text>

          {menuLoading ? (
            <ActivityIndicator color={Colors.light.maroon} style={{ marginTop: 20 }} />
          ) : !menu || menu.comidas.length === 0 ? (
            <Text style={styles.emptyText}>No hay menú disponible para hoy</Text>
          ) : (
            menu.comidas.map((comida) => (
              <View key={comida.id} style={styles.mealCard}>
                <TouchableOpacity
                  style={styles.mealHeader}
                  onPress={() =>
                    setExpandedMeal(
                      expandedMeal === comida.tipo_comida ? null : comida.tipo_comida
                    )
                  }
                >
                  <View style={styles.mealTitleRow}>
                    <MaterialCommunityIcons
                      name={MEAL_ICONS[comida.tipo_comida] ?? "food"}
                      size={20}
                      color={Colors.light.maroon}
                    />
                    <Text style={styles.mealTitle}>{comida.tipo_comida}</Text>
                  </View>
                  <Ionicons
                    name={expandedMeal === comida.tipo_comida ? "chevron-up" : "chevron-down"}
                    size={18}
                    color={Colors.light.gray}
                  />
                </TouchableOpacity>

                {expandedMeal === comida.tipo_comida && (
                  <View style={styles.mealBody}>
                    {comida.platos.map((p) => (
                      <Text key={p.id} style={styles.platoItem}>❖  {p.nombre}</Text>
                    ))}

                    {comida.energia_kcal !== null && (
                      <View style={styles.nutriBox}>
                        <Text style={styles.nutriTitle}>Aporte Nutricional</Text>
                        <View style={styles.nutriGrid}>
                          <NutrRow label="Energía"       value={`${comida.energia_kcal} Kcal`} />
                          <NutrRow label="Lípidos"       value={`${comida.lipidos_g} g`} />
                          <NutrRow label="Proteínas"     value={`${comida.proteinas_g} g`} />
                          <NutrRow label="Carbohidratos" value={`${comida.carbohidratos_g} g`} />
                        </View>
                      </View>
                    )}
                  </View>
                )}
              </View>
            ))
          )}
        </View>

        <Text style={styles.footer}>VRAD - UNI 2024</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function NutrRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.nutriRow}>
      <Text style={styles.nutriLabel}>{label}</Text>
      <Text style={styles.nutriValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    padding: 24,
    paddingTop: 16,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  greeting:     { color: "white", fontSize: 22, fontWeight: "900" },
  codigo:       { color: "rgba(255,255,255,0.7)", fontSize: 13, fontWeight: "600", marginTop: 2 },
  logoutBtn:    { padding: 8 },
  creditsCard:  {
    flexDirection: "row", alignItems: "center",
    backgroundColor: "white", margin: 16, borderRadius: 16,
    padding: 18, elevation: 3,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08, shadowRadius: 6,
  },
  creditsLabel: { fontSize: 10, color: Colors.light.gray, fontWeight: "700", letterSpacing: 1 },
  creditsValue: { fontSize: 28, fontWeight: "900", color: Colors.light.maroon, marginTop: 2 },
  queueSection: { marginHorizontal: 16, marginBottom: 8 },
  joinBtn: {
    backgroundColor: Colors.light.maroon, borderRadius: 16, padding: 16,
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, elevation: 4,
  },
  viewTicketBtn: {
    backgroundColor: Colors.light.success ?? "#10B981", borderRadius: 16, padding: 16,
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, elevation: 4,
  },
  queueBtnText: { color: "white", fontSize: 16, fontWeight: "700" },
  menuSection:  { margin: 16 },
  sectionTitle: { fontSize: 12, fontWeight: "800", color: Colors.light.gray, letterSpacing: 2, marginBottom: 12 },
  emptyText:    { color: Colors.light.gray, textAlign: "center", marginTop: 20 },
  mealCard:     { backgroundColor: "white", borderRadius: 16, marginBottom: 12, overflow: "hidden", elevation: 2 },
  mealHeader:   { flexDirection: "row", justifyContent: "space-between", alignItems: "center", padding: 16 },
  mealTitleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  mealTitle:    { fontSize: 15, fontWeight: "800", color: Colors.light.text, letterSpacing: 1 },
  mealBody:     { paddingHorizontal: 16, paddingBottom: 16 },
  platoItem:    { fontSize: 14, color: Colors.light.text, marginBottom: 6, fontWeight: "500" },
  nutriBox:     { backgroundColor: Colors.light.maroonExtraLight, borderRadius: 12, padding: 14, marginTop: 12 },
  nutriTitle:   { fontSize: 11, fontWeight: "800", color: Colors.light.maroon, letterSpacing: 1, marginBottom: 8, textAlign: "center" },
  nutriGrid:    { gap: 4 },
  nutriRow:     { flexDirection: "row", justifyContent: "space-between" },
  nutriLabel:   { fontSize: 13, color: Colors.light.text, fontWeight: "600" },
  nutriValue:   { fontSize: 13, color: Colors.light.maroon, fontWeight: "700" },
  footer:       { textAlign: "center", color: Colors.light.gray, fontSize: 11, marginVertical: 24 },
});
