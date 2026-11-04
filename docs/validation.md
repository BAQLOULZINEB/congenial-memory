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

Le modèle MiniLM réel a été exécuté. Le service LLM optionnel n'est pas installé dans cet environnement : son repli local et ses contrats sont testés, mais aucune génération avec un véritable serveur LLM n'est revendiquée. Le prototype est destiné à une utilisation locale, avec comptes locaux, sans déploiement public. Les PDF scannés nécessitent un OCR non inclus.

Le fichier personnel non suivi `build_cv_project.py` reste hors du périmètre de cette migration ; ses avertissements de lint préexistants n'ont pas été modifiés.

## Revue finale : comptes, diagrammes et graphiques

- Authentification réutilisée depuis le projet immobilier (détail dans auth-reuse.md) : inscription, connexion, persistance de session, déconnexion, bcrypt et JWT.
- 37 tests backend réussis, dont isolation de deux comptes, mot de passe erroné, doublon email, session expirée, limite bcrypt UTF-8 et conservation des anciens bilans. Les six tests auth/stockage ont été rejoués après la dernière modification backend.
- 17 tests React réussis, dont sélection des diagrammes, presets de pondération, total invalide et valeur accessible de la jauge.
- Parcours navigateur : création d’un compte synthétique, analyse réelle à 67,7, sauvegarde du bilan et historique retrouvé après redémarrage du serveur.
- Les trois diagrammes Système, Pipeline NLP et Données/API fonctionnent. La vue système complète tient dans 1280 × 720 ; les détails changent à la sélection d’un composant.
- Settings et architecture à 375 px : aucune largeur de document supérieure à la largeur disponible.
- Jauge et barres utilisent les scores calculés. Aucun score fictif n’est affiché avant une analyse ; un critère non exigé reste sans barre.
- Logo monogramme SVG, favicon assortie, titres plus directs, texte courant de 13–14 px dans les panneaux compacts et surfaces vitrées cohérentes.
- Le lancement final conserve les données existantes. Les anciens rapports sans propriétaire ne deviennent pas accessibles aux nouveaux comptes.
- Connexion et déconnexion explicites vérifiées dans le navigateur après inscription. Session reconnue après redémarrage serveur. La page de connexion à 375 px n’a aucun débordement horizontal.
