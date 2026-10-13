// ============================================================================
// PLANTILLAS DE TARJETAS DE INVERSION
// Funciones puras: reciben datos y devuelven HTML (con los textos escapados).
// ============================================================================

import { RISK_LEVELS } from "../config.js";
import { capitalize, formatNumber } from "../utils/format.js";
import { escapeHtml } from "../utils/html.js";

/** Tarjeta de un plazo fijo con la ganancia calculada para el capital. */
export function fixedTermCard(term, { bank, capital, featured }) {
    const dias = term.plazo_min === term.plazo_max
        ? `${term.plazo_min} días`
        : `${term.plazo_min} a ${term.plazo_max} días`;
    const termDays = term.plazo_min;
    const ganancia = capital * (term.tna / 100) * (termDays / 365);
    const total = capital + ganancia;

    return `
        <article class="option-card ${featured ? "featured" : ""}">
            <div class="tags">
                <span class="tag tag-safe">Tasa fija</span>
            </div>
            <h4>Plazo fijo de ${dias}</h4>
            <p class="option-type">Tasa informada por ${escapeHtml(bank)}</p>
            <div class="option-highlight">
                <span>Ganancia para $${formatNumber(capital)}</span>
                <strong>+$${formatNumber(ganancia)}</strong>
            </div>
            <p class="option-total">
                Recibirías aproximadamente <strong>$${formatNumber(total)}</strong>
            </p>
            <ul class="option-details">
                ${detailRow("Rendimiento anual informado", `${formatNumber(term.tna)}%`)}
                ${detailRow("Disponibilidad", `Al finalizar ${termDays} días`)}
            </ul>
        </article>
    `;
}

/** Tarjeta de un fondo comun de inversion con el rendimiento estimado. */
export function fundCard(fund, { plazo }) {
    const riskClass = RISK_LEVELS.includes(fund.perfil_riesgo)
        ? `tag-${fund.perfil_riesgo}`
        : "";

    return `
        <article class="option-card">
            <div class="tags">
                <span class="tag ${riskClass}">Riesgo ${escapeHtml(fund.perfil_riesgo)}</span>
            </div>
            <h4>Fondo de inversión</h4>
            <p class="option-type">${escapeHtml(fund.tipo)}</p>
            <p class="option-name">${escapeHtml(fund.nombre)}</p>
            <div class="option-highlight">
                <span>Rendimiento estimado para ${plazo} días</span>
                <strong>${formatNumber(fund.rendimiento_periodo_pct)}%</strong>
            </div>
            <p class="option-total">
                Ganancia estimada para ${plazo} días:
                <strong>$${formatNumber(fund.rendimiento)}</strong>
            </p>
            <ul class="option-details">
                ${detailRow("Perfil de riesgo", escapeHtml(capitalize(fund.perfil_riesgo)))}
                ${detailRow("TNA estimada", formatPercentOr(fund.tna, "No disponible"))}
                ${detailRow("Rendimiento último día", formatPercentOr(fund.rendimiento_ultimo_dia_pct, "No informado"))}
                ${detailRow("Liquidez", escapeHtml(fund.liquidez))}
                ${detailRow(
                    "Acceso por app",
                    escapeHtml(fund.acceso_app || "Confirmá la disponibilidad en la app del banco."),
                    { stacked: true }
                )}
            </ul>
            <small class="option-note">No está garantizado y puede variar. Fuente: ${escapeHtml(fund.fuente)}.</small>
        </article>
    `;
}

// El valor ya debe venir escapado o ser generado por nosotros.
function detailRow(label, value, { stacked = false } = {}) {
    return `<li${stacked ? ' class="stacked"' : ""}><span>${label}</span><span>${value}</span></li>`;
}

function formatPercentOr(value, fallback) {
    return value !== null ? `${formatNumber(value)}%` : fallback;
}
