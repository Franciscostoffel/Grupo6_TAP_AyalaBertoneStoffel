// ============================================================================
// REFERENCIAS A LA INTERFAZ Y ESTADO DE LA PANTALLA
// ============================================================================

const form = document.getElementById("investment-form");
const button = document.getElementById("analyze-button");
const loading = document.getElementById("loading");
const results = document.getElementById("results");
const errorMessage = document.getElementById("error-message");

const resultCapital = document.getElementById("result-capital");
const resultPlazo = document.getElementById("result-plazo");
const resultRisk = document.getElementById("result-risk");

const investmentPlaceholder = document.querySelector(".investment-placeholder");
const aiPlaceholder = document.querySelector(".ai-placeholder");
const investmentTabs = document.querySelectorAll(".investment-tab");
let currentOptions = [];
let currentPlazo = 0;
let currentCapital = 0;
let currentFixedTerms = [];
let currentSection = "plazo_fijo";

// ============================================================================
// CATALOGOS DE PRESENTACION
// ============================================================================

// Solo contiene enlaces oficiales. Las tasas y los fondos vienen del backend.
const bankProducts = {
    "Banco Nación": { url: "https://www.bna.com.ar/Personas/Inversiones" },
    "Banco Galicia": { url: "https://www.galicia.ar/personas/inversiones" },
    "Banco Santander": { url: "https://www.santander.com.ar/personas/inversiones" },
    "BBVA": { url: "https://www.bbva.com.ar/personas/productos/inversiones.html" },
    "ICBC": { url: "https://icbc.com.ar/personas/productos-servicios/inversiones" }
};

// ============================================================================
// NAVEGACION ENTRE BANCOS
// ============================================================================

investmentTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        investmentTabs.forEach((item) => item.classList.remove("active"));
        tab.classList.add("active");
        renderBankOptions(tab.dataset.bank, currentSection);
    });
});

// ============================================================================
// ENVIO DEL FORMULARIO Y CONSULTA DE RECOMENDACIONES
// ============================================================================

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const capital = Number(document.getElementById("capital").value);
    const plazo = Number(document.getElementById("plazo").value);
    const riesgo = document.getElementById("riesgo").value;

    if (!capital || capital <= 0) {
        showError("Ingresá un capital válido.");
        return;
    }

    if (!plazo || plazo <= 0) {
        showError("Seleccioná un plazo.");
        return;
    }

    if (!riesgo) {
        showError("Seleccioná un nivel de riesgo.");
        return;
    }

    hideError();
    results.classList.add("hidden");
    loading.classList.remove("hidden");
    button.disabled = true;

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ capital, plazo, riesgo })
        });

        if (!response.ok) {
            throw new Error("Ocurrió un error al analizar la inversión.");
        }

        const data = await response.json();

        // 1. Mostrar resumen
        resultCapital.textContent = formatNumber(data.capital);
        resultPlazo.textContent = data.plazo;
        resultRisk.textContent = capitalize(data.riesgo);

                currentOptions = data.opciones;
                currentPlazo = data.plazo;
                currentCapital = data.capital;
                currentFixedTerms = data.plazos_fijos;
                renderBankOptions("Banco Nación", "plazo_fijo");

        // 3. Mostrar la recomendación
        aiPlaceholder.innerHTML = `
            <p style="padding: 12px; background: #f0f4f8; border-left: 4px solid #1a73e8; margin: 0; line-height: 1.5;">
                ${escapeHtml(data.recomendacion)}
            </p>
        `;

        results.classList.remove("hidden");

    } catch (error) {
        showError(error.message);
    } finally {
        loading.classList.add("hidden");
        button.disabled = false;
    }
});

// ============================================================================
// RENDERIZADO DE OPCIONES DE INVERSION
// ============================================================================

function renderBankOptions(bank, section = "plazo_fijo") {
      const catalog = bankProducts[bank];
      const plazos = currentFixedTerms.filter((item) => item.banco === bank);
      const fondos = currentOptions
          .filter((op) => op.banco === bank && !op.garantizado);
      currentSection = section;
      let tableHtml = `
            <div class="subtabs">
                <button class="subtab ${section === "plazo_fijo" ? "active" : ""}" data-section="plazo_fijo">Plazo fijo</button>
                <button class="subtab ${section === "fondos" ? "active" : ""}" data-section="fondos">Fondos de inversión</button>
            </div>
        `;
      tableHtml += catalog
          ? `<div class="bank-catalog">
                <div class="bank-catalog-header">
                    <div>
                        <h4>${escapeHtml(bank)}</h4>
                        <p>Resultados calculados para el monto y plazo ingresados.</p>
                    </div>
                    <a href="${catalog.url}" target="_blank" rel="noopener">Ir al sitio del banco</a>
                </div></div>`
          : "";

      if (section === "plazo_fijo") {
          tableHtml += plazos.length
          ? `<h4 class="live-data-title">Plazos fijos disponibles</h4>
             <div class="term-cards">`
          : `<div class="empty-category">Este banco no tiene una tasa disponible en la fuente consultada.</div>`;

      plazos.forEach((term, index) => {
          const dias = term.plazo_min === term.plazo_max
              ? `${term.plazo_min} días`
              : `Entre ${term.plazo_min} y ${term.plazo_max} días`;
          const termDays = term.plazo_min;
          const ganancia = currentCapital * (term.tna / 100) * (termDays / 365);
          const total = currentCapital + ganancia;

          tableHtml += `
              <article class="term-card ${index === 0 ? "recommended" : ""}">
                  <h4>Plazo fijo de ${dias}</h4>
                  <p class="investment-type">Tasa informada por ${escapeHtml(bank)}</p>
                  <div class="investment-main-value">
                      <span>Para $${formatNumber(currentCapital)}</span>
                      <strong>+$${formatNumber(ganancia)}</strong>
                  </div>
                  <p class="investment-total">
                      Recibirías aproximadamente <strong>$${formatNumber(total)}</strong>
                  </p>
                  <ul class="investment-details">
                      <li><strong>Rendimiento anual informado:</strong> ${term.tna}%</li>
                      <li><strong>Disponibilidad:</strong> al finalizar ${termDays} días</li>
                  </ul>
              </article>
          `;
      });

      tableHtml += plazos.length ? `</div>` : "";
      } else {
      if (fondos.length) {
          tableHtml += `
              <h4 class="live-data-title">Fondos relacionados con este banco</h4>
              <div class="investment-cards">
          `;
          fondos.forEach((fund) => {
              tableHtml += `
                  <article class="investment-card">
                      <h4>Fondo de inversión</h4>
                      <p class="investment-type">${escapeHtml(fund.tipo)}</p>
                      <p>${escapeHtml(fund.nombre)}</p>
                      <div class="investment-main-value">
                          <span>Rendimiento estimado para ${currentPlazo} días</span>
                          <strong>${formatNumber(fund.rendimiento_periodo_pct)}%</strong>
                      </div>
                      <p class="investment-total">
                          Ganancia estimada para ${currentPlazo} días:
                          <strong>$${formatNumber(fund.rendimiento)}</strong>
                      </p>
                      <ul class="investment-details">
                          <li><strong>Perfil de riesgo:</strong> ${capitalize(fund.perfil_riesgo)}</li>
                          <li><strong>TNA estimada:</strong> ${fund.tna !== null
                              ? `${formatNumber(fund.tna)}%`
                              : "No disponible"}</li>
                          <li><strong>Rendimiento último día:</strong> ${fund.rendimiento_ultimo_dia_pct !== null
                              ? `${formatNumber(fund.rendimiento_ultimo_dia_pct)}%`
                              : "No informado"}</li>
                          <li><strong>Liquidez:</strong> ${escapeHtml(fund.liquidez)}</li>
                          <li><strong>Acceso por app:</strong> ${escapeHtml(fund.acceso_app || "Confirmá la disponibilidad en la app del banco.")}</li>
                      </ul>
                      <small>No está garantizado y puede variar. Fuente: ${escapeHtml(fund.fuente)}.</small>
                  </article>
              `;
          });
          tableHtml += `</div>`;
      } else {
          tableHtml += `<div class="empty-category">No encontramos fondos asociados a este banco en la fuente consultada.</div>`;
      }
      }
      investmentPlaceholder.innerHTML = tableHtml;
      investmentPlaceholder.querySelectorAll(".subtab").forEach((tab) => {
          tab.addEventListener("click", () => renderBankOptions(bank, tab.dataset.section));
      });
}

// ============================================================================
// FORMATEO Y SEGURIDAD DE DATOS MOSTRADOS
// ============================================================================

function formatNumber(number) {
    return new Intl.NumberFormat("es-AR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number);
}

function capitalize(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// ============================================================================
// ESTADO DE ERRORES DE LA INTERFAZ
// ============================================================================

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function hideError() {
    errorMessage.classList.add("hidden");
}