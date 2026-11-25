export const demoCV = `Profil
Ingénieure data junior, 2 ans d'expérience professionnelle en analyse de données.
Compétences techniques
Python, SQL, Pandas, scikit-learn, Git, FastAPI.
Expériences professionnelles
Développement d'une API FastAPI pour servir un modèle de classification.
Analyse de données avec Python et Pandas et automatisation de rapports SQL.
Projets
Construction d'un modèle scikit-learn, validation croisée et suivi de la précision.
Formation
Diplôme d'ingénieur en informatique, spécialité data science.
Compétences
Travail en équipe, communication et rigueur.`;

export const demoJob = `Data Scientist — équipe produit
Nous recherchons un profil avec 3 ans d'expérience professionnelle et un Master en informatique.
Compétences techniques
Python et SQL sont obligatoires.
Maîtrise du Machine Learning et de scikit-learn.
Docker et AWS sont requis pour le déploiement.
FastAPI est un atout.
Compétences
Communication, travail en équipe et autonomie.`;

// All scenarios go through the same API/model as uploaded documents; no preset scores.
export const demoExamples = [
  { label: "Data junior", cv: demoCV, job: demoJob },
  { label: "Data confirmé", job: demoJob, cv: `Profil
Data scientist, 5 ans d'expérience professionnelle.
Compétences techniques
Python, SQL, Machine Learning, scikit-learn, Docker, AWS, FastAPI.
Expériences professionnelles
Déploiement de modèles de Machine Learning avec Docker et AWS.
Formation
Master informatique.
Compétences
Communication, travail en équipe et autonomie.` },
  { label: "Reconversion", job: demoJob, cv: `Profil
Début de carrière : 6 mois d'expérience professionnelle en analyse de données.
Compétences techniques
Python, Excel.
Expériences professionnelles
Préparation de tableaux Excel et scripts Python.
Formation
Licence informatique.
Compétences
Communication.` },
  { label: "Parcours daté", job: demoJob, cv: `Profil
Développeuse data et API.
Compétences techniques
Python, SQL, scikit-learn, Docker, FastAPI, Git.
Expériences professionnelles
Janvier 2021 - décembre 2022 : développement Python et SQL.
Janvier 2023 - décembre 2024 : API FastAPI et déploiement Docker.
Formation
Master informatique.
Compétences
Communication, travail en équipe.` },
];

export const criteria = [
  {
    key: "hard_skills",
    label: "Compétences techniques",
    short: "Technique",
    color: "lime",
    default: 50,
  },
  {
    key: "experience",
    label: "Expérience professionnelle",
    short: "Expérience",
    color: "orange",
    default: 25,
  },
  {
    key: "education",
    label: "Formation académique",
    short: "Formation",
    color: "purple",
    default: 15,
  },
  {
    key: "soft_skills",
    label: "Compétences transversales",
    short: "Soft skills",
    color: "blue",
    default: 10,
  },
];
export const defaultWeights = Object.fromEntries(
  criteria.map((c) => [c.key, c.default]),
);
