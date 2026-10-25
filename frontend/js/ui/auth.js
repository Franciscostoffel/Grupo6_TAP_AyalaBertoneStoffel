// Vista de acceso y restauración de la sesión. Las credenciales no se persisten.
import { getCurrentUser, login, logout, register } from "../services/auth.js";

const view = document.getElementById("auth-view");
const app = document.getElementById("app-content");
const form = document.getElementById("auth-form");
const title = document.getElementById("auth-title");
const submit = document.getElementById("auth-submit");
const toggle = document.getElementById("auth-toggle");
const loading = document.getElementById("auth-loading");
const feedback = document.getElementById("session-feedback");
const retry = document.getElementById("auth-retry");
const logoutButton = document.getElementById("logout-button");
let registering = false;
let version = 0;
let callbacks;

function showError(message) {
    feedback.textContent = message;
    feedback.classList.remove("hidden");
}

function clearError() {
    feedback.textContent = "";
    feedback.classList.add("hidden");
}

function setMode() {
    title.textContent = registering ? "Creá tu cuenta" : "Iniciá sesión";
    submit.textContent = registering ? "Crear cuenta" : "Ingresar";
    toggle.textContent = registering ? "Ya tengo cuenta" : "Crear una cuenta";
    form.elements.password.minLength = registering ? 15 : 1;
    form.elements.password.autocomplete = registering ? "new-password" : "current-password";
    document.getElementById("password-help").classList.toggle("hidden", !registering);
    form.elements.password.value = "";
    clearError();
}

function displayUser(user) {
    view.classList.add("hidden");
    app.classList.remove("hidden");
    document.querySelectorAll(".auth-only").forEach((element) => element.classList.remove("hidden"));
    document.getElementById("user-email").textContent = user.email;
    document.querySelector(".skip-link").href = "#simulador";
    form.reset();
    clearError();
    callbacks.onAuthenticated(user);
}

export function showSignedOut(message = "") {
    version += 1;
    registering = false;
    callbacks.onSignedOut();
    app.classList.add("hidden");
    view.classList.remove("hidden");
    loading.classList.add("hidden");
    form.classList.remove("hidden");
    toggle.classList.remove("hidden");
    retry.classList.add("hidden");
    document.querySelectorAll(".auth-only").forEach((element) => element.classList.add("hidden"));
    document.getElementById("user-email").textContent = "";
    document.querySelector(".skip-link").href = "#auth-title";
    form.reset();
    setMode();
    if (message) showError(message);
}

async function restoreSession() {
    const attempt = ++version;
    clearError();
    view.classList.remove("hidden");
    app.classList.add("hidden");
    document.querySelectorAll(".auth-only").forEach((element) => element.classList.add("hidden"));
    loading.classList.remove("hidden");
    form.classList.add("hidden");
    toggle.classList.add("hidden");
    retry.classList.add("hidden");
    try {
        const user = await getCurrentUser();
        if (attempt === version) displayUser(user);
    } catch (error) {
        if (attempt !== version) return;
        if (error.status === 401) {
            showSignedOut();
        } else {
            view.classList.remove("hidden");
            app.classList.add("hidden");
            document.querySelectorAll(".auth-only").forEach((element) => element.classList.add("hidden"));
            showError(error.message);
            retry.classList.remove("hidden");
        }
    } finally {
        if (attempt === version) loading.classList.add("hidden");
    }
}

export function initAuth(handlers) {
    callbacks = handlers;
    setMode();
    toggle.addEventListener("click", () => {
        registering = !registering;
        setMode();
        form.elements.email.focus();
    });
    retry.addEventListener("click", restoreSession);
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.reportValidity()) return;
        const attempt = ++version;
        const data = { email: form.elements.email.value, password: form.elements.password.value };
        submit.disabled = toggle.disabled = true;
        submit.textContent = "Esperá un momento...";
        clearError();
        try {
            const user = await (registering ? register(data) : login(data));
            if (attempt !== version) return;
            displayUser(user);
            document.getElementById("capital").focus({ preventScroll: true });
        } catch (error) {
            if (attempt === version) showError(error.message);
        } finally {
            data.password = "";
            form.elements.password.value = "";
            submit.disabled = toggle.disabled = false;
            submit.textContent = registering ? "Crear cuenta" : "Ingresar";
        }
    });
    logoutButton.addEventListener("click", async () => {
        logoutButton.disabled = true;
        clearError();
        try {
            await logout();
            showSignedOut();
            form.elements.email.focus();
        } catch (error) {
            showError(error.message);
        } finally {
            logoutButton.disabled = false;
        }
    });
    // Una página recuperada desde la caché de navegación debe revalidar su sesión.
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) restoreSession();
    });
    restoreSession();
}
