// ============================================================================
// TEMA CLARO / OSCURO
// El tema guardado se aplica antes de pintar desde un script en index.html;
// aca solo se maneja el boton para cambiarlo.
// ============================================================================

import { THEME_STORAGE_KEY } from "../config.js";

export function initThemeToggle() {
    const toggle = document.getElementById("theme-toggle");
    const root = document.documentElement;

    toggle.addEventListener("click", () => {
        const isDark = root.dataset.theme
            ? root.dataset.theme === "dark"
            : window.matchMedia("(prefers-color-scheme: dark)").matches;
        const nextTheme = isDark ? "light" : "dark";

        root.dataset.theme = nextTheme;
        try {
            localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
        } catch {
            // Sin almacenamiento: el tema se mantiene solo en esta visita.
        }
    });
}
