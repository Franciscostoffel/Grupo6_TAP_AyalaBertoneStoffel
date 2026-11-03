"""Endpoint GET /api/bonds: lo llama el frontend para el apartado "Bonos"."""

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.bond import BondsResponse
from backend.services import bond_service
from backend.services.exceptions import DataNotReadyError

router = APIRouter(prefix="/api", tags=["Bonos"])


@router.get("/bonds", response_model=BondsResponse)
def list_bonds(capital: float | None = Query(default=None, gt=0)):
    """Letras y bonos del Tesoro. Con "capital" calcula la ganancia al vencimiento."""
    try:
        return bond_service.list_bonds(capital)
    except DataNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error))
