// ============================================================================
// PESTAÑAS DE BANCOS Y BILLETERAS
// Se crean a partir de las listas BANKS y WALLETS de config.js.
// ============================================================================

import { BANKS, SECTIONS, WALLETS } from "../config.js";
import { escapeHtml } from "../utils/html.js";
import { orderEntities, sectionOptions } from "../utils/investment-order.js";
import { getPreferences, savePreferences } from "../services/auth.js";
import { state, setBankPreferences } from "../state.js";

const tabList = document.getElementById("bank-tabs");
const primaryBankSelect = document.getElementById("primary-bank");
const favoritesFilter = document.getElementById("favorites-filter");
let selectBank;

// Crea un botón por banco y por billetera. alElegir recibe el nombre tocado.
export function initBankTabs(alElegir) {
    selectBank = alElegir;
    primaryBankSelect.insertAdjacentHTML("beforeend", BANKS.map((bank) =>
        `<option value="${escapeHtml(bank.name)}">${escapeHtml(bank.name)}</option>`
    ).join(""));
    refreshBankTabs();
    tabList.addEventListener("click", toggleFavorite);
    primaryBankSelect.addEventListener("change", () => updatePreferences(primaryBankSelect.value || null));
    favoritesFilter.addEventListener("click", () => {
        state.favoriteOnly = !state.favoriteOnly;
        refreshBankTabs();
    });
}

// Regenera el orden sin perder la seleccion, las estrellas ni el filtro.
export function refreshBankTabs() {
    renderTabs(selectBank);
    renderPreferenceState();
    setActiveBankTab(state.selectedBank);
}

function renderTabs(alElegir) {
    let html = "";
    const visibleOptions = sectionOptions(state.options, state.selectedSection);
    orderEntities(BANKS, visibleOptions, state.primaryBank, state.favoriteBanks).forEach((banco) => {
        html += tabButton(banco);
    });
    html += `<span id="wallets-label" class="tab-group-label">Billeteras</span>`;
    orderEntities(WALLETS, sectionOptions(state.options, SECTIONS.FUNDS)).forEach((billetera) => {
        html += tabButton(billetera);
    });
    tabList.innerHTML = html;

    const tabs = tabList.querySelectorAll(".bank-tab");
    tabs.forEach((tab, posicion) => {
        tab.addEventListener("click", () => {
            setActiveBankTab(tab.dataset.bank);
            alElegir(tab.dataset.bank);
        });
        tab.addEventListener("keydown", (event) => {
            let siguiente;
            if (event.key === "ArrowRight") siguiente = posicion + 1;
            else if (event.key === "ArrowLeft") siguiente = posicion - 1;
            else return;
            event.preventDefault();
            if (siguiente >= tabs.length) siguiente = 0;
            if (siguiente < 0) siguiente = tabs.length - 1;
            tabs[siguiente].focus();
            tabs[siguiente].click();
        });
    });
    applyFavoriteFilter();
}

function tabButton(entidad) {
    return `
        <span class="bank-tab-wrap" data-bank-wrap="${escapeHtml(entidad.name)}">
            <button type="button" class="bank-tab" role="tab" aria-selected="false"
                    aria-controls="bank-panel" tabindex="-1" data-bank="${escapeHtml(entidad.name)}">
                ${escapeHtml(entidad.label)}
            </button>
            ${isBank(entidad.name) ? `<button type="button" class="favorite-bank" aria-label="Agregar ${escapeHtml(entidad.label)} a favoritos"
                data-favorite-bank="${escapeHtml(entidad.name)}" aria-pressed="false">☆</button>` : ""}
        </span>
    `;
}

function isBank(name) {
    return BANKS.some((bank) => bank.name === name);
}

function toggleFavorite(event) {
    const button = event.target.closest(".favorite-bank");
    if (!button) return;
    event.stopPropagation();
    const bank = button.dataset.favoriteBank;
    const favorites = state.favoriteBanks.includes(bank)
        ? state.favoriteBanks.filter((name) => name !== bank)
        : [...state.favoriteBanks, bank];
    updatePreferences(state.primaryBank, favorites);
}

async function updatePreferences(primaryBank, favoriteBanks = state.favoriteBanks) {
    const updatedFavorites = primaryBank && !favoriteBanks.includes(primaryBank)
        ? [primaryBank, ...favoriteBanks]
        : favoriteBanks;
    primaryBankSelect.disabled = true;
    tabList.querySelectorAll(".favorite-bank").forEach((button) => { button.disabled = true; });
    try {
        const preferences = await savePreferences({
            primary_bank: primaryBank,
            favorite_banks: updatedFavorites
        });
        setBankPreferences(preferences);
        document.dispatchEvent(new CustomEvent("bank-preferences-changed"));
        refreshBankTabs();
        if (primaryBank) {
            setActiveBankTab(primaryBank);
            selectBank(primaryBank);
        }
        if (state.favoriteOnly && state.favoriteBanks.length === 0) {
            state.favoriteOnly = false;
        }
        applyFavoriteFilter();
        renderPreferenceState();
    } catch (error) {
        window.alert(error.message);
        primaryBankSelect.value = state.primaryBank || "";
    } finally {
        primaryBankSelect.disabled = false;
        tabList.querySelectorAll(".favorite-bank").forEach((button) => { button.disabled = false; });
    }
}

export async function loadBankPreferences() {
    try {
        const preferences = await getPreferences();
        setBankPreferences(preferences);
        document.dispatchEvent(new CustomEvent("bank-preferences-changed"));
        refreshBankTabs();
        if (state.primaryBank) {
            setActiveBankTab(state.primaryBank);
            selectBank(state.primaryBank);
        }
    } catch (error) {
        window.alert(error.message);
    }
}

function renderPreferenceState() {
    primaryBankSelect.value = state.primaryBank || "";
    tabList.querySelectorAll(".favorite-bank").forEach((button) => {
        const active = state.favoriteBanks.includes(button.dataset.favoriteBank);
        button.textContent = active ? "★" : "☆";
        button.setAttribute("aria-pressed", String(active));
        button.setAttribute("aria-label", active ? "Quitar de favoritos" : "Agregar a favoritos");
    });
    applyFavoriteFilter();
    favoritesFilter.disabled = state.favoriteBanks.length === 0;
    favoritesFilter.textContent = state.favoriteOnly ? "★ Ver todos los bancos" : "★ Ver solo favoritos";
    favoritesFilter.setAttribute("aria-pressed", String(state.favoriteOnly));
}

function applyFavoriteFilter() {
    tabList.querySelectorAll(".bank-tab-wrap").forEach((wrapper) => {
        wrapper.classList.toggle(
            "hidden",
            state.favoriteOnly && !state.favoriteBanks.includes(wrapper.dataset.bankWrap)
        );
    });
    const walletsLabel = document.getElementById("wallets-label");
    if (walletsLabel) walletsLabel.classList.toggle("hidden", state.favoriteOnly);
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
