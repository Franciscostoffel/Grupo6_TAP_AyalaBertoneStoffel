"""Actualiza las dos fuentes externas: plazos fijos y fondos."""

import asyncio

import httpx

from backend.core.config import EXTERNAL_HTTP_TIMEOUT_SECONDS
from backend.db.repositories import source_cache_repository
from backend.services.fixed_deposit_sync import sync_fixed_deposits
from backend.services.fund_sync import sync_funds


async def sync_all_sources():
    """Descarga plazos fijos y fondos al mismo tiempo.

    Si los datos guardados tienen menos de una hora, no se descarga nada.
    """
    if source_cache_repository.investment_cache_is_fresh():
        print("[CACHE] Datos vigentes; no se consultan las APIs externas.")
        return

    print("[BACKGROUND JOB] Sincronizando plazos fijos y fondos...")
    async with httpx.AsyncClient(
        timeout=EXTERNAL_HTTP_TIMEOUT_SECONDS, verify=False
    ) as client:
        # asyncio.gather ejecuta las dos descargas en paralelo y espera a ambas.
        resultados = await asyncio.gather(
            sync_fixed_deposits(client),
            sync_funds(client),
            return_exceptions=True,
        )
        for resultado in resultados:
            if isinstance(resultado, Exception):
                print(f"[JOB ERROR] Sincronización: {resultado}")
    print("[BACKGROUND JOB] Sincronización completada.")
