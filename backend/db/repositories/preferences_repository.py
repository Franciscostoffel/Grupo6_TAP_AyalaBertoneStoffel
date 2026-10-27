"""Persistencia de las preferencias de bancos de cada usuario."""

from psycopg.rows import dict_row


def get_preferences(conn, user_id) -> dict:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SELECT banco_principal FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.execute("""
            SELECT bank_name
            FROM user_favorite_banks
            WHERE user_id = %s
            ORDER BY bank_name
        """, (user_id,))
        favorites = [row["bank_name"] for row in cursor.fetchall()]
    return {
        "primary_bank": user["banco_principal"] if user else None,
        "favorite_banks": favorites,
    }


def save_preferences(conn, user_id, primary_bank, favorite_banks) -> dict:
    conn.execute("UPDATE users SET banco_principal = %s WHERE id = %s", (primary_bank, user_id))
    conn.execute("DELETE FROM user_favorite_banks WHERE user_id = %s", (user_id,))
    if favorite_banks:
        with conn.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO user_favorite_banks (user_id, bank_name) VALUES (%s, %s)",
                [(user_id, bank_name) for bank_name in favorite_banks],
            )
    return get_preferences(conn, user_id)
