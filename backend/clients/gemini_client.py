"""Consulta a la inteligencia artificial Gemini (Google)."""

import httpx

from backend.core.config import (
    GEMINI_API_BASE_URL,
    GEMINI_HTTP_TIMEOUT_SECONDS,
    GEMINI_MAX_OUTPUT_TOKENS,
)


def generate_content(api_key: str, model: str, prompt: str) -> dict:
    """Envía el texto (prompt) a Gemini y devuelve su respuesta completa."""
    respuesta = httpx.post(
        f"{GEMINI_API_BASE_URL}/{model}:generateContent",
        headers={"x-goog-api-key": api_key},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS},
        },
        timeout=GEMINI_HTTP_TIMEOUT_SECONDS,
    )
    if respuesta.is_error:
        print(
            f"[GEMINI HTTP ERROR] status={respuesta.status_code} "
            f"detalle={respuesta.text[:500]}"
        )
        respuesta.raise_for_status()
    return respuesta.json()


def extract_text(datos: dict) -> str:
    """Saca el texto de la respuesta de Gemini.

    La respuesta viene así: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
    """
    candidatos = datos.get("candidates", [{}])
    partes = candidatos[0].get("content", {}).get("parts", [])

    textos = []
    for parte in partes:
        if parte.get("text"):
            textos.append(parte.get("text", "").strip())
    return " ".join(textos).strip()
