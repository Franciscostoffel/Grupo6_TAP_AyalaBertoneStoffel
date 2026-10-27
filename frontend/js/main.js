// ============================================================================
// PUNTO DE ENTRADA DE LA INTERFAZ
// Conecta las partes: el formulario pide el análisis, el estado lo guarda y
// las vistas lo dibujan en pantalla.
// ============================================================================

import { analyzeInvestment } from "./services/api.js";
import { clearSessionState, setAnalysis, state } from "./state.js";
import { initAuth, showSignedOut } from "./ui/auth.js";
import { initBankTabs, loadBankPreferences, setActiveBankTab } from "./ui/bank-tabs.js";
import { renderBankPanel } from "./ui/bank-panel.js";
import { initForm, setFormLoading, showFormError } from "./ui/form.js";
import { hideLoading, showLoading, showResults } from "./ui/results.js";
import { initThemeToggle } from "./ui/theme.js";
import { initInfoTooltip } from "./ui/tooltip.js";
import { getFavoriteInvestments } from "./services/auth.js";
import { renderFavoriteInvestments } from "./ui/favorite-investments.js";
import { setFavoriteInvestments } from "./state.js";

const simulatorView = document.getElementById("simulador");
const loadingView = document.getElementById("loading");
const resultsView = document.getElementById("results");
const favoritesView = document.getElementById("favorites-dashboard");
const howView = document.getElementById("como-funciona");

initThemeToggle();
initInfoTooltip();
document.addEventListener("favorite-investments-changed", renderFavoriteInvestments);
document.addEventListener("bank-preferences-changed", renderFavoriteInvestments);
document.querySelectorAll("[data-app-view]").forEach((link) => {
    link.addEventListener("click", (event) => {
        event.preventDefault();
        showAppView(link.dataset.appView);
    });
});
document.querySelector('a[href="#como-funciona"]').addEventListener("click", (event) => {
    event.preventDefault();
    showAppView("simulator");
    howView.scrollIntoView({ behavior: "smooth", block: "start" });
    howView.classList.remove("section-highlight");
    requestAnimationFrame(() => howView.classList.add("section-highlight"));
    window.setTimeout(() => howView.classList.remove("section-highlight"), 1800);
});
initBankTabs(alElegirBanco);
initForm(analizar);

let sessionVersion = 0;
initAuth({
    onAuthenticated(user) {
        sessionVersion += 1;
        state.user = user;
        showAppView("simulator");
        loadBankPreferences();
        refreshFavoriteInvestments();
    },
    onSignedOut() {
        sessionVersion += 1;
        clearSessionState();
        renderFavoriteInvestments();
        document.getElementById("investment-form").reset();
        document.getElementById("results").classList.add("hidden");
        document.getElementById("bank-panel").replaceChildren();
        document.getElementById("ai-recommendation").textContent = "";
        document.getElementById("error-message").classList.add("hidden");
        hideLoading();
        setFormLoading(false);
    }
});

function showAppView(view) {
    const showFavorites = view === "favorites";
    simulatorView.classList.toggle("hidden", showFavorites);
    if (showFavorites) loadingView.classList.add("hidden");
    howView.classList.toggle("hidden", showFavorites);
    if (showFavorites) resultsView.classList.add("hidden");
    favoritesView.classList.toggle("hidden", !showFavorites);
    if (showFavorites) {
        refreshFavoriteInvestments();
        favoritesView.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
        if (state.options.length > 0) resultsView.classList.remove("hidden");
        simulatorView.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

async function refreshFavoriteInvestments() {
    try {
        const favorites = await getFavoriteInvestments();
        setFavoriteInvestments(favorites);
        renderFavoriteInvestments();
    } catch (error) {
        window.alert(error.message);
    }
}

// Se ejecuta al tocar una pestaña de banco.
function alElegirBanco(nombreBanco) {
    state.selectedBank = nombreBanco;
    renderBankPanel();
}

// Se ejecuta al enviar el formulario con datos válidos.
async function analizar(datos) {
    if (!state.user) return;
    const requestVersion = sessionVersion;
    setFormLoading(true);
    showLoading();

    try {
        const resultado = await analyzeInvestment(datos);
        if (requestVersion !== sessionVersion) return;

        setAnalysis(resultado);
        setActiveBankTab(state.selectedBank);
        renderBankPanel();
        showResults(resultado);
    } catch (error) {
        if (requestVersion !== sessionVersion) return;
        hideLoading();
        if (error.status === 401) {
            showSignedOut("Tu sesión venció. Iniciá sesión nuevamente.");
            return;
        }
        showFormError(error.message);
    } finally {
        if (requestVersion === sessionVersion) setFormLoading(false);
    }
}
