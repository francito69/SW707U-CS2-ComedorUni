import { MaterialCommunityIcons, Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  Modal,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Colors } from "../constants/theme";
import { useUser } from "../constants/UserContext";

import { API_URL, WS_URL, NGROK_HEADERS } from "../constants/api";
const PING_MS = 150_000;

const ESTADO_COLOR: Record<string, string> = {
  ESPERANDO: Colors.light.maroon,
  LLAMADO:   "#F59E0B",
  ATENDIDO:  "#10B981",
  CANCELADO: Colors.light.error ?? "#EF4444",
};

const ESTADO_ICON: Record<string, any> = {
  ESPERANDO: "clock-outline",
  LLAMADO:   "bell-ring",
  ATENDIDO:  "check-circle",
  CANCELADO: "close-circle",
};

export default function TicketScreen() {
  const { user, setQueue } = useUser();
  const queue = user?.queue;

  const [estado, setEstado]           = useState(queue?.estado ?? "ESPERANDO");
  const [posicion, setPosicion]       = useState(queue?.posicion ?? 0);
  const [turnoActual, setTurnoActual] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);
  const [pingModal, setPingModal]     = useState(false);
  const [leaveModal, setLeaveModal]   = useState(false);
  const [confirming, setConfirming]   = useState(false);
  const [confirmError, setConfirmError] = useState(false);

  const ws          = useRef<WebSocket | null>(null);
  const pingTimer   = useRef<ReturnType<typeof setInterval> | null>(null);
  const pingTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!user?.sid || !queue) return;
    connectWS();
    fetchStatus();
    return () => cleanup();
  }, []);

  const cleanup = () => {
    pingTimer.current && clearInterval(pingTimer.current);
    pingTimeout.current && clearTimeout(pingTimeout.current);
    ws.current?.close();
  };

  const connectWS = () => {
    if (!user?.sid) return;
    const socket = new WebSocket(`${WS_URL}/queue/ws/${user.sid}`);
    ws.current = socket;

    socket.onopen = () => {
      setWsConnected(true);
      startHeartbeat();
    };

    socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        handleWsMessage(msg);
      } catch {}
    };

    socket.onclose = () => {
      setWsConnected(false);
      pingTimer.current && clearInterval(pingTimer.current);
    };

    socket.onerror = () => setWsConnected(false);
  };

  const startHeartbeat = () => {
    pingTimer.current = setInterval(() => {
      ws.current?.send(JSON.stringify({ type: "ping" }));
    }, PING_MS);
  };

  const handleWsMessage = (msg: any) => {
    switch (msg.type) {
      case "ping_request":
        setPingModal(true);
        pingTimeout.current = setTimeout(() => setPingModal(false), 180_000);
        break;
      case "llamado":
        setEstado("LLAMADO");
        setQueue(queue ? { ...queue, estado: "LLAMADO" } : null);
        break;
      case "estado":
        setEstado(msg.estado);
        setQueue(queue ? { ...queue, estado: msg.estado } : null);
        break;
      case "cancelado":
        setEstado("CANCELADO");
        break;
    }
  };

  const fetchStatus = async () => {
    if (!user?.sid) return;
    try {
      const res  = await fetch(`${API_URL}/queue/status?sid=${user.sid}`);
      const data = await res.json();
      if (res.ok) {
        setEstado(data.estado);
        setPosicion(data.posicion);
        setTurnoActual(data.turno_actual);
        setQueue(queue ? { ...queue, estado: data.estado, posicion: data.posicion } : null);
      }
    } catch {}
  };

  const handleConfirm = async () => {
    if (!user?.sid || confirming) return;
    setConfirming(true);
    setConfirmError(false);
    pingTimeout.current && clearTimeout(pingTimeout.current);
    setPingModal(false);
    try {
      const res  = await fetch(`${API_URL}/queue/confirm`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid: user.sid }),
      });
      const data = await res.json();
      setEstado(data.estado);
      setQueue(queue ? {
        ...queue,
        estado: data.estado,
        turno_asignado: data.turno_asignado ?? queue.turno_asignado,
      } : null);
    } catch {
      setConfirmError(true);
    } finally {
      setConfirming(false);
    }
  };

  const handleLeave = async () => {
    setLeaveModal(false);
    try {
      await fetch(`${API_URL}/queue/leave`, {
        method: "POST",
        headers: NGROK_HEADERS,
        body: JSON.stringify({ sid: user?.sid }),
      });
    } catch {}
    cleanup();
    setQueue(null);
    router.replace("/home");
  };

  if (!queue) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={{ color: Colors.light.gray }}>No tienes turno activo</Text>
        <TouchableOpacity onPress={() => router.replace("/home")} style={{ marginTop: 16 }}>
          <Text style={{ color: Colors.light.maroon, fontWeight: "700" }}>Volver al inicio</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const color = ESTADO_COLOR[estado] ?? Colors.light.maroon;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: color }]}>
      <StatusBar barStyle="light-content" />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.replace("/home")}>
          <Ionicons name="arrow-back" size={26} color="white" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>TICKET DIGITAL</Text>
        <View style={styles.wsIndicator}>
          <View style={[styles.wsDot, { backgroundColor: wsConnected ? "#4ADE80" : "#EF4444" }]} />
        </View>
      </View>

      {/* Ticket card */}
      <View style={styles.card}>

        {/* Posición o turno según estado */}
        <View style={styles.turnoSection}>
          <Text style={styles.turnoLabel}>
            {estado === "ATENDIDO" ? "TU TURNO" : "TU POSICIÓN"}
          </Text>
          <Text style={[styles.turnoNumber, { color }]}>
            {estado === "ATENDIDO"
              ? (queue.turno_asignado ?? "—")
              : queue.numero_turno}
          </Text>
          <View style={[styles.estadoBadge, { backgroundColor: color + "20" }]}>
            <MaterialCommunityIcons name={ESTADO_ICON[estado]} size={16} color={color} />
            <Text style={[styles.estadoText, { color }]}>{estado}</Text>
          </View>
        </View>

        <View style={styles.divider} />

        {/* Info */}
        <View style={styles.infoRow}>
          <InfoItem label="SERVICIO"     value={queue.tipo} />
          <InfoItem label="TURNOS ANTES" value={`${posicion}`} />
          <InfoItem label="TURNO ACTUAL" value={`${turnoActual}`} />
        </View>

        <View style={styles.divider} />

        {/* Acciones */}
        {estado === "LLAMADO" && (
          <>
            <TouchableOpacity
              style={[styles.confirmBtn, { backgroundColor: color }]}
              onPress={handleConfirm}
              disabled={confirming}
            >
              {confirming
                ? <ActivityIndicator color="white" />
                : <Text style={styles.confirmBtnText}>✓ Confirmar presencia</Text>
              }
            </TouchableOpacity>
            {confirmError && (
              <Text style={styles.errorText}>No se pudo confirmar. Intenta de nuevo.</Text>
            )}
          </>
        )}

        {(estado === "ESPERANDO" || estado === "LLAMADO") && (
          <TouchableOpacity style={styles.leaveBtn} onPress={() => setLeaveModal(true)}>
            <Text style={styles.leaveBtnText}>Salir de la cola</Text>
          </TouchableOpacity>
        )}

        {estado === "ATENDIDO" && (
          <TouchableOpacity
            style={[styles.confirmBtn, { backgroundColor: "#10B981" }]}
            onPress={() => router.replace("/home")}
          >
            <Text style={styles.confirmBtnText}>Volver al inicio</Text>
          </TouchableOpacity>
        )}

        {estado === "CANCELADO" && (
          <TouchableOpacity
            style={[styles.confirmBtn, { backgroundColor: Colors.light.error ?? "#EF4444" }]}
            onPress={() => { cleanup(); setQueue(null); router.replace("/home"); }}
          >
            <Text style={styles.confirmBtnText}>Volver al inicio</Text>
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.hint}>
        {wsConnected ? "Conectado en tiempo real" : "Sin conexión en tiempo real"}
      </Text>

      {/* Modal: ¿Sigues en la cola? */}
      <Modal visible={pingModal} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <MaterialCommunityIcons name="help-circle-outline" size={48} color={Colors.light.maroon} />
            <Text style={styles.modalTitle}>¿Sigues en la cola?</Text>
            <Text style={styles.modalBody}>
              Confirma tu presencia para mantener tu turno #{queue.numero_turno}.
            </Text>
            <TouchableOpacity
              style={[styles.confirmBtn, { backgroundColor: Colors.light.maroon, marginTop: 16, width: "100%" }]}
              onPress={() => {
                pingTimeout.current && clearTimeout(pingTimeout.current);
                setPingModal(false);
                ws.current?.send(JSON.stringify({ type: "ping" }));
              }}
            >
              <Text style={styles.confirmBtnText}>Sigo aquí</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Modal: Confirmar salida */}
      <Modal visible={leaveModal} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <MaterialCommunityIcons name="exit-run" size={48} color={Colors.light.error ?? "#EF4444"} />
            <Text style={styles.modalTitle}>¿Salir de la cola?</Text>
            <Text style={styles.modalBody}>
              Perderás tu turno #{queue.numero_turno} y no podrás recuperarlo.
            </Text>
            <TouchableOpacity
              style={[styles.confirmBtn, { backgroundColor: Colors.light.error ?? "#EF4444", marginTop: 16, width: "100%" }]}
              onPress={handleLeave}
            >
              <Text style={styles.confirmBtnText}>Sí, salir</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.leaveBtn, { marginTop: 8 }]}
              onPress={() => setLeaveModal(false)}
            >
              <Text style={[styles.leaveBtnText, { color: Colors.light.maroon }]}>Cancelar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoItem}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1 },
  center:       { flex: 1, alignItems: "center", justifyContent: "center" },
  header:       { flexDirection: "row", alignItems: "center", justifyContent: "space-between", padding: 20 },
  headerTitle:  { color: "white", fontSize: 16, fontWeight: "800", letterSpacing: 1 },
  wsIndicator:  { width: 30, alignItems: "flex-end" },
  wsDot:        { width: 10, height: 10, borderRadius: 5 },
  card:         {
    backgroundColor: "white", borderRadius: 28, margin: 16,
    padding: 28, elevation: 10,
    shadowColor: "#000", shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15, shadowRadius: 12,
  },
  turnoSection: { alignItems: "center", paddingVertical: 12 },
  turnoLabel:   { fontSize: 11, fontWeight: "800", color: Colors.light.gray, letterSpacing: 2 },
  turnoNumber:  { fontSize: 88, fontWeight: "900", lineHeight: 96 },
  estadoBadge:  { flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20, marginTop: 8 },
  estadoText:   { fontWeight: "700", fontSize: 13 },
  divider:      { height: 1, backgroundColor: Colors.light.grayLight, marginVertical: 20 },
  infoRow:      { flexDirection: "row", justifyContent: "space-around" },
  infoItem:     { alignItems: "center" },
  infoLabel:    { fontSize: 10, color: Colors.light.gray, fontWeight: "700", letterSpacing: 1 },
  infoValue:    { fontSize: 18, fontWeight: "800", color: Colors.light.text, marginTop: 4 },
  confirmBtn:   { borderRadius: 14, padding: 16, alignItems: "center", marginTop: 8 },
  confirmBtnText: { color: "white", fontWeight: "700", fontSize: 16 },
  leaveBtn:     { alignItems: "center", marginTop: 16, padding: 10 },
  leaveBtnText: { color: Colors.light.gray, fontWeight: "600", fontSize: 14 },
  errorText:    { color: Colors.light.error ?? "#EF4444", fontSize: 13, textAlign: "center", marginTop: 8, fontWeight: "600" },
  hint:         { color: "rgba(255,255,255,0.6)", textAlign: "center", fontSize: 12, marginBottom: 16 },
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.5)", alignItems: "center", justifyContent: "center" },
  modalCard:    { backgroundColor: "white", borderRadius: 24, padding: 28, width: "80%", alignItems: "center" },
  modalTitle:   { fontSize: 20, fontWeight: "900", color: Colors.light.text, marginTop: 12 },
  modalBody:    { fontSize: 14, color: Colors.light.gray, textAlign: "center", marginTop: 8, lineHeight: 20 },
});
