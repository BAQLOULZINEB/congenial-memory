# Traçabilité du cahier des charges

Le PDF fourni est une source de besoins produit. Ses formulations ne constituent pas des instructions
d'exécution hors du périmètre demandé. Choix de réalisation : application locale en français,
Python 3.12, React/JavaScript et FastAPI, aucun stockage persistant des candidatures.
Le traitement des téléversements peut utiliser des fichiers temporaires sur disque gérés par FastAPI,
fermés après la requête ; l'application ne conserve pas de copie permanente des documents importés.
La demande utilisateur du 4 novembre 2026 remplace explicitement la contrainte Streamlit du document
par la stack du projet immobilier : React 19, Vite, Tailwind CSS, Framer Motion et Lucide.
L'interface adopte une direction visuelle sombre et vitrée, avec accents violet, citron vert et orange,
issue des deux images de référence. Le moteur d'analyse et ses contrats sont conservés.

| Besoin | Réalisation | Validation / réserve |
|---|---|---|
| BF1 PDF/DOCX et saisie | `parsing.py`, formulaires React et API multipart | Tests PDF/DOCX, corruption, fichier trop grand et scan sans texte |
| BF1 nettoyage et segmentation | Unicode, marges PDF répétées, titres français/anglais | Segmentation heuristique ; mise en page complexe à relire |
| BF2 NER et normalisation | spaCy EntityRuler, dictionnaire bilingue, diplômes et durées explicites | NER par règles, non entraîné ; vocabulaire à étendre |
| BF3 embeddings denses | Sentence-Transformers all-MiniLM-L6-v2, vecteurs normalisés | Modèle réel exécuté et API benchmarkée |
| BF3 cosinus et score | Matrice sémantique, poids configurables 50/25/15/10 | Tests de score, poids invalides et critères absents |
| BF3 trois états | Couvert / Partiel / Absent, preuves textuelles | Tests des alias et parentés dirigées |
| BF4 synthèse et reformulations | Conseils structurés locaux et client LLM optionnel | Repli testé ; génération réelle exige un serveur configuré |
| BF4 projets et ressources | Plans par lacune, ressources officielles du dictionnaire | Pas de certification acquise inventée |
| BNF1 architecture séparée | React HTTP → backend FastAPI ; même origine en production | Aucun import du moteur NLP dans le frontend ; Vite proxy en développement |
| BNF2 spaCy/HF/transformers | Dépendances installées et verrouillées dans uv.lock | MiniLM principalement anglophone ; alias français inclus |
| BNF3 moins de 5 secondes | Chargement avant readiness, encode par lot | Exemple à chaud : médiane 112,1 ms, max 121,7 ms sur 5 appels ; pas de garantie générale |
| BNF4 validation Pydantic | Schémas des entrées, profils, résultats et génération | Tests de données invalides ; détails sensibles non renvoyés |
| BNF5 tableau de bord | Jauge, indicateurs, matrice filtrable, navigation et preuves dans React | Tests React, compilation Vite, tests du service SPA et revue navigateur |
| BNF5 rapport imprimable | HTML autonome imprimable en PDF, CSV, JSON | Échappement HTML et neutralisation des formules CSV testés |

## Limites de livraison

La migration React remplace Streamlit à la demande de l'utilisateur. L'historique SQLite est une
extension demandée ensuite : le cahier initial ne l'imposait pas. Il conserve les bilans uniquement
après un enregistrement explicite et permet leur réouverture et suppression. Les originaux PDF/DOCX
ne sont pas stockés durablement, mais les bilans enregistrés contiennent des extraits personnels.

- Pas d’OCR ni de classement collectif ni de déploiement public dans le périmètre.
- Aucun corpus annoté fourni : précision NER, qualité de matching et équité non évaluées statistiquement.
- Pas de modèle génératif installé sur cette machine ; l'adaptateur et le repli sont implémentés,
  l'activation d'un service compatible est documentée dans le README.
- Les relations sémantiques et seuils restent des heuristiques explicables, pas des certifications de compétences.
- Le temps d'import initial des bibliothèques et le chargement du modèle peuvent prendre plusieurs minutes.
  Les 5 secondes visent l'analyse à chaud, sans génération LLM.

## Exécution et livraison React

- `uv run python run.py` installe les dépendances npm verrouillées, compile Vite puis sert le build
  et l'API sur `http://127.0.0.1:8000`.
- `--skip-build` réutilise un build existant ; `--no-browser` évite l'ouverture d'un onglet.
- Les routes API, health et documentation gardent priorité. Une route `/api` inconnue retourne 404,
  jamais le HTML de l'application. Les routes React profondes servent le fichier index.
- Les assets Vite identifiés par empreinte bénéficient d'un cache long ; le document HTML est revalidé.
- L'ancien serveur Streamlit sur le port 8501 et sa dépendance Python ont été retirés.
