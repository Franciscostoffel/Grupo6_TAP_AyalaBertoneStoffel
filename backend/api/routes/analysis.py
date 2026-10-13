"""Endpoint POST /api/analyze: lo llama el frontend al tocar "Analizar inversiones"."""

from fastapi import APIRouter, HTTPException

from backend.schemas.investment import InvestmentRequest, InvestmentResponse
from backend.services import analysis_service
from backend.services.exceptions import DataNotReadyError, InvalidRiskError, NoOptionsError

router = APIRouter(prefix="/api", tags=["Análisis"])


@router.post("/analyze", response_model=InvestmentResponse)
async def analyze_investment(data: InvestmentRequest):
    """Compara plazos fijos y fondos según capital, plazo y riesgo."""
    try:
        return await analysis_service.analyze_investment(data)
    except DataNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except InvalidRiskError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except NoOptionsError as error:
        raise HTTPException(status_code=404, detail=str(error))
