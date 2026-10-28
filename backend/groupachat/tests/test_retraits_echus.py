# -*- coding: utf-8 -*-
"""F-031 : relances de retrait à J+3 et J+7, livraison réputée acquise à J+14.

Un seul acheteur qui ne vient pas chercher son colis laissait la campagne en
distribution pour toujours, et la réputation du groupeur n'était jamais
créditée. Ces tests couvrent les relances, la clôture à J+14 (préavis de 72 h,
garde des fonds consignés, retrait tardif), la commande planifiée, l'API, et
les courses de verrous (C-052, `valider_retrait`) qui exigent PostgreSQL.

Le temps se règle en reculant `mise_a_disposition_le` : on n'attend jamais.
« Pile » = exactement N jours ; « la veille » = N jours moins une minute.
"""

from __future__ import annotations

import logging
import threading
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError, OperationalError, connection, transaction
from django.utils import timezone

from groupachat.catalogue.management.commands.charger_demo import VERSION_DEMO
from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Avis, Participation
from groupachat.commandes.tests import participer_et_payer
from groupachat.comptes.models import Reputation, Utilisateur
from groupachat.echanges.models import Notification
from groupachat.paiements.models import Sequestre, Transaction
from groupachat.paiements.retraits import (
    relancer_les_retraits,
    relancer_retrait,
    reputer_livree,
    reputer_livrees_les_echues,
)
from groupachat.paiements.services import (
    ErreurPaiement,
    annuler,
    cloturer,
    demander_decaissement,
    executer_decaissement,
    mettre_a_disposition,
    valider_retrait,
    _verrouiller_sequestre,
)

pytestmark = pytest.mark.django_db

ABSENT_HORS_POSTGRES = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="SQLite ignore select_for_update : la course n'y est pas reproductible",
)

J3 = timedelta(days=3)
J7 = timedelta(days=7)
J14 = timedelta(days=14)
UNE_MINUTE = timedelta(minutes=1)


# ── Aides ───────────────────────────────────────────────────────────────────


@pytest.fixture
def cas(connecte, campagne, administrateur):
    """Campagne en distribution par le vrai parcours : A1 4 pièces, A2 3, A3 2, A4 1."""
    acheteurs = [
        Utilisateur.objects.create_user(
            f"9100000{i}", "mdpSolide2026", nom=f"Acheteur{i}", prenom="Test",
            telephone_verifie=True,
        )
        for i in range(1, 5)
    ]
    campagne.point_remise = "Boutique Abalo"
    campagne.save(update_fields=["point_remise"])
    for acheteur, quantite in zip(acheteurs, (4, 3, 2, 1)):
        participer_et_payer(connecte, acheteur, campagne, quantite=quantite)
    cloturer(campagne)
    executer_decaissement(demander_decaissement(campagne), administrateur)
    mettre_a_disposition(campagne, "Boutique Abalo")
    campagne.refresh_from_db()
    parts = [
        Participation.objects.get(campagne=campagne, acheteur=a) for a in acheteurs
    ]
    return SimpleNamespace(campagne=campagne, acheteurs=acheteurs, parts=parts)


def _reculer(campagne, delta):
    # L'instance du test suit la base : les messages se comparent à sa date.
    campagne.mise_a_disposition_le = timezone.now() - delta
    Campagne.objects.filter(pk=campagne.pk).update(
        mise_a_disposition_le=campagne.mise_a_disposition_le
    )


def _poser_relances(campagne, j3=None, j7=None):
    """Date les relances comme si elles étaient parties il y a `j3` / `j7`."""
    maintenant = timezone.now()
    Campagne.objects.filter(pk=campagne.pk).update(
        relance_retrait_j3_le=maintenant - j3 if j3 else None,
        relance_retrait_j7_le=maintenant - j7 if j7 else None,
    )


def _a_j_plus_14_avec_relances(cas):
    _reculer(cas.campagne, J14)
    _poser_relances(cas.campagne, j3=J14 - J3, j7=J7)


def _tache(*options) -> str:
    sortie = StringIO()
    call_command("cloturer_les_campagnes_echues", *options, stdout=sortie)
    return sortie.getvalue()


def _forcer(part, **champs):
    Participation.objects.filter(pk=part.pk).update(**champs)


def _statut(part) -> str:
    return Participation.objects.get(pk=part.pk).statut


def _retirer(cas, indice):
    part = Participation.objects.get(pk=cas.parts[indice].pk)
    return valider_retrait(cas.campagne, part.code_retrait, cas.campagne.groupeur)


def _reputation(campagne) -> Reputation:
    return Reputation.objects.get(groupeur=campagne.groupeur)


def _relances(campagne=None):
    filtre = Notification.objects.filter(genre=Notification.Genre.RELANCE_RETRAIT)
    return filtre.filter(campagne=campagne) if campagne else filtre


def _empreinte(campagne) -> dict:
    """Tout ce que la tâche pourrait écrire, pour prouver qu'elle n'a rien écrit."""
    campagne = Campagne.objects.get(pk=campagne.pk)
    sequestre = Sequestre.objects.get(campagne=campagne)
    reputation = _reputation(campagne)
    return {
        "notifications": Notification.objects.count(),
        "transactions": Transaction.objects.count(),
        "statut_campagne": campagne.statut,
        "relances": (campagne.relance_retrait_j3_le, campagne.relance_retrait_j7_le),
        "parts": sorted(
            Participation.objects.filter(campagne=campagne).values_list("id", "statut")
        ),
        "sequestre": (sequestre.montant_consigne, sequestre.montant_libere,
                      sequestre.montant_rembourse, sequestre.statut),
        "reputation": (reputation.campagnes_terminees, reputation.participants_servis,
                       reputation.avis_recus, str(reputation.note)),
    }


# ── Relances ────────────────────────────────────────────────────────────────


class TestRelances:
    def test_rien_n_est_envoye_avant_le_troisieme_jour(self, cas):
        _reculer(cas.campagne, J3 - UNE_MINUTE)

        sortie = _tache()

        assert not _relances().exists()
        cas.campagne.refresh_from_db()
        assert cas.campagne.relance_retrait_j3_le is None
        assert cas.campagne.relance_retrait_j7_le is None
        assert "0 relance(s)" in sortie

    def test_la_premiere_relance_part_pile_a_j_plus_3(self, cas):
        a1, a2, a3, a4 = cas.parts
        _forcer(a3, statut=Participation.Statut.RETIREE, retiree_le=timezone.now())
        _forcer(a4, statut=Participation.Statut.REMBOURSEE)
        _reculer(cas.campagne, J3)

        _tache()

        relances = _relances(cas.campagne)
        assert relances.count() == 2
        assert set(relances.values_list("destinataire_id", flat=True)) == {
            cas.acheteurs[0].id, cas.acheteurs[1].id}
        echeance = f"{cas.campagne.mise_a_disposition_le + J14:%d/%m/%Y}"
        for part in (a1, a2):
            relance = relances.get(destinataire=part.acheteur)
            assert relance.titre == "Votre colis vous attend"
            assert relance.lien == f"/mes-achats/{part.id}"
            assert cas.campagne.titre in relance.message
            assert "Boutique Abalo" in relance.message
            assert part.code_retrait in relance.message, "le code de CETTE part"
            assert echeance in relance.message
        cas.campagne.refresh_from_db()
        assert cas.campagne.relance_retrait_j3_le is not None
        assert cas.campagne.relance_retrait_j7_le is None
        assert cas.campagne.statut == Campagne.Statut.DISTRIBUTION

    def test_une_part_retiree_rembourse_ou_en_attente_n_est_pas_relancee(self, cas):
        for part, statut in zip(cas.parts, ("retiree", "remboursee", "annulee",
                                            "en_attente_paiement")):
            _forcer(part, statut=statut)
        _reculer(cas.campagne, J3)

        _tache()

        assert not _relances().exists()

    def test_deux_passages_le_meme_jour_n_envoient_qu_une_relance(self, cas):
        _reculer(cas.campagne, J3)
        _tache()
        posee = Campagne.objects.get(pk=cas.campagne.pk).relance_retrait_j3_le

        _tache()
        _tache()

        assert _relances().count() == 4
        assert Campagne.objects.get(pk=cas.campagne.pk).relance_retrait_j3_le == posee

    def test_rien_de_plus_la_veille_du_septieme_jour(self, cas):
        _reculer(cas.campagne, J3)
        _tache()
        _reculer(cas.campagne, J7 - UNE_MINUTE)

        _tache()

        assert _relances().count() == 4
        assert Campagne.objects.get(pk=cas.campagne.pk).relance_retrait_j7_le is None

    def test_la_seconde_relance_part_pile_a_j_plus_7(self, cas):
        _reculer(cas.campagne, J3)
        _tache()
        _reculer(cas.campagne, J7)
        j3 = Campagne.objects.get(pk=cas.campagne.pk).relance_retrait_j3_le

        _tache()

        derniere = _relances().filter(titre="Dernier rappel : colis à retirer")
        assert derniere.count() == 4
        un = derniere.get(destinataire=cas.acheteurs[0])
        assert "réputée faite" in un.message
        assert cas.parts[0].code_retrait in un.message
        campagne = Campagne.objects.get(pk=cas.campagne.pk)
        assert campagne.relance_retrait_j7_le is not None
        assert campagne.relance_retrait_j3_le == j3
        _tache()
        assert _relances().count() == 8, "repasser n'envoie rien de plus"

    def test_apres_une_panne_seule_la_relance_la_plus_avancee_part(self, cas):
        _reculer(cas.campagne, timedelta(days=8))

        _tache()

        relances = _relances()
        assert relances.count() == 4
        assert set(relances.values_list("titre", flat=True)) == {
            "Dernier rappel : colis à retirer"}
        campagne = Campagne.objects.get(pk=cas.campagne.pk)
        assert campagne.relance_retrait_j7_le is not None
        assert campagne.relance_retrait_j3_le is None, "la J+3 arriverait en retard"
        _reculer(cas.campagne, timedelta(days=9))
        _tache()
        assert _relances().count() == 4

    def test_une_etape_sans_destinataire_est_quand_meme_jouee(self, cas):
        for part in cas.parts:
            _forcer(part, statut=Participation.Statut.RETIREE,
                    retiree_le=timezone.now())
        _reculer(cas.campagne, J3)

        _tache()

        assert not _relances().exists()
        posee = Campagne.objects.get(pk=cas.campagne.pk).relance_retrait_j3_le
        assert posee is not None
        _tache()
        assert Campagne.objects.get(pk=cas.campagne.pk).relance_retrait_j3_le == posee

    def test_une_campagne_terminee_annulee_ou_en_approvisionnement_n_est_pas_relancee(
        self, cas
    ):
        _reculer(cas.campagne, timedelta(days=5))
        for statut in (Campagne.Statut.TERMINEE, Campagne.Statut.ANNULEE,
                       Campagne.Statut.APPROVISIONNEMENT):
            Campagne.objects.filter(pk=cas.campagne.pk).update(statut=statut)

            assert relancer_les_retraits() == []
            assert relancer_retrait(cas.campagne) is None

        assert not _relances().exists()
        campagne = Campagne.objects.get(pk=cas.campagne.pk)
        assert campagne.relance_retrait_j3_le is None
        assert campagne.relance_retrait_j7_le is None

    def test_pas_de_relance_ordinaire_au_dela_de_j_plus_14(self, cas):
        _reculer(cas.campagne, J14)
        _poser_relances(cas.campagne, j3=J14 - J3, j7=J7)

        assert relancer_retrait(cas.campagne) is None
        assert relancer_les_retraits() == []


# ── Livraison réputée à J+14 ────────────────────────────────────────────────


class TestLivraisonReputee:
    def test_rien_ne_bouge_la_veille_du_quatorzieme_jour(self, cas):
        _retirer(cas, 0)
        _reculer(cas.campagne, J14 - UNE_MINUTE)
        _poser_relances(cas.campagne, j3=J7, j7=J7)
        avant = _empreinte(cas.campagne)

        sortie = _tache()

        assert _empreinte(cas.campagne) == avant
        assert "0 campagne(s) close(s) à J+14" in sortie
        assert not Notification.objects.filter(
            genre__in=["livraison_reputee", "campagne_terminee"]).exists()

    def test_a_j_plus_14_pile_les_parts_non_retirees_sont_reputees_livrees(self, cas):
        a1, a2, a3, a4 = cas.parts
        _retirer(cas, 0)
        retiree = Participation.objects.get(pk=a1.pk)
        _forcer(a4, statut=Participation.Statut.REMBOURSEE)
        _a_j_plus_14_avec_relances(cas)

        sortie = _tache()

        for part in (a2, a3):
            relue = Participation.objects.get(pk=part.pk)
            assert relue.statut == Participation.Statut.REPUTEE_LIVREE
            assert relue.reputee_livree_le is not None
            assert relue.retiree_le is None
        intacte = Participation.objects.get(pk=a1.pk)
        assert intacte.statut == Participation.Statut.RETIREE
        assert (intacte.retiree_le, intacte.remise_par_id) == (
            retiree.retiree_le, retiree.remise_par_id)
        assert intacte.reputee_livree_le is None
        assert _statut(a4) == Participation.Statut.REMBOURSEE
        assert "1 campagne(s) close(s) à J+14" in sortie

    def test_la_campagne_passe_terminee(self, cas):
        _a_j_plus_14_avec_relances(cas)

        assert reputer_livrees_les_echues() == [cas.campagne.id]

        cas.campagne.refresh_from_db()
        assert cas.campagne.statut == Campagne.Statut.TERMINEE

    def test_la_reputation_compte_la_campagne_mais_pas_les_parts_non_retirees(self, cas):
        _retirer(cas, 0)
        avant = _reputation(cas.campagne)
        _a_j_plus_14_avec_relances(cas)

        _tache()

        apres = _reputation(cas.campagne)
        assert apres.campagnes_terminees == avant.campagnes_terminees + 1
        assert apres.participants_servis == avant.participants_servis + 1
        assert (apres.note, apres.avis_recus) == (avant.note, avant.avis_recus)

    def test_personne_n_est_venu_la_campagne_se_termine_sans_participant_servi(
        self, cas
    ):
        avant = _reputation(cas.campagne).participants_servis
        _a_j_plus_14_avec_relances(cas)

        _tache()

        assert [_statut(p) for p in cas.parts] == ["reputee_livree"] * 4
        assert _reputation(cas.campagne).campagnes_terminees == 1
        assert _reputation(cas.campagne).participants_servis == avant
        message = Notification.objects.get(
            genre=Notification.Genre.CAMPAGNE_TERMINEE).message
        assert "4 colis non retiré(s)" in message
        assert "0 participant(s) servi(s)" in message

    def test_un_second_passage_ne_credite_pas_deux_fois(self, cas):
        _retirer(cas, 0)
        _a_j_plus_14_avec_relances(cas)
        _tache()
        apres = _empreinte(cas.campagne)
        dates = list(Participation.objects.values_list("reputee_livree_le", flat=True))

        _tache()
        _tache()

        assert _empreinte(cas.campagne) == apres
        assert list(
            Participation.objects.values_list("reputee_livree_le", flat=True)) == dates

    def test_une_campagne_deja_terminee_n_est_pas_touchee(self, cas):
        for indice in range(4):
            _retirer(cas, indice)
        assert _reputation(cas.campagne).campagnes_terminees == 1
        _reculer(cas.campagne, timedelta(days=20))
        avant = _empreinte(cas.campagne)

        _tache()

        assert _empreinte(cas.campagne) == avant
        with pytest.raises(ErreurPaiement):
            reputer_livree(cas.campagne)

    def test_une_part_annulee_ou_remboursee_reste_telle_quelle(self, cas):
        _forcer(cas.parts[2], statut=Participation.Statut.REMBOURSEE)
        _forcer(cas.parts[3], statut=Participation.Statut.ANNULEE)
        _a_j_plus_14_avec_relances(cas)

        _tache()

        assert [_statut(p) for p in cas.parts] == [
            "reputee_livree", "reputee_livree", "remboursee", "annulee"]

    def test_la_jauge_et_le_montant_collecte_ne_baissent_pas(
        self, connecte, cas
    ):
        def lire():
            donnees = connecte(cas.campagne.groupeur).get(
                f"/api/groupeur/campagnes/{cas.campagne.id}/").data
            return (donnees["quantite_reservee"], donnees["montant_collecte"],
                    donnees["nombre_participants"])

        avant = lire()
        _a_j_plus_14_avec_relances(cas)

        _tache()

        assert lire() == avant == (10, 180000, 4)

    def test_le_sequestre_n_est_pas_touche(self, cas):
        avant = _empreinte(cas.campagne)["sequestre"]
        transactions = Transaction.objects.count()
        _a_j_plus_14_avec_relances(cas)

        _tache()

        sequestre = Sequestre.objects.get(campagne=cas.campagne)
        assert (sequestre.montant_consigne, sequestre.montant_libere,
                sequestre.montant_rembourse, sequestre.statut) == avant == (
            180000, 180000, 0, Sequestre.Statut.LIBERE)
        assert Transaction.objects.count() == transactions

    def test_l_acheteur_et_le_groupeur_sont_prevenus(self, cas):
        _retirer(cas, 0)
        _forcer(cas.parts[3], statut=Participation.Statut.REMBOURSEE)
        avant = Notification.objects.count()
        _a_j_plus_14_avec_relances(cas)

        _tache()

        livraisons = Notification.objects.filter(genre="livraison_reputee")
        assert set(livraisons.values_list("destinataire_id", flat=True)) == {
            cas.acheteurs[1].id, cas.acheteurs[2].id}
        for part in cas.parts[1:3]:
            note = livraisons.get(destinataire=part.acheteur)
            assert note.titre == "Délai de retrait écoulé"
            assert note.lien == f"/mes-achats/{part.id}"
            assert "votre code reste valable" in note.message
        groupeur = Notification.objects.get(genre="campagne_terminee")
        assert groupeur.destinataire == cas.campagne.groupeur
        assert groupeur.titre == "Campagne terminée"
        assert groupeur.lien == f"/groupeur/campagnes/{cas.campagne.id}"
        assert "2 colis non retiré(s)" in groupeur.message
        assert "1 participant(s) servi(s)" in groupeur.message
        assert Notification.objects.count() == avant + 3, "A1 et A4 : rien"

    def test_sans_relance_prealable_la_cloture_attend_le_preavis(self, cas):
        _reculer(cas.campagne, timedelta(days=20))

        _tache()

        assert _relances().filter(
            titre="Dernier rappel : colis à retirer").count() == 4
        assert [_statut(p) for p in cas.parts] == ["prete"] * 4
        campagne = Campagne.objects.get(pk=cas.campagne.pk)
        assert campagne.statut == Campagne.Statut.DISTRIBUTION
        assert campagne.relance_retrait_j7_le is not None
        assert _reputation(cas.campagne).campagnes_terminees == 0
        assert not Notification.objects.filter(genre="livraison_reputee").exists()

        # Le préavis de 72 h court depuis la relance de rattrapage.
        Campagne.objects.filter(pk=cas.campagne.pk).update(
            relance_retrait_j7_le=timezone.now() - timedelta(hours=72) + UNE_MINUTE)
        _tache()
        assert [_statut(p) for p in cas.parts] == ["prete"] * 4
        assert _relances().count() == 4, "pas de seconde relance"

        Campagne.objects.filter(pk=cas.campagne.pk).update(
            relance_retrait_j7_le=timezone.now() - timedelta(hours=72))
        _tache()
        assert [_statut(p) for p in cas.parts] == ["reputee_livree"] * 4
        assert Campagne.objects.get(pk=cas.campagne.pk).statut == "terminee"
        assert _reputation(cas.campagne).campagnes_terminees == 1

    def test_la_seule_relance_j_plus_3_ne_vaut_pas_preavis(self, cas):
        """D3 : seule la relance qui annonce la clôture compte comme préavis."""
        _reculer(cas.campagne, timedelta(days=20))
        _poser_relances(cas.campagne, j3=timedelta(days=15))

        _tache()

        assert [_statut(p) for p in cas.parts] == ["prete"] * 4
        assert Campagne.objects.get(pk=cas.campagne.pk).relance_retrait_j7_le
        assert _relances().filter(
            titre="Dernier rappel : colis à retirer").count() == 4

    def test_une_campagne_dont_les_fonds_sont_encore_consignes_n_est_pas_close(
        self, cas, caplog
    ):
        # État forcé : le chemin financée → distribution est fermé depuis F-024.
        Sequestre.objects.filter(campagne=cas.campagne).update(montant_libere=0)
        _a_j_plus_14_avec_relances(cas)
        avant = _empreinte(cas.campagne)

        with caplog.at_level(logging.WARNING, logger="groupachat.paiements.retraits"):
            sortie = _tache()
            _tache()

        assert _empreinte(cas.campagne) == avant
        assert "0 campagne(s) close(s) à J+14" in sortie
        alertes = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(alertes) == 2, "un avertissement à chaque passage"
        texte = alertes[0].getMessage()
        assert str(cas.campagne.id) in texte
        for secret in ("Acheteur", "Abalo", "9100000", cas.parts[0].code_retrait):
            assert secret not in texte

    def test_une_campagne_bloquee_n_empeche_pas_les_autres(
        self, connecte, cas, produit, ama, yao, administrateur
    ):
        Sequestre.objects.filter(campagne=cas.campagne).update(montant_libere=0)
        _a_j_plus_14_avec_relances(cas)
        saine = Campagne.objects.create(
            produit=produit, groupeur=cas.campagne.groupeur, titre="Seconde",
            prix_unitaire=18000, quantite_minimale=2, point_remise="Lomé",
            date_limite=timezone.now() + timedelta(days=3),
            statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now(),
        )
        participer_et_payer(connecte, ama, saine, quantite=2)
        cloturer(saine)
        executer_decaissement(demander_decaissement(saine), administrateur)
        mettre_a_disposition(saine)
        _reculer(saine, J14)
        _poser_relances(saine, j3=J14 - J3, j7=J7)

        closes = reputer_livrees_les_echues()

        assert closes == [saine.id]
        cas.campagne.refresh_from_db()
        assert cas.campagne.statut == Campagne.Statut.DISTRIBUTION

    def test_une_part_reputee_livree_peut_noter_le_groupeur(self, connecte, cas):
        _a_j_plus_14_avec_relances(cas)
        _tache()
        part = Participation.objects.get(pk=cas.parts[1].pk)
        assert part.peut_etre_notee

        reponse = connecte(cas.acheteurs[1]).post(
            "/api/avis/", {"participation": part.id, "note": 2}, format="json")

        assert reponse.status_code == 201, reponse.data
        reputation = _reputation(cas.campagne)
        assert reputation.avis_recus == 1
        assert float(reputation.note) == 2.0
        deuxieme = connecte(cas.acheteurs[1]).post(
            "/api/avis/", {"participation": part.id, "note": 5}, format="json")
        assert deuxieme.status_code == 400
        assert Avis.objects.count() == 1

    def test_la_contrainte_refuse_une_part_reputee_livree_sans_date(self, cas):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                _forcer(cas.parts[0], statut="reputee_livree",
                        reputee_livree_le=None)

    def test_une_part_retiree_peut_garder_sa_date_de_reputation(self, cas):
        _forcer(cas.parts[0], statut="retiree", retiree_le=timezone.now(),
                reputee_livree_le=timezone.now())

        assert _statut(cas.parts[0]) == "retiree"


# ── Retrait et clôture ──────────────────────────────────────────────────────


class TestRetraitApresEcheance:
    def _terminer_par_la_tache(self, cas):
        _a_j_plus_14_avec_relances(cas)
        _tache()

    def test_le_dernier_code_puis_la_tache_ne_creditent_la_campagne_qu_une_fois(
        self, cas
    ):
        _forcer(cas.parts[3], statut=Participation.Statut.REMBOURSEE)
        for indice in range(3):
            _retirer(cas, indice)
        assert _reputation(cas.campagne).campagnes_terminees == 1
        _a_j_plus_14_avec_relances(cas)

        _tache()

        assert _reputation(cas.campagne).campagnes_terminees == 1
        assert _reputation(cas.campagne).participants_servis == 3

    def test_la_tache_puis_un_code_tardif_ne_creditent_la_campagne_qu_une_fois(
        self, cas
    ):
        self._terminer_par_la_tache(cas)

        _retirer(cas, 1)

        assert _reputation(cas.campagne).campagnes_terminees == 1
        assert _reputation(cas.campagne).participants_servis == 1

    def test_un_code_presente_apres_j_plus_14_est_accepte(self, connecte, cas):
        _retirer(cas, 0)
        self._terminer_par_la_tache(cas)
        part = Participation.objects.get(pk=cas.parts[1].pk)
        date = part.reputee_livree_le
        avant = _reputation(cas.campagne)

        reponse = connecte(cas.campagne.groupeur).post(
            f"/api/groupeur/campagnes/{cas.campagne.id}/retrait/",
            {"code": part.code_retrait}, format="json")

        assert reponse.status_code == 200, reponse.data
        part.refresh_from_db()
        assert part.statut == Participation.Statut.RETIREE
        assert part.retiree_le is not None
        assert part.remise_par == cas.campagne.groupeur
        assert part.reputee_livree_le == date, "la trace est conservée"
        apres = _reputation(cas.campagne)
        assert apres.participants_servis == avant.participants_servis + 1
        assert apres.campagnes_terminees == avant.campagnes_terminees == 1
        cas.campagne.refresh_from_db()
        assert cas.campagne.statut == Campagne.Statut.TERMINEE
        assert Notification.objects.filter(
            destinataire=part.acheteur, genre="retrait_confirme").count() == 1
        assert Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT).count() == 0

    def test_un_code_deja_retire_reste_refuse_apres_la_cloture(self, connecte, cas):
        self._terminer_par_la_tache(cas)
        code = cas.parts[1].code_retrait
        api = connecte(cas.campagne.groupeur)
        adresse = f"/api/groupeur/campagnes/{cas.campagne.id}/retrait/"
        assert api.post(adresse, {"code": code}, format="json").status_code == 200
        avant = _reputation(cas.campagne).participants_servis

        reponse = api.post(adresse, {"code": code}, format="json")

        assert reponse.status_code == 400
        assert "déjà retiré" in reponse.data["detail"]
        assert _reputation(cas.campagne).participants_servis == avant

    def test_un_code_etranger_ou_inconnu_reste_refuse_apres_la_cloture(
        self, connecte, cas
    ):
        self._terminer_par_la_tache(cas)
        adresse = f"/api/groupeur/campagnes/{cas.campagne.id}/retrait/"
        api = connecte(cas.campagne.groupeur)
        avant = _empreinte(cas.campagne)

        inconnu = api.post(adresse, {"code": "ZZZZZZZZ"}, format="json")
        etranger = api.post(adresse, {"code": f"GA|{cas.campagne.id + 99}|ABC"},
                            format="json")

        assert inconnu.status_code == etranger.status_code == 400
        assert inconnu.data["detail"] == "Code inconnu pour cette campagne."
        assert etranger.data["detail"] == "Ce QR code ne concerne pas cette campagne."
        assert _empreinte(cas.campagne) == avant

    def test_seul_le_groupeur_de_la_campagne_valide_un_retrait(
        self, connecte, client, cas, ama
    ):
        self._terminer_par_la_tache(cas)
        adresse = f"/api/groupeur/campagnes/{cas.campagne.id}/retrait/"
        corps = {"code": cas.parts[1].code_retrait}
        avant = _empreinte(cas.campagne)

        assert connecte(ama).post(adresse, corps, format="json").status_code == 403
        client.force_authenticate(user=None)
        assert client.post(adresse, corps, format="json").status_code in (401, 403)
        assert _empreinte(cas.campagne) == avant

    def test_un_retrait_ordinaire_avant_l_echeance_reste_inchange(self, cas):
        _reculer(cas.campagne, timedelta(days=5))

        for indice in range(4):
            _retirer(cas, indice)

        cas.campagne.refresh_from_db()
        assert cas.campagne.statut == Campagne.Statut.TERMINEE
        assert _reputation(cas.campagne).campagnes_terminees == 1
        assert _reputation(cas.campagne).participants_servis == 4

    def test_une_campagne_sans_distribution_refuse_un_code_de_part_prete(self, cas):
        """La part prête d'une campagne qui n'est plus en distribution est refusée."""
        Campagne.objects.filter(pk=cas.campagne.pk).update(
            statut=Campagne.Statut.TERMINEE)

        with pytest.raises(ErreurPaiement, match="distribution de cette campagne"):
            _retirer(cas, 0)

        assert _statut(cas.parts[0]) == "prete"


# ── API ─────────────────────────────────────────────────────────────────────


class TestApi:
    def test_l_acheteur_voit_sa_part_reputee_livree(self, connecte, cas):
        a1, a2 = cas.parts[0], cas.parts[1]
        _a_j_plus_14_avec_relances(cas)
        _tache()

        reponse = connecte(cas.acheteurs[1]).get(f"/api/participations/{a2.id}/")

        assert reponse.status_code == 200
        assert reponse.data["statut"] == "reputee_livree"
        assert reponse.data["statut_libelle"] == "Non retirée — réputée livrée"
        assert reponse.data["reputee_livree_le"]
        assert reponse.data["campagne"]["fin_du_retrait_le"]
        autre = connecte(cas.acheteurs[0]).get(f"/api/participations/{a2.id}/")
        assert autre.status_code == 404
        assert "code_retrait" not in autre.data

    def test_une_part_prete_n_a_pas_de_date_de_reputation_et_la_campagne_annonce_son_echeance(
        self, connecte, cas
    ):
        a1 = cas.parts[0]

        part = connecte(cas.acheteurs[0]).get(f"/api/participations/{a1.id}/").data
        campagne = connecte(cas.acheteurs[0]).get(
            f"/api/catalogue/campagnes/{cas.campagne.id}/").data

        assert part["reputee_livree_le"] is None
        attendue = cas.campagne.mise_a_disposition_le + J14
        assert campagne["fin_du_retrait_le"] == part["campagne"]["fin_du_retrait_le"]
        assert abs(
            timezone.datetime.fromisoformat(
                campagne["fin_du_retrait_le"].replace("Z", "+00:00")) - attendue
        ) < timedelta(seconds=1)

    def test_une_campagne_sans_mise_a_disposition_n_a_pas_d_echeance(
        self, connecte, campagne
    ):
        reponse = connecte(campagne.groupeur).get(
            f"/api/catalogue/campagnes/{campagne.id}/")

        assert reponse.data["fin_du_retrait_le"] is None

    def test_le_groupeur_voit_les_parts_reputees_livrees_dans_sa_liste(
        self, connecte, cas
    ):
        _retirer(cas, 0)
        _a_j_plus_14_avec_relances(cas)
        _tache()

        reponse = connecte(cas.campagne.groupeur).get(
            f"/api/groupeur/campagnes/{cas.campagne.id}/participants/")

        assert reponse.status_code == 200
        par_id = {ligne["id"]: ligne for ligne in reponse.data}
        assert par_id[cas.parts[0].id]["statut"] == "retiree"
        for part in cas.parts[1:]:
            ligne = par_id[part.id]
            assert ligne["statut"] == "reputee_livree"
            assert ligne["statut_libelle"] == "Non retirée — réputée livrée"
            assert ligne["reputee_livree_le"]
            assert "code_retrait" not in ligne

    def test_un_autre_groupeur_ne_voit_pas_les_participants(
        self, connecte, cas, groupeur_en_attente, ama
    ):
        adresse = f"/api/groupeur/campagnes/{cas.campagne.id}/participants/"

        assert connecte(ama).get(adresse).status_code == 403
        assert connecte(groupeur_en_attente).get(adresse).status_code in (403, 404)
        autre = Utilisateur.objects.create_user(
            "93009999", "mdpSolide2026", nom="Autre", prenom="Groupeur",
            telephone_verifie=True, role=Utilisateur.Role.GROUPEUR)
        from groupachat.comptes.models import DossierKYC
        DossierKYC.objects.create(
            utilisateur=autre, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-9", numero_mobile_money="93009999",
            nom_commerce="Autre", statut=DossierKYC.Statut.VALIDE)
        assert connecte(autre).get(adresse).status_code == 404

    def test_le_tableau_de_bord_groupeur_compte_la_campagne_terminee_sans_baisser_la_collecte(
        self, connecte, cas
    ):
        api = connecte(cas.campagne.groupeur)
        avant = api.get("/api/groupeur/tableau-de-bord/").data
        _a_j_plus_14_avec_relances(cas)
        _tache()

        # Compte relu : la session de test garde l'instance (et sa réputation
        # en cache) de la première requête.
        api = connecte(Utilisateur.objects.get(pk=cas.campagne.groupeur_id))
        apres = api.get("/api/groupeur/tableau-de-bord/").data

        assert apres["campagnes"]["terminees"] == avant["campagnes"]["terminees"] + 1
        assert apres["campagnes"]["a_distribuer"] == 0
        assert apres["collecte"] == avant["collecte"]
        assert apres["reputation"]["campagnes_terminees"] == 1

    def test_le_tableau_de_bord_admin_compte_la_campagne_terminee(
        self, connecte, cas, administrateur
    ):
        _a_j_plus_14_avec_relances(cas)
        _tache()

        reponse = connecte(administrateur).get("/api/admin/tableau-de-bord/")

        assert reponse.status_code == 200
        assert reponse.data["campagnes"]["terminees"] == 1

    def test_le_controle_des_sequestres_signale_une_distribution_a_solde_positif(
        self, cas
    ):
        Sequestre.objects.filter(campagne=cas.campagne).update(montant_libere=0)
        sortie = StringIO()

        with pytest.raises(CommandError):
            call_command("controler_les_sequestres", stdout=sortie)

        assert str(cas.campagne.id) in sortie.getvalue()


# ── Commande planifiée ──────────────────────────────────────────────────────


class TestCommandePlanifiee:
    def test_la_commande_enchaine_cloture_remboursement_relances_et_j_plus_14(
        self, cas, connecte, produit, ama
    ):
        _a_j_plus_14_avec_relances(cas)
        echue = Campagne.objects.create(
            produit=produit, groupeur=cas.campagne.groupeur, titre="Échue",
            prix_unitaire=18000, quantite_minimale=2, point_remise="Lomé",
            date_limite=timezone.now() + timedelta(days=3),
            statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now())
        participer_et_payer(connecte, ama, echue, quantite=2)
        Campagne.objects.filter(pk=echue.pk).update(
            date_limite=timezone.now() - UNE_MINUTE)

        sortie = _tache()

        assert f"campagne {echue.id} → financee" in sortie
        assert f"campagne {cas.campagne.id} → terminée" in sortie
        assert "1 clôture(s), 0 remboursement(s), 0 relance(s), " \
               "1 campagne(s) close(s) à J+14." in sortie

    def test_la_commande_annonce_les_relances_envoyees(self, cas):
        _reculer(cas.campagne, J3)

        sortie = _tache()

        assert f"campagne {cas.campagne.id} → relance j3" in sortie
        assert "1 relance(s)" in sortie

    def test_le_mode_a_blanc_annonce_sans_rien_changer(
        self, cas, connecte, produit, ama, yao, administrateur
    ):
        def campagne_en_distribution(titre, acheteur, delta):
            autre = Campagne.objects.create(
                produit=produit, groupeur=cas.campagne.groupeur, titre=titre,
                prix_unitaire=18000, quantite_minimale=1, point_remise="Lomé",
                date_limite=timezone.now() + timedelta(days=3),
                statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now())
            participer_et_payer(connecte, acheteur, autre, quantite=1)
            cloturer(autre)
            executer_decaissement(demander_decaissement(autre), administrateur)
            mettre_a_disposition(autre)
            _reculer(autre, delta)
            return autre

        due_j3 = cas.campagne
        _reculer(due_j3, J3)
        due_j7 = campagne_en_distribution("Due J7", ama, J7)
        a_clore = campagne_en_distribution("A clore", yao, J14)
        _poser_relances(a_clore, j3=J14 - J3, j7=J7)
        bloquee = campagne_en_distribution(
            "Bloquée", Utilisateur.objects.get(telephone="91000001"), J14)
        _poser_relances(bloquee, j3=J14 - J3, j7=J7)
        Sequestre.objects.filter(campagne=bloquee).update(montant_libere=0)
        empreintes = {c.pk: _empreinte(c) for c in (due_j3, due_j7, a_clore, bloquee)}

        sortie = _tache("--a-blanc")

        assert f"{due_j3.id} · {due_j3.titre[:44]} → relance j3" in sortie
        assert f"{due_j7.id} · Due J7 → relance j7" in sortie
        assert f"{a_clore.id} · A clore → clôture à J+14 (1 colis non retirés)" in sortie
        assert f"{bloquee.id} · Bloquée → bloquée : fonds consignés" in sortie
        for identifiant, empreinte in empreintes.items():
            assert _empreinte(Campagne.objects.get(pk=identifiant)) == empreinte

        # Le passage réel traite les mêmes campagnes que celles annoncées.
        reel = _tache()
        assert f"campagne {due_j3.id} → relance j3" in reel
        assert f"campagne {due_j7.id} → relance j7" in reel
        assert f"campagne {a_clore.id} → terminée" in reel
        assert f"campagne {bloquee.id} → terminée" not in reel

    def test_le_jeu_de_demonstration_contient_une_campagne_reputee_livree(self):
        call_command("charger_demo", stdout=StringIO())

        assert VERSION_DEMO == "7"
        terminee = Campagne.objects.filter(
            statut=Campagne.Statut.TERMINEE,
            participations__statut=Participation.Statut.REPUTEE_LIVREE,
        ).distinct()
        assert terminee.count() == 1
        assert terminee.get().participations.filter(
            statut=Participation.Statut.RETIREE).exists()
        assert Notification.objects.filter(genre="relance_retrait").exists()
        for sequestre in Sequestre.objects.all():
            assert sequestre.montant_libere + sequestre.montant_rembourse <= (
                sequestre.montant_consigne)
        sortie = StringIO()
        call_command("controler_les_sequestres", stdout=sortie)
        assert "Aucune anomalie." in sortie.getvalue()


# ── Verrous (PostgreSQL) ────────────────────────────────────────────────────


def _lancer_en_fil(action):
    """Joue `action` dans un fil à connexion propre ; garde toute exception."""
    resultats: list = []

    def _corps():
        try:
            resultats.append(action())
        except Exception as erreur:  # noqa: BLE001 : le test examine l'erreur
            resultats.append(erreur)
        finally:
            connection.close()

    fil = threading.Thread(target=_corps)
    fil.start()
    return fil, resultats


@ABSENT_HORS_POSTGRES
@pytest.mark.django_db(transaction=True)
class TestCourses:
    """Un verrou tenu par le test plutôt qu'une course au hasard : déterministe."""

    @pytest.mark.parametrize("tache_d_abord", [False, True])
    def test_le_dernier_code_et_la_tache_ne_terminent_la_campagne_qu_une_fois(
        self, cas, tache_d_abord
    ):
        _retirer(cas, 0)
        for part in cas.parts[2:]:
            _forcer(part, statut=Participation.Statut.REMBOURSEE)
        _a_j_plus_14_avec_relances(cas)
        code = Participation.objects.get(pk=cas.parts[1].pk).code_retrait
        perimee = Campagne.objects.get(pk=cas.campagne.pk)

        with transaction.atomic():
            if tache_d_abord:
                reputer_livree(cas.campagne)
                fil, resultats = _lancer_en_fil(
                    lambda: valider_retrait(perimee, code, cas.campagne.groupeur))
            else:
                valider_retrait(cas.campagne, code, cas.campagne.groupeur)
                fil, resultats = _lancer_en_fil(lambda: reputer_livree(perimee))
            fil.join(timeout=0.5)
            assert fil.is_alive(), "le second doit attendre le verrou de la campagne"
        fil.join(timeout=10)

        reputation = _reputation(cas.campagne)
        assert reputation.campagnes_terminees == 1, "jamais deux fois"
        assert reputation.participants_servis == 2
        part = Participation.objects.get(pk=cas.parts[1].pk)
        assert part.statut == Participation.Statut.RETIREE
        if tache_d_abord:
            assert not isinstance(resultats[0], Exception), resultats
            assert part.reputee_livree_le is not None, "trace conservée"
            assert part.retiree_le is not None
        else:
            assert isinstance(resultats[0], ErreurPaiement)
            assert part.reputee_livree_le is None
            assert Notification.objects.filter(genre="campagne_terminee").count() == 0
        assert Campagne.objects.get(pk=cas.campagne.pk).statut == "terminee"

    def _en_cours_financable(self, connecte, campagne, ama, yao):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)
        Campagne.objects.filter(pk=campagne.pk).update(
            date_limite=timezone.now() - UNE_MINUTE)
        return Campagne.objects.get(pk=campagne.pk)

    def test_la_cloture_et_l_annulation_simultanees_restent_coherentes(
        self, connecte, campagne, ama, yao
    ):
        campagne = self._en_cours_financable(connecte, campagne, ama, yao)

        with transaction.atomic():
            annuler(campagne, "test")
            cloturee_le = Campagne.objects.get(pk=campagne.pk).cloturee_le
            fil, resultats = _lancer_en_fil(lambda: cloturer(campagne))
            fil.join(timeout=0.5)
            assert fil.is_alive(), "la clôture doit attendre la campagne"
        fil.join(timeout=10)

        assert resultats == [Campagne.Statut.ANNULEE]
        relue = Campagne.objects.get(pk=campagne.pk)
        assert relue.statut == Campagne.Statut.ANNULEE
        assert relue.cloturee_le == cloturee_le
        sequestre = Sequestre.objects.get(campagne=campagne)
        assert sequestre.statut == Sequestre.Statut.REMBOURSE
        assert not Notification.objects.filter(titre="Campagne financée").exists()

    def test_la_cloture_verrouille_la_campagne_avant_le_sequestre(
        self, connecte, campagne, ama, yao
    ):
        """C-052 : `cloturer` prenait le séquestre puis la campagne, `annuler`
        l'inverse ; PostgreSQL répondait « deadlock detected »."""
        campagne = self._en_cours_financable(connecte, campagne, ama, yao)

        with transaction.atomic():
            Campagne.objects.select_for_update().get(pk=campagne.pk)
            fil, resultats = _lancer_en_fil(lambda: cloturer(campagne))
            fil.join(timeout=0.5)
            assert fil.is_alive(), "la clôture attend la campagne, sans rien tenir"
            # Le séquestre est libre : sans le correctif, le fil le tient déjà.
            _verrouiller_sequestre(campagne)
        fil.join(timeout=10)

        assert not any(isinstance(r, OperationalError) for r in resultats), resultats
        assert resultats == [Campagne.Statut.FINANCEE]


class TestCloturerSousVerrou:
    def test_cloturer_relit_la_campagne_sous_verrou(self, connecte, campagne, ama, yao):
        """R32 : un objet chargé « en cours » ne rouvre pas une campagne annulée."""
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)
        perimee = Campagne.objects.get(pk=campagne.pk)
        annuler(campagne, "test")
        notifications = Notification.objects.count()

        statut = cloturer(perimee)

        assert statut == Campagne.Statut.ANNULEE
        assert Campagne.objects.get(pk=campagne.pk).statut == Campagne.Statut.ANNULEE
        assert Sequestre.objects.get(campagne=campagne).statut == (
            Sequestre.Statut.REMBOURSE)
        assert Notification.objects.count() == notifications

    def test_cloturer_notifie_et_bloque_le_sequestre(
        self, connecte, campagne, ama, yao
    ):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)

        assert cloturer(campagne) == Campagne.Statut.FINANCEE

        relue = Campagne.objects.get(pk=campagne.pk)
        assert relue.cloturee_le is not None
        assert Sequestre.objects.get(campagne=campagne).statut == (
            Sequestre.Statut.BLOQUE)
        assert Notification.objects.filter(
            genre="campagne_financee", titre="Campagne financée").count() == 3
