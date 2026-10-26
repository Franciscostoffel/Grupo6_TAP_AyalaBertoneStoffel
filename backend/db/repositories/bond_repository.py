"""Guarda y lee las letras y bonos (tabla bonds)."""

from backend.db.connection import get_connection


def save_bond(bono: dict):
    """Guarda un bono. Si ya existe uno con el mismo ticker, lo actualiza."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO bonds (ticker, tipo, precio, tna, tea, tir, fecha_vencimiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(ticker) DO UPDATE SET
            tipo = excluded.tipo,
            precio = excluded.precio,
            tna = excluded.tna,
            tea = excluded.tea,
            tir = excluded.tir,
            fecha_vencimiento = excluded.fecha_vencimiento
    """, (
        bono["ticker"],
        bono["tipo"],
        bono["precio"],
        bono["tna"],
        bono["tea"],
        bono["tir"],
        bono["fecha_vencimiento"],
    ))
    conn.commit()
    conn.close()


def clear_all():
    """Borra todos los bonos antes de guardar los datos nuevos."""
    conn = get_connection()
    conn.execute("DELETE FROM bonds")
    conn.commit()
    conn.close()


def get_bonds() -> list[dict]:
    """Devuelve los bonos ordenados del que vence antes al que vence después."""
    conn = get_connection()
    filas = conn.execute("""
        SELECT ticker, tipo, precio, tna, tea, tir, fecha_vencimiento
        FROM bonds
        ORDER BY fecha_vencimiento, ticker
    """).fetchall()
    conn.close()

    bonos = []
    for ticker, tipo, precio, tna, tea, tir, fecha_vencimiento in filas:
        bonos.append({
            "ticker": ticker,
            "tipo": tipo,
            "precio": precio,
            "tna": tna,
            "tea": tea,
            "tir": tir,
            "fecha_vencimiento": fecha_vencimiento,
        })
    return bonos
