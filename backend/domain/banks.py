"""Reconoce a qué banco o billetera pertenece una tasa o un fondo."""

import unicodedata

from backend.core.config import BANCOS_SELECCIONADOS, SOCIEDADES_GERENTES


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
    """Devuelve el banco o billetera dueño del fondo según su sociedad gerente.

    Ejemplo: gerente "Pellegrini S.A.S.G.F.C.I." -> "Banco Nación".
    No se usa el banco "depositario" (el que guarda el dinero del fondo),
    porque un mismo banco custodia fondos de muchas empresas distintas.
    """
    gerente = quitar_acentos(str(fondo.get("gerente") or "")).upper()
    for clave, entidad in SOCIEDADES_GERENTES.items():
        if clave in gerente:
            return entidad
    return None


def quitar_acentos(texto: str) -> str:
    """Convierte "Ualá" en "Uala" para comparar sin importar los acentos."""
    texto_separado = unicodedata.normalize("NFKD", texto)
    return texto_separado.encode("ascii", "ignore").decode()
