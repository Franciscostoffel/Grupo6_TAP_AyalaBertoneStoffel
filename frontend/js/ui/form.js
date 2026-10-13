// ============================================================================
// FORMULARIO DE INVERSION
// Formateo del capital, montos sugeridos, validacion y estado del boton.
// ============================================================================

import { formatCapitalInput, parseCapital } from "../utils/format.js";

const form = document.getElementById("investment-form");
const capitalInput = document.getElementById("capital");
const submitButton = document.getElementById("analyze-button");
const submitLabel = submitButton.querySelector(".btn-label");
const errorMessage = document.getElementById("error-message");

/**
 * Conecta los eventos del formulario. Cuando los datos son validos llama a
 * onSubmit con { capital, plazo, riesgo }.
 */
export function initForm({ onSubmit }) {
    capitalInput.addEventListener("input", handleCapitalInput);

    document.querySelectorAll(".chip[data-amount]").forEach((chip) => {
        chip.addEventListener("click", () => {
            capitalInput.value = formatCapitalInput(chip.dataset.amount);
            clearFieldError(capitalInput);
        });
    });

    form.querySelectorAll("input[type=radio]").forEach((radio) => {
        radio.addEventListener("change", () => clearFieldError(radio));
    });

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const values = readValues();
        if (validate(values)) {
            hideFormError();
            onSubmit(values);
        }
    });
}

export function setFormLoading(isLoading) {
    submitButton.disabled = isLoading;
    submitButton.classList.toggle("is-loading", isLoading);
    submitLabel.textContent = isLoading ? "Analizando..." : "Analizar inversiones";
}

export function showFormError(message, field) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");

    if (field) {
        field.closest(".form-group")?.classList.add("invalid");
        field.focus();
    }

    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

export function hideFormError() {
    errorMessage.classList.add("hidden");
    form.querySelectorAll(".form-group.invalid")
        .forEach((group) => group.classList.remove("invalid"));
}


// ----------------------------------------------------------------------------
// Lectura y validacion
// ----------------------------------------------------------------------------

function readValues() {
    return {
        capital: parseCapital(capitalInput.value),
        plazo: Number(form.elements.plazo.value),
        riesgo: form.elements.riesgo.value
    };
}

function validate({ capital, plazo, riesgo }) {
    if (!capital || capital <= 0) {
        showFormError("Ingresá un capital válido.", capitalInput);
        return false;
    }

    if (!plazo || plazo <= 0) {
        showFormError("Seleccioná un plazo.", form.elements.plazo[0]);
        return false;
    }

    if (!riesgo) {
        showFormError("Seleccioná un nivel de riesgo.", form.elements.riesgo[0]);
        return false;
    }

    return true;
}

function clearFieldError(field) {
    if (field.closest(".form-group")?.classList.contains("invalid")) {
        hideFormError();
    }
}


// ----------------------------------------------------------------------------
// Capital con separadores de miles
// ----------------------------------------------------------------------------

// Reformatea mientras se escribe sin que el cursor salte al final.
function handleCapitalInput() {
    const caret = capitalInput.selectionStart ?? capitalInput.value.length;
    const significantBeforeCaret = capitalInput.value
        .slice(0, caret)
        .replace(/[^\d,]/g, "").length;

    capitalInput.value = formatCapitalInput(capitalInput.value);

    let position = 0;
    let seen = 0;
    while (position < capitalInput.value.length && seen < significantBeforeCaret) {
        if (/[\d,]/.test(capitalInput.value[position])) seen++;
        position++;
    }
    capitalInput.setSelectionRange(position, position);
    clearFieldError(capitalInput);
}
