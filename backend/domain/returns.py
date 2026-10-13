"""Fórmulas de tasas y rendimientos."""


def normalize_percentage(valor: float) -> float:
    """Algunas fuentes publican 0.35 en vez de 35. Lo pasamos siempre a porcentaje."""
    if 0 < valor < 1:
        return valor * 100
    return valor


def annualized_return_from_30d(rendimiento_30d: float | None) -> float | None:
    """Estima una TNA repitiendo 12 veces el rendimiento de los últimos 30 días.

    Ejemplo: 2% mensual -> (1,02 ^ 12 - 1) x 100 = 26,8% anual.
    """
    if rendimiento_30d is None or rendimiento_30d <= -100:
        return None
    return ((1 + rendimiento_30d / 100) ** 12 - 1) * 100


def fund_period_return_pct(rendimiento_30d: float, plazo: int) -> float:
    """Lleva el rendimiento de 30 días de un fondo al plazo que eligió el usuario.

    Ejemplo: 2% en 30 días, para 90 días -> (1,02 ^ 3 - 1) x 100 = 6,12%.
    """
    return ((1 + rendimiento_30d / 100) ** (plazo / 30) - 1) * 100


def simple_period_return_pct(tna: float, plazo: int) -> float:
    """Parte proporcional de una tasa anual. Ejemplo: 36% anual en 30 días = 2,96%."""
    return tna * plazo / 365


def fixed_deposit_gain(capital: float, tna: float, plazo: int) -> float:
    """Ganancia de un plazo fijo (interés simple): capital x tasa x días / 365."""
    return capital * (tna / 100) * (plazo / 365)
