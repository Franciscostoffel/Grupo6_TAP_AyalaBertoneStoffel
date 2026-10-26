"""Crea las tablas de PostgreSQL si todavía no existen."""

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
    """Crea las tablas de inversiones, usuarios y sesiones.

    - rates: tasa general de plazo fijo de cada banco.
    - fixed_deposit_terms: tasa de cada rango de días de cada banco.
    - fci_funds: fondos comunes de inversión.
    - bonds: letras y bonos del Tesoro (tasa fija y CER).
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

    # tna y tea solo existen en los de tasa fija; tir solo en los CER.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bonds (
            ticker TEXT PRIMARY KEY,
            tipo TEXT NOT NULL,
            precio REAL NOT NULL,
            tna REAL,
            tea REAL,
            tir REAL,
            fecha_vencimiento DATE NOT NULL
        )
    """)

    create_auth_tables(cursor)

    conn.commit()
    conn.close()


def create_auth_tables(cursor):
    """Tablas propias de autenticación, también compatibles con PostgreSQL local."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email TEXT NOT NULL CONSTRAINT users_email_key UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT users_email_normalized CHECK (email = lower(btrim(email)))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            token_hash TEXT PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMPTZ NOT NULL,
            CHECK (expires_at > created_at)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS user_sessions_user_id_idx ON user_sessions (user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS user_sessions_expires_at_idx ON user_sessions (expires_at)")
    # El dueño de las tablas (conexión del backend) conserva acceso. Sin políticas
    # públicas, la Data API de Supabase no puede leer usuarios ni sesiones.
    cursor.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    cursor.execute("ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY")
    cursor.execute("REVOKE ALL ON users, user_sessions FROM PUBLIC")
    cursor.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                REVOKE ALL ON users, user_sessions FROM anon;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                REVOKE ALL ON users, user_sessions FROM authenticated;
            END IF;
        END $$
    """)


def agregar_columnas_faltantes(cursor, tabla, columnas):
    """Agrega a la tabla las columnas de la lista que todavía no tiene."""
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (tabla,),
    )
    columnas_existentes = {fila[0] for fila in cursor.fetchall()}

    for nombre, definicion in columnas:
        if nombre not in columnas_existentes:
            cursor.execute(
                f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"
            )
