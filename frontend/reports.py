import csv
import html
import io


def gap_csv(result: dict) -> str:
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Compétence", "Catégorie", "Statut", "Obligatoire", "Preuve"])
    for gap in result["gaps"]:
        values = [gap["skill"], gap["category"], gap["status"], str(gap["required"]), gap["evidence"]]
        writer.writerow(["'" + v if v.lstrip().startswith(("=", "+", "-", "@")) else v for v in values])
    return "\ufeff" + stream.getvalue()


def html_report(result: dict) -> str:
    esc = lambda value: html.escape(str(value))
    rows = "".join(f"<tr><td>{esc(g['skill'])}</td><td>{esc(g['status'])}</td><td>{esc(g['evidence'])}</td></tr>"
                   for g in result["gaps"])
    actions = "".join(f"<li><strong>{esc(a['skill'])}</strong> — {esc(a['project'])}<br>"
                      f"Ressource : {esc(a['resource'])}<br>Validation : {esc(a['success_criterion'])}</li>"
                      for a in result["recommendations"]["actions"])
    components = "".join(f"<li>{esc(k)} : {esc(v['score'] if v['score'] is not None else 'Non exigé')} / 100 "
                         f"— {esc(v['explanation'])}</li>" for k, v in result["components"].items())
    warnings = "".join(f"<li>{esc(w)}</li>" for w in result["warnings"])
    rewrites = "".join(f"<li>{esc(r['original'])}<br>→ {esc(r['suggestion'])}"
                       + (f"<br><small>{esc(r['rationale'])}</small>" if r.get("rationale") else "") + "</li>"
                       for r in result["recommendations"]["rewrites"])
    rec = result["recommendations"]
    critique = "".join(f"<li><strong>[{esc(c['severity'])}] {esc(c['point'])}</strong><br>{esc(c['explanation'])}</li>"
                       for c in rec.get("critique") or [])
    verdict = (f"<p><strong>Verdict : {esc(rec['verdict'])}</strong></p>" if rec.get("verdict") else "")
    critique_block = (f"<h2>Bilan critique</h2><p>{esc(rec.get('verdict_rationale', ''))}</p><ul>{critique}</ul>"
                      if critique else "")
    return f"""<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Rapport Talent Match</title><style>
body{{font:15px/1.6 system-ui,sans-serif;color:#172b4d;max-width:950px;margin:40px auto;padding:20px}}
h1,h2{{color:#0f766e}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}
li{{margin:12px 0}}.score{{font-size:48px;font-weight:700}}@media print{{body{{margin:0}}tr,li{{break-inside:avoid}}}}
</style><body><p>EMSI · IA & DATA SCIENCE · 5AISDR G8</p><h1>Bilan d'adéquation</h1>
<div class="score">{result['score']:.1f}<small> / 100</small></div>
{verdict}<p>{esc(rec['summary'])}</p>{critique_block}<h2>Détail du score</h2><ul>{components}</ul>
<p>Poids effectifs : {esc(result['effective_weights'])}</p>
<h2>Matrice des compétences</h2><table><thead><tr><th>Compétence</th><th>État</th><th>Preuve</th></tr></thead>
<tbody>{rows}</tbody></table><h2>Reformulations proposées</h2><ul>{rewrites}</ul>
<h2>Feuille de route</h2><ol>{actions}</ol><h2>Méthode et limites</h2><ul>{warnings}</ul>
<p>Modèle : {esc(result['embedding_model'])} · Conseils : {esc(result['recommendations']['source'])}
· Durée : {result['timings_ms']['total']:.0f} ms</p>
<p>Rapport confidentiel. Utilisez la fonction Imprimer de votre navigateur pour l'enregistrer en PDF.</p></body></html>"""
