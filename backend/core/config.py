"""Configuración general y catálogos fijos de la aplicación.

Todo valor que pueda cambiar (URLs, tiempos, nombres de bancos) vive acá para
no tener que buscarlo dentro de la lógica.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ============================================================================
# RUTAS
# ============================================================================

CARPETA_PROYECTO = Path(__file__).resolve().parents[2]

# Lee el archivo .env de la carpeta del proyecto (si existe) y carga sus
# valores como variables de entorno. Así alcanza con poner la clave de Gemini
# en .env, tanto al ejecutar con Docker como con uvicorn.
load_dotenv(CARPETA_PROYECTO / ".env")

# PostgreSQL es la única fuente de persistencia. En desarrollo puede apuntar a
# la base local de docker-compose y en producción a la URL del proveedor.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Render define RENDER automáticamente. En local se permite HTTP explícitamente.
APP_ENV = os.getenv("APP_ENV", "production" if os.getenv("RENDER") else "development")
COOKIE_SECURE = APP_ENV == "production"
SESSION_COOKIE_NAME = "__Host-session" if COOKIE_SECURE else "session"
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
AUTH_ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "AUTH_ALLOWED_ORIGINS",
        "" if COOKIE_SECURE else "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",") if origin.strip()
}


def validate_auth_config():
    """Falla al iniciar si falta una configuración necesaria para autenticar."""
    from urllib.parse import urlsplit

    if APP_ENV not in {"development", "production", "test"}:
        raise RuntimeError("APP_ENV debe ser development, production o test.")
    if os.getenv("RENDER") and APP_ENV != "production":
        raise RuntimeError("En Render, APP_ENV debe ser production para usar cookies seguras.")
    if not DATABASE_URL:
        raise RuntimeError("Configurá DATABASE_URL en el entorno.")
    if not AUTH_ALLOWED_ORIGINS:
        raise RuntimeError("Configurá AUTH_ALLOWED_ORIGINS con la URL pública de la aplicación.")
    for origin in AUTH_ALLOWED_ORIGINS:
        parsed = urlsplit(origin)
        if (parsed.scheme not in {"http", "https"} or not parsed.netloc
                or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password):
            raise RuntimeError("AUTH_ALLOWED_ORIGINS debe contener orígenes sin rutas.")
        if COOKIE_SECURE and parsed.scheme != "https":
            raise RuntimeError("Los orígenes de producción deben usar HTTPS.")

FRONTEND_PATH = CARPETA_PROYECTO / "frontend"


# ============================================================================
# FUENTES EXTERNAS
# ============================================================================

FIXED_DEPOSIT_API_URL = (
    "https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo/"
)
FUNDS_API_URL = "https://compararfondos.com.ar/api/fondos"

EXTERNAL_HTTP_TIMEOUT_SECONDS = 15.0

# Claves con las que se registra cada sincronización en la tabla source_cache.
SOURCE_FIXED_DEPOSITS = "plazos_fijos"
SOURCE_FUNDS = "fci"

FIXED_DEPOSIT_SOURCE_NAME = "ArgentinaDatos"
FUND_SOURCE_NAME = "CompararFondos / CAFCI"
FIXED_DEPOSIT_TYPE = "Plazo Fijo"


# ============================================================================
# CACHE Y TAREAS PROGRAMADAS
# ============================================================================

CACHE_TTL_SECONDS = 60 * 60
SYNC_INTERVAL_HOURS = 1


# ============================================================================
# GEMINI
# La clave y el modelo se leen del entorno en cada consulta.
# ============================================================================

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_DEFAULT_MODEL = "gemini-3.5-flash-lite"
GEMINI_HTTP_TIMEOUT_SECONDS = 4.5
RECOMMENDATION_TIMEOUT_SECONDS = 5
GEMINI_MAX_OPTIONS_IN_PROMPT = 10


# ============================================================================
# CATALOGOS DE BANCOS
# ============================================================================

# Texto que aparece en el nombre de la entidad -> nombre que se muestra.
BANCOS_SELECCIONADOS = {
    "NACION": "Banco Nación",
    "PROVINCIA DE BUENOS AIRES": "Banco Provincia",
    "GALICIA": "Banco Galicia",
    "BBVA": "BBVA",
    "SANTANDER": "Banco Santander",
    "INDUSTRIAL AND COMMERCIAL BANK OF CHINA": "ICBC",
    "MACRO": "Banco Macro",
    "CIUDAD": "Banco Ciudad",
    "CREDICOOP": "Banco Credicoop",
    "BANCO DE LA CIUDAD DE BUENOS AIRES": "Banco Ciudad",
    "PATAGONIA": "Banco Patagonia",
    "SUPERVIELLE": "Banco Supervielle",
    "HIPOTECARIO": "Banco Hipotecario",
    "COMAFI": "Banco Comafi",
    "BICA": "Banco Bica",
    "CMF": "Banco CMF",
}

# Cada fondo común de inversión lo administra una "sociedad gerente". Muchos
# bancos y billeteras tienen la suya: con esta lista sabemos a quién pertenece
# cada fondo. Clave: texto que aparece en el nombre de la sociedad gerente.
SOCIEDADES_GERENTES = {
    "PELLEGRINI": "Banco Nación",
    "GALICIA ASSET": "Banco Galicia",
    "SANTANDER ASSET": "Banco Santander",
    "BBVA ASSET": "BBVA",
    "ICBC INVESTMENTS": "ICBC",
    "PROVINFONDOS": "Banco Provincia",
    "MACRO FONDOS": "Banco Macro",
    "CIUDAD ADMINISTRADORA": "Banco Ciudad",
    "PATAGONIA INVERSORA": "Banco Patagonia",
    "SUPERVIELLE ASSET": "Banco Supervielle",
    "COMAFI ADMINISTRADORA": "Banco Comafi",
    "CMF ASSET": "Banco CMF",
    # Billeteras virtuales: el dinero de la cuenta rinde a través de estos fondos.
    "MERCADO PAGO": "Mercado Pago",
    "UALA FONDOS": "Ualá",
}
