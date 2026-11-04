import { useId } from "react";
export default function ScoreGauge({ score, compact = false }) {
  const id = useId();
  const value =
    score === null || score === undefined
      ? null
      : Math.max(0, Math.min(100, score));
  return (
    <div className={`score-gauge ${compact ? "gauge-compact" : ""}`}>
      <svg
        viewBox="0 0 240 140"
        role="img"
        aria-label={
          value === null
            ? "Adéquation : aucune analyse"
            : `Adéquation : ${value.toLocaleString("fr-FR")} sur 100`
        }
      >
        <defs>
          <linearGradient id={id}>
            <stop stopColor="#6550a1" />
            <stop offset=".55" stopColor="#955eb9" />
            <stop offset="1" stopColor="#bd663d" />
          </linearGradient>
        </defs>
        <path
          d="M 25 115 A 95 95 0 0 1 215 115"
          pathLength="100"
          fill="none"
          stroke="#26301924"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d="M 25 115 A 95 95 0 0 1 215 115"
          pathLength="100"
          fill="none"
          stroke={`url(#${id})`}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${value ?? 0} 100`}
          className="gauge-progress"
          opacity={value === null ? 0 : 1}
        />
        <text x="120" y="101" textAnchor="middle" className="gauge-value">
          {value === null
            ? "—"
            : value.toLocaleString("fr-FR", { maximumFractionDigits: 1 })}
        </text>
        <text x="120" y="123" textAnchor="middle" className="gauge-caption">
          {value === null ? "en attente d’analyse" : "sur 100"}
        </text>
        <text x="21" y="138" className="gauge-end">
          0
        </text>
        <text x="202" y="138" className="gauge-end">
          100
        </text>
      </svg>
    </div>
  );
}
