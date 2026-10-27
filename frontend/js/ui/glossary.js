// ============================================================================
// GLOSARIO DE TERMINOS
// Palabras técnicas que muestran una explicación sencilla al pasar el mouse
// (o al tocarlas en el celular). Hay un solo cartel para toda la página y se
// ubica con position: fixed para que no lo corten las tablas con scroll.
// ============================================================================

import { escapeHtml } from "../utils/html.js";

const DEFINITIONS = {
    tna: "Tasa Nominal Anual. Es el porcentaje que te pagan por tu plata en un año, " +
        "sin contar que los intereses se reinvierten. Ejemplo: con una TNA de 36%, " +
        "por $100.000 ganarías unos $3.000 por mes. Sirve para comparar opciones entre sí.",
    tea: "Tasa Efectiva Anual. Es lo que realmente ganarías en un año si cada vez que " +
        "cobrás los intereses los volvés a invertir (interés sobre interés). " +
        "Por eso siempre es un poco más alta que la TNA.",
    rescate: "Rescatar es sacar tu plata del fondo. Este número indica cuántos días tarda " +
        "en llegarte a tu cuenta desde que pedís retirarla. Por ejemplo, 0 días " +
        "significa que la tenés en el mismo día.",
    vencimiento: "Cuánto ganás en total, en porcentaje, si comprás el bono hoy y lo " +
        "guardás hasta la fecha en que vence (el día en que te devuelven la plata). " +
        "No es anual: es la ganancia de todo ese período.",
};

// Devuelve el HTML de un término con su explicación. El texto visible se escapa.
export function term(clave, texto) {
    return `<span class="term" tabindex="0" data-term="${clave}">${escapeHtml(texto)}</span>`;
}

// Recibe un texto del backend (sin escapar) y marca "Rescate informado" si aparece.
export function withTerms(texto) {
    const seguro = escapeHtml(texto);
    return seguro.replace("Rescate informado", term("rescate", "Rescate informado"));
}

export function initGlossary() {
    const cartel = document.createElement("div");
    cartel.className = "term-tooltip";
    cartel.id = "term-tooltip";
    cartel.setAttribute("role", "tooltip");
    document.body.append(cartel);

    let actual = null;

    function show(elemento) {
        actual = elemento;
        cartel.textContent = DEFINITIONS[elemento.dataset.term];
        elemento.setAttribute("aria-describedby", cartel.id);
        cartel.classList.add("open");
        place(elemento);
    }

    function hide() {
        if (actual !== null) {
            actual.removeAttribute("aria-describedby");
        }
        actual = null;
        cartel.classList.remove("open");
    }

    // Debajo del término; si no entra, arriba. Nunca se sale por los costados.
    function place(elemento) {
        const caja = elemento.getBoundingClientRect();
        const margen = 12;
        const izquierda = Math.min(
            Math.max(margen, caja.left),
            window.innerWidth - cartel.offsetWidth - margen
        );
        let arriba = caja.bottom + 8;
        if (arriba + cartel.offsetHeight > window.innerHeight - margen) {
            arriba = caja.top - cartel.offsetHeight - 8;
        }
        cartel.style.left = `${izquierda}px`;
        cartel.style.top = `${arriba}px`;
    }

    document.addEventListener("mouseover", (event) => {
        const elemento = event.target.closest(".term");
        if (elemento !== null && elemento !== actual) {
            show(elemento);
        }
    });
    document.addEventListener("mouseout", (event) => {
        const elemento = event.target.closest(".term");
        if (elemento !== null && !elemento.contains(event.relatedTarget)) {
            hide();
        }
    });
    document.addEventListener("focusin", (event) => {
        const elemento = event.target.closest(".term");
        if (elemento !== null) {
            show(elemento);
        }
    });
    document.addEventListener("focusout", hide);

    // En pantallas táctiles: un toque abre, otro toque (o tocar afuera) cierra.
    document.addEventListener("click", (event) => {
        const elemento = event.target.closest(".term");
        if (elemento === null) {
            hide();
        } else if (elemento !== actual) {
            show(elemento);
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            hide();
        }
    });
    window.addEventListener("scroll", hide, true);
}
