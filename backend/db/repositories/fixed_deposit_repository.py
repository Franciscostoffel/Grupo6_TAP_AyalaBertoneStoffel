"""Guarda y lee los plazos fijos (tablas rates y fixed_deposit_terms)."""

from backend.core.config import FIXED_DEPOSIT_TYPE
from backend.db.connection import get_connection


def save_rate(nombre: str, tipo: str, tna: float, fecha_datos: str | None = None):
    """Guarda la tasa general de plazo fijo de un banco.

    Si el banco ya existe en la tabla, actualiza su tasa (ON CONFLICT).
    """
    conn = get_connection()
    conn.execute("""
        INSERT INTO rates (
            nombre, tipo, tna, garantizado, fuente, fecha_datos, updated_at
        )
        VALUES (%s, %s, %s, 1, 'ArgentinaDatos', %s, CURRENT_TIMESTAMP)
        ON CONFLICT(nombre) DO UPDATE SET
            tipo = excluded.tipo,
            tna = excluded.tna,
            fecha_datos = excluded.fecha_datos,
            updated_at = CURRENT_TIMESTAMP
    """, (nombre, tipo, tna, fecha_datos))
    conn.commit()
    conn.close()


def save_term(banco: str, plazo_min: int, plazo_max: int, tna: float):
    """Guarda la tasa de un rango de días (por ejemplo, de 30 a 59 días)."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO fixed_deposit_terms
            (banco, plazo_min_dias, plazo_max_dias, tna, fecha_datos)
        VALUES (%s, %s, %s, %s, CURRENT_DATE)
        ON CONFLICT(banco, plazo_min_dias, plazo_max_dias) DO UPDATE SET
            tna = excluded.tna,
            fecha_datos = excluded.fecha_datos
    """, (banco, plazo_min, plazo_max, tna))
    conn.commit()
    conn.close()


def clear_all():
    """Borra todos los plazos fijos antes de guardar los datos nuevos."""
    conn = get_connection()
    conn.execute("DELETE FROM rates WHERE tipo = %s", (FIXED_DEPOSIT_TYPE,))
    conn.execute("DELETE FROM fixed_deposit_terms")
    conn.commit()
    conn.close()


def get_rates() -> list[dict]:
    """Devuelve la tasa general de cada banco (solo las mayores a cero)."""
    conn = get_connection()
    filas = conn.execute("""
        SELECT nombre, tipo, tna, garantizado, fuente, fecha_datos
        FROM rates
        WHERE tna > 0
    """).fetchall()
    conn.close()

    tasas = []
    for fila in filas:
        nombre, tipo, tna, garantizado, fuente, fecha_datos = fila
        # En los plazos fijos el nombre guardado es el del banco.
        if tipo == FIXED_DEPOSIT_TYPE:
            banco = nombre
        else:
            banco = None
        tasas.append({
            "nombre": nombre,
            "banco": banco,
            "tipo": tipo,
            "tna": tna,
            "garantizado": bool(garantizado),
            "fuente": fuente,
            "fecha_datos": fecha_datos,
        })
    return tasas


def get_terms() -> list[dict]:
    """Devuelve los rangos de días de cada banco, ordenados por banco y plazo."""
    conn = get_connection()
    filas = conn.execute("""
        SELECT banco, plazo_min_dias, plazo_max_dias, tna, fecha_datos
        FROM fixed_deposit_terms
        ORDER BY banco, plazo_min_dias
    """).fetchall()
    conn.close()

    plazos = []
    for banco, plazo_min, plazo_max, tna, fecha_datos in filas:
        plazos.append({
            "banco": banco,
            "plazo_min": plazo_min,
            "plazo_max": plazo_max,
            "tna": tna,
            "fecha_datos": fecha_datos,
        })
    return plazos
