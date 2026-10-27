"""Contratos de autenticación; la respuesta pública nunca incluye credenciales."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from backend.services.preferences_service import ALLOWED_BANKS
from backend.schemas.investment import EntityResult


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class RegisterRequest(LoginRequest):
    password: SecretStr = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime


class BankPreferences(BaseModel):
    primary_bank: str | None = Field(default=None, max_length=100)
    favorite_banks: list[str] = Field(default_factory=list, max_length=15)

    @field_validator("primary_bank")
    @classmethod
    def validate_primary_bank(cls, value):
        if value is not None and value not in ALLOWED_BANKS:
            raise ValueError("El banco seleccionado no es válido.")
        return value

    @field_validator("favorite_banks")
    @classmethod
    def validate_favorite_banks(cls, values):
        if any(value not in ALLOWED_BANKS for value in values):
            raise ValueError("Uno de los bancos favoritos no es válido.")
        if len(set(values)) != len(values):
            raise ValueError("No se pueden repetir bancos favoritos.")
        return values


class FavoriteInvestmentRequest(BaseModel):
    investment_key: str = Field(min_length=1, max_length=500)
    capital: float = Field(gt=0)
    plazo: int = Field(gt=0)
    riesgo: str = Field(min_length=1, max_length=20)
    option: EntityResult


class FavoriteInvestmentResponse(BaseModel):
    id: UUID
    investment_key: str
    capital: float
    plazo: int
    riesgo: str
    option_data: EntityResult
    created_at: datetime
    current_option: EntityResult | None = None
    current_status: str
    current_updated_at: str | None = None
