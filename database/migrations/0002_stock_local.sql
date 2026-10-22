-- Stock local de la maquina. El stock vive aca y se sincroniza con la api cada X segundos:
--  - pull: datos del slot (producto, precio, fila/columna) y reposiciones pendientes
--  - push: stock local + reposiciones aplicadas
CREATE TABLE IF NOT EXISTS stock_slots (
    slot_num INTEGER PRIMARY KEY,
    slot_id INTEGER UNIQUE,              -- id del slot en la api
    producto_id INTEGER,
    stock INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 0,
    precio REAL NOT NULL DEFAULT 0,
    precio_oferta REAL,
    fila INTEGER,
    columna INTEGER,
    activo BOOLEAN NOT NULL DEFAULT 1,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_sync TIMESTAMP                 -- ultimo push exitoso a la api
);

-- Reposiciones (R suma, A ajuste absoluto) ya aplicadas al stock local.
-- Evita aplicar dos veces la misma reposicion si falla la confirmacion a la api.
CREATE TABLE IF NOT EXISTS reposiciones_aplicadas (
    reposicion_id INTEGER PRIMARY KEY,   -- id de la reposicion en la api
    slot_num INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    stock_anterior INTEGER NOT NULL,
    stock_resultante INTEGER NOT NULL,
    confirmada BOOLEAN NOT NULL DEFAULT 0,
    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
