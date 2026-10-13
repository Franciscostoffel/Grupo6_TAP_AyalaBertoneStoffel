"""Nivel de riesgo de cada producto y si es apto para el usuario."""

# Cada nivel tiene un número para poder compararlos: bajo < moderado < alto.
RISK_LEVELS = {"bajo": 0, "moderado": 1, "alto": 2}

# El plazo fijo tiene la tasa asegurada, por eso siempre es de riesgo bajo.
FIXED_DEPOSIT_RISK = "bajo"


def fund_risk(tipo: str, horizonte: str | None) -> str:
    """Clasifica un fondo según su tipo y horizonte.

    - MM (mercado de dinero) o RFP (renta fija) de corto plazo -> bajo
    - RFP de más plazo, MIX (mixto), MULTI (multimercado), USD -> moderado
    - Cualquier otro, por ejemplo renta variable (acciones) -> alto
    """
    tipo = tipo.upper()
    horizonte = (horizonte or "").lower()

    if tipo == "MM":
        return "bajo"
    if tipo == "RFP" and horizonte == "corto":
        return "bajo"
    if tipo in ["RFP", "MIX", "MULTI", "USD"]:
        return "moderado"
    return "alto"


def is_valid_risk(riesgo: str) -> bool:
    """El riesgo tiene que ser "bajo", "moderado" o "alto"."""
    return riesgo in RISK_LEVELS


def risk_matches(riesgo_usuario: str, riesgo_producto: str) -> bool:
    """Un producto es apto si su riesgo es igual o menor al que acepta el usuario.

    Ejemplo: quien acepta "moderado" puede ver productos "bajo" y "moderado".
    """
    nivel_producto = RISK_LEVELS.get(riesgo_producto, 2)
    nivel_usuario = RISK_LEVELS.get(riesgo_usuario, 0)
    return nivel_producto <= nivel_usuario
