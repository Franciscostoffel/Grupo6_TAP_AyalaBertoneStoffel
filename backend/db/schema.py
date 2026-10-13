"""Creación de tablas y migración de columnas agregadas en versiones previas."""

import sqlite3

from backend.db.connection import get_connection

# Columnas que pueden faltar en bases creadas con versiones anteriores.
RATES_MIGRATIONS = (
    ("garantizado", "INTEGER NOT NULL DEFAULT 1"),
    ("fuente", "TEXT NOT NULL DEFAULT 'ArgentinaDatos'"),
    ("fecha_datos", "TEXT"),
)

FCI_MIGRATIONS = (
    ("banco", "TEXT"),
    ("rendimiento_30d", "REAL"),
    ("rendimiento_1d", "REAL"),
    ("fecha_vcp", "TEXT"),
    ("depositaria", "TEXT"),
    ("gerente", "TEXT"),
    ("gestora", "TEXT"),
    ("minimo", "REAL"),
    ("plazo_liq", "INTEGER"),
)


def init_db():
    """Crea la caché local usada por la API y agrega columnas faltantes."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rates (
                nombre TEXT PRIMARY KEY,
                tipo TEXT,
                tna REAL,
                garantizado INTEGER NOT NULL DEFAULT 1,
                fuente TEXT NOT NULL DEFAULT 'ArgentinaDatos',
                fecha_datos TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixed_deposit_terms (
                banco TEXT NOT NULL,
                plazo_min_dias INTEGER NOT NULL,
                plazo_max_dias INTEGER NOT NULL,
                tna REAL NOT NULL,
                fecha_datos TEXT,
                PRIMARY KEY (banco, plazo_min_dias, plazo_max_dias)
            )
        """)
        _add_missing_columns(cursor, "rates", RATES_MIGRATIONS)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fci_funds (
                nombre TEXT PRIMARY KEY,
                banco TEXT,
                tipo TEXT NOT NULL,
                horizonte TEXT,
                tna_estimada REAL,
                rendimiento_1d REAL,
                rendimiento_30d REAL,
                vcp REAL,
                fecha_datos TEXT,
                fecha_vcp TEXT,
                depositaria TEXT,
                gerente TEXT,
                gestora TEXT,
                minimo REAL,
                plazo_liq INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_cache (
                fuente TEXT PRIMARY KEY,
                synced_at TIMESTAMP NOT NULL
            )
        """)
        _add_missing_columns(cursor, "fci_funds", FCI_MIGRATIONS)


def _add_missing_columns(
    cursor: sqlite3.Cursor,
    table: str,
    columns: tuple[tuple[str, str], ...],
):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    for column, definition in columns:
        if column not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
