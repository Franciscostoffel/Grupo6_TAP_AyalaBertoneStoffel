// ============================================================================
// FORMATEO DE NUMEROS Y TEXTO
// ============================================================================

// Muestra un número con formato argentino: 1234567.5 -> "1.234.567,50"
export function formatNumber(numero) {
    return numero.toLocaleString("es-AR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// "moderado" -> "Moderado"
export function capitalize(texto) {
    return texto.charAt(0).toUpperCase() + texto.slice(1);
}

// Formatea lo que se escribe en el campo de capital: "1500000" -> "1.500.000"
export function formatCapitalInput(texto) {
    // Nos quedamos solo con los dígitos (se borran puntos, letras, espacios, etc.).
    const soloDigitos = String(texto).replace(/[^0-9]/g, "");
    if (soloDigitos === "") {
        return "";
    }
    return Number(soloDigitos).toLocaleString("es-AR");
}

// Convierte el texto del campo en número: "1.500.000" -> 1500000
export function parseCapital(texto) {
    return Number(texto.replaceAll(".", ""));
}
