"""Sesiones persistentes: solo se guarda el hash de cada token."""

from psycopg.rows import dict_row

from backend.db.connection import get_connection


def create_session(conn, token_hash: str, user_id, expires_at):
    conn.execute("""
        INSERT INTO user_sessions (token_hash, user_id, expires_at) VALUES (%s, %s, %s)
    """, (token_hash, user_id, expires_at))


def delete_session(conn, token_hash: str):
    conn.execute("DELETE FROM user_sessions WHERE token_hash = %s", (token_hash,))


def get_user(conn, token_hash: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("""
            SELECT u.id, u.email, u.created_at
            FROM user_sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %s AND s.expires_at > CURRENT_TIMESTAMP
        """, (token_hash,))
        return cursor.fetchone()


def delete_expired_sessions():
    """La autorización verifica el vencimiento aunque esta limpieza no se ejecute."""
    with get_connection() as conn:
        conn.execute("DELETE FROM user_sessions WHERE expires_at <= CURRENT_TIMESTAMP")
