"""Descarga las letras y bonos del Tesoro y los guarda en la base de datos."""

import httpx

from backend.clients import argentinadatos_client
from backend.core.config import SOURCE_BONDS
from backend.db.repositories import bond_repository, source_cache_repository
from backend.domain.bonds import normalize_cer_bond, normalize_fixed_rate_bill


async def sync_bonds(client: httpx.AsyncClient):
    """Reemplaza los bonos guardados por los que publica hoy la fuente.

    Si algo falla, se muestra el error y quedan los datos anteriores.
    """
    try:
        letras = await argentinadatos_client.fetch_fixed_rate_bills(client)
        bonos_cer = await argentinadatos_client.fetch_cer_bonds(client)

        # Primero se limpian todos; así, si alguno viene roto, no se borra nada.
        bonos = []
        for letra in letras:
            bonos.append(normalize_fixed_rate_bill(letra))
        for bono in bonos_cer:
            bonos.append(normalize_cer_bond(bono))

        bond_repository.clear_all()
        for bono in bonos:
            if bono is not None:  # None = datos no confiables
                bond_repository.save_bond(bono)
        source_cache_repository.mark_source_synced(SOURCE_BONDS)
    except Exception as e:
        print(f"[JOB ERROR] Bonos: {e}")
