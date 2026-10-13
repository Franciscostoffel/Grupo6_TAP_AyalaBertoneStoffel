"""Consulta los fondos comunes de inversión a la API de CompararFondos."""

import httpx

from backend.core.config import FUNDS_API_URL


async def fetch_funds(client: httpx.AsyncClient) -> list[dict]:
    """Devuelve la lista de fondos. La API los manda dentro de la clave "funds"."""
    respuesta = await client.get(FUNDS_API_URL)
    respuesta.raise_for_status()
    return respuesta.json().get("funds", [])
