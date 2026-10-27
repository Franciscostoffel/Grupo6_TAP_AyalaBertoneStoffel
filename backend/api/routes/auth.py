"""Autenticación con cookie HttpOnly. El token nunca forma parte del JSON."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from psycopg import OperationalError
from starlette.responses import JSONResponse

from backend.api.dependencies import get_current_user, limit_auth_attempts, require_same_origin
from backend.core.config import COOKIE_SECURE, SESSION_COOKIE_NAME, SESSION_TTL_SECONDS
from backend.schemas.auth import (
    BankPreferences, FavoriteInvestmentRequest, FavoriteInvestmentResponse,
    LoginRequest, RegisterRequest, UserResponse,
)
from backend.services import preferences_service
from backend.services import favorite_investment_service
from backend.services import auth_service
from backend.services.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError


class AuthRoute(APIRoute):
    """Evita cachear respuestas o devolver entradas sensibles en errores de validación."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                response = await handler(request)
            except RequestValidationError:
                response = JSONResponse({"detail": "Revisá el email y la contraseña ingresados."}, status_code=422)
            except HTTPException as error:
                response = JSONResponse({"detail": error.detail}, status_code=error.status_code,
                                        headers=error.headers)
            except OperationalError:
                response = JSONResponse({"detail": "El servicio no está disponible. Probá nuevamente."}, status_code=503)
            response.headers["Cache-Control"] = "no-store"
            return response

        return safe_handler


router = APIRouter(prefix="/api/auth", tags=["Autenticación"], route_class=AuthRoute)
write_dependencies = [Depends(require_same_origin)]
credential_dependencies = [*write_dependencies, Depends(limit_auth_attempts)]


def _set_session_cookie(response: Response, token: str):
    response.set_cookie(SESSION_COOKIE_NAME, token, max_age=SESSION_TTL_SECONDS,
                        httponly=True, secure=COOKIE_SECURE, samesite="lax", path="/")


@router.post("/register", response_model=UserResponse, status_code=201, dependencies=credential_dependencies)
def register(data: RegisterRequest, request: Request, response: Response):
    try:
        user, token = auth_service.register(str(data.email), data.password.get_secret_value(),
                                           request.cookies.get(SESSION_COOKIE_NAME))
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(409, str(error)) from None
    _set_session_cookie(response, token)
    return user


@router.post("/login", response_model=UserResponse, dependencies=credential_dependencies)
def login(data: LoginRequest, request: Request, response: Response):
    try:
        user, token = auth_service.login(str(data.email), data.password.get_secret_value(),
                                        request.cookies.get(SESSION_COOKIE_NAME))
    except InvalidCredentialsError as error:
        raise HTTPException(401, str(error)) from None
    _set_session_cookie(response, token)
    return user


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return user


@router.get("/preferences", response_model=BankPreferences)
def get_preferences(user=Depends(get_current_user)):
    return preferences_service.get_preferences(user["id"])


@router.put("/preferences", response_model=BankPreferences,
            dependencies=write_dependencies)
def save_preferences(data: BankPreferences, user=Depends(get_current_user)):
    return preferences_service.save_preferences(
        user["id"], data.primary_bank, data.favorite_banks
    )


@router.get("/favorite-investments", response_model=list[FavoriteInvestmentResponse])
def list_favorite_investments(user=Depends(get_current_user)):
    return favorite_investment_service.list_favorites(user["id"])


@router.post("/favorite-investments", response_model=FavoriteInvestmentResponse, status_code=201,
             dependencies=write_dependencies)
def save_favorite_investment(data: FavoriteInvestmentRequest, user=Depends(get_current_user)):
    return favorite_investment_service.save_favorite(user["id"], data)


@router.delete("/favorite-investments/{investment_key}", status_code=204,
               dependencies=write_dependencies)
def delete_favorite_investment(investment_key: str, user=Depends(get_current_user)):
    favorite_investment_service.delete_favorite(user["id"], investment_key)


@router.post("/logout", status_code=204, dependencies=write_dependencies)
def logout(request: Request, response: Response):
    auth_service.logout(request.cookies.get(SESSION_COOKIE_NAME))
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", secure=COOKIE_SECURE,
                           httponly=True, samesite="lax")
