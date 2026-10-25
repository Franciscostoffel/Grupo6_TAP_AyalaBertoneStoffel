"""Conexión a PostgreSQL usando la URL configurada en el entorno."""

import psycopg

from backend.core.config import DATABASE_URL


def get_connection():
    """Abre una conexión a PostgreSQL.

    Quien la usa debe llamar a conn.commit() si guardó algo y siempre a
    conn.close() al terminar.
    """
    return psycopg.connect(DATABASE_URL)
