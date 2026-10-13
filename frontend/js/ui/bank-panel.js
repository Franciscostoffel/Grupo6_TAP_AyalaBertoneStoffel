// ============================================================================
// PANEL DEL BANCO SELECCIONADO
// Encabezado del banco, selector Plazo fijo / Fondos y tarjetas de opciones.
// ============================================================================

import { BANKS, SECTIONS } from "../config.js";
import { state } from "../state.js";
import { escapeHtml } from "../utils/html.js";
import { externalLinkIcon } from "./icons.js";
import { fixedTermCard, fundCard } from "./option-cards.js";

const panel = document.getElementById("bank-panel");

// Un solo listener para los botones de seccion, que se regeneran en cada render.
panel.addEventListener("click", (event) => {
    const subtab = event.target.closest(".subtab");
    if (!subtab) return;
    state.selectedSection = subtab.dataset.section;
    renderBankPanel();
});

/** Dibuja el panel para state.selectedBank y state.selectedSection. */
export function renderBankPanel() {
    const bank = state.selectedBank;
    const section = state.selectedSection;
    const fixedTerms = state.fixedTerms.filter((item) => item.banco === bank);
    const funds = state.funds.filter((item) => item.banco === bank && !item.garantizado);

    panel.innerHTML = `
        ${bankHeader(bank)}
        ${sectionSwitcher(section, fixedTerms.length, funds.length)}
        ${section === SECTIONS.FIXED_TERM
            ? fixedTermsList(bank, fixedTerms)
            : fundsList(funds)}
    `;
}


// ----------------------------------------------------------------------------
// Partes del panel
// ----------------------------------------------------------------------------

function bankHeader(bank) {
    const url = BANKS.find((item) => item.name === bank)?.url;

    return `
        <div class="bank-header">
            <div>
                <h4>${escapeHtml(bank)}</h4>
                <p>Resultados calculados para el monto y plazo ingresados.</p>
            </div>
            ${url
                ? `<a class="bank-link" href="${url}" target="_blank" rel="noopener">Ir al sitio del banco ${externalLinkIcon}</a>`
                : ""}
        </div>
    `;
}

function sectionSwitcher(section, fixedTermCount, fundCount) {
    const button = (value, label, count) => `
        <button
            type="button"
            class="subtab ${section === value ? "active" : ""}"
            data-section="${value}"
            aria-pressed="${section === value}"
        >
            ${label} <span class="subtab-count">${count}</span>
        </button>
    `;

    return `
        <div class="subtabs" role="group" aria-label="Tipo de inversión">
            ${button(SECTIONS.FIXED_TERM, "Plazo fijo", fixedTermCount)}
            ${button(SECTIONS.FUNDS, "Fondos de inversión", fundCount)}
        </div>
    `;
}

function fixedTermsList(bank, fixedTerms) {
    if (!fixedTerms.length) {
        return `<div class="empty-state">Este banco no tiene una tasa disponible en la fuente consultada.</div>`;
    }

    const cards = fixedTerms
        .map((term, index) => fixedTermCard(term, {
            bank,
            capital: state.capital,
            featured: index === 0
        }))
        .join("");

    return `
        <h5 class="bank-panel-title">Plazos fijos disponibles</h5>
        <div class="option-grid">${cards}</div>
    `;
}

function fundsList(funds) {
    if (!funds.length) {
        return `<div class="empty-state">No encontramos fondos asociados a este banco en la fuente consultada.</div>`;
    }

    const cards = funds
        .map((fund) => fundCard(fund, { plazo: state.plazo }))
        .join("");

    return `
        <h5 class="bank-panel-title">Fondos relacionados con este banco</h5>
        <div class="option-grid">${cards}</div>
    `;
}
