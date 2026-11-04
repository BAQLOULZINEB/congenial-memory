# Talent Match — ouverture, lancement et compte de test

## Chemin du projet

```text
C:\Users\zineb\OneDrive\Documents\ChatGPT\AI GENRATIVE TEXTUEL
```

## Ouvrir dans VS Code et lancer tout (PowerShell)

```powershell
cd "C:\Users\zineb\OneDrive\Documents\ChatGPT\AI GENRATIVE TEXTUEL"
code .
uv sync --frozen
uv run python run.py
```

Le lanceur installe les dépendances React avec npm, compile l’interface, démarre FastAPI sur le port 8000 et ouvre le navigateur. SQLite est initialisée automatiquement : aucune commande de base de données séparée. Node.js/npm et uv doivent être disponibles (déjà présents sur ce poste).

URL : http://127.0.0.1:8000/connexion

L’application tourne déjà si cette URL répond ; il n’est alors pas nécessaire de lancer un deuxième serveur. `Ctrl+C` dans le terminal du serveur permet de l’arrêter.

Relancer sans recompiler si les sources React n’ont pas changé :

```powershell
uv run python run.py --skip-build
```

## Compte local déjà testé

- Nom : Prototype QA
- Email : `prototype.qa.1104@example.test`
- Mot de passe : `Prototype-QA-42!`
- Vérifié le 4 novembre 2026 : connexion API HTTP 200.

Ce compte de démonstration existe dans la base locale `data/talentmatch.sqlite3`. Il n’est pas créé automatiquement sur une nouvelle installation. Pour votre propre espace, utilisez « Créer un compte ».

## Commandes de vérification

```powershell
uv run pytest -q
npm --prefix frontend-react test
npm --prefix frontend-react run lint
npm --prefix frontend-react run build
```

## Modification visuelle minimale

Le français, la disposition et le fonctionnement des formulaires restent inchangés. Seuls un fichier CSS de surcharge et son import ont été ajoutés. Le bouton reste désactivé lorsque les champs sont vides, tout en gardant sa couleur citron ; le curseur et l’attribut disabled restent actifs. Les états hover/focus des boutons viennent du style partagé `.button`.

Sources : `frontend-react/src/login-theme.css` et l’import final de `frontend-react/src/main.jsx`.

```jsx
import "./login-theme.css";
```

Code CSS complet :

```css
/* Reuse the dashboard surfaces and tokens; keep the auth layout unchanged. */
.auth-page {
  background: linear-gradient(130deg, #1b1b27, #101018 75%);
}
.auth-frame {
  background: linear-gradient(130deg, #1b1b27, #101018 75%);
  border-color: var(--line);
}
.auth-art {
  background: var(--purple);
  color: #2b203b;
  border-radius: var(--radius);
}
.auth-art-type em,
.auth-art > p,
.auth-paper,
.auth-art-footer {
  color: #2b203b;
}
.auth-art-footer {
  border-top: 0;
}
.auth-input {
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid var(--line);
  border-radius: 12px;
  color: var(--text);
}
.auth-input:focus {
  border-color: var(--purple);
  box-shadow: none;
  outline: 3px solid var(--purple);
  outline-offset: 4px;
}
.auth-label,
.auth-page .brand-lockup {
  color: var(--text);
}
.auth-link,
.auth-page .brand-lockup > svg {
  color: var(--purple);
}
.auth-submit {
  background: var(--lime);
  color: #252b18;
}
.auth-submit:disabled {
  opacity: 1;
  cursor: not-allowed;
}
.auth-footnote,
.auth-help {
  font-size: 12px;
  color: var(--text-caption);
}
.auth-art-footer {
  font-size: 12px;
}
```
