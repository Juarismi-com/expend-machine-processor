from contextlib import closing
from database.conn import connect


def _to_dict(row):
    return dict(row) if row is not None else None


def get_slot(slot_num):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM stock_slots WHERE slot_num = ?", (slot_num,)
        ).fetchone()
    return _to_dict(row)


def list_slots():
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM stock_slots ORDER BY slot_num").fetchall()
    return [dict(r) for r in rows]


def descontar_stock(slot_num, cantidad=1):
    """Descuenta stock de forma atomica, nunca queda negativo. Retorna True si desconto."""
    with closing(connect()) as conn, conn:
        cur = conn.execute(
            """UPDATE stock_slots
               SET stock = stock - ?, fecha_actualizacion = CURRENT_TIMESTAMP
               WHERE slot_num = ? AND stock >= ?""",
            (cantidad, slot_num, cantidad),
        )
        return cur.rowcount == 1

