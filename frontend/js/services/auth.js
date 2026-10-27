// La cookie HttpOnly la administra el navegador; JavaScript nunca lee el token.
import { AUTH_ENDPOINT } from "../config.js";

async function request(path, data, method) {
    let response;
    try {
        response = await fetch(`${AUTH_ENDPOINT}/${path}`, {
            method: method || (data === undefined ? "GET" : "POST"),
            credentials: "same-origin",
            cache: "no-store",
            headers: { "Content-Type": "application/json", "X-Requested-With": "fetch" },
            ...(data === undefined ? {} : { body: JSON.stringify(data) })
        });
    } catch {
        throw new Error("No pudimos conectarnos. Probá nuevamente en unos segundos.");
    }
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const error = new Error(typeof body.detail === "string" ? body.detail : "No pudimos completar la solicitud.");
        error.status = response.status;
        throw error;
    }
    return response.status === 204 ? null : response.json();
}

export const getCurrentUser = () => request("me");
export const login = (data) => request("login", data);
export const register = (data) => request("register", data);
export const logout = () => request("logout", {});
export const getPreferences = () => request("preferences");
export const savePreferences = (data) => request("preferences", data, "PUT");
export const getFavoriteInvestments = () => request("favorite-investments");
export const saveFavoriteInvestment = (data) => request("favorite-investments", data);
export const deleteFavoriteInvestment = (key) => request(
    `favorite-investments/${encodeURIComponent(key)}`, undefined, "DELETE"
);
