"""Contrato del endpoint de análisis. Cambiarlo afecta al frontend."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InvestmentRequest(BaseModel):
    capital: float = Field(gt=0)
    plazo: int = Field(gt=0)
    riesgo: str


class EntityResult(BaseModel):
    nombre: str
    banco: str | None
    tipo: str
    categoria: str
    instrumento: str    # "Renta Fija Tradicional" o "Fondo Común de Inversión"
    horizonte: str
    perfil_riesgo: str
    tna: float | None
    rendimiento_ultimo_dia_pct: float | None
    rendimiento_periodo_pct: float | None
    garantizado: bool
    fuente: str
    fecha_datos: str | None
    rendimiento: float
    monto_final: float
    liquidez: str
    acceso_app: str | None


class InvestmentResponse(BaseModel):
    capital: float
    plazo: int
    riesgo: str
    opciones: list[EntityResult]
    recomendacion: str
    plazos_fijos: list[dict]
