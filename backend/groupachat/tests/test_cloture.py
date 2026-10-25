# -*- coding: utf-8 -*-
"""Le cycle de clôture : ce qui se ferme seul, et ce qui attend une décision.

La règle que ces tests protègent tient en une phrase : **à la date limite
la collecte se ferme, mais l'argent ne repart pas tout seul**. Un groupeur
peut décider de maintenir la commande malgré le nombre ; rembourser
d'office ferait échouer des groupages qui auraient abouti.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Participation
from groupachat.echanges.models import Notification
from groupachat.paiements.models import Sequestre, Transaction
from groupachat.paiements.services import cloturer_les_echus, rembourser_les_indecis

pytestmark = pytest.mark.django_db


def participer(connecte, acheteur, campagne, quantite):
    api = connecte(acheteur)
    part = api.post(
        "/api/participations/",
        {"campagne": campagne.id, "quantite": quantite},
        format="json",
    ).data
    api.post(f"/api/participations/{part['id']}/payer/", {}, format="json")
    return part


def faire_expirer(campagne: Campagne) -> None:
    """Recule la date limite sans attendre — `update` évite `save()`."""
    Campagne.objects.filter(pk=campagne.pk).update(
        date_limite=timezone.now() - timedelta(hours=1)
    )
    campagne.refresh_from_db()


class TestClotureAutomatique:
    def test_une_collecte_echue_se_ferme_seule(self, connecte, campagne, ama):
        participer(connecte, ama, campagne, 3)
        faire_expirer(campagne)

        cloturer_les_echus()
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.MINIMUM_NON_ATTEINT

    def test_le_minimum_atteint_finance_la_campagne(self, connecte, campagne, ama):
        participer(connecte, ama, campagne, campagne.quantite_minimale)
        faire_expirer(campagne)

        cloturer_les_echus()
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.FINANCEE

    def test_une_collecte_en_cours_n_est_pas_touchee(self, connecte, campagne, ama):
        participer(connecte, ama, campagne, 2)
        cloturer_les_echus()
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.EN_COURS


class TestArgentNonRendu:
    """Le cœur de la règle."""

    @pytest.fixture
    def manquee(self, connecte, campagne, ama, yao):
        participer(connecte, ama, campagne, 3)
        participer(connecte, yao, campagne, 2)
        faire_expirer(campagne)
        cloturer_les_echus()
        campagne.refresh_from_db()
        return campagne

    def test_la_cloture_ne_rembourse_personne(self, manquee, ama):
        assert manquee.statut == Campagne.Statut.MINIMUM_NON_ATTEINT

        part = Participation.objects.get(acheteur=ama)
        assert part.statut == Participation.Statut.PAYEE, "la part reste payée"
        assert not Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).exists(), "aucun remboursement ne doit partir à la clôture"

        sequestre = Sequestre.objects.get(campagne=manquee)
        assert sequestre.solde == 90000, "l'argent reste consigné"

    def test_les_participants_savent_que_ca_n_a_pas_abouti(self, manquee, ama, yao):
        for acheteur in (ama, yao):
            avis = Notification.objects.get(
                destinataire=acheteur,
                genre=Notification.Genre.GROUPAGE_NON_ABOUTI,
            )
            assert "n'a pas abouti" in avis.titre.lower() or "abouti" in avis.titre
            assert "reste consignée" in avis.message

    def test_le_groupeur_est_invite_a_trancher(self, manquee):
        avis = Notification.objects.get(
            destinataire=manquee.groupeur,
            genre=Notification.Genre.DECISION_ATTENDUE,
        )
        assert "Maintenez-vous" in avis.message


class TestDecisionDuGroupeur:
    @pytest.fixture
    def manquee(self, connecte, campagne, ama, yao):
        participer(connecte, ama, campagne, 3)
        participer(connecte, yao, campagne, 2)
        faire_expirer(campagne)
        cloturer_les_echus()
        campagne.refresh_from_db()
        return campagne

    def test_il_peut_maintenir_malgre_le_nombre(self, connecte, manquee, ama):
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        )
        assert reponse.status_code == 200, reponse.data

        manquee.refresh_from_db()
        assert manquee.statut == Campagne.Statut.FINANCEE
        assert Participation.objects.get(acheteur=ama).statut == (
            Participation.Statut.PAYEE
        )
        assert Notification.objects.filter(
            destinataire=ama, genre=Notification.Genre.CAMPAGNE_MAINTENUE
        ).exists()

    def test_une_campagne_maintenue_suit_le_cours_normal(self, connecte, manquee):
        api = connecte(manquee.groupeur)
        api.post(f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json")
        retrait = api.post(
            f"/api/groupeur/campagnes/{manquee.id}/demander-retrait/", {}, format="json"
        )
        assert retrait.status_code == 201, retrait.data
        assert retrait.data["frais"] == 1500

    def test_il_peut_annuler_et_tout_le_monde_est_rembourse(
        self, connecte, manquee, ama, yao
    ):
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/annuler/", {}, format="json"
        )
        assert reponse.status_code == 200, reponse.data

        manquee.refresh_from_db()
        assert manquee.statut == Campagne.Statut.ANNULEE
        for acheteur in (ama, yao):
            assert Participation.objects.get(acheteur=acheteur).statut == (
                Participation.Statut.REMBOURSEE
            )
        assert Sequestre.objects.get(campagne=manquee).solde == 0

    def test_une_annulation_pese_sur_la_reputation(self, connecte, manquee):
        """Une note qui ne peut que monter ne dit rien de personne."""
        from groupachat.comptes.models import Reputation

        connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/annuler/", {}, format="json"
        )
        reputation = Reputation.objects.get(groupeur=manquee.groupeur)
        assert reputation.campagnes_annulees == 1

    def test_un_autre_groupeur_ne_decide_pas_a_sa_place(self, connecte, manquee, ama):
        assert connecte(ama).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        ).status_code == 403


class TestDelaiDeDecision:
    @pytest.fixture
    def manquee(self, connecte, campagne, ama):
        participer(connecte, ama, campagne, 3)
        faire_expirer(campagne)
        cloturer_les_echus()
        campagne.refresh_from_db()
        return campagne

    def test_rien_ne_bouge_avant_le_delai(self, manquee):
        assert rembourser_les_indecis() == []
        manquee.refresh_from_db()
        assert manquee.statut == Campagne.Statut.MINIMUM_NON_ATTEINT

    def test_le_silence_finit_par_rembourser(self, manquee, ama, settings):
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now()
            - timedelta(days=settings.DELAI_DECISION_JOURS + 1)
        )
        rendues = rembourser_les_indecis()

        assert manquee.id in rendues
        manquee.refresh_from_db()
        assert manquee.statut == Campagne.Statut.ANNULEE
        assert Participation.objects.get(acheteur=ama).statut == (
            Participation.Statut.REMBOURSEE
        )

    def test_un_delai_nul_desactive_le_remboursement(self, manquee, settings):
        """Au cas où l'on voudrait que seule une main humaine tranche."""
        settings.DELAI_DECISION_JOURS = 0
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now() - timedelta(days=365)
        )
        assert rembourser_les_indecis() == []


class TestCatalogueEtHistorique:
    """Ce qui disparaît du catalogue reste lisible pour qui a payé."""

    @pytest.fixture
    def manquee(self, connecte, campagne, ama):
        participer(connecte, ama, campagne, 3)
        faire_expirer(campagne)
        cloturer_les_echus()
        campagne.refresh_from_db()
        return campagne

    def test_elle_quitte_le_catalogue(self, client, manquee):
        resultats = client.get("/api/catalogue/campagnes/").data["results"]
        assert manquee.id not in [c["id"] for c in resultats]

    def test_une_collecte_depassee_sort_de_la_liste_sans_attendre_la_tache(
        self, client, connecte, campagne, ama
    ):
        """La tâche tourne à l'heure ; la liste, elle, doit être juste tout de suite."""
        participer(connecte, ama, campagne, 2)
        faire_expirer(campagne)
        # Pas de clôture : la campagne est encore « en_cours » en base.
        assert campagne.statut == Campagne.Statut.EN_COURS

        resultats = client.get("/api/catalogue/campagnes/").data["results"]
        assert campagne.id not in [c["id"] for c in resultats]

    def test_la_participante_rouvre_la_fiche_depuis_son_historique(
        self, connecte, manquee, ama
    ):
        reponse = connecte(ama).get(f"/api/catalogue/campagnes/{manquee.id}/")
        assert reponse.status_code == 200, "sa propre commande ne doit pas disparaître"
        assert reponse.data["produit"]["nom"]
        assert reponse.data["point_remise"]

    def test_le_fil_de_discussion_reste_lisible(self, connecte, manquee, ama):
        connecte(ama).post(
            f"/api/campagnes/{manquee.id}/commentaires/",
            {"texte": "Et pour la suite ?"},
            format="json",
        )
        reponse = connecte(ama).get(f"/api/campagnes/{manquee.id}/commentaires/")
        assert reponse.status_code == 200
        assert reponse.data["count"] >= 1

    def test_une_campagne_annulee_reste_consultable(self, connecte, manquee, ama):
        connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/annuler/", {}, format="json"
        )
        assert connecte(ama).get(
            f"/api/catalogue/campagnes/{manquee.id}/"
        ).status_code == 200


class TestCommandePlanifiee:
    def test_la_commande_ferme_et_rembourse(self, connecte, campagne, ama, capsys):
        participer(connecte, ama, campagne, 2)
        faire_expirer(campagne)

        call_command("cloturer_les_campagnes_echues")
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.MINIMUM_NON_ATTEINT
        assert "clôture" in capsys.readouterr().out

    def test_le_mode_a_blanc_ne_change_rien(self, connecte, campagne, ama):
        participer(connecte, ama, campagne, 2)
        faire_expirer(campagne)

        call_command("cloturer_les_campagnes_echues", "--a-blanc")
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.EN_COURS
