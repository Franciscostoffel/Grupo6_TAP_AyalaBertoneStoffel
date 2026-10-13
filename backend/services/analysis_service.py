"""Análisis de inversión: filtra por riesgo, calcula rendimientos y ordena."""

from __future__ import annotations

from backend.core.config import FIXED_DEPOSIT_TYPE
from backend.db.repositories import fixed_deposit_repository, fund_repository
from backend.domain.returns import (
    fixed_deposit_gain,
    fund_period_return_pct,
    simple_period_return_pct,
)
from backend.domain.risk import FIXED_DEPOSIT_RISK, fund_risk, is_valid_risk, risk_matches
from backend.schemas.investment import EntityResult, InvestmentRequest, InvestmentResponse
from backend.services.exceptions import DataNotReadyError, InvalidRiskError, NoOptionsError
from backend.services.recommendation_service import get_recommendation

ACCESO_APP_FONDO = (
    "Asociado al banco; confirmá en la app si está habilitado "
    "para tu cuenta."
)


async def analyze_investment(request: InvestmentRequest) -> InvestmentResponse:
    """Arma las opciones a partir de la caché y agrega la recomendación."""
    rates = [
        rate for rate in fixed_deposit_repository.get_rates()
        if rate["tipo"] == FIXED_DEPOSIT_TYPE
    ]
    fixed_terms = fixed_deposit_repository.get_terms()
    funds = fund_repository.get_funds()

    if not rates and not funds:
        raise DataNotReadyError(
            "La base de datos se está sincronizando. Reintente en unos segundos."
        )

    riesgo = request.riesgo.strip().lower()
    if not is_valid_risk(riesgo):
        raise InvalidRiskError("Nivel de riesgo inválido.")

    opciones = [
        opcion
        for item in rates + funds
        if (opcion := _build_option(item, request.capital, request.plazo, riesgo))
        is not None
    ]
    if not opciones:
        raise NoOptionsError(
            "No encontramos opciones compatibles con ese nivel de riesgo."
        )

    opciones.sort(key=lambda x: x.rendimiento, reverse=True)
    recomendacion = await get_recommendation(
        request.capital, request.plazo, riesgo, opciones
    )

    return InvestmentResponse(
        capital=request.capital,
        plazo=request.plazo,
        riesgo=request.riesgo,
        opciones=opciones,
        recomendacion=recomendacion,
        plazos_fijos=fixed_terms,
    )


# ----------------------------------------------------------------------------
# Construcción de cada opción
# ----------------------------------------------------------------------------

def _build_option(
    item: dict,
    capital: float,
    plazo: int,
    riesgo: str,
) -> EntityResult | None:
    """Devuelve la opción calculada, o None si supera el riesgo aceptado."""
    es_fci = item["tipo"].startswith("FCI")
    perfil_riesgo = (
        fund_risk(item["tipo"].replace("FCI ", ""), item.get("horizonte"))
        if es_fci
        else FIXED_DEPOSIT_RISK
    )
    if not risk_matches(riesgo, perfil_riesgo):
        return None

    figures = (
        _fund_figures(item, capital, plazo)
        if es_fci
        else _fixed_deposit_figures(item, capital, plazo)
    )
    ganancia = figures["ganancia"]

    return EntityResult(
        nombre=item["nombre"],
        banco=item.get("banco"),
        tipo=item["tipo"],
        categoria=figures["categoria"],
        instrumento=figures["instrumento"],
        horizonte=figures["horizonte"],
        perfil_riesgo=perfil_riesgo,
        tna=item["tna"],
        rendimiento_ultimo_dia_pct=item.get("rendimiento_1d") if es_fci else None,
        rendimiento_periodo_pct=round(figures["rendimiento_periodo_pct"], 4),
        garantizado=item["garantizado"],
        fuente=item["fuente"],
        fecha_datos=item["fecha_datos"],
        rendimiento=round(ganancia, 2),
        monto_final=round(capital + ganancia, 2),
        liquidez=figures["liquidez"],
        acceso_app=ACCESO_APP_FONDO if es_fci and item.get("banco") else None,
    )


def _fund_figures(item: dict, capital: float, plazo: int) -> dict:
    """Rendimiento real de los últimos 30 días proyectado al plazo elegido."""
    rendimiento_30d = item.get("rendimiento_30d")
    rendimiento_periodo_pct = (
        fund_period_return_pct(rendimiento_30d, plazo)
        if rendimiento_30d is not None
        else simple_period_return_pct(item["tna"], plazo)
    )
    plazo_liq = item.get("plazo_liq")
    tipo_fci = item["tipo"].lower()

    return {
        "rendimiento_periodo_pct": rendimiento_periodo_pct,
        "ganancia": capital * rendimiento_periodo_pct / 100,
        "liquidez": (
            f"Rescate informado: {plazo_liq} día(s)"
            if plazo_liq is not None
            else "Según plazo de rescate del fondo"
        ),
        "instrumento": "Fondo Común de Inversión",
        "horizonte": item["horizonte"] or "No informado",
        "categoria": (
            "money_market"
            if "mercado de dinero" in tipo_fci or "plazo fijo" in tipo_fci
            else "fondos"
        ),
    }


def _fixed_deposit_figures(item: dict, capital: float, plazo: int) -> dict:
    """Interés simple de la TNA informada por el banco."""
    tna = item["tna"]
    return {
        "rendimiento_periodo_pct": simple_period_return_pct(tna, plazo),
        "ganancia": fixed_deposit_gain(capital, tna, plazo),
        "liquidez": f"Al vencimiento ({plazo} días)",
        "instrumento": "Renta Fija Tradicional",
        "horizonte": f"Referencia para {plazo} días",
        "categoria": "plazo_fijo",
    }
