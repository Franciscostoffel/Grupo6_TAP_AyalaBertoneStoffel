import { deleteFavoriteInvestment } from "../services/auth.js";
import { setFavoriteInvestments, state } from "../state.js";
import { renderBankPanel } from "./bank-panel.js";
import { capitalize, formatNumber } from "../utils/format.js";
import { escapeHtml } from "../utils/html.js";

const dashboardList = document.getElementById("favorite-investments-dashboard-list");
const bankList = document.getElementById("favorite-banks-list");
const section = document.getElementById("favorites-dashboard");

export function renderFavoriteInvestments() {
    renderInvestmentList(dashboardList);
    renderBankList();
}

function renderInvestmentList(list) {
    if (state.favoriteInvestments.length === 0) {
        list.innerHTML = `<p class="empty-state">Todavía no guardaste inversiones favoritas.</p>`;
        return;
    }
    list.innerHTML = state.favoriteInvestments.map(favoriteCard).join("");
}

function renderBankList() {
    const banks = state.favoriteBanks;
    if (!state.primaryBank && banks.length === 0) {
        bankList.innerHTML = `<p class="empty-state">Todavía no elegiste un banco.</p>`;
        return;
    }
    const primary = state.primaryBank
        ? `<span class="favorite-bank-pill primary">Mi banco: ${escapeHtml(state.primaryBank)}</span>`
        : "";
    const favorites = banks
        .filter((bank) => bank !== state.primaryBank)
        .map((bank) => `<span class="favorite-bank-pill">★ ${escapeHtml(bank)}</span>`)
        .join("");
    bankList.innerHTML = `<div class="favorite-bank-pills">${primary}${favorites}</div>`;
}

function favoriteCard(favorite) {
    const option = favorite.option_data;
    const current = favorite.current_option;
    const statusText = favorite.current_status === "actualizada"
        ? "Hay datos nuevos"
        : favorite.current_status === "no_disponible"
            ? "Ya no está disponible"
            : "Datos vigentes";
    const currentDetails = current
        ? `<div class="favorite-current-details">
                <strong>Actual: +$${formatNumber(current.rendimiento)}</strong>
                <span>TNA ${current.tna === null ? "No disponible" : `${formatNumber(current.tna)}%`} · Monto final $${formatNumber(current.monto_final)}</span>
           </div>`
        : `<p class="favorite-unavailable">No encontramos una versión actual de esta inversión.</p>`;
    return `
        <article class="favorite-investment-card">
            <div>
                <p class="favorite-investment-bank">${escapeHtml(option.banco || "Entidad no informada")}</p>
                <h3>${escapeHtml(option.nombre)}</h3>
                <p class="muted">${escapeHtml(option.tipo)} · Riesgo ${escapeHtml(capitalize(option.perfil_riesgo))}</p>
                <small class="favorite-saved-details">Guardada con TNA ${option.tna === null ? "no disponible" : `${formatNumber(option.tna)}%`} · Monto final $${formatNumber(option.monto_final)} · ${escapeHtml(option.liquidez)}</small>
            </div>
            <div class="favorite-investment-result">
                <span class="favorite-status ${favorite.current_status}">${statusText}</span>
                <strong>Guardado: +$${formatNumber(option.rendimiento)}</strong>
                <span>${favorite.plazo} días · Capital $${formatNumber(favorite.capital)}</span>
            </div>
            <div class="favorite-investment-current">
                ${currentDetails}
                ${favorite.current_updated_at ? `<small>Fuente actualizada: ${escapeHtml(String(favorite.current_updated_at))}</small>` : ""}
            </div>
            <button type="button" class="btn btn-ghost remove-favorite-investment"
                    data-investment-key="${escapeHtml(favorite.investment_key)}">
                Quitar
            </button>
        </article>
    `;
}

section.addEventListener("click", async (event) => {
    const button = event.target.closest(".remove-favorite-investment");
    if (!button) return;
    button.disabled = true;
    try {
        await deleteFavoriteInvestment(button.dataset.investmentKey);
        setFavoriteInvestments(state.favoriteInvestments.filter(
            (favorite) => favorite.investment_key !== button.dataset.investmentKey
        ));
        renderFavoriteInvestments();
        if (state.options.length > 0) renderBankPanel();
    } catch (error) {
        button.disabled = false;
        window.alert(error.message);
    }
});
