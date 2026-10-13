"""Sincronización de fondos comunes de inversión desde CompararFondos/CAFCI."""

import httpx

from backend.clients import compararfondos_client
from backend.core.config import SOURCE_FUNDS
from backend.db.repositories import fund_repository, source_cache_repository
from backend.domain.banks import bank_for_fund
from backend.domain.funds import select_one_class_per_fund
from backend.domain.returns import annualized_return_from_30d


async def sync_funds(client: httpx.AsyncClient):
    """Reemplaza el catálogo de fondos guardado por el publicado hoy.

    Si la consulta falla, se registra el error y se conserva la caché anterior.
    """
    try:
        fondos = await compararfondos_client.fetch_funds(client)
        fund_repository.clear_all()
        for item in select_one_class_per_fund(fondos):
            fund_repository.save_fund(**_normalize_fund(item))
        source_cache_repository.mark_source_synced(SOURCE_FUNDS)
    except Exception as e:
        print(f"[JOB ERROR] FCI: {e}")


def _normalize_fund(item: dict) -> dict:
    """Traduce un fondo de la fuente a las columnas de la tabla fci_funds."""
    rendimiento_30d = float(item.get("r30"))
    return {
        "nombre": str(item.get("nombreBase") or item.get("nombre")).strip(),
        "banco": bank_for_fund(item),
        "tipo": f"FCI {item.get('tipo') or 'Otros'}",
        "horizonte": item.get("horizonte"),
        # Si la fuente no publica una TNA, se estima con el rendimiento de 30 días.
        "tna_estimada": (
            float(item["tna"])
            if item.get("tna") is not None and float(item["tna"]) > 0
            else annualized_return_from_30d(rendimiento_30d)
        ),
        "rendimiento_1d": (
            float(item["variacionDia"])
            if item.get("variacionDia") is not None
            else None
        ),
        "rendimiento_30d": rendimiento_30d,
        "vcp": item.get("vcpHoy"),
        "fecha_datos": item.get("fechaVcp"),
        "fecha_vcp": item.get("fechaVcp"),
        "depositaria": item.get("depositaria"),
        "gerente": item.get("gerente"),
        "gestora": item.get("gestora"),
        "minimo": item.get("minimo"),
        "plazo_liq": item.get("plazoLiq"),
    }
