"""Endpoint de análisis de inversiones."""

from fastapi import APIRouter, HTTPException

from backend.schemas.investment import InvestmentRequest, InvestmentResponse
from backend.services import analysis_service
from backend.services.exceptions import DataNotReadyError, InvalidRiskError, NoOptionsError

router = APIRouter(prefix="/api", tags=["Análisis"])

# Código HTTP que corresponde a cada error del servicio.
ERROR_STATUS = {
    DataNotReadyError: 503,
    InvalidRiskError: 422,
    NoOptionsError: 404,
}


@router.post("/analyze", response_model=InvestmentResponse)
async def analyze_investment(data: InvestmentRequest):
    """Compara plazos fijos y fondos según capital, plazo y riesgo."""
    try:
        return await analysis_service.analyze_investment(data)
    except (DataNotReadyError, InvalidRiskError, NoOptionsError) as error:
        raise HTTPException(
            status_code=ERROR_STATUS[type(error)],
            detail=str(error),
        ) from error
