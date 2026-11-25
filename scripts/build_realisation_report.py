"""Build the French implementation report from verified project facts and app captures."""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
 Flowable,
 Image,
 PageBreak,
 Paragraph,
 SimpleDocTemplate,
 Spacer,
 Table,
 TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('Body', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold', italic='Body', boldItalic='Bold')
NAVY = colors.HexColor('#153b65')
CYAN = colors.HexColor('#00a6c4')
INK = colors.HexColor('#243344')
styles = {
 'body': ParagraphStyle('body', fontName='Body', fontSize=10.3, leading=15.6, textColor=INK, spaceAfter=9),
 'h1': ParagraphStyle('h1', fontName='Bold', fontSize=22, leading=27, textColor=NAVY, spaceAfter=19),
 'h2': ParagraphStyle('h2', fontName='Bold', fontSize=12.5, leading=17, textColor=NAVY, spaceBefore=9, spaceAfter=8),
 'small': ParagraphStyle('small', fontName='Body', fontSize=8.5, leading=12, textColor=INK, spaceAfter=7),
 'caption': ParagraphStyle('caption', fontName='Body', fontSize=9, leading=13, textColor=NAVY, spaceBefore=7, spaceAfter=14),
 'cell': ParagraphStyle('cell', fontName='Body', fontSize=9, leading=13, textColor=INK),
 'code': ParagraphStyle('code', fontName='Body', fontSize=9, leading=14, backColor=colors.HexColor('#f1f5f9'), borderPadding=9, spaceAfter=12),
}
story=[]
source=[]
sections=[]

def p(text, kind='body'):
 story.append(Paragraph(text,styles[kind]));source.append(text.replace('<b>','').replace('</b>','').replace('<br/>','\n'))

def page(title):
 if story: story.append(PageBreak())
 sections.append(title);p(title,'h1'); source.append('')

def sub(title): p(title,'h2')

def table(headers, rows, widths):
 data=[[Paragraph(escape(str(c)),styles['cell']) for c in row] for row in [headers]+rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3eef6')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),1,CYAN),('LINEBELOW',(0,1),(-1,-1),0.4,colors.HexColor('#dce3ea'))]))
 story.append(t);story.append(Spacer(1,12))
 source.append(' | '.join(headers));source.extend(' | '.join(map(str,r)) for r in rows)

def shot(name,caption):
 path=ROOT/'output'/name
 w,h=ImageReader(str(path)).getSize()
 story.append(Image(str(path),width=487,height=487*h/w))
 p(caption,'caption');source.append(f'![{caption}](../{name})')

class Diagram(Flowable):
 def __init__(self,kind):
  super().__init__();self.width=487;self.height=235;self.kind=kind
 def draw(self):
  c=self.canv
  def box(x,y,w,h,title,lines):
   c.setFillColor(colors.HexColor('#eef3fa'));c.setStrokeColor(colors.HexColor('#b4c8df'));c.roundRect(x,y,w,h,8,fill=1)
   c.setFillColor(NAVY);c.setFont('Bold',10);c.drawString(x+10,y+h-20,title)
   c.setFont('Body',8.8)
   for i,line in enumerate(lines):c.drawString(x+10,y+h-39-i*14,line)
  def arrow(x,y,x2,y2,label=''):
   c.setStrokeColor(CYAN);c.setLineWidth(1.3);c.line(x,y,x2,y2)
   if x2>x:c.line(x2,y2,x2-5,y2+3);c.line(x2,y2,x2-5,y2-3)
   elif y2<y:c.line(x2,y2,x2-3,y2+5);c.line(x2,y2,x2+3,y2+5)
   c.setFillColor(INK);c.setFont('Body',8);c.drawString(min(x,x2)+4,max(y,y2)+6,label)
  if self.kind=='system':
   box(0,145,135,80,'Interface React',['Saisie / navigation','Résultats / exports']);box(176,145,135,80,'API FastAPI',['Validation Pydantic','JWT / orchestration']);box(352,145,135,80,'Pipeline NLP',['spaCy + MiniLM','Score + conseils'])
   arrow(135,180,176,180,'HTTP');arrow(311,180,352,180,'appel')
   box(176,15,135,80,'SQLite',['Comptes locaux','Bilans enregistrés']);arrow(243,145,243,95,'SQL')
   c.setFont('Body',9);c.setFillColor(INK);c.drawString(0,119,'Réponse : JSON validé, puis restitution dans React.')
  else:
   box(0,60,205,160,'utilisateurs',['PK  id : INTEGER','nom : TEXT','email : TEXT UNIQUE','mot_de_passe_hash : TEXT','cree_le : TEXT'])
   box(278,15,209,205,'analyses',['PK  id : TEXT (UUID)','FK  utilisateur_id : INTEGER','title / created_at : TEXT','score : REAL [0,100]','is_demo : INTEGER','payload : TEXT (JSON)','Index : propriétaire + date'])
   arrow(205,135,278,135,'1 → N')
   c.setFont('Body',8.5);c.setFillColor(INK);c.drawString(0,29,'Les anciens bilans sans propriétaire restent isolés.')

def footer(c,doc):
 c.saveState();c.setStrokeColor(CYAN);c.line(54,791,541,791)
 c.setFont('Body',8);c.setFillColor(NAVY);c.drawString(54,805,'TALENT MATCH  |  COMPTE RENDU DE RÉALISATION')
 c.setFont('Body',8);c.drawString(54,31,'EMSI · 5AISDR · G8  |  Année universitaire 2026-2027')
 c.drawRightString(541,31,str(doc.page+1));c.restoreState()

page('Résumé et organisation du rapport')
p('Talent Match est un prototype local d’analyse de CV et d’offres d’emploi. Il transforme deux documents en un bilan lisible : compétences couvertes, écarts, score d’adéquation et pistes de progression. La réalisation associe une interface React en français, une API FastAPI, un pipeline NLP explicable et une base SQLite pour les comptes et les bilans enregistrés.')
p('Ce compte rendu décrit la version réalisée et vérifiée le <b>4 novembre 2026</b>. Il complète le cahier des charges initial : React remplace Streamlit à la demande du commanditaire ; l’authentification et l’historique constituent des extensions. Les captures proviennent du prototype exécuté localement avec des documents et un compte de démonstration.')
table(['Partie','Page'],[(t,str(n)) for t,n in [('1. Objectifs et conformité',3),('2. Architecture du système',4),('3. Extraction documentaire et NLP',5),('4. Calcul du score et interprétation',6),('5. Base de données et persistance',7),('6. Authentification et connexion',8),('7. Tableau de bord et identité visuelle',9),('8. Saisie et lancement d’une analyse',10),('9. Résultats et étude de cas',11),('10. Recommandations et exports',12),('11. Configuration et architecture interactive',13),('12. Historique et cycle de vie des données',14),('13. API et organisation du code',15),('14. Validation et résultats des tests',16),('15. Installation et démonstration',17),('16. Bilan, limites et perspectives',18)]],[421,66])

page('1. Objectifs et conformité')
sub('Du besoin à la solution')
p('La lecture manuelle d’un CV face à une offre demande de repérer des termes équivalents, de vérifier les exigences et de justifier les écarts. L’objectif du projet est d’aider cette lecture, sans automatiser une décision d’embauche. Le candidat peut repérer les éléments à mieux présenter ; un lecteur peut vérifier les preuves qui accompagnent les résultats.')
table(['Besoin initial','Réalisation et état'],[
 ('Ingestion PDF/DOCX et texte','Import de fichiers textuels ou saisie directe ; validation des tailles et des contenus.'),
 ('Extraction et normalisation','Nettoyage Unicode, sections heuristiques, spaCy EntityRuler et dictionnaire d’alias.'),
 ('Appariement sémantique','Embeddings MiniLM normalisés, similarité cosinus et relations dirigées entre compétences.'),
 ('Score et trois états','Score pondéré, états Couvert / Partiel / Absent, preuves et avertissements.'),
 ('Recommandations','Conseils locaux opérationnels ; adaptateur LLM facultatif avec repli en cas d’erreur.'),
 ('Restitution et rapport','Tableau de bord, jauge, barres, matrice et exports HTML imprimable, CSV et JSON.'),
 ('Évolutions demandées','React à la place de Streamlit ; comptes locaux, JWT et historique SQLite.')],[155,332])
sub('Périmètre de réalisation')
p('Le prototype traite une paire CV/offre à la fois. Il ne propose ni classement collectif de candidats, ni OCR des documents scannés, ni évaluation scientifique de l’équité. Les critères sont fondés sur les informations reconnues dans les documents ; une absence de preuve détectée ne prouve pas une absence réelle de compétence.')
p('Le cahier des charges fixe la finalité du système. Les changements de technologie et les extensions sont présentés ici explicitement pour conserver la traçabilité des choix, sans confondre spécification initiale et réalisation finale.')

page('2. Architecture du système')
story.append(Diagram('system'))
p('Figure 1. Architecture logique du prototype local. Le stockage est accessible par l’API ; le navigateur et le moteur NLP ne manipulent pas directement la base.','caption')
sub('Séparation des responsabilités')
p('<b>React</b> gère la saisie, les états de chargement, la navigation et l’affichage. <b>FastAPI</b> valide les requêtes, appelle le pipeline et contrôle l’accès à l’historique. Le <b>moteur Python</b> extrait les informations et calcule le bilan. <b>SQLite</b> conserve les comptes et uniquement les analyses que l’utilisateur choisit d’enregistrer.')
sub('Déroulement d’une requête')
p('1. Le client prépare les textes ou fichiers et convertit les poids en fractions.<br/>2. L’API contrôle les données avec Pydantic et extrait les contenus.<br/>3. Le pipeline nettoie, reconnaît les entités, vectorise et compare les compétences.<br/>4. Le calcul produit sous-scores, score global, preuves et conseils.<br/>5. Le JSON validé revient dans l’interface. Un enregistrement distinct écrit le bilan dans SQLite.')
sub('Déploiement local')
p('En mode compilé, FastAPI sert aussi le build Vite : interface et API partagent l’origine http://127.0.0.1:8000. En développement, Vite utilise le port 5173 et relaie les appels API vers le port 8000. Le modèle est chargé avant que le service annonce sa disponibilité.')

page('3. Extraction documentaire et NLP')
sub('Ingestion et contrôles')
p('Pour chacun des deux documents, l’utilisateur choisit un fichier ou un texte. PyMuPDF lit les PDF textuels ; python-docx extrait les paragraphes des fichiers DOCX. La configuration limite chaque fichier à 5 Mio et chaque texte à 30 000 caractères ; l’interface rappelle aussi la limite de 30 pages pour les PDF. Les fichiers illisibles ou sans texte exploitable déclenchent une erreur explicite.')
sub('Nettoyage et segmentation')
p('Le nettoyage harmonise les caractères et espaces. Les marges répétées des PDF sont traitées pour limiter le bruit. La segmentation recherche des titres de sections français ou anglais : profil, compétences, expériences, formation et projets. Cette méthode reste heuristique : des colonnes complexes, des titres atypiques ou des scans peuvent nécessiter une correction manuelle.')
sub('Reconnaissance des compétences')
p('Le composant EntityRuler de spaCy utilise un dictionnaire de compétences et d’alias. Une variante connue est normalisée vers un nom canonique : par exemple, « sklearn » devient « scikit-learn ». Chaque entité conserve un extrait justificatif. Les durées explicites et les niveaux académiques sont également repérés ; les périodes calendaires ne sont pas cumulées automatiquement.')
sub('Comparaison sémantique')
p('Sentence-Transformers charge <b>all-MiniLM-L6-v2</b>. Les noms de compétences et leurs extraits sont encodés par lot. Les vecteurs normalisés permettent de calculer le cosinus par produit scalaire. Une compétence exactement reconnue est traitée avant toute proximité sémantique, afin de privilégier les preuves explicites.')
p('Un rapprochement partiel exige une relation connue du dictionnaire, ou une similarité d’au moins 0,60 dans le même domaine technique. Une relation connue impose un coefficient minimal de 0,60. Cette règle explique pourquoi une compétence connexe peut apporter un crédit limité, sans être déclarée acquise.')
sub('Ce que le modèle fait réellement')
p('MiniLM produit des représentations numériques ; il ne rédige pas de conseils. Le système n’entraîne pas un nouveau modèle sur les CV. Le NER est fondé sur des règles, et le modèle d’embeddings est préentraîné. Les compétences absentes du dictionnaire peuvent donc être ignorées.')

page('4. Calcul du score et interprétation')
table(['État','Justification','Crédit'],[
 ('Couvert','Même compétence canonique reconnue dans le CV.','100'),
 ('Partiel','Preuve connexe admise par les règles de rapprochement.','50 × similarité'),
 ('Absent','Aucune preuve reconnue pour cette exigence.','0')],[76,302,109])
p('Les compétences obligatoires ont un coefficient de 1 ; les compétences souhaitables comptent pour 0,5. Le sous-score technique, comme le sous-score transversal, est la moyenne de ces crédits pondérés par l’importance des exigences.')
sub('Expérience et formation')
p('Pour une exigence reconnue, le sous-score vaut 100 × min(valeur du CV / valeur attendue, 1). L’expérience utilise les années déclarées explicitement. La formation utilise un niveau académique ordinal ; elle ne certifie ni l’équivalence du diplôme ni l’adéquation de la spécialité. Si le CV ne fournit pas de preuve reconnue pour une exigence présente, le sous-score vaut zéro.')
sub('Pondération et critères absents')
p('<b>Score = 0,50 × technique + 0,25 × expérience + 0,15 × formation + 0,10 × transversal</b>','code')
p('Cette formule correspond au profil Technique par défaut. Les paramètres permettent d’autres répartitions dont la somme doit être 100 %. Lorsqu’un critère n’est pas exigé dans l’offre, son sous-score est nul au sens « non applicable » (valeur JSON null), et son poids est exclu. Les poids des autres critères sont renormalisés : poids effectif = poids demandé / somme des poids applicables.')
sub('Exemple de lecture')
p('La démonstration donne environ 58,8 en technique, 66,7 en expérience, 100 en formation et 66,7 en transversal. Avec la pondération par défaut, le score final arrondi est <b>67,7/100</b>. Le calcul interne utilise les valeurs non réduites à une décimale ; les arrondis affichés peuvent expliquer de petits écarts de recalcul manuel.')
p('Ce score mesure une adéquation documentaire selon les règles du prototype. Il ne représente ni une probabilité d’embauche, ni une note universelle du candidat, ni une validation de ses compétences réelles.')

page('5. Base de données et persistance')
story.append(Diagram('db'))
p('Figure 2. Modèle relationnel simplifié : un utilisateur possède plusieurs bilans ; chaque bilan est filtré par son propriétaire.','caption')
sub('Choix de SQLite')
p('SQLite évite d’installer un serveur de base pour la démonstration. Le fichier data/talentmatch.sqlite3 est créé au démarrage ; DATABASE_PATH permet de changer son emplacement. L’accès est centralisé dans backend/storage.py, avec requêtes paramétrées, transactions, fermeture des connexions, clés étrangères activées et mode WAL.')
sub('Un résumé indexable et un résultat complet')
p('Les colonnes title, created_at, score et is_demo suffisent à présenter la liste des bilans. Le champ payload conserve le résultat JSON validé, avec preuves, critères et recommandations. La taille d’un résultat enregistré est limitée à 2 Mio. Les fichiers originaux PDF/DOCX ne sont pas conservés dans cette table.')
sub('Propriété et migration')
p('La colonne utilisateur_id a été ajoutée pour rattacher les nouvelles analyses à leur compte. Les bilans antérieurs, dont le propriétaire est absent, ne sont pas attribués arbitrairement à un nouvel utilisateur. Les lectures et suppressions vérifient à la fois l’identifiant du bilan et celui du compte authentifié.')
p('La base n’est pas chiffrée par l’application. Les extraits du CV présents dans un bilan restent des données personnelles : la session Windows, les exports et les sauvegardes doivent être protégés.')

page('6. Authentification et connexion')
shot('react-login.png','Figure 3. Page de connexion : fond sombre, action citron vert et panneau lavande, cohérents avec le tableau de bord.')
sub('Réutilisation adaptée')
p('Le parcours de connexion et d’inscription reprend les composants et principes du projet prediction-prix-immobilier, puis les adapte à Talent Match. Cette réutilisation conserve une structure connue tout en remplaçant les éléments propres au domaine immobilier, le stockage et les styles. Sa provenance est décrite dans docs/auth-reuse.md.')
sub('Mécanisme de session')
p('Les mots de passe sont hachés avec bcrypt. Après connexion, l’API délivre un JWT HS256 valable 60 minutes, contenant notamment sub, iat et exp. Le client conserve le jeton sous une clé propre à Talent Match et l’envoie comme Bearer token. Une réponse 401 invalide la session ; la déconnexion efface l’état local.')
p('L’inscription contrôle le nom, l’adresse email et le mot de passe, avec une limite de 72 octets compatible bcrypt. L’email est unique. Le secret JWT local est généré dans un fichier exclu de Git. Les routes d’historique nécessitent une identité valide ; les routes de calcul transitoire restent accessibles sans JWT dans ce prototype local.')

page('7. Tableau de bord et identité visuelle')
shot('react-dashboard.png','Figure 4. Vue d’ensemble réelle avec le dernier bilan de démonstration à 67,7/100.')
sub('Hiérarchie visuelle')
p('Le tableau de bord organise les actions dans des panneaux distincts : démarrer une analyse, comprendre le parcours, consulter le dernier bilan, essayer la démonstration et explorer l’architecture. Le monogramme TM et la navigation latérale donnent un repère stable sur toutes les pages.')
p('La direction visuelle reprend les références fournies : fond violet sombre, surfaces noires vitrées, cartes lavande, citron vert et orange. Les couleurs fortes servent à distinguer les fonctions et les indicateurs ; le contraste sombre sur les cartes claires favorise la lecture. Les titres sont plus marqués que les libellés et les informations secondaires.')
sub('Adaptation et navigation')
p('À 1280 × 720, le tableau de bord tient dans la fenêtre. Les pages longues disposent d’un défilement central afin de conserver la navigation visible. Sur petit écran, la mise en page passe en colonne et le menu devient repliable. Les transitions accompagnent le changement de page ; elles ne portent aucune information indispensable.')
p('Les contrôles prévoient des états de focus et une utilisation au clavier. Le menu mobile gère le retour du focus et la touche Échap. La jauge expose aussi sa valeur sous une forme accessible, au-delà de sa représentation graphique.')

page('8. Saisie et lancement d’une analyse')
shot('react-analysis.png','Figure 5. Formulaire avec les textes synthétiques de démonstration et les poids de calcul visibles.')
sub('Un parcours en deux entrées')
p('Le panneau « Votre parcours » reçoit le CV ; « Votre objectif » reçoit l’offre. Chaque panneau permet soit un import, soit un collage de texte. Les limites sont affichées près de la saisie. La démonstration remplit des contenus synthétiques pour rendre le prototype testable sans document personnel.')
sub('États et erreurs')
p('Le lancement prépare une requête JSON ou multipart. Le bouton et les messages rendent le chargement visible ; les erreurs de validation sont restituées dans l’interface. Les contrôles serveur restent obligatoires même si le navigateur a déjà vérifié les champs. Les résultats tardifs d’une requête devenue obsolète ne doivent pas écraser la saisie courante.')
sub('Consentement à l’enrichissement')
p('L’option de modèle de langage est distincte du calcul local. L’interface explique que les preuves peuvent être transmises au service configuré. La capture montre le contrôle activé ; cela ne démontre pas la présence d’un serveur LLM. Sans service disponible, le prototype conserve ses conseils locaux et affiche un avertissement.')

page('9. Résultats et étude de cas')
shot('react-score-charts.png','Figure 6. Restitution du score avec jauge semi-circulaire et barres des critères, alimentées par le calcul réel.')
sub('Documents de démonstration')
p('Le CV décrit un profil data junior avec deux ans d’expérience, Python, SQL, Pandas, scikit-learn, Git et FastAPI, ainsi qu’un diplôme d’ingénieur. L’offre attend trois ans d’expérience, un Master, Python et SQL, du Machine Learning, Docker et AWS. FastAPI y constitue un atout.')
sub('Analyse des écarts')
p('Python, SQL, scikit-learn et FastAPI disposent de preuves explicites. Docker et AWS sont absents des informations reconnues. Le Machine Learning bénéficie d’une correspondance partielle liée à une compétence connexe. L’expérience obtient environ 66,7 % car le document déclare deux ans pour trois attendus. La formation atteint le niveau exigé.')
p('La jauge synthétise le résultat, mais les barres indiquent ce qui contribue au score. La matrice permet ensuite de relire les compétences et leurs extraits. Un critère non applicable n’est pas représenté comme un zéro : il reste sans barre pour éviter une interprétation trompeuse.')

page('10. Recommandations et exports')
shot('react-progression.png','Figure 7. Partie visible du plan de progression : points d’appui, priorités et projets proposés. La suite reste accessible par défilement.')
sub('Passer du diagnostic à une action')
p('Les conseils locaux s’appuient sur les écarts détectés. Ils proposent des projets pour documenter une compétence manquante, des ressources officielles connues du dictionnaire et des pistes pour mieux présenter les acquis. Dans l’exemple, Docker et AWS deviennent des priorités techniques ; l’autonomie nécessite une preuve concrète à contextualiser.')
p('Les reformulations rappellent de ne mentionner un résultat mesurable que s’il est vérifiable. Le système ne doit pas transformer une suggestion en expérience acquise. Le LLM facultatif enrichit cette rédaction ; sa réponse est validée, avec retour aux conseils locaux si le service échoue.')
sub('Trois formats de sortie')
p('<b>HTML :</b> rapport autonome consultable et imprimable en PDF.<br/><b>CSV :</b> données tabulaires pour une relecture ou une analyse externe.<br/><b>JSON :</b> résultat structuré conservant les détails du pipeline.')
p('Les exports sont produits dans le navigateur. Le HTML échappe les contenus importés ; le CSV neutralise les préfixes de formules. Les fichiers exportés peuvent contenir des extraits personnels et doivent être partagés volontairement.')

page('11. Configuration et architecture interactive')
shot('react-settings.png','Figure 8. Répartition des critères, profils prédéfinis et option de génération de conseils.')
sub('Des paramètres compréhensibles')
p('Trois profils facilitent le réglage : Équilibré (25/25/25/25), Technique (50/25/15/10) et Expérience (30/45/15/10). Les curseurs permettent un ajustement fin ; la somme affichée doit atteindre 100. Les paramètres concernent la prochaine analyse, et ne réécrivent pas silencieusement un bilan enregistré.')
sub('Une page d’explication pour l’ingénieur')
p('La page Architecture expose trois vues sélectionnables : Système, Pipeline NLP et Données & API. La sélection d’un composant affiche sa responsabilité. La vue système distingue l’interface, le serveur, le moteur et SQLite ; les autres vues détaillent le traitement et les contrats. Cette documentation visuelle facilite la soutenance et la maintenance.')
p('Les réglages restent dans l’état de l’onglet. L’historique est persistant uniquement après sauvegarde explicite. Cette distinction évite de confondre une préférence temporaire, une analyse en mémoire et un bilan conservé dans la base.')

page('12. Historique et cycle de vie des données')
shot('react-history.png','Figure 9. Bilan de démonstration enregistré dans l’historique du compte local.')
sub('Enregistrer, rouvrir, supprimer')
p('L’utilisateur choisit explicitement d’enregistrer un résultat. L’historique affiche le titre, la date, le score et la provenance de démonstration. La liste est paginée par groupes de 12 bilans. La réouverture recharge le résultat complet ; la suppression demande une confirmation dans l’interface.')
sub('Ce qui reste après fermeture')
p('Un résultat non enregistré réside dans l’état de l’onglet et disparaît au rechargement. Un bilan enregistré reste dans SQLite jusqu’à suppression. Les originaux importés ne sont pas sauvegardés durablement par l’application ; FastAPI peut utiliser des fichiers temporaires pendant la requête, fermés après traitement.')
p('Le JSON d’un bilan conserve cependant les sections et extraits nécessaires à l’explication. Le cache Hugging Face contient les poids du modèle, pas les documents des utilisateurs. Les fichiers de base et le secret de session sont exclus du dépôt de code.')
sub('Séparation entre comptes')
p('Le propriétaire est déterminé par l’identité authentifiée, pas par un identifiant libre fourni par le navigateur. Les tests couvrent l’impossibilité de lire ou supprimer le bilan d’un autre compte et la conservation des anciens enregistrements non attribués.')

page('13. API et organisation du code')
table(['Route','Rôle / accès'],[
 ('GET /health','État du moteur et disponibilité du service.'),
 ('POST /api/analyze','Analyse de deux textes JSON ; calcul transitoire.'),
 ('POST /api/analyze/files','Analyse multipart de fichiers ou textes.'),
 ('POST /api/auth/inscription','Création d’un compte local.'),
 ('POST /api/auth/connexion','Vérification des identifiants et émission du JWT.'),
 ('GET /api/auth/moi','Utilisateur de la session authentifiée.'),
 ('POST /api/analyses','Enregistrement d’un bilan ; JWT requis.'),
 ('GET /api/analyses','Liste paginée appartenant au compte ; JWT requis.'),
 ('GET /api/analyses/{id}','Réouverture d’un bilan du compte.'),
 ('DELETE /api/analyses/{id}','Suppression d’un bilan du compte.')],[216,271])
sub('Organisation des modules')
p('<b>backend/main.py</b> expose les routes et sert l’interface ; <b>schemas.py</b> définit les contrats. <b>parsing.py</b>, <b>extraction.py</b>, <b>embeddings.py</b> et <b>analysis.py</b> composent le pipeline. <b>recommendations.py</b> produit les conseils. <b>auth.py</b>, <b>auth_routes.py</b> et <b>storage.py</b> isolent l’identité et la persistance.')
p('<b>frontend-react/src</b> contient les pages, les composants de jauge, l’historique et les exports. <b>tests</b> porte les tests Python ; les tests React sont associés à l’interface. <b>run.py</b> orchestre la compilation et le lancement ; <b>docs</b> regroupe les décisions, la traçabilité et la validation.')
p('Les routes API sont prioritaires sur le repli SPA : une route API inconnue retourne une erreur 404, tandis qu’une route React profonde reçoit index.html. Les assets Vite avec empreinte sont mis en cache ; le HTML est revalidé.')

page('14. Validation et résultats des tests')
p('La validation combine tests automatisés, compilation, appels au moteur réel et parcours dans le navigateur. Les résultats ci-dessous concernent le prototype local au 4 novembre 2026 ; ils ne constituent pas une mesure de précision scientifique sur un corpus de recrutement.')
table(['Vérification','Résultat / couverture'],[
 ('Tests backend','37 tests réussis : contrats, parsing, scoring, erreurs, persistance, authentification et isolation des comptes.'),
 ('Tests frontend','17 tests réussis : états de requête, navigation mobile, historique, diagrammes, profils et jauge.'),
 ('Qualité et compilation','Ruff, lint JavaScript et compilation Vite réussis lors de la validation de livraison.'),
 ('Moteur réel','Smoke test texte et PDF/DOCX avec MiniLM réel : résultat de démonstration 67,7/100.'),
 ('Parcours navigateur','Connexion, consultation du bilan, sauvegarde, rechargement, réouverture et déconnexion vérifiés.'),
 ('Affichage','1280 × 720 sans débordement horizontal ; tests mobiles à 320/375 px selon les pages.'),
 ('LLM optionnel','Contrats et repli local testés ; aucune génération réelle avec serveur LLM revendiquée.')],[132,355])
sub('Performance observée')
p('Une série locale documentée de cinq analyses à chaud a donné une médiane de 112,1 ms et un maximum de 121,7 ms. Un autre appel du smoke test a mesuré environ 250 ms. Ces valeurs concernent un exemple court après chargement ; elles ne sont ni une garantie universelle, ni la durée du premier démarrage, ni une mesure avec génération LLM.')
sub('Échecs pris en charge et réserves')
p('Les tests couvrent notamment les poids invalides, les documents corrompus ou sans texte, les compétences non reconnues, les identifiants erronés, les emails dupliqués et les sessions expirées. Une dépréciation tierce Starlette/httpx est signalée sans faire échouer les tests. L’accessibilité complète et la sécurité d’un déploiement public restent à auditer.')

page('15. Installation et démonstration')
sub('Environnement reproductible')
p('Le projet utilise Python 3.11 à 3.13 (environnement local Python 3.12), uv, Node.js et npm. uv.lock et le verrou npm fixent les dépendances. Le premier lancement nécessite l’accès aux paquets et au modèle ; le chargement initial peut prendre plusieurs minutes.')
p('cd "C:\\Users\\zineb\\OneDrive\\Documents\\ChatGPT\\AI GENRATIVE TEXTUEL"<br/>uv sync --frozen<br/>uv run python run.py','code')
p('Le lanceur installe les dépendances npm, compile React puis démarre l’application sur http://127.0.0.1:8000. L’option --skip-build réutilise un build existant ; --no-browser évite l’ouverture automatique d’un onglet. La base est initialisée automatiquement, sans serveur SQL supplémentaire.')
sub('Scénario de soutenance')
p('1. Se connecter avec le compte de démonstration documenté dans START_HERE.md.<br/>2. Présenter la vue d’ensemble et lancer l’exemple synthétique.<br/>3. Montrer les poids, puis calculer l’adéquation.<br/>4. Expliquer le score 67,7 et une preuve couverte, partielle et absente.<br/>5. Ouvrir le plan de progression et exporter le rapport.<br/>6. Enregistrer le bilan, recharger et le retrouver dans l’historique.<br/>7. Présenter l’architecture et préciser les limites du moteur.')
sub('Commandes de vérification')
p('uv run pytest -q<br/>npm --prefix frontend-react test<br/>npm --prefix frontend-react run build<br/>uv run python -X utf8 scripts/smoke_react.py','code')
p('Le smoke test nécessite le serveur démarré et prêt. Les identifiants du compte synthétique sont fournis séparément dans le guide de lancement ; aucun mot de passe ni secret JWT n’est intégré à ce rapport destiné à être partagé.')
sub('Configuration facultative')
p('DATABASE_PATH choisit le fichier SQLite. EMBEDDING_MODEL désigne le modèle d’embeddings. LLM_BASE_URL, LLM_MODEL et LLM_API_KEY configurent le service génératif compatible. L’activation de ce service est distincte du fonctionnement local standard.')

page('16. Bilan, limites et perspectives')
sub('Bilan de la réalisation')
p('Le projet relie une interface utilisable à un moteur NLP réel et à une persistance locale. Le parcours complet va de l’import documentaire à la restitution des preuves, puis à l’export ou à l’enregistrement d’un bilan. Les diagrammes et les critères détaillés rendent le calcul explicable pour une démonstration d’ingénierie.')
sub('Limites identifiées')
p('<b>Qualité documentaire :</b> pas d’OCR ; une structure de CV complexe peut perturber l’extraction.<br/><b>Couverture linguistique :</b> dictionnaire limité et MiniLM principalement anglophone ; les alias français ne remplacent pas une évaluation multilingue.<br/><b>Évaluation :</b> absence de corpus annoté, donc pas de précision, rappel ou mesure d’équité annoncés.<br/><b>Conseils :</b> règles locales fonctionnelles ; serveur LLM facultatif non validé en exécution réelle.<br/><b>Sécurité :</b> base non chiffrée, jeton côté navigateur, absence de réinitialisation de mot de passe et de limitation du débit adaptée à une exposition publique.')
sub('Perspectives prioritaires')
p('Une prochaine version devrait d’abord constituer un corpus anonymisé et annoté pour mesurer l’extraction et le matching. Elle pourrait ensuite comparer un modèle multilingue, étendre les dictionnaires, améliorer l’interprétation des expériences et intégrer un OCR avec contrôle de qualité. Avant un déploiement public, il faudrait renforcer les sessions, protéger toutes les routes coûteuses, définir la conservation des données et tester la charge.')
sub('Sources du compte rendu')
p('Les informations pédagogiques proviennent du cahier des charges fourni. Les descriptions techniques sont fondées sur le code du projet et les documents README.md, docs/architecture.md, docs/auth-reuse.md, docs/requirements.md et docs/validation.md. Les captures sont celles de l’application locale, avec données synthétiques. Les diagrammes de ce rapport représentent la réalisation observée, et non une architecture future.','small')
p('Talent Match constitue ainsi une réalisation démontrable du cycle « extraire, évaluer, guider ». Son usage pertinent reste l’aide à la lecture d’une candidature, avec contrôle humain des preuves et des conclusions.')

body=OUT/'_body.pdf'
SimpleDocTemplate(str(body),pagesize=(595.28,841.89),leftMargin=54,rightMargin=54,topMargin=66,bottomMargin=55,title='Talent Match - Compte rendu de réalisation',author='DRISSI Yassir ; BENHEDDANE Mohamed ; BAQLOUL Zineb').build(story,onFirstPage=footer,onLaterPages=footer)

# The institutional logos are extracted from the supplied cover, without redrawing them.
from reportlab.pdfgen import canvas

cover=OUT/'_cover.pdf'
c=canvas.Canvas(str(cover),pagesize=(595.28,841.89))
c.drawImage(str(ROOT/'tmp/report-logos.png'),60,691,width=475,height=65,mask='auto')
def center(text,y,size=12,font='Body',color=NAVY):
 c.setFont(font,size);c.setFillColor(color);c.drawCentredString(297.64,y,text)
center('ÉCOLE MAROCAINE DES SCIENCES DE L’INGÉNIEUR',642,13,'Bold')
center('Membre de HONORIS UNITED UNIVERSITIES',622,9,color=colors.grey)
center('MODULE : IA & DATA SCIENCE',565,13)
center('FILIÈRE : 5e ANNÉE (5AISDR) - GROUPE G8',535,11,color=CYAN)
c.setStrokeColor(CYAN);c.setLineWidth(1.2);c.line(62,484,533,484)
center('COMPTE RENDU',450,24,'Bold');center('DE RÉALISATION',419,24,'Bold')
c.line(62,397,533,397)
center('TALENT MATCH',360,20,'Bold')
center('Analyseur intelligent de CV et d’offres d’emploi',333,13,'Bold')
center('Conception, développement et validation du prototype',302,11)
center('React · FastAPI · NLP · Authentification · SQLite',282,10)
c.setFillColor(INK);c.setFont('Bold',11);c.drawString(62,205,'Réalisé par :')
c.setFont('Body',11)
for y,name in [(184,'DRISSI Yassir'),(167,'BENHEDDANE Mohamed'),(150,'BAQLOUL Zineb')]:c.drawString(62,y,name)
c.setFont('Bold',11);c.drawString(345,205,'Encadré par :');c.setFont('Body',11);c.drawString(345,184,'Mme Salma Aitoussous')
center('Année universitaire 2026-2027',91,11)
center('Version de réalisation · 4 novembre 2026',70,9,color=colors.grey)
c.save()
from pypdf import PdfReader, PdfWriter

writer=PdfWriter()
for path in [cover,body]:
 for pg in PdfReader(path).pages:writer.add_page(pg)
writer.add_metadata({'/Title':'Talent Match - Compte rendu de réalisation','/Author':'DRISSI Yassir ; BENHEDDANE Mohamed ; BAQLOUL Zineb'})
final=OUT/'Compte_rendu_realisation_Talent_Match.pdf'
with final.open('wb') as f:writer.write(f)
(OUT/'Compte_rendu_realisation_Talent_Match.md').write_text('# Talent Match - Compte rendu de réalisation\n\n'+ '\n\n'.join(source),encoding='utf-8')
cover.unlink();body.unlink()
print(str(final));print('Pages:',len(writer.pages))
