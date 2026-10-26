// ============================================================================
// SECCIONES DE CARGA Y RESULTADOS
// ============================================================================

import { capitalize, formatNumber } from "../utils/format.js";

const loading = document.getElementById("loading");
const results = document.getElementById("results");
const resultCapital = document.getElementById("result-capital");
const resultPlazo = document.getElementById("result-plazo");
const resultRisk = document.getElementById("result-risk");
const aiRecommendation = document.getElementById("ai-recommendation");

export function showLoading() {
    results.classList.add("hidden");
    loading.classList.remove("hidden");
    loading.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function hideLoading() {
    loading.classList.add("hidden");
}

/** Completa los datos y el resumen de IA, y muestra la seccion de resultados. */
export function showResults(data) {
    resultCapital.textContent = formatNumber(data.capital);
    resultPlazo.textContent = data.plazo;
    resultRisk.textContent = capitalize(data.riesgo);
    aiRecommendation.textContent = data.recomendacion;

    hideLoading();
    results.classList.remove("hidden");
    results.focus({ preventScroll: true });
    results.scrollIntoView({ behavior: "smooth", block: "start" });
}
