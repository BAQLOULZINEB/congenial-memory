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
