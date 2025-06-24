# libs/db.py
import sqlite3

DB_PATH = "expend_local.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_product_by_slot(key):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, precio, stock, slot FROM productos WHERE slot = ?", (key,))
        row = cursor.fetchone()
        return dict(row) if row else None

    finally:
        conn.close()
