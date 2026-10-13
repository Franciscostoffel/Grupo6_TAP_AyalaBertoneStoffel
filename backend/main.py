"""Punto de entrada de Inversión Inteligente.

Solo arma la aplicación: ciclo de vida, rutas de la API y archivos estáticos.
La lógica está repartida en capas:

    api/       endpoints HTTP (presentación)
    services/  casos de uso: análisis, recomendación y sincronización
    domain/    reglas de negocio puras (riesgo, rendimientos, bancos)
    clients/   consultas a APIs externas (ArgentinaDatos, CompararFondos, Gemini)
    db/        conexión, esquema y repositorios de SQLite
    schemas/   modelos de entrada y salida de la API
    tasks/     sincronización periódica
    core/      configuración
"""

import asyncio
import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import analysis
from backend.core.config import FRONTEND_PATH
from backend.db.schema import init_db
from backend.services.sync_service import sync_all_sources
from backend.tasks.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepara la caché, la sincroniza en segundo plano y programa las actualizaciones."""
    init_db()
    asyncio.create_task(sync_all_sources())
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Inversión Inteligente",
    description="Comparador Concurrente con SQLite, APIs y Money Market",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(analysis.router)


# ============================================================================
# ARCHIVOS ESTATICOS DEL FRONTEND
# Se monta al final para que no tape las rutas de la API.
# ============================================================================

# En Windows el registro puede asociar .js a text/plain, y el navegador
# rechaza los modulos de JavaScript servidos con ese tipo.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")

app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
