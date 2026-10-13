"""Formato de los datos que entran y salen de la API.

Pydantic valida automáticamente: si el frontend manda un capital negativo o
falta un campo, FastAPI responde con error 422 sin que escribamos nada.
"""

from pydantic import BaseModel, Field


class InvestmentRequest(BaseModel):
    """Lo que manda el frontend."""
    capital: float = Field(gt=0)   # gt=0: tiene que ser mayor a cero
    plazo: int = Field(gt=0)       # en días
    riesgo: str                    # "bajo", "moderado" o "alto"


class EntityResult(BaseModel):
    """Una opción de inversión ya calculada (un plazo fijo o un fondo)."""
    nombre: str
    banco: str | None
    tipo: str
    categoria: str          # "plazo_fijo", "money_market" o "fondos"
    instrumento: str        # "Renta Fija Tradicional" o "Fondo Común de Inversión"
    horizonte: str
    perfil_riesgo: str
    tna: float | None
    rendimiento_ultimo_dia_pct: float | None
    rendimiento_periodo_pct: float | None
    garantizado: bool
    fuente: str
    fecha_datos: str | None
    rendimiento: float      # ganancia en pesos
    monto_final: float      # capital + ganancia
    liquidez: str
    acceso_app: str | None


class InvestmentResponse(BaseModel):
    """Lo que devuelve la API al frontend."""
    capital: float
    plazo: int
    riesgo: str
    opciones: list[EntityResult]
    recomendacion: str
    plazos_fijos: list[dict]
