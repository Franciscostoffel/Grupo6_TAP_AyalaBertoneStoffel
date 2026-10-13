"""Fondos comunes de inversión normalizados (tabla fci_funds)."""

from __future__ import annotations

from backend.core.config import FUND_SOURCE_NAME
from backend.db.connection import get_connection


def save_fund(
    nombre: str,
    banco: str | None,
    tipo: str,
    horizonte: str | None,
    tna_estimada: float | None,
    rendimiento_1d: float | None,
    rendimiento_30d: float | None,
    vcp: float | None,
    fecha_datos: str | None,
    fecha_vcp: str | None,
    depositaria: str | None,
    gerente: str | None,
    gestora: str | None,
    minimo: float | None,
    plazo_liq: int | None,
):
    """Guarda un fondo normalizado; hay una fila por nombre base del fondo."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO fci_funds (
                nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
                rendimiento_30d, vcp,
                fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo,
                plazo_liq, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
            nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
            rendimiento_30d, vcp,
            fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo, plazo_liq
        ))


def clear_all():
    """Borra el catálogo de fondos antes de cargar una sincronización nueva."""
    with get_connection() as conn:
        conn.execute("DELETE FROM fci_funds")


def get_funds() -> list[dict]:
    """Devuelve los fondos con rendimiento a 30 días, del mejor al peor."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
                   rendimiento_30d, vcp,
                   fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo,
                   plazo_liq
            FROM fci_funds
            WHERE rendimiento_30d IS NOT NULL
            ORDER BY rendimiento_30d DESC
        """).fetchall()

    return [
        {
            "nombre": row[0],
            "banco": row[1],
            "tipo": row[2],
            "horizonte": row[3],
            "tna": row[4],
            "rendimiento_1d": row[5],
            "rendimiento_30d": row[6],
            "vcp": row[7],
            "fecha_datos": row[8],
            "fecha_vcp": row[9],
            "depositaria": row[10],
            "gerente": row[11],
            "gestora": row[12],
            "minimo": row[13],
            "plazo_liq": row[14],
            "garantizado": False,
            "fuente": FUND_SOURCE_NAME,
        }
        for row in rows
    ]
