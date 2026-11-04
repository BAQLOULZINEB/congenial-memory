// Page /inscription : nom + email + mot de passe -> POST /auth/inscription -> connexion automatique

import { LoaderCircle, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import CadreAuth, {
  ChampAuth,
  MessageErreur,
} from "../components/CadreAuth.jsx";
import { useAuth } from "../context/AuthContext.jsx";

// Même règle que l'API (MOTIF_EMAIL dans api/main.py)
const MOTIF_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

// Vérifie les champs avant l'envoi (mêmes règles que le schéma Pydantic « Inscription »)
function verifier({ nom, email, motDePasse }) {
  const erreurs = {};
  if (nom.trim().length < 2) erreurs.nom = "Au moins 2 caractères.";
  if (!MOTIF_EMAIL.test(email.trim()))
    erreurs.email = "Adresse email invalide.";
  if (motDePasse.length < 8) erreurs.motDePasse = "Au moins 8 caractères.";
  if (new TextEncoder().encode(motDePasse).length > 72)
    erreurs.motDePasse =
      "Au plus 72 octets (attention aux caractères accentués).";
  return erreurs;
}

export default function Inscription() {
  const { utilisateur, inscription } = useAuth();
  const navigate = useNavigate();

  const [champs, setChamps] = useState({ nom: "", email: "", motDePasse: "" });
  const [erreurs, setErreurs] = useState({});
  const [erreurApi, setErreurApi] = useState("");
  const [envoi, setEnvoi] = useState(false);

  // Déjà connecté en arrivant sur la page (!envoi : pas juste après l'inscription)
  if (utilisateur && !envoi) return <Navigate to="/" replace />;

  // Met à jour un champ ; si une erreur était affichée, on la recalcule en direct
  function modifier(cle, valeur) {
    const suivants = { ...champs, [cle]: valeur };
    setChamps(suivants);
    if (erreurs[cle]) setErreurs(verifier(suivants));
  }

  async function envoyer(evenement) {
    evenement.preventDefault();
    setErreurApi("");
    const trouvees = verifier(champs);
    setErreurs(trouvees);
    if (Object.keys(trouvees).length > 0) return;

    setEnvoi(true);
    try {
      await inscription(
        champs.nom.trim(),
        champs.email.trim(),
        champs.motDePasse,
      );
      navigate("/", { replace: true });
    } catch (e) {
      setErreurApi(e.message); // 409 : « Un compte existe déjà avec cet email. »
      setEnvoi(false);
    }
  }

  return (
    <CadreAuth
      titre="Créer un compte"
      sousTitre="Un espace personnel pour vos bilans de candidature."
    >
      <form onSubmit={envoyer} noValidate>
        <MessageErreur>{erreurApi}</MessageErreur>
        <ChampAuth
          label="Nom"
          autoComplete="name"
          value={champs.nom}
          onChange={(e) => modifier("nom", e.target.value)}
          erreur={erreurs.nom}
        />
        <ChampAuth
          label="Email"
          type="email"
          autoComplete="email"
          value={champs.email}
          onChange={(e) => modifier("email", e.target.value)}
          erreur={erreurs.email}
        />
        <ChampAuth
          label="Mot de passe"
          type="password"
          autoComplete="new-password"
          value={champs.motDePasse}
          onChange={(e) => modifier("motDePasse", e.target.value)}
          erreur={erreurs.motDePasse}
          aide="8 caractères minimum."
        />
        <button type="submit" disabled={envoi} className="button auth-submit">
          {envoi ? (
            <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <UserPlus className="size-4" aria-hidden="true" />
          )}
          {envoi ? "Création du compte…" : "Créer mon compte"}
        </button>
      </form>
      <p className="auth-switch">
        Déjà inscrit ?{" "}
        <Link to="/connexion" className="auth-link">
          Se connecter
        </Link>
      </p>
    </CadreAuth>
  );
}
