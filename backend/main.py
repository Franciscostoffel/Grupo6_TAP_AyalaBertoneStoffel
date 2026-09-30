from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


app = FastAPI(
    title="Inversión Inteligente",
    description="Sistema de comparación de opciones de inversión",
    version="1.0.0"
)


# =========================
# MODELOS
# =========================

class InvestmentRequest(BaseModel):
    capital: float = Field(gt=0)
    plazo: int = Field(gt=0)
    riesgo: str


class InvestmentResponse(BaseModel):
    message: str
    capital: float
    plazo: int
    riesgo: str


# =========================
# API
# =========================

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Backend funcionando correctamente"
    }


@app.post("/api/analyze", response_model=InvestmentResponse)
async def analyze_investment(data: InvestmentRequest):

    return InvestmentResponse(
        message="Datos recibidos correctamente",
        capital=data.capital,
        plazo=data.plazo,
        riesgo=data.riesgo
    )


# =========================
# FRONTEND
# =========================

frontend_path = Path(__file__).resolve().parent.parent / "frontend"
app.mount(
    "/",
    StaticFiles(directory=frontend_path, html=True),
    name="frontend"
)