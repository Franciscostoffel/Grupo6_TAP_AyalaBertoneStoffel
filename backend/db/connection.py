"""Conexión a la base de datos SQLite que usamos como caché local."""

import sqlite3

from backend.core.config import DB_PATH


def get_connection():
    """Abre la base de datos.

    Quien la usa debe llamar a conn.commit() si guardó algo y siempre a
    conn.close() al terminar.
    """
    return sqlite3.connect(DB_PATH)
