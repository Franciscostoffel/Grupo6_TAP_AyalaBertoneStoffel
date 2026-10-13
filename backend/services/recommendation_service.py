"""Arma el texto de recomendación: con Gemini si está disponible, o uno propio si falla."""

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
    """Pide la recomendación a Gemini y espera como máximo 5 segundos.

    asyncio.to_thread ejecuta la consulta en otro hilo para que el servidor
    pueda seguir atendiendo a otros usuarios mientras espera a Gemini.
    asyncio.wait_for corta la espera si pasa el tiempo máximo.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(generar_recomendacion_gemini, capital, plazo, riesgo, opciones),
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
    """Le pide a Gemini un texto breve que explique la mejor opción."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return RECOMENDACION_NO_CONFIGURADA

    modelo = os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
    try:
        respuesta = gemini_client.generate_content(
            api_key=api_key,
            model=modelo,
            prompt=armar_prompt(capital, plazo, riesgo, opciones),
        )
        recomendacion = gemini_client.extract_text(respuesta)

        # Solo aceptamos la respuesta si tiene texto y al menos un número.
        if recomendacion and tiene_numeros(recomendacion):
            uso = respuesta.get("usageMetadata", "no informado")
            print(f"[GEMINI OK] modelo={modelo} intento=1 uso={uso}")
            return recomendacion
        raise ValueError("Gemini devolvió una respuesta vacía o sin números en dígitos.")
    except Exception as error:
        print(f"[GEMINI ERROR] modelo={modelo} intento=1: {error}")
        return generar_recomendacion_local(opciones, plazo)


def generar_recomendacion_local(opciones: list[EntityResult], plazo: int) -> str:
    """Recomendación armada por nosotros cuando Gemini falla o tarda demasiado."""
    mejor = opciones[0]  # las opciones ya vienen ordenadas de mayor a menor ganancia
    banco = mejor.banco or "no informado por la fuente"

    if mejor.tna is not None:
        tna = f", con una TNA de referencia del {formato_argentino(mejor.tna)}%"
    else:
        tna = ""

    return (
        f"La opción destacada es {mejor.nombre}, banco asociado: {banco}{tna}. "
        f"Ganancia estimada: ${formato_argentino(mejor.rendimiento)}; "
        f"monto final: ${formato_argentino(mejor.monto_final)}; {mejor.liquidez}. "
        "Es una simulación orientativa y el rendimiento no está garantizado."
    )


def formato_argentino(numero: float) -> str:
    """Escribe el número como en Argentina: 212492.84 -> "212.492,84".

    Python usa el formato inglés (212,492.84), así que intercambiamos los
    separadores: primero la coma pasa a "X", después el punto a coma y al
    final la "X" a punto.
    """
    texto = f"{numero:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def tiene_numeros(texto: str) -> bool:
    for caracter in texto:
        if caracter.isdigit():
            return True
    return False


def armar_prompt(capital: float, plazo: int, riesgo: str, opciones: list[EntityResult]) -> str:
    """Arma las instrucciones que se le mandan a Gemini."""
    # Solo mandamos las 10 mejores opciones para no hacer el texto muy largo.
    opciones_para_prompt = []
    for opcion in opciones[:GEMINI_MAX_OPTIONS_IN_PROMPT]:
        opciones_para_prompt.append(opcion.model_dump())

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
