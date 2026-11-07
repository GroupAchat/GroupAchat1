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
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Participation
from groupachat.comptes import parrainage, points
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
    participation.save(
        update_fields=["statut", "payee_le", "code_retrait", "code_otp_sms"]
    )

    sequestre = sequestre_de(campagne)
    sequestre.montant_consigne += participation.montant_total
    sequestre.save(update_fields=["montant_consigne"])

    # Les points de l'acheteur. L'attribution porte la participation : si le
    # paiement est rejoué, elle ne comptera pas deux fois.
    points.attribuer(
        participation.acheteur,
        points.Motif.ACHAT,
        "participation",
        participation.id,
    )

    # Le parrainage se joue **ici** et nulle part ailleurs : un clic ou une
    # inscription sans achat ne valent rien, et un paiement refusé n'arrive
    # jamais jusqu'à cette ligne.
    parrainage.valider_au_paiement(participation)

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
        lien=f"/mes-achats/{participation.id}",
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
def ajuster_les_prix(campagne: Campagne) -> int:
    """Applique la chute de prix à **tous** les participants, et rend la différence.

    C'est le cœur du mécanisme de partage. Un acheteur n'a de raison de faire
    venir ses amis que si la baisse le concerne lui aussi : une chute
    réservée aux derniers arrivés punirait celui qui a commandé le premier,
    c'est-à-dire exactement celui qu'on veut récompenser. La part déjà payée
    est donc recalculée au nombre final de participants, et le surplus
    revient à l'acheteur.

    Le prix ne peut que **descendre** : la tranche choisie par l'acheteur est
    figée à la commande, et une chute non atteinte reste sans effet. Personne
    ne se voit jamais réclamer un complément.

    Appelé à la clôture, une fois le compte des participants arrêté. Rendre
    la différence en cours de collecte n'aurait pas de sens : le nombre peut
    encore monter, et on rembourserait plusieurs fois la même part.

    Rend le nombre de participations ajustées.
    """
    participants = campagne.nombre_participants
    ajustees = 0

    for participation in campagne.participations.filter(
        statut__in=Participation.STATUTS_PAYES
    ).select_related("acheteur"):
        nouveau = campagne.prix_pour(participation.quantite, participants)
        if nouveau >= participation.prix_unitaire_applique:
            continue

        surplus = (participation.prix_unitaire_applique - nouveau) * participation.quantite
        ancien = participation.prix_unitaire_applique
        participation.prix_unitaire_applique = nouveau
        participation.montant_total -= surplus
        participation.save(update_fields=["prix_unitaire_applique", "montant_total"])

        _rendre_le_surplus(participation, surplus, ancien, nouveau, participants)
        ajustees += 1

    return ajustees


def _rendre_le_surplus(
    participation: Participation,
    surplus: int,
    ancien: int,
    nouveau: int,
    participants: int,
) -> None:
    """Renvoie la différence et sort la somme du séquestre.

    Un remboursement partiel, et non une annulation : la part reste payée,
    la commande suit son cours, seule une fraction repart. Le séquestre doit
    le savoir, faute de quoi le groupeur se verrait décaisser un argent qui
    n'est plus à lui.
    """
    operateur = (
        Transaction.objects.filter(participation=participation)
        .values_list("operateur", flat=True)
        .first()
        or "tmoney"
    )
    _, reference = _executer_paiement(
        surplus, participation.acheteur.telephone, operateur
    )
    Transaction.objects.create(
        participation=participation,
        sens=Transaction.Sens.REMBOURSEMENT,
        montant=surplus,
        operateur=operateur,
        numero=participation.acheteur.telephone,
        reference=reference,
        statut=Transaction.Statut.CONFIRMEE,
        confirmee_le=timezone.now(),
    )

    sequestre = sequestre_de(participation.campagne)
    sequestre.montant_rembourse += surplus
    sequestre.save(update_fields=["montant_rembourse"])

    Notification.objects.create(
        destinataire=participation.acheteur,
        genre=Notification.Genre.REMBOURSEMENT,
        titre="Le prix a baissé",
        message=(
            f"Vous étiez {participants} participants : la pièce passe de "
            f"{ancien} à {nouveau} FCFA. {surplus} FCFA vous sont rendus."
        ),
        campagne=participation.campagne,
    )


@transaction.atomic
def cloturer(campagne: Campagne) -> str:
    """Ferme la collecte à la date limite et décide de la suite.

    Deux issues, et une seule est définitive :

    - **minimum atteint** → la campagne est financée, le groupeur peut
      demander ses fonds ;
    - **minimum manqué** → la campagne passe en attente de décision. Elle
      quitte le catalogue, les participants sont prévenus que le groupage
      n'a pas abouti, **mais l'argent ne repart pas**.

    ⚠️ **Le remboursement automatique à la date limite serait une erreur
    produit.** Un groupeur peut très bien décider de maintenir la commande
    malgré le nombre — parce qu'il a déjà négocié avec son fournisseur, ou
    parce qu'il complète de sa poche. Rembourser d'office lui retirerait
    cette possibilité et ferait échouer des groupages qui auraient abouti.
    """
    if campagne.statut != Campagne.Statut.EN_COURS:
        return campagne.statut

    sequestre = sequestre_de(campagne)
    campagne.cloturee_le = timezone.now()

    if campagne.minimum_atteint:
        # Le compte des participants est arrêté : on applique la chute de
        # prix avant tout le reste, pour que le séquestre et les
        # notifications parlent des montants définitifs.
        ajuster_les_prix(campagne)
        campagne.statut = Campagne.Statut.FINANCEE
        sequestre.statut = Sequestre.Statut.BLOQUE
        sequestre.save(update_fields=["statut"])
        campagne.save(update_fields=["statut", "cloturee_le"])
        _prevenir_participants(
            campagne,
            Notification.Genre.CAMPAGNE_FINANCEE,
            "Campagne financée",
            f"« {campagne.titre} » a atteint son objectif. "
            "L'OAG va s'approvisionner.",
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

    # Minimum manqué : on ferme, on prévient, on attend le groupeur.
    campagne.statut = Campagne.Statut.MINIMUM_NON_ATTEINT
    campagne.save(update_fields=["statut", "cloturee_le"])
    sequestre.statut = Sequestre.Statut.BLOQUE
    sequestre.save(update_fields=["statut"])

    manque = max(0, campagne.quantite_minimale - campagne.quantite_reservee)
    _prevenir_participants(
        campagne,
        Notification.Genre.GROUPAGE_NON_ABOUTI,
        "Le groupage n'a pas abouti",
        f"« {campagne.titre} » s'est terminée à {campagne.quantite_reservee} "
        f"pièces sur {campagne.quantite_minimale} — il en manquait {manque}. "
        "Votre paiement n'est pas renvoyé pour autant : le groupeur peut "
        "encore décider de maintenir la commande. Vous serez prévenu de sa "
        "décision.",
    )
    Notification.objects.create(
        destinataire=campagne.groupeur,
        genre=Notification.Genre.DECISION_ATTENDUE,
        titre="Décision attendue",
        message=(
            f"« {campagne.titre} » s'est close à {campagne.quantite_reservee} "
            f"pièces sur {campagne.quantite_minimale}. Maintenez-vous la "
            f"commande ? Sans réponse sous {settings.DELAI_DECISION_JOURS} "
            "jours, les participants seront remboursés."
        ),
        campagne=campagne,
        lien=f"/groupeur/campagnes/{campagne.id}",
    )
    return campagne.statut


@transaction.atomic
def maintenir(campagne: Campagne) -> Campagne:
    """Le groupeur maintient la commande malgré le minimum manqué.

    La campagne rejoint le cours normal : elle est financée, et la suite —
    décaissement, approvisionnement, distribution — ne change pas.
    """
    if campagne.statut != Campagne.Statut.MINIMUM_NON_ATTEINT:
        raise ErreurPaiement("Cette campagne n'attend pas de décision.")

    # Même si le minimum a été manqué, une chute de prix a pu être franchie :
    # elle est due.
    ajuster_les_prix(campagne)
    campagne.statut = Campagne.Statut.FINANCEE
    campagne.save(update_fields=["statut"])

    _prevenir_participants(
        campagne,
        Notification.Genre.CAMPAGNE_MAINTENUE,
        "Le groupage est maintenu",
        f"Bonne nouvelle : le groupeur maintient « {campagne.titre} » malgré "
        "le nombre. Votre commande suit son cours.",
    )
    return campagne


@transaction.atomic
def annuler(campagne: Campagne, motif: str = "") -> Campagne:
    """Annule la campagne et rend sa mise à chaque participant.

    Seule porte de sortie vers le remboursement : ni la clôture ni le temps
    qui passe ne remboursent d'eux-mêmes — il faut une décision, celle du
    groupeur, celle de l'équipe, ou celle de la tâche d'échéance.
    """
    if campagne.statut not in (
        Campagne.Statut.MINIMUM_NON_ATTEINT,
        Campagne.Statut.EN_COURS,
        Campagne.Statut.FINANCEE,
    ):
        raise ErreurPaiement("Cette campagne ne peut plus être annulée.")

    campagne.statut = Campagne.Statut.ANNULEE
    campagne.motif_annulation = motif or "Groupage non abouti."
    if campagne.cloturee_le is None:
        campagne.cloturee_le = timezone.now()
    campagne.save(update_fields=["statut", "motif_annulation", "cloturee_le"])

    _prevenir_participants(
        campagne,
        Notification.Genre.CAMPAGNE_ANNULEE,
        "Groupage annulé",
        f"« {campagne.titre} » n'aboutira pas. Vous êtes intégralement "
        "remboursé, sans rien avoir à demander.",
    )
    for participation in campagne.participations.filter(
        statut=Participation.Statut.PAYEE
    ).select_related("acheteur"):
        rembourser(participation, motif="groupage non abouti")

    sequestre = sequestre_de(campagne)
    sequestre.refresh_from_db()
    sequestre.statut = Sequestre.Statut.REMBOURSE
    sequestre.solde_le = timezone.now()
    sequestre.save(update_fields=["statut", "solde_le"])

    # La réputation retient aussi les campagnes qui n'ont pas abouti : une
    # note qui ne peut que monter ne dit plus rien de personne.
    from groupachat.comptes.models import Reputation

    reputation, _ = Reputation.objects.get_or_create(groupeur=campagne.groupeur)
    reputation.campagnes_annulees += 1
    reputation.save(update_fields=["campagnes_annulees"])
    return campagne


def _prevenir_participants(campagne, genre, titre, message) -> int:
    """Envoie la même nouvelle à tous ceux qui ont payé."""
    destinataires = campagne.participations.filter(
        statut__in=Participation.STATUTS_PAYES
    ).select_related("acheteur")
    Notification.objects.bulk_create(
        [
            Notification(
                destinataire=part.acheteur,
                genre=genre,
                titre=titre,
                message=message,
                campagne=campagne,
                lien=f"/campagnes/{campagne.id}",
            )
            for part in destinataires
        ]
    )
    return destinataires.count()


# ── Les tâches d'échéance ───────────────────────────────────────────────────
#
# Appelées par `manage.py cloturer_les_campagnes_echues`, à faire tourner
# une fois par heure. Sans elles, une campagne dépassée resterait au
# catalogue et l'argent dormirait sans que personne ne soit prévenu.


def cloturer_les_echus() -> list[tuple[int, str]]:
    """Ferme toutes les collectes dont la date limite est passée."""
    echues = Campagne.objects.filter(
        statut=Campagne.Statut.EN_COURS, date_limite__lte=timezone.now()
    )
    return [(campagne.id, cloturer(campagne)) for campagne in echues]


def rembourser_les_indecis() -> list[int]:
    """Rembourse les campagnes laissées sans décision trop longtemps.

    C'est le garde-fou de la règle « l'argent ne repart pas tout seul » :
    il la borne, sans la contredire. Le groupeur garde tout son délai ;
    passé celui-ci, l'acheteur récupère sa mise sans avoir à réclamer.

    À ``DELAI_DECISION_JOURS = 0``, la tâche ne fait rien : seule une
    décision humaine peut alors débloquer la situation.
    """
    if settings.DELAI_DECISION_JOURS <= 0:
        return []

    limite = timezone.now() - timedelta(days=settings.DELAI_DECISION_JOURS)
    oubliees = Campagne.objects.filter(
        statut=Campagne.Statut.MINIMUM_NON_ATTEINT, cloturee_le__lte=limite
    )
    rendues = []
    for campagne in oubliees:
        annuler(
            campagne,
            motif=(
                f"Sans décision du groupeur {settings.DELAI_DECISION_JOURS} "
                "jours après la clôture."
            ),
        )
        rendues.append(campagne.id)
    return rendues


@transaction.atomic
def demander_decaissement(campagne: Campagne) -> Decaissement:
    """Le groupeur réclame les fonds d'une campagne financée."""
    if campagne.statut != Campagne.Statut.FINANCEE:
        raise ErreurPaiement("Seule une campagne financée peut être décaissée.")
    if Decaissement.objects.filter(campagne=campagne).exists():
        raise ErreurPaiement("Un décaissement a déjà été demandé.")

    sequestre = sequestre_de(campagne)
    # Le taux se lit au moment du calcul et se fige dans le décaissement :
    # un groupeur qui monte en grade la semaine suivante ne fait pas
    # recalculer un retrait déjà chiffré.
    compteur = points.compteur_de(campagne.groupeur)
    taux = compteur.commission_centiemes
    frais, net = Decaissement.calculer(sequestre.solde, taux)
    dossier = getattr(campagne.groupeur, "dossier_kyc", None)
    return Decaissement.objects.create(
        campagne=campagne,
        montant_brut=sequestre.solde,
        frais=frais,
        montant_net=net,
        taux_commission=taux,
        grade_applique=compteur.grade,
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
def _message_de_disposition(campagne: Campagne, participation) -> str:
    """Ce que lit l'acheteur quand son lot arrive.

    Le message dit **sa** destination, pas celle de la campagne : lui envoyer
    « à retirer au bureau de poste » alors qu'il a demandé la livraison le
    ferait sortir pour rien. Et les frais de livraison sont annoncés ici,
    parce qu'ils se paient à l'agence et jamais à nous.
    """
    if participation.mode_retrait == Participation.ModeRetrait.LIVRAISON:
        return (
            f"« {campagne.titre} » part en livraison à votre adresse. "
            f"Les frais de livraison sont à régler à l'agence à la remise. "
            f"Gardez votre code : {participation.code_retrait}."
        )
    return (
        f"« {campagne.titre} » est à retirer au {participation.bureau_poste}. "
        f"Présentez votre code : {participation.code_retrait}."
    )


def mettre_a_disposition(campagne: Campagne) -> int:
    """L'OAG annonce que la marchandise est arrivée.

    C'est le geste qui déclenche la distribution : **tous les participants
    sont notifiés**, chacun avec la destination qu'il a lui-même choisie et le
    rappel de son code. Il n'y a pas de lieu commun à annoncer — l'un passe
    au bureau de poste de son quartier, l'autre se fait livrer.
    """
    if campagne.statut not in (
        Campagne.Statut.APPROVISIONNEMENT,
        Campagne.Statut.DECAISSEE,
        Campagne.Statut.FINANCEE,
    ):
        raise ErreurPaiement("Cette campagne n'en est pas à la distribution.")

    campagne.statut = Campagne.Statut.DISTRIBUTION
    campagne.mise_a_disposition_le = timezone.now()
    campagne.save(update_fields=["statut", "mise_a_disposition_le"])

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
                message=_message_de_disposition(campagne, participation),
                campagne=campagne,
                lien=f"/mes-achats/{participation.id}",
            )
        )
    Notification.objects.bulk_create(notifications)
    participations.update(statut=Participation.Statut.PRETE)
    return len(notifications)


def code_du_scan(saisie: str) -> str:
    """Le code, qu'il soit dicté ou lu dans un QR.

    Un QR scanné arrive sous la forme `GA|<campagne>|<code>`. Le code y est
    lisible à l'œil **à dessein** : un téléphone dont l'appareil photo ne
    marche pas doit pouvoir le dicter.
    """
    propre = (saisie or "").strip().upper()
    if propre.startswith("GA|"):
        morceaux = propre.split("|")
        if len(morceaux) != 3:
            raise ErreurPaiement("Ce QR code n'est pas lisible.")
        return morceaux[2]
    return propre


@transaction.atomic
def remettre_le_colis(saisie: str, livreur) -> Participation:
    """Le livreur scanne, le colis est remis.

    **Le code est cherché partout, pas dans une campagne.** Un livreur porte
    dans la même tournée les colis de plusieurs groupages : lui demander de
    choisir d'abord la campagne, c'est lui demander une information qu'il n'a
    pas — il a un paquet et un code, rien d'autre. Les codes sont uniques sur
    toute la plateforme, la recherche directe suffit.

    C'est **l'agence qui remet**, jamais l'OAG : celui-ci confie le lot en
    bloc et ne rencontre pas ses acheteurs. S'il validait lui-même, la preuve
    de livraison ne prouverait plus rien — celui qui doit livrer signerait sa
    propre livraison.
    """
    code = code_du_scan(saisie)

    participation = (
        Participation.objects.select_for_update()
        .select_related("campagne", "acheteur")
        .filter(models.Q(code_retrait=code) | models.Q(code_otp_sms=code))
        .first()
    )
    if participation is None:
        raise ErreurPaiement("Code inconnu.")
    if participation.statut == Participation.Statut.RETIREE:
        raise ErreurPaiement(
            f"Colis déjà remis le {participation.retiree_le:%d/%m/%Y à %H:%M}."
        )
    if participation.statut != Participation.Statut.PRETE:
        raise ErreurPaiement("Ce colis n'est pas encore prêt à être remis.")

    campagne = participation.campagne
    participation.statut = Participation.Statut.RETIREE
    participation.retiree_le = timezone.now()
    participation.remise_par = livreur
    participation.save(update_fields=["statut", "retiree_le", "remise_par"])

    porteur = livreur.get_transporteur_display() if livreur.transporteur else "l'agence"
    Notification.objects.create(
        destinataire=participation.acheteur,
        genre=Notification.Genre.RETRAIT_CONFIRME,
        titre="Colis remis",
        message=(
            f"Votre part de « {campagne.titre} » vous a été remise par "
            f"{porteur}. Merci !"
        ),
        campagne=campagne,
        lien=f"/mes-achats/{participation.id}",
    )

    # L'OAG apprend la remise **ici** : c'est le scan du livreur qui lui dit
    # que telle personne a bien reçu son colis. Sans cette ligne, il devrait
    # appeler l'agence pour savoir où en est sa distribution.
    Notification.objects.create(
        destinataire=campagne.groupeur,
        genre=Notification.Genre.RETRAIT_CONFIRME,
        titre="Colis remis à un acheteur",
        message=(
            f"{participation.acheteur.nom_public} a reçu sa part de "
            f"« {campagne.titre} » ({porteur})."
        ),
        campagne=campagne,
        lien=f"/groupeur/campagnes/{campagne.id}",
    )

    # Dernier colis remis : la campagne est terminée et la réputation de
    # l'OAG en tient compte.
    if not campagne.participations.filter(statut=Participation.Statut.PRETE).exists():
        campagne.statut = Campagne.Statut.TERMINEE
        campagne.save(update_fields=["statut"])
        _crediter_reputation(campagne)

    return participation


def _crediter_reputation(campagne: Campagne) -> None:
    """Enregistre le volume d'activité d'un groupeur à la fin d'une campagne.

    ⚠️ **Cette fonction ne touche pas à la note.** Celle-ci vient des avis
    laissés par les acheteurs — la plateforme met en relation, elle ne juge
    pas. Ce qu'on compte ici, c'est le volume : combien de campagnes menées
    à terme, combien de personnes servies. Les deux s'affichent côte à
    côte, et l'acheteur fait la part des choses.
    """
    from groupachat.comptes.models import Reputation

    reputation, _ = Reputation.objects.get_or_create(groupeur=campagne.groupeur)
    reputation.campagnes_terminees += 1
    reputation.participants_servis += campagne.participations.filter(
        statut=Participation.Statut.RETIREE
    ).count()
    reputation.save(update_fields=["campagnes_terminees", "participants_servis"])

    # **Aucun point pour le groupage abouti.** Le cahier des charges v2 a
    # tranché : les points récompensent l'acheteur et le parrainage, pas le
    # volume d'affaires de l'OAG. Le grade reste donc un parcours de fidélité
    # et d'ancienneté, et non une prime au chiffre.


def recalculer_reputation(groupeur) -> None:
    """Recalcule la note d'un groupeur à partir des avis reçus.

    **Ce sont les acheteurs qui notent, pas la plateforme.** Group
    Achat met en relation ; elle ne juge pas la qualité d'un produit.
    La note moyenne est donc celle des avis, point.

    Sans aucun avis, la note reste à zéro : un groupeur qui débute n'a
    pas cinq étoiles par défaut, il n'a pas encore de réputation. Les
    compteurs de campagnes, eux, disent le volume — ils s'affichent à
    côté de la note et laissent l'acheteur faire la part des choses
    entre « 5/5 sur un avis » et « 4,2/5 sur quarante ».
    """
    from django.db.models import Avg, Count

    from groupachat.commandes.models import Avis
    from groupachat.comptes.models import Reputation

    reputation, _ = Reputation.objects.get_or_create(groupeur=groupeur)
    mesure = Avis.objects.filter(
        participation__campagne__groupeur=groupeur
    ).aggregate(moyenne=Avg("note"), nombre=Count("id"))

    reputation.note = round(mesure["moyenne"] or 0, 2)
    reputation.avis_recus = mesure["nombre"]
    reputation.save()


