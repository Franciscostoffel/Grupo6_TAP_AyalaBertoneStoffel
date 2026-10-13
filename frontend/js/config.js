// ============================================================================
// CONFIGURACION Y CATALOGOS DE PRESENTACION
// ============================================================================

export const ANALYZE_ENDPOINT = "/api/analyze";

// Debe coincidir con la clave que lee el script en linea de index.html.
export const THEME_STORAGE_KEY = "theme";

// Bancos en el orden en que se muestran las pestañas. "name" coincide con el
// nombre que devuelve el backend; "url" solo existe para enlaces oficiales.
// Las tasas y los fondos siempre vienen del backend.
export const BANKS = [
    { name: "Banco Nación", label: "Nación", url: "https://www.bna.com.ar/Personas/Inversiones" },
    { name: "Banco Galicia", label: "Galicia", url: "https://www.galicia.ar/personas/inversiones" },
    { name: "Banco Santander", label: "Santander", url: "https://www.santander.com.ar/personas/inversiones" },
    { name: "BBVA", label: "BBVA", url: "https://www.bbva.com.ar/personas/productos/inversiones.html" },
    { name: "ICBC", label: "ICBC", url: "https://icbc.com.ar/personas/productos-servicios/inversiones" },
    { name: "Banco Provincia", label: "Provincia" },
    { name: "Banco Macro", label: "Macro" },
    { name: "Banco Credicoop", label: "Credicoop" },
    { name: "Banco Ciudad", label: "Ciudad" },
    { name: "Banco Patagonia", label: "Patagonia" },
    { name: "Banco Supervielle", label: "Supervielle" },
    { name: "Banco Hipotecario", label: "Hipotecario" },
    { name: "Banco Comafi", label: "Comafi" },
    { name: "Banco Bica", label: "Bica" },
    { name: "Banco CMF", label: "CMF" }
];

export const RISK_LEVELS = ["bajo", "moderado", "alto"];

// Secciones disponibles dentro de cada banco.
export const SECTIONS = {
    FIXED_TERM: "plazo_fijo",
    FUNDS: "fondos"
};
