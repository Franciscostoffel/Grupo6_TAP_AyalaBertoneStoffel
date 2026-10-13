// ============================================================================
// PUNTO DE ENTRADA DE LA INTERFAZ
// Conecta los modulos: el formulario pide el analisis, el estado lo guarda y
// las vistas lo dibujan.
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

initBankTabs({
    onSelect: (bankName) => {
        state.selectedBank = bankName;
        renderBankPanel();
    }
});

initForm({ onSubmit: handleAnalyze });

async function handleAnalyze(request) {
    setFormLoading(true);
    showLoading();

    try {
        const data = await analyzeInvestment(request);

        setAnalysis(data);
        setActiveBankTab(state.selectedBank);
        renderBankPanel();
        showResults(data);
    } catch (error) {
        hideLoading();
        showFormError(error.message);
    } finally {
        setFormLoading(false);
    }
}
