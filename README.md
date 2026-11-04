# Talent Match — Analyseur intelligent de CV et d'offre d'emploi

Projet du module IA & Data Science, EMSI, 5AISDR G8, année 2026–2027.
Réalisé pour le cahier des charges de DRISSI Yassir, BENHEDDANE Mohamed et BAQLOUL Zineb,
encadré par Mme Salma Aitoussous.

## Lancer sur Windows

Prérequis : [uv](https://docs.astral.sh/uv/getting-started/installation/), Node.js 22.12+ avec npm,
et accès Internet au premier lancement. Python 3.12 est recommandé ; uv peut l'installer automatiquement.
L'interface utilise React 19, JavaScript, Vite, Tailwind CSS, Framer Motion et Lucide,
comme le projet de référence immobilier. Streamlit a été retiré.

```powershell
uv sync --frozen
uv run python run.py
```

Ou exécuter `start.ps1` depuis PowerShell. Interface : http://127.0.0.1:8000.
API et documentation interactive : http://127.0.0.1:8000/docs. Le port 8501 n'est plus utilisé.
Le lanceur installe les dépendances JavaScript avec `npm ci`, compile React puis démarre FastAPI.
L'interface et l'API partagent la même origine ; aucun serveur Vite n'est nécessaire pour cette utilisation.
Le modèle MiniLM est téléchargé au premier lancement puis conservé dans le cache Hugging Face.
Le lanceur attend le chargement avant d'ouvrir le navigateur. Ctrl+C arrête le service.
Le port 8000 doit être libre. SQLite conserve uniquement les bilans explicitement enregistrés.

Pour réutiliser un build existant sans réinstaller ou compiler :

```powershell
uv run python run.py --skip-build
```

Ajouter `--no-browser` pour ne pas ouvrir automatiquement un onglet.

## Développement React

Dans un premier terminal à la racine :

```powershell
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Dans un second terminal :

```powershell
cd frontend-react
npm ci
npm run dev
```

Vite sert alors l'interface sur http://127.0.0.1:5173 et relaie `/api` et `/health` vers FastAPI.
Ne lancez pas `run.py` et la commande uvicorn en parallèle sur le même port.
Pour une livraison compilée : `npm run build` dans `frontend-react`, puis `uv run python run.py --skip-build` à la racine.

## Utiliser

1. Importer un CV PDF/DOCX ou coller son texte.
2. Importer une offre PDF/DOCX ou coller sa description. Utiliser une seule source par document.
3. Ajuster les quatre poids, dont la somme doit rester égale à 100 %.
4. Lancer l'analyse, consulter les preuves et les compétences couvertes, partielles et absentes.
5. Choisir **Enregistrer ce bilan** pour le conserver dans SQLite, puis le retrouver dans **Bilans enregistrés**.
6. Exporter le bilan HTML imprimable, la matrice CSV ou le résultat JSON complet.
   Ouvrir le HTML dans un navigateur puis **Imprimer → Enregistrer en PDF**.

Le mode démonstration fournit un exemple de CV et d'offre sans utiliser de données personnelles.
Le backend ne conserve pas les fichiers utilisateur après leur traitement. Le mécanisme d'import de FastAPI
peut utiliser des fichiers temporaires sur disque pour les téléversements volumineux ; ils sont fermés à la fin
du traitement de la requête. Les résultats non enregistrés disparaissent au rechargement de la page.
Les bilans enregistrés restent dans `data/talentmatch.sqlite3` jusqu'à leur suppression depuis l'historique.
Ils contiennent les extraits des documents, mais pas les fichiers originaux. La base locale n'est pas chiffrée
par l'application et est exclue de Git. `DATABASE_PATH` personnalise son emplacement.
Les exports sont téléchargés explicitement par l'utilisateur.

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

Le [guide d'architecture](docs/architecture.md) explique les couches, le parcours d'une analyse,
les échanges React/FastAPI, le calcul NLP et le traitement des données, avec des diagrammes.

```text
frontend-react/src/   React/JS : dashboard, formulaires, résultats, conseils et exports
frontend-react/dist/ Build de production Vite (généré, ignoré par Git)
frontend/reports.py   Exporteurs Python historiques conservés pour usages programmatiques
backend/main.py       FastAPI : contrats JSON et multipart, readiness, service du build React
backend/storage.py    SQLite : sauvegarde, liste, réouverture et suppression des bilans
backend/parsing.py    Lecture PDF/DOCX et nettoyage
backend/extraction.py spaCy EntityRuler, segmentation, durées et diplômes
backend/taxonomy.py   Dictionnaire bilingue, relations dirigées et ressources
backend/embeddings.py Sentence-Transformers / Hugging Face, modèle chargé une fois
backend/analysis.py   Similarités, matrice d'écarts et score composite
backend/recommendations.py  Conseils locaux + génération optionnelle
backend/schemas.py    Structures Pydantic typées et validées
tests/               Tests du pipeline, API, sécurité des exports et service du build React
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
uv run ruff check backend frontend tests run.py scripts
cd frontend-react
npm test
npm run lint
npm run build
```

Avec l'application en cours d'exécution, le parcours d'intégration HTTP peut être vérifié depuis la racine :

```powershell
uv run python scripts/smoke_react.py
uv run python scripts/benchmark.py
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
Le prototype fournit des comptes locaux et un historique isolé par utilisateur. Il ne constitue pas un déploiement public sécurisé.

La cible de 5 secondes concerne le pipeline à chaud, hors téléchargement du modèle et génération LLM.
Les durées de chaque analyse sont affichées. Ce n'est pas une garantie sur tout matériel ou document.

## Références techniques

- [FastAPI : fichiers et formulaires](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/)
- [spaCy : EntityRuler](https://spacy.io/api/entityruler)
- [Sentence-Transformers : encode et normalisation](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)
- [React : interface utilisateur](https://react.dev/learn)
- [Vite : compilation et développement](https://vite.dev/guide/)

## Comptes et réutilisation du projet de référence

Les pages Connexion et Inscription, leurs champs accessibles (affichage du mot de passe, erreurs), le contexte React et le module bcrypt/JWT ont été copiés depuis `prediction-prix-immobilier`, puis adaptés. Voir `docs/auth-reuse.md`.

Au premier lancement, créez votre propre compte sur `/inscription`. Les mots de passe sont hachés avec bcrypt. Les jetons expirent après 60 minutes. Les bilans sont filtrés par utilisateur sur le serveur. Les anciens bilans sans propriétaire restent conservés en base mais ne sont attribués automatiquement à aucun compte.
