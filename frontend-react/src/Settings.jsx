import {
  RotateCcw,
  Sparkles,
  ShieldCheck,
  Check,
  SlidersHorizontal,
} from "lucide-react";
import { criteria, defaultWeights } from "./demo";
export default function Settings({ weights, setWeights, llm, setLLM }) {
  const total = Object.values(weights).reduce((a, b) => a + Number(b), 0);
  const presets = [
    [
      "Équilibré",
      { hard_skills: 25, experience: 25, education: 25, soft_skills: 25 },
    ],
    ["Technique", defaultWeights],
    [
      "Expérience",
      { hard_skills: 30, experience: 45, education: 15, soft_skills: 10 },
    ],
  ];
  return (
    <div className="configuration-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">VOTRE MOTEUR, VOS PRIORITÉS</p>
          <h1>Un réglage plus personnel.</h1>
          <p className="heading-description">
            Ajustez les critères de votre prochaine analyse.
          </p>
        </div>
        <span className="engineering-badge">
          <SlidersHorizontal size={16} /> Configuration
        </span>
      </header>
      <div className="configuration-grid">
        <section className="glass-card weight-panel">
          <div className="configuration-title">
            <div>
              <p className="eyebrow">01 / LE SCORE</p>
              <h2>Ce qui compte pour vous.</h2>
            </div>
            <span
              className={`weight-total ${total !== 100 ? "invalid" : ""}`}
              aria-live="polite"
            >
              {total === 100 && <Check size={16} />} {total}
              <small>/100</small>
            </span>
          </div>
          <div
            className="weight-presets"
            role="group"
            aria-label="Profils de pondération"
          >
            {presets.map(([label, values]) => (
              <button
                key={label}
                aria-pressed={criteria.every(
                  (c) => weights[c.key] === values[c.key],
                )}
                onClick={() => setWeights({ ...values })}
              >
                {label}
              </button>
            ))}
          </div>
          <div
            className="weight-distribution"
            aria-label="Répartition des quatre critères"
          >
            {criteria.map((c) => (
              <span
                key={c.key}
                className={c.color}
                style={{ flex: weights[c.key] || 0 }}
              />
            ))}
          </div>
          <div className="weight-sliders">
            {criteria.map((c) => (
              <div className="weight-control" key={c.key}>
                <label htmlFor={c.key}>
                  <i className={c.color} />
                  {c.label}
                  <strong>
                    {weights[c.key]}
                    <small> %</small>
                  </strong>
                </label>
                <input
                  id={c.key}
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={weights[c.key]}
                  aria-describedby="weight-help"
                  onChange={(e) =>
                    setWeights({ ...weights, [c.key]: Number(e.target.value) })
                  }
                  style={{ "--range-color": `var(--${c.color})` }}
                />
              </div>
            ))}
          </div>
          <div className="configuration-footer">
            <p
              id="weight-help"
              className={total !== 100 ? "field-error" : ""}
              role={total !== 100 ? "alert" : undefined}
            >
              {total === 100
                ? "100 points répartis. Prêt pour l’analyse."
                : `Total ${total} %. Ajustez à 100 % pour lancer une analyse.`}
            </p>
            <button
              className="text-button"
              onClick={() => setWeights({ ...defaultWeights })}
            >
              <RotateCcw size={15} />
              Rétablir 50 / 25 / 15 / 10
            </button>
          </div>
        </section>
        <div className="configuration-side">
          <section className="intelligence-panel">
            <div className="configuration-title">
              <span className="setting-icon">
                <Sparkles size={25} />
              </span>
              <span className="mode-badge">
                {llm ? "Enrichissement activé" : "Mode local"}
              </span>
            </div>
            <p className="eyebrow">02 / LES CONSEILS</p>
            <h2>Une aide à la rédaction.</h2>
            <label className="switch-label">
              <input
                type="checkbox"
                checked={llm}
                onChange={(e) => setLLM(e.target.checked)}
              />
              <span className="switch-track" />
              <strong>Utiliser le modèle de langage</strong>
            </label>
            <p>
              En activant cette option, les preuves de compétences sont envoyées
              au service configuré. Elles peuvent contenir des données
              personnelles.
            </p>
            <div className="llm-fallback">
              <ShieldCheck size={17} />
              <span>
                Service indisponible ? Les conseils locaux prennent le relais,
                avec un avertissement.
              </span>
            </div>
          </section>
          <section className="configuration-privacy glass-card">
            <ShieldCheck size={23} />
            <div>
              <h2>Vous gardez la main.</h2>
              <p>
                Réglages conservés dans cet onglet. Bilans sauvegardés dans
                SQLite uniquement à votre demande.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
