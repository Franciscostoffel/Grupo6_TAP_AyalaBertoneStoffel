// ============================================================================
// FORMATEO DE NUMEROS Y TEXTO
// ============================================================================

const numberFormatter = new Intl.NumberFormat("es-AR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
});

export function formatNumber(number) {
    return numberFormatter.format(number);
}

export function capitalize(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}

// Agrega separadores de miles (formato es-AR) y limita los decimales a dos.
export function formatCapitalInput(value) {
    const clean = String(value).replace(/[^\d,]/g, "");
    const [integerPart, ...decimalParts] = clean.split(",");
    const integer = integerPart.replace(/^0+(?=\d)/, "");
    const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

    return decimalParts.length
        ? `${grouped || "0"},${decimalParts.join("").slice(0, 2)}`
        : grouped;
}

// Convierte "1.234.567,89" en 1234567.89.
export function parseCapital(value) {
    return Number(value.replaceAll(".", "").replace(",", "."));
}
