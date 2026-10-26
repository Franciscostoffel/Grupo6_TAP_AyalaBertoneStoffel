// ============================================================================
// COMUNICACION CON EL BACKEND
// ============================================================================

import { ANALYZE_ENDPOINT, BONDS_ENDPOINT } from "../config.js";

// Le pide al backend el análisis. Si algo sale mal, lanza un Error con un
// mensaje listo para mostrarle al usuario.
export async function analyzeInvestment(datos) {
    const respuesta = await request(ANALYZE_ENDPOINT, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-Requested-With": "fetch" },
        body: JSON.stringify(datos)
    });

    if (!respuesta.ok) {
        throw await errorFromResponse(respuesta, "Ocurrió un error al analizar la inversión.");
    }
    return respuesta.json();
}

// Pide las letras y bonos. Con capital, el backend calcula la ganancia de cada uno.
export async function fetchBonds(capital = null) {
    let url = BONDS_ENDPOINT;
    if (capital !== null) {
        url += `?capital=${encodeURIComponent(capital)}`;
    }

    const respuesta = await request(url, { credentials: "same-origin" });

    if (!respuesta.ok) {
        throw await errorFromResponse(respuesta, "No pudimos obtener los bonos.");
    }
    return respuesta.json();
}

async function request(url, opciones) {
    try {
        return await fetch(url, opciones);
    } catch (error) {
        // fetch solo falla así cuando no hay conexión con el servidor.
        throw new Error("No pudimos conectarnos con el servidor. Probá de nuevo en unos segundos.");
    }
}

// El backend manda los errores así: { "detail": "mensaje" }
async function errorFromResponse(respuesta, mensajePorDefecto) {
    let mensaje = mensajePorDefecto;
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
    return error;
}
