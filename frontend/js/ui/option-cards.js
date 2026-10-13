// ============================================================================
// TARJETAS DE INVERSION
// Cada función recibe datos y devuelve el HTML de una tarjeta.
// ============================================================================

import { RISK_LEVELS } from "../config.js";
import { capitalize, formatNumber } from "../utils/format.js";
import { escapeHtml } from "../utils/html.js";

// Tarjeta de un plazo fijo. Calcula la ganancia para el capital ingresado.
export function fixedTermCard(plazo, banco, capital, destacado) {
    let dias;
    if (plazo.plazo_min === plazo.plazo_max) {
        dias = `${plazo.plazo_min} días`;
    } else {
        dias = `${plazo.plazo_min} a ${plazo.plazo_max} días`;
    }

    // Interés simple: capital x tasa anual x días / 365
    const diasDelPlazo = plazo.plazo_min;
    const ganancia = capital * (plazo.tna / 100) * (diasDelPlazo / 365);
    const total = capital + ganancia;

    return `
        <article class="option-card ${destacado ? "featured" : ""}">
            <div class="tags">
                <span class="tag tag-safe">Tasa fija</span>
            </div>
            <h4>Plazo fijo de ${dias}</h4>
            <p class="option-type">Tasa informada por ${escapeHtml(banco)}</p>
            <div class="option-highlight">
                <span>Ganancia para $${formatNumber(capital)}</span>
                <strong>+$${formatNumber(ganancia)}</strong>
            </div>
            <p class="option-total">
                Recibirías aproximadamente <strong>$${formatNumber(total)}</strong>
            </p>
            <ul class="option-details">
                ${detailRow("Rendimiento anual informado", `${formatNumber(plazo.tna)}%`)}
                ${detailRow("Disponibilidad", `Al finalizar ${diasDelPlazo} días`)}
            </ul>
        </article>
    `;
}

// Tarjeta de un fondo común de inversión. Los cálculos ya vienen del backend.
export function fundCard(fondo, plazo) {
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
                ${detailRow("TNA estimada", percentOrText(fondo.tna, "No disponible"))}
                ${detailRow("Rendimiento último día", percentOrText(fondo.rendimiento_ultimo_dia_pct, "No informado"))}
                ${detailRow("Liquidez", escapeHtml(fondo.liquidez))}
                ${detailRow("Acceso por app", escapeHtml(accesoApp), true)}
            </ul>
            <small class="option-note">No está garantizado y puede variar. Fuente: ${escapeHtml(fondo.fuente)}.</small>
        </article>
    `;
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
