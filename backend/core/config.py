"""Configuración general y catálogos fijos de la aplicación.

Todo valor que pueda cambiar (URLs, tiempos, nombres de bancos) vive acá para
no tener que buscarlo dentro de la lógica.
"""

from pathlib import Path

# ============================================================================
# RUTAS
# ============================================================================

# Se resuelve desde el directorio de trabajo, igual que antes de separar capas.
DB_PATH = "investments.db"

FRONTEND_PATH = Path(__file__).resolve().parents[2] / "frontend"


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

# Nombres alternativos con los que los fondos mencionan a algunos bancos.
FUND_BANK_ALIASES = {
    "ICBC": "ICBC",
    "BANCO NACION": "Banco Nación",
    "BANCO GALICIA": "Banco Galicia",
    "BANCO SANTANDER": "Banco Santander",
    "BBVA": "BBVA",
}
