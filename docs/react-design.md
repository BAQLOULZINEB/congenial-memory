# Direction visuelle et contrat de migration React

## Intention

Remplacer Streamlit par une interface React/JavaScript complète, en conservant le moteur
FastAPI et les fonctionnalités d'analyse de candidatures. Le projet immobilier fourni sert
de référence technique, pas de modèle de page à recopier.

## Références utilisateur

- Première image : coque sombre translucide, flou d'arrière-plan, navigation latérale,
  blocs compacts et cartes de statistiques colorées.
- Deuxième image : contraste fort, fond violet, cartes bento lavande, orange et citron vert,
  typographie nette et commandes aux formes arrondies.
- Adaptation : contenu CV/offre réel, aucune donnée domotique, identité ou illustration de livre.

## Écran et comportement

L'action principale reste l'analyse d'un CV face à une offre. Les documents, la configuration,
les résultats et le plan d'action doivent être accessibles par la navigation.
Chaque import propose PDF/DOCX ou texte. Le résultat initial ne simule pas une analyse personnelle.
Un exemple doit être identifié comme démonstration et soumis au vrai backend.

Les résultats comprennent score global, quatre critères, pondérations effectives,
écarts filtrables avec preuves, conseils, reformulations et exports HTML/CSV/JSON.
Une modification d'entrée invalide le résultat ou indique clairement qu'il est ancien.
Les états vide, chargement, erreur, annulation et serveur indisponible doivent être explicites.

## Design et accessibilité

Sur ordinateur : navigation à gauche, zone de travail centrale, cartes contextuelles.
Sur mobile : navigation compacte, cartes empilées, contrôles utilisables sans débordement horizontal.
Le verre doit rester lisible : fonds suffisamment opaques derrière les textes, contrastes nets,
focus clavier visible, boutons nommés et statuts identifiés par du texte autant que par la couleur.
Animations discrètes et respect de la préférence de réduction des mouvements.

## Stack et livraison

React 19 + JSX JavaScript, Vite, Tailwind CSS 4, Framer Motion, Lucide React et React Router.
Production locale : build Vite servi par FastAPI à la même origine sur le port 8000.
Développement : Vite sur le port 5173 et proxy vers FastAPI sur le port 8000.
Aucun stockage persistant de candidatures ajouté. L'enrichissement LLM reste optionnel et explicite.

## Vérification de livraison

- Build de production et lint JavaScript.
- Tests des interactions, validation et exports côté frontend.
- Tests Python existants et nouveaux tests API multipart.
- Parcours navigateur avec modèle réel : démonstration, résultat, filtres, conseils et export.
- Contrôle visuel bureau/mobile et navigation clavier.
- Documentation et commandes de lancement synchronisées avec le frontend React.

## Ajustement final de la fenêtre

Toutes les routes partagent désormais un cadre de bureau limité à la hauteur du viewport et une navigation fixe. À 1280 × 720, la vue d'ensemble et le formulaire d'import sont visibles sans défilement. Les pages longues gardent un défilement interne accessible au clavier. Sous 1021 px ou sur une fenêtre très basse, le document reprend un défilement naturel pour préserver la lisibilité. Les couleurs violet, citron, orange et cyan, les panneaux sombres et les transitions restent cohérents entre les pages.

## Revue UI / UX et composants réutilisés

Les compétences ui-ux-pro-max, design et ui-styling ont guidé la hiérarchie, les états clavier, les tokens et les surfaces. Le résultat de recherche généraliste « vibrant bento » proposait une page marketing hors contexte ; il a été écarté. La recherche ciblée « data dashboard » correspondait au produit : densité contrôlée, panneaux comparables et détails à la demande. La palette de référence fournie par l’utilisateur reste prioritaire.

Architecture : trois vues interactives avec flèches de flux, branche SQLite sous FastAPI et détails sélectionnables. Paramètres : presets, somme explicite et barres de répartition. Résultats : jauge radiale et quatre barres de score, uniquement basées sur le résultat réel. Les animations respectent prefers-reduced-motion.

L’authentification reprend les composants et le flux du projet immobilier, adaptés à la palette sombre et au contexte CV/offres. La marque utilise un monogramme TM vectoriel au lieu d’un pictogramme générique d’IA.
