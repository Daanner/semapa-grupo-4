-- =========================================================
-- SEMAPA Grupo 4 - Esquema PostgreSQL recomendado
-- Para producción: PostgreSQL + particionamiento por mes en lecturas_iot.
-- =========================================================

CREATE TABLE IF NOT EXISTS subalcaldias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS distritos (
    id SERIAL PRIMARY KEY,
    subalcaldia_id INTEGER NOT NULL REFERENCES subalcaldias(id),
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    poblacion INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS zonas (
    id SERIAL PRIMARY KEY,
    distrito_id INTEGER NOT NULL REFERENCES distritos(id),
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),
    riesgo_hidrico VARCHAR(20) DEFAULT 'NORMAL'
);

CREATE TABLE IF NOT EXISTS categorias_tarifarias (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    tarifa_base NUMERIC(10,2) NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    ci_nit VARCHAR(30) NOT NULL UNIQUE,
    nombres VARCHAR(120) NOT NULL,
    apellidos VARCHAR(120),
    telefono VARCHAR(30),
    correo VARCHAR(120),
    direccion TEXT
);

CREATE TABLE IF NOT EXISTS infraestructuras (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(40) NOT NULL UNIQUE,
    zona_id INTEGER NOT NULL REFERENCES zonas(id),
    direccion TEXT NOT NULL,
    tipo VARCHAR(40) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'ACTIVA',
    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7)
);

CREATE TABLE IF NOT EXISTS contratos (
    id SERIAL PRIMARY KEY,
    numero_contrato VARCHAR(40) NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    infraestructura_id INTEGER NOT NULL REFERENCES infraestructuras(id),
    categoria_id INTEGER NOT NULL REFERENCES categorias_tarifarias(id),
    fecha_inicio DATE NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'ACTIVO'
);

CREATE TABLE IF NOT EXISTS radiobases (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    codigo VARCHAR(40) NOT NULL UNIQUE,
    zona_id INTEGER NOT NULL REFERENCES zonas(id),
    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),
    estado VARCHAR(30) NOT NULL DEFAULT 'ACTIVA'
);

CREATE TABLE IF NOT EXISTS medidores (
    id SERIAL PRIMARY KEY,
    mac VARCHAR(17) NOT NULL UNIQUE,
    modelo VARCHAR(80) NOT NULL,
    contrato_id INTEGER NOT NULL REFERENCES contratos(id),
    radiobase_id INTEGER NOT NULL REFERENCES radiobases(id),
    estado VARCHAR(30) NOT NULL DEFAULT 'ACTIVO',
    fecha_instalacion DATE,
    ultima_senal TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lecturas_iot (
    id BIGSERIAL PRIMARY KEY,
    medidor_id INTEGER NOT NULL REFERENCES medidores(id),
    radiobase_id INTEGER NOT NULL REFERENCES radiobases(id),
    fecha_hora TIMESTAMP NOT NULL,
    lectura_anterior NUMERIC(12,2) NOT NULL,
    lectura_actual NUMERIC(12,2) NOT NULL,
    consumo_m3 NUMERIC(12,2) NOT NULL,
    temperatura_c NUMERIC(5,2),
    origen VARCHAR(20) NOT NULL DEFAULT 'IOT',
    hash_evento VARCHAR(80) NOT NULL UNIQUE,
    fecha_pago TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lecturas_medidor_fecha ON lecturas_iot(medidor_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_lecturas_fecha ON lecturas_iot(fecha_hora);
