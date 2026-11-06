# -*- coding: utf-8 -*-
"""Attribuer et dépenser des points.

Le barème est ici, en un seul endroit : dispersé dans les vues, il finirait
par diverger entre deux chemins qui récompensent la même chose.

Toute attribution est **idempotente**. Elle porte l'événement qui l'a causée,
et une contrainte d'unicité en base interdit qu'un même événement compte deux
fois. C'est la protection contre le détournement le plus simple du système :
faire échouer puis rejouer une opération pour empocher les points deux fois.
"""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import F

from .models import CompteurPoints, MouvementPoints

Motif = MouvementPoints.Motif

# Ce que rapporte chaque événement. On récompense ce qu'on veut voir se
# répéter : acheter, faire venir quelqu'un, payer son abonnement.
#
# **Un groupage abouti ne rapporte rien.** Le cahier des charges v2 a tranché :
# les points récompensent l'acheteur et le parrainage, pas le volume d'affaires
# de l'OAG. Le motif reste déclaré pour ne pas réécrire l'historique, mais il
# vaut zéro : `attribuer` refuse alors de créer un mouvement.
BAREME: dict[str, int] = {
    Motif.ACHAT: 5,
    Motif.GROUPAGE_ABOUTI: 0,
    Motif.PARRAINAGE: 2,
    Motif.ABONNEMENT_PUBLICATION: 10,
    Motif.PACK_PUBLICATION: 2,
    Motif.CONTACT_PRIVE: 10,
}


class SoldeInsuffisant(Exception):
    """Dépense refusée : le solde ne couvre pas."""


def compteur_de(utilisateur) -> CompteurPoints:
    compteur, _ = CompteurPoints.objects.get_or_create(utilisateur=utilisateur)
    return compteur


@transaction.atomic
def attribuer(utilisateur, motif: str, origine_genre: str, origine_id: int,
              points: int | None = None) -> MouvementPoints | None:
    """Crédite les points d'un événement, une seule fois.

    Rend le mouvement créé, ou `None` si cet événement avait déjà été compté.
    Le `None` n'est pas une erreur : un appel en double est précisément ce
    contre quoi la fonction protège, et l'appelant n'a rien à rattraper.
    """
    montant = BAREME[motif] if points is None else points
    if montant <= 0:
        return None

    compteur = compteur_de(utilisateur)
    try:
        with transaction.atomic():
            mouvement = MouvementPoints.objects.create(
                compteur=compteur,
                motif=motif,
                points=montant,
                origine_genre=origine_genre,
                origine_id=origine_id,
            )
    except IntegrityError:
        return None

    # `F()` plutôt qu'une lecture suivie d'une écriture : deux attributions
    # simultanées sur le même compte perdraient l'une des deux.
    CompteurPoints.objects.filter(pk=compteur.pk).update(
        cumules=F("cumules") + montant, solde=F("solde") + montant
    )
    return mouvement


@transaction.atomic
def depenser(utilisateur, points: int, origine_genre: str,
             origine_id: int) -> MouvementPoints:
    """Débite le solde, sans jamais toucher aux points cumulés.

    C'est tout l'intérêt des deux compteurs : dépenser ne fait pas perdre son
    grade, sinon personne ne dépenserait rien.
    """
    if points <= 0:
        raise ValueError("Une dépense porte sur un nombre positif de points.")

    # `select_for_update` verrouille la ligne le temps de la vérification :
    # sans ça, deux dépenses simultanées passeraient toutes les deux le test
    # du solde avant que l'une d'elles ne l'ait entamé.
    compteur = CompteurPoints.objects.select_for_update().get(
        pk=compteur_de(utilisateur).pk
    )
    if compteur.solde < points:
        raise SoldeInsuffisant(
            f"Il vous faut {points} points, vous en avez {compteur.solde}."
        )

    mouvement = MouvementPoints.objects.create(
        compteur=compteur,
        motif=Motif.DEPENSE,
        points=-points,
        origine_genre=origine_genre,
        origine_id=origine_id,
    )
    CompteurPoints.objects.filter(pk=compteur.pk).update(solde=F("solde") - points)
    return mouvement
