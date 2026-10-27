"""Arma el resumen informativo: con Gemini si está disponible, o uno propio si falla.

Es solo una descripción de los resultados calculados. No debe aconsejar
ni recomendar invertir: eso es asesoramiento financiero y está regulado.
"""

import asyncio
import json
import os

from backend.clients import gemini_client
from backend.core.config import GEMINI_DEFAULT_MODEL, RECOMMENDATION_TIMEOUT_SECONDS
from backend.schemas.investment import EntityResult

CAMPOS_PARA_PROMPT = {
    "nombre", "banco", "tipo", "perfil_riesgo", "tna", "garantizado",
    "rendimiento", "monto_final", "liquidez",
}

RECOMENDACION_NO_CONFIGURADA = (
    "El resumen con IA no está configurado. "
    "Los resultados se calcularon con los datos disponibles."
)

RECOMENDACION_SIN_BANCOS = (
    "No hay opciones de los bancos o billeteras de la aplicación para ese nivel "
    "de riesgo. Es una simulación informativa, no una recomendación de inversión."
)


async def get_recommendation(
    capital: float,
    plazo: int,
    riesgo: str,
    opciones: list[EntityResult],
) -> str:
    """Pide el resumen a Gemini y espera como máximo 5 segundos.

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
        print("[GEMINI TIMEOUT] Se usa el resumen local.")
        return generar_recomendacion_local(opciones, plazo)


def generar_recomendacion_gemini(
    capital: float,
    plazo: int,
    riesgo: str,
    opciones: list[EntityResult],
) -> str:
    """Le pide a Gemini un texto breve que describa la opción de mayor ganancia."""
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
        if (recomendacion and tiene_numeros(recomendacion)
                and opciones[0].banco.lower() in recomendacion.lower()):
            uso = respuesta.get("usageMetadata", "no informado")
            print(f"[GEMINI OK] modelo={modelo} intento=1 uso={uso}")
            return recomendacion
        raise ValueError("Gemini devolvió una respuesta vacía, sin números o sin el banco.")
    except Exception as error:
        print(f"[GEMINI ERROR] modelo={modelo} intento=1: {error}")
        return generar_recomendacion_local(opciones, plazo)


def generar_recomendacion_local(opciones: list[EntityResult], plazo: int) -> str:
    """Resumen armado por nosotros cuando Gemini falla o tarda demasiado."""
    mejor = opciones[0]  # las opciones ya vienen ordenadas de mayor a menor ganancia

    if mejor.tna is not None:
        tna = f", con una TNA de referencia del {formato_argentino(mejor.tna)}%"
    else:
        tna = ""

    if mejor.garantizado:
        garantia = "tasa fija pactada"
    else:
        garantia = "rendimiento no garantizado"

    return (
        f"Según los datos, la opción con mayor ganancia estimada es {mejor.nombre} "
        f"de {mejor.banco}{tna} (riesgo {mejor.perfil_riesgo}, {garantia}). "
        f"Ganancia estimada: ${formato_argentino(mejor.rendimiento)}; "
        f"monto final: ${formato_argentino(mejor.monto_final)}; {mejor.liquidez}. "
        "Es una simulación informativa, no una recomendación de inversión."
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
    opcion =opciones[0].model_dump(include=CAMPOS_PARA_PROMPT)
    if opcion["tna"] is not None:
        opcion["tna"] = round(opcion["tna"], 2)

    return f"""
Actúa como un asistente que describe datos en una aplicación argentina.
NO eres asesor financiero: no recomiendes, no aconsejes ni sugieras invertir
en nada, y no uses palabras como "recomiendo", "te conviene", "deberías" o
"la mejor opción para vos". Solo describe los resultados de forma neutral.
El usuario quiere invertir ${capital:,.2f} ARS durante {plazo} días y acepta un
nivel de riesgo '{riesgo}'.

Esta es la opción con mayor ganancia estimada, ya calculada por el sistema:
{json.dumps(opcion, ensure_ascii=False)}

Redacta un resumen informativo muy breve y claro de esa opción.
Responde únicamente en texto plano, sin Markdown, títulos, viñetas, símbolos
como # o **, saludos ni explicaciones largas. Usa como máximo 3 oraciones y
70 palabras. Escribe todos los números usando dígitos, nunca con palabras:
por ejemplo, "$100.000", "30 días", "41,81%" y "$102.953,70". Usa siempre
"$" para importes, "%" para porcentajes y dígitos para los días. Indica
siempre el nombre de esa opción y el banco o billetera del campo "banco",
escrito exactamente igual (por ejemplo "Fima Renta Plus de Banco Galicia").
Incluye también la ganancia estimada, el monto final, su liquidez y su
perfil de riesgo (campo "perfil_riesgo"); si "garantizado" es false aclara
que el rendimiento no está garantizado. Menciona la TNA solo como referencia
si está disponible. Usa exclusivamente los datos recibidos, no inventes
información ni asegures rendimientos.
Termina con una sola frase breve indicando que es una simulación informativa,
no una recomendación de inversión.
"""
