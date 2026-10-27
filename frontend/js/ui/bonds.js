// ============================================================================
// APARTADO DE BONOS
// Dos tablas: bonos a tasa fija (se comparan con un plazo fijo) y bonos que
// ajustan por inflación (CER). Los números ya vienen calculados del backend.
// ============================================================================

import { BOND_SECTIONS } from "../config.js";
import { formatNumber } from "../utils/format.js";
import { escapeHtml } from "../utils/html.js";
import { term } from "./glossary.js";

const panel = document.getElementById("bonds-panel");

// Último listado recibido, el plazo del análisis (0 si no hubo) y la pestaña elegida.
let bonos = null;
let plazo = 0;
let seccion = BOND_SECTIONS.FIXED_RATE;

// Al tocar una pestaña se vuelve a dibujar con la sección elegida.
panel.addEventListener("click", (event) => {
    const boton = event.target.closest(".subtab");
    if (boton === null) {
        return;
    }
    seccion = boton.dataset.section;
    renderBonds();
});

export function showBondsMessage(mensaje) {
    panel.innerHTML = `<div class="empty-state">${escapeHtml(mensaje)}</div>`;
}

export function setBonds(datos, plazoElegido = 0) {
    bonos = datos;
    plazo = plazoElegido;
    renderBonds();
}

export function clearBonds() {
    bonos = null;
    plazo = 0;
    seccion = BOND_SECTIONS.FIXED_RATE;
    panel.replaceChildren();
}

function renderBonds() {
    let html = `
        <div class="subtabs" role="group" aria-label="Tipo de bono">
            ${tabButton(BOND_SECTIONS.FIXED_RATE, "Tasa fija", bonos.tasa_fija.length)}
            ${tabButton(BOND_SECTIONS.CER, "Ajustan por CER", bonos.cer.length)}
        </div>
    `;
    if (seccion === BOND_SECTIONS.FIXED_RATE) {
        html += fixedRateTable();
    } else {
        html += cerTable();
    }
    panel.innerHTML = html;
}

function tabButton(valor, texto, cantidad) {
    const activa = valor === seccion;
    return `
        <button type="button" class="subtab ${activa ? "active" : ""}"
                data-section="${valor}" aria-pressed="${activa}">
            ${texto} <span class="subtab-count">${cantidad}</span>
        </button>
    `;
}

function fixedRateTable() {
    const conCapital = bonos.capital !== null;
    const masCercano = closestToTerm(bonos.tasa_fija);

    let filas = "";
    bonos.tasa_fija.forEach((bono) => {
        const destacado = bono === masCercano;
        filas += `
            <tr class="${destacado ? "highlight" : ""}">
                <th scope="row">
                    ${escapeHtml(bono.ticker)}
                    ${destacado ? `<span class="tag tag-safe">Cerca de tus ${plazo} días</span>` : ""}
                </th>
                <td>${formatDate(bono.fecha_vencimiento)}</td>
                <td class="num">${bono.dias_al_vencimiento}</td>
                <td class="num">$${formatNumber(bono.precio)}</td>
                <td class="num">${formatNumber(bono.tna)}%</td>
                <td class="num">${formatNumber(bono.tea)}%</td>
                <td class="num">${formatNumber(bono.rendimiento_pct)}%</td>
                ${conCapital ? `<td class="num"><strong>+$${formatNumber(bono.ganancia)}</strong></td>` : ""}
            </tr>
        `;
    });

    let nota = "";
    if (conCapital) {
        nota = ` La ganancia está calculada para tus <strong>$${formatNumber(bonos.capital)}</strong>.`;
    }

    return `
        <p class="panel-note">
            Las LECAP y BONCAP pagan una tasa fija en pesos y devuelven el capital
            al vencimiento, como un plazo fijo. El rendimiento supone comprarlas hoy
            al precio de mercado y esperar al vencimiento, sin comisiones.${nota}
        </p>
        ${table(["Bono", "Vence", "Días", "Precio", term("tna", "TNA"), term("tea", "TEA"), term("vencimiento", "Rinde al vencer"), conCapital ? "Ganancia" : null], filas)}
    `;
}

function cerTable() {
    let filas = "";
    bonos.cer.forEach((bono) => {
        filas += `
            <tr>
                <th scope="row">${escapeHtml(bono.ticker)}</th>
                <td>${formatDate(bono.fecha_vencimiento)}</td>
                <td class="num">${bono.dias_al_vencimiento}</td>
                <td class="num">$${formatNumber(bono.precio)}</td>
                <td class="num">${formatNumber(bono.tir)}%</td>
            </tr>
        `;
    });

    return `
        <p class="panel-note">
            Su capital se ajusta por inflación (índice CER). La TIR indica cuánto
            rinden <strong>por encima</strong> de la inflación: una TIR de 5% significa
            inflación + 5% anual. Como la inflación futura no se conoce, no
            calculamos la ganancia en pesos.
        </p>
        ${table(["Bono", "Vence", "Días", "Precio", "TIR real"], filas)}
    `;
}

// Arma la tabla. Las dos primeras columnas son texto y el resto números
// (van alineados a la derecha). Los títulos en null se omiten.
function table(titulos, filas) {
    let encabezado = "";
    titulos.forEach((titulo, posicion) => {
        if (titulo === null) {
            return;
        }
        const clase = posicion >= 2 ? ' class="num"' : "";
        encabezado += `<th scope="col"${clase}>${titulo}</th>`;
    });

    return `
        <div class="table-scroll">
            <table class="bonds-table">
                <thead><tr>${encabezado}</tr></thead>
                <tbody>${filas}</tbody>
            </table>
        </div>
    `;
}

// El bono que vence más cerca del plazo del análisis (null si no hubo análisis).
function closestToTerm(lista) {
    let elegido = null;
    if (plazo === 0) {
        return elegido;
    }
    lista.forEach((bono) => {
        if (elegido === null
                || Math.abs(bono.dias_al_vencimiento - plazo) < Math.abs(elegido.dias_al_vencimiento - plazo)) {
            elegido = bono;
        }
    });
    return elegido;
}

// "2027-01-15" -> "15/01/2027"
function formatDate(fechaIso) {
    const [anio, mes, dia] = fechaIso.split("-");
    return `${dia}/${mes}/${anio}`;
}
