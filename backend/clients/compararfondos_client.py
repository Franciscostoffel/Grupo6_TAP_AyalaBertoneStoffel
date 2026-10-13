"""Cliente de CompararFondos: catálogo de fondos comunes de inversión (CAFCI)."""

import httpx

from backend.core.config import FUNDS_API_URL


async def fetch_funds(client: httpx.AsyncClient) -> list[dict]:
    """Devuelve la lista de fondos publicada por la fuente."""
    response = await client.get(FUNDS_API_URL)
    response.raise_for_status()
    return response.json().get("funds", [])
