import os
import sqlite3
from flask import g
import env

# Fuera del repo/ignorado por git: el stock local no debe pisarse con un git pull
DATABASE_PATH = getattr(env, "DATABASE_PATH", "db/expend_local.db")


def connect():
    """Conexion nueva, para usar fuera de un request (hilos de sync) o en servicios."""
    directory = os.path.dirname(DATABASE_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn

def get_db():
    if 'db' not in g:
        g.db = connect()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
