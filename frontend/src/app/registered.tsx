import { View, Text, StyleSheet, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../constants/theme';
import { Feather, Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

export default function RegisteredScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.content}>
        <LinearGradient
          colors={[Colors.light.success, '#10B981']}
          style={styles.successCircle}
        >
          <Feather name="check" size={60} color="white" />
        </LinearGradient>

        <Text style={styles.title}>¡Ingreso{"\n"}Registrado!</Text>
        <Text style={styles.subtitle}>
          Tu acceso ha sido validado correctamente.{"\n"}Disfruta de tu comida.
        </Text>

        <View style={styles.infoCard}>
          <View style={styles.infoIconContainer}>
            <Ionicons name="time" size={28} color={Colors.light.success} />
          </View>
          <View style={styles.infoTextContainer}>
            <Text style={styles.infoLabel}>Hora de registro</Text>
            <Text style={styles.infoValue}>12:35 PM</Text>
          </View>
        </View>

        <View style={{ marginTop: 60, opacity: 0.3 }}>
           <Ionicons name="restaurant" size={40} color={Colors.light.gray} />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 30,
  },
  successCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 40,
    elevation: 10,
    shadowColor: Colors.light.success,
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: Colors.light.text,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.gray,
    textAlign: 'center',
    marginTop: 15,
    lineHeight: 24,
  },
  infoCard: {
    backgroundColor: Colors.light.secondary,
    padding: 25,
    borderRadius: 24,
    width: '100%',
    marginTop: 50,
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 15,
    backgroundColor: 'white',
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoTextContainer: {
    marginLeft: 20,
  },
  infoLabel: {
    fontSize: 12,
    color: Colors.light.gray,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  infoValue: {
    fontSize: 20,
    fontWeight: '800',
    color: Colors.light.text,
    marginTop: 2,
  },
});
