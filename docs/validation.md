# Validation du prototype React

Vérification locale : 4 novembre 2026.

- Backend : `uv run pytest -q` — 34 tests réussis. Une dépréciation tierce Starlette/httpx reste signalée.
- Frontend : `npm --prefix frontend-react test` — 14 tests réussis.
- Qualité : `uv run ruff check backend frontend tests scripts run.py` et `npm --prefix frontend-react run lint` réussis.
- Production : `npm --prefix frontend-react run build` réussi ; application servie par FastAPI sur http://127.0.0.1:8000.
- Test réel : `uv run python -X utf8 scripts/smoke_react.py` valide HTML, état du moteur, erreurs de validation, analyse texte et import PDF + DOCX. Score de démonstration : 67,7/100.
- Base SQLite : tests de création, relecture, pagination, validation, suppression et requêtes paramétrées. Dans le navigateur : enregistrement du bilan de démonstration, rechargement de la page, réouverture du même bilan et du même score.
- Interface : les huit routes gardent un document de 1280 × 720, sans débordement horizontal ni défilement externe. Le tableau de bord et le formulaire d'import tiennent intégralement dans cette fenêtre. Les rapports longs défilent dans le panneau central ; la navigation reste visible.
- Tableau de bord : aucun des cinq panneaux ne dépasse sa hauteur disponible à 1280 × 720.
- Responsive : formulaire à 320 px sans débordement horizontal ; navigation mobile masquée du lecteur d'écran lorsqu'elle est fermée. Gestion clavier du menu couverte par les tests React.
- Architecture vérifiée à 1440 × 900 : chaîne React → FastAPI → NLP → bilan → SQLite et explication des responsabilités.
- Captures locales : `output/react-dashboard.png` et `output/react-analysis.png`.

## Périmètre et limites

React remplace Streamlit à la demande de l'utilisateur. SQLite ajoute un historique explicite au cahier des charges initial. Les analyses non enregistrées restent transitoires. Les originaux PDF/DOCX ne sont pas sauvegardés dans la base ; les bilans contiennent des extraits et ne sont pas chiffrés.

Le modèle MiniLM réel a été exécuté. Le service LLM optionnel n'est pas installé dans cet environnement : son repli local et ses contrats sont testés, mais aucune génération avec un véritable serveur LLM n'est revendiquée. Le prototype est destiné à une utilisation locale, sans comptes utilisateurs ni déploiement public. Les PDF scannés nécessitent un OCR non inclus.

Le fichier personnel non suivi `build_cv_project.py` reste hors du périmètre de cette migration ; ses avertissements de lint préexistants n'ont pas été modifiés.
