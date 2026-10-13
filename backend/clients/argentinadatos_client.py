"""Consulta las tasas de plazo fijo a la API de ArgentinaDatos."""

import httpx

from backend.core.config import FIXED_DEPOSIT_API_URL


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
