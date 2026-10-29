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
from rest_framework.test import APIClient

from groupachat.catalogue.models import Campagne
from groupachat.comptes.models import DossierKYC, Reputation, Utilisateur
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


def _rien_n_a_change(campagne: Campagne, notifications_avant: int) -> None:
    """Après un refus : statut, parts, séquestre et notifications intacts."""
    campagne.refresh_from_db()
    assert campagne.statut == Campagne.Statut.MINIMUM_NON_ATTEINT
    assert not Participation.objects.filter(
        statut=Participation.Statut.REMBOURSEE
    ).exists()
    sequestre = Sequestre.objects.get(campagne=campagne)
    assert (sequestre.solde, sequestre.montant_rembourse) == (90000, 0)
    assert Notification.objects.count() == notifications_avant


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

    def test_le_motif_par_defaut_est_enregistre(self, connecte, manquee):
        for corps in ({}, {"motif": ""}):
            Campagne.objects.filter(pk=manquee.pk).update(
                statut=Campagne.Statut.MINIMUM_NON_ATTEINT, motif_annulation=""
            )
            reponse = connecte(manquee.groupeur).post(
                f"/api/groupeur/campagnes/{manquee.id}/annuler/", corps, format="json"
            )
            assert reponse.status_code == 200, reponse.data
            manquee.refresh_from_db()
            assert manquee.motif_annulation == "Groupage non abouti."

    def test_le_motif_saisi_est_enregistre(self, connecte, manquee):
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/annuler/",
            {"motif": "Fournisseur indisponible"},
            format="json",
        )
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["statut"] == "annulee"
        assert reponse.data["motif_annulation"] == "Fournisseur indisponible"
        manquee.refresh_from_db()
        assert manquee.motif_annulation == "Fournisseur indisponible"

    def test_la_decision_maintenir_rend_la_campagne_financee_sans_rembourser(
        self, connecte, manquee, ama, yao
    ):
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        )
        assert reponse.data["statut"] == "financee"
        sequestre = Sequestre.objects.get(campagne=manquee)
        assert sequestre.solde == 90000
        assert sequestre.montant_rembourse == 0
        assert not Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).exists()
        for acheteur in (ama, yao):
            avis = Notification.objects.get(
                destinataire=acheteur, genre=Notification.Genre.CAMPAGNE_MAINTENUE
            )
            assert avis.lien == f"/campagnes/{manquee.id}"

    def test_l_annulation_notifie_et_rembourse_chaque_acheteur(
        self, connecte, manquee, ama, yao
    ):
        connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/annuler/", {}, format="json"
        )
        for acheteur, montant in ((ama, 54000), (yao, 36000)):
            for genre in (
                Notification.Genre.CAMPAGNE_ANNULEE,
                Notification.Genre.REMBOURSEMENT,
            ):
                assert Notification.objects.filter(
                    destinataire=acheteur, genre=genre
                ).count() == 1, genre
            remboursements = Transaction.objects.filter(
                participation__acheteur=acheteur, sens=Transaction.Sens.REMBOURSEMENT
            )
            assert [t.montant for t in remboursements] == [montant]
        sequestre = Sequestre.objects.get(campagne=manquee)
        assert sequestre.montant_rembourse == sequestre.montant_consigne == 90000
        assert sequestre.solde == 0
        assert sequestre.statut == Sequestre.Statut.REMBOURSE

    def test_un_autre_groupeur_ne_voit_pas_la_campagne_et_rien_n_est_ecrit(
        self, connecte, manquee
    ):
        autre = Utilisateur.objects.create_user(
            "93004455", "mdpSolide2026", nom="Autre", prenom="Groupeur",
            telephone_verifie=True, role=Utilisateur.Role.GROUPEUR,
        )
        DossierKYC.objects.create(
            utilisateur=autre, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-9", numero_mobile_money="93004455",
            nom_commerce="Autre", statut=DossierKYC.Statut.VALIDE,
        )
        avant = Notification.objects.count()
        api = connecte(autre)
        for action in ("maintenir", "annuler"):
            reponse = api.post(
                f"/api/groupeur/campagnes/{manquee.id}/{action}/", {}, format="json"
            )
            assert reponse.status_code == 404, action
        _rien_n_a_change(manquee, avant)

    def test_un_acheteur_et_un_anonyme_ne_decident_pas_et_rien_n_est_ecrit(
        self, connecte, manquee, ama
    ):
        avant = Notification.objects.count()
        clients = (connecte(ama), APIClient())
        for api in clients:
            for action in ("maintenir", "annuler", "cloturer"):
                reponse = api.post(
                    f"/api/groupeur/campagnes/{manquee.id}/{action}/", {}, format="json"
                )
                assert reponse.status_code in (401, 403), (action, reponse.status_code)
        _rien_n_a_change(manquee, avant)

    @pytest.mark.parametrize(
        "statut",
        [Campagne.Statut.EN_COURS, Campagne.Statut.FINANCEE, Campagne.Statut.ANNULEE],
    )
    def test_maintenir_hors_decision_est_refuse(self, connecte, manquee, statut):
        Campagne.objects.filter(pk=manquee.pk).update(statut=statut)
        avant = Notification.objects.count()
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        )
        assert reponse.status_code == 400
        assert reponse.data["detail"] == "Cette campagne n'attend pas de décision."
        manquee.refresh_from_db()
        assert manquee.statut == statut
        assert Notification.objects.count() == avant

    def test_annuler_deux_fois_ne_rembourse_qu_une_fois(self, connecte, manquee):
        api = connecte(manquee.groupeur)
        url = f"/api/groupeur/campagnes/{manquee.id}/annuler/"
        assert api.post(url, {}, format="json").status_code == 200
        remboursements = Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).count()

        seconde = api.post(url, {}, format="json")
        assert seconde.status_code == 400
        assert seconde.data["detail"] == "Cette campagne ne peut plus être annulée."
        assert Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).count() == remboursements == 2
        assert Sequestre.objects.get(campagne=manquee).montant_rembourse == 90000
        assert Reputation.objects.get(groupeur=manquee.groupeur).campagnes_annulees == 1

    def test_annuler_apres_maintien_reste_permis_tant_que_rien_n_est_decaisse(
        self, connecte, manquee, ama
    ):
        """Décision D1 : le groupeur peut changer d'avis jusqu'au décaissement."""
        api = connecte(manquee.groupeur)
        api.post(f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json")
        reponse = api.post(
            f"/api/groupeur/campagnes/{manquee.id}/annuler/", {}, format="json"
        )
        assert reponse.status_code == 200
        assert Participation.objects.get(acheteur=ama).statut == (
            Participation.Statut.REMBOURSEE
        )

    def test_la_cloture_anticipee_sans_minimum_attend_la_decision(
        self, connecte, campagne, ama
    ):
        participer(connecte, ama, campagne, 3)
        reponse = connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        assert reponse.status_code == 200
        assert reponse.data == {"statut": "minimum_non_atteint"}
        assert Notification.objects.filter(
            destinataire=ama, genre=Notification.Genre.GROUPAGE_NON_ABOUTI
        ).exists()
        assert Notification.objects.filter(
            destinataire=campagne.groupeur, genre=Notification.Genre.DECISION_ATTENDUE
        ).exists()
        assert Sequestre.objects.get(campagne=campagne).montant_rembourse == 0
        assert not Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).exists()

    def test_la_cloture_anticipee_avec_minimum_finance(self, connecte, campagne, ama):
        participer(connecte, ama, campagne, campagne.quantite_minimale)
        reponse = connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        assert reponse.data == {"statut": "financee"}
        for destinataire in (ama, campagne.groupeur):
            assert Notification.objects.filter(
                destinataire=destinataire, genre=Notification.Genre.CAMPAGNE_FINANCEE
            ).exists()


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

    def test_maintenir_est_permis_juste_avant_le_septieme_jour(
        self, connecte, manquee, settings
    ):
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now()
            - timedelta(days=settings.DELAI_DECISION_JOURS, minutes=-1)
        )
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        )
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["statut"] == "financee"

    def test_maintenir_est_refuse_des_le_septieme_jour_sans_attendre_la_tache(
        self, connecte, manquee, ama, settings
    ):
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now() - timedelta(days=settings.DELAI_DECISION_JOURS)
        )
        avant = Notification.objects.count()
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        )
        assert reponse.status_code == 400
        assert "délai" in reponse.data["detail"]
        manquee.refresh_from_db()
        assert manquee.statut == Campagne.Statut.MINIMUM_NON_ATTEINT
        assert Notification.objects.count() == avant

    def test_annuler_reste_permis_apres_le_delai(self, connecte, manquee, settings):
        """C'est l'issue que la tâche appliquerait : la devancer ne lèse personne."""
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now() - timedelta(days=settings.DELAI_DECISION_JOURS + 1)
        )
        reponse = connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/annuler/", {}, format="json"
        )
        assert reponse.status_code == 200

    def test_un_delai_nul_laisse_maintenir_sans_limite(
        self, connecte, manquee, settings
    ):
        settings.DELAI_DECISION_JOURS = 0
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now() - timedelta(days=365)
        )
        assert connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        ).status_code == 200

    def test_la_tache_ne_rembourse_pas_une_campagne_maintenue(
        self, connecte, manquee, ama, settings
    ):
        """La tâche a sélectionné la campagne avant que le groupeur ne maintienne."""
        connecte(manquee.groupeur).post(
            f"/api/groupeur/campagnes/{manquee.id}/maintenir/", {}, format="json"
        )
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now() - timedelta(days=settings.DELAI_DECISION_JOURS + 1)
        )
        assert rembourser_les_indecis() == []
        assert Participation.objects.get(acheteur=ama).statut == (
            Participation.Statut.PAYEE
        )

    def test_la_tache_enregistre_le_motif_du_silence(self, manquee, settings):
        Campagne.objects.filter(pk=manquee.pk).update(
            cloturee_le=timezone.now() - timedelta(days=settings.DELAI_DECISION_JOURS + 1)
        )
        rembourser_les_indecis()
        manquee.refresh_from_db()
        assert manquee.motif_annulation == (
            "Sans décision du groupeur 7 jours après la clôture."
        )
        assert Sequestre.objects.get(campagne=manquee).solde == 0


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
