# -*- coding: utf-8 -*-
"""F-024 : l'argent d'une campagne ne sort qu'une fois.

Panne d'origine (T1) : le groupeur annule une campagne financée dont il a déjà
demandé le retrait ; les acheteurs sont remboursés, puis l'administrateur
exécute le décaissement resté en attente et verse la même somme une seconde
fois. Ces tests couvrent ce croisement, ses variantes et les garde-fous.

Les courses réelles (R31 à R33) exigent PostgreSQL : SQLite ignore
`select_for_update`. R34 porte la même preuve (relecture sous verrou) sur
tous les moteurs.
"""

from __future__ import annotations

import threading

import pytest
from django.db import connection, transaction
from rest_framework.test import APIClient

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Participation
from groupachat.commandes.tests import participer_et_payer
from groupachat.echanges.models import Notification
from groupachat.paiements.models import Decaissement, Sequestre, Transaction
from groupachat.paiements.services import (
    ErreurPaiement,
    annuler,
    demander_decaissement,
    executer_decaissement,
    mettre_a_disposition,
)

pytestmark = pytest.mark.django_db

ABSENT_HORS_POSTGRES = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="SQLite ignore select_for_update : la course n'y est pas reproductible",
)


@pytest.fixture
def financee(connecte, campagne, ama, yao):
    """Campagne financée : 180 000 FCFA consignés, retrait non encore demandé."""
    participer_et_payer(connecte, ama, campagne, quantite=6)
    participer_et_payer(connecte, yao, campagne, quantite=4)
    connecte(campagne.groupeur).post(
        f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
    )
    campagne.refresh_from_db()
    assert campagne.statut == Campagne.Statut.FINANCEE
    return campagne


@pytest.fixture
def demande(financee):
    """Le décaissement demandé, en attente de l'administrateur."""
    return demander_decaissement(financee)


def _sequestre(campagne) -> Sequestre:
    return Sequestre.objects.get(campagne=campagne)


def _fonds_verses(campagne) -> int:
    return Notification.objects.filter(
        campagne=campagne, titre="Fonds versés"
    ).count()


def _executer(connecte, administrateur, decaissement):
    return connecte(administrateur).post(
        f"/api/admin/decaissements/{decaissement.id}/executer/", {}, format="json"
    )


def _annuler(connecte, campagne, motif="Fournisseur défaillant"):
    return connecte(campagne.groupeur).post(
        f"/api/groupeur/campagnes/{campagne.id}/annuler/",
        {"motif": motif}, format="json",
    )


def _mettre_a_disposition(connecte, campagne):
    return connecte(campagne.groupeur).post(
        f"/api/groupeur/campagnes/{campagne.id}/mise-a-disposition/",
        {"point_remise": "Boutique Abalo"}, format="json",
    )


# ── Administrateur : exécuter ───────────────────────────────────────────────


class TestExecution:
    def test_un_decaissement_en_attente_n_est_pas_execute_apres_l_annulation(
        self, connecte, financee, demande, administrateur
    ):
        """T1 : annuler puis exécuter versait 358 500 FCFA pour 180 000 consignés."""
        assert _annuler(connecte, financee).status_code == 200
        reponse = _executer(connecte, administrateur, demande)

        assert reponse.status_code == 400
        assert "detail" in reponse.data
        sequestre = _sequestre(financee)
        assert (sequestre.montant_libere, sequestre.montant_rembourse) == (0, 180000)
        financee.refresh_from_db()
        assert financee.statut == Campagne.Statut.ANNULEE
        assert _fonds_verses(financee) == 0
        assert sequestre.montant_libere + sequestre.montant_rembourse == 180000

    def test_un_decaissement_refuse_ne_peut_pas_etre_execute(
        self, connecte, financee, demande, administrateur
    ):
        _annuler(connecte, financee)
        demande.refresh_from_db()
        assert demande.statut == Decaissement.Statut.REFUSE

        reponse = _executer(connecte, administrateur, demande)

        assert reponse.status_code == 400
        assert "refusé" in reponse.data["detail"]
        demande.refresh_from_db()
        assert demande.statut == Decaissement.Statut.REFUSE
        assert _sequestre(financee).montant_libere == 0

    def test_un_decaissement_deja_execute_ne_verse_pas_deux_fois(
        self, connecte, financee, demande, administrateur
    ):
        assert _executer(connecte, administrateur, demande).status_code == 200
        demande.refresh_from_db()
        reference, date = demande.reference, demande.execute_le

        reponse = _executer(connecte, administrateur, demande)

        assert reponse.status_code == 400
        assert reponse.data["detail"] == "Ce décaissement a déjà été exécuté."
        assert _sequestre(financee).montant_libere == 180000
        assert _fonds_verses(financee) == 1
        demande.refresh_from_db()
        assert (demande.reference, demande.execute_le) == (reference, date)

    def test_l_execution_rend_l_etat_apres_ecriture(
        self, connecte, financee, demande, administrateur
    ):
        reponse = _executer(connecte, administrateur, demande)

        assert reponse.status_code == 200, reponse.data
        assert reponse.data["statut"] == "execute"
        assert reponse.data["reference"]
        assert reponse.data["execute_le"]
        assert _sequestre(financee).statut == Sequestre.Statut.LIBERE

    def test_le_decaissement_est_refuse_quand_le_solde_ne_suffit_pas(
        self, connecte, financee, demande, administrateur
    ):
        """Une part remboursée après la demande réduit le solde sous le brut."""
        part = Participation.objects.filter(campagne=financee).first()
        from groupachat.paiements.services import rembourser

        rembourser(part, motif="test")
        avant = _sequestre(financee)

        reponse = _executer(connecte, administrateur, demande)

        assert reponse.status_code == 400
        assert reponse.data["detail"] == (
            "Le séquestre ne contient pas assez de fonds pour ce versement."
        )
        demande.refresh_from_db()
        assert demande.statut == Decaissement.Statut.DEMANDE
        apres = _sequestre(financee)
        assert apres.montant_libere == avant.montant_libere == 0
        assert _fonds_verses(financee) == 0

    @pytest.mark.parametrize(
        "statut",
        [
            Campagne.Statut.EN_COURS,
            Campagne.Statut.MINIMUM_NON_ATTEINT,
            Campagne.Statut.APPROVISIONNEMENT,
            Campagne.Statut.DISTRIBUTION,
            Campagne.Statut.TERMINEE,
        ],
    )
    def test_le_decaissement_n_est_execute_que_sur_une_campagne_financee(
        self, connecte, financee, demande, administrateur, statut
    ):
        Campagne.objects.filter(pk=financee.pk).update(statut=statut)

        reponse = _executer(connecte, administrateur, demande)

        assert reponse.status_code == 400
        assert reponse.data["detail"] == (
            "Ce décaissement ne peut plus être exécuté : la campagne n'est plus financée."
        )
        demande.refresh_from_db()
        assert demande.statut == Decaissement.Statut.DEMANDE
        assert _sequestre(financee).montant_libere == 0
        financee.refresh_from_db()
        assert financee.statut == statut

    def test_seul_l_administrateur_execute_un_decaissement(
        self, connecte, client, financee, demande, ama
    ):
        chemin = f"/api/admin/decaissements/{demande.id}/executer/"
        assert connecte(ama).post(chemin, {}, format="json").status_code == 403
        assert connecte(financee.groupeur).post(chemin, {}, format="json").status_code == 403
        anonyme = APIClient()
        assert anonyme.post(chemin, {}, format="json").status_code in (401, 403)
        assert _sequestre(financee).montant_libere == 0
        demande.refresh_from_db()
        assert demande.statut == Decaissement.Statut.DEMANDE

    def test_un_decaissement_inconnu_est_introuvable(self, connecte, administrateur):
        reponse = connecte(administrateur).post(
            "/api/admin/decaissements/999999/executer/", {}, format="json"
        )
        assert reponse.status_code == 404

    def test_les_gardes_passent_avant_l_appel_a_l_operateur(
        self, connecte, financee, demande, administrateur, monkeypatch
    ):
        """Un refus ne doit jamais avoir appelé l'opérateur : l'argent serait parti."""
        appels = []
        monkeypatch.setattr(
            "groupachat.paiements.services._executer_paiement",
            lambda *a, **k: appels.append(a) or (True, "X"),
        )
        _annuler(connecte, financee)
        appels.clear()  # les remboursements de l'annulation passent par l'opérateur

        assert _executer(connecte, administrateur, demande).status_code == 400
        assert appels == []


# ── Administrateur : lecture du refus ───────────────────────────────────────


class TestRefusALAnnulation:
    def test_l_annulation_refuse_le_decaissement_avec_un_motif(
        self, connecte, financee, demande, administrateur
    ):
        _annuler(connecte, financee, motif="Fournisseur défaillant")

        reponse = connecte(administrateur).get("/api/admin/decaissements/")

        ligne = next(l for l in reponse.data["results"] if l["id"] == demande.id)
        assert ligne["statut"] == "refuse"
        assert ligne["motif_refus"].startswith("Campagne annulée le ")
        assert ligne["motif_refus"].endswith(": Fournisseur défaillant")

    def test_l_annulation_d_une_campagne_financee_refuse_le_decaissement_en_attente(
        self, connecte, financee, demande
    ):
        reponse = _annuler(connecte, financee)

        assert reponse.status_code == 200, reponse.data
        financee.refresh_from_db()
        assert financee.statut == Campagne.Statut.ANNULEE
        sequestre = _sequestre(financee)
        assert (sequestre.montant_consigne, sequestre.montant_rembourse,
                sequestre.montant_libere) == (180000, 180000, 0)
        assert sequestre.statut == Sequestre.Statut.REMBOURSE
        assert Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT).count() == 2
        assert Participation.objects.filter(
            campagne=financee, statut=Participation.Statut.REMBOURSEE).count() == 2
        demande.refresh_from_db()
        assert demande.statut == Decaissement.Statut.REFUSE
        assert demande.motif_refus

    def test_le_groupeur_est_prevenu_de_l_annulation_de_son_retrait(
        self, connecte, financee, demande
    ):
        _annuler(connecte, financee, motif="Fournisseur défaillant")

        notification = Notification.objects.get(
            destinataire=financee.groupeur, titre="Demande de retrait annulée"
        )
        assert notification.genre == Notification.Genre.CAMPAGNE_ANNULEE
        assert "178500" in notification.message
        assert notification.lien == f"/groupeur/campagnes/{financee.id}"

    def test_l_annulation_sans_decaissement_reste_possible(self, connecte, financee):
        reponse = _annuler(connecte, financee)

        assert reponse.status_code == 200, reponse.data
        assert not Decaissement.objects.exists()
        assert not Notification.objects.filter(
            titre="Demande de retrait annulée").exists()

    def test_on_n_annule_pas_une_campagne_dont_les_fonds_sont_verses(
        self, connecte, financee, demande, administrateur
    ):
        _executer(connecte, administrateur, demande)

        reponse = _annuler(connecte, financee)

        assert reponse.status_code == 400
        assert reponse.data["detail"] == (
            "Les fonds ont déjà été versés au groupeur : "
            "cette campagne ne peut plus être annulée."
        )
        financee.refresh_from_db()
        assert financee.statut == Campagne.Statut.APPROVISIONNEMENT
        assert Participation.objects.filter(
            campagne=financee, statut=Participation.Statut.PAYEE).count() == 2
        assert _sequestre(financee).montant_rembourse == 0

    def test_l_annulation_est_refusee_si_un_decaissement_est_execute_meme_si_la_campagne_est_financee(
        self, connecte, financee, demande, administrateur
    ):
        """Garde de défense : indépendante du statut de la campagne."""
        _executer(connecte, administrateur, demande)
        Campagne.objects.filter(pk=financee.pk).update(
            statut=Campagne.Statut.FINANCEE)

        reponse = _annuler(connecte, financee)

        assert reponse.status_code == 400
        assert "déjà été versés" in reponse.data["detail"]
        sequestre = _sequestre(financee)
        assert (sequestre.montant_libere, sequestre.montant_rembourse) == (180000, 0)
        assert not Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT).exists()

    @pytest.mark.parametrize(
        "statut",
        [Campagne.Statut.DISTRIBUTION, Campagne.Statut.TERMINEE,
         Campagne.Statut.ANNULEE],
    )
    def test_l_annulation_est_refusee_apres_la_distribution(
        self, connecte, financee, statut
    ):
        Campagne.objects.filter(pk=financee.pk).update(statut=statut)

        reponse = _annuler(connecte, financee)

        assert reponse.status_code == 400
        assert _sequestre(financee).montant_rembourse == 0

    def test_l_annulation_est_reservee_au_groupeur_de_la_campagne(
        self, connecte, financee, ama, groupeur_en_attente
    ):
        chemin = f"/api/groupeur/campagnes/{financee.id}/annuler/"
        assert connecte(ama).post(chemin, {}, format="json").status_code == 403
        assert connecte(groupeur_en_attente).post(
            chemin, {}, format="json").status_code in (403, 404)
        assert APIClient().post(chemin, {}, format="json").status_code in (401, 403)
        financee.refresh_from_db()
        assert financee.statut == Campagne.Statut.FINANCEE
        assert _sequestre(financee).montant_rembourse == 0


# ── Groupeur : mise à disposition ───────────────────────────────────────────


class TestMiseADisposition:
    def test_on_ne_met_pas_a_disposition_une_campagne_financee(
        self, connecte, financee, ama
    ):
        reponse = _mettre_a_disposition(connecte, financee)

        assert reponse.status_code == 400
        assert reponse.data["detail"] == (
            "Les fonds n'ont pas encore été versés : "
            "la marchandise ne peut pas être mise à disposition."
        )
        financee.refresh_from_db()
        assert financee.statut == Campagne.Statut.FINANCEE
        assert not Participation.objects.filter(
            campagne=financee, statut=Participation.Statut.PRETE).exists()
        assert not Notification.objects.filter(
            genre=Notification.Genre.MARCHANDISE_DISPONIBLE).exists()
        assert _sequestre(financee).solde == 180000

    def test_on_ne_met_pas_a_disposition_avec_un_retrait_seulement_demande(
        self, connecte, financee, demande
    ):
        assert _mettre_a_disposition(connecte, financee).status_code == 400
        demande.refresh_from_db()
        assert demande.statut == Decaissement.Statut.DEMANDE

    def test_la_mise_a_disposition_suit_le_versement(
        self, connecte, financee, demande, administrateur, ama
    ):
        _executer(connecte, administrateur, demande)

        reponse = _mettre_a_disposition(connecte, financee)

        assert reponse.status_code == 200, reponse.data
        assert reponse.data == {"participants_notifies": 2,
                                "point_remise": "Boutique Abalo"}
        financee.refresh_from_db()
        assert financee.statut == Campagne.Statut.DISTRIBUTION
        assert Participation.objects.filter(
            campagne=financee, statut=Participation.Statut.PRETE).count() == 2
        assert _sequestre(financee).montant_libere == 180000

    @pytest.mark.parametrize(
        "statut",
        [Campagne.Statut.DISTRIBUTION, Campagne.Statut.TERMINEE,
         Campagne.Statut.ANNULEE, Campagne.Statut.EN_COURS,
         Campagne.Statut.DECAISSEE],
    )
    def test_la_mise_a_disposition_est_refusee_hors_approvisionnement(
        self, connecte, financee, statut
    ):
        Campagne.objects.filter(pk=financee.pk).update(statut=statut)

        reponse = _mettre_a_disposition(connecte, financee)

        assert reponse.status_code == 400
        assert reponse.data["detail"] == "Cette campagne n'en est pas à la distribution."
        assert not Notification.objects.filter(
            genre=Notification.Genre.MARCHANDISE_DISPONIBLE).exists()

    def test_un_groupeur_ne_met_pas_a_disposition_la_campagne_d_un_autre(
        self, connecte, financee, groupeur_en_attente
    ):
        reponse = connecte(groupeur_en_attente).post(
            f"/api/groupeur/campagnes/{financee.id}/mise-a-disposition/",
            {}, format="json",
        )
        assert reponse.status_code in (403, 404)
        financee.refresh_from_db()
        assert financee.statut == Campagne.Statut.FINANCEE


# ── Acheteur ────────────────────────────────────────────────────────────────


class TestAcheteur:
    def test_l_acheteur_n_est_prevenu_qu_une_fois_du_remboursement(
        self, connecte, financee, demande, administrateur, ama
    ):
        _annuler(connecte, financee)
        _executer(connecte, administrateur, demande)

        mes = Notification.objects.filter(destinataire=ama)
        assert mes.filter(titre="Groupage annulé").count() == 1
        assert mes.filter(titre__icontains="Remboursement").count() == 1
        assert not mes.filter(titre="Fonds versés").exists()

    def test_aucune_notification_de_retrait_sans_fonds_liberes(
        self, connecte, financee, ama
    ):
        _mettre_a_disposition(connecte, financee)

        participation = Participation.objects.get(campagne=financee, acheteur=ama)
        assert participation.statut == Participation.Statut.PAYEE
        assert not Notification.objects.filter(
            destinataire=ama, genre=Notification.Genre.MARCHANDISE_DISPONIBLE
        ).exists()


# ── Demande de retrait ──────────────────────────────────────────────────────


class TestDemande:
    def test_une_demande_apres_l_annulation_est_un_refus_lisible(
        self, connecte, financee
    ):
        _annuler(connecte, financee)

        reponse = connecte(financee.groupeur).post(
            f"/api/groupeur/campagnes/{financee.id}/demander-retrait/",
            {}, format="json",
        )
        assert reponse.status_code == 400
        assert not Decaissement.objects.exists()

    def test_la_demande_relit_la_campagne_sous_verrou(self, connecte, financee):
        """Objet périmé : la campagne a été annulée après sa lecture par la vue."""
        perimee = Campagne.objects.get(pk=financee.pk)
        annuler(financee, "test")

        with pytest.raises(ErreurPaiement):
            demander_decaissement(perimee)
        assert not Decaissement.objects.exists()


# ── Objet périmé et concurrence ─────────────────────────────────────────────


class TestRelectureSousVerrou:
    def test_le_service_relit_le_decaissement_sous_verrou(
        self, financee, demande, administrateur
    ):
        """R34 : l'instance reçue date d'avant l'annulation ; le service ne la croit pas."""
        perime = Decaissement.objects.get(pk=demande.pk)
        annuler(financee, "test")

        with pytest.raises(ErreurPaiement, match="refusé"):
            executer_decaissement(perime, administrateur)

        sequestre = _sequestre(financee)
        assert (sequestre.montant_libere, sequestre.montant_rembourse) == (0, 180000)
        assert _fonds_verses(financee) == 0

    def test_une_instance_perimee_encore_en_attente_ne_verse_pas_deux_fois(
        self, financee, demande, administrateur
    ):
        perime = Decaissement.objects.get(pk=demande.pk)
        executer_decaissement(demande, administrateur)

        with pytest.raises(ErreurPaiement, match="déjà été exécuté"):
            executer_decaissement(perime, administrateur)

        assert _sequestre(financee).montant_libere == 180000
        assert _fonds_verses(financee) == 1

    def test_le_service_rend_le_decaissement_relu(
        self, financee, demande, administrateur
    ):
        perime = Decaissement.objects.get(pk=demande.pk)

        rendu = executer_decaissement(perime, administrateur)

        assert rendu.statut == Decaissement.Statut.EXECUTE
        assert rendu.execute_par == administrateur


class TestJeuDeDemonstration:
    def test_le_jeu_de_demonstration_se_charge_avec_un_sequestre_coherent(self):
        from django.core.management import call_command

        call_command("charger_demo", synchroniser=True)

        assert Sequestre.objects.exists()
        for sequestre in Sequestre.objects.all():
            assert (
                sequestre.montant_libere + sequestre.montant_rembourse
                <= sequestre.montant_consigne
            )
        assert Campagne.objects.filter(
            statut=Campagne.Statut.FINANCEE,
            decaissement__statut=Decaissement.Statut.DEMANDE,
        ).exists()


def _lancer_en_fil(action):
    """Joue `action` dans un fil à connexion propre ; rend (fil, résultats)."""
    resultats: list = []

    def _corps():
        try:
            resultats.append(action())
        except ErreurPaiement as erreur:
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

    def _preparer(self, connecte, campagne, ama, yao):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json")
        campagne.refresh_from_db()
        return campagne, demander_decaissement(campagne)

    def test_deux_executions_simultanees_ne_paient_qu_une_fois(
        self, connecte, campagne, ama, yao, administrateur
    ):
        campagne, demande = self._preparer(connecte, campagne, ama, yao)
        with transaction.atomic():
            executer_decaissement(demande, administrateur)
            fil, resultats = _lancer_en_fil(
                lambda: executer_decaissement(
                    Decaissement.objects.get(pk=demande.pk), administrateur))
            fil.join(timeout=0.5)
            assert fil.is_alive(), "le second doit attendre le verrou"
        fil.join(timeout=10)

        assert isinstance(resultats[0], ErreurPaiement)
        assert "déjà été exécuté" in str(resultats[0])
        assert _sequestre(campagne).montant_libere == 180000
        assert _fonds_verses(campagne) == 1

    @pytest.mark.parametrize("annulation_d_abord", [True, False])
    def test_l_execution_et_l_annulation_simultanees_ne_paient_pas_deux_fois(
        self, connecte, campagne, ama, yao, administrateur, annulation_d_abord
    ):
        campagne, demande = self._preparer(connecte, campagne, ama, yao)
        premiere = (lambda: annuler(campagne, "test")) if annulation_d_abord else (
            lambda: executer_decaissement(demande, administrateur))
        seconde = (lambda: executer_decaissement(
            Decaissement.objects.get(pk=demande.pk), administrateur)
        ) if annulation_d_abord else (
            lambda: annuler(Campagne.objects.get(pk=campagne.pk), "test"))
        with transaction.atomic():
            premiere()
            fil, resultats = _lancer_en_fil(seconde)
            fil.join(timeout=0.5)
            assert fil.is_alive()
        fil.join(timeout=10)

        assert isinstance(resultats[0], ErreurPaiement)
        sequestre = _sequestre(campagne)
        assert sequestre.montant_libere + sequestre.montant_rembourse <= (
            sequestre.montant_consigne)
        assert (sequestre.montant_libere == 0) == annulation_d_abord

    def test_l_execution_et_la_mise_a_disposition_simultanees_restent_coherentes(
        self, connecte, campagne, ama, yao, administrateur
    ):
        campagne, demande = self._preparer(connecte, campagne, ama, yao)
        with transaction.atomic():
            # Le verrou est pris par le bloc externe : PostgreSQL libère ceux
            # d'un point de sauvegarde annulé, on ne peut donc pas compter
            # sur la tentative qui échoue pour le garder.
            Campagne.objects.select_for_update().get(pk=campagne.pk)
            with pytest.raises(ErreurPaiement):
                mettre_a_disposition(campagne, "Boutique")
            fil, resultats = _lancer_en_fil(
                lambda: executer_decaissement(
                    Decaissement.objects.get(pk=demande.pk), administrateur))
            fil.join(timeout=0.5)
            assert fil.is_alive(), "l'exécution doit attendre le verrou"
        fil.join(timeout=10)

        assert resultats[0].statut == Decaissement.Statut.EXECUTE
        assert not Participation.objects.filter(
            campagne=campagne, statut=Participation.Statut.PRETE).exists()
        assert mettre_a_disposition(
            Campagne.objects.get(pk=campagne.pk), "Boutique") == 2
        assert _sequestre(campagne).montant_libere == 180000
