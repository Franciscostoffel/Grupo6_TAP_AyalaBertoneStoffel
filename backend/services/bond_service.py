"""Listado de letras y bonos del Tesoro para el apartado "Bonos".

Los de tasa fija (LECAP y BONCAP) se comparan como un plazo fijo: si el
usuario indica un capital, se calcula cuánto ganaría si los mantiene hasta el
vencimiento. Los CER dependen de la inflación futura, así que solo se muestra
su TIR real.
"""

from datetime import datetime, timedelta, timezone

from backend.core.config import BOND_MAX_DAYS, BOND_TYPE_FIXED_RATE
from backend.db.repositories import bond_repository
from backend.domain.returns import effective_period_return_pct
from backend.schemas.bond import BondResult, BondsResponse
from backend.services.exceptions import DataNotReadyError

# Argentina no usa horario de verano: siempre está tres horas atrás de UTC.
ZONA_ARGENTINA = timezone(timedelta(hours=-3))


def list_bonds(capital: float | None = None) -> BondsResponse:
    """Devuelve los bonos que todavía no vencieron, separados en tasa fija y CER."""
    bonos = bond_repository.get_bonds()
    if not bonos:
        raise DataNotReadyError("Los bonos se están sincronizando. Reintente en unos segundos.")

    hoy = datetime.now(ZONA_ARGENTINA).date()
    tasa_fija = []
    cer = []
    for bono in bonos:
        dias = (bono["fecha_vencimiento"] - hoy).days
        if dias <= 0:
            continue  # venció después de la última sincronización

        if bono["tipo"] == BOND_TYPE_FIXED_RATE:
            # Hasta un año, como el simulador. Más lejos la fuente mezcla bonos
            # que pagan cupones (como el TY30P) y el cálculo de ganancia no sirve.
            if dias <= BOND_MAX_DAYS:
                tasa_fija.append(fixed_rate_result(bono, dias, capital))
        else:
            cer.append(cer_result(bono, dias))

    return BondsResponse(capital=capital, tasa_fija=tasa_fija, cer=cer)


def fixed_rate_result(bono: dict, dias: int, capital: float | None) -> BondResult:
    """Comprando hoy y esperando al vencimiento se gana la TEA llevada a esos días."""
    rendimiento_pct = effective_period_return_pct(bono["tea"], dias)
    ganancia = None
    if capital is not None:
        ganancia = round(capital * rendimiento_pct / 100, 2)

    return BondResult(
        ticker=bono["ticker"],
        precio=bono["precio"],
        fecha_vencimiento=bono["fecha_vencimiento"],
        dias_al_vencimiento=dias,
        tna=bono["tna"],
        tea=bono["tea"],
        rendimiento_pct=round(rendimiento_pct, 2),
        ganancia=ganancia,
        tir=None,
    )


def cer_result(bono: dict, dias: int) -> BondResult:
    """Los CER solo muestran su TIR: la ganancia en pesos depende de la inflación."""
    return BondResult(
        ticker=bono["ticker"],
        precio=bono["precio"],
        fecha_vencimiento=bono["fecha_vencimiento"],
        dias_al_vencimiento=dias,
        tna=None,
        tea=None,
        rendimiento_pct=None,
        ganancia=None,
        tir=bono["tir"],
    )
