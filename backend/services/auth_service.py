"""Registro, login y sesiones sin depender de FastAPI ni de cookies HTTP."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from psycopg.errors import UniqueViolation

from backend.core.config import SESSION_TTL_SECONDS
from backend.core.security import hash_password, hash_token, new_session_token, password_hasher, verify_password
from backend.db.connection import get_connection
from backend.db.repositories import session_repository, user_repository
from backend.services.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError


def _create_session(conn, user_id, previous_token):
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)
    if previous_token and len(previous_token) <= 128:
        session_repository.delete_session(conn, hash_token(previous_token))
    session_repository.create_session(conn, hash_token(token), user_id, expires_at)
    return token


def register(email: str, password: str, previous_token: str | None = None):
    password_hash = hash_password(password)
    try:
        # El contexto confirma todo junto o revierte usuario y sesión ante un error.
        with get_connection() as conn:
            user = user_repository.create_user(conn, uuid4(), email, password_hash)
            token = _create_session(conn, user["id"], previous_token)
    except UniqueViolation as error:
        if error.diag.constraint_name != "users_email_key":
            raise
        raise EmailAlreadyRegisteredError("Ya existe una cuenta con ese email.") from None
    return user, token


def login(email: str, password: str, previous_token: str | None = None):
    with get_connection() as conn:
        user = user_repository.get_by_email(conn, email)
    if not verify_password(user["password_hash"] if user else None, password):
        raise InvalidCredentialsError("Email o contraseña incorrectos.")
    with get_connection() as conn:
        if password_hasher.check_needs_rehash(user["password_hash"]):
            user_repository.update_password_hash(conn, user["id"], hash_password(password))
        token = _create_session(conn, user["id"], previous_token)
    return user, token


def get_current_user(token: str | None):
    if not token or len(token) != 43:
        return None
    with get_connection() as conn:
        return session_repository.get_user(conn, hash_token(token))


def logout(token: str | None):
    if token and len(token) <= 128:
        with get_connection() as conn:
            session_repository.delete_session(conn, hash_token(token))
