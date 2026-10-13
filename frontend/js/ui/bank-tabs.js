// ============================================================================
// PESTAÑAS DE BANCOS
// Se generan desde config.js y se pueden recorrer con las flechas del teclado.
// ============================================================================

import { BANKS } from "../config.js";
import { escapeHtml } from "../utils/html.js";

const tabList = document.getElementById("bank-tabs");

/** Dibuja una pestaña por banco. onSelect recibe el nombre del banco. */
export function initBankTabs({ onSelect }) {
    tabList.innerHTML = BANKS.map((bank) => `
        <button
            type="button"
            class="bank-tab"
            role="tab"
            aria-selected="false"
            aria-controls="bank-panel"
            tabindex="-1"
            data-bank="${escapeHtml(bank.name)}"
        >${escapeHtml(bank.label)}</button>
    `).join("");

    const tabs = [...tabList.querySelectorAll(".bank-tab")];

    tabs.forEach((tab, index) => {
        tab.addEventListener("click", () => {
            setActiveBankTab(tab.dataset.bank);
            onSelect(tab.dataset.bank);
        });

        tab.addEventListener("keydown", (event) => {
            const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
            if (!step) return;
            event.preventDefault();
            const next = tabs[(index + step + tabs.length) % tabs.length];
            next.focus();
            next.click();
        });
    });
}

/** Marca como activa la pestaña del banco y la centra si hay desplazamiento. */
export function setActiveBankTab(bankName) {
    tabList.querySelectorAll(".bank-tab").forEach((tab) => {
        const active = tab.dataset.bank === bankName;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
        tab.tabIndex = active ? 0 : -1;

        if (active) {
            tab.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
        }
    });
}
