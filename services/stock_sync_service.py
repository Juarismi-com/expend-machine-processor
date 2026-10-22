import logging
import threading
from contextlib import closing

import requests

import env
from env import API_URL, MACHINE_ID
from database.conn import connect

logger = logging.getLogger(__name__)

STOCK_SYNC_INTERVAL = getattr(env, "STOCK_SYNC_INTERVAL", 60)  # segundos
SYNC_TIMEOUT = 15
VENTAS_POR_LOTE = 200
# Ventas P/E sin terminar despues de este tiempo se cancelan (cliente abandono o proceso cortado)
VENTA_ABANDONADA_MINUTOS = 15

_sync_lock = threading.Lock()
_wakeup = threading.Event()
_sync_thread = None


def _sync_url():
    return f"{API_URL}/maquinas/{MACHINE_ID}/stock-sync"


def _pull_remoto():
    res = requests.get(_sync_url(), timeout=SYNC_TIMEOUT)
    res.raise_for_status()
    return res.json()


def _aplicar_remoto(conn, data):
    """Actualiza los datos del slot que administra la api y aplica las reposiciones pendientes.

    El stock NO se pisa con el remoto: solo se toma el remoto la primera vez que
    aparece el slot (carga inicial). Despues solo cambia por ventas o reposiciones.
    La fila/columna (GPIO) se configura en el admin y siempre se toma de la api.
    """
    for slot in data.get("slots", []):
        conn.execute(
            """INSERT INTO stock_slots
                   (slot_num, slot_id, producto_id, stock, stock_minimo, precio,
                    precio_oferta, fila, columna, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(slot_num) DO UPDATE SET
                   slot_id = excluded.slot_id,
                   producto_id = excluded.producto_id,
                   stock_minimo = excluded.stock_minimo,
                   precio = excluded.precio,
                   precio_oferta = excluded.precio_oferta,
                   fila = excluded.fila,
                   columna = excluded.columna,
                   activo = excluded.activo""",
            (
                slot["slot_num"],
                slot.get("slot_id"),
                slot.get("producto_id"),
                max(0, int(slot.get("stock") or 0)),
                slot.get("stock_minimo") or 0,
                float(slot.get("precio") or 0),
                float(slot["precio_oferta"]) if slot.get("precio_oferta") is not None else None,
                slot.get("fila"),
                slot.get("columna"),
                1 if slot.get("activo", True) else 0,
            ),
        )

    aplicadas = 0
    for rep in data.get("reposiciones", []):
        ya_aplicada = conn.execute(
            "SELECT 1 FROM reposiciones_aplicadas WHERE reposicion_id = ?", (rep["id"],)
        ).fetchone()
        if ya_aplicada:
            continue

        row = conn.execute(
            "SELECT stock FROM stock_slots WHERE slot_num = ?", (rep["slot_num"],)
        ).fetchone()
        if row is None:
            logger.warning("Reposicion %s para slot %s inexistente localmente", rep["id"], rep["slot_num"])
            continue

        stock_anterior = row["stock"]
        cantidad = int(rep["cantidad"])
        stock_resultante = cantidad if rep.get("tipo") == "A" else stock_anterior + cantidad
        stock_resultante = max(0, stock_resultante)

        conn.execute(
            """UPDATE stock_slots SET stock = ?, fecha_actualizacion = CURRENT_TIMESTAMP
               WHERE slot_num = ?""",
            (stock_resultante, rep["slot_num"]),
        )
        conn.execute(
            """INSERT INTO reposiciones_aplicadas
                   (reposicion_id, slot_num, tipo, cantidad, stock_anterior, stock_resultante)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (rep["id"], rep["slot_num"], rep.get("tipo", "R"), cantidad, stock_anterior, stock_resultante),
        )
        aplicadas += 1
        logger.info(
            "Reposicion %s aplicada: slot=%s tipo=%s cantidad=%s stock %s -> %s",
            rep["id"], rep["slot_num"], rep.get("tipo"), cantidad, stock_anterior, stock_resultante,
        )

    return aplicadas


def _cancelar_abandonadas(conn):
    with conn:
        cur = conn.execute(
            f"""UPDATE ventas_locales
                SET estado = 'C', sincronizada = 0,
                    notas = CASE estado WHEN 'E' THEN 'Interrumpida durante el cobro, revisar' ELSE 'Abandonada' END,
                    fecha_actualizacion = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                WHERE estado IN ('P', 'E')
                  AND COALESCE(fecha_actualizacion, fecha)
                      < strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-{VENTA_ABANDONADA_MINUTOS} minutes')"""
        )
    return cur.rowcount


def _push_ventas(conn):
    """Sube las ventas terminadas (A, R, C) que la api todavia no tiene. Idempotente por uuid."""
    _cancelar_abandonadas(conn)
    total = 0
    while True:
        rows = conn.execute(
            """SELECT uuid, slot_num, producto_id, precio_venta, estado, metodo_pago, notas, fecha
               FROM ventas_locales
               WHERE sincronizada = 0 AND estado IN ('A', 'R', 'C')
               ORDER BY id LIMIT ?""",
            (VENTAS_POR_LOTE,),
        ).fetchall()
        if not rows:
            return total

        res = requests.post(
            f"{API_URL}/maquinas/{MACHINE_ID}/ventas-sync",
            json={"ventas": [dict(r) for r in rows]},
            timeout=SYNC_TIMEOUT,
        )
        res.raise_for_status()

        with conn:
            conn.executemany(
                "UPDATE ventas_locales SET sincronizada = 1, remote_id = ? WHERE uuid = ?",
                [(v.get("id"), v["uuid"]) for v in res.json()],
            )
        total += len(rows)
        if len(rows) < VENTAS_POR_LOTE:
            return total


def _push_local(conn):
    """Envia el stock local y confirma las reposiciones aplicadas que la api aun no conoce."""
    slots = [
        {"slot_num": r["slot_num"], "stock": r["stock"]}
        for r in conn.execute("SELECT slot_num, stock FROM stock_slots")
    ]
    pendientes = [
        {"id": r["reposicion_id"], "stock_resultante": r["stock_resultante"]}
        for r in conn.execute(
            "SELECT reposicion_id, stock_resultante FROM reposiciones_aplicadas WHERE confirmada = 0"
        )
    ]

    res = requests.put(
        _sync_url(),
        json={"slots": slots, "reposiciones_aplicadas": pendientes},
        timeout=SYNC_TIMEOUT,
    )
    res.raise_for_status()

    with conn:
        if pendientes:
            conn.executemany(
                "UPDATE reposiciones_aplicadas SET confirmada = 1 WHERE reposicion_id = ?",
                [(p["id"],) for p in pendientes],
            )
        conn.execute("UPDATE stock_slots SET fecha_sync = CURRENT_TIMESTAMP")

    return len(slots), len(pendientes)


def sync_stock():
    """Un ciclo completo: push de ventas, pull (slots + reposiciones) y push (stock local).

    No bloquea: si ya hay un sync en curso retorna {"en_curso": True} sin esperar.
    Las llamadas http se hacen fuera de transacciones, las ventas siguen operando durante el sync.
    """
    if not _sync_lock.acquire(blocking=False):
        return {"en_curso": True}

    try:
        with closing(connect()) as conn:
            return _sync(conn)
    finally:
        _sync_lock.release()


def _sync(conn):
    ventas = 0
    try:
        ventas = _push_ventas(conn)
    except requests.exceptions.HTTPError as e:
        # una venta rechazada por la api no debe frenar el sync de stock
        logger.error("La api rechazo el push de ventas: %s %s", e, e.response.text if e.response is not None else "")

    data = _pull_remoto()

    with conn:
        conn.execute("BEGIN IMMEDIATE")
        reposiciones = _aplicar_remoto(conn, data)

    slots, confirmadas = _push_local(conn)

    return {
        "ventas_enviadas": ventas,
        "reposiciones_aplicadas": reposiciones,
        "slots_enviados": slots,
        "reposiciones_confirmadas": confirmadas,
    }


def _loop():
    while True:
        try:
            result = sync_stock()
            logger.info("Sync de stock OK: %s", result)
        except requests.exceptions.RequestException as e:
            # sin conexion: se sigue vendiendo con el stock local y se reintenta
            logger.warning("Sync de stock sin conexion con la api: %s", e)
        except Exception:
            logger.exception("Error inesperado en el sync de stock")
        _wakeup.wait(STOCK_SYNC_INTERVAL)
        _wakeup.clear()


def request_sync():
    """Pide un sync lo antes posible (ej. luego de una venta) sin esperar a que termine."""
    _wakeup.set()


def start_stock_sync():
    """Levanta el hilo de sincronizacion (una sola vez por proceso)."""
    global _sync_thread
    if _sync_thread is not None or not STOCK_SYNC_INTERVAL:
        return
    _sync_thread = threading.Thread(target=_loop, name="stock-sync", daemon=True)
    _sync_thread.start()
    logger.info("Sync de stock iniciado cada %s segundos", STOCK_SYNC_INTERVAL)
