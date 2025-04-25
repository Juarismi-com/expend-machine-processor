# libs/db.py
import sqlite3

DB_PATH = "expend_local.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def obtener_productos(key):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, precio, stock FROM productos WHERE slot = ?", (key,))
        rows = cursor.fetchone()
        return dict(row) if row else None
        #return [dict(row) for row in rows]
    finally:
        conn.close()
