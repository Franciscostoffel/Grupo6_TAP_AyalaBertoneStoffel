const form = document.getElementById("investment-form");

const button = document.getElementById("analyze-button");

const loading = document.getElementById("loading");

const results = document.getElementById("results");

const errorMessage = document.getElementById("error-message");

const resultCapital = document.getElementById("result-capital");

const resultPlazo = document.getElementById("result-plazo");

const resultRisk = document.getElementById("result-risk");


form.addEventListener("submit", async (event) => {

    event.preventDefault();


    // Obtener datos del formulario

    const capital = Number(
        document.getElementById("capital").value
    );

    const plazo = Number(
        document.getElementById("plazo").value
    );

    const riesgo = document.getElementById("riesgo").value;


    // Validación básica

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


    // Preparar interfaz

    hideError();

    results.classList.add("hidden");

    loading.classList.remove("hidden");

    button.disabled = true;


    try {

        // Request al backend

        const response = await fetch("/api/analyze", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                capital: capital,
                plazo: plazo,
                riesgo: riesgo
            })

        });


        if (!response.ok) {
            throw new Error(
                "Ocurrió un error al analizar la inversión."
            );
        }


        const data = await response.json();


        // Mostrar respuesta

        resultCapital.textContent =
            formatNumber(data.capital);

        resultPlazo.textContent =
            data.plazo;

        resultRisk.textContent =
            capitalize(data.riesgo);


        results.classList.remove("hidden");


    } catch (error) {

        showError(error.message);

    } finally {

        loading.classList.add("hidden");

        button.disabled = false;

    }

});


function formatNumber(number) {

    return new Intl.NumberFormat("es-AR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number);

}


function capitalize(text) {

    return text.charAt(0).toUpperCase() + text.slice(1);

}


function showError(message) {

    errorMessage.textContent = message;

    errorMessage.classList.remove("hidden");

}


function hideError() {

    errorMessage.classList.add("hidden");

}