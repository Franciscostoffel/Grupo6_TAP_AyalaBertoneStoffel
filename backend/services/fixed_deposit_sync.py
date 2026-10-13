"""Sincronización de plazos fijos desde ArgentinaDatos hacia SQLite."""

import httpx

from backend.clients import argentinadatos_client
from backend.core.config import FIXED_DEPOSIT_TYPE, SOURCE_FIXED_DEPOSITS
from backend.db.repositories import fixed_deposit_repository, source_cache_repository
from backend.domain.banks import bank_for_entity
from backend.domain.returns import normalize_percentage


async def sync_fixed_deposits(client: httpx.AsyncClient):
    """Reemplaza las tasas y plazos guardados por los publicados hoy.

    Si la consulta falla, se registra el error y se conserva la caché anterior.
    """
    try:
        entidades = await argentinadatos_client.fetch_fixed_deposits(client)
        if entidades is None:
            return

        fixed_deposit_repository.clear_all()
        for item in entidades:
            _save_entity(item)
        source_cache_repository.mark_source_synced(SOURCE_FIXED_DEPOSITS)
    except Exception as e:
        print(f"[JOB ERROR] Plazos Fijos: {e}")


def _save_entity(item: dict):
    """Guarda la tasa general y los plazos de una entidad, si es un banco elegido."""
    nombre = bank_for_entity(str(item.get("entidad", "")).strip())
    tna = normalize_percentage(
        float(item.get("tnaClientes", 0) or item.get("tnaNoClientes", 0))
    )
    if not nombre or tna <= 0:
        return

    fixed_deposit_repository.save_rate(nombre, FIXED_DEPOSIT_TYPE, round(tna, 2))

    for term in item.get("tasas", []):
        plazo_min = term.get("plazoMinDias")
        plazo_max = term.get("plazoMaxDias")
        raw_term_tna = term.get("tna")
        if plazo_min and plazo_max and raw_term_tna:
            fixed_deposit_repository.save_term(
                nombre,
                int(plazo_min),
                int(plazo_max),
                round(normalize_percentage(float(raw_term_tna)), 2),
            )
