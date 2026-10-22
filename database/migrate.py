import logging
import os
from contextlib import closing
from database.conn import connect

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def run_migrations():
    """Aplica en orden las migraciones de database/migrations que todavia no se ejecutaron.

    Cada archivo .sql se aplica una sola vez (queda registrado en schema_migrations),
    las ya aplicadas no se vuelven a tocar. Cada migracion corre en su propia transaccion.
    """
    with closing(connect()) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()

        applied = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
        pending = sorted(
            f for f in os.listdir(MIGRATIONS_DIR)
            if f.endswith(".sql") and f not in applied
        )

        for name in pending:
            logger.info("Aplicando migracion %s", name)
            with open(os.path.join(MIGRATIONS_DIR, name), encoding="utf8") as f:
                sql = f.read()

            name_sql = name.replace("'", "''")
            try:
                conn.executescript(
                    f"BEGIN IMMEDIATE;\n{sql}\n;"
                    f"INSERT INTO schema_migrations (name) VALUES ('{name_sql}');\nCOMMIT;"
                )
            except Exception:
                if conn.in_transaction:
                    conn.rollback()
                raise

        if pending:
            print(f"Migraciones aplicadas: {', '.join(pending)}")
        else:
            print("Base de datos al dia, sin migraciones pendientes")

        return pending
