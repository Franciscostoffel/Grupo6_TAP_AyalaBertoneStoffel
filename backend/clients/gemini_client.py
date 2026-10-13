"""Cliente de la API de Gemini (Google AI Studio)."""

import httpx

from backend.core.config import GEMINI_API_BASE_URL, GEMINI_HTTP_TIMEOUT_SECONDS


def generate_content(api_key: str, model: str, prompt: str) -> dict:
    """Envía el prompt al modelo y devuelve la respuesta JSON completa."""
    response = httpx.post(
        f"{GEMINI_API_BASE_URL}/{model}:generateContent",
        headers={"x-goog-api-key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=GEMINI_HTTP_TIMEOUT_SECONDS,
    )
    if response.is_error:
        print(
            f"[GEMINI HTTP ERROR] status={response.status_code} "
            f"detalle={response.text[:500]}"
        )
        response.raise_for_status()
    return response.json()


def extract_text(response_data: dict) -> str:
    """Une los fragmentos de texto del primer candidato de la respuesta."""
    parts = (
        response_data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    return " ".join(
        part.get("text", "").strip()
        for part in parts
        if part.get("text")
    ).strip()
