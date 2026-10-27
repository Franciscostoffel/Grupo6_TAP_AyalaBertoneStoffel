"""Persistencia de inversiones guardadas por los usuarios."""

from uuid import uuid4

from psycopg.rows import dict_row
from psycopg.types.json import Json


def list_favorites(conn, user_id) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("""
            SELECT id, investment_key, capital, plazo, riesgo, option_data, created_at
            FROM user_favorite_investments
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        return cursor.fetchall()


def save_favorite(conn, user_id, investment_key, capital, plazo, riesgo, option_data) -> dict:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("""
            INSERT INTO user_favorite_investments
                (id, user_id, investment_key, capital, plazo, riesgo, option_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, investment_key) DO UPDATE SET
                capital = EXCLUDED.capital,
                plazo = EXCLUDED.plazo,
                riesgo = EXCLUDED.riesgo,
                option_data = EXCLUDED.option_data
            RETURNING id, investment_key, capital, plazo, riesgo, option_data, created_at
        """, (uuid4(), user_id, investment_key, capital, plazo, riesgo, Json(option_data)))
        return cursor.fetchone()


def delete_favorite(conn, user_id, investment_key):
    conn.execute("""
        DELETE FROM user_favorite_investments
        WHERE user_id = %s AND investment_key = %s
    """, (user_id, investment_key))
