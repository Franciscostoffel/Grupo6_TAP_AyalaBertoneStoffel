// ============================================================================
// ESTADO DE LA PANTALLA
// Guarda el ultimo analisis recibido para volver a dibujar las opciones al
// cambiar de banco o de seccion sin consultar otra vez al backend.
// ============================================================================

import { BANKS, SECTIONS } from "./config.js";

export const state = {
    user: null,
    capital: 0,
    plazo: 0,
    risk: "",
    options: [],       // todas las opciones calculadas por el backend
    fixedTerms: [],    // tasas que publica cada banco por rango de días
    primaryBank: null,
    favoriteBanks: [],
    favoriteOnly: false,
    favoriteInvestments: [],
    selectedBank: BANKS[0].name,
    selectedSection: SECTIONS.FIXED_TERM
};

export function clearSessionState() {
    state.user = null;
    state.capital = 0;
    state.plazo = 0;
    state.risk = "";
    state.options = [];
    state.fixedTerms = [];
    state.primaryBank = null;
    state.favoriteBanks = [];
    state.favoriteOnly = false;
    state.favoriteInvestments = [];
    state.selectedBank = state.primaryBank || BANKS[0].name;
    state.selectedSection = SECTIONS.FIXED_TERM;
}

export function setBankPreferences(preferences) {
    state.primaryBank = preferences.primary_bank;
    state.favoriteBanks = preferences.favorite_banks;
}

export function setFavoriteInvestments(investments) {
    state.favoriteInvestments = investments;
}

export function investmentKey(option, capital, plazo) {
    return [option.banco || "", option.nombre, option.tipo, capital, plazo].join("|");
}

export function setAnalysis(data) {
    state.capital = data.capital;
    state.plazo = data.plazo;
    state.risk = data.riesgo;
    state.options = data.opciones;
    state.fixedTerms = data.plazos_fijos;
    state.selectedBank = state.primaryBank || BANKS[0].name;
    state.selectedSection = SECTIONS.FIXED_TERM;
}
