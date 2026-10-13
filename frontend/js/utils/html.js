// ============================================================================
// SEGURIDAD DEL HTML GENERADO
// ============================================================================

// Todo dato que venga del backend pasa por aca antes de insertarse con innerHTML.
export function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
