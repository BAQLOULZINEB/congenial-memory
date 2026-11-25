// =====================================================================
// Contexte d'authentification : partage l'utilisateur connecté avec
// toutes les pages, sans le passer de composant en composant.
// =====================================================================

import { createContext, useContext, useEffect, useState } from "react";
import { api, effacerJeton, enregistrerJeton, lireJeton } from "../api.js";
import { clearAnalysisSession } from "../../sessionAnalysis";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Le jeton est relu dans le localStorage au démarrage (connexion conservée après F5)
  const [jeton, setJeton] = useState(lireJeton);
  const [utilisateur, setUtilisateur] = useState(null);
  // S'il y a un jeton, on doit d'abord le vérifier auprès de l'API
  const [verification, setVerification] = useState(() => Boolean(lireJeton()));

  // À chaque nouveau jeton : GET /auth/moi pour vérifier qu'il est valide
  useEffect(() => {
    if (!jeton) return;
    let actif = true; // évite de modifier l'état si le composant a disparu entre-temps
    api
      .moi()
      .then((u) => actif && setUtilisateur(u))
      .catch(() => {
        if (!actif) return;
        effacerJeton();
        setJeton(null);
        setUtilisateur(null);
      })
      .finally(() => actif && setVerification(false));
    return () => {
      actif = false;
    };
  }, [jeton]);

  useEffect(() => {
    const expire = () => {
      setJeton(null);
      setUtilisateur(null);
      setVerification(false);
    };
    window.addEventListener("talentmatch:session-expired", expire);
    const sync = (event) => {
      if (event.key === "talentmatch.session") {
        clearAnalysisSession();
        setUtilisateur(null);
        setVerification(Boolean(lireJeton()));
        setJeton(lireJeton());
      }
    };
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("talentmatch:session-expired", expire);
      window.removeEventListener("storage", sync);
    };
  }, []);

  async function connexion(email, motDePasse) {
    const reponse = await api.connexion(email, motDePasse);
    enregistrerJeton(reponse.access_token);
    setUtilisateur(reponse.utilisateur);
    setJeton(reponse.access_token);
  }

  async function inscription(nom, email, motDePasse) {
    await api.inscription(nom, email, motDePasse);
    // Inscription réussie : connexion automatique
    await connexion(email, motDePasse);
  }

  function deconnexion() {
    effacerJeton();
    setJeton(null);
    setUtilisateur(null);
  }

  const valeur = {
    utilisateur,
    verification,
    connexion,
    inscription,
    deconnexion,
  };
  return <AuthContext.Provider value={valeur}>{children}</AuthContext.Provider>;
}

// Raccourci : const { utilisateur } = useAuth()
// eslint-disable-next-line react/only-export-components
export function useAuth() {
  return (
    useContext(AuthContext) || {
      utilisateur: null,
      verification: false,
      deconnexion: () => {},
    }
  );
}
