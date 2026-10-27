// Ejecutar con Node.js 24: node --test frontend/tests/*.test.mjs
import assert from "node:assert/strict";
import { test } from "node:test";
import { BANKS, WALLETS, SECTIONS, FIXED_DEPOSIT_TYPE } from "../js/config.js";
import { state, clearSessionState, setAnalysis } from "../js/state.js";
import { formatNumber } from "../js/utils/format.js";

test("ordenamiento y controles de bancos e inversiones", async (t) => {
    const makeElement = () => ({
        innerHTML: "", listeners: new Map(), attributes: {}, dataset: {},
        classList: {
            values: new Set(),
            toggle(name, force) {
                if (force) this.values.add(name);
                else this.values.delete(name);
            },
            contains(name) { return this.values.has(name); }
        },
        addEventListener(type, callback) { this.listeners.set(type, callback); },
        setAttribute(name, value) { this.attributes[name] = value; },
        insertAdjacentHTML() {}, scrollIntoView() {},
        querySelectorAll() { return []; }
    });
    const elements = new Map(["bank-panel", "bank-tabs", "primary-bank", "favorites-filter", "wallets-label"]
        .map((id) => [id, makeElement()]));
    const tabList = elements.get("bank-tabs");
    let tabs = [];
    let stars = [];
    let wrappers = [];
    Object.defineProperty(tabList, "innerHTML", {
        get() { return this.html || ""; },
        set(html) {
            this.html = html;
            tabs = [...html.matchAll(/data-bank="([^"]+)"/g)].map((match) =>
                Object.assign(makeElement(), { dataset: { bank: match[1] } }));
            stars = [...html.matchAll(/data-favorite-bank="([^"]+)"/g)].map((match) =>
                Object.assign(makeElement(), { dataset: { favoriteBank: match[1] } }));
            wrappers = [...html.matchAll(/data-bank-wrap="([^"]+)"/g)].map((match) =>
                Object.assign(makeElement(), { dataset: { bankWrap: match[1] } }));
        }
    });
    tabList.querySelectorAll = (selector) => selector === ".bank-tab" ? tabs
        : selector === ".favorite-bank" ? stars : selector === ".bank-tab-wrap" ? wrappers : [];
    const originalDocument = globalThis.document;
    const originalCustomEvent = globalThis.CustomEvent;
    const originalFetch = globalThis.fetch;
    const events = new Map();
    globalThis.document = {
        getElementById: (id) => elements.get(id),
        addEventListener: (type, callback) => events.set(type, callback),
        dispatchEvent: (event) => events.get(event.type)?.(event)
    };
    globalThis.CustomEvent = class { constructor(type) { this.type = type; } };
    const requests = [];
    globalThis.fetch = async (url, init) => {
        assert.equal(url, "/api/auth/preferences");
        assert.equal(init.method, "PUT");
        const body = JSON.parse(init.body);
        requests.push(body);
        return { ok: true, status: 200, json: async () => ({
            ...body, favorite_banks: body.favorite_banks.slice().reverse()
        }) };
    };
    try {
        const { initBankTabs, refreshBankTabs } = await import("../js/ui/bank-tabs.js");
        const { renderBankPanel } = await import("../js/ui/bank-panel.js");
        // Mismo enlace de eventos que usa main.js.
        document.addEventListener("investment-section-changed", refreshBankTabs);
        const [primary, first, second, absent] = BANKS.map((bank) => bank.name);
        const fund = (banco, rendimiento) => ({ banco, rendimiento, nombre: `Fondo ${rendimiento}`,
            tipo: "FCI", garantizado: false, perfil_riesgo: "bajo", liquidez: "Inmediata",
            fuente: "Test", tna: 20, rendimiento_periodo_pct: 1, rendimiento_ultimo_dia_pct: null });
        const fixed = (banco, rendimiento) => ({ ...fund(banco, rendimiento),
            tipo: FIXED_DEPOSIT_TYPE, garantizado: true, horizonte: "30 dias", monto_final: 100000 + rendimiento });
        state.primaryBank = primary;
        state.favoriteBanks = [primary, first, second];
        state.selectedBank = first;
        state.selectedSection = SECTIONS.FIXED_TERM;
        state.capital = 100000;
        state.plazo = 30;
        state.options = [fixed(primary, 1000), fixed(first, 22000), fixed(second, 24000),
            fund(first, 40000), fund(first, 20000), fund(second, 10000), fund(absent, 90000),
            fund(WALLETS[0].name, 100), fund(WALLETS[1].name, 200)];
        const originalOptions = state.options.slice();
        initBankTabs((bank) => { state.selectedBank = bank; renderBankPanel(); });
        renderBankPanel();
        const tabNames = () => tabs.map((tab) => tab.dataset.bank);
        assert.deepEqual(tabNames().slice(0, 3), [primary, second, first]);
        assert.ok(elements.get("bank-panel").innerHTML.includes(`+$${formatNumber(22000)}`));
        const clickSection = (section) => elements.get("bank-panel").listeners.get("click")({ target: {
            closest: (selector) => selector === ".subtab" ? { dataset: { section } } : null
        } });
        clickSection(SECTIONS.FUNDS);
        assert.deepEqual(tabNames().slice(0, 4), [primary, first, second, absent]);
        const fundHtml = elements.get("bank-panel").innerHTML;
        assert.ok(fundHtml.indexOf("Fondo 40000") < fundHtml.indexOf("Fondo 20000"));
        assert.ok(fundHtml.includes(`$${formatNumber(40000)}`));
        assert.equal(state.selectedBank, first);
        assert.equal(tabs.find((tab) => tab.dataset.bank === first).attributes["aria-selected"], "true");
        assert.equal(stars.find((star) => star.dataset.favoriteBank === first).attributes["aria-pressed"], "true");
        assert.deepEqual(tabNames().slice(-2), [WALLETS[1].name, WALLETS[0].name]);
        clickSection(SECTIONS.FIXED_TERM);
        assert.deepEqual(tabNames().slice(0, 3), [primary, second, first]);
        assert.equal(state.options.length, originalOptions.length);
        state.options.forEach((option, index) => assert.equal(option, originalOptions[index]));
        assert.equal(requests.length, 0, "Cambiar de seccion no consulta APIs");

        const assertUniqueGroups = () => {
            const ordered = tabNames();
            assert.equal(ordered.length, BANKS.length + WALLETS.length);
            assert.equal(new Set(ordered).size, ordered.length);
            assert.ok(ordered.slice(0, BANKS.length).every((name) => BANKS.some((bank) => bank.name === name)));
            assert.ok(ordered.slice(BANKS.length).every((name) => WALLETS.some((wallet) => wallet.name === name)));
        };

        const cases = [
            { title: "sin Mi banco ni favoritos", own: null, favorites: [], expected: [second, first, primary, absent] },
            { title: "Mi banco sin favoritos", own: primary, favorites: [], expected: [primary, second, first, absent] },
            { title: "varios favoritos desordenados", own: null, favorites: [primary, first, second], expected: [second, first, primary, absent] },
            { title: "Mi banco tambien favorito aparece una sola vez", own: primary, favorites: [first, primary, second], expected: [primary, second, first, absent] },
            { title: "favorito sin plazo fijo queda al final de favoritos", own: null, favorites: [absent, first, second], expected: [second, first, absent, primary] }
        ];
        for (const scenario of cases) {
            await t.test(scenario.title, () => {
                state.primaryBank = scenario.own;
                state.favoriteBanks = scenario.favorites.slice();
                state.selectedSection = SECTIONS.FIXED_TERM;
                refreshBankTabs();
                assert.deepEqual(tabNames().slice(0, 4), scenario.expected);
                assert.deepEqual(state.favoriteBanks, scenario.favorites, "Renderizar no cambia preferencias");
                assertUniqueGroups();
            });
        }

        await t.test("empates mantienen el orden del catalogo", () => {
            state.primaryBank = null;
            state.favoriteBanks = [second, first];
            state.options = [fixed(second, 22000), fixed(first, 22000)];
            refreshBankTabs();
            assert.deepEqual(tabNames().slice(0, 2), [first, second]);
            assertUniqueGroups();
        });

        await t.test("marcar y desmarcar favoritos reordena tras guardar", async () => {
            state.primaryBank = primary;
            state.favoriteBanks = [primary, first];
            state.options = [fixed(primary, 1000), fixed(first, 22000), fixed(second, 24000), fixed(absent, 29000)];
            refreshBankTabs();
            const clickFavorite = async (name) => {
                const star = stars.find((item) => item.dataset.favoriteBank === name);
                tabList.listeners.get("click")({
                    target: { closest: () => star }, stopPropagation() {}
                });
                await new Promise((resolve) => setImmediate(resolve));
            };
            await clickFavorite(second);
            assert.deepEqual(tabNames().slice(0, 4), [primary, second, first, absent]);
            assert.equal(stars.find((star) => star.dataset.favoriteBank === second).attributes["aria-pressed"], "true");
            await clickFavorite(second);
            assert.deepEqual(tabNames().slice(0, 4), [primary, first, absent, second]);
            assert.equal(stars.find((star) => star.dataset.favoriteBank === second).attributes["aria-pressed"], "false");
            assert.equal(requests.length, 2, "Solo una llamada de guardado por clic");
            assert.ok(stars.every((star) => star.disabled === false));
            assertUniqueGroups();
        });

        await t.test("filtro solo favoritos conserva el orden y oculta billeteras", () => {
            state.favoriteOnly = false;
            elements.get("favorites-filter").listeners.get("click")();
            assert.equal(state.favoriteOnly, true);
            assert.deepEqual(wrappers.filter((item) => !item.classList.contains("hidden")).map((item) => item.dataset.bankWrap), [primary, first]);
            assert.equal(elements.get("wallets-label").classList.contains("hidden"), true);
            elements.get("favorites-filter").listeners.get("click")();
            assert.equal(state.favoriteOnly, false);
            assert.ok(wrappers.every((item) => !item.classList.contains("hidden")));
            assertUniqueGroups();
        });

        await t.test("quitar el ultimo favorito desactiva el filtro", async () => {
            state.primaryBank = null;
            state.favoriteBanks = [first];
            state.favoriteOnly = true;
            refreshBankTabs();
            tabList.listeners.get("click")({
                target: { closest: () => stars.find((star) => star.dataset.favoriteBank === first) },
                stopPropagation() {}
            });
            await new Promise((resolve) => setImmediate(resolve));
            assert.deepEqual(state.favoriteBanks, []);
            assert.equal(state.favoriteOnly, false);
            assert.equal(elements.get("favorites-filter").disabled, true);
            assert.ok(wrappers.every((item) => !item.classList.contains("hidden")));
        });

        await t.test("nueva simulacion recalcula retornos y reinicia la seccion visible", () => {
            state.primaryBank = primary;
            state.favoriteBanks = [primary, first, second];
            state.selectedSection = SECTIONS.FUNDS;
            setAnalysis({ capital: 100000, plazo: 30, riesgo: "bajo", plazos_fijos: [],
                opciones: [fixed(primary, 1000), fixed(first, 28000), fixed(second, 15000), fund(second, 50000)] });
            refreshBankTabs();
            assert.equal(state.selectedSection, SECTIONS.FIXED_TERM);
            assert.deepEqual(tabNames().slice(0, 3), [primary, first, second]);
            clickSection(SECTIONS.FUNDS);
            assert.deepEqual(tabNames().slice(0, 3), [primary, second, first]);
            assertUniqueGroups();
        });

        await t.test("billeteras muestran sus fondos ordenados sin plazo fijo", () => {
            state.options = [fund(WALLETS[0].name, 500), fund(WALLETS[0].name, 1500), fund(WALLETS[1].name, 2000)];
            state.selectedSection = SECTIONS.FIXED_TERM;
            refreshBankTabs();
            const walletTab = tabs.find((tab) => tab.dataset.bank === WALLETS[0].name);
            walletTab.listeners.get("click")();
            const html = elements.get("bank-panel").innerHTML;
            assert.ok(html.indexOf("Fondo 1500") < html.indexOf("Fondo 500"));
            assert.equal(html.includes('class="subtab '), false);
            assert.equal(state.selectedBank, WALLETS[0].name);
            assert.deepEqual(tabNames().slice(-2), [WALLETS[1].name, WALLETS[0].name]);
            assertUniqueGroups();
        });
    } finally {
        clearSessionState();
        globalThis.document = originalDocument;
        globalThis.CustomEvent = originalCustomEvent;
        globalThis.fetch = originalFetch;
    }
});
