"""Cálculos de tasas y rendimientos."""

from __future__ import annotations


def normalize_percentage(value: float) -> float:
    """Convierte tasas publicadas como fracción (0.35) a porcentaje (35)."""
    return value * 100 if 0 < value < 1 else value


def annualized_return_from_30d(rendimiento_30d: float | None) -> float | None:
    """Estima una TNA anualizando el rendimiento de los últimos 30 días."""
    if rendimiento_30d is None or rendimiento_30d <= -100:
        return None
    return ((1 + rendimiento_30d / 100) ** 12 - 1) * 100


def fund_period_return_pct(rendimiento_30d: float, plazo: int) -> float:
    """Proyecta el rendimiento de 30 días de un fondo al plazo elegido."""
    return ((1 + rendimiento_30d / 100) ** (plazo / 30) - 1) * 100


def simple_period_return_pct(tna: float, plazo: int) -> float:
    """Rendimiento proporcional de una TNA para la cantidad de días indicada."""
    return tna * plazo / 365


def fixed_deposit_gain(capital: float, tna: float, plazo: int) -> float:
    """Ganancia de un plazo fijo con interés simple."""
    return capital * (tna / 100) * (plazo / 365)
