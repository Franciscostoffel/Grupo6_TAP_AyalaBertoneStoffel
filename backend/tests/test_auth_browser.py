"""Opcional: TEST_DATABASE_URL + RUN_BROWSER_TESTS=1; requiere Playwright y Edge.

Instalar solo en desarrollo: uv pip install --python .venv/Scripts/python.exe playwright
Ejecutar: python -m unittest backend.tests.test_auth_browser -v
Usa un servidor local y una base exclusiva de pruebas, nunca el .env.
"""

import os
import socket
import tempfile
import threading
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import psycopg
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from psycopg.conninfo import conninfo_to_dict

from backend.api import dependencies
from backend.api.routes import analysis, auth
from backend.core.config import FRONTEND_PATH
from backend.db import schema
from backend.services import auth_service


@unittest.skipUnless(os.getenv("RUN_BROWSER_TESTS") == "1" and os.getenv("TEST_DATABASE_URL"),
                     "Requiere RUN_BROWSER_TESTS=1, TEST_DATABASE_URL y Playwright con Edge")
class AuthBrowserTests(unittest.TestCase):
    def test_browser_registration_reload_expiry_login_logout_and_network_retry(self):
        from playwright.sync_api import sync_playwright

        url = os.environ["TEST_DATABASE_URL"]
        if "test" not in conninfo_to_dict(url).get("dbname", "").lower():
            raise RuntimeError("Usar una base exclusiva cuyo nombre contenga test.")
        email = f"auth-browser-{uuid4()}@example.com"
        password = "browser test password phrase"
        artifacts = Path(tempfile.gettempdir()) / "inversion-auth-preview"
        artifacts.mkdir(exist_ok=True)
        with ExitStack() as stack:
            for target in (schema, auth_service):
                stack.enter_context(patch.object(target, "get_connection", side_effect=lambda: psycopg.connect(url)))
            schema.init_db()
            def cleanup_user():
                with psycopg.connect(url) as conn:
                    conn.execute("DELETE FROM users WHERE email = %s", (email,))
            stack.callback(cleanup_user)
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            origin = f"http://127.0.0.1:{sock.getsockname()[1]}"
            stack.enter_context(patch.object(dependencies, "AUTH_ALLOWED_ORIGINS", {origin}))
            stack.enter_context(patch.object(dependencies, "auth_rate_limiter", dependencies.AuthRateLimiter()))
            stack.enter_context(patch.object(dependencies, "SESSION_COOKIE_NAME", "session"))
            stack.enter_context(patch.object(auth, "SESSION_COOKIE_NAME", "session"))
            stack.enter_context(patch.object(auth, "COOKIE_SECURE", False))
            app = FastAPI()
            app.include_router(auth.router)
            app.include_router(analysis.router)
            app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True))
            server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off", ws="none"))
            thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
            thread.start()
            def stop_server():
                server.should_exit = True
                thread.join(timeout=10)
                sock.close()
            stack.callback(stop_server)
            for _ in range(200):
                if server.started:
                    break
                time.sleep(0.05)
            self.assertTrue(server.started)
            playwright = stack.enter_context(sync_playwright())
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            stack.callback(browser.close)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(origin)
            page.locator("#auth-form").wait_for(state="visible")
            self.assertFalse(page.locator("#app-content").is_visible())
            page.screenshot(path=str(artifacts / "login-desktop.png"), full_page=True, animations="disabled")

            page.locator("#auth-toggle").click()
            page.locator("#auth-email").fill(email)
            page.locator("#auth-password").fill(password)
            page.locator("#auth-submit").click()
            page.locator("#app-content").wait_for(state="visible")
            self.assertEqual(page.locator("#user-email").inner_text(), email)
            cookies = context.cookies()
            self.assertTrue(next(cookie for cookie in cookies if cookie["name"] == "session")["httpOnly"])
            self.assertNotIn("session=", page.evaluate("document.cookie"))
            page.reload()
            page.locator("#app-content").wait_for(state="visible")
            page.screenshot(path=str(artifacts / "app-desktop.png"), full_page=True, animations="disabled")

            # Vence la sesión en la base; el siguiente análisis debe volver al login.
            with psycopg.connect(url) as conn:
                conn.execute("""
                    UPDATE user_sessions SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 days',
                    expires_at = CURRENT_TIMESTAMP - INTERVAL '1 day'
                    WHERE user_id IN (SELECT id FROM users WHERE email = %s)
                """, (email,))
            page.locator("#capital").fill("100000")
            page.locator('input[name="plazo"][value="30"]').check(force=True)
            page.locator('input[name="riesgo"][value="bajo"]').check(force=True)
            page.locator("#analyze-button").click()
            page.locator("#auth-form").wait_for(state="visible")
            self.assertIn("venció", page.locator("#session-feedback").inner_text())
            self.assertFalse(page.locator("#app-content").is_visible())

            page.locator("#auth-email").fill(email)
            page.locator("#auth-password").fill("incorrect password")
            page.locator("#auth-submit").click()
            page.get_by_text("Email o contraseña incorrectos.", exact=True).wait_for()
            page.locator("#auth-password").fill(password)
            page.locator("#auth-submit").click()
            page.locator("#app-content").wait_for(state="visible")

            # Un análisis pendiente no debe volver a mostrar datos tras logout.
            pending = []
            page.route("**/api/analyze", lambda route: pending.append(route))
            page.locator("#capital").fill("100000")
            page.locator('input[name="plazo"][value="30"]').check(force=True)
            page.locator('input[name="riesgo"][value="bajo"]').check(force=True)
            page.locator("#analyze-button").click()
            page.wait_for_function("document.querySelector('#analyze-button').disabled")
            page.locator("#logout-button").click()
            page.locator("#auth-form").wait_for(state="visible")
            self.assertEqual(len(pending), 1)
            pending[0].fulfill(json={"capital": 100000, "plazo": 30, "riesgo": "bajo", "opciones": [],
                                     "plazos_fijos": [], "recomendacion": "Respuesta anterior"})
            page.wait_for_function("document.querySelector('#ai-recommendation').textContent === ''")
            self.assertFalse(page.locator("#results").is_visible())
            self.assertFalse(any(cookie["name"] == "session" for cookie in context.cookies()))

            page.set_viewport_size({"width": 390, "height": 844})
            page.emulate_media(color_scheme="dark")
            page.screenshot(path=str(artifacts / "login-mobile-dark.png"), full_page=True, animations="disabled")
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 390)
            page.route("**/api/auth/me", lambda route: route.abort())
            page.reload()
            page.locator("#auth-retry").wait_for(state="visible")
            self.assertFalse(page.locator("#app-content").is_visible())
            page.unroute("**/api/auth/me")
            page.locator("#auth-retry").click()
            page.locator("#auth-form").wait_for(state="visible")
            self.assertEqual(errors, [])
            print(f"Capturas de revisión: {artifacts}")
