"""Guarda y lee los fondos comunes de inversión (tabla fci_funds)."""

from backend.core.config import FUND_SOURCE_NAME
from backend.db.connection import get_connection


def save_fund(fondo: dict):
    """Guarda un fondo. Si ya existe uno con el mismo nombre, lo actualiza.

    'fondo' es un diccionario con las mismas claves que las columnas de la tabla.
    """
    conn = get_connection()
    conn.execute("""
        INSERT INTO fci_funds (
            nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
            rendimiento_30d, vcp,
            fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo,
            plazo_liq, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT(nombre) DO UPDATE SET
            banco = excluded.banco,
            tipo = excluded.tipo,
            horizonte = excluded.horizonte,
            tna_estimada = excluded.tna_estimada,
            rendimiento_1d = excluded.rendimiento_1d,
            rendimiento_30d = excluded.rendimiento_30d,
            vcp = excluded.vcp,
            fecha_datos = excluded.fecha_datos,
            fecha_vcp = excluded.fecha_vcp,
            depositaria = excluded.depositaria,
            gerente = excluded.gerente,
            gestora = excluded.gestora,
            minimo = excluded.minimo,
            plazo_liq = excluded.plazo_liq,
            updated_at = CURRENT_TIMESTAMP
    """, (
        fondo["nombre"],
        fondo["banco"],
        fondo["tipo"],
        fondo["horizonte"],
        fondo["tna_estimada"],
        fondo["rendimiento_1d"],
        fondo["rendimiento_30d"],
        fondo["vcp"],
        fondo["fecha_datos"],
        fondo["fecha_vcp"],
        fondo["depositaria"],
        fondo["gerente"],
        fondo["gestora"],
        fondo["minimo"],
        fondo["plazo_liq"],
    ))
    conn.commit()
    conn.close()


def clear_all():
    """Borra todos los fondos antes de guardar los datos nuevos."""
    conn = get_connection()
    conn.execute("DELETE FROM fci_funds")
    conn.commit()
    conn.close()


def get_funds() -> list[dict]:
    """Devuelve los fondos que tienen rendimiento a 30 días, del mejor al peor."""
    conn = get_connection()
    filas = conn.execute("""
        SELECT nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
               rendimiento_30d, vcp,
               fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo,
               plazo_liq
        FROM fci_funds
        WHERE rendimiento_30d IS NOT NULL
        ORDER BY rendimiento_30d DESC
    """).fetchall()
    conn.close()

    fondos = []
    for fila in filas:
        fondos.append({
            "nombre": fila[0],
            "banco": fila[1],
            "tipo": fila[2],
            "horizonte": fila[3],
            "tna": fila[4],
            "rendimiento_1d": fila[5],
            "rendimiento_30d": fila[6],
            "vcp": fila[7],
            "fecha_datos": fila[8],
            "fecha_vcp": fila[9],
            "depositaria": fila[10],
            "gerente": fila[11],
            "gestora": fila[12],
            "minimo": fila[13],
            "plazo_liq": fila[14],
            # Los fondos nunca están garantizados (a diferencia del plazo fijo).
            "garantizado": False,
            "fuente": FUND_SOURCE_NAME,
        })
    return fondos
