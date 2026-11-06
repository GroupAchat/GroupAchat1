# -*- coding: utf-8 -*-
"""La vérification avant mise en ligne, selon le grade de l'OAG.

| Grade | Vérification |
|---|---|
| Nouveau | systématique |
| Bronze | systématique |
| Argent | par sondage — une sur quatre |
| Or | a posteriori, donc publication libre |

**C'est le seul filtre entre un OAG tout neuf et la vitrine.** Le dossier KYC
dit qui il est ; il ne dit rien de ce qu'il publie. Un prix absurde, une photo
volée ou un produit interdit passés en direct coûtent plus cher à réparer
qu'à relire — et c'est l'acheteur qui paie la différence, puisque c'est la
plateforme qu'il croit.

Le sondage de l'Argent est **déterministe** : une campagne sur quatre, comptée
sur ses mises en ligne passées. Un tirage au sort aurait le même effet moyen,
mais ni l'OAG ni l'équipe ne pourraient vérifier après coup que la règle a été
suivie — et un contrôle qu'on ne peut pas auditer finit par être soupçonné.
"""

from __future__ import annotations

from groupachat.comptes import points
from groupachat.comptes.grades import Grade

UNE_SUR_N_EN_ARGENT = 4


def verification_requise(oag) -> bool:
    grade = points.compteur_de(oag).grade

    if grade == Grade.OR:
        return False
    if grade in (Grade.NOUVEAU, Grade.BRONZE):
        return True

    # Argent : une sur quatre. Le compteur porte sur les **mises en ligne
    # demandées** — tout ce qui a quitté le brouillon.
    #
    # Compter `publiee_le` serait le piège : une campagne en vérification
    # n'en a pas encore, le compteur ne bougerait jamais, et toutes les
    # campagnes d'un Argent passeraient par la relecture. Un refus ramène au
    # brouillon et sort donc du compte, ce qui est juste : la mise en ligne
    # n'a pas eu lieu.
    from groupachat.catalogue.models import Campagne

    deja_demandees = (
        Campagne.objects.filter(groupeur=oag)
        .exclude(statut=Campagne.Statut.BROUILLON)
        .count()
    )
    return deja_demandees % UNE_SUR_N_EN_ARGENT == 0


def motif_de_la_verification(oag) -> str:
    """Pourquoi cette campagne attend, dit à l'OAG sans détour."""
    grade = points.compteur_de(oag).grade
    if grade in (Grade.NOUVEAU, Grade.BRONZE):
        return (
            "À ce grade, chaque Offre d'achat est relue avant d'apparaître au "
            "catalogue. En général sous 24 heures."
        )
    return (
        "Au grade Argent, un groupage sur quatre est relu avant d'apparaître "
        "au catalogue. Celui-ci est tombé sur le sondage."
    )
