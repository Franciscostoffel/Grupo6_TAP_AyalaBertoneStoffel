// ============================================================================
// COMUNICACION CON EL BACKEND
// ============================================================================

import { ANALYZE_ENDPOINT } from "../config.js";

// Le pide al backend el análisis. Si algo sale mal, lanza un Error con un
// mensaje listo para mostrarle al usuario.
export async function analyzeInvestment(datos) {
    let respuesta;

    try {
        respuesta = await fetch(ANALYZE_ENDPOINT, {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json", "X-Requested-With": "fetch" },
            body: JSON.stringify(datos)
        });
    } catch (error) {
        // fetch solo falla así cuando no hay conexión con el servidor.
        throw new Error("No pudimos conectarnos con el servidor. Probá de nuevo en unos segundos.");
    }

    if (!respuesta.ok) {
        // El backend manda los errores así: { "detail": "mensaje" }
        let mensaje = "Ocurrió un error al analizar la inversión.";
        try {
            const cuerpo = await respuesta.json();
            if (typeof cuerpo.detail === "string") {
                mensaje = cuerpo.detail;
            }
        } catch (error) {
            // La respuesta no era JSON: dejamos el mensaje genérico.
        }
        const error = new Error(mensaje);
        error.status = respuesta.status;
        throw error;
    }

    return respuesta.json();
}
