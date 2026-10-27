// Orden de presentacion: reutiliza las ganancias calculadas por la simulacion.
import { FIXED_DEPOSIT_TYPE, SECTIONS } from "../config.js";

// La misma seleccion alimenta las tarjetas y la clave numerica de las pestanas.
export function sectionOptions(options, section) {
    return options.filter((option) => section === SECTIONS.FIXED_TERM
        ? option.tipo === FIXED_DEPOSIT_TYPE
        : !option.garantizado
    );
}

function compareReturns(first, second) {
    const firstValid = Number.isFinite(first);
    const secondValid = Number.isFinite(second);
    if (firstValid !== secondValid) return firstValid ? -1 : 1;
    if (!firstValid || first === second) return 0;
    return first > second ? -1 : 1;
}

export function orderOptions(options) {
    return options.slice().sort((first, second) =>
        compareReturns(first.rendimiento, second.rendimiento)
    );
}

export function orderEntities(entities, options, primaryBank = null, favoriteBanks = []) {
    const bestReturns = new Map();
    for (const option of options) {
        if (!Number.isFinite(option.rendimiento)) continue;
        if (!bestReturns.has(option.banco) || option.rendimiento > bestReturns.get(option.banco)) {
            bestReturns.set(option.banco, option.rendimiento);
        }
    }

    const favorites = new Set(favoriteBanks);
    const priority = (entity) => entity.name === primaryBank ? 0 : favorites.has(entity.name) ? 1 : 2;
    // El sort estable conserva el orden del catalogo cuando hay empate.
    return entities.slice().sort((first, second) =>
        priority(first) - priority(second)
        || compareReturns(bestReturns.get(first.name), bestReturns.get(second.name))
    );
}
