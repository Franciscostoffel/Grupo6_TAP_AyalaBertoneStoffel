// ============================================================================
// ESTADO DE LA PANTALLA
// Guarda el ultimo analisis recibido para volver a dibujar las opciones al
// cambiar de banco o de seccion sin consultar otra vez al backend.
// ============================================================================

import { BANKS, SECTIONS } from "./config.js";

export const state = {
    capital: 0,
    plazo: 0,
    funds: [],
    fixedTerms: [],
    selectedBank: BANKS[0].name,
    selectedSection: SECTIONS.FIXED_TERM
};

export function setAnalysis(data) {
    state.capital = data.capital;
    state.plazo = data.plazo;
    state.funds = data.opciones;
    state.fixedTerms = data.plazos_fijos;
    state.selectedBank = BANKS[0].name;
    state.selectedSection = SECTIONS.FIXED_TERM;
}
