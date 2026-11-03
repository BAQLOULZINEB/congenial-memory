import json
import os
import sys
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from frontend.reports import gap_csv, html_report

load_dotenv(ROOT / ".env")
API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="Talent Match · Analyse de CV", page_icon="◈", layout="wide")
st.markdown("""<style>
.block-container{max-width:1240px;padding-top:2.5rem}h1{letter-spacing:-1.7px;font-weight:750!important}
[data-testid="stMetric"]{background:white;border:1px solid #e4eaf1;border-radius:16px;padding:18px}
[data-testid="stSidebar"]{border-right:1px solid #e4eaf1}.eyebrow{color:#0f766e;font-size:12px;
font-weight:750;letter-spacing:2px}.intro{font-size:18px;color:#63738b;max-width:700px}
.pill{display:inline-block;border:1px solid #ccdeda;padding:5px 12px;border-radius:20px;color:#0f766e;font-size:12px}
div[data-testid="stForm"]{background:white;border-radius:18px}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ◈ Talent Match")
    st.caption("VOTRE PROCHAINE ÉTAPE, ÉCLAIRÉE.")
    st.divider()
    page = st.radio("Espace de travail", ["Analyser une candidature", "Comprendre la méthode"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Pondération du score**")
    st.caption("Répartissez 100 points entre les critères.")
    labels = {"hard_skills": "Compétences techniques", "experience": "Expérience",
              "education": "Formation", "soft_skills": "Compétences transversales"}
    defaults = [50, 25, 15, 10]
    weights = {k: st.slider(v, 0, 100, default, 5) / 100 for (k, v), default in zip(labels.items(), defaults)}
    total = round(sum(weights.values()) * 100)
    if total != 100:
        st.error(f"Total : {total} %. Ajustez à 100 %.")
    else:
        st.caption("✓ Total : 100 %")
    st.divider()
    st.caption("EMSI · 5AISDR · Groupe G8\n\nProjet IA & Data Science · 2026–2027")

if page == "Comprendre la méthode":
    st.title("Un score que vous pouvez expliquer.")
    st.write("Le pipeline suit trois étapes : extraire, évaluer, guider.")
    st.markdown("""
1. **Extraire** : lecture PDF/DOCX, nettoyage, segmentation, reconnaissance d'entités avec le dictionnaire spaCy.
2. **Évaluer** : normalisation des alias, embeddings all-MiniLM-L6-v2 et similarité cosinus.
   Une mention explicite vaut 100 ; une compétence connexe reste partielle (50 × similarité), jamais acquise.
3. **Guider** : synthèse, pistes de reformulation et projets de progression. Un service de génération peut enrichir les conseils avec votre accord.

Les critères absents de l'offre sont exclus et leurs poids redistribués. Une preuve absente du CV pour une exigence identifiée vaut zéro et doit être vérifiée.
Les compétences souhaitables comptent moitié moins que les prérequis. Le score n'est ni une probabilité d'embauche ni un classement objectif des personnes.

**Limites** : pas d'OCR intégré ; vocabulaire technique limité au dictionnaire ; durées explicites uniquement ;
formation évaluée par niveau, sans équivalence automatique des spécialités. MiniLM est principalement anglophone :
les correspondances françaises reposent aussi sur les alias bilingues. Les mentions négatives complexes demandent une vérification humaine.

**Confidentialité** : aucun fichier ni résultat n'est enregistré par l'application sur disque.
Les données restent en mémoire pendant la session. Si vous activez la génération, les preuves de compétences sont transmises au service configuré.
Le fichier JSON exporté contient les sections extraites : conservez-le comme un document personnel.
""")
    st.stop()

st.markdown('<div class="eyebrow">EXTRAIRE · ÉVALUER · GUIDER</div>', unsafe_allow_html=True)
st.title("Votre profil. Le poste. Les possibilités.")
st.markdown('<p class="intro">Comparez votre CV à une offre et transformez les écarts en un plan de progression concret.</p>', unsafe_allow_html=True)
st.markdown('<span class="pill">Analyse explicable</span> &nbsp; <span class="pill">PDF & DOCX</span> &nbsp; <span class="pill">Données en mémoire</span>', unsafe_allow_html=True)
st.write("")

demo = st.toggle("Essayer avec une candidature de démonstration", key="demo")
with st.form("analysis_form"):
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("01 · Votre parcours")
        cv_file = st.file_uploader("Importer votre CV", type=["pdf", "docx"], disabled=demo)
        cv_text = st.text_area("Ou coller le texte du CV", value=(ROOT / "examples/cv.txt").read_text(encoding="utf-8") if demo else "",
                               height=200, key=f"cv_{demo}", disabled=demo,
                               placeholder="Profil, expériences, compétences, formation…")
    with right:
        st.subheader("02 · Votre objectif")
        job_file = st.file_uploader("Importer l'offre d'emploi", type=["pdf", "docx"], disabled=demo)
        job_text = st.text_area("Ou coller l'offre d'emploi", value=(ROOT / "examples/job.txt").read_text(encoding="utf-8") if demo else "",
                                height=200, key=f"job_{demo}", disabled=demo,
                                placeholder="Description du poste et compétences recherchées…")
    st.caption("5 Mo et 30 pages maximum par fichier. Les PDF doivent contenir du texte sélectionnable.")
    use_llm = st.checkbox("Enrichir les conseils avec le modèle de langage configuré", value=False)
    st.caption("Cette option transmet les preuves de compétences au service configuré par l'administrateur. Les conseils locaux restent disponibles sans ce service.")
    submitted = st.form_submit_button("Analyser l'adéquation →", type="primary", use_container_width=True, disabled=total != 100)

if submitted:
    st.session_state.pop("result", None)
    if (not demo and cv_file and cv_text.strip()) or (not demo and job_file and job_text.strip()):
        st.error("Choisissez un fichier ou un texte pour chaque document, pas les deux.")
    elif (not cv_file and len(cv_text.strip()) < 30) or (not job_file and len(job_text.strip()) < 30):
        st.error("Ajoutez un CV et une offre contenant chacun au moins 30 caractères.")
    else:
        with st.spinner("Lecture des documents et comparaison des compétences…"):
            try:
                data = {"cv_text": cv_text, "job_text": job_text, "weights": json.dumps(weights), "use_llm": str(use_llm).lower()}
                files = {}
                if not demo:
                    for key, upload in [("cv_file", cv_file), ("job_file", job_file)]:
                        if upload:
                            files[key] = (upload.name, upload.getvalue(), upload.type)
                response = httpx.post(API + "/api/analyze/files", data=data, files=files or None, timeout=90)
                if response.is_success:
                    st.session_state.result = response.json()
                else:
                    detail = response.json().get("detail", "Erreur pendant l'analyse.")
                    st.error(detail if isinstance(detail, str) else "Données invalides. Vérifiez les documents.")
            except httpx.ConnectError:
                st.error("Le serveur d'analyse n'est pas disponible. Lancez le projet avec python run.py et attendez le chargement du modèle.")
            except httpx.TimeoutException:
                st.error("Le serveur met trop de temps à répondre. Réessayez avec un document plus court.")
            except (httpx.HTTPError, ValueError):
                st.error("Réponse du serveur illisible. Vérifiez les journaux du backend.")

result = st.session_state.get("result")
if result:
    st.divider()
    st.subheader("Votre bilan d'adéquation")
    st.caption("Résultat du dernier envoi. Après toute modification des documents ou des poids, relancez l'analyse.")
    score_col, summary_col = st.columns([1, 3])
    with score_col:
        st.metric("Score global", f"{result['score']:.1f} / 100")
        st.progress(result["score"] / 100)
    with summary_col:
        st.write(result["recommendations"]["summary"])
        counts = {status: sum(g["status"] == status for g in result["gaps"]) for status in ["Couvert", "Partiel", "Absent"]}
        st.write(f"🟢 {counts['Couvert']} couvertes · 🟠 {counts['Partiel']} partielles · ⚪ {counts['Absent']} absentes")
        st.caption(f"Analyse : {result['timings_ms']['total'] / 1000:.2f} s · Conseils : " +
                   ("modèle de langage" if result["recommendations"]["source"] == "llm" else "génération locale structurée"))
    cols = st.columns(4)
    for col, (key, label) in zip(cols, labels.items()):
        component = result["components"][key]
        col.metric(label, f"{component['score']:.0f} %" if component["score"] is not None else "Non exigé")
        col.caption(f"Poids effectif : {result['effective_weights'][key] * 100:.1f} %")
    gaps_tab, guide_tab, evidence_tab = st.tabs(["Matrice des écarts", "Votre plan d'action", "Preuves & méthode"])
    with gaps_tab:
        selected = st.multiselect("Afficher les statuts", ["Couvert", "Partiel", "Absent"], default=["Couvert", "Partiel", "Absent"])
        rows = [{"Compétence": g["skill"], "État": g["status"], "Exigence": "Requis" if g["required"] else "Souhaitable",
                 "Preuve dans le CV": g["evidence"]} for g in result["gaps"] if g["status"] in selected]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with guide_tab:
        first, second = st.columns(2)
        with first:
            st.markdown("#### Vos points d'appui")
            for item in result["recommendations"]["strengths"]:
                st.write("✓ " + item)
        with second:
            st.markdown("#### Vos priorités")
            for item in result["recommendations"]["priorities"]:
                st.write("→ " + item)
        st.markdown("#### Une feuille de route concrète")
        for action in result["recommendations"]["actions"]:
            with st.expander(action["skill"], expanded=True):
                st.write(action["project"])
                st.write("**Objectif vérifiable :** " + action["success_criterion"])
                st.write("**Ressource :** " + action["resource"])
        st.markdown("#### Mieux formuler vos acquis")
        for rewrite in result["recommendations"]["rewrites"]:
            st.caption("Extrait : " + rewrite["original"])
            st.write(rewrite["suggestion"])
    with evidence_tab:
        for warning in result["warnings"]:
            st.info(warning)
        for key, component in result["components"].items():
            st.write(f"**{labels[key]}** — {component['explanation']}")
        st.caption("Modèle : " + result["embedding_model"])
        a, b = st.columns(2)
        for col, title, profile in [(a, "CV", result["cv"]), (b, "Offre", result["job"])]:
            with col:
                st.markdown("#### Sections reconnues · " + title)
                for section, text in profile["sections"].items():
                    with st.expander(section):
                        st.text(text)
    st.divider()
    st.markdown("#### Emporter votre analyse")
    a, b, c = st.columns(3)
    a.download_button("↓ Rapport imprimable", html_report(result), "rapport-talent-match.html", "text/html", use_container_width=True)
    b.download_button("↓ Matrice CSV", gap_csv(result), "competences.csv", "text/csv", use_container_width=True)
    c.download_button("↓ Analyse JSON", json.dumps(result, ensure_ascii=False, indent=2), "analyse.json", "application/json", use_container_width=True)
    st.caption("Ouvrez le rapport HTML et utilisez Imprimer → Enregistrer en PDF.")
    if st.button("Effacer les résultats de cette session"):
        st.session_state.pop("result", None)
        st.rerun()
else:
    st.write("")
    for col, title, body in zip(st.columns(3), ["01  Extraire", "02  Évaluer", "03  Progresser"],
                                ["Vos compétences et expériences, structurées à partir de vos documents.",
                                 "Une comparaison qui distingue les acquis, les notions connexes et les écarts.",
                                 "Des pistes concrètes pour valoriser votre profil et préparer la suite."]):
        with col, st.container(border=True):
            st.markdown("#### " + title)
            st.write(body)
