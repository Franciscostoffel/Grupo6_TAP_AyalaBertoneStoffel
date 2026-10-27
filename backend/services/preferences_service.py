"""Reglas de negocio para las preferencias de bancos."""

from backend.core.config import BANCOS_SELECCIONADOS
from backend.db.connection import get_connection
from backend.db.repositories import preferences_repository

ALLOWED_BANKS = frozenset(BANCOS_SELECCIONADOS.values())


def get_preferences(user_id):
    with get_connection() as conn:
        return preferences_repository.get_preferences(conn, user_id)


def save_preferences(user_id, primary_bank, favorite_banks):
    with get_connection() as conn:
        return preferences_repository.save_preferences(conn, user_id, primary_bank, favorite_banks)
