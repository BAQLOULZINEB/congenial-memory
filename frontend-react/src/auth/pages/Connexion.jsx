// Page /connexion : email + mot de passe -> POST /auth/connexion -> jeton

import { LoaderCircle, LogIn } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import CadreAuth, {
  ChampAuth,
  MessageErreur,
} from "../components/CadreAuth.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function Connexion() {
  const { utilisateur, connexion } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  // Déjà connecté en arrivant sur la page : pas besoin de cette page
  // (!envoi : juste après la connexion, c'est envoyer() qui choisit où aller)
  if (utilisateur && !envoi) return <Navigate to="/" replace />;

  async function envoyer(evenement) {
    evenement.preventDefault(); // empêche le rechargement de la page par le formulaire
    setErreur("");
    setEnvoi(true);
    try {
      await connexion(email.trim(), motDePasse);
      // Retour à la page demandée avant la redirection, sinon tableau de bord
      navigate(location.state?.depuis || "/", { replace: true });
    } catch (e) {
      setErreur(e.message); // 401 : « Email ou mot de passe incorrect. »
      setEnvoi(false);
    }
  }

  return (
    <CadreAuth
      titre="Bon retour"
      sousTitre="Retrouvez vos analyses et vos pistes de progression."
    >
      <form onSubmit={envoyer} noValidate>
        <MessageErreur>{erreur}</MessageErreur>
        <ChampAuth
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <ChampAuth
          label="Mot de passe"
          type="password"
          autoComplete="current-password"
          value={motDePasse}
          onChange={(e) => setMotDePasse(e.target.value)}
          required
        />
        <button
          type="submit"
          disabled={envoi || !email || !motDePasse}
          className="button auth-submit"
        >
          {envoi ? (
            <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <LogIn className="size-4" aria-hidden="true" />
          )}
          {envoi ? "Connexion…" : "Se connecter"}
        </button>
      </form>
      <p className="auth-switch">
        Pas encore de compte ?{" "}
        <Link to="/inscription" className="auth-link">
          Créer un compte
        </Link>
      </p>
    </CadreAuth>
  );
}
