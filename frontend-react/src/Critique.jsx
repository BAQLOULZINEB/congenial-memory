import { Gavel, Info, OctagonAlert, TriangleAlert } from "lucide-react";
import "./critique.css";

const VERDICT_TONE = {
  Solide: "good",
  "Recevable avec réserves": "fair",
  Fragile: "weak",
  "Non recommandée en l'état": "bad",
};
const SEVERITY = {
  bloquant: { label: "Bloquant", Icon: OctagonAlert },
  majeur: { label: "Majeur", Icon: TriangleAlert },
  mineur: { label: "Mineur", Icon: Info },
};

export function VerdictBadge({ verdict }) {
  if (!verdict) return null;
  return (
    <span className={`verdict-badge verdict-${VERDICT_TONE[verdict] ?? "fair"}`}>
      <Gavel size={14} aria-hidden="true" />
      Verdict : {verdict}
    </span>
  );
}

export function CritiquePanel({ recommendations: r }) {
  const items = r.critique ?? [];
  if (!r.verdict && !items.length) return null;
  return (
    <section className="glass-card critique-panel" aria-labelledby="critique-title">
      <div className="critique-head">
        <h2 id="critique-title">
          <Gavel size={20} aria-hidden="true" />
          Le regard du recruteur
        </h2>
        <VerdictBadge verdict={r.verdict} />
      </div>
      {r.verdict_rationale && <p className="critique-rationale">{r.verdict_rationale}</p>}
      <ul className="critique-list">
        {items.map((c, i) => {
          const { label, Icon } = SEVERITY[c.severity] ?? SEVERITY.mineur;
          return (
            <li key={i} className={`critique-item severity-${c.severity}`}>
              <span className="severity-tag">
                <Icon size={14} aria-hidden="true" />
                {label}
              </span>
              <div>
                <strong>{c.point}</strong>
                <p>{c.explanation}</p>
              </div>
            </li>
          );
        })}
      </ul>
      <small className="muted">
        {r.source === "llm"
          ? "Rédigé par un modèle de langage puis contrôlé : verdict jamais plus favorable que les règles, reformulations citant le CV mot pour mot, aucun chiffre ajouté."
          : "Bilan critique calculé par règles à partir des écarts détectés."}
      </small>
    </section>
  );
}
