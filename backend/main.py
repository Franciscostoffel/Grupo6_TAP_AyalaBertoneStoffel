"""Punto de entrada de Inversión Inteligente.

Este archivo solo arma la aplicación. La lógica está repartida en capas:

    api/       recibe los pedidos HTTP del frontend
    services/  coordina cada tarea (analizar, recomendar, sincronizar)
    domain/    reglas de negocio y fórmulas (riesgo, rendimientos, bancos)
    clients/   consulta APIs externas (ArgentinaDatos, CompararFondos, Gemini)
    db/        guarda y lee datos en PostgreSQL
    schemas/   formato de los datos que entran y salen de la API
    tasks/     actualización automática cada hora
    core/      configuración (URLs, tiempos, bancos)

Se ejecuta con:  uvicorn backend.main:app
"""

import asyncio
import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import analysis, auth
from backend.core.config import FRONTEND_PATH, validate_auth_config
from backend.db.schema import init_db
from backend.services.sync_service import sync_all_sources
from backend.tasks.scheduler import start_scheduler, stop_scheduler


# "lifespan" es la forma que tiene FastAPI de ejecutar código al prender y al
# apagar el servidor. Lo que está antes de "yield" corre al iniciar; lo que
# está después, al cerrar.
@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_auth_config()
    init_db()                                  # crea las tablas si no existen
    asyncio.create_task(sync_all_sources())    # descarga los datos sin frenar el arranque
    start_scheduler()                          # programa la descarga cada una hora
    yield
    stop_scheduler()


app = FastAPI(
    title="Inversión Inteligente",
    description="Comparador Concurrente con PostgreSQL, APIs y Money Market",
    version="1.0.0",
    lifespan=lifespan,
)

# Las rutas de la API se registran antes que los archivos estáticos.
app.include_router(auth.router)
app.include_router(analysis.router)


# ============================================================================
# ARCHIVOS DEL FRONTEND
# Se registra al final para que no tape las rutas de la API.
# ============================================================================

# En Windows a veces los .js se envían como texto plano y el navegador los
# rechaza. Con esto nos aseguramos de que se envíen con el tipo correcto.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")

# Sirve index.html, css/ y js/ desde la carpeta frontend.
app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
