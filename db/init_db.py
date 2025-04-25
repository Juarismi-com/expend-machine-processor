import sqlite3

conn = sqlite3.connect("expend_local.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL,
    stock INTEGER,
    slot INTEGER
    column INTEGER
)
""")

conn.commit()
conn.close()