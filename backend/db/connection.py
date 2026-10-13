"""Acceso a la base SQLite usada como caché local."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from backend.core.config import DB_PATH


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Abre una conexión, confirma los cambios si todo salió bien y la cierra."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
