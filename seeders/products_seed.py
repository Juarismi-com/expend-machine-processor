import sqlite3

conn = sqlite3.connect("expend_local.db")
cursor = conn.cursor()

cursor.executemany("INSERT INTO productos (nombre, precio, stock, slot) VALUES (?, ?, ?, ?)", [
    ("Coca", 1500.00, 10, 1),
    ("Fanta", 20.00, 50, 2),
    ("Sprite", 35.00, 30, 3)
])

conn.commit()
conn.close()