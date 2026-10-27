"""Reglas de negocio para inversiones guardadas."""

from backend.db.connection import get_connection
from backend.db.repositories import favorite_investment_repository
from backend.db.repositories import fixed_deposit_repository, fund_repository
from backend.services import analysis_service
from backend.domain.risk import is_valid_risk


def _current_version(favorite):
    option = favorite["option_data"]
    risk = str(favorite["riesgo"]).strip().lower()
    if not is_valid_risk(risk):
        return None, "no_disponible", None

    rates = [
        rate for rate in fixed_deposit_repository.get_rates()
        if rate["tipo"] == analysis_service.FIXED_DEPOSIT_TYPE
    ]
    terms = fixed_deposit_repository.get_terms()
    rates = analysis_service.apply_rate_for_term(rates, terms, favorite["plazo"])
    products = rates + fund_repository.get_funds()
    product = next(
        (
            item for item in products
            if item["nombre"] == option["nombre"]
            and item.get("banco") == option.get("banco")
            and item["tipo"] == option["tipo"]
        ),
        None,
    )
    if product is None:
        return None, "no_disponible", None

    current = analysis_service.build_option(
        product, favorite["capital"], favorite["plazo"], risk
    )
    if current is None:
        return None, "no_disponible", product.get("fecha_datos")

    current_data = current.model_dump()
    changed = any(
        current_data.get(field) != option.get(field)
        for field in ("tna", "rendimiento_periodo_pct", "rendimiento", "monto_final")
    )
    return current, "actualizada" if changed else "vigente", product.get("fecha_datos")


def list_favorites(user_id):
    with get_connection() as conn:
        favorites = favorite_investment_repository.list_favorites(conn, user_id)
    for favorite in favorites:
        current, status, updated_at = _current_version(favorite)
        favorite["current_option"] = current
        favorite["current_status"] = status
        favorite["current_updated_at"] = updated_at
    return favorites


def save_favorite(user_id, data):
    with get_connection() as conn:
        favorite = favorite_investment_repository.save_favorite(
            conn, user_id, data.investment_key, data.capital, data.plazo,
            data.riesgo, data.option.model_dump()
        )
    current, status, updated_at = _current_version(favorite)
    favorite["current_option"] = current
    favorite["current_status"] = status
    favorite["current_updated_at"] = updated_at
    return favorite


def delete_favorite(user_id, investment_key):
    with get_connection() as conn:
        favorite_investment_repository.delete_favorite(conn, user_id, investment_key)
