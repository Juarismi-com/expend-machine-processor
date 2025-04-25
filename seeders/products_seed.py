import sqlite3

conn = sqlite3.connect("expend_local.db")
cursor = conn.cursor()


cursor.executemany("INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)", [
    ("Coca", 1500.00, 10),
    ("Fanta", 20.00, 50),
    ("Listado", 35.00, 30)
])

conn.commit()
conn.close()