"""Identificación del banco a partir de los textos que publican las fuentes."""

from __future__ import annotations

import unicodedata

from backend.core.config import BANCOS_SELECCIONADOS, FUND_BANK_ALIASES


def bank_for_entity(entidad: str) -> str | None:
    """Devuelve el banco de una entidad de plazo fijo, si está entre los elegidos."""
    entidad_mayuscula = entidad.upper()
    return next(
        (
            nombre_banco
            for clave, nombre_banco in BANCOS_SELECCIONADOS.items()
            if clave in entidad_mayuscula
        ),
        None,
    )


def bank_for_fund(item: dict) -> str | None:
    """Busca el banco asociado a un fondo en su nombre, administradora o gestores."""
    text = _without_accents(
        " ".join(
            str(item.get(field, "")) for field in
            ("nombre", "administradora", "depositaria")
        )
    ).upper()
    text += " " + " ".join(
        str(item.get(field, "")) for field in ("gerente", "gestora")
    ).upper()
    for key, bank in {**BANCOS_SELECCIONADOS, **FUND_BANK_ALIASES}.items():
        if _without_accents(key).upper() in text:
            return bank
    return None


def _without_accents(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
