"""Elige qué tasa de plazo fijo corresponde al plazo que pidió el usuario."""

# La tasa general que publica cada banco es la del plazo fijo a 30 días.
DIAS_TASA_GENERAL = 30


def choose_rate_for_term(tasa_general: float, rangos: list[dict], plazo: int) -> tuple[float, str]:
    """Devuelve la TNA que corresponde al plazo y un texto que explica de dónde salió.

    Los bancos publican tasas para algunos plazos (por ejemplo 60, 90 y 365 días).
    1. Si alguno de esos rangos incluye el plazo del usuario, se usa esa tasa.
    2. Si no, se usa la del plazo publicado más cercano por debajo.
       La tasa general cuenta como la de 30 días.

    Ejemplo: el usuario pide 180 días y el banco publica 60, 90 y 365 días
    -> se usa la tasa de 90 días.
    """
    # 1. ¿Hay un rango que incluya exactamente el plazo pedido?
    for rango in rangos:
        if rango["plazo_min"] <= plazo <= rango["plazo_max"]:
            return rango["tna"], f"Tasa publicada para {describir_dias(rango)}"

    # 2. Buscamos el plazo publicado más largo que no supere el pedido.
    tna_elegida = tasa_general
    dias_elegidos = DIAS_TASA_GENERAL
    for rango in rangos:
        if dias_elegidos < rango["plazo_max"] < plazo:
            tna_elegida = rango["tna"]
            dias_elegidos = rango["plazo_max"]

    if dias_elegidos == plazo:
        return tna_elegida, f"Tasa publicada para {plazo} días"
    return tna_elegida, f"Tasa de {dias_elegidos} días (el banco no publica una para {plazo} días)"


def describir_dias(rango: dict) -> str:
    """{"plazo_min": 60, "plazo_max": 89} -> "60 a 89 días"."""
    if rango["plazo_min"] == rango["plazo_max"]:
        return f"{rango['plazo_min']} días"
    return f"{rango['plazo_min']} a {rango['plazo_max']} días"
