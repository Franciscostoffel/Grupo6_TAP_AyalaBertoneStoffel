"""Clasificación de riesgo de los productos y compatibilidad con el perfil elegido."""

from __future__ import annotations

RISK_LEVELS = {"bajo": 0, "moderado": 1, "alto": 2}

# Los plazos fijos están garantizados, por eso siempre son de riesgo bajo.
FIXED_DEPOSIT_RISK = "bajo"


def fund_risk(tipo: str, horizonte: str | None) -> str:
    """Clasifica un fondo según el tipo de activo y el horizonte publicados.

    Mercado de dinero y renta fija corta: bajo. Renta fija de mayor horizonte,
    mixtos, multimercado y dólar: moderado. El resto (renta variable): alto.
    """
    tipo = tipo.upper()
    horizonte = (horizonte or "").lower()
    if tipo == "MM" or (tipo == "RFP" and horizonte == "corto"):
        return "bajo"
    if tipo in {"RFP", "MIX", "MULTI", "USD"}:
        return "moderado"
    return "alto"


def is_valid_risk(riesgo: str) -> bool:
    return riesgo in RISK_LEVELS


def risk_matches(selected: str, category: str) -> bool:
    """Un producto es apto si su riesgo no supera el que acepta el usuario."""
    return RISK_LEVELS.get(category, 2) <= RISK_LEVELS.get(selected, 0)
