// ============================================================================
// FORMULARIO DE INVERSION
// Formato del capital, montos sugeridos, validación y estado del botón.
// ============================================================================

import { formatCapitalInput, parseCapital } from "../utils/format.js";

const form = document.getElementById("investment-form");
const capitalInput = document.getElementById("capital");
const submitButton = document.getElementById("analyze-button");
const submitLabel = submitButton.querySelector(".btn-label");
const errorMessage = document.getElementById("error-message");

// Conecta los eventos del formulario. Cuando los datos son válidos llama a
// la función alEnviar con { capital, plazo, riesgo }.
export function initForm(alEnviar) {
    // Mientras se escribe, se agregan los puntos de miles.
    capitalInput.addEventListener("input", () => {
        capitalInput.value = formatCapitalInput(capitalInput.value);
        clearFieldError(capitalInput);
    });

    // Botones de montos sugeridos ($100 mil, $500 mil, ...).
    const chips = document.querySelectorAll(".chip[data-amount]");
    chips.forEach((chip) => {
        chip.addEventListener("click", () => {
            capitalInput.value = formatCapitalInput(chip.dataset.amount);
            clearFieldError(capitalInput);
        });
    });

    // Al elegir un plazo o un riesgo se borra el error de ese campo.
    const radios = form.querySelectorAll("input[type=radio]");
    radios.forEach((radio) => {
        radio.addEventListener("change", () => clearFieldError(radio));
    });

    form.addEventListener("submit", (event) => {
        event.preventDefault(); // evita que el navegador recargue la página
        const datos = readValues();
        if (validate(datos)) {
            hideFormError();
            alEnviar(datos);
        }
    });
}

// Muestra u oculta el "cargando" del botón mientras se espera al servidor.
export function setFormLoading(cargando) {
    submitButton.disabled = cargando;
    if (cargando) {
        submitButton.classList.add("is-loading");
        submitLabel.textContent = "Analizando...";
    } else {
        submitButton.classList.remove("is-loading");
        submitLabel.textContent = "Analizar inversiones";
    }
}

// Muestra un mensaje de error. Si se indica un campo, lo marca en rojo.
export function showFormError(mensaje, campo) {
    errorMessage.textContent = mensaje;
    errorMessage.classList.remove("hidden");

    if (campo) {
        campo.closest(".form-group").classList.add("invalid");
        campo.focus();
    }

    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

export function hideFormError() {
    errorMessage.classList.add("hidden");
    const gruposConError = form.querySelectorAll(".form-group.invalid");
    gruposConError.forEach((grupo) => grupo.classList.remove("invalid"));
}


// ----------------------------------------------------------------------------
// Lectura y validación
// ----------------------------------------------------------------------------

function readValues() {
    return {
        capital: parseCapital(capitalInput.value),
        plazo: Number(form.elements.plazo.value),
        riesgo: form.elements.riesgo.value
    };
}

function validate(datos) {
    if (!datos.capital || datos.capital <= 0) {
        showFormError("Ingresá un capital válido.", capitalInput);
        return false;
    }

    if (!datos.plazo || datos.plazo <= 0) {
        showFormError("Seleccioná un plazo.", form.elements.plazo[0]);
        return false;
    }

    if (!datos.riesgo) {
        showFormError("Seleccioná un nivel de riesgo.", form.elements.riesgo[0]);
        return false;
    }

    return true;
}

function clearFieldError(campo) {
    const grupo = campo.closest(".form-group");
    if (grupo.classList.contains("invalid")) {
        hideFormError();
    }
}
