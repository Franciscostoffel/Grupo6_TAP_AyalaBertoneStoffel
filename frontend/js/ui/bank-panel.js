// ============================================================================
// PANEL DEL BANCO O BILLETERA SELECCIONADO
// Muestra el nombre, los botones "Plazo fijo / Fondos" y las tarjetas.
// ============================================================================

import { BANKS, FIXED_DEPOSIT_TYPE, SECTIONS, WALLETS } from "../config.js";
import { state } from "../state.js";
import { investmentKey } from "../state.js";
import { saveFavoriteInvestment, deleteFavoriteInvestment } from "../services/auth.js";
import { escapeHtml } from "../utils/html.js";
import { externalLinkIcon } from "./icons.js";
import { fixedDepositCard, fundCard, publishedRatesList } from "./option-cards.js";

const panel = document.getElementById("bank-panel");

// Los botones "Plazo fijo" y "Fondos" se vuelven a crear cada vez que se dibuja
// el panel, por eso escuchamos los clics en el panel y vemos qué botón fue.
panel.addEventListener("click", (event) => {
    const favoriteButton = event.target.closest(".favorite-investment");
    if (favoriteButton) {
        toggleFavoriteInvestment(Number(favoriteButton.dataset.optionIndex));
        return;
    }
    const boton = event.target.closest(".subtab");
    if (boton === null) {
        return;
    }
    state.selectedSection = boton.dataset.section;
    renderBankPanel();
});

async function toggleFavoriteInvestment(optionIndex) {
    const option = state.options[optionIndex];
    if (!option) return;
    const key = investmentKey(option, state.capital, state.plazo);
    const saved = state.favoriteInvestments.some((favorite) => favorite.investment_key === key);
    try {
        if (saved) {
            await deleteFavoriteInvestment(key);
            state.favoriteInvestments = state.favoriteInvestments.filter(
                (favorite) => favorite.investment_key !== key
            );
        } else {
            const favorite = await saveFavoriteInvestment({
                investment_key: key,
                capital: state.capital,
                plazo: state.plazo,
                riesgo: state.risk,
                option,
            });
            state.favoriteInvestments = [
                favorite,
                ...state.favoriteInvestments.filter((item) => item.investment_key !== key),
            ];
        }
        document.dispatchEvent(new CustomEvent("favorite-investments-changed"));
        renderBankPanel();
    } catch (error) {
        window.alert(error.message);
    }
}

// Dibuja el panel de la entidad y la sección que están guardados en state.
export function renderBankPanel() {
    const entidad = state.selectedBank;
    const esBilletera = isWallet(entidad);

    // Opción de plazo fijo ya calculada por el backend para el plazo del usuario.
    let opcionPlazoFijo = null;
    for (const opcion of state.options) {
        if (opcion.banco === entidad && opcion.tipo === FIXED_DEPOSIT_TYPE) {
            opcionPlazoFijo = opcion;
        }
    }

    // Tasas que publica el banco para cada plazo (solo informativas).
    const tasasPublicadas = state.fixedTerms.filter((rango) => rango.banco === entidad);

    // Fondos de la entidad que cumplen con el riesgo elegido (los fondos nunca están garantizados).
    const fondos = state.options.filter((opcion) => opcion.banco === entidad && !opcion.garantizado);

    let contenido;
    if (esBilletera) {
        // Las billeteras no tienen plazo fijo: solo se muestran sus fondos.
        contenido = walletIntro() + fundsList(fondos);
    } else {
        const cantidadPlazoFijo = opcionPlazoFijo ? 1 : 0;
        contenido = sectionSwitcher(state.selectedSection, cantidadPlazoFijo, fondos.length);
        if (state.selectedSection === SECTIONS.FIXED_TERM) {
            contenido += fixedDepositSection(opcionPlazoFijo, tasasPublicadas);
        } else {
            contenido += fundsList(fondos);
        }
    }

    panel.innerHTML = entityHeader(entidad) + contenido;
}


// ----------------------------------------------------------------------------
// Partes del panel
// ----------------------------------------------------------------------------

function entityHeader(entidad) {
    const url = findUrl(entidad);
    let enlace = "";
    if (url) {
        enlace = `<a class="bank-link" href="${url}" target="_blank" rel="noopener">Ir al sitio oficial ${externalLinkIcon}</a>`;
    }

    return `
        <div class="bank-header">
            <div>
                <h4>${escapeHtml(entidad)}</h4>
                <p>Resultados calculados para el monto y plazo ingresados.</p>
            </div>
            ${enlace}
        </div>
    `;
}

// Busca en config.js el sitio oficial del banco o billetera (no todos lo tienen).
function findUrl(nombre) {
    for (const entidad of BANKS.concat(WALLETS)) {
        if (entidad.name === nombre) {
            return entidad.url;
        }
    }
    return undefined;
}

function isWallet(nombre) {
    for (const billetera of WALLETS) {
        if (billetera.name === nombre) {
            return true;
        }
    }
    return false;
}

function walletIntro() {
    return `
        <p class="panel-note">
            El dinero que dejás en la cuenta de esta billetera rinde a través de
            estos fondos comunes de inversión. El rendimiento no está garantizado.
        </p>
    `;
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

function fixedDepositSection(opcion, tasasPublicadas) {
    if (opcion === null) {
        return `<div class="empty-state">Este banco no tiene una tasa disponible en la fuente consultada.</div>`;
    }

    let html = `
        <h5 class="bank-panel-title">Plazo fijo para tus ${state.plazo} días</h5>
        <div class="option-grid">${fixedDepositCard(opcion, state.plazo, state.capital, state.options.indexOf(opcion))}</div>
    `;
    if (tasasPublicadas.length > 0) {
        html += publishedRatesList(tasasPublicadas);
    }
    return html;
}

function fundsList(fondos) {
    if (fondos.length === 0) {
        return `<div class="empty-state">No encontramos fondos de esta entidad para el riesgo elegido.</div>`;
    }

    let tarjetas = "";
    fondos.forEach((fondo) => {
        tarjetas += fundCard(fondo, state.plazo, state.options.indexOf(fondo));
    });

    return `
        <h5 class="bank-panel-title">Fondos administrados por esta entidad</h5>
        <div class="option-grid">${tarjetas}</div>
    `;
}
