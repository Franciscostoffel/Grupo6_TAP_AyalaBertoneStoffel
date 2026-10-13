// ============================================================================
// PESTAÑAS DE BANCOS
// Se crean a partir de la lista BANKS de config.js.
// ============================================================================

import { BANKS } from "../config.js";
import { escapeHtml } from "../utils/html.js";

const tabList = document.getElementById("bank-tabs");

// Crea un botón por banco. alElegir recibe el nombre del banco tocado.
export function initBankTabs(alElegir) {
    let html = "";
    BANKS.forEach((banco) => {
        html += `
            <button
                type="button"
                class="bank-tab"
                role="tab"
                aria-selected="false"
                aria-controls="bank-panel"
                tabindex="-1"
                data-bank="${escapeHtml(banco.name)}"
            >${escapeHtml(banco.label)}</button>
        `;
    });
    tabList.innerHTML = html;

    const tabs = tabList.querySelectorAll(".bank-tab");

    tabs.forEach((tab, posicion) => {
        tab.addEventListener("click", () => {
            setActiveBankTab(tab.dataset.bank);
            alElegir(tab.dataset.bank);
        });

        // Con las flechas del teclado se pasa al banco siguiente o anterior.
        tab.addEventListener("keydown", (event) => {
            let siguiente;
            if (event.key === "ArrowRight") {
                siguiente = posicion + 1;
            } else if (event.key === "ArrowLeft") {
                siguiente = posicion - 1;
            } else {
                return;
            }
            event.preventDefault();

            // Si se pasa del último vuelve al primero, y al revés.
            if (siguiente >= tabs.length) siguiente = 0;
            if (siguiente < 0) siguiente = tabs.length - 1;

            tabs[siguiente].focus();
            tabs[siguiente].click();
        });
    });
}

// Marca como activa la pestaña del banco elegido.
export function setActiveBankTab(nombreBanco) {
    const tabs = tabList.querySelectorAll(".bank-tab");
    tabs.forEach((tab) => {
        const activa = tab.dataset.bank === nombreBanco;
        tab.classList.toggle("active", activa);
        tab.setAttribute("aria-selected", String(activa));
        tab.tabIndex = activa ? 0 : -1;

        // En celulares la fila se desliza: llevamos la pestaña elegida a la vista.
        if (activa) {
            tab.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
        }
    });
}
