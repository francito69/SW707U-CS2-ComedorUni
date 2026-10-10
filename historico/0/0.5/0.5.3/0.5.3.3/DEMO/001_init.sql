-- Estructura simplificada del sistema del comedor de la UNI
CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombres VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS turno_dia (
    id SERIAL PRIMARY KEY,
    fecha DATE DEFAULT CURRENT_DATE,
    tipo_comida VARCHAR(20) NOT NULL
);

-- Tabla del Módulo M7 (busca tu FastAPI)
CREATE TABLE IF NOT EXISTS configuracion (
    version INT PRIMARY KEY,
    max_aforo_comedor INT NOT NULL,
    tiempo_max_confirmacion_min INT NOT NULL,
    tiempo_tolerancia_expiracion_min INT NOT NULL,
    modificado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datos semilla para la UNI (Aforo inicial listo para el primer GET de la demo)
INSERT INTO estudiantes (codigo, nombres) VALUES ('20220001A', 'Diego Alva');
INSERT INTO configuracion (version, max_aforo_comedor, tiempo_max_confirmacion_min, tiempo_tolerancia_expiracion_min, modificado_por) 
VALUES (1, 1200, 15, 5, 'admin-bienestar');