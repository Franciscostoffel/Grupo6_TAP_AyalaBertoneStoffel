"""Integración real: TEST_DATABASE_URL debe apuntar a una base exclusiva de pruebas."""

import os
import unittest
from contextlib import ExitStack
from uuid import uuid4

import psycopg
from psycopg.conninfo import conninfo_to_dict

from backend.core.security import hash_token, verify_password
from backend.db import schema
from backend.db.repositories import session_repository
from backend.services import auth_service
from backend.services.exceptions import EmailAlreadyRegisteredError


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Requiere TEST_DATABASE_URL de una base aislada")
class AuthPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ["TEST_DATABASE_URL"]
        if "test" not in conninfo_to_dict(cls.url).get("dbname", "").lower():
            raise RuntimeError("Las pruebas requieren una base cuyo nombre contenga test.")

    def setUp(self):
        from unittest.mock import patch

        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for target in (schema, auth_service, session_repository):
            self.stack.enter_context(patch.object(target, "get_connection", side_effect=lambda: psycopg.connect(self.url)))
        schema.init_db()
        schema.init_db()
        self.email = f"auth-test-{uuid4()}@example.com"
        self.password = "integration test password"
        self.addCleanup(self.delete_test_user)

    def delete_test_user(self):
        with psycopg.connect(self.url) as conn:
            conn.execute("DELETE FROM users WHERE email = %s", (self.email,))

    def test_register_login_rotation_expiry_logout_and_cascade(self):
        user, token = auth_service.register(self.email, self.password)
        with psycopg.connect(self.url) as conn:
            stored = conn.execute("SELECT password_hash FROM users WHERE id = %s", (user["id"],)).fetchone()[0]
            self.assertTrue(verify_password(stored, self.password))
            self.assertEqual(conn.execute("SELECT token_hash FROM user_sessions WHERE user_id = %s", (user["id"],)).fetchone()[0], hash_token(token))
        self.assertEqual(auth_service.get_current_user(token)["id"], user["id"])
        with self.assertRaises(EmailAlreadyRegisteredError):
            auth_service.register(self.email, self.password)
        _, replacement = auth_service.login(self.email, self.password, token)
        self.assertIsNone(auth_service.get_current_user(token))
        self.assertIsNotNone(auth_service.get_current_user(replacement))
        with psycopg.connect(self.url) as conn:
            conn.execute("""
                UPDATE user_sessions SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 days',
                expires_at = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE token_hash = %s
            """, (hash_token(replacement),))
        self.assertIsNone(auth_service.get_current_user(replacement))
        session_repository.delete_expired_sessions()
        _, another = auth_service.login(self.email, self.password)
        auth_service.logout(another)
        auth_service.logout(another)
        self.assertIsNone(auth_service.get_current_user(another))
        _, final = auth_service.login(self.email, self.password)
        self.delete_test_user()
        self.assertIsNone(auth_service.get_current_user(final))

    def test_user_is_rolled_back_if_session_creation_fails(self):
        from unittest.mock import patch

        with patch.object(session_repository, "create_session", side_effect=RuntimeError("simulated failure")):
            with self.assertRaises(RuntimeError):
                auth_service.register(self.email, self.password)
        with psycopg.connect(self.url) as conn:
            self.assertIsNone(conn.execute("SELECT id FROM users WHERE email = %s", (self.email,)).fetchone())

    def test_main_lifespan_and_routes_work_together(self):
        from unittest.mock import AsyncMock, patch

        from fastapi.testclient import TestClient

        from backend import main
        from backend.core import config

        with patch.object(config, "DATABASE_URL", self.url), \
             patch.object(main, "sync_all_sources", new_callable=AsyncMock), \
             patch.object(main, "start_scheduler"), patch.object(main, "stop_scheduler"), \
             TestClient(main.app, base_url="http://localhost:8000") as client:
            headers = {"Origin": "http://localhost:8000", "X-Requested-With": "fetch"}
            self.assertEqual(client.get("/").status_code, 200)
            self.assertEqual(client.get("/api/auth/me").status_code, 401)
            response = client.post("/api/auth/register", json={"email": self.email, "password": self.password}, headers=headers)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(client.get("/api/auth/me").json()["email"], self.email)
            self.assertEqual(client.post("/api/auth/logout", json={}, headers=headers).status_code, 204)
            self.assertEqual(client.get("/api/auth/me").status_code, 401)

    def test_rls_is_enabled_without_public_policies(self):
        with psycopg.connect(self.url) as conn:
            rows = conn.execute("SELECT relname, relrowsecurity FROM pg_class WHERE oid IN ('users'::regclass, 'user_sessions'::regclass)").fetchall()
            self.assertEqual(dict(rows), {"users": True, "user_sessions": True})
            self.assertEqual(conn.execute("SELECT count(*) FROM pg_policies WHERE schemaname = 'public' AND tablename IN ('users', 'user_sessions')").fetchone()[0], 0)
