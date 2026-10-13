"""Tasas generales y plazos de plazo fijo (tablas rates y fixed_deposit_terms)."""

from __future__ import annotations

from backend.core.config import FIXED_DEPOSIT_TYPE
from backend.db.connection import get_connection


def save_rate(
    nombre: str,
    tipo: str,
    tna: float,
    fecha_datos: str | None = None,
):
    """Guarda la tasa general de plazo fijo de un banco."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO rates (
                nombre, tipo, tna, garantizado, fuente, fecha_datos, updated_at
            )
            VALUES (?, ?, ?, 1, 'ArgentinaDatos', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(nombre) DO UPDATE SET
                tipo = excluded.tipo,
                tna = excluded.tna,
                fecha_datos = excluded.fecha_datos,
                updated_at = CURRENT_TIMESTAMP
        """, (nombre, tipo, tna, fecha_datos))


def save_term(banco: str, plazo_min: int, plazo_max: int, tna: float):
    """Guarda la tasa de un rango de días de plazo fijo de un banco."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO fixed_deposit_terms
                (banco, plazo_min_dias, plazo_max_dias, tna, fecha_datos)
            VALUES (?, ?, ?, ?, CURRENT_DATE)
            ON CONFLICT(banco, plazo_min_dias, plazo_max_dias) DO UPDATE SET
                tna = excluded.tna,
                fecha_datos = excluded.fecha_datos
        """, (banco, plazo_min, plazo_max, tna))


def clear_all():
    """Borra los plazos fijos antes de cargar una sincronización nueva."""
    with get_connection() as conn:
        conn.execute("DELETE FROM rates WHERE tipo = ?", (FIXED_DEPOSIT_TYPE,))
        conn.execute("DELETE FROM fixed_deposit_terms")


def get_rates() -> list[dict]:
    """Devuelve las tasas generales con TNA positiva."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT nombre, tipo, tna, garantizado, fuente, fecha_datos
            FROM rates
            WHERE tna > 0
        """).fetchall()

    return [
        {
            "nombre": row[0],
            "banco": row[0] if row[1] == FIXED_DEPOSIT_TYPE else None,
            "tipo": row[1],
            "tna": row[2],
            "garantizado": bool(row[3]),
            "fuente": row[4],
            "fecha_datos": row[5],
        }
        for row in rows
    ]


def get_terms() -> list[dict]:
    """Devuelve los plazos de cada banco ordenados por banco y días."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT banco, plazo_min_dias, plazo_max_dias, tna, fecha_datos
            FROM fixed_deposit_terms
            ORDER BY banco, plazo_min_dias
        """).fetchall()

    return [
        {
            "banco": row[0],
            "plazo_min": row[1],
            "plazo_max": row[2],
            "tna": row[3],
            "fecha_datos": row[4],
        }
        for row in rows
    ]
