// ============================================================================
// TOOLTIP DE LA RECOMENDACION DE IA
// En escritorio se abre con hover (CSS); en pantallas tactiles, con un toque.
// ============================================================================

export function initInfoTooltip() {
    const button = document.querySelector(".info-button");
    const tooltip = document.getElementById("ai-info-text");

    button.addEventListener("click", (event) => {
        event.stopPropagation();
        tooltip.classList.toggle("open");
    });

    document.addEventListener("click", () => tooltip.classList.remove("open"));
}
