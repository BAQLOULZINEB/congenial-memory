# Réutilisation de l’authentification

Source locale : `C:/Users/zineb/Documents/dev ai tps/prediction-prix-immobilier`.

| Source copiée | Destination adaptée |
|---|---|
| frontend-react/src/pages/Connexion.jsx | frontend-react/src/auth/pages/Connexion.jsx |
| frontend-react/src/pages/Inscription.jsx | frontend-react/src/auth/pages/Inscription.jsx |
| frontend-react/src/components/CadreAuth.jsx | frontend-react/src/auth/components/CadreAuth.jsx |
| frontend-react/src/context/AuthContext.jsx | frontend-react/src/auth/context/AuthContext.jsx |
| api/auth.py | backend/auth.py |
| Routes /auth de api/main.py | backend/auth_routes.py |
| Schéma utilisateurs et relation propriétaire de db/schema.sql | backend/storage.py |

Le projet source utilise PostgreSQL. Talent Match conserve SQLite, déjà intégrée au prototype : paramètres SQL `?`, clé entière auto-incrémentée et dates SQLite. Aucun identifiant ni fichier .env du projet source n’a été copié. Aucun serveur PostgreSQL supplémentaire n’est nécessaire.

## Parcours

Inscription → bcrypt → table utilisateurs → connexion → JWT HS256 de 60 minutes → interface React.

Chaque enregistrement reçoit l’identifiant issu du jeton vérifié. Toutes les lectures et suppressions de bilans filtrent aussi ce propriétaire. Connaître un UUID ne donne pas accès à un autre bilan (réponse 404). Une session absente, invalide ou expirée renvoie 401. L’interface retourne à la connexion lorsque la session est refusée.

La clé JWT aléatoire est générée localement dans un fichier `.jwt-key` près de la base, exclu de Git. Les mots de passe de plus de 72 octets sont refusés sans troncature. Le navigateur conserve le jeton dans localStorage, comme la source. La déconnexion efface ce jeton du navigateur ; elle ne révoque pas une copie déjà extraite avant son expiration.

## Migration non destructive

Ajout de la table utilisateurs et de la colonne nullable analyses.utilisateur_id. Les bilans historiques sans propriétaire restent présents, mais sont invisibles aux comptes nouvellement créés. Aucune attribution silencieuse au premier inscrit. Une reprise de ces données doit être décidée séparément.

## Limites de livraison

Prototype sur localhost : pas de vérification email, de récupération de mot de passe, de limitation anti-abus distribuée ni de durcissement de déploiement public. Les endpoints d’analyse transitoire restent utilisables sans compte ; l’historique est protégé. Le fichier SQLite n’est pas chiffré. Ne pas exposer ce serveur tel quel sur Internet.
