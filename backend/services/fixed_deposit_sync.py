"""Descarga las tasas de plazo fijo y las guarda en la base de datos."""

import httpx

from backend.clients import argentinadatos_client
from backend.core.config import FIXED_DEPOSIT_TYPE, SOURCE_FIXED_DEPOSITS
from backend.db.repositories import fixed_deposit_repository, source_cache_repository
from backend.domain.banks import bank_for_entity
from backend.domain.returns import normalize_percentage


async def sync_fixed_deposits(client: httpx.AsyncClient):
    """Reemplaza las tasas guardadas por las que publica hoy la fuente.

    Si algo falla, se muestra el error y quedan los datos anteriores.
    """
    try:
        entidades = await argentinadatos_client.fetch_fixed_deposits(client)
        if entidades is None:
            return

        fixed_deposit_repository.clear_all()
        for entidad in entidades:
            save_entity(entidad)
        source_cache_repository.mark_source_synced(SOURCE_FIXED_DEPOSITS)
    except Exception as e:
        print(f"[JOB ERROR] Plazos Fijos: {e}")


def save_entity(entidad: dict):
    """Guarda la tasa general y los rangos de días de un banco, si es de los elegidos."""
    nombre_banco = bank_for_entity(str(entidad.get("entidad", "")).strip())

    # Se usa la tasa para clientes; si no está, la tasa para no clientes.
    tasa_publicada = entidad.get("tnaClientes", 0) or entidad.get("tnaNoClientes", 0)
    tna = normalize_percentage(float(tasa_publicada))

    if not nombre_banco or tna <= 0:
        return

    fixed_deposit_repository.save_rate(nombre_banco, FIXED_DEPOSIT_TYPE, round(tna, 2))

    # Cada banco puede informar tasas distintas según la cantidad de días.
    for rango in entidad.get("tasas", []):
        plazo_min = rango.get("plazoMinDias")
        plazo_max = rango.get("plazoMaxDias")
        tna_rango = rango.get("tna")
        if plazo_min and plazo_max and tna_rango:
            fixed_deposit_repository.save_term(
                nombre_banco,
                int(plazo_min),
                int(plazo_max),
                round(normalize_percentage(float(tna_rango)), 2),
            )
