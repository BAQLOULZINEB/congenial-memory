// =====================================================================
// Cadre commun aux pages Connexion et Inscription :
// carte blanche (formulaire) + panneau décoratif zellige
// =====================================================================

import { CircleAlert, Eye, EyeOff } from "lucide-react";
import { useId, useState } from "react";
import Brand from "../../Brand.jsx";

export default function CadreAuth({ titre, sousTitre, children }) {
  return (
    <main className="auth-page">
      <section className="auth-frame">
        <div className="auth-form-panel">
          <Brand />
          <div className="auth-intro">
            <p className="eyebrow">ESPACE PERSONNEL</p>
            <h1>{titre}</h1>
            <p>{sousTitre}</p>
          </div>
          {children}
          <p className="auth-footnote">
            Compte local · mot de passe haché · session de 60 minutes
          </p>
        </div>
        <aside className="auth-art">
          <span className="auth-edition">TALENT MATCH / CANDIDATURES</span>
          <div className="auth-art-type">
            Votre parcours.
            <br />
            <em>
              Votre prochaine
              <br />
              étape.
            </em>
          </div>
          <div className="auth-visual" aria-hidden="true">
            <div className="auth-paper">
              <span>PARCOURS</span>
              <i />
              <i />
              <i />
              <strong>CV</strong>
            </div>
            <div className="auth-paper second">
              <span>OPPORTUNITÉ</span>
              <i />
              <i />
              <i />
              <strong>OFFRE</strong>
            </div>
          </div>
          <p>
            Comparez votre CV à une offre.
            <br />
            Identifiez vos acquis et préparez la suite.
          </p>
          <span className="auth-art-footer">
            Analyse explicable. Décision humaine.
          </span>
        </aside>
      </section>
    </main>
  );
}

// Champ de formulaire : <label> relié à l'<input> + message d'erreur éventuel
// type="password" : ajoute un bouton pour afficher / masquer le mot de passe
export function ChampAuth({ label, type = "text", erreur, aide, ...props }) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  const motDePasse = type === "password";

  return (
    <div className="auth-field">
      <label htmlFor={id} className="auth-label">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={motDePasse && visible ? "text" : type}
          aria-invalid={Boolean(erreur)}
          aria-describedby={erreur || aide ? `${id}-info` : undefined}
          className={`auth-input ${erreur ? "invalid" : ""}`}
          {...props}
        />
        {motDePasse && (
          <button
            type="button"
            onClick={() => setVisible(!visible)}
            aria-label={
              visible ? "Masquer le mot de passe" : "Afficher le mot de passe"
            }
            className="password-reveal"
          >
            {visible ? (
              <EyeOff className="size-4" aria-hidden="true" />
            ) : (
              <Eye className="size-4" aria-hidden="true" />
            )}
          </button>
        )}
      </div>
      {(erreur || aide) && (
        <p id={`${id}-info`} className={erreur ? "field-error" : "auth-help"}>
          {erreur || aide}
        </p>
      )}
    </div>
  );
}

// Encadré d'erreur renvoyée par l'API (lu par les lecteurs d'écran grâce à role="alert")
export function MessageErreur({ children }) {
  if (!children) return null;
  return (
    <div role="alert" className="auth-error">
      <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
