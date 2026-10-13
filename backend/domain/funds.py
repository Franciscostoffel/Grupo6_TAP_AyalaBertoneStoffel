"""Reglas para depurar el catálogo de fondos publicado por la fuente."""

import re

CLASE_A_PATTERN = re.compile(r"\bCLASE\s+A\b")


def select_one_class_per_fund(fondos: list[dict]) -> list[dict]:
    """Deja una sola clase por fondo, prefiriendo la Clase A cuando existe.

    Se descartan los fondos sin nombre o sin rendimiento a 30 días.
    """
    fondos_por_nombre: dict[str, dict] = {}
    for item in fondos:
        nombre = str(item.get("nombre") or "").strip()
        nombre_base = str(item.get("nombreBase") or nombre).strip()
        if not nombre or item.get("r30") is None:
            continue

        actual = fondos_por_nombre.get(nombre_base)
        es_clase_a = _is_clase_a(nombre)
        actual_es_clase_a = bool(actual and _is_clase_a(str(actual.get("nombre", ""))))
        if actual is None or (es_clase_a and not actual_es_clase_a):
            fondos_por_nombre[nombre_base] = item

    return list(fondos_por_nombre.values())


def _is_clase_a(nombre: str) -> bool:
    return bool(CLASE_A_PATTERN.search(nombre.upper()))
