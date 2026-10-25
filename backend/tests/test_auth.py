"""Pruebas HTTP y de servicios sin tocar la base de datos configurada en .env."""

import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import OperationalError

from backend.api.dependencies import AuthRateLimiter
from backend.api.routes import analysis, auth
from backend.core import config
from backend.core.security import hash_password, hash_token, new_session_token, verify_password
from backend.schemas.auth import RegisterRequest
from backend.services import auth_service
from backend.services.exceptions import DataNotReadyError, EmailAlreadyRegisteredError, InvalidCredentialsError


class AuthHttpTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch("backend.api.dependencies.AUTH_ALLOWED_ORIGINS", {"https://testserver"}))
        self.stack.enter_context(patch("backend.api.dependencies.auth_rate_limiter", AuthRateLimiter()))
        self.stack.enter_context(patch("backend.api.routes.auth.COOKIE_SECURE", True))
        self.stack.enter_context(patch("backend.api.routes.auth.SESSION_COOKIE_NAME", "__Host-session"))
        self.stack.enter_context(patch("backend.api.dependencies.SESSION_COOKIE_NAME", "__Host-session"))
        app = FastAPI()
        app.include_router(auth.router)
        app.include_router(analysis.router)
        self.client = self.stack.enter_context(TestClient(app, base_url="https://testserver"))
        self.headers = {"Origin": "https://testserver", "X-Requested-With": "fetch"}
        self.payload = {"email": "PERSON@Example.com", "password": "a sufficiently long password"}
        self.user = {"id": uuid4(), "email": "person@example.com", "created_at": datetime.now(timezone.utc)}

    def test_register_normalizes_email_sets_secure_cookie_and_hides_secrets(self):
        token = new_session_token()
        with patch.object(auth_service, "register", return_value=({**self.user, "password_hash": "secret"}, token)) as register:
            response = self.client.post("/api/auth/register", json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(register.call_args.args[:2], ("person@example.com", self.payload["password"]))
        self.assertEqual(set(response.json()), {"id", "email", "created_at"})
        cookie = response.headers["set-cookie"]
        for attribute in ("__Host-session=", "HttpOnly", "Secure", "SameSite=lax", "Path=/", "Max-Age=604800"):
            self.assertIn(attribute, cookie)
        self.assertNotIn("Domain=", cookie)
        self.assertNotIn(token, response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_me_reads_cookie_and_logout_clears_it(self):
        token = new_session_token()
        self.client.cookies.set("__Host-session", token)
        with patch.object(auth_service, "get_current_user", return_value=self.user) as current:
            response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)
        current.assert_called_once_with(token)
        with patch.object(auth_service, "logout") as logout:
            response = self.client.post("/api/auth/logout", json={}, headers=self.headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertIn("Max-Age=0", response.headers["set-cookie"])
        logout.assert_called_once_with(token)

    def test_logout_without_session_is_idempotent(self):
        with patch.object(auth_service, "logout") as logout:
            response = self.client.post("/api/auth/logout", json={}, headers=self.headers)
        self.assertEqual(response.status_code, 204)
        logout.assert_called_once_with(None)

    def test_invalid_or_expired_session_denies_me_and_analysis(self):
        with patch.object(auth_service, "get_current_user", return_value=None):
            self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
            response = self.client.post("/api/analyze", json={"capital": 1000, "plazo": 30, "riesgo": "bajo"}, headers=self.headers)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_analysis_keeps_existing_service_contract(self):
        payload = {"capital": 1000, "plazo": 30, "riesgo": "bajo"}
        result = {**payload, "opciones": [], "plazos_fijos": [], "recomendacion": "Prueba"}
        with patch.object(auth_service, "get_current_user", return_value=self.user), \
             patch.object(analysis.analysis_service, "analyze_investment", new_callable=AsyncMock, return_value=result) as analyze:
            response = self.client.post("/api/analyze", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), result)
        self.assertEqual(analyze.call_args.args[0].model_dump(), payload)
        with patch.object(auth_service, "get_current_user", return_value=self.user), \
             patch.object(analysis.analysis_service, "analyze_investment", new_callable=AsyncMock,
                          side_effect=DataNotReadyError("Sincronizando")):
            response = self.client.post("/api/analyze", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 503)

    def test_authenticated_analysis_also_rejects_cross_origin(self):
        with patch.object(auth_service, "get_current_user", return_value=self.user):
            response = self.client.post("/api/analyze", json={"capital": 1000, "plazo": 30, "riesgo": "bajo"},
                                        headers={**self.headers, "Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)

    def test_cross_origin_or_missing_custom_header_is_rejected_before_service(self):
        with patch.object(auth_service, "login") as login:
            for headers in ({}, {"Origin": "https://testserver"},
                            {**self.headers, "Origin": "https://evil.example"},
                            {**self.headers, "Sec-Fetch-Site": "cross-site"}):
                response = self.client.post("/api/auth/login", json=self.payload, headers=headers)
                self.assertEqual(response.status_code, 403)
            login.assert_not_called()

    def test_validation_does_not_echo_password_or_input(self):
        secret = "short-secret"
        response = self.client.post("/api/auth/register", json={"email": "bad", "password": secret}, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.text)
        self.assertNotIn("input", response.json())
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_registration_password_length_boundaries(self):
        with patch.object(auth_service, "register", return_value=(self.user, new_session_token())) as register:
            for length, expected in ((7, 422), (8, 201), (128, 201), (129, 422)):
                with self.subTest(length=length):
                    response = self.client.post("/api/auth/register", headers=self.headers,
                                                json={"email": self.user["email"], "password": "a" * length})
                    self.assertEqual(response.status_code, expected)
            self.assertEqual(register.call_count, 2)

    def test_login_error_and_duplicate_email(self):
        with patch.object(auth_service, "login", side_effect=InvalidCredentialsError("Email o contraseña incorrectos.")):
            response = self.client.post("/api/auth/login", json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 401)
        with patch.object(auth_service, "register", side_effect=EmailAlreadyRegisteredError("Ya existe una cuenta con ese email.")):
            response = self.client.post("/api/auth/register", json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 409)

    def test_database_error_is_generic(self):
        with patch.object(auth_service, "login", side_effect=OperationalError("database connection secret")):
            response = self.client.post("/api/auth/login", json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.text)

    def test_rate_limit_prevents_more_hashing(self):
        with patch.object(auth_service, "login", side_effect=InvalidCredentialsError("Credenciales incorrectas.")) as login:
            for _ in range(20):
                self.assertEqual(self.client.post("/api/auth/login", json=self.payload, headers=self.headers).status_code, 401)
            response = self.client.post("/api/auth/login", json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 429)
        self.assertIn("retry-after", response.headers)
        self.assertEqual(login.call_count, 20)


class AuthServiceTests(unittest.TestCase):
    def test_password_hash_and_dummy_verification(self):
        password = "a sufficiently long password"
        stored = hash_password(password)
        self.assertTrue(stored.startswith("$argon2id$"))
        self.assertNotIn(password, stored)
        self.assertTrue(verify_password(stored, password))
        self.assertFalse(verify_password(stored, "incorrect"))
        self.assertFalse(verify_password(None, password))
        self.assertFalse(verify_password("invalid-hash", password))

    def test_register_uses_one_transaction_and_stores_only_token_hash(self):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        user = {"id": uuid4(), "email": "person@example.com"}
        with patch.object(auth_service, "get_connection", return_value=conn), \
             patch.object(auth_service.user_repository, "create_user", return_value=user) as create_user, \
             patch.object(auth_service.session_repository, "create_session") as create_session, \
             patch.object(auth_service.session_repository, "delete_session") as delete_session:
            result, token = auth_service.register(user["email"], "a sufficiently long password", "old-token")
        self.assertEqual(result, user)
        self.assertIs(create_user.call_args.args[0], conn)
        self.assertIs(create_session.call_args.args[0], conn)
        self.assertEqual(create_session.call_args.args[1], hash_token(token))
        self.assertEqual(delete_session.call_args.args[1], hash_token("old-token"))
        self.assertGreater(create_session.call_args.args[3], datetime.now(timezone.utc) + timedelta(days=6))
        conn.__exit__.assert_called_once_with(None, None, None)

    def test_register_failure_exits_transaction_with_error(self):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        with patch.object(auth_service, "get_connection", return_value=conn), \
             patch.object(auth_service.user_repository, "create_user", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                auth_service.register("person@example.com", "a sufficiently long password")
        self.assertIs(conn.__exit__.call_args.args[0], RuntimeError)

    def test_missing_and_wrong_password_have_same_error(self):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        with patch.object(auth_service, "get_connection", return_value=conn), \
             patch.object(auth_service.user_repository, "get_by_email") as get_user:
            for user in (None, {"password_hash": hash_password("a different password")}):
                get_user.return_value = user
                with self.assertRaisesRegex(InvalidCredentialsError, "Email o contraseña incorrectos"):
                    auth_service.login("person@example.com", "wrong password")

    def test_missing_or_oversized_session_does_not_open_database(self):
        with patch.object(auth_service, "get_connection") as connect:
            for token in (None, "", "x" * 500):
                self.assertIsNone(auth_service.get_current_user(token))
            connect.assert_not_called()

    def test_password_spaces_are_preserved(self):
        data = RegisterRequest(email="  PERSON@Example.com  ", password=" password with spaces ")
        self.assertEqual(data.email, "person@example.com")
        self.assertEqual(data.password.get_secret_value(), " password with spaces ")

    def test_production_requires_https_origin_and_database_url(self):
        with patch.object(config, "APP_ENV", "production"), patch.object(config, "COOKIE_SECURE", True), \
             patch.object(config, "DATABASE_URL", "postgresql://configured"), \
             patch.object(config, "AUTH_ALLOWED_ORIGINS", {"http://example.com"}):
            with self.assertRaises(RuntimeError):
                config.validate_auth_config()
        with patch.object(config, "DATABASE_URL", ""):
            with self.assertRaises(RuntimeError):
                config.validate_auth_config()


if __name__ == "__main__":
    unittest.main()
