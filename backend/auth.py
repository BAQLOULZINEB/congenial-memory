# =====================================================================
# Authentification : hachage des mots de passe (bcrypt) + jetons JWT (PyJWT)
# + dépendance FastAPI « utilisateur courant » pour protéger les routes.
# =====================================================================
# Importer les outils nécessaires
import secrets
from datetime import UTC, datetime, timedelta
from sqlite3 import Connection
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.storage import connection, database_path


def get_bdd():
    with connection() as db:
        yield db


def signing_key():
    path = database_path().with_suffix(".jwt-key")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as key_file:
            key_file.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    return path.read_text(encoding="utf-8").strip()

# Clé JWT générée localement et conservée hors Git, distincte du projet source.

ALGORITHME = "HS256"
DUREE_JETON_MINUTES = 60


# ---------------------------------------------------------------------
# 1. Mots de passe
# ---------------------------------------------------------------------
def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Renvoie le hachage bcrypt (sel aléatoire inclus) du mot de passe."""
    # Validation rejects passwords above the bcrypt byte limit; never truncate.
    octets = mot_de_passe.encode("utf-8")
    return bcrypt.hashpw(octets, bcrypt.gensalt()).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, hachage: str) -> bool:
    """Recalcule le hachage avec le même sel et compare : True si c'est le bon mot de passe."""
    octets = mot_de_passe.encode("utf-8")
    if len(octets) > 72:
        return False
    return bcrypt.checkpw(octets, hachage.encode("utf-8"))


# ---------------------------------------------------------------------
# 2. Jetons JWT
# ---------------------------------------------------------------------
def creer_jeton(utilisateur_id: int) -> str:
    """Crée un jeton signé qui contient l'id de l'utilisateur et expire dans 60 minutes."""
    maintenant = datetime.now(UTC)
    contenu = {
        "sub": str(utilisateur_id),  # "subject" : à qui appartient le jeton (texte obligatoire)
        "iat": maintenant,           # date de création
        "exp": maintenant + timedelta(minutes=DUREE_JETON_MINUTES),  # date d'expiration
    }
    return jwt.encode(contenu, signing_key(), algorithm=ALGORITHME)


# ---------------------------------------------------------------------
# 3. Dépendance « utilisateur courant »
# ---------------------------------------------------------------------
# Lit l'en-tête "Authorization: Bearer <jeton>" (et ajoute le bouton Authorize dans /docs).
# auto_error=False : c'est nous qui renvoyons l'erreur, pour avoir toujours un 401.
schema_bearer = HTTPBearer(auto_error=False)


def utilisateur_courant(
    identifiants: Annotated[HTTPAuthorizationCredentials | None, Depends(schema_bearer)],
    bdd: Annotated[Connection, Depends(get_bdd)],
) -> dict:
    """Vérifie le jeton et renvoie l'utilisateur connecté, sinon erreur 401."""
    erreur_401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton manquant, invalide ou expiré. Veuillez vous reconnecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Pas d'en-tête Authorization
    if identifiants is None:
        raise erreur_401

    # Vérifier la signature et l'expiration (algorithme imposé : refuse les jetons "none")
    try:
        contenu = jwt.decode(identifiants.credentials, signing_key(), algorithms=[ALGORITHME], options={"require": ["sub", "iat", "exp"]})
        utilisateur_id = int(contenu["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise erreur_401

    # Vérifier que l'utilisateur existe toujours en base
    ligne = bdd.execute(
        "SELECT id, nom, email, cree_le FROM utilisateurs WHERE id = ?", (utilisateur_id,)
    ).fetchone()
    if ligne is None:
        raise erreur_401

    return dict(ligne)
