-- =========================================================
-- SEMAPA Grupo 4 - Base de Datos Operacional/Analítica
-- Motor local: SQLite
-- Diseño equivalente para PostgreSQL en app/db/schema_postgresql.sql
-- =========================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS subalcaldias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS distritos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subalcaldia_id INTEGER NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    poblacion INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (subalcaldia_id) REFERENCES subalcaldias(id)
);

CREATE TABLE IF NOT EXISTS zonas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distrito_id INTEGER NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    latitud REAL,
    longitud REAL,
    riesgo_hidrico TEXT DEFAULT 'NORMAL',
    FOREIGN KEY (distrito_id) REFERENCES distritos(id)
);

CREATE TABLE IF NOT EXISTS categorias_tarifarias (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    tarifa_base REAL NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ci_nit TEXT NOT NULL UNIQUE,
    nombres TEXT NOT NULL,
    apellidos TEXT,
    telefono TEXT,
    correo TEXT,
    direccion TEXT
);

CREATE TABLE IF NOT EXISTS infraestructuras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    zona_id INTEGER NOT NULL,
    direccion TEXT NOT NULL,
    tipo TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ACTIVA',
    latitud REAL,
    longitud REAL,
    FOREIGN KEY (zona_id) REFERENCES zonas(id)
);

CREATE TABLE IF NOT EXISTS contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_contrato TEXT NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL,
    infraestructura_id INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL,
    fecha_inicio TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ACTIVO',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (infraestructura_id) REFERENCES infraestructuras(id),
    FOREIGN KEY (categoria_id) REFERENCES categorias_tarifarias(id)
);

CREATE TABLE IF NOT EXISTS radiobases (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    zona_id INTEGER NOT NULL,
    latitud REAL,
    longitud REAL,
    estado TEXT NOT NULL DEFAULT 'ACTIVA',
    FOREIGN KEY (zona_id) REFERENCES zonas(id)
);

CREATE TABLE IF NOT EXISTS medidores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT NOT NULL UNIQUE,
    modelo TEXT NOT NULL,
    contrato_id INTEGER NOT NULL,
    radiobase_id INTEGER NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ACTIVO',
    fecha_instalacion TEXT,
    ultima_senal TEXT,
    FOREIGN KEY (contrato_id) REFERENCES contratos(id),
    FOREIGN KEY (radiobase_id) REFERENCES radiobases(id)
);

CREATE TABLE IF NOT EXISTS lecturas_iot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medidor_id INTEGER NOT NULL,
    radiobase_id INTEGER NOT NULL,
    fecha_hora TEXT NOT NULL,
    lectura_anterior REAL NOT NULL,
    lectura_actual REAL NOT NULL,
    consumo_m3 REAL NOT NULL,
    temperatura_c REAL,
    origen TEXT NOT NULL DEFAULT 'IOT',
    hash_evento TEXT NOT NULL UNIQUE,
    fecha_pago TEXT,
    FOREIGN KEY (medidor_id) REFERENCES medidores(id),
    FOREIGN KEY (radiobase_id) REFERENCES radiobases(id)
);

CREATE TABLE IF NOT EXISTS lecturas_manuales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medidor_id INTEGER NOT NULL,
    usuario_campo TEXT NOT NULL,
    lectura_actual REAL NOT NULL,
    fotografia_url TEXT,
    latitud REAL,
    longitud REAL,
    observacion TEXT,
    fecha_registro TEXT NOT NULL,
    estado_sync TEXT DEFAULT 'PENDIENTE',
    FOREIGN KEY (medidor_id) REFERENCES medidores(id)
);

CREATE TABLE IF NOT EXISTS preavisos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contrato_id INTEGER NOT NULL,
    periodo TEXT NOT NULL,
    consumo_total_m3 REAL NOT NULL,
    monto_estimado REAL NOT NULL,
    fecha_generacion TEXT NOT NULL,
    codigo_pago TEXT NOT NULL UNIQUE,
    estado TEXT DEFAULT 'GENERADO',
    FOREIGN KEY (contrato_id) REFERENCES contratos(id)
);

CREATE TABLE IF NOT EXISTS mensajes_preaviso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preaviso_id INTEGER NOT NULL,
    canal TEXT NOT NULL,
    destinatario TEXT,
    mensaje TEXT NOT NULL,
    estado TEXT DEFAULT 'ENCOLADO',
    fecha_creacion TEXT NOT NULL,
    fecha_envio TEXT,
    FOREIGN KEY (preaviso_id) REFERENCES preavisos(id)
);

CREATE TABLE IF NOT EXISTS carga_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proceso TEXT NOT NULL,
    total_recibidos INTEGER DEFAULT 0,
    insertados INTEGER DEFAULT 0,
    duplicados_omitidos INTEGER DEFAULT 0,
    fecha TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lecturas_medidor_fecha ON lecturas_iot(medidor_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_lecturas_fecha ON lecturas_iot(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_medidores_radiobase ON medidores(radiobase_id);
CREATE INDEX IF NOT EXISTS idx_contratos_cliente ON contratos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_infra_zona ON infraestructuras(zona_id);
CREATE INDEX IF NOT EXISTS idx_preavisos_periodo ON preavisos(periodo);
