import uuid
from contextlib import closing
from database.conn import connect
from services import stock_service

SIN_STOCK_MESSAGE = "No se dispone de stock para este slot"
NOW_UTC = "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"


class VentaError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.message = message
        self.status = status


def _to_dict(row):
    return dict(row) if row is not None else None


def get_venta(venta_id):
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM ventas_locales WHERE id = ?", (venta_id,)).fetchone()
    return _to_dict(row)


def crear_venta(slot_num):
    """Registra una venta pendiente (P) en la maquina, sin depender de la api."""
    slot = stock_service.get_slot(slot_num)
    # Manda siempre el stock local (la sincronizacion la hace otro proceso):
    # un slot que todavia no esta en la tabla local no tiene stock
    if slot is None or slot["stock"] <= 0:
        raise VentaError(SIN_STOCK_MESSAGE)
    if not slot["activo"] or slot["producto_id"] is None:
        raise VentaError("Slot sin producto asignado")

    precio = slot["precio_oferta"] if (slot["precio_oferta"] or 0) > 0 else slot["precio"]
    if not precio or precio <= 0:
        raise VentaError("Slot sin precio asignado")

    with closing(connect()) as conn, conn:
        cur = conn.execute(
            """INSERT INTO ventas_locales (uuid, slot_num, producto_id, precio_venta)
               VALUES (?, ?, ?, ?)""",
            (str(uuid.uuid4()), slot_num, slot["producto_id"], precio),
        )
        venta_id = cur.lastrowid

    venta = get_venta(venta_id)
    venta["config"] = {"fila": slot["fila"], "columna": slot["columna"]}
    return venta


def tomar_venta(venta_id):
    """Pasa la venta de P a E (en proceso) reservando stock, en una sola sentencia atomica.

    Una venta en proceso cuenta como stock reservado: dos cobros simultaneos
    no pueden vender la misma ultima unidad.
    """
    with closing(connect()) as conn, conn:
        cur = conn.execute(
            f"""UPDATE ventas_locales
                SET estado = 'E', fecha_actualizacion = {NOW_UTC}
                WHERE id = :id AND estado = 'P'
                  AND (SELECT stock FROM stock_slots s WHERE s.slot_num = ventas_locales.slot_num)
                      > (SELECT COUNT(*) FROM ventas_locales v
                         WHERE v.slot_num = ventas_locales.slot_num AND v.estado = 'E')""",
            {"id": venta_id},
        )
        if cur.rowcount == 1:
            return

    venta = get_venta(venta_id)
    if venta is None:
        raise VentaError("Venta no encontrada", 404)
    if venta["estado"] != "P":
        raise VentaError("Venta ya fue procesada")
    finalizar_venta(venta_id, "C", notas=SIN_STOCK_MESSAGE)
    raise VentaError(SIN_STOCK_MESSAGE)


def finalizar_venta(venta_id, estado, metodo_pago=None, notas=None):
    """Estado final (A, R, C). Queda pendiente de sincronizar con la api."""
    with closing(connect()) as conn, conn:
        conn.execute(
            f"""UPDATE ventas_locales
                SET estado = ?, metodo_pago = COALESCE(?, metodo_pago), notas = ?,
                    fecha_actualizacion = {NOW_UTC}, sincronizada = 0
                WHERE id = ?""",
            (estado, metodo_pago, notas, venta_id),
        )
    return get_venta(venta_id)


def list_ventas(limit=50):
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM ventas_locales ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
