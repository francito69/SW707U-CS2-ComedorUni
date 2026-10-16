"""
DEMO TSDB — ComedorUNI
Módulos: M1 (auth_events), M4 (notification_events), M5 (historial_*)

Endpoints de simulación (POST):
  /demo/login       → registra evento en auth_events         [M1]
  /demo/notify      → registra evento en notification_events  [M4]
  /demo/enqueue     → registra en historial_encolamiento      [M5]
  /demo/attend      → registra en historial_asistencia        [M5]

Endpoints de consulta TSDB (GET):
  /demo/auth-summary          → pico de logins por minuto (time_bucket)   [M1]
  /demo/notification-summary  → tasa de éxito push por ventana de 5 min   [M4]
  /demo/conversion-report     → % encolados que fueron atendidos por día   [M5]
  /demo/hypertables           → metadata de las hypertables en TimescaleDB
"""

import os
import time
import random
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="DEMO TSDB — ComedorUNI")

DB_PARAMS = {
    "host":     os.getenv("DB_HOST",     "postgres-tsdb"),
    "dbname":   os.getenv("DB_NAME",     "comedor_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "password123"),
    "port":     int(os.getenv("DB_PORT", "5432")),
}


def get_conn():
    return psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)


# ─── Modelos de entrada ────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    codigo: str
    evento: str = "login_ok"   # login_ok | login_fail | biometric_ok | biometric_fail | logout

class NotifyRequest(BaseModel):
    evento: str   = "turno.llamado"   # turno.llamado | turno.cancelado
    success: bool = True

class EnqueueRequest(BaseModel):
    estudiante_id: int
    tipo_comida:   str = "ALMUERZO"

class AttendRequest(BaseModel):
    estudiante_id: int
    tipo_comida:   str = "ALMUERZO"


# ─── Salud ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "demo": "TSDB-ComedorUNI"}


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINTS DE SIMULACIÓN (equivalentes a lo que haría el código real de M1/M4/M5)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/demo/login", summary="[M1] Registrar evento de autenticación en auth_events")
def demo_login(req: LoginRequest):
    """
    Simula lo que _record_auth_event() haría en auth/router.py.
    Inserta en la hypertable auth_events con latencia aleatoria (demo).
    """
    latency = random.randint(120, 500)
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO auth_events (codigo, evento, latency_ms) VALUES (%s, %s, %s)",
                (req.codigo, req.evento, latency),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "insertado_en": "auth_events (hypertable)",
        "codigo": req.codigo,
        "evento": req.evento,
        "latency_ms": latency,
    }


@app.post("/demo/notify", summary="[M4] Registrar métrica de notificación push en notification_events")
def demo_notify(req: NotifyRequest):
    """
    Simula lo que _record_notification() haría en notifications/consumer.py.
    Inserta en la hypertable notification_events.
    """
    latency = random.randint(80, 400)
    detalle = None if req.success else "ExpoError: DeviceNotRegistered"
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notification_events (evento, success, latency_ms, detalle) VALUES (%s, %s, %s, %s)",
                (req.evento, req.success, latency, detalle),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "insertado_en": "notification_events (hypertable)",
        "evento": req.evento,
        "success": req.success,
        "latency_ms": latency,
    }


@app.post("/demo/enqueue", summary="[M5] Registrar encolamiento en historial_encolamiento")
def demo_enqueue(req: EnqueueRequest):
    """
    Simula lo que tracking/service.py hace al recibir turno.encolado de RabbitMQ.
    Inserta en la hypertable historial_encolamiento.
    """
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO historial_encolamiento (estudiante_id, turno_dia_id, tipo_comida)
                   VALUES (%s, %s, %s)
                   ON CONFLICT DO NOTHING""",
                (req.estudiante_id, 1, req.tipo_comida),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "insertado_en": "historial_encolamiento (hypertable)",
        "estudiante_id": req.estudiante_id,
        "tipo_comida": req.tipo_comida,
    }


@app.post("/demo/attend", summary="[M5] Registrar asistencia en historial_asistencia")
def demo_attend(req: AttendRequest):
    """
    Simula lo que tracking/service.py hace al recibir turno.atendido de RabbitMQ.
    Inserta en la hypertable historial_asistencia.
    """
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO historial_asistencia (estudiante_id, turno_dia_id, tipo_comida)
                   VALUES (%s, %s, %s)
                   ON CONFLICT DO NOTHING""",
                (req.estudiante_id, 1, req.tipo_comida),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "insertado_en": "historial_asistencia (hypertable)",
        "estudiante_id": req.estudiante_id,
        "tipo_comida": req.tipo_comida,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINTS DE CONSULTA TSDB
#  Cada uno demuestra una característica de TimescaleDB que no existe en
#  PostgreSQL estándar: time_bucket, particionado automático, continuous aggregate.
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/demo/auth-summary", summary="[M1] Pico de logins por minuto (time_bucket)")
def demo_auth_summary():
    """
    Consulta auth_events con time_bucket('1 minute', ts).
    En PostgreSQL estándar esto sería date_trunc('minute', ts),
    que no aprovecha el particionado por tiempo — TimescaleDB solo
    toca el chunk del intervalo consultado.
    """
    sql = """
        SELECT
            time_bucket('1 minute', ts)                            AS minuto,
            COUNT(*) FILTER (WHERE evento = 'login_ok')            AS login_ok,
            COUNT(*) FILTER (WHERE evento = 'login_fail')          AS login_fail,
            COUNT(*) FILTER (WHERE evento = 'biometric_ok')        AS biometric_ok,
            COUNT(*) FILTER (WHERE evento = 'biometric_fail')      AS biometric_fail,
            ROUND(AVG(latency_ms))                                 AS latencia_prom_ms
        FROM auth_events
        WHERE ts > NOW() - INTERVAL '3 hours'
        GROUP BY minuto
        ORDER BY minuto DESC
        LIMIT 20;
    """
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "descripcion": "Eventos de autenticación agrupados por minuto (últimas 3 h)",
        "funcion_tsdb": "time_bucket('1 minute', ts)",
        "filas": [dict(r) for r in rows],
    }


@app.get("/demo/notification-summary", summary="[M4] Tasa de éxito push por ventana de 5 minutos")
def demo_notification_summary():
    """
    Consulta notification_events con time_bucket('5 minutes', ts).
    Muestra cuántas notificaciones fallaron en cada ventana
    para detectar intervalos de degradación del servicio Expo.
    """
    sql = """
        SELECT
            time_bucket('5 minutes', ts)                    AS ventana,
            evento,
            COUNT(*)                                        AS total,
            COUNT(*) FILTER (WHERE success)                 AS exitosas,
            COUNT(*) FILTER (WHERE NOT success)             AS fallidas,
            ROUND(
                COUNT(*) FILTER (WHERE success) * 100.0
                / NULLIF(COUNT(*), 0), 1
            )                                               AS pct_exito,
            ROUND(AVG(latency_ms))                          AS latencia_prom_ms
        FROM notification_events
        WHERE ts > NOW() - INTERVAL '3 hours'
        GROUP BY ventana, evento
        ORDER BY ventana DESC
        LIMIT 20;
    """
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "descripcion": "Métricas de entrega push agrupadas por ventana de 5 min (últimas 3 h)",
        "funcion_tsdb": "time_bucket('5 minutes', ts)",
        "filas": [dict(r) for r in rows],
    }


@app.get("/demo/conversion-report", summary="[M5] Tasa de conversión encolar→atendido por día")
def demo_conversion_report():
    """
    JOIN entre historial_encolamiento y historial_asistencia.
    Ambas son hypertables — el particionado por tiempo acelera el
    GROUP BY diario sobre grandes volúmenes históricos.
    """
    sql = """
        SELECT
            time_bucket('1 day', e.encolado_at)    AS dia,
            e.tipo_comida,
            COUNT(e.id)                             AS encolados,
            COUNT(a.id)                             AS atendidos,
            ROUND(
                COUNT(a.id) * 100.0
                / NULLIF(COUNT(e.id), 0), 1
            )                                       AS pct_conversion
        FROM historial_encolamiento e
        LEFT JOIN historial_asistencia a
            ON  a.estudiante_id = e.estudiante_id
            AND a.turno_dia_id  = e.turno_dia_id
        WHERE e.encolado_at > NOW() - INTERVAL '30 days'
        GROUP BY dia, e.tipo_comida
        ORDER BY dia DESC;
    """
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "descripcion": "Conversión encolar→atendido por día (últimos 30 días)",
        "funcion_tsdb": "time_bucket('1 day', encolado_at) + JOIN entre hypertables",
        "filas": [dict(r) for r in rows],
    }


@app.get("/demo/hypertables", summary="Metadata de las hypertables registradas en TimescaleDB")
def demo_hypertables():
    """
    Consulta timescaledb_information.hypertables para mostrar
    el número de chunks activos en cada tabla.
    Esta vista solo existe cuando TimescaleDB está activo.
    """
    sql = """
        SELECT
            hypertable_name,
            num_chunks,
            num_dimensions,
            compression_enabled
        FROM timescaledb_information.hypertables
        ORDER BY hypertable_name;
    """
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "descripcion": "Hypertables registradas en esta instancia de TimescaleDB",
        "nota": "num_chunks aumenta con el tiempo; cada chunk es una partición temporal",
        "hypertables": [dict(r) for r in rows],
    }
