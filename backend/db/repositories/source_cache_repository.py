"""Registro de la última sincronización de cada fuente (tabla source_cache)."""

import time

from backend.core.config import CACHE_TTL_SECONDS, SOURCE_FIXED_DEPOSITS, SOURCE_FUNDS
from backend.db.connection import get_connection


def mark_source_synced(source: str):
    """Registra que una fuente externa se actualizó correctamente."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO source_cache (fuente, synced_at)
            VALUES (?, CURRENT_TIMESTAMP)
            ON CONFLICT(fuente) DO UPDATE SET synced_at = excluded.synced_at
        """, (source,))


def investment_cache_is_fresh() -> bool:
    """Indica si las dos fuentes se sincronizaron dentro del tiempo de caché."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT fuente, synced_at
            FROM source_cache
            WHERE fuente IN (?, ?)
        """, (SOURCE_FIXED_DEPOSITS, SOURCE_FUNDS)).fetchall()

    if len(rows) != 2:
        return False
    return all(
        (time.time() - time.mktime(time.strptime(
            synced_at, "%Y-%m-%d %H:%M:%S"
        ))) < CACHE_TTL_SECONDS
        for _, synced_at in rows
    )
