// ============================================================================
// PUNTO DE ENTRADA DE LA INTERFAZ
// Conecta las partes: el formulario pide el análisis, el estado lo guarda y
// las vistas lo dibujan en pantalla.
// ============================================================================

import { analyzeInvestment, fetchBonds } from "./services/api.js";
import { clearSessionState, setAnalysis, state } from "./state.js";
import { initAuth, showSignedOut } from "./ui/auth.js";
import { initBankTabs, setActiveBankTab } from "./ui/bank-tabs.js";
import { renderBankPanel } from "./ui/bank-panel.js";
import { clearBonds, setBonds, showBondsMessage } from "./ui/bonds.js";
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
        cargarBonos();
    },
    onSignedOut() {
        sessionVersion += 1;
        bondsVersion += 1;
        clearSessionState();
        document.getElementById("investment-form").reset();
        document.getElementById("results").classList.add("hidden");
        document.getElementById("bank-panel").replaceChildren();
        document.getElementById("ai-recommendation").textContent = "";
        document.getElementById("error-message").classList.add("hidden");
        clearBonds();
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
        cargarBonos(resultado.capital, resultado.plazo);
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

// Carga el apartado de bonos. Después de un análisis se pide con el capital
// para que el backend calcule la ganancia de cada bono a tasa fija.
// Solo se dibuja la respuesta del último pedido.
let bondsVersion = 0;
async function cargarBonos(capital = null, plazo = 0) {
    bondsVersion += 1;
    const requestVersion = bondsVersion;
    showBondsMessage("Cargando bonos...");

    try {
        const bonos = await fetchBonds(capital);
        if (requestVersion !== bondsVersion) return;
        setBonds(bonos, plazo);
    } catch (error) {
        if (requestVersion !== bondsVersion) return;
        if (error.status === 401) {
            showSignedOut("Tu sesión venció. Iniciá sesión nuevamente.");
            return;
        }
        showBondsMessage(error.message);
    }
}
