# Correctifs ciblés du 11 novembre 2026

- Expérience : durées en années/mois et périodes datées dans une rubrique
  d'expérience reconnue. Formats numériques, mois français/anglais, années et
  poste en cours. Les intervalles qui se chevauchent sont fusionnés. Une durée
  explicitement déclarée reste prioritaire ; les années seules utilisent la
  différence entre années et les mois précis incluent le mois de fin. Les dates
  de formation et de publication d'offres ne deviennent pas de l'expérience.
  Cela reste une estimation : une rubrique non reconnue ou une mise en page
  complexe peut demander une vérification. Les durées de plusieurs postes sans
  dates ne sont pas additionnées, car leurs chevauchements sont inconnus.
- Nouvelle analyse : le bouton d'exemple parcourt quatre paires de documents
  synthétiques, puis revient à la première. Les calculs passent par la même API
  que les vrais CV ; aucun score n'est codé dans les exemples. Les poids actuels
  restent inchangés pour permettre une comparaison à configuration constante.
- Session : le dernier bilan, sa provenance et son identifiant d'enregistrement
  sont restaurés après actualisation dans le même onglet et pour le même compte.
  Ce cache sessionStorage est effacé à la déconnexion ou à l'expiration détectée.
  Les fichiers et brouillons ne sont pas restaurés. L'historique SQLite conserve
  son enregistrement explicite ; aucune sauvegarde durable automatique n'est ajoutée.
  Un message signale l'impossibilité de conserver le bilan si le stockage est indisponible.

Les règles de score et les modèles sont inchangés. La variation des scores de
démonstration illustre la réaction aux entrées, pas une mesure de précision sur
un corpus annoté. Le compte rendu du 4 novembre décrit l'état antérieur à ces correctifs.
