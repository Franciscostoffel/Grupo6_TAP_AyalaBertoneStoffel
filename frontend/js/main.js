// ============================================================================
// PUNTO DE ENTRADA DE LA INTERFAZ
// Conecta las partes: el formulario pide el análisis, el estado lo guarda y
// las vistas lo dibujan en pantalla.
// ============================================================================

import { analyzeInvestment } from "./services/api.js";
import { clearSessionState, setAnalysis, state } from "./state.js";
import { initAuth, showSignedOut } from "./ui/auth.js";
import { initBankTabs, setActiveBankTab } from "./ui/bank-tabs.js";
import { renderBankPanel } from "./ui/bank-panel.js";
import { initForm, setFormLoading, showFormError } from "./ui/form.js";
import { hideLoading, showLoading, showResults } from "./ui/results.js";
import { initThemeToggle } from "./ui/theme.js";
import { initInfoTooltip } from "./ui/tooltip.js";

initThemeToggle();
initInfoTooltip();
initBankTabs(alElegirBanco);
initForm(analizar);

let sessionVersion = 0;
initAuth({
    onAuthenticated(user) {
        sessionVersion += 1;
        state.user = user;
    },
    onSignedOut() {
        sessionVersion += 1;
        clearSessionState();
        document.getElementById("investment-form").reset();
        document.getElementById("results").classList.add("hidden");
        document.getElementById("bank-panel").replaceChildren();
        document.getElementById("ai-recommendation").textContent = "";
        document.getElementById("error-message").classList.add("hidden");
        hideLoading();
        setFormLoading(false);
    }
});

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
