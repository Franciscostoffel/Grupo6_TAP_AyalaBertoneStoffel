// Ejecutar con Node.js 24: node --test frontend/tests/investment-order.test.mjs
import assert from "node:assert/strict";
import { test } from "node:test";
import { orderEntities, orderOptions, sectionOptions } from "../js/utils/investment-order.js";
import { FIXED_DEPOSIT_TYPE, SECTIONS } from "../js/config.js";

const entities = (...names) => names.map((name) => ({ name }));
const names = (items) => items.map((item) => item.name);
const option = (banco, rendimiento, extra = {}) => ({ banco, rendimiento, ...extra });

test("regresion: plazos fijos de favoritos y otros ordenados por la ganancia visible", () => {
    const banks = entities("Propio", "F1", "F2", "F3", "F4", "N1", "N2", "N3", "N4", "N5");
    const gains = [1000, 22000, 20000, 22000, 24000, 29000, null, 25000, 19000, 27000];
    const options = banks.map((bank, index) => option(bank.name, gains[index],
        { tipo: FIXED_DEPOSIT_TYPE, garantizado: true }));
    // Fondos que antes alteraban el orden de los plazos fijos, incluido uno sin plazo fijo.
    options.push(option("F2", 90000, { tipo: "FCI", garantizado: false }),
        option("N2", 100000, { tipo: "FCI", garantizado: false }));
    const visible = sectionOptions(options, SECTIONS.FIXED_TERM);
    const ordered = orderEntities(banks, visible, "Propio", ["Propio", "F1", "F2", "F3", "F4"]);
    assert.deepEqual(names(ordered), ["Propio", "F4", "F1", "F3", "F2", "N1", "N5", "N3", "N4", "N2"]);
});

test("al pasar a fondos usa el mejor fondo y descarta los plazos fijos", () => {
    const banks = entities("A", "B", "C");
    const options = [option("A", 29000, { tipo: FIXED_DEPOSIT_TYPE, garantizado: true }),
        option("B", 19000, { tipo: FIXED_DEPOSIT_TYPE, garantizado: true }),
        option("A", 1000, { tipo: "FCI", garantizado: false }),
        option("B", 2000, { tipo: "FCI", garantizado: false }),
        option("B", 24000, { tipo: "FCI", garantizado: false }),
        option("C", 90000, { tipo: FIXED_DEPOSIT_TYPE, garantizado: true })];
    assert.deepEqual(names(orderEntities(banks, sectionOptions(options, SECTIONS.FIXED_TERM))), ["C", "A", "B"]);
    assert.deepEqual(names(orderEntities(banks, sectionOptions(options, SECTIONS.FUNDS))), ["B", "A", "C"]);
});

test("no interpreta textos formateados como ganancias numericas", () => {
    const options = [option("A", "$24.000,00"), option("B", 22000), option("C", 100000)];
    assert.deepEqual(names(orderEntities(entities("A", "B", "C"), options)), ["C", "B", "A"]);
});

test("Mi banco, favoritos y otros respetan la prioridad del ejemplo sin duplicados", () => {
    const banks = entities("BBVA", "Macro", "Santander", "Galicia", "ICBC", "Nacion");
    const options = [option("Galicia", 60000), option("Nacion", 75000),
        option("Santander", 55000), option("BBVA", 90000),
        option("ICBC", 70000), option("Macro", 40000)];
    const ordered = orderEntities(banks, options, "Galicia", ["Santander", "Galicia", "Nacion"]);
    assert.deepEqual(names(ordered), ["Galicia", "Nacion", "Santander", "BBVA", "ICBC", "Macro"]);
    assert.equal(new Set(names(ordered)).size, banks.length);
});

test("sin banco propio o favoritos se omiten esos grupos", () => {
    const banks = entities("A", "B", "C");
    const options = [option("A", 10), option("B", 30), option("C", 20)];
    assert.deepEqual(names(orderEntities(banks, options)), ["B", "C", "A"]);
    assert.deepEqual(names(orderEntities(banks, options, null, ["A"])), ["A", "B", "C"]);
    assert.deepEqual(names(orderEntities(banks, options, "C")), ["C", "B", "A"]);
});

test("el comparador usa el maximo de las opciones recibidas y no conserva retornos anteriores", () => {
    const banks = entities("A", "B");
    const options = [option("A", 5, { tipo: "Plazo Fijo" }),
        option("A", 40, { tipo: "FCI" }), option("B", 30)];
    assert.deepEqual(names(orderEntities(banks, options)), ["A", "B"]);
    assert.deepEqual(names(orderEntities(banks, [option("A", 5), option("B", 30)])), ["B", "A"]);
});

test("cada seccion respeta cero, perdidas y ausencia total de opciones dentro de cada grupo", () => {
    const banks = entities("Propio", "F sin datos", "F perdida", "F cero", "N sin datos", "N perdida", "N cero");
    for (const section of [SECTIONS.FIXED_TERM, SECTIONS.FUNDS]) {
        const details = section === SECTIONS.FIXED_TERM
            ? { tipo: FIXED_DEPOSIT_TYPE, garantizado: true }
            : { tipo: "FCI", garantizado: false };
        const options = [option("F perdida", -500, details), option("F cero", 0, details),
            option("N perdida", -100, details), option("N cero", 0, details)];
        const favorites = ["F sin datos", "F perdida", "F cero", "Propio"];
        assert.deepEqual(names(orderEntities(banks, sectionOptions(options, section), "Propio", favorites)),
            ["Propio", "F cero", "F perdida", "F sin datos", "N cero", "N perdida", "N sin datos"]);
        assert.deepEqual(names(orderEntities(banks, [], "Propio", favorites)), names(banks));
    }
});

test("sin retorno valido queda al final de su grupo incluso frente a perdidas", () => {
    const banks = entities("Sin datos", "Invalido", "Negativo", "Cero", "Propio", "Favorito");
    const options = [option("Invalido", null), option("Invalido", NaN),
        option("Invalido", Infinity), option("Negativo", -20), option("Cero", 0)];
    assert.deepEqual(names(orderEntities(banks, options, "Propio", ["Favorito", "Negativo"])),
        ["Propio", "Negativo", "Favorito", "Cero", "Sin datos", "Invalido"]);
});

test("empates y ausencia de simulacion conservan el orden del catalogo dentro de cada grupo", () => {
    const banks = entities("B", "A", "C");
    assert.deepEqual(names(orderEntities(banks, [option("A", 20), option("B", 20)])), ["B", "A", "C"]);
    assert.deepEqual(names(orderEntities(banks, [], null, ["C", "A"])), ["A", "C", "B"]);
});

test("billeteras ordenadas dentro de su propio catalogo", () => {
    const options = [option("Banco", 100), option("Wallet A", 5), option("Wallet B", 20)];
    assert.deepEqual(names(orderEntities(entities("Wallet A", "Wallet B"), options)), ["Wallet B", "Wallet A"]);
});

test("ordena opciones sin mutar datos ni perder referencias para favoritos", () => {
    const low = Object.freeze(option("A", -5));
    const high = Object.freeze(option("A", 20));
    const tie = Object.freeze(option("A", 20));
    const invalid = Object.freeze(option("A", null));
    const options = Object.freeze([low, high, tie, invalid]);
    const banks = Object.freeze(entities("A", "B"));
    assert.deepEqual(orderOptions(options), [high, tie, low, invalid]);
    assert.equal(orderOptions(options)[0], options[1]);
    orderEntities(banks, options);
    assert.deepEqual(options, [low, high, tie, invalid]);
    assert.deepEqual(names(banks), ["A", "B"]);
});

test("panel ordena tarjetas y el boton de favorito guarda la opcion correcta", async () => {
    const listeners = new Map();
    const panel = { innerHTML: "", addEventListener: (event, callback) => listeners.set(event, callback) };
    const requests = [];
    const originalDocument = globalThis.document;
    const originalFetch = globalThis.fetch;
    const originalCustomEvent = globalThis.CustomEvent;
    globalThis.document = { getElementById: () => panel, dispatchEvent() {} };
    globalThis.CustomEvent = class { constructor(type) { this.type = type; } };
    globalThis.fetch = async (url, init) => {
        const body = JSON.parse(init.body);
        requests.push({ url, body });
        return { ok: true, status: 200, json: async () => ({ investment_key: body.investment_key }) };
    };
    const { state, clearSessionState } = await import("../js/state.js");
    try {
        const { renderBankPanel } = await import("../js/ui/bank-panel.js");
        const common = { tipo: "FCI", garantizado: false, perfil_riesgo: "bajo",
            liquidez: "Inmediata", fuente: "Test", tna: 20, rendimiento_periodo_pct: 1,
            rendimiento_ultimo_dia_pct: null };
        state.capital = 1000;
        state.plazo = 30;
        state.risk = "bajo";
        state.selectedBank = "BBVA";
        state.selectedSection = "fondos";
        state.options = [option("BBVA", 10, { ...common, nombre: "Menor" }),
            option("BBVA", 50, { ...common, nombre: "Mayor" })];
        renderBankPanel();
        assert.ok(panel.innerHTML.indexOf("Mayor") < panel.innerHTML.indexOf("Menor"));
        assert.deepEqual([...panel.innerHTML.matchAll(/data-option-index="(\d+)"/g)].map((m) => Number(m[1])), [1, 0]);
        listeners.get("click")({ target: { closest: () => ({ dataset: { optionIndex: "1" } }) } });
        await new Promise((resolve) => setImmediate(resolve));
        assert.equal(requests.length, 1);
        assert.equal(requests[0].body.option.nombre, "Mayor");
        assert.equal(state.favoriteInvestments[0].investment_key, "BBVA|Mayor|FCI|1000|30");
        assert.equal(state.options[0].nombre, "Menor");
    } finally {
        clearSessionState();
        globalThis.document = originalDocument;
        globalThis.fetch = originalFetch;
        globalThis.CustomEvent = originalCustomEvent;
    }
});
