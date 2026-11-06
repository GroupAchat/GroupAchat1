# -*- coding: utf-8 -*-
"""Les grades d'un OAG, et ce qu'ils changent.

Le grade n'est pas une décoration : il décide de **la commission** que la
plateforme prélève et du **contrôle** exercé avant la mise en ligne. Un OAG
progresse vers l'autonomie en prouvant qu'il la mérite, et c'est aussi ce qui
libère la capacité de vérification de l'équipe.

**Les taux sont en centièmes de pour-cent**, pas en décimaux. Tous les
montants de l'application sont des entiers de FCFA ; introduire un `Decimal`
ici rouvrirait la question de l'arrondi à chaque calcul de commission. 4 %
s'écrit donc 400, et la commission d'un montant vaut `montant * 400 // 10000`.

Le cahier des charges v2 fixe Bronze à 250 points, Argent à 400 et Or à 600.
Un OAG qui vient d'être validé n'a encore rien gagné : il lui faut donc un
état **avant** Bronze, sans quoi il n'aurait aucun grade. C'est `NOUVEAU`,
et il paie la même commission que Bronze — personne n'est financièrement
pénalisé de n'être qu'au début.
"""

from __future__ import annotations

from django.db import models


class Grade(models.TextChoices):
    NOUVEAU = "nouveau", "Nouveau"
    BRONZE = "bronze", "Bronze"
    ARGENT = "argent", "Argent"
    OR = "or", "Or"


# Bronze n'est plus le point de départ : c'est un palier à atteindre, à 250
# points. Avant lui, `NOUVEAU` couvre l'observation.
SEUILS: dict[str, int] = {
    Grade.NOUVEAU: 0,
    Grade.BRONZE: 250,
    Grade.ARGENT: 400,
    Grade.OR: 600,
}

COMMISSIONS_CENTIEMES: dict[str, int] = {
    Grade.NOUVEAU: 400,
    Grade.BRONZE: 400,
    Grade.ARGENT: 300,
    Grade.OR: 200,
}

# Du plus exigeant au moins exigeant : le premier seuil atteint gagne.
_ORDRE = [Grade.OR, Grade.ARGENT, Grade.BRONZE, Grade.NOUVEAU]

# De bas en haut, pour dire ce qu'il reste à parcourir.
_ORDRE_CROISSANT = [Grade.BRONZE, Grade.ARGENT, Grade.OR]


def grade_pour(points_cumules: int) -> str:
    """Le grade que donnent ces points.

    On lit les seuils du plus haut au plus bas pour que le résultat ne dépende
    pas de l'ordre de déclaration : un barème saisi de travers ne doit pas
    rétrograder quelqu'un qui a plus de points.
    """
    for grade in _ORDRE:
        if points_cumules >= SEUILS[grade]:
            return grade
    return Grade.NOUVEAU


def commission_centiemes(grade: str) -> int:
    """Le taux applicable, en centièmes de pour-cent."""
    return COMMISSIONS_CENTIEMES.get(grade, COMMISSIONS_CENTIEMES[Grade.NOUVEAU])


def commission_sur(montant: int, taux_centiemes: int) -> int:
    """La commission due sur un montant, en francs entiers.

    L'arrondi se fait **vers le bas**, en faveur de l'OAG : sur un écart
    d'un franc, mieux vaut que ce soit la plateforme qui le laisse.
    """
    return max(0, montant) * max(0, taux_centiemes) // 10000


def prochain_palier(points_cumules: int) -> tuple[str, int] | None:
    """Le grade suivant et ce qu'il reste à parcourir, ou None au sommet."""
    for grade in _ORDRE_CROISSANT:
        if points_cumules < SEUILS[grade]:
            return grade, SEUILS[grade] - points_cumules
    return None
