"""Cliente de ArgentinaDatos: tasas de plazo fijo por entidad."""

from __future__ import annotations

import httpx

from backend.core.config import FIXED_DEPOSIT_API_URL


async def fetch_fixed_deposits(client: httpx.AsyncClient) -> list[dict] | None:
    """Devuelve las entidades publicadas, o None si la respuesta no fue un 200."""
    response = await client.get(FIXED_DEPOSIT_API_URL)
    response.raise_for_status()
    if response.status_code != 200:
        return None
    return response.json()
