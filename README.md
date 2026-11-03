# Talent Match — Analyseur intelligent de CV et d'offre d'emploi

Projet du module IA & Data Science, EMSI, 5AISDR G8, année 2026–2027.
Réalisé pour le cahier des charges de DRISSI Yassir, BENHEDDANE Mohamed et BAQLOUL Zineb,
encadré par Mme Salma Aitoussous.

## Lancer sur Windows

Prérequis : [uv](https://docs.astral.sh/uv/getting-started/installation/) et accès Internet au premier lancement.
Python 3.12 est recommandé ; uv peut l'installer automatiquement.

```powershell
uv sync --frozen
uv run python run.py
```

Ou exécuter `start.ps1` depuis PowerShell. Interface : http://127.0.0.1:8501.
API et documentation interactive : http://127.0.0.1:8000/docs.
Le modèle MiniLM est téléchargé au premier lancement puis conservé dans le cache Hugging Face.
Le lanceur attend le chargement avant d'ouvrir le navigateur. Ctrl+C arrête les deux services.
Les ports 8000 et 8501 doivent être libres.

Lancement séparé, dans deux terminaux à la racine :

```powershell
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
uv run streamlit run frontend/app.py --server.address 127.0.0.1
```

## Utiliser

1. Importer un CV PDF/DOCX ou coller son texte.
2. Importer une offre PDF/DOCX ou coller sa description. Utiliser une seule source par document.
3. Ajuster les quatre poids, dont la somme doit rester égale à 100 %.
4. Lancer l'analyse, consulter les preuves et les compétences couvertes, partielles et absentes.
5. Exporter le bilan HTML imprimable, la matrice CSV ou le résultat JSON complet.
   Ouvrir le HTML dans un navigateur puis **Imprimer → Enregistrer en PDF**.

Le mode démonstration charge `examples/cv.txt` et `examples/job.txt`.
Aucun fichier utilisateur n'est enregistré par le backend. Les résultats restent dans la session Streamlit.

## Génération textuelle

Sans configuration, le moteur produit des conseils structurés locaux. **Ce mode n'est pas un LLM**.
Pour une génération conditionnée par un modèle de langage, installer un serveur local compatible
avec l'API Chat Completions, par exemple Ollama, puis :

```powershell
ollama pull qwen2.5:3b
Copy-Item .env.example .env
```

Ollama doit être actif. La configuration par défaut utilise `http://localhost:11434/v1`.
Pour un autre serveur, régler `LLM_BASE_URL`, `LLM_MODEL` et, si nécessaire, `LLM_API_KEY`.
Activer la case d'enrichissement dans l'interface. Seules les compétences et leurs extraits justificatifs
sont envoyés ; ces extraits peuvent contenir des données personnelles. Un service distant reçoit ces données.
La réponse est validée par Pydantic. Les liens restent issus du dictionnaire.
En cas d'indisponibilité ou de JSON invalide, le mode local prend le relais avec un avertissement visible.
La génération peut prendre jusqu'à 45 secondes, hors objectif de latence du calcul NLP.

## Architecture

```text
frontend/app.py       Streamlit : saisie, graphiques, preuves, exports
frontend/reports.py   HTML imprimable et CSV protégés contre l'injection
backend/main.py       FastAPI : contrats JSON et multipart, readiness
backend/parsing.py    Lecture PDF/DOCX et nettoyage
backend/extraction.py spaCy EntityRuler, segmentation, durées et diplômes
backend/taxonomy.py   Dictionnaire bilingue, relations dirigées et ressources
backend/embeddings.py Sentence-Transformers / Hugging Face, modèle chargé une fois
backend/analysis.py   Similarités, matrice d'écarts et score composite
backend/recommendations.py  Conseils locaux + génération optionnelle
backend/schemas.py    Structures Pydantic typées et validées
tests/               Tests du pipeline, API, sécurité des exports et interface
```

Le frontend appelle uniquement l'API pour l'analyse. Aucun calcul NLP dans la couche de présentation.
L'API expose `POST /api/analyze` (JSON), `POST /api/analyze/files` (multipart/form) et `GET /health`.
Les champs JSON : `cv_text`, `job_text`, `weights` et `use_llm`.
En multipart : mêmes champs (weights est une chaîne JSON), plus `cv_file` et `job_file` facultatifs.

## Calcul explicable

Pondération par défaut : `0.50 × technique + 0.25 × expérience + 0.15 × formation + 0.10 × transversal`.

- Alias canonique présent : **Couvert**, 100 points.
- Relation dirigée connue (ex. PyTorch → Deep Learning), ou similarité cosinus ≥ 0,60 dans le même domaine :
  **Partiel**, `50 × similarité` points. Pour une relation connue, le coefficient est au minimum 0,60.
- Sinon : **Absent**, zéro point. Une parenté sémantique ne prouve jamais une maîtrise.
- Une exigence souhaitable compte moitié moins qu'une exigence obligatoire.
- Expérience : ratio des années déclarées, plafonné à 100 %. Pas de sommation des périodes ambiguës.
- Formation : ratio du niveau académique reconnu, plafonné à 100 %. La spécialité doit être contrôlée manuellement.
- Si l'offre ne précise pas un critère, son poids est redistribué entre les critères renseignés.
  Si le CV n'apporte pas de preuve pour une exigence explicite, le critère vaut zéro avec avertissement.
- Une offre sans compétence reconnue produit une erreur explicite plutôt qu'un score arbitraire.

## Validation et limites

```powershell
uv run pytest -q
uv run ruff check .
```

Les tests unitaires injectent des embeddings déterministes : ils vérifient la logique sans télécharger de modèle.
Le modèle réel est utilisé dans l'application ; le script `scripts/benchmark.py` mesure la latence après préchauffage.
Les fichiers sont limités à 5 Mo, 30 pages PDF et 30 000 caractères. Les DOCX décompressés sont limités à 30 Mo.
Les PDF scannés demandent un OCR externe, les PDF chiffrés sont refusés.

La reconnaissance d'entités repose sur des règles spaCy, et non sur un modèle NER entraîné sur un corpus de CV.
Le dictionnaire est extensible mais non exhaustif. La négation simple est filtrée ; les négations complexes,
les exigences alternatives et les formulations ambiguës nécessitent une relecture.
MiniLM all-MiniLM-L6-v2 est principalement anglophone ; les alias bilingues facilitent le français,
mais une évaluation sur corpus annoté français reste nécessaire. Les seuils ne sont pas calibrés scientifiquement.
Les suggestions LLM doivent être relues et ne doivent jamais servir à inventer des acquis.
Ce projet local ne fournit pas authentification, multi-utilisateur, stockage ou déploiement public sécurisé.

La cible de 5 secondes concerne le pipeline à chaud, hors téléchargement du modèle et génération LLM.
Les durées de chaque analyse sont affichées. Ce n'est pas une garantie sur tout matériel ou document.

## Références techniques

- [FastAPI : fichiers et formulaires](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/)
- [spaCy : EntityRuler](https://spacy.io/api/entityruler)
- [Sentence-Transformers : encode et normalisation](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)
- [Streamlit : import de fichiers](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)

