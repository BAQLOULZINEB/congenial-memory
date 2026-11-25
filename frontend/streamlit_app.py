"""Talent Match — client Streamlit (BNF1).

Pure presentation layer: every computation goes through the FastAPI backend's typed contracts
(`POST /api/analyze/files` → `AnalysisResult`). Start the backend first, then:

    uv run --group ui streamlit run frontend/streamlit_app.py

`TALENT_MATCH_API` overrides the backend URL (default http://127.0.0.1:8000).
"""
import json
import os
import sys
from pathlib import Path

import httpx
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontend.reports import gap_csv, html_report

API = os.environ.get("TALENT_MATCH_API", "http://127.0.0.1:8000").rstrip("/")
STATUS_ICON = {"Couvert": "🟢 Couvert", "Partiel": "🟠 Partiel", "Absent": "🔴 Absent"}
SEVERITY = {"bloquant": st.error, "majeur": st.warning, "mineur": st.info}
VERDICT = {"Solide": st.success, "Recevable avec réserves": st.info, "Fragile": st.warning,
           "Non recommandée en l'état": st.error}
LABELS = {"hard_skills": "Compétences techniques", "experience": "Expérience", "education": "Formation",
          "soft_skills": "Savoir-être"}

st.set_page_config(page_title="Talent Match", page_icon="🎯", layout="wide")
st.title("🎯 Talent Match — Analyseur de CV et d'offre")
st.caption("EMSI · IA & Data Science · 5AISDR G8 — Extraire → Évaluer → Guider")

with st.sidebar:
    st.header("Pondérations")
    raw = {k: st.slider(LABELS[k], 0, 100, v, step=5)
           for k, v in {"hard_skills": 50, "experience": 25, "education": 15, "soft_skills": 10}.items()}
    total = sum(raw.values())
    if total == 0:
        st.error("Au moins un critère doit avoir un poids non nul.")
    weights = {k: round(v / total, 4) for k, v in raw.items()} if total else {}
    if weights:  # The API requires an exact total of 1.
        weights["soft_skills"] = round(1 - sum(v for k, v in weights.items() if k != "soft_skills"), 4)
        st.caption("Poids normalisés : " + ", ".join(f"{LABELS[k]} {v:.0%}" for k, v in weights.items()))
    use_llm = st.toggle("Bilan critique généré par IA", value=True,
                        help="Les sections du CV (hors coordonnées) sont envoyées au modèle configuré côté backend.")
    try:
        health = httpx.get(f"{API}/health", timeout=3).json()
        st.success(f"Backend prêt · {health['embedding_model'].split('/')[-1]}") if health["status"] == "ready" \
            else st.warning("Backend en cours de démarrage…")
    except httpx.HTTPError:
        st.error(f"Backend injoignable sur {API}")

left, right = st.columns(2)
with left:
    st.subheader("Votre CV")
    cv_file = st.file_uploader("Glissez votre CV (PDF ou DOCX)", type=["pdf", "docx"])
    cv_text = "" if cv_file else st.text_area("…ou collez son texte", height=220)
with right:
    st.subheader("L'offre d'emploi")
    job_file = st.file_uploader("Glissez l'offre (PDF ou DOCX)", type=["pdf", "docx"])
    job_text = "" if job_file else st.text_area("…ou collez la fiche de poste", height=220)

if st.button("Analyser", type="primary", disabled=not weights):
    files = {k: (f.name, f.getvalue()) for k, f in (("cv_file", cv_file), ("job_file", job_file)) if f}
    data = {"cv_text": cv_text, "job_text": job_text, "weights": json.dumps(weights), "use_llm": str(use_llm).lower()}
    with st.spinner("Extraction, vectorisation et génération du bilan…"):
        try:
            response = httpx.post(f"{API}/api/analyze/files", data=data, files=files or None, timeout=120)
        except httpx.HTTPError:
            st.error("Le backend ne répond pas.")
            st.stop()
    if response.status_code != 200:
        st.error(response.json().get("detail", "Analyse impossible."))
        st.stop()
    st.session_state["result"] = response.json()

result = st.session_state.get("result")
if result:
    rec = result["recommendations"]
    st.divider()
    top_left, top_right = st.columns([1, 2])
    with top_left:
        st.metric("Score d'adéquation", f"{result['score']:.1f} / 100")
        st.progress(min(result["score"] / 100, 1.0))
        st.caption(f"Calculé en {result['timings_ms']['total'] / 1000:.2f} s · conseils "
                   f"{'générés par LLM, vérifiés' if rec['source'] == 'llm' else 'locaux'}")
    with top_right:
        if rec.get("verdict"):
            VERDICT.get(rec["verdict"], st.info)(f"**Verdict : {rec['verdict']}** — {rec.get('verdict_rationale', '')}")
        st.write(rec["summary"])

    cols = st.columns(4)
    for col, (key, component) in zip(cols, result["components"].items()):
        col.metric(LABELS.get(key, key), "Non exigé" if component["score"] is None else f"{component['score']:.0f}/100",
                   f"poids {result['effective_weights'][key]:.0%}", delta_color="off", help=component["explanation"])

    tab_gap, tab_critique, tab_plan, tab_method = st.tabs(
        ["Matrice des écarts", "Bilan critique", "Plan de progression", "Méthode et limites"])
    with tab_gap:
        st.dataframe([{"Exigence": g["skill"], "État": STATUS_ICON[g["status"]],
                       "Type": "Prérequis" if g["required"] else "Souhaitable",
                       "Terme de l'offre": g.get("term") or "", "Similarité": g["similarity"], "Preuve": g["evidence"]}
                      for g in result["gaps"]], use_container_width=True, hide_index=True,
                     column_config={"Similarité": st.column_config.ProgressColumn(min_value=0, max_value=1)})
    with tab_critique:
        for item in rec.get("critique") or []:
            SEVERITY.get(item["severity"], st.info)(f"**[{item['severity'].upper()}] {item['point']}** — {item['explanation']}")
        st.subheader("Reformulations")
        for rewrite in rec["rewrites"]:
            with st.container(border=True):
                st.markdown(f"**Votre extrait :** {rewrite['original']}")
                st.markdown(f"**Proposition :** {rewrite['suggestion']}")
                if rewrite.get("rationale"):
                    st.caption(rewrite["rationale"])
    with tab_plan:
        for action in rec["actions"]:
            with st.expander(f"🎯 {action['skill']}"):
                st.write(action["project"])
                st.markdown(f"**Critère de réussite :** {action['success_criterion']}")
                st.markdown(f"**Ressource :** {action['resource']}")
    with tab_method:
        for warning in result["warnings"]:
            st.caption("• " + warning)
        st.caption(f"Modèle d'embeddings : {result['embedding_model']}")

    d1, d2, d3 = st.columns(3)
    d1.download_button("Rapport HTML (imprimable en PDF)", html_report(result), "bilan-talent-match.html", "text/html")
    d2.download_button("Matrice CSV", gap_csv(result), "competences.csv", "text/csv")
    d3.download_button("Données JSON", json.dumps(result, ensure_ascii=False, indent=2), "analyse-talent-match.json",
                       "application/json")
