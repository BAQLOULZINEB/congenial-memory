# Traçabilité du cahier des charges

Le PDF fourni est une source de besoins produit. Ses formulations ne constituent pas des instructions
d'exécution hors du périmètre demandé. Choix de réalisation : application locale en français,
Python 3.12, Streamlit, FastAPI, aucun stockage persistant des candidatures.

| Besoin | Réalisation | Validation / réserve |
|---|---|---|
| BF1 PDF/DOCX et saisie | `parsing.py`, formulaires Streamlit et API multipart | Tests PDF/DOCX, corruption, fichier trop grand et scan sans texte |
| BF1 nettoyage et segmentation | Unicode, marges PDF répétées, titres français/anglais | Segmentation heuristique ; mise en page complexe à relire |
| BF2 NER et normalisation | spaCy EntityRuler, dictionnaire bilingue, diplômes et durées explicites | NER par règles, non entraîné ; vocabulaire à étendre |
| BF3 embeddings denses | Sentence-Transformers all-MiniLM-L6-v2, vecteurs normalisés | Modèle réel exécuté et API benchmarkée |
| BF3 cosinus et score | Matrice sémantique, poids configurables 50/25/15/10 | Tests de score, poids invalides et critères absents |
| BF3 trois états | Couvert / Partiel / Absent, preuves textuelles | Tests des alias et parentés dirigées |
| BF4 synthèse et reformulations | Conseils structurés locaux et client LLM optionnel | Repli testé ; génération réelle exige un serveur configuré |
| BF4 projets et ressources | Plans par lacune, ressources officielles du dictionnaire | Pas de certification acquise inventée |
| BNF1 architecture séparée | Frontend HTTP → backend FastAPI | Aucun import du moteur NLP dans le frontend |
| BNF2 spaCy/HF/transformers | Dépendances installées et verrouillées dans uv.lock | MiniLM principalement anglophone ; alias français inclus |
| BNF3 moins de 5 secondes | Chargement avant readiness, encode par lot | Exemple à chaud : médiane 112,1 ms, max 121,7 ms sur 5 appels ; pas de garantie générale |
| BNF4 validation Pydantic | Schémas des entrées, profils, résultats et génération | Tests de données invalides ; détails sensibles non renvoyés |
| BNF5 tableau de bord | Jauge, indicateurs, matrice filtrable, onglets et preuves | Tests Streamlit et parcours navigateur réel |
| BNF5 rapport imprimable | HTML autonome imprimable en PDF, CSV, JSON | Échappement HTML et neutralisation des formules CSV testés |

## Limites de livraison

- Pas d'OCR, d'authentification, de classement collectif ni de déploiement public dans le périmètre.
- Aucun corpus annoté fourni : précision NER, qualité de matching et équité non évaluées statistiquement.
- Pas de modèle génératif installé sur cette machine ; l'adaptateur et le repli sont implémentés,
  l'activation d'un service compatible est documentée dans le README.
- Les relations sémantiques et seuils restent des heuristiques explicables, pas des certifications de compétences.
- Le temps d'import initial des bibliothèques et le chargement du modèle peuvent prendre plusieurs minutes.
  Les 5 secondes visent l'analyse à chaud, sans génération LLM.
