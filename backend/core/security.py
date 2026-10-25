"""Contraseñas Argon2id y tokens opacos; no contiene lógica HTTP ni SQL."""

import hashlib
import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError

# 19 MiB, dos iteraciones y un hilo: mínimo recomendado para Argon2id.
password_hasher = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID)
_DUMMY_HASH = password_hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """También verifica un hash cuando el email no existe para reducir diferencias."""
    try:
        valid = password_hasher.verify(password_hash or _DUMMY_HASH, password)
        return bool(password_hash) and valid
    except (VerificationError, InvalidHashError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
