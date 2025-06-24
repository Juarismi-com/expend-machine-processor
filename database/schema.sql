CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL
)

CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maquina_id TEXT NOT NULL,
    slot_num INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 0,
    precio REAL NOT NULL DEFAULT 0.0,
    precio_oferta REAL,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE (maquina_id, slot_num)
);

CREATE TABLE IF NOT EXISTS slot_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_num INTEGER NOT NULL UNIQUE,
    fila INTEGER NOT NULL,
    columna INTEGER NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    maquina_id TEXT NOT NULL,
    precio_venta REAL NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    metodo_pago TEXT,
    notas TEXT,

    FOREIGN KEY (slot_id) REFERENCES slots(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);