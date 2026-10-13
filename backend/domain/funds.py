"""Limpia el listado de fondos que publica la fuente."""

import re


def select_one_class_per_fund(fondos: list[dict]) -> list[dict]:
    """Deja una sola clase por fondo, prefiriendo la "Clase A" si existe.

    Un mismo fondo se publica varias veces (Clase A, Clase B, ...) con el mismo
    "nombreBase". Nos quedamos con una sola. También se descartan los fondos
    sin nombre o sin rendimiento de los últimos 30 días ("r30").
    """
    elegidos = {}  # nombreBase -> fondo elegido

    for fondo in fondos:
        nombre = str(fondo.get("nombre") or "").strip()
        nombre_base = str(fondo.get("nombreBase") or nombre).strip()
        if not nombre or fondo.get("r30") is None:
            continue

        if nombre_base not in elegidos:
            elegidos[nombre_base] = fondo
        elif es_clase_a(nombre) and not es_clase_a(str(elegidos[nombre_base].get("nombre", ""))):
            elegidos[nombre_base] = fondo

    return list(elegidos.values())


def es_clase_a(nombre: str) -> bool:
    """True si el nombre contiene "CLASE A" como palabra (no "CLASE AB")."""
    return re.search(r"\bCLASE\s+A\b", nombre.upper()) is not None
