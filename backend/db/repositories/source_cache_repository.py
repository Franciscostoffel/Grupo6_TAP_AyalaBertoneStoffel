"""Registra cuándo se actualizó cada fuente externa (tabla source_cache)."""

import time

from backend.core.config import CACHE_TTL_SECONDS, SOURCE_FIXED_DEPOSITS, SOURCE_FUNDS
from backend.db.connection import get_connection


def mark_source_synced(fuente: str):
    """Anota que la fuente se actualizó bien en este momento."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO source_cache (fuente, synced_at)
        VALUES (%s, CURRENT_TIMESTAMP)
        ON CONFLICT(fuente) DO UPDATE SET synced_at = excluded.synced_at
    """, (fuente,))
    conn.commit()
    conn.close()


def investment_cache_is_fresh() -> bool:
    """Devuelve True si las dos fuentes se actualizaron hace menos de una hora."""
    conn = get_connection()
    filas = conn.execute("""
        SELECT fuente, synced_at
        FROM source_cache
        WHERE fuente IN (%s, %s)
    """, (SOURCE_FIXED_DEPOSITS, SOURCE_FUNDS)).fetchall()
    conn.close()

    # Si alguna de las dos fuentes nunca se sincronizó, hay que actualizar.
    if len(filas) != 2:
        return False

    for fuente, synced_at in filas:
        segundos_transcurridos = time.time() - synced_at.timestamp()
        if segundos_transcurridos >= CACHE_TTL_SECONDS:
            return False
    return True
