// ============================================================================
// PUNTO DE ENTRADA DE LA INTERFAZ
// Conecta las partes: el formulario pide el análisis, el estado lo guarda y
// las vistas lo dibujan en pantalla.
// ============================================================================

import { analyzeInvestment } from "./services/api.js";
import { setAnalysis, state } from "./state.js";
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

// Se ejecuta al tocar una pestaña de banco.
function alElegirBanco(nombreBanco) {
    state.selectedBank = nombreBanco;
    renderBankPanel();
}

// Se ejecuta al enviar el formulario con datos válidos.
async function analizar(datos) {
    setFormLoading(true);
    showLoading();

    try {
        const resultado = await analyzeInvestment(datos);

        setAnalysis(resultado);
        setActiveBankTab(state.selectedBank);
        renderBankPanel();
        showResults(resultado);
    } catch (error) {
        hideLoading();
        showFormError(error.message);
    } finally {
        setFormLoading(false);
    }
}
