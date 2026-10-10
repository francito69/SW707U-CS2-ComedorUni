-- ─────────────────────────────────────────────────────────────────────────────
--  DEMO TSDB — ComedorUNI
--  Activa TimescaleDB y crea las hypertables para M1, M4 y M5.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ─────────────────────────────────────────────
--  M5 · Tablas de seguimiento (luego hypertables)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS historial_encolamiento (
    id              SERIAL PRIMARY KEY,
    estudiante_id   INTEGER      NOT NULL,
    turno_dia_id    INTEGER      NOT NULL DEFAULT 1,
    tipo_comida     VARCHAR(20)  NOT NULL CHECK (tipo_comida IN ('ALMUERZO', 'CENA')),
    encolado_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS historial_asistencia (
    id              SERIAL PRIMARY KEY,
    estudiante_id   INTEGER      NOT NULL,
    turno_dia_id    INTEGER      NOT NULL DEFAULT 1,
    tipo_comida     VARCHAR(20)  NOT NULL CHECK (tipo_comida IN ('ALMUERZO', 'CENA')),
    atendido_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
--  M1 · Eventos de autenticación
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth_events (
    ts          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    codigo      VARCHAR(20),
    evento      VARCHAR(30)  NOT NULL CHECK (evento IN ('login_ok','login_fail','biometric_ok','biometric_fail','logout')),
    latency_ms  INTEGER,
    detalle     TEXT
);

-- ─────────────────────────────────────────────
--  M4 · Métricas de notificaciones push
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_events (
    ts          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    evento      VARCHAR(30)  NOT NULL CHECK (evento IN ('turno.llamado','turno.cancelado')),
    success     BOOLEAN      NOT NULL,
    latency_ms  INTEGER,
    detalle     TEXT
);

-- ─────────────────────────────────────────────
--  Convertir a hypertables (particionado automático por tiempo)
-- ─────────────────────────────────────────────
SELECT create_hypertable('historial_encolamiento', 'encolado_at', if_not_exists => TRUE);
SELECT create_hypertable('historial_asistencia',   'atendido_at', if_not_exists => TRUE);
SELECT create_hypertable('auth_events',            'ts',          if_not_exists => TRUE);
SELECT create_hypertable('notification_events',    'ts',          if_not_exists => TRUE);

-- ─────────────────────────────────────────────
--  Continuous aggregate: asistencia diaria (M5 dashboard)
--  Se actualiza incrementalmente — no recalcula todo el historial.
-- ─────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS asistencia_diaria
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', atendido_at) AS dia,
    tipo_comida,
    COUNT(*)                           AS total_atendidos
FROM historial_asistencia
GROUP BY dia, tipo_comida;

-- ─────────────────────────────────────────────
--  Semilla: actividad simulada de apertura de cola (hace 2 horas)
-- ─────────────────────────────────────────────
INSERT INTO auth_events (ts, codigo, evento, latency_ms) VALUES
(NOW() - INTERVAL '120 minutes', '20220001A', 'login_ok',       275),
(NOW() - INTERVAL '120 minutes', '20220002B', 'login_fail',     140),
(NOW() - INTERVAL '119 minutes', '20220003C', 'login_ok',       305),
(NOW() - INTERVAL '119 minutes', '20220004D', 'login_ok',       290),
(NOW() - INTERVAL '118 minutes', '20220005E', 'login_ok',       320),
(NOW() - INTERVAL '118 minutes', '20220001A', 'biometric_ok',   415),
(NOW() - INTERVAL '117 minutes', '20220003C', 'biometric_ok',   380),
(NOW() - INTERVAL '117 minutes', '20220004D', 'biometric_fail', 210),
(NOW() - INTERVAL '116 minutes', '20220005E', 'biometric_ok',   398),
(NOW() - INTERVAL '115 minutes', '20220006F', 'login_ok',       265);

INSERT INTO historial_encolamiento (estudiante_id, turno_dia_id, tipo_comida, encolado_at) VALUES
(1, 1, 'ALMUERZO', NOW() - INTERVAL '115 minutes'),
(3, 1, 'ALMUERZO', NOW() - INTERVAL '114 minutes'),
(4, 1, 'ALMUERZO', NOW() - INTERVAL '113 minutes'),
(5, 1, 'ALMUERZO', NOW() - INTERVAL '112 minutes'),
(6, 1, 'ALMUERZO', NOW() - INTERVAL '111 minutes');

INSERT INTO historial_asistencia (estudiante_id, turno_dia_id, tipo_comida, atendido_at) VALUES
(1, 1, 'ALMUERZO', NOW() - INTERVAL '110 minutes'),
(3, 1, 'ALMUERZO', NOW() - INTERVAL '108 minutes'),
(5, 1, 'ALMUERZO', NOW() - INTERVAL '105 minutes'),
(6, 1, 'ALMUERZO', NOW() - INTERVAL '100 minutes');

INSERT INTO notification_events (ts, evento, success, latency_ms) VALUES
(NOW() - INTERVAL '110 minutes', 'turno.llamado', TRUE,  175),
(NOW() - INTERVAL '108 minutes', 'turno.llamado', TRUE,  210),
(NOW() - INTERVAL '105 minutes', 'turno.llamado', FALSE, 340),
(NOW() - INTERVAL '100 minutes', 'turno.llamado', TRUE,  188);
