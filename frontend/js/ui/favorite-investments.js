import { deleteFavoriteInvestment } from "../services/auth.js";
import { setFavoriteInvestments, state } from "../state.js";
import { renderBankPanel } from "./bank-panel.js";
import { capitalize, formatNumber } from "../utils/format.js";
import { escapeHtml } from "../utils/html.js";
import { term, withTerms } from "./glossary.js";

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
        ? `<div class="favorite-bank-group"><p class="favorite-bank-label">Mi banco</p><span class="favorite-bank-pill primary">${escapeHtml(state.primaryBank)}</span></div>`
        : "";
    const favorites = banks
        .filter((bank) => bank !== state.primaryBank)
        .map((bank) => `<span class="favorite-bank-pill">★ ${escapeHtml(bank)}</span>`)
        .join("");
    bankList.innerHTML = `<div class="favorite-bank-groups">${primary}${favorites ? `<div class="favorite-bank-group"><p class="favorite-bank-label">Bancos favoritos</p><div class="favorite-bank-pills">${favorites}</div></div>` : ""}</div>`;
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
        ? investmentMetrics(current)
        : `<p class="favorite-unavailable">No encontramos una versión actual de esta inversión.</p>`;
    return `
        <article class="favorite-investment-card">
            <header class="favorite-card-header">
                <div class="favorite-card-identity">
                    <p class="favorite-investment-bank">${escapeHtml(option.banco || "Entidad no informada")}</p>
                    <h4>${escapeHtml(option.nombre)}</h4>
                    <p class="favorite-investment-type"><span>${escapeHtml(option.tipo)}</span><span class="favorite-risk">Riesgo ${escapeHtml(capitalize(option.perfil_riesgo))}</span></p>
                </div>
                <span class="favorite-status ${escapeHtml(favorite.current_status)}">${statusText}</span>
            </header>
            <dl class="favorite-investment-context">
                <div><dt>Capital simulado</dt><dd>$${formatNumber(favorite.capital)}</dd></div>
                <div><dt>Plazo</dt><dd>${favorite.plazo} días</dd></div>
                <div><dt>Liquidez al guardar</dt><dd>${withTerms(option.liquidez)}</dd></div>
            </dl>
            <div class="favorite-comparison">
                <section class="favorite-value-panel" aria-label="Valores guardados">
                    <h5>Al guardar</h5>
                    ${investmentMetrics(option)}
                </section>
                <section class="favorite-value-panel favorite-value-panel-current" aria-label="Valores actuales">
                    <h5>Con datos actuales</h5>
                    ${currentDetails}
                </section>
            </div>
            <footer class="favorite-card-footer">
                <small>${favorite.current_updated_at ? `Fuente actualizada: ${escapeHtml(String(favorite.current_updated_at))}` : "Sin fecha de actualización disponible"}</small>
                <button type="button" class="btn btn-ghost remove-favorite-investment"
                        aria-label="Quitar ${escapeHtml(option.nombre)} de favoritos"
                        data-investment-key="${escapeHtml(favorite.investment_key)}">
                    Quitar de favoritos
                </button>
            </footer>
        </article>
    `;
}

function investmentMetrics(option) {
    const sign = option.rendimiento < 0 ? "−" : "+";
    return `
        <p class="favorite-gain-label">Rendimiento estimado</p>
        <strong class="favorite-gain${option.rendimiento < 0 ? " is-negative" : ""}">${sign}$${formatNumber(Math.abs(option.rendimiento))}</strong>
        <dl class="favorite-metrics">
            <div><dt>${term("tna", "TNA")}</dt><dd>${option.tna === null ? "No disponible" : `${formatNumber(option.tna)}%`}</dd></div>
            <div><dt>Monto final</dt><dd>$${formatNumber(option.monto_final)}</dd></div>
        </dl>
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
