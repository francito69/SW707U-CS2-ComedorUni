-- ─────────────────────────────────────────────
--  M1 · Estudiantes
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS estudiantes (
    id                SERIAL       PRIMARY KEY,
    codigo            VARCHAR(20)  NOT NULL UNIQUE,
    nombres           VARCHAR(255) NOT NULL,
    apellido_paterno  VARCHAR(255) NOT NULL,
    apellido_materno  VARCHAR(255),
    email             VARCHAR(255) UNIQUE,
    push_token        VARCHAR(255),
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
--  M2 · Plantilla de turnos (horarios por defecto)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS turnos_config (
    id              SERIAL      PRIMARY KEY,
    tipo            VARCHAR(20) NOT NULL UNIQUE,  -- 'ALMUERZO' | 'CENA'
    hora_apertura   TIME        NOT NULL,         -- desde cuándo se puede encolar
    hora_inicio     TIME        NOT NULL,         -- empieza la atención
    hora_cierre     TIME        NOT NULL,         -- termina la atención
    raciones_max    INTEGER     DEFAULT 5000,
    activo          BOOLEAN     DEFAULT TRUE
);

INSERT INTO turnos_config (tipo, hora_apertura, hora_inicio, hora_cierre) VALUES
    ('ALMUERZO', '6:00', '7:00', '8:00'),
    ('CENA',     '11:30', '12:30', '13:30'),
    ('PRUEBA',   '00:00', '00:10', '23:59');  -- para pruebas, turno siempre abierto

-- ─────────────────────────────────────────────
--  M2 · Instancia diaria del turno
--  Garantiza: solo un ALMUERZO y una CENA por día
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS turno_dia (
    id              SERIAL      PRIMARY KEY,
    config_id       INTEGER     NOT NULL REFERENCES turnos_config(id),
    fecha           DATE        NOT NULL DEFAULT CURRENT_DATE,
    raciones_max    INTEGER,                      -- sobreescribe el default si se necesita
    hora_apertura   TIME,                         -- sobreescribe si se necesita
    hora_cierre     TIME,                         -- sobreescribe si se necesita
    abierto         BOOLEAN     DEFAULT TRUE,
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (config_id, fecha)                     -- un almuerzo y una cena por día
);


-- Mock data: instancias del día actual (los admins crearán las de días futuros)
INSERT INTO turno_dia (config_id, fecha,raciones_max) VALUES
    (1, (NOW() AT TIME ZONE 'America/Lima')::DATE, 5000),
    (2, (NOW() AT TIME ZONE 'America/Lima')::DATE, 5000),
    (3, (NOW() AT TIME ZONE 'America/Lima')::DATE, 10);  -- turno de prueba, siempre abierto

-- ─────────────────────────────────────────────
--  M2 · Turnos de estudiantes
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS turnos (
    id              SERIAL      PRIMARY KEY,
    estudiante_id   INTEGER     NOT NULL REFERENCES estudiantes(id),
    turno_dia_id    INTEGER     NOT NULL REFERENCES turno_dia(id),
    numero_turno    INTEGER     NOT NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'ESPERANDO',
    ingresado_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    llamado_at      TIMESTAMP,
    confirmado_at   TIMESTAMP,
    cancelado_at    TIMESTAMP,
    ultimo_ping     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (estado IN ('ESPERANDO', 'LLAMADO', 'ATENDIDO', 'CANCELADO'))
);

CREATE INDEX IF NOT EXISTS idx_turnos_dia ON turnos (turno_dia_id, estado);

-- Un número de turno no puede repetirse dentro del mismo día, aunque la lógica falle
/*
Primero creamos el índice único para que la base de datos rechace un
duplicado, ahora toca analzar la lógica de negocio para que no se genere un duplicado
*/
CREATE UNIQUE INDEX IF NOT EXISTS idx_turnos_numero_turno_unico
ON turnos (turno_dia_id, numero_turno);

-- Solo un turno activo por estudiante por día, pero permite múltiples cancelaciones
CREATE UNIQUE INDEX IF NOT EXISTS idx_turnos_activo
ON turnos (estudiante_id, turno_dia_id)
WHERE estado != 'CANCELADO';

-- ─────────────────────────────────────────────
--  M3 · Menú diario
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS menu_dia (
    id              SERIAL        PRIMARY KEY,
    fecha           DATE          NOT NULL,
    tipo_comida     VARCHAR(20)   NOT NULL,    -- 'DESAYUNO' | 'ALMUERZO' | 'CENA'
    energia_kcal    DECIMAL(8,2),
    lipidos_g       DECIMAL(6,2),
    proteinas_g     DECIMAL(6,2),
    carbohidratos_g DECIMAL(6,2),
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (fecha, tipo_comida),
    CHECK (tipo_comida IN ('DESAYUNO', 'ALMUERZO', 'CENA'))
);

CREATE TABLE IF NOT EXISTS menu_platos (
    id          SERIAL        PRIMARY KEY,
    menu_dia_id INTEGER       NOT NULL REFERENCES menu_dia(id) ON DELETE CASCADE,
    nombre      VARCHAR(255)  NOT NULL
);

-- Mock data: menú del día actual (fecha en timezone Lima)
INSERT INTO menu_dia (fecha, tipo_comida, energia_kcal, lipidos_g, proteinas_g, carbohidratos_g) VALUES
    ((NOW() AT TIME ZONE 'America/Lima')::DATE, 'DESAYUNO', 607.98, 16.83, 19.44,  81.31),
    ((NOW() AT TIME ZONE 'America/Lima')::DATE, 'ALMUERZO', 1332.46, 51.11, 43.31, 171.35),
    ((NOW() AT TIME ZONE 'America/Lima')::DATE, 'CENA',     1042.36, 27.04, 38.46, 131.83);

INSERT INTO menu_platos (menu_dia_id, nombre)
SELECT id, unnest(ARRAY['AVENA CON MEMBRILLO', 'PAN DE TOLETE CON QUESO', 'FRUTA'])
FROM menu_dia WHERE fecha = (NOW() AT TIME ZONE 'America/Lima')::DATE AND tipo_comida = 'DESAYUNO';

INSERT INTO menu_platos (menu_dia_id, nombre)
SELECT id, unnest(ARRAY['SOPA DE FIDEOS', 'ARROZ CHAUFA DE CERDO', 'REFRESCO DE CHICHA MORADA', 'FRUTA'])
FROM menu_dia WHERE fecha = (NOW() AT TIME ZONE 'America/Lima')::DATE AND tipo_comida = 'ALMUERZO';

INSERT INTO menu_platos (menu_dia_id, nombre)
SELECT id, unnest(ARRAY['AJI DE PAVITA PRESADO CON PAPAS', 'ARROZ', 'INFUSION DE CEBADA', 'FRUTA'])
FROM menu_dia WHERE fecha = (NOW() AT TIME ZONE 'America/Lima')::DATE AND tipo_comida = 'CENA';

-- ─────────────────────────────────────────────
--  M5 · Seguimiento
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS historial_asistencia (
    id              SERIAL      PRIMARY KEY,
    estudiante_id   INTEGER     NOT NULL REFERENCES estudiantes(id),
    turno_dia_id    INTEGER     NOT NULL REFERENCES turno_dia(id),
    numero_turno    INTEGER     NOT NULL,
    tipo_comida     VARCHAR(20),
    atendido_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (estudiante_id, turno_dia_id)
);

CREATE TABLE IF NOT EXISTS historial_encolamiento (
    id              SERIAL      PRIMARY KEY,
    estudiante_id   INTEGER     NOT NULL REFERENCES estudiantes(id),
    turno_dia_id    INTEGER     NOT NULL REFERENCES turno_dia(id),
    numero_turno    INTEGER     NOT NULL,
    tipo_comida     VARCHAR(20),
    encolado_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (estudiante_id, turno_dia_id)
);
