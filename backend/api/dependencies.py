"""Controles HTTP reutilizables para las rutas autenticadas."""

import time
from collections import OrderedDict
from threading import Lock

from fastapi import HTTPException, Request

from backend.core.config import AUTH_ALLOWED_ORIGINS, SESSION_COOKIE_NAME
from backend.services import auth_service


def require_same_origin(request: Request):
    """El encabezado personalizado exige preflight fuera del origen; no habilitamos CORS."""
    if request.headers.get("X-Requested-With") != "fetch":
        raise HTTPException(403, "Solicitud no permitida.")
    if request.headers.get("origin") not in AUTH_ALLOWED_ORIGINS:
        raise HTTPException(403, "Origen no permitido.")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Solicitud no permitida.")


def get_current_user(request: Request):
    user = auth_service.get_current_user(request.cookies.get(SESSION_COOKIE_NAME))
    if user is None:
        raise HTTPException(401, "Iniciá sesión para continuar.", headers={"Cache-Control": "no-store"})
    return user


class AuthRateLimiter:
    """Límite por IP, acotado en memoria para el despliegue actual de un proceso."""

    def __init__(self):
        self._buckets = OrderedDict()
        self._lock = Lock()

    def check(self, key, limit, window):
        now = time.monotonic()
        with self._lock:
            start, count = self._buckets.get(key, (now, 0))
            if now - start >= window:
                start, count = now, 0
            if count >= limit:
                raise HTTPException(429, "Demasiados intentos. Probá más tarde.",
                                    headers={"Retry-After": str(max(1, int(window - (now - start))))})
            self._buckets[key] = (start, count + 1)
            self._buckets.move_to_end(key)
            while len(self._buckets) > 10000:
                self._buckets.popitem(last=False)


auth_rate_limiter = AuthRateLimiter()


def limit_auth_attempts(request: Request):
    # request.client usa solamente la configuración de proxies confiables de Uvicorn.
    # Nunca se interpreta X-Forwarded-For manualmente.
    ip = request.client.host if request.client else "unknown"
    registering = request.url.path.endswith("/register")
    auth_rate_limiter.check((request.url.path, ip), 10 if registering else 20,
                            3600 if registering else 900)
