-- Ventas registradas primero en la maquina; el sync las sube a la api cada X segundos.
-- estado: P pendiente de pago, E en proceso (cobrando/despachando), A aceptada, R rechazada, C cancelada
CREATE TABLE IF NOT EXISTS ventas_locales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- se usa como facturaNro en el POS
    uuid TEXT NOT NULL UNIQUE,              -- identifica la venta en la api (evita duplicados)
    slot_num INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    precio_venta REAL NOT NULL,
    estado TEXT NOT NULL DEFAULT 'P',
    metodo_pago TEXT,
    notas TEXT,
    fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),  -- UTC
    fecha_actualizacion TEXT,
    remote_id INTEGER,                      -- id en la api luego de sincronizar
    sincronizada BOOLEAN NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ventas_locales_sync ON ventas_locales (sincronizada, estado);
