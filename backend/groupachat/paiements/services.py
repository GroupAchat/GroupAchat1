# -*- coding: utf-8 -*-
"""Les mouvements d'argent et les transitions qu'ils provoquent.

Tout ce qui touche au séquestre passe par ici, et non par les vues : ce sont
les règles qui protègent l'acheteur, et elles doivent se lire au même endroit
qu'on arrive par l'API, par une commande d'administration ou par la tâche de
clôture automatique.

**Rien n'est réellement encaissé.** La passerelle est simulée : elle fabrique
une référence et déclare la transaction confirmée. Le jour où un agrégateur
est branché, seule :func:`_executer_paiement` change.
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Participation
from groupachat.echanges.models import Notification
from groupachat.paiements.models import Decaissement, Sequestre, Transaction


class ErreurPaiement(Exception):
    """Un paiement refusé pour une raison métier, pas pour une panne."""


def _reference_simulee(prefixe: str) -> str:
    return f"{prefixe}-{timezone.now():%Y%m%d}-{secrets.token_hex(3).upper()}"


def _executer_paiement(montant: int, numero: str, operateur: str) -> tuple[bool, str]:
    """Appelle l'opérateur Mobile Money. Simulé pour l'instant.

    Rend (succès, référence). C'est le seul point à réécrire pour brancher un
    vrai agrégateur ; tout le reste du module raisonne sur ce résultat.
    """
    return True, _reference_simulee("SIM")


def sequestre_de(campagne: Campagne) -> Sequestre:
    """Le séquestre de la campagne, créé à la volée s'il manque."""
    sequestre, _ = Sequestre.objects.get_or_create(campagne=campagne)
    return sequestre


@transaction.atomic
def encaisser(participation: Participation, operateur: str, numero: str) -> Transaction:
    """Encaisse la part d'un acheteur et la consigne au séquestre.

    L'argent va au séquestre, **jamais au groupeur** : c'est toute la promesse
    faite à l'acheteur. Le code de retrait n'est attribué qu'ici, une fois le
    paiement confirmé.
    """
    if participation.statut != Participation.Statut.EN_ATTENTE_PAIEMENT:
        raise ErreurPaiement("Cette part n'est plus en attente de paiement.")

    # On relit la campagne sous verrou : deux acheteurs qui paient en même
    # temps sur la dernière place disponible doivent être départagés.
    campagne = Campagne.objects.select_for_update().get(pk=participation.campagne_id)
    if not campagne.collecte_ouverte:
        raise ErreurPaiement("La collecte de cette campagne est close.")
    if campagne.quantite_maximale is not None:
        reste = campagne.quantite_maximale - campagne.quantite_reservee
        if participation.quantite > reste:
            raise ErreurPaiement(
                f"Il ne reste que {max(reste, 0)} pièce(s) disponible(s)."
            )

    succes, reference = _executer_paiement(
        participation.montant_total, numero, operateur
    )
    mouvement = Transaction.objects.create(
        participation=participation,
        sens=Transaction.Sens.ENCAISSEMENT,
        montant=participation.montant_total,
        operateur=operateur,
        numero=numero,
        reference=reference,
        statut=Transaction.Statut.CONFIRMEE if succes else Transaction.Statut.ECHOUEE,
        confirmee_le=timezone.now() if succes else None,
        motif_echec="" if succes else "Refus de l'opérateur.",
    )
    if not succes:
        raise ErreurPaiement("Le paiement a été refusé par l'opérateur.")

    participation.statut = Participation.Statut.PAYEE
    participation.payee_le = timezone.now()
    participation.attribuer_code_retrait()
    participation.save(update_fields=["statut", "payee_le", "code_retrait"])

    sequestre = sequestre_de(campagne)
    sequestre.montant_consigne += participation.montant_total
    sequestre.save(update_fields=["montant_consigne"])

    _notifier_paiement(campagne, participation)
    return mouvement


def _notifier_paiement(campagne: Campagne, participation: Participation) -> None:
    Notification.objects.create(
        destinataire=participation.acheteur,
        genre=Notification.Genre.PAIEMENT_ENREGISTRE,
        titre="Paiement enregistré",
        message=(
            f"Votre part de {participation.montant_total} FCFA est consignée. "
            f"Votre code de retrait : {participation.code_retrait}."
        ),
        campagne=campagne,
        lien=f"/participations/{participation.id}",
    )
    # Le suivi nominatif en temps réel : c'est ce qui remplace la liste
    # WhatsApp et les captures d'écran.
    Notification.objects.create(
        destinataire=campagne.groupeur,
        genre=Notification.Genre.PAIEMENT_RECU,
        titre="Nouveau paiement",
        message=(
            f"{participation.acheteur.nom_complet} a payé "
            f"{participation.quantite} pièce(s) — {participation.montant_total} FCFA."
        ),
        campagne=campagne,
        lien=f"/groupeur/campagnes/{campagne.id}",
    )

    if campagne.minimum_atteint:
        Notification.objects.create(
            destinataire=campagne.groupeur,
            genre=Notification.Genre.MINIMUM_ATTEINT,
            titre="Minimum atteint",
            message=f"« {campagne.titre} » a atteint son minimum de pièces.",
            campagne=campagne,
            lien=f"/groupeur/campagnes/{campagne.id}",
        )


@transaction.atomic
def rembourser(participation: Participation, motif: str = "") -> Transaction | None:
    """Rend sa mise à un acheteur et le retire du séquestre.

    Les frais d'opérateur sont à la charge de la plateforme — c'est le prix
    de la promesse « livré ou remboursé ».
    """
    if participation.statut not in Participation.STATUTS_PAYES:
        return None

    succes, reference = _executer_paiement(
        participation.montant_total,
        participation.acheteur.telephone,
        Transaction.objects.filter(
            participation=participation, sens=Transaction.Sens.ENCAISSEMENT
        ).values_list("operateur", flat=True).first()
        or "tmoney",
    )
    mouvement = Transaction.objects.create(
        participation=participation,
        sens=Transaction.Sens.REMBOURSEMENT,
        montant=participation.montant_total,
        operateur=Transaction.objects.filter(participation=participation)
        .values_list("operateur", flat=True)
        .first()
        or "tmoney",
        numero=participation.acheteur.telephone,
        reference=reference,
        statut=Transaction.Statut.CONFIRMEE,
        confirmee_le=timezone.now(),
    )

    participation.statut = Participation.Statut.REMBOURSEE
    participation.save(update_fields=["statut"])

    sequestre = sequestre_de(participation.campagne)
    sequestre.montant_rembourse += participation.montant_total
    sequestre.save(update_fields=["montant_rembourse"])

    Notification.objects.create(
        destinataire=participation.acheteur,
        genre=Notification.Genre.REMBOURSEMENT,
        titre="Remboursement effectué",
        message=(
            f"{participation.montant_total} FCFA vous ont été remboursés"
            + (f" — {motif}" if motif else ".")
        ),
        campagne=participation.campagne,
    )
    return mouvement


@transaction.atomic
def cloturer(campagne: Campagne) -> str:
    """Ferme la collecte et décide du sort de la campagne.

    Minimum atteint, la campagne est financée ; sinon elle est annulée et
    **tout le monde est remboursé**, sans que personne ait à réclamer.
    """
    if campagne.statut != Campagne.Statut.EN_COURS:
        return campagne.statut

    sequestre = sequestre_de(campagne)
    campagne.cloturee_le = timezone.now()

    if campagne.minimum_atteint:
        campagne.statut = Campagne.Statut.FINANCEE
        sequestre.statut = Sequestre.Statut.BLOQUE
        sequestre.save(update_fields=["statut"])
        campagne.save(update_fields=["statut", "cloturee_le"])

        for participation in campagne.participations.filter(
            statut=Participation.Statut.PAYEE
        ).select_related("acheteur"):
            Notification.objects.create(
                destinataire=participation.acheteur,
                genre=Notification.Genre.CAMPAGNE_FINANCEE,
                titre="Campagne financée",
                message=(
                    f"« {campagne.titre} » a atteint son objectif. "
                    "Le groupeur va s'approvisionner."
                ),
                campagne=campagne,
            )
        Notification.objects.create(
            destinataire=campagne.groupeur,
            genre=Notification.Genre.CAMPAGNE_FINANCEE,
            titre="Campagne financée",
            message=f"« {campagne.titre} » est financée : demandez votre retrait.",
            campagne=campagne,
            lien=f"/groupeur/campagnes/{campagne.id}",
        )
        return campagne.statut

    campagne.statut = Campagne.Statut.ANNULEE
    campagne.motif_annulation = "Minimum de pièces non atteint à la date limite."
    campagne.save(update_fields=["statut", "cloturee_le", "motif_annulation"])

    for participation in campagne.participations.filter(
        statut=Participation.Statut.PAYEE
    ).select_related("acheteur"):
        Notification.objects.create(
            destinataire=participation.acheteur,
            genre=Notification.Genre.CAMPAGNE_ANNULEE,
            titre="Campagne annulée",
            message=(
                f"« {campagne.titre} » n'a pas atteint son minimum. "
                "Vous êtes intégralement remboursé."
            ),
            campagne=campagne,
        )
        rembourser(participation, motif="campagne annulée")

    sequestre.refresh_from_db()
    sequestre.statut = Sequestre.Statut.REMBOURSE
    sequestre.solde_le = timezone.now()
    sequestre.save(update_fields=["statut", "solde_le"])
    return campagne.statut


@transaction.atomic
def demander_decaissement(campagne: Campagne) -> Decaissement:
    """Le groupeur réclame les fonds d'une campagne financée."""
    if campagne.statut != Campagne.Statut.FINANCEE:
        raise ErreurPaiement("Seule une campagne financée peut être décaissée.")
    if Decaissement.objects.filter(campagne=campagne).exists():
        raise ErreurPaiement("Un décaissement a déjà été demandé.")

    sequestre = sequestre_de(campagne)
    frais, net = Decaissement.calculer(sequestre.solde)
    dossier = getattr(campagne.groupeur, "dossier_kyc", None)
    return Decaissement.objects.create(
        campagne=campagne,
        montant_brut=sequestre.solde,
        frais=frais,
        montant_net=net,
        numero_mobile_money=(
            dossier.numero_mobile_money if dossier else campagne.groupeur.telephone
        ),
        operateur="tmoney",
    )


@transaction.atomic
def executer_decaissement(decaissement: Decaissement, administrateur) -> Decaissement:
    """L'administrateur libère les fonds vers le groupeur."""
    if decaissement.statut == Decaissement.Statut.EXECUTE:
        raise ErreurPaiement("Ce décaissement a déjà été exécuté.")

    succes, reference = _executer_paiement(
        decaissement.montant_net,
        decaissement.numero_mobile_money,
        decaissement.operateur,
    )
    if not succes:
        decaissement.statut = Decaissement.Statut.REFUSE
        decaissement.motif_refus = "Refus de l'opérateur."
        decaissement.save(update_fields=["statut", "motif_refus"])
        raise ErreurPaiement("Le versement a été refusé par l'opérateur.")

    decaissement.statut = Decaissement.Statut.EXECUTE
    decaissement.execute_le = timezone.now()
    decaissement.execute_par = administrateur
    decaissement.reference = reference
    decaissement.save(
        update_fields=["statut", "execute_le", "execute_par", "reference"]
    )

    sequestre = sequestre_de(decaissement.campagne)
    # Le montant brut, frais compris, quitte le séquestre : les frais sont le
    # revenu de la plateforme, pas de l'argent encore détenu pour autrui.
    sequestre.montant_libere += decaissement.montant_brut
    sequestre.statut = Sequestre.Statut.LIBERE
    sequestre.solde_le = timezone.now()
    sequestre.save(update_fields=["montant_libere", "statut", "solde_le"])

    campagne = decaissement.campagne
    campagne.statut = Campagne.Statut.APPROVISIONNEMENT
    campagne.save(update_fields=["statut"])

    Notification.objects.create(
        destinataire=campagne.groupeur,
        genre=Notification.Genre.CAMPAGNE_FINANCEE,
        titre="Fonds versés",
        message=(
            f"{decaissement.montant_net} FCFA ont été versés sur "
            f"{decaissement.numero_mobile_money} "
            f"({decaissement.frais} FCFA de frais de plateforme)."
        ),
        campagne=campagne,
    )
    return decaissement


@transaction.atomic
def mettre_a_disposition(campagne: Campagne, point_remise: str = "") -> int:
    """Le groupeur annonce que la marchandise est arrivée.

    C'est le geste qui déclenche la distribution : **tous les participants
    sont notifiés**, avec le point de remise et le rappel de leur code.
    """
    if campagne.statut not in (
        Campagne.Statut.APPROVISIONNEMENT,
        Campagne.Statut.DECAISSEE,
        Campagne.Statut.FINANCEE,
    ):
        raise ErreurPaiement("Cette campagne n'en est pas à la distribution.")

    if point_remise:
        campagne.point_remise = point_remise
    campagne.statut = Campagne.Statut.DISTRIBUTION
    campagne.mise_a_disposition_le = timezone.now()
    campagne.save(update_fields=["statut", "mise_a_disposition_le", "point_remise"])

    participations = campagne.participations.filter(
        statut=Participation.Statut.PAYEE
    ).select_related("acheteur")

    notifications = []
    for participation in participations:
        notifications.append(
            Notification(
                destinataire=participation.acheteur,
                genre=Notification.Genre.MARCHANDISE_DISPONIBLE,
                titre="Votre produit est arrivé",
                message=(
                    f"« {campagne.titre} » est à retirer à {campagne.point_remise}. "
                    f"Présentez votre code : {participation.code_retrait}."
                ),
                campagne=campagne,
                lien=f"/participations/{participation.id}",
            )
        )
    Notification.objects.bulk_create(notifications)
    participations.update(statut=Participation.Statut.PRETE)
    return len(notifications)


@transaction.atomic
def valider_retrait(campagne: Campagne, code: str, agent) -> Participation:
    """Remet le colis contre présentation du code ou du QR.

    Le code est cherché **dans cette campagne seulement** : un code valide
    d'une autre campagne ne doit pas ouvrir celle-ci.
    """
    code = (code or "").strip().upper()
    # Un QR scanné arrive sous la forme GA|<campagne>|<code>.
    if code.startswith("GA|"):
        morceaux = code.split("|")
        if len(morceaux) != 3 or morceaux[1] != str(campagne.id):
            raise ErreurPaiement("Ce QR code ne concerne pas cette campagne.")
        code = morceaux[2]

    participation = campagne.participations.filter(code_retrait=code).first()
    if participation is None:
        raise ErreurPaiement("Code inconnu pour cette campagne.")
    if participation.statut == Participation.Statut.RETIREE:
        raise ErreurPaiement(
            f"Colis déjà retiré le {participation.retiree_le:%d/%m/%Y à %H:%M}."
        )
    if participation.statut != Participation.Statut.PRETE:
        raise ErreurPaiement("Cette part n'est pas prête à être retirée.")

    participation.statut = Participation.Statut.RETIREE
    participation.retiree_le = timezone.now()
    participation.remise_par = agent
    participation.save(update_fields=["statut", "retiree_le", "remise_par"])

    Notification.objects.create(
        destinataire=participation.acheteur,
        genre=Notification.Genre.RETRAIT_CONFIRME,
        titre="Retrait confirmé",
        message=f"Vous avez retiré votre part de « {campagne.titre} ». Merci !",
        campagne=campagne,
    )

    # Dernier colis remis : la campagne est terminée et la réputation du
    # groupeur en tient compte.
    if not campagne.participations.filter(statut=Participation.Statut.PRETE).exists():
        campagne.statut = Campagne.Statut.TERMINEE
        campagne.save(update_fields=["statut"])
        _crediter_reputation(campagne)

    return participation


def _crediter_reputation(campagne: Campagne) -> None:
    from groupachat.comptes.models import Reputation

    reputation, _ = Reputation.objects.get_or_create(groupeur=campagne.groupeur)
    reputation.campagnes_terminees += 1
    reputation.participants_servis += campagne.participations.filter(
        statut=Participation.Statut.RETIREE
    ).count()

    # Note sur cinq : la part des campagnes menées à terme, amputée des
    # litiges. Un groupeur sans historique part de zéro, pas de cinq — la
    # note doit se gagner.
    total = reputation.campagnes_terminees + reputation.campagnes_annulees
    if total:
        reussite = reputation.campagnes_terminees / total
        penalite = min(reputation.litiges * 0.2, 2)
        reputation.note = max(0, round(reussite * 5 - penalite, 2))
    reputation.save()


FRAIS_PLATEFORME = settings.FRAIS_PLATEFORME_FCFA
