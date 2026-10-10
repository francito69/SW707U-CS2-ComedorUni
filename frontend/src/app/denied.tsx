import { View, Text, TouchableOpacity, StyleSheet, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Feather, Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/theme';

export default function DeniedScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.content}>
        <View style={styles.errorIconContainer}>
          <Feather name="shield-off" size={45} color={Colors.light.maroon} />
        </View>

        <Text style={styles.title}>Acceso Denegado</Text>
        <Text style={styles.description}>
          Parece que no tienes los permisos necesarios o no estás usando un correo institucional @uni.pe.
        </Text>

        <View style={styles.buttonContainer}>
          <TouchableOpacity style={styles.retryButton} onPress={() => router.back()}>
            <Text style={styles.retryButtonText}>Volver a Intentar</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.helpButton}>
            <Text style={styles.helpButtonText}>Contactar Soporte</Text>
          </TouchableOpacity>
        </View>

        <View style={{ marginTop: 40, flexDirection: 'row', alignItems: 'center', opacity: 0.5 }}>
           <Ionicons name="information-circle" size={18} color={Colors.light.gray} />
           <Text style={{ marginLeft: 6, fontSize: 12, color: Colors.light.gray }}>Verifica tu conexión y cuenta</Text>
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
  errorIconContainer: {
    width: 100,
    height: 100,
    backgroundColor: Colors.light.maroonExtraLight,
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: Colors.light.text,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    color: Colors.light.gray,
    textAlign: 'center',
    marginTop: 15,
    lineHeight: 24,
  },
  buttonContainer: {
    width: '100%',
    marginTop: 60,
  },
  retryButton: {
    backgroundColor: Colors.light.maroon,
    padding: 18,
    borderRadius: 18,
    alignItems: 'center',
    width: '100%',
    elevation: 4,
    shadowColor: Colors.light.maroon,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '700',
  },
  helpButton: {
    padding: 18,
    alignItems: 'center',
    marginTop: 10,
  },
  helpButtonText: {
    color: Colors.light.gray,
    fontSize: 14,
    fontWeight: '600',
  },
});
