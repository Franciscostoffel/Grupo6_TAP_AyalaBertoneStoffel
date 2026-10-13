"""Reconoce a qué banco pertenece una tasa o un fondo a partir de su nombre."""

import unicodedata

from backend.core.config import BANCOS_SELECCIONADOS, FUND_BANK_ALIASES


def bank_for_entity(entidad: str) -> str | None:
    """Devuelve el banco de una entidad de plazo fijo, o None si no es de los elegidos.

    Ejemplo: "BANCO DE LA NACION ARGENTINA" contiene "NACION" -> "Banco Nación".
    """
    entidad_mayuscula = entidad.upper()
    for clave, nombre_banco in BANCOS_SELECCIONADOS.items():
        if clave in entidad_mayuscula:
            return nombre_banco
    return None


def bank_for_fund(fondo: dict) -> str | None:
    """Busca el banco de un fondo en su nombre, administradora, depositaria y gestores."""
    texto = quitar_acentos(
        str(fondo.get("nombre", "")) + " "
        + str(fondo.get("administradora", "")) + " "
        + str(fondo.get("depositaria", ""))
    ).upper()
    texto += " " + (
        str(fondo.get("gerente", "")) + " " + str(fondo.get("gestora", ""))
    ).upper()

    # Primero se buscan los nombres principales y después los alternativos.
    for clave, nombre_banco in BANCOS_SELECCIONADOS.items():
        if quitar_acentos(clave).upper() in texto:
            return nombre_banco
    for clave, nombre_banco in FUND_BANK_ALIASES.items():
        if quitar_acentos(clave).upper() in texto:
            return nombre_banco
    return None


def quitar_acentos(texto: str) -> str:
    """Convierte "Nación" en "Nacion" para comparar sin importar los acentos."""
    texto_separado = unicodedata.normalize("NFKD", texto)
    return texto_separado.encode("ascii", "ignore").decode()
