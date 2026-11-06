# -*- coding: utf-8 -*-
"""Le nom d'utilisateur : la seule chose que l'autre partie voit de vous.

Sur la plateforme, l'acheteur et l'OAG ne se connaissent pas. Chacun n'existe
que sous un nom qu'il a choisi, et seul l'abonnement Contact Privé ouvre le
pont entre les deux. Un nom mal choisi défait tout le dispositif à lui seul :
« Boutique Ramatou – Grand Marché » dit où aller, « Faya 90112233 » donne le
numéro, « Group Achat Officiel » usurpe la plateforme.

Ce module tient ce qui se vérifie **mécaniquement**. Ce qui ne se vérifie pas
mécaniquement — qu'un nom ne soit pas l'enseigne du commerce de l'OAG — reste
à la personne qui mène l'entretien de validation : il faut connaître le
commerce pour reconnaître son nom.
"""

from __future__ import annotations

import re
import unicodedata

from django.core.exceptions import ValidationError

LONGUEUR_MIN = 3
LONGUEUR_MAX = 24

# Les séparateurs sont ignorés pour la comparaison : « Faya-02 », « faya 02 »
# et « FAYA_02 » sont le même nom, et deux OAG portant l'un et l'autre ne
# seraient distingués par aucun acheteur.
SEPARATEURS = "-_. "

CARACTERES_AUTORISES = re.compile(r"^[0-9A-Za-zÀ-ÖØ-öø-ÿ\-_. ]+$")

# Six chiffres d'affilée, c'est déjà un numéro togolais tronqué. En dessous,
# on gêne les noms légitimes du genre « Faya-2024 ».
SUITE_DE_CHIFFRES = re.compile(r"\d{6,}")

# Mots que personne ne peut s'attribuer : ils désignent soit la plateforme,
# soit un niveau de confiance que seule la plateforme accorde.
RESERVES = {
    "officiel",
    "officielle",
    "certifie",
    "certifiee",
    "verifie",
    "verifiee",
    "garanti",
    "garantie",
    "admin",
    "administrateur",
    "administration",
    "moderateur",
    "moderation",
    "support",
    "equipe",
    "staff",
    "groupachat",
    "groupeachat",
    "achatgroupe",
    "oag",
}

# Un nom qui contient de quoi joindre quelqu'un ailleurs contourne l'abonnement
# aussi sûrement qu'un numéro en clair.
MESSAGERIES = (
    "whatsapp",
    "wame",
    "telegram",
    "messenger",
    "facebook",
    "instagram",
    "tiktok",
    "snapchat",
    "gmail",
    "yahoo",
)


def normaliser(nom: str) -> str:
    """Rend la forme qui sert à comparer deux noms entre eux.

    Minuscules, sans accents, sans séparateurs. C'est cette forme qui porte
    la contrainte d'unicité en base : comparer les formes affichées laisserait
    passer « Faya-02 » à côté de « faya02 ».
    """
    sans_accent = "".join(
        c
        for c in unicodedata.normalize("NFD", nom or "")
        if unicodedata.category(c) != "Mn"
    )
    return "".join(c for c in sans_accent.lower() if c not in SEPARATEURS)


def valider(nom: str) -> None:
    """Lève `ValidationError` si le nom ne peut pas être porté.

    Les messages s'adressent à la personne qui saisit, pas au journal : ils
    disent quoi corriger.
    """
    nom = (nom or "").strip()

    if len(nom) < LONGUEUR_MIN:
        raise ValidationError(
            f"Le nom d'utilisateur fait au moins {LONGUEUR_MIN} caractères."
        )
    if len(nom) > LONGUEUR_MAX:
        raise ValidationError(
            f"Le nom d'utilisateur fait au plus {LONGUEUR_MAX} caractères."
        )
    if not CARACTERES_AUTORISES.match(nom):
        raise ValidationError(
            "Le nom d'utilisateur n'accepte que des lettres, des chiffres, "
            "le tiret, le point, le tiret bas et l'espace."
        )

    repere = normaliser(nom)

    if not repere:
        raise ValidationError("Le nom d'utilisateur ne peut pas être vide.")
    if not any(c.isalpha() for c in repere):
        raise ValidationError("Le nom d'utilisateur contient au moins une lettre.")
    if SUITE_DE_CHIFFRES.search(repere):
        raise ValidationError(
            "Le nom d'utilisateur ne peut pas contenir de numéro de téléphone."
        )

    for mot in RESERVES:
        if mot in repere:
            raise ValidationError(
                f"« {mot} » est réservé : ce nom laisserait croire que vous "
                "parlez au nom de la plateforme ou qu'elle vous a distingué."
            )

    for messagerie in MESSAGERIES:
        if messagerie in repere:
            raise ValidationError(
                "Le nom d'utilisateur ne peut pas renvoyer vers une autre "
                "messagerie : hors de la plateforme, rien n'est couvert."
            )


def nom_de_repli(prenom: str, nom: str) -> str:
    """Ce sous quoi apparaît un acheteur qui n'a pas choisi de nom.

    Prénom et initiale : assez pour que le vendeur sache à qui il répond,
    pas assez pour retrouver quelqu'un.
    """
    prenom = (prenom or "").strip()
    initiale = (nom or "").strip()[:1].upper()
    if prenom and initiale:
        return f"{prenom} {initiale}."
    return prenom or "Acheteur"
