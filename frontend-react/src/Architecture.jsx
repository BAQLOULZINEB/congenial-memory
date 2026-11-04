import { useState } from "react";
import {
  ArrowRight,
  Database,
  Code2,
  Layers,
  Sparkles,
  Monitor,
  ShieldCheck,
} from "lucide-react";

const views = {
  system: {
    title: "Des responsabilités clairement séparées.",
    subtitle: "Architecture de conteneurs · prototype local",
    nodes: [
      [
        "browser",
        "Navigateur",
        "React · JavaScript",
        "Interface",
        "Documents, réglages et résultats. React Router gère la navigation ; les exports sont générés dans le navigateur.",
        Monitor,
        "purple",
      ],
      [
        "api",
        "Serveur applicatif",
        "FastAPI · Pydantic",
        "API HTTP",
        "Vérifie le JWT pour l’historique personnel. Valide les entrées, orchestre l’analyse et expose les bilans enregistrés. Sert également les fichiers React compilés sur le port 8000.",
        Code2,
        "orange",
      ],
      [
        "nlp",
        "Moteur d’analyse",
        "spaCy · MiniLM",
        "Traitement Python",
        "Extrait les compétences, compare les preuves et calcule le score pondéré. Le modèle est chargé au démarrage du serveur.",
        Sparkles,
        "lime",
      ],
      [
        "db",
        "Historique local",
        "SQLite · stockage local",
        "Persistance",
        "La table analyses conserve uniquement les bilans enregistrés explicitement, filtrés par le compte connecté. Les fichiers PDF/DOCX originaux ne sont pas stockés.",
        Database,
        "blue",
      ],
    ],
    links: ["HTTP / JSON", "Appel Python", "SQL via l’API"],
  },
  pipeline: {
    title: "Du document aux preuves, puis au score.",
    subtitle: "Flux de traitement · un CV et une offre",
    nodes: [
      [
        "read",
        "Lire & nettoyer",
        "PyMuPDF · python-docx",
        "01 / Extraction",
        "Lecture des PDF textuels et DOCX, nettoyage et découpage en sections. Les PDF scannés nécessitent un OCR externe.",
        Layers,
        "purple",
      ],
      [
        "extract",
        "Reconnaître",
        "spaCy · dictionnaire",
        "02 / Normalisation",
        "Reconnaissance des compétences et de leurs alias, des diplômes et des durées explicites. Les preuves restent reliées au texte source.",
        Code2,
        "orange",
      ],
      [
        "match",
        "Comparer",
        "all-MiniLM-L6-v2",
        "03 / Similarités",
        "Les embeddings, les alias et les relations entre compétences alimentent les états Couvert, Partiel et Absent.",
        Sparkles,
        "lime",
      ],
      [
        "score",
        "Restituer",
        "Score · conseils · JSON",
        "04 / Résultat",
        "Agrégation des critères disponibles avec leurs poids effectifs. Conseils locaux par défaut ; enrichissement LLM facultatif avec validation et repli local.",
        Monitor,
        "blue",
      ],
    ],
    links: ["Texte nettoyé", "Compétences", "Écarts & preuves"],
  },
  data: {
    title: "Une sauvegarde explicite, un contrat précis.",
    subtitle: "Flux de persistance · indépendant de l’analyse",
    nodes: [
      [
        "save",
        "Enregistrer",
        "Action utilisateur",
        "01 / Consentement",
        "Le navigateur envoie le titre, le résultat validé et l’indicateur de démonstration uniquement après un clic sur Enregistrer ce bilan.",
        Monitor,
        "purple",
      ],
      [
        "validate",
        "Valider",
        "POST /api/analyses",
        "02 / Contrat",
        "Pydantic valide SaveAnalysisRequest. Le stockage limite le rapport JSON à 2 Mo ; les requêtes SQL utilisent des paramètres.",
        ShieldCheck,
        "orange",
      ],
      [
        "table",
        "Conserver",
        "Table analyses",
        "03 / SQLite",
        "id (UUID), title, created_at (UTC), score, is_demo et payload (JSON). utilisateur_id relie chaque bilan à son compte. Fichier local data/talentmatch.sqlite3, index par propriétaire et date.",
        Database,
        "blue",
      ],
      [
        "restore",
        "Retrouver",
        "GET · DELETE",
        "04 / Historique",
        "GET /api/analyses : liste paginée. GET /api/analyses/{id} : bilan complet. DELETE /api/analyses/{id} : suppression explicite.",
        Layers,
        "lime",
      ],
    ],
    links: ["Titre + résultat", "INSERT paramétré", "Lecture / suppression"],
  },
};
export default function Architecture() {
  const [view, setView] = useState("system");
  const [selected, setSelected] = useState("api");
  const current = views[view];
  const active =
    current.nodes.find((n) => n[0] === selected) || current.nodes[0];
  return (
    <div className="engineering-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">COMPRENDRE LE PROTOTYPE</p>
          <h1>L’architecture, en perspective.</h1>
          <p className="heading-description">
            Les composants, leurs échanges et la place de vos données.
          </p>
        </div>
        <span className="engineering-badge">
          <span /> Exécution locale
        </span>
      </header>
      <div
        className="diagram-tabs"
        role="group"
        aria-label="Vues de l’architecture"
      >
        {[
          ["system", "01", "Système"],
          ["pipeline", "02", "Pipeline NLP"],
          ["data", "03", "Données & API"],
        ].map(([id, num, label]) => (
          <button
            key={id}
            aria-pressed={view === id}
            onClick={() => {
              setView(id);
              setSelected(views[id].nodes[0][0]);
            }}
          >
            <span>{num}</span>
            {label}
          </button>
        ))}
      </div>
      <section
        className="system-diagram glass-card"
        aria-label={current.subtitle}
      >
        <div className="diagram-heading">
          <div>
            <p className="eyebrow">{current.subtitle}</p>
            <h2>{current.title}</h2>
          </div>
          <Layers aria-hidden="true" />
        </div>
        <div className="diagram-boundary">
          <span>
            {view === "system"
              ? "POSTE LOCAL · navigateur + processus Python + fichier SQLite"
              : view === "pipeline"
                ? "BACKEND · pipeline d’analyse"
                : "STOCKAGE LOCAL · aucune sauvegarde automatique"}
          </span>
          <div
            className={`system-nodes ${view === "system" ? "system-topology" : ""}`}
          >
            {current.nodes.map(([id, title, tech, label, , Icon, color], i) => (
              <div
                className={`system-step ${view === "system" && i === 3 ? "database-branch" : ""}`}
                key={id}
              >
                {view === "system" && i === 3 && (
                  <div className="database-connection">
                    SQL · lecture / écriture ↕
                  </div>
                )}
                <button
                  className={`system-node ${color} ${active[0] === id ? "node-selected" : ""}`}
                  aria-pressed={active[0] === id}
                  onClick={() => setSelected(id)}
                >
                  <Icon size={27} aria-hidden="true" />
                  <small>{label}</small>
                  <strong>{title}</strong>
                  <span>{tech}</span>
                </button>
                {i < (view === "system" ? 2 : 3) && (
                  <div className="diagram-connector" aria-hidden="true">
                    <span>{current.links[i]}</span>
                    <ArrowRight size={24} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="diagram-return">
          <ArrowRight size={16} aria-hidden="true" />
          <span>
            {view === "system"
              ? "Retour : résultat JSON → React. SQLite est reliée à FastAPI, jamais directement au moteur NLP."
              : view === "pipeline"
                ? "Option : conseils → service LLM configuré → réponse validée, ou repli local explicite."
                : "Réouverture : SQLite → FastAPI → React. L’analyse initiale ne crée aucune ligne en base."}
          </span>
        </div>
      </section>
      <div className="engineering-details">
        <section className="glass-card component-detail" aria-live="polite">
          <p className="eyebrow">COMPOSANT SÉLECTIONNÉ</p>
          <h2>{active[1]}</h2>
          <p>{active[4]}</p>
          <code>{active[2]}</code>
        </section>
        <aside className="engineering-note">
          <ShieldCheck size={23} aria-hidden="true" />
          <h2>Les frontières du prototype.</h2>
          <p>
            Le cahier des charges définit le pipeline d’analyse. React remplace
            Streamlit et SQLite ajoute l’historique à votre demande.
          </p>
          <small>
            Comptes locaux · JWT · base non chiffrée · LLM facultatif
          </small>
        </aside>
      </div>
    </div>
  );
}
