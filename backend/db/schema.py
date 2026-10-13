"""Crea las tablas de la base de datos si todavía no existen."""

from backend.db.connection import get_connection

# Columnas que se agregaron en versiones nuevas. Si alguien tiene una base
# vieja sin estas columnas, se agregan automáticamente al iniciar.
COLUMNAS_NUEVAS_RATES = [
    ("garantizado", "INTEGER NOT NULL DEFAULT 1"),
    ("fuente", "TEXT NOT NULL DEFAULT 'ArgentinaDatos'"),
    ("fecha_datos", "TEXT"),
]

COLUMNAS_NUEVAS_FONDOS = [
    ("banco", "TEXT"),
    ("rendimiento_30d", "REAL"),
    ("rendimiento_1d", "REAL"),
    ("fecha_vcp", "TEXT"),
    ("depositaria", "TEXT"),
    ("gerente", "TEXT"),
    ("gestora", "TEXT"),
    ("minimo", "REAL"),
    ("plazo_liq", "INTEGER"),
]


def init_db():
    """Crea las cuatro tablas de la aplicación.

    - rates: tasa general de plazo fijo de cada banco.
    - fixed_deposit_terms: tasa de cada rango de días de cada banco.
    - fci_funds: fondos comunes de inversión.
    - source_cache: cuándo se actualizó por última vez cada fuente.
    """
    conn = get_connection()
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
    agregar_columnas_faltantes(cursor, "rates", COLUMNAS_NUEVAS_RATES)

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
    agregar_columnas_faltantes(cursor, "fci_funds", COLUMNAS_NUEVAS_FONDOS)

    conn.commit()
    conn.close()


def agregar_columnas_faltantes(cursor, tabla, columnas):
    """Agrega a la tabla las columnas de la lista que todavía no tiene."""
    # PRAGMA table_info devuelve una fila por columna; el nombre está en la posición 1.
    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas_existentes = []
    for fila in cursor.fetchall():
        columnas_existentes.append(fila[1])

    for nombre, definicion in columnas:
        if nombre not in columnas_existentes:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}")
