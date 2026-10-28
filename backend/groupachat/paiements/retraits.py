# -*- coding: utf-8 -*-
"""Les colis non retirés : relances à J+3 et J+7, livraison réputée à J+14.

Cahier des charges §4 « Colis non récupéré » : sans retrait dans les quatorze
jours qui suivent la mise à disposition, la livraison est réputée acquise et
le dossier se clôt. Sans cette tâche, un seul acheteur qui ne vient pas
laisserait la campagne en distribution pour toujours et la réputation du
groupeur ne serait jamais créditée.

Ce module est séparé de ``services.py`` (déjà long) mais en garde les règles :
verrou de la campagne d'abord (``_verrouiller``), exception métier
``ErreurPaiement``, transition ``distribution → terminée`` par ``_terminer``.

**Aucun argent ne bouge ici.** Le séquestre est versé au décaissement, avant
la distribution : une part réputée livrée n'a rien à libérer ni à rembourser.
Une campagne en distribution dont les fonds seraient encore consignés n'est
donc pas close, mais laissée à l'administrateur (décision D1).

Appelé par ``manage.py cloturer_les_campagnes_echues``, une fois par heure.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from groupachat.catalogue.models import (
    DELAI_PREMIERE_RELANCE_JOURS,
    DELAI_RETRAIT_JOURS,
    DELAI_SECONDE_RELANCE_JOURS,
    PREAVIS_AVANT_LIVRAISON_REPUTEE_HEURES,
    Campagne,
)
from groupachat.commandes.models import Participation
from groupachat.echanges.models import Notification
from groupachat.paiements.models import Sequestre
from groupachat.paiements.services import ErreurPaiement, _terminer, _verrouiller

logger = logging.getLogger(__name__)

# Ce que la clôture à J+14 décide pour une campagne, lu par la tâche comme par
# `--a-blanc` : une seule règle, donc la même liste dans les deux modes.
CLOTURE_DUE = "cloture"
CLOTURE_BLOQUEE = "bloquee"
CLOTURE_RATTRAPAGE = "rattrapage"
CLOTURE_PREAVIS = "preavis"
CLOTURE_PAS_ECHUE = "pas_echue"


def _age(campagne: Campagne, maintenant: datetime) -> timedelta | None:
    """Durée écoulée depuis la mise à disposition.

    En durée et non en jours civils : J+3 vaut 72 h, comme le délai de
    décision (``_delai_de_decision_expire``).
    """
    if campagne.mise_a_disposition_le is None:
        return None
    return maintenant - campagne.mise_a_disposition_le


def etape_de_relance(campagne: Campagne, maintenant: datetime) -> str | None:
    """L'étape de relance due (``j3`` ou ``j7``), ou None.

    Une seule étape à la fois, la plus avancée : après une panne de J+2 à J+8,
    seule la J+7 part. La J+3 arriverait en retard et contredirait l'échéance
    que la J+7 annonce.
    """
    age = _age(campagne, maintenant)
    if campagne.statut != Campagne.Statut.DISTRIBUTION or age is None:
        return None
    # Passé J+14, c'est la clôture qui joue (et sa relance de rattrapage).
    if age >= timedelta(days=DELAI_RETRAIT_JOURS):
        return None
    if (
        age >= timedelta(days=DELAI_SECONDE_RELANCE_JOURS)
        and campagne.relance_retrait_j7_le is None
    ):
        return "j7"
    if (
        age >= timedelta(days=DELAI_PREMIERE_RELANCE_JOURS)
        and campagne.relance_retrait_j3_le is None
        and campagne.relance_retrait_j7_le is None
    ):
        return "j3"
    return None


def situation_a_j_plus_14(campagne: Campagne, maintenant: datetime) -> str:
    """Ce que la clôture à J+14 ferait de cette campagne, sans rien écrire."""
    age = _age(campagne, maintenant)
    if (
        campagne.statut != Campagne.Statut.DISTRIBUTION
        or age is None
        or age < timedelta(days=DELAI_RETRAIT_JOURS)
    ):
        return CLOTURE_PAS_ECHUE
    # Lecture seule : `--a-blanc` appelle cette fonction et ne doit rien créer.
    sequestre = Sequestre.objects.filter(campagne=campagne).first()
    if sequestre is not None and sequestre.solde > 0:
        return CLOTURE_BLOQUEE
    # Seule la relance J+7 (ou de rattrapage) annonce la clôture : la J+3 ne
    # vaut pas préavis (décision D3, scénario R20).
    preavis = campagne.relance_retrait_j7_le
    if preavis is None:
        return CLOTURE_RATTRAPAGE
    if preavis > maintenant - timedelta(hours=PREAVIS_AVANT_LIVRAISON_REPUTEE_HEURES):
        return CLOTURE_PREAVIS
    return CLOTURE_DUE


def _envoyer_relance(
    campagne: Campagne, etape: str, echeance: datetime, maintenant: datetime
) -> int:
    """Une notification par part prête ; la date de l'étape est posée dans tous les cas.

    L'étape est « jouée » même sans destinataire : sans cela, la tâche la
    rejouerait à chaque passage horaire.
    """
    parts = campagne.participations.filter(
        statut=Participation.Statut.PRETE
    ).select_related("acheteur")
    date = f"{echeance:%d/%m/%Y}"
    notifications = []
    for part in parts:
        if etape == "j3":
            titre = "Votre colis vous attend"
            message = (
                f"« {campagne.titre} » vous attend à {campagne.point_remise}. "
                f"Présentez votre code {part.code_retrait} avant le {date}."
            )
        else:
            titre = "Dernier rappel : colis à retirer"
            message = (
                f"« {campagne.titre} » vous attend toujours à "
                f"{campagne.point_remise}. Sans retrait avant le {date}, la "
                "remise sera réputée faite et la campagne close. "
                f"Votre code : {part.code_retrait}."
            )
        notifications.append(
            Notification(
                destinataire=part.acheteur,
                genre=Notification.Genre.RELANCE_RETRAIT,
                titre=titre,
                message=message,
                campagne=campagne,
                lien=f"/mes-achats/{part.id}",
            )
        )
    Notification.objects.bulk_create(notifications)
    if etape == "j3":
        campagne.relance_retrait_j3_le = maintenant
        campagne.save(update_fields=["relance_retrait_j3_le"])
    else:
        campagne.relance_retrait_j7_le = maintenant
        campagne.save(update_fields=["relance_retrait_j7_le"])
    return len(notifications)


@transaction.atomic
def relancer_retrait(campagne: Campagne) -> str | None:
    """Envoie au plus UNE relance (la plus avancée due). None si rien à faire.

    La date posée sous le verrou de la campagne rend l'appel idempotent : deux
    passages le même jour, ou deux exécutions simultanées, n'envoient qu'une
    relance.
    """
    campagne = _verrouiller(campagne)
    maintenant = timezone.now()
    etape = etape_de_relance(campagne, maintenant)
    if etape is None:
        return None
    _envoyer_relance(campagne, etape, campagne.fin_du_retrait_le, maintenant)
    return etape


def relancer_les_retraits() -> list[tuple[int, str]]:
    """Tâche : (campagne, étape) pour chaque relance envoyée."""
    limite = timezone.now() - timedelta(days=DELAI_PREMIERE_RELANCE_JOURS)
    candidates = Campagne.objects.filter(
        statut=Campagne.Statut.DISTRIBUTION, mise_a_disposition_le__lte=limite
    )
    envoyees = []
    for campagne in candidates:
        etape = relancer_retrait(campagne)
        if etape is not None:
            envoyees.append((campagne.id, etape))
    return envoyees


@transaction.atomic
def reputer_livree(campagne: Campagne) -> int:
    """Passe les parts prêtes en « réputées livrées » et termine la campagne.

    Rend le nombre de parts concernées. Retourne 0 sans terminer quand le
    préavis de 72 h n'est pas encore acquis : la relance de rattrapage part
    (si aucune J+7 n'a jamais été envoyée), puis la clôture attend.
    """
    campagne = _verrouiller(campagne)
    maintenant = timezone.now()
    if campagne.statut != Campagne.Statut.DISTRIBUTION:
        raise ErreurPaiement("Cette campagne n'est pas en distribution.")
    age = _age(campagne, maintenant)
    if age is None or age < timedelta(days=DELAI_RETRAIT_JOURS):
        raise ErreurPaiement("Le délai de retrait de 14 jours n'est pas écoulé.")

    situation = situation_a_j_plus_14(campagne, maintenant)
    if situation == CLOTURE_BLOQUEE:
        # Journalisé à chaque passage horaire, sans état ni colonne de plus :
        # le cas est défensif depuis F-024 et l'administrateur doit le voir.
        logger.warning(
            "Campagne %s en distribution depuis plus de %s jours avec des fonds "
            "encore consignés : clôture suspendue.",
            campagne.id,
            DELAI_RETRAIT_JOURS,
        )
        raise ErreurPaiement(
            "Des fonds sont encore consignés : la campagne attend l'administrateur."
        )
    if situation == CLOTURE_RATTRAPAGE:
        # Le dernier délai annoncé est déjà passé : on prévient d'une
        # nouvelle échéance, 72 h plus tard, plutôt que de clore sans préavis.
        echeance = maintenant + timedelta(hours=PREAVIS_AVANT_LIVRAISON_REPUTEE_HEURES)
        _envoyer_relance(campagne, "j7", echeance, maintenant)
        return 0
    if situation == CLOTURE_PREAVIS:
        return 0

    # Verrou de la campagne déjà pris : les parts viennent ensuite. Sans
    # select_related, PostgreSQL verrouillerait aussi les comptes joints.
    identifiants = list(
        campagne.participations.select_for_update()
        .filter(statut=Participation.Statut.PRETE)
        .values_list("id", flat=True)
    )
    parts = list(
        Participation.objects.filter(id__in=identifiants).select_related("acheteur")
    )
    Participation.objects.filter(id__in=identifiants).update(
        statut=Participation.Statut.REPUTEE_LIVREE, reputee_livree_le=maintenant
    )
    Notification.objects.bulk_create(
        [
            Notification(
                destinataire=part.acheteur,
                genre=Notification.Genre.LIVRAISON_REPUTEE,
                titre="Délai de retrait écoulé",
                message=(
                    f"Vous n'avez pas retiré votre part de « {campagne.titre} » "
                    f"dans les {DELAI_RETRAIT_JOURS} jours : la remise est "
                    "réputée faite et la campagne est close. Pour toute "
                    "question, écrivez au groupeur sous la campagne. Si le "
                    "groupeur a encore votre colis, votre code reste valable."
                ),
                campagne=campagne,
                lien=f"/mes-achats/{part.id}",
            )
            for part in parts
        ]
    )

    _terminer(campagne)
    servis = campagne.participations.filter(
        statut=Participation.Statut.RETIREE
    ).count()
    Notification.objects.create(
        destinataire=campagne.groupeur,
        genre=Notification.Genre.CAMPAGNE_TERMINEE,
        titre="Campagne terminée",
        message=(
            f"« {campagne.titre} » est close. {len(parts)} colis non retiré(s) "
            f"en {DELAI_RETRAIT_JOURS} jours sont réputés livrés ; {servis} "
            "participant(s) servi(s) comptent dans votre réputation."
        ),
        campagne=campagne,
        lien=f"/groupeur/campagnes/{campagne.id}",
    )
    logger.info(
        "Campagne %s terminée à J+%s : %s part(s) réputée(s) livrée(s).",
        campagne.id,
        DELAI_RETRAIT_JOURS,
        len(parts),
    )
    return len(parts)


def reputer_livrees_les_echues() -> list[int]:
    """Tâche : identifiants des campagnes closes à J+14.

    Chaque campagne est traitée dans sa propre transaction : l'une bloquée par
    ses fonds consignés, ou terminée entre la sélection et le verrou par un
    dernier code, n'empêche pas les autres.
    """
    limite = timezone.now() - timedelta(days=DELAI_RETRAIT_JOURS)
    echues = Campagne.objects.filter(
        statut=Campagne.Statut.DISTRIBUTION, mise_a_disposition_le__lte=limite
    )
    closes = []
    for campagne in echues:
        try:
            reputer_livree(campagne)
        except ErreurPaiement as erreur:
            logger.info("Campagne %s non close à J+14 : %s", campagne.id, erreur)
            continue
        campagne.refresh_from_db(fields=["statut"])
        if campagne.statut == Campagne.Statut.TERMINEE:
            closes.append(campagne.id)
    return closes
