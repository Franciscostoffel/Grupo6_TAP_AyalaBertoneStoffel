"""SQL de usuarios. Las operaciones compuestas reciben la misma conexión."""

from psycopg.rows import dict_row


def create_user(conn, user_id, email: str, password_hash: str) -> dict:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("""
            INSERT INTO users (id, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, email, created_at
        """, (user_id, email, password_hash))
        return cursor.fetchone()


def get_by_email(conn, email: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("""
            SELECT id, email, password_hash, created_at FROM users WHERE email = %s
        """, (email,))
        return cursor.fetchone()


def update_password_hash(conn, user_id, password_hash: str):
    conn.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
