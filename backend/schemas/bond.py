"""Formato de las letras y bonos que devuelve la API."""

from datetime import date

from pydantic import BaseModel


class BondResult(BaseModel):
    """Una letra o bono. Los campos que no aplican a su tipo quedan en None."""
    ticker: str
    precio: float                   # precio en pesos cada 100 nominales
    fecha_vencimiento: date
    dias_al_vencimiento: int
    tna: float | None               # solo tasa fija
    tea: float | None               # solo tasa fija
    rendimiento_pct: float | None   # solo tasa fija: cuánto rinde hasta el vencimiento
    ganancia: float | None          # solo tasa fija y si se mandó el capital
    tir: float | None               # solo CER: rendimiento por encima de la inflación


class BondsResponse(BaseModel):
    """Lo que devuelve GET /api/bonds."""
    capital: float | None
    tasa_fija: list[BondResult]
    cer: list[BondResult]
