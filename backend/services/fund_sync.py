"""Descarga los fondos comunes de inversión y los guarda en la base de datos."""

import httpx

from backend.clients import compararfondos_client
from backend.core.config import SOURCE_FUNDS
from backend.db.repositories import fund_repository, source_cache_repository
from backend.domain.banks import bank_for_fund
from backend.domain.funds import select_one_class_per_fund
from backend.domain.returns import annualized_return_from_30d


async def sync_funds(client: httpx.AsyncClient):
    """Reemplaza los fondos guardados por los que publica hoy la fuente.

    Si algo falla, se muestra el error y quedan los datos anteriores.
    """
    try:
        fondos = await compararfondos_client.fetch_funds(client)
        fund_repository.clear_all()
        for fondo in select_one_class_per_fund(fondos):
            fund_repository.save_fund(normalize_fund(fondo))
        source_cache_repository.mark_source_synced(SOURCE_FUNDS)
    except Exception as e:
        print(f"[JOB ERROR] FCI: {e}")


def normalize_fund(fondo: dict) -> dict:
    """Pasa un fondo del formato de la API al formato de nuestra tabla fci_funds."""
    rendimiento_30d = float(fondo.get("r30"))

    # Si la fuente publica una TNA la usamos; si no, la estimamos con el rendimiento de 30 días.
    if fondo.get("tna") is not None and float(fondo["tna"]) > 0:
        tna_estimada = float(fondo["tna"])
    else:
        tna_estimada = annualized_return_from_30d(rendimiento_30d)

    if fondo.get("variacionDia") is not None:
        rendimiento_1d = float(fondo["variacionDia"])
    else:
        rendimiento_1d = None

    return {
        "nombre": str(fondo.get("nombreBase") or fondo.get("nombre")).strip(),
        "banco": bank_for_fund(fondo),
        "tipo": f"FCI {fondo.get('tipo') or 'Otros'}",
        "horizonte": fondo.get("horizonte"),
        "tna_estimada": tna_estimada,
        "rendimiento_1d": rendimiento_1d,
        "rendimiento_30d": rendimiento_30d,
        "vcp": fondo.get("vcpHoy"),
        "fecha_datos": fondo.get("fechaVcp"),
        "fecha_vcp": fondo.get("fechaVcp"),
        "depositaria": fondo.get("depositaria"),
        "gerente": fondo.get("gerente"),
        "gestora": fondo.get("gestora"),
        "minimo": fondo.get("minimo"),
        "plazo_liq": fondo.get("plazoLiq"),
    }
