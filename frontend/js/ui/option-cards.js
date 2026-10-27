// ============================================================================
// TARJETAS DE INVERSION
// Cada función recibe datos y devuelve el HTML de una tarjeta.
// ============================================================================

import { RISK_LEVELS } from "../config.js";
import { capitalize, formatNumber } from "../utils/format.js";
import { escapeHtml } from "../utils/html.js";
import { term, withTerms } from "./glossary.js";
import { investmentKey, state } from "../state.js";

// Tarjeta del plazo fijo de un banco para el plazo que eligió el usuario.
// La tasa, la ganancia y el monto final ya vienen calculados por el backend.
export function fixedDepositCard(opcion, plazo, capital, optionIndex) {
    return `
        <article class="option-card featured">
            <div class="tags">
                <span class="tag tag-safe">Tasa fija</span>
                ${favoriteButton(opcion, capital, plazo, optionIndex)}
            </div>
            <h4>Plazo fijo a ${plazo} días</h4>
            <p class="option-type">${escapeHtml(opcion.horizonte)}</p>
            <div class="option-highlight">
                <span>Ganancia para $${formatNumber(capital)}</span>
                <strong>+$${formatNumber(opcion.rendimiento)}</strong>
            </div>
            <p class="option-total">
                Recibirías aproximadamente <strong>$${formatNumber(opcion.monto_final)}</strong>
            </p>
            <ul class="option-details">
                ${detailRow(`Tasa nominal anual (${term("tna", "TNA")})`, `${formatNumber(opcion.tna)}%`)}
                ${detailRow("Disponibilidad", escapeHtml(opcion.liquidez))}
            </ul>
        </article>
    `;
}

// Tabla chica con las tasas que publica el banco para cada plazo.
export function publishedRatesList(rangos) {
    let filas = "";
    rangos.forEach((rango) => {
        let dias;
        if (rango.plazo_min === rango.plazo_max) {
            dias = `${rango.plazo_min} días`;
        } else {
            dias = `${rango.plazo_min} a ${rango.plazo_max} días`;
        }
        filas += detailRow(dias, `${formatNumber(rango.tna)}%`);
    });

    return `
        <h5 class="bank-panel-title rates-title">Otras tasas que publica el banco</h5>
        <ul class="option-details rates-list">${filas}</ul>
    `;
}

// Tarjeta de un fondo común de inversión. Los cálculos ya vienen del backend.
export function fundCard(fondo, plazo, optionIndex) {
    // La etiqueta de riesgo toma el color verde, naranja o rojo según el nivel.
    let claseRiesgo = "";
    if (RISK_LEVELS.includes(fondo.perfil_riesgo)) {
        claseRiesgo = `tag-${fondo.perfil_riesgo}`;
    }

    const accesoApp = fondo.acceso_app || "Confirmá la disponibilidad en la app del banco.";

    return `
        <article class="option-card">
            <div class="tags">
                <span class="tag ${claseRiesgo}">Riesgo ${escapeHtml(fondo.perfil_riesgo)}</span>
                ${favoriteButton(fondo, state.capital, plazo, optionIndex)}
            </div>
            <h4>Fondo de inversión</h4>
            <p class="option-type">${escapeHtml(fondo.tipo)}</p>
            <p class="option-name">${escapeHtml(fondo.nombre)}</p>
            <div class="option-highlight">
                <span>Rendimiento estimado para ${plazo} días</span>
                <strong>${formatNumber(fondo.rendimiento_periodo_pct)}%</strong>
            </div>
            <p class="option-total">
                Ganancia estimada para ${plazo} días:
                <strong>$${formatNumber(fondo.rendimiento)}</strong>
            </p>
            <ul class="option-details">
                ${detailRow("Perfil de riesgo", escapeHtml(capitalize(fondo.perfil_riesgo)))}
                ${detailRow(`${term("tna", "TNA")} estimada`, percentOrText(fondo.tna, "No disponible"))}
                ${detailRow("Rendimiento último día", percentOrText(fondo.rendimiento_ultimo_dia_pct, "No informado"))}
                ${detailRow("Liquidez", withTerms(fondo.liquidez))}
                ${detailRow("Acceso por app", escapeHtml(accesoApp), true)}
            </ul>
            <small class="option-note">No está garantizado y puede variar. Fuente: ${escapeHtml(fondo.fuente)}.</small>
        </article>
    `;
}

function favoriteButton(option, capital, plazo, optionIndex) {
    const key = investmentKey(option, capital, plazo);
    const active = state.favoriteInvestments.some((favorite) => favorite.investment_key === key);
    return `<button type="button" class="favorite-investment" data-option-index="${optionIndex}"
        aria-label="${active ? "Quitar inversión de favoritos" : "Guardar inversión en favoritos"}"
        aria-pressed="${active}">${active ? "★" : "☆"}</button>`;
}

// Una fila "etiqueta ... valor". Con enDosLineas=true el valor va debajo
// (se usa para textos largos).
function detailRow(etiqueta, valor, enDosLineas = false) {
    const clase = enDosLineas ? ' class="stacked"' : "";
    return `<li${clase}><span>${etiqueta}</span><span>${valor}</span></li>`;
}

// Si hay valor muestra "12,50%"; si no, el texto alternativo.
function percentOrText(valor, textoAlternativo) {
    if (valor === null) {
        return textoAlternativo;
    }
    return `${formatNumber(valor)}%`;
}
