export function escapeHTML(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (ch) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        ch
      ],
  );
}
export function csvReport(result) {
  const cell = (v) => {
    const text = String(v);
    return (
      '"' +
      (/^[\s]*[=+@-]/.test(text) ? "'" : "") +
      text.replaceAll('"', '""') +
      '"'
    );
  };
  return (
    "\uFEFF" +
    [
      ["Compétence", "Statut", "Exigence", "Preuve"],
      ...result.gaps.map((g) => [
        g.skill,
        g.status,
        g.required ? "Requis" : "Souhaitable",
        g.evidence,
      ]),
    ]
      .map((row) => row.map(cell).join(","))
      .join("\r\n")
  );
}
export function htmlReport(r) {
  const h = escapeHTML;
  return `<!doctype html><html lang="fr"><meta charset="utf-8"><title>Bilan Talent Match</title><style>body{font:15px/1.7 system-ui;color:#202032;max-width:920px;margin:40px auto;padding:24px}h1{font-size:36px}h2{margin-top:32px}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:12px;border-bottom:1px solid #ddd}li{margin-bottom:12px}.score{font-size:60px;color:#6240a0}@media print{body{margin:0}tr,li{break-inside:avoid}}</style><body><p>TALENT MATCH · BILAN CONFIDENTIEL</p><h1>Votre profil, en perspective.</h1><div class="score">${h(r.score)} / 100</div>${r.recommendations.verdict ? `<p><strong>Verdict : ${h(r.recommendations.verdict)}</strong></p>` : ""}<p>${h(r.recommendations.summary)}</p>${(r.recommendations.critique ?? []).length ? `<h2>Bilan critique</h2>${r.recommendations.verdict_rationale ? `<p>${h(r.recommendations.verdict_rationale)}</p>` : ""}<ul>${r.recommendations.critique.map((c) => `<li><strong>[${h(c.severity)}] ${h(c.point)}</strong><br>${h(c.explanation)}</li>`).join("")}</ul>` : ""}<h2>Décomposition du score</h2><ul>${Object.entries(
    r.components,
  )
    .map(
      ([key, c]) =>
        `<li>${h(key)} : ${c.score === null ? "Non exigé" : h(c.score) + "/100"} — ${h(c.explanation)}. Poids effectif : ${h(Math.round(r.effective_weights[key] * 100))}%.</li>`,
    )
    .join(
      "",
    )}</ul><h2>Matrice des compétences</h2><table><tr><th>Compétence</th><th>État</th><th>Preuve</th></tr>${r.gaps.map((g) => `<tr><td>${h(g.skill)}</td><td>${h(g.status)}</td><td>${h(g.evidence)}</td></tr>`).join("")}</table><h2>Plan de progression</h2><ol>${r.recommendations.actions.map((a) => `<li><strong>${h(a.skill)}</strong><p>${h(a.project)}</p><p>Validation : ${h(a.success_criterion)}</p><p>Ressource : ${h(a.resource)}</p></li>`).join("")}</ol><h2>Reformulations proposées</h2>${r.recommendations.rewrites.map((v) => `<p>${h(v.original)}<br>→ ${h(v.suggestion)}</p>`).join("")}<h2>Méthode et limites</h2><ul>${r.warnings.map((w) => `<li>${h(w)}</li>`).join("")}</ul><p>Modèle : ${h(r.embedding_model)}. Conseils : ${h(r.recommendations.source)}. Temps : ${h(r.timings_ms.total)} ms.</p><p>Utilisez Imprimer → Enregistrer en PDF dans votre navigateur.</p></body></html>`;
}
export function downloadReport(result, format) {
  const variants = {
    html: [
      htmlReport(result),
      "text/html;charset=utf-8",
      "bilan-talent-match.html",
    ],
    csv: [csvReport(result), "text/csv;charset=utf-8", "competences.csv"],
    json: [
      JSON.stringify(result, null, 2),
      "application/json",
      "analyse-talent-match.json",
    ],
  };
  const [content, type, name] = variants[format];
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
