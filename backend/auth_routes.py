"""Authentication routes adapted from prediction-prix-immobilier/api/main.py."""
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from backend.auth import creer_jeton, get_bdd, hacher_mot_de_passe, utilisateur_courant, verifier_mot_de_passe

router = APIRouter(prefix="/api")

class Connexion(BaseModel):
    email: str = Field(max_length=254)
    mot_de_passe: str = Field(min_length=1, max_length=72)

class Inscription(Connexion):
    nom: str = Field(min_length=2, max_length=50)
    email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    mot_de_passe: str = Field(min_length=8, max_length=72)

    @field_validator("nom", "email", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("mot_de_passe")
    @classmethod
    def bcrypt_length(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Mot de passe trop long : 72 octets maximum.")
        return value

# Route POST "/auth/inscription" : crée un compte (mot de passe haché)
@router.post("/auth/inscription", status_code=status.HTTP_201_CREATED)
def inscription(donnees: Inscription, bdd: Annotated[sqlite3.Connection, Depends(get_bdd)]):
    # Email en minuscules : "Ali@x.com" et "ali@x.com" sont le même compte
    email = donnees.email.lower()
    nom = donnees.nom.strip()

    try:
        # SQLite lie les valeurs séparément du SQL.
        # RETURNING : récupère la ligne créée (id et date remplis par SQLite)
        utilisateur = bdd.execute(
            """INSERT INTO utilisateurs (nom, email, mot_de_passe_hash)
               VALUES (?, ?, ?)
               RETURNING id, nom, email, cree_le""",
            (nom, email, hacher_mot_de_passe(donnees.mot_de_passe)),
        ).fetchone()
        bdd.commit()
    except sqlite3.IntegrityError:
        # La contrainte UNIQUE sur email a refusé l'insertion
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Un compte existe déjà avec cet email.")

    return dict(utilisateur)


# Route POST "/auth/connexion" : vérifie les identifiants, renvoie un jeton JWT
@router.post("/auth/connexion")
def connexion(donnees: Connexion, bdd: Annotated[sqlite3.Connection, Depends(get_bdd)]):
    ligne = bdd.execute(
        "SELECT id, nom, email, mot_de_passe_hash FROM utilisateurs WHERE email = ?",
        (donnees.email.strip().lower(),),
    ).fetchone()

    # Même message que l'email soit inconnu ou le mot de passe faux :
    # on ne révèle pas quels emails sont inscrits
    if ligne is None or not verifier_mot_de_passe(donnees.mot_de_passe, ligne["mot_de_passe_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Email ou mot de passe incorrect.",
                            headers={"WWW-Authenticate": "Bearer"})

    return {
        "access_token": creer_jeton(ligne["id"]),
        "token_type": "bearer",
        "utilisateur": {"id": ligne["id"], "nom": ligne["nom"], "email": ligne["email"]},
    }


# Route GET "/auth/moi" : renvoie l'utilisateur connecté (jeton obligatoire)
@router.get("/auth/moi")
def moi(utilisateur: Annotated[dict, Depends(utilisateur_courant)]):
    return dict(utilisateur)
