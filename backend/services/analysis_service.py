"""Análisis de inversión: es el corazón del sistema.

Pasos:
1. Lee de la base de datos los plazos fijos y los fondos.
2. Descarta los productos con más riesgo del que acepta el usuario.
3. Calcula cuánto ganaría con cada uno según su capital y plazo.
4. Ordena de mayor a menor ganancia y pide la recomendación de texto.
"""

from backend.core.config import FIXED_DEPOSIT_TYPE
from backend.db.repositories import fixed_deposit_repository, fund_repository
from backend.domain.fixed_deposit_rates import choose_rate_for_term
from backend.domain.returns import (
    fixed_deposit_gain,
    fund_period_return_pct,
    simple_period_return_pct,
)
from backend.domain.risk import FIXED_DEPOSIT_RISK, fund_risk, is_valid_risk, risk_matches
from backend.schemas.investment import EntityResult, InvestmentRequest, InvestmentResponse
from backend.services.exceptions import DataNotReadyError, InvalidRiskError, NoOptionsError
from backend.services.recommendation_service import (
    RECOMENDACION_SIN_BANCOS,
    get_recommendation,
)

TEXTO_ACCESO_APP = (
    "Fondo de esta entidad; confirmá en su app si está habilitado "
    "para tu cuenta."
)


async def analyze_investment(pedido: InvestmentRequest) -> InvestmentResponse:
    """Devuelve las opciones de inversión calculadas para el pedido del usuario."""
    # 1. Leer los datos guardados.
    tasas = []
    for tasa in fixed_deposit_repository.get_rates():
        if tasa["tipo"] == FIXED_DEPOSIT_TYPE:
            tasas.append(tasa)
    plazos_fijos = fixed_deposit_repository.get_terms()
    fondos = fund_repository.get_funds()

    if not tasas and not fondos:
        raise DataNotReadyError(
            "La base de datos se está sincronizando. Reintente en unos segundos."
        )

    riesgo = pedido.riesgo.strip().lower()
    if not is_valid_risk(riesgo):
        raise InvalidRiskError("Nivel de riesgo inválido.")

    # Cada banco usa la tasa que corresponde al plazo pedido (30, 90, 365 días...).
    tasas = apply_rate_for_term(tasas, plazos_fijos, pedido.plazo)

    # 2 y 3. Filtrar por riesgo y calcular la ganancia de cada producto.
    opciones = []
    for producto in tasas + fondos:
        opcion = build_option(producto, pedido.capital, pedido.plazo, riesgo)
        if opcion is not None:
            opciones.append(opcion)

    if not opciones:
        raise NoOptionsError("No encontramos opciones compatibles con ese nivel de riesgo.")

    # 4. Ordenar de mayor a menor ganancia y pedir la recomendación.
    opciones.sort(key=obtener_ganancia, reverse=True)

    opciones_con_banco = []
    for opcion in opciones:
        if opcion.banco:
            opciones_con_banco.append(opcion)

    if opciones_con_banco:
        recomendacion = await get_recommendation(
            pedido.capital, pedido.plazo, riesgo, opciones_con_banco
        )
    else:
        recomendacion = RECOMENDACION_SIN_BANCOS

    return InvestmentResponse(
        capital=pedido.capital,
        plazo=pedido.plazo,
        riesgo=pedido.riesgo,
        opciones=opciones,
        recomendacion=recomendacion,
        plazos_fijos=plazos_fijos,
    )


def apply_rate_for_term(tasas: list[dict], plazos_fijos: list[dict], plazo: int) -> list[dict]:
    """Reemplaza la tasa general de cada banco por la que corresponde al plazo."""
    tasas_del_plazo = []
    for tasa in tasas:
        rangos_del_banco = []
        for rango in plazos_fijos:
            if rango["banco"] == tasa["banco"]:
                rangos_del_banco.append(rango)

        tna, detalle = choose_rate_for_term(tasa["tna"], rangos_del_banco, plazo)

        tasa_del_plazo = dict(tasa)  # copia, para no modificar la original
        tasa_del_plazo["tna"] = tna
        tasa_del_plazo["detalle_tasa"] = detalle
        tasas_del_plazo.append(tasa_del_plazo)
    return tasas_del_plazo


def obtener_ganancia(opcion: EntityResult) -> float:
    """Se usa para ordenar las opciones por ganancia."""
    return opcion.rendimiento


def build_option(producto: dict, capital: float, plazo: int, riesgo: str) -> EntityResult | None:
    """Calcula una opción. Devuelve None si el producto tiene más riesgo del aceptado."""
    es_fondo = producto["tipo"].startswith("FCI")

    if es_fondo:
        perfil_riesgo = fund_risk(producto["tipo"].replace("FCI ", ""), producto.get("horizonte"))
    else:
        perfil_riesgo = FIXED_DEPOSIT_RISK

    if not risk_matches(riesgo, perfil_riesgo):
        return None

    if es_fondo:
        calculo = calculate_fund(producto, capital, plazo)
        rendimiento_ultimo_dia = producto.get("rendimiento_1d")
        if producto.get("banco"):
            acceso_app = TEXTO_ACCESO_APP
        else:
            acceso_app = None
    else:
        calculo = calculate_fixed_deposit(producto, capital, plazo)
        rendimiento_ultimo_dia = None
        acceso_app = None

    ganancia = calculo["ganancia"]

    return EntityResult(
        nombre=producto["nombre"],
        banco=producto.get("banco"),
        tipo=producto["tipo"],
        categoria=calculo["categoria"],
        instrumento=calculo["instrumento"],
        horizonte=calculo["horizonte"],
        perfil_riesgo=perfil_riesgo,
        tna=producto["tna"],
        rendimiento_ultimo_dia_pct=rendimiento_ultimo_dia,
        rendimiento_periodo_pct=round(calculo["rendimiento_periodo_pct"], 4),
        garantizado=producto["garantizado"],
        fuente=producto["fuente"],
        fecha_datos=producto["fecha_datos"],
        rendimiento=round(ganancia, 2),
        monto_final=round(capital + ganancia, 2),
        liquidez=calculo["liquidez"],
        acceso_app=acceso_app,
    )


def calculate_fund(fondo: dict, capital: float, plazo: int) -> dict:
    """Ganancia de un fondo: usa su rendimiento real de los últimos 30 días."""
    rendimiento_30d = fondo.get("rendimiento_30d")
    if rendimiento_30d is not None:
        porcentaje = fund_period_return_pct(rendimiento_30d, plazo)
    else:
        porcentaje = simple_period_return_pct(fondo["tna"], plazo)

    if fondo.get("plazo_liq") is not None:
        liquidez = f"Rescate informado: {fondo['plazo_liq']} día(s)"
    else:
        liquidez = "Según plazo de rescate del fondo"

    tipo = fondo["tipo"].lower()
    if "mercado de dinero" in tipo or "plazo fijo" in tipo:
        categoria = "money_market"
    else:
        categoria = "fondos"

    return {
        "rendimiento_periodo_pct": porcentaje,
        "ganancia": capital * porcentaje / 100,
        "liquidez": liquidez,
        "instrumento": "Fondo Común de Inversión",
        "horizonte": fondo["horizonte"] or "No informado",
        "categoria": categoria,
    }


def calculate_fixed_deposit(tasa: dict, capital: float, plazo: int) -> dict:
    """Ganancia de un plazo fijo: interés simple sobre la TNA del banco."""
    return {
        "rendimiento_periodo_pct": simple_period_return_pct(tasa["tna"], plazo),
        "ganancia": fixed_deposit_gain(capital, tasa["tna"], plazo),
        "liquidez": f"Al vencimiento ({plazo} días)",
        "instrumento": "Renta Fija Tradicional",
        "horizonte": tasa["detalle_tasa"],  # explica qué tasa del banco se usó
        "categoria": "plazo_fijo",
    }
