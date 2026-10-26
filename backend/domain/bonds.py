"""Limpia las letras y bonos que publica la fuente."""

from backend.core.config import BOND_TYPE_CER, BOND_TYPE_FIXED_RATE


def normalize_fixed_rate_bill(letra: dict) -> dict | None:
    """Pasa una LECAP o BONCAP al formato de la tabla bonds.

    Devuelve None si no tiene precio o si la tasa no es positiva (por ejemplo
    los duales, que la fuente publica con una tasa que no sirve para comparar).
    """
    precio = letra.get("precioArs") or 0
    tna = letra.get("tnaPorcentaje") or 0
    tea = letra.get("teaPorcentaje") or 0
    if precio <= 0 or tna <= 0 or tea <= 0:
        return None

    return {
        "ticker": letra["ticker"],
        "tipo": BOND_TYPE_FIXED_RATE,
        "precio": precio,
        "tna": tna,
        "tea": tea,
        "tir": None,
        "fecha_vencimiento": letra["fechaVencimiento"],
    }


def normalize_cer_bond(bono: dict) -> dict | None:
    """Pasa un bono CER al formato de la tabla bonds.

    Su TIR es real (por encima de la inflación): puede ser baja o negativa y
    aun así ser un dato válido. Solo se descarta si falta el precio o la TIR.
    """
    precio = bono.get("precioArs") or 0
    tir = bono.get("tirPorcentaje")
    if precio <= 0 or tir is None:
        return None

    return {
        "ticker": bono["ticker"],
        "tipo": BOND_TYPE_CER,
        "precio": precio,
        "tna": None,
        "tea": None,
        "tir": tir,
        "fecha_vencimiento": bono["fechaVencimiento"],
    }
