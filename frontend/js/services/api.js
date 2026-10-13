// ============================================================================
// COMUNICACION CON EL BACKEND
// ============================================================================

import { ANALYZE_ENDPOINT } from "../config.js";

/**
 * Pide al backend el analisis de inversiones.
 * Lanza un Error con un mensaje listo para mostrar al usuario.
 */
export async function analyzeInvestment({ capital, plazo, riesgo }) {
    let response;

    try {
        response = await fetch(ANALYZE_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ capital, plazo, riesgo })
        });
    } catch {
        throw new Error("No pudimos conectarnos con el servidor. Probá de nuevo en unos segundos.");
    }

    if (!response.ok) {
        // FastAPI devuelve { detail: "..." } en los errores controlados.
        const body = await response.json().catch(() => null);
        throw new Error(
            typeof body?.detail === "string"
                ? body.detail
                : "Ocurrió un error al analizar la inversión."
        );
    }

    return response.json();
}
