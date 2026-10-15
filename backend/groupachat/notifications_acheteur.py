# -*- coding: utf-8 -*-
"""Ce qu'on écrit à un acheteur dans sa cloche. Rédaction seule.

⚠️ **À ne pas confondre avec ``notifications.py``**, qui est le voisin le plus
proche et un tout autre sujet : celui-là compose ce qu'on écrit à un
**groupeur** quand son dossier KYC est tranché, par courriel ou par appel
(§10.5). Celui-ci compose ce qui s'affiche dans la cloche d'un **acheteur**,
dans l'application. Deux publics, deux canaux, deux moments.

**Ce module ne connaît pas Django**, comme ``domaine.py``, ``moderation.py``
et ``notifications.py`` : il ne fait que composer du texte. C'est la couche
Django qui enregistre, et c'est ce qui permet de relire chaque formulation
sans base de données.

## Ce que c'est, et ce que ce n'est surtout pas

**C'est la plateforme qui écrit, toujours.** Le groupeur peut *déclencher* une
notification — « le produit est arrivé » — mais il n'en rédige jamais le
texte. La différence n'est pas cosmétique, elle tient trois règles produit
d'un coup :

- **pas de messagerie privée.** Un champ libre du groupeur vers ses acheteurs
  serait une messagerie, quel que soit le nom qu'on lui donne ;
- **l'anonymat des deux côtés.** Le groupeur ne sait pas à qui part la
  notification : il annonce un fait sur sa campagne, et nous la distribuons.
  Il n'y voit ni nom, ni numéro, ni quartier ;
- **la modération du §15.** Un texte libre partant à trente personnes d'un
  coup devrait passer le filtre, et un filtre sur un envoi groupé est
  exactement le genre de chose qu'on oublie de brancher. Ici il n'y a pas de
  texte libre : il n'y a rien à filtrer.

## Pourquoi le texte est figé à l'envoi

Chaque notification décrit **un événement daté**. « Vos 5 000 F vous ont été
remboursés » doit continuer à dire 5 000 F si le prix de la part change
ensuite, et « le produit est arrivé » reste vrai même si le groupage est
annulé après. On écrit donc le texte une fois, au moment du fait, et on ne le
recalcule jamais à l'affichage.

Le revers est assumé : corriger une formulation ne corrige pas les
notifications déjà parties. C'est le bon compromis pour un journal
d'événements, et le mauvais pour une interface — d'où ce module, qui tient
**toutes** les formulations au même endroit pour qu'on puisse au moins les
relire d'un coup.
"""

from __future__ import annotations

from decimal import Decimal


def formater_francs(montant: Decimal | int) -> str:
    """« 5 000 F » — espace insécable fine entre les milliers, comme §1.4.

    ⚠️ L'espace des milliers est U+202F (fine insécable) et celui qui précède
    le ``F`` est U+00A0 (insécable). Les deux comptent : un montant coupé en
    fin de ligne entre le nombre et son unité se relit deux fois.
    """
    return f"{int(montant):,}".replace(",", " ") + " F"


def produit_arrive(campagne) -> tuple[str, str]:
    """Le groupeur annonce qu'il a reçu la marchandise.

    ⚠️ **Elle ne promet aucune date de livraison.** Le groupeur sait que le
    produit est chez lui ; il ne sait pas quand la tournée passera, et nous
    non plus tant que la livraison n'est pas organisée (§6 du cahier des
    charges). Écrire « livraison demain » ici serait inventer un engagement
    que personne ne tient — et cette notification est justement celle qu'on
    relira pour reprocher le retard.
    """
    return (
        "Votre commande est arrivée",
        f"{campagne.groupeur.pseudonyme} a reçu « {campagne.titre} ». "
        "Votre livraison est en préparation : vous recevrez votre code de "
        "livraison quand la tournée sera lancée.",
    )


def reponse_a_une_question(question) -> tuple[str, str]:
    """Le groupeur a répondu à une question publique.

    ⚠️ **On peut citer la réponse sans risque, et seulement pour une
    raison** : elle est passée par ``Question.save``, donc par le filtre du
    §15, avant d'arriver ici. Recopier un texte de groupeur venu d'un champ
    non filtré ferait de cette cloche un contournement de la modération — un
    numéro de téléphone interdit dans le fil public mais distribué par
    notification.
    """
    extrait = " ".join(question.reponse.split())
    if len(extrait) > 120:
        extrait = extrait[:119].rstrip() + "…"
    return (
        f"{question.campagne.groupeur.pseudonyme} a répondu à votre question",
        f"Sur « {question.campagne.titre} » : {extrait}",
    )


def groupage_cloture(campagne) -> tuple[str, str]:
    """Le groupage est clôturé ; la commande part chez le fournisseur.

    ⚠️ **Ne jamais écrire ici que l'argent reste détenu.** À la clôture, le
    solde devient retirable par le groupeur : c'est la **garantie** de Group
    Achat qui porte à partir de ce moment, pas la détention des fonds. La
    formulation interdite est au §1.7 de la spec des écrans.
    """
    return (
        "Groupage clôturé",
        f"« {campagne.titre} » est clôturé. {campagne.groupeur.pseudonyme} "
        "confirme la commande sous 48 h. Group Achat garantit votre livraison.",
    )


def groupage_annule(commande) -> tuple[str, str]:
    """Le groupage n'a pas abouti : remboursement intégral.

    **Le montant est celui que cette personne a payé**, frais de livraison
    compris, et il est dit en clair. C'est la notification qu'on relira pour
    vérifier un compte : un « vous avez été remboursé » sans chiffre n'aide
    personne, et un chiffre hors livraison ferait croire à une retenue —
    alors qu'aucun frais n'est prélevé sur un groupage annulé (§7).
    """
    return (
        "Groupage annulé — vous êtes remboursé",
        f"« {commande.campagne.titre} » n'a pas abouti. Vos "
        f"{formater_francs(commande.total)} vous ont été remboursés, frais de "
        "livraison compris.",
    )
