// Adapted from prediction-prix-immobilier: bearer token + JSON auth endpoints.
const TOKEN_KEY = "talentmatch.session";
export const lireJeton = () => localStorage.getItem(TOKEN_KEY);
export const enregistrerJeton = (token) =>
  localStorage.setItem(TOKEN_KEY, token);
export const effacerJeton = () => localStorage.removeItem(TOKEN_KEY);
export function authHeaders() {
  const token = lireJeton();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
export async function authFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { ...options.headers, ...authHeaders() },
  });
  if (response.status === 401) {
    effacerJeton();
    window.dispatchEvent(new Event("talentmatch:session-expired"));
  }
  return response;
}
async function request(path, body) {
  const response = await authFetch("/api/auth/" + path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Vérifiez les informations saisies.",
    );
  return data;
}
export const api = {
  connexion: (email, mot_de_passe) =>
    request("connexion", { email, mot_de_passe }),
  inscription: (nom, email, mot_de_passe) =>
    request("inscription", { nom, email, mot_de_passe }),
  moi: () => request("moi"),
};
