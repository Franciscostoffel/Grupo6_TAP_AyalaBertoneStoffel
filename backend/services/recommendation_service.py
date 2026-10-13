"""Recomendación en texto: Gemini cuando está disponible, o una local si falla."""

from __future__ import annotations

import asyncio
import json
import os

from backend.clients import gemini_client
from backend.core.config import (
    GEMINI_DEFAULT_MODEL,
    GEMINI_MAX_OPTIONS_IN_PROMPT,
    RECOMMENDATION_TIMEOUT_SECONDS,
)
from backend.schemas.investment import EntityResult

RECOMENDACION_NO_CONFIGURADA = (
    "La recomendación de IA no está configurada. "
    "La opción principal se calculó con los datos disponibles."
)


async def get_recommendation(
    capital: float,
    plazo: int,
    riesgo: str,
    opciones: list[EntityResult],
) -> str:
    """Pide la recomendación a Gemini con un tiempo máximo de espera.

    La llamada a Gemini es síncrona, así que corre en otro hilo para no
    bloquear el event loop de FastAPI mientras espera la respuesta.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(
                generar_recomendacion_gemini, capital, plazo, riesgo, opciones
            ),
            timeout=RECOMMENDATION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        print("[GEMINI TIMEOUT] Se usa la recomendación local.")
        return generar_recomendacion_local(opciones, plazo)


def generar_recomendacion_gemini(
    capital: float,
    plazo: int,
    riesgo: str,
    opciones: list[EntityResult],
) -> str:
    """Genera una explicación breve de las opciones usando Gemini."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return RECOMENDACION_NO_CONFIGURADA

    model = os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
    intento = 1
    try:
        response_data = gemini_client.generate_content(
            api_key=api_key,
            model=model,
            prompt=_build_prompt(capital, plazo, riesgo, opciones),
        )
        recomendacion = gemini_client.extract_text(response_data)
        if recomendacion and any(char.isdigit() for char in recomendacion):
            usage = response_data.get("usageMetadata", "no informado")
            print(
                f"[GEMINI OK] modelo={model} intento={intento} "
                f"uso={usage}"
            )
            return recomendacion
        raise ValueError(
            "Gemini devolvió una respuesta vacía o sin números en dígitos."
        )
    except Exception as error:
        print(f"[GEMINI ERROR] modelo={model} intento={intento}: {error}")
        return generar_recomendacion_local(opciones, plazo)


def generar_recomendacion_local(
    opciones: list[EntityResult],
    plazo: int,
) -> str:
    """Recomendación determinística cuando Gemini no responde a tiempo o falla."""
    mejor = opciones[0]
    banco = mejor.banco or "no informado por la fuente"
    tna = (
        f", con una TNA de referencia del {mejor.tna:.2f}%"
        if mejor.tna is not None
        else ""
    )
    return (
        f"La opción destacada es {mejor.nombre}, banco asociado: {banco}{tna}. "
        f"Ganancia estimada: ${mejor.rendimiento:,.2f}; "
        f"monto final: ${mejor.monto_final:,.2f}; {mejor.liquidez}. "
        "Es una simulación orientativa y el rendimiento no está garantizado."
    )


def _build_prompt(
    capital: float,
    plazo: int,
    riesgo: str,
    opciones: list[EntityResult],
) -> str:
    # Se limita el contexto para evitar prompts innecesariamente grandes.
    opciones_para_prompt = [
        opcion.model_dump() for opcion in opciones[:GEMINI_MAX_OPTIONS_IN_PROMPT]
    ]
    return f"""
Actúa como un asesor financiero claro y prudente para una aplicación argentina.
El usuario quiere invertir ${capital:,.2f} ARS durante {plazo} días y acepta un
nivel de riesgo '{riesgo}'.

Estas son las opciones ya filtradas y calculadas por el sistema:
{json.dumps(opciones_para_prompt, ensure_ascii=False, indent=2)}

Redacta una recomendación muy breve, clara y agradable para el usuario.
Responde únicamente en texto plano, sin Markdown, títulos, viñetas, símbolos
como # o **, saludos ni explicaciones largas. Usa como máximo 3 oraciones y
70 palabras. Escribe todos los números usando dígitos, nunca con palabras:
por ejemplo, "$100.000", "30 días", "41,81%" y "$102.953,70". Usa siempre
"$" para importes, "%" para porcentajes y dígitos para los días. Indica
siempre el nombre de la opción elegida y escribe "Banco asociado: no informado
por la fuente" si el campo banco está vacío. Incluye también el banco asociado
cuando esté disponible, la ganancia estimada, el monto final y su liquidez;
menciona la TNA solo como referencia si está disponible. Usa exclusivamente
los datos recibidos, no inventes información ni asegures rendimientos.
Termina con una sola frase breve indicando que es una simulación orientativa
y que los rendimientos no están garantizados.
"""
