// ============================================================================
// PANEL DEL BANCO SELECCIONADO
// Muestra el nombre del banco, los botones "Plazo fijo / Fondos" y las tarjetas.
// ============================================================================

import { BANKS, SECTIONS } from "../config.js";
import { state } from "../state.js";
import { escapeHtml } from "../utils/html.js";
import { externalLinkIcon } from "./icons.js";
import { fixedTermCard, fundCard } from "./option-cards.js";

const panel = document.getElementById("bank-panel");

// Los botones "Plazo fijo" y "Fondos" se vuelven a crear cada vez que se dibuja
// el panel, por eso escuchamos los clics en el panel y vemos qué botón fue.
panel.addEventListener("click", (event) => {
    const boton = event.target.closest(".subtab");
    if (boton === null) {
        return;
    }
    state.selectedSection = boton.dataset.section;
    renderBankPanel();
});

// Dibuja el panel del banco y la sección que están guardados en state.
export function renderBankPanel() {
    const banco = state.selectedBank;
    const seccion = state.selectedSection;

    const plazosDelBanco = state.fixedTerms.filter((plazo) => plazo.banco === banco);
    const fondosDelBanco = state.funds.filter((fondo) => fondo.banco === banco && !fondo.garantizado);

    let contenido;
    if (seccion === SECTIONS.FIXED_TERM) {
        contenido = fixedTermsList(banco, plazosDelBanco);
    } else {
        contenido = fundsList(fondosDelBanco);
    }

    panel.innerHTML =
        bankHeader(banco) +
        sectionSwitcher(seccion, plazosDelBanco.length, fondosDelBanco.length) +
        contenido;
}


// ----------------------------------------------------------------------------
// Partes del panel
// ----------------------------------------------------------------------------

function bankHeader(banco) {
    const url = findBankUrl(banco);
    let enlace = "";
    if (url) {
        enlace = `<a class="bank-link" href="${url}" target="_blank" rel="noopener">Ir al sitio del banco ${externalLinkIcon}</a>`;
    }

    return `
        <div class="bank-header">
            <div>
                <h4>${escapeHtml(banco)}</h4>
                <p>Resultados calculados para el monto y plazo ingresados.</p>
            </div>
            ${enlace}
        </div>
    `;
}

// Busca en config.js el sitio oficial del banco (no todos lo tienen).
function findBankUrl(nombreBanco) {
    for (const banco of BANKS) {
        if (banco.name === nombreBanco) {
            return banco.url;
        }
    }
    return undefined;
}

function sectionSwitcher(seccionActiva, cantidadPlazos, cantidadFondos) {
    return `
        <div class="subtabs" role="group" aria-label="Tipo de inversión">
            ${sectionButton(SECTIONS.FIXED_TERM, "Plazo fijo", cantidadPlazos, seccionActiva)}
            ${sectionButton(SECTIONS.FUNDS, "Fondos de inversión", cantidadFondos, seccionActiva)}
        </div>
    `;
}

function sectionButton(seccion, texto, cantidad, seccionActiva) {
    const activa = seccion === seccionActiva;
    return `
        <button
            type="button"
            class="subtab ${activa ? "active" : ""}"
            data-section="${seccion}"
            aria-pressed="${activa}"
        >
            ${texto} <span class="subtab-count">${cantidad}</span>
        </button>
    `;
}

function fixedTermsList(banco, plazos) {
    if (plazos.length === 0) {
        return `<div class="empty-state">Este banco no tiene una tasa disponible en la fuente consultada.</div>`;
    }

    let tarjetas = "";
    plazos.forEach((plazo, posicion) => {
        const destacado = posicion === 0; // el primero se resalta con borde
        tarjetas += fixedTermCard(plazo, banco, state.capital, destacado);
    });

    return `
        <h5 class="bank-panel-title">Plazos fijos disponibles</h5>
        <div class="option-grid">${tarjetas}</div>
    `;
}

function fundsList(fondos) {
    if (fondos.length === 0) {
        return `<div class="empty-state">No encontramos fondos asociados a este banco en la fuente consultada.</div>`;
    }

    let tarjetas = "";
    fondos.forEach((fondo) => {
        tarjetas += fundCard(fondo, state.plazo);
    });

    return `
        <h5 class="bank-panel-title">Fondos relacionados con este banco</h5>
        <div class="option-grid">${tarjetas}</div>
    `;
}
