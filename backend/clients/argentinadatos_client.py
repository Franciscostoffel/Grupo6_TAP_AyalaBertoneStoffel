"""Consulta las tasas de plazo fijo y los bonos a la API de ArgentinaDatos."""

import httpx

from backend.core.config import BILLS_API_URL, CER_BONDS_API_URL, FIXED_DEPOSIT_API_URL


async def fetch_fixed_deposits(client: httpx.AsyncClient) -> list[dict] | None:
    """Devuelve la lista de entidades con sus tasas.

    Si la API responde con error, raise_for_status() lanza una excepción.
    Si responde bien pero con un código distinto de 200, devuelve None.
    """
    respuesta = await client.get(FIXED_DEPOSIT_API_URL)
    respuesta.raise_for_status()
    if respuesta.status_code != 200:
        return None
    return respuesta.json()


async def fetch_fixed_rate_bills(client: httpx.AsyncClient) -> list[dict]:
    """Devuelve las letras y bonos a tasa fija (LECAP y BONCAP) con su TNA y TEA.

    La API los manda dentro de la clave "letras".
    """
    respuesta = await client.get(BILLS_API_URL)
    respuesta.raise_for_status()
    return respuesta.json().get("letras", [])


async def fetch_cer_bonds(client: httpx.AsyncClient) -> list[dict]:
    """Devuelve los bonos que ajustan por CER con su TIR real.

    La API los manda dentro de la clave "bonos".
    """
    respuesta = await client.get(CER_BONDS_API_URL)
    respuesta.raise_for_status()
    return respuesta.json().get("bonos", [])
