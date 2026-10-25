# -*- coding: utf-8 -*-
"""Le parcours complet : participer, payer, clôturer, décaisser, retirer."""

from __future__ import annotations

import pytest
from django.utils import timezone

from groupachat.catalogue.models import Campagne, PalierPrix
from groupachat.commandes.models import Participation
from groupachat.comptes.models import Reputation
from groupachat.echanges.models import Notification
from groupachat.paiements.models import Decaissement, Sequestre, Transaction

pytestmark = pytest.mark.django_db


def participer_et_payer(connecte, acheteur, campagne, quantite=5):
    api = connecte(acheteur)
    reponse = api.post(
        "/api/participations/",
        {"campagne": campagne.id, "quantite": quantite},
        format="json",
    )
    assert reponse.status_code == 201, reponse.data
    identifiant = reponse.data["id"]
    paiement = api.post(
        f"/api/participations/{identifiant}/payer/",
        {"operateur": "tmoney"},
        format="json",
    )
    assert paiement.status_code == 200, paiement.data
    return paiement.data


class TestParticipation:
    def test_un_numero_non_verifie_ne_peut_pas_participer(
        self, client, campagne, ama
    ):
        ama.telephone_verifie = False
        ama.save()
        client.force_authenticate(user=ama)
        reponse = client.post("/api/participations/",
                              {"campagne": campagne.id, "quantite": 1}, format="json")
        assert reponse.status_code == 403

    def test_le_groupeur_ne_participe_pas_a_sa_propre_campagne(
        self, connecte, campagne, groupeur
    ):
        reponse = connecte(groupeur).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        )
        assert reponse.status_code == 400

    def test_le_prix_est_celui_du_palier_atteint_avec_cette_part(
        self, connecte, campagne, ama
    ):
        PalierPrix.objects.create(campagne=campagne, quantite_min=5, prix_unitaire=16500)
        reponse = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 5},
            format="json",
        )
        assert reponse.data["prix_unitaire_applique"] == 16500
        assert reponse.data["montant_total"] == 82500

    def test_pas_de_code_avant_paiement(self, connecte, campagne, ama):
        reponse = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        )
        assert reponse.data["code_retrait"] is None
        assert reponse.data["charge_qr"] is None

    def test_une_collecte_close_refuse_les_nouvelles_parts(
        self, connecte, campagne, ama
    ):
        campagne.statut = Campagne.Statut.FINANCEE
        campagne.save()
        reponse = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        )
        assert reponse.status_code == 400

    def test_le_maximum_de_pieces_est_respecte(self, connecte, campagne, ama, yao):
        campagne.quantite_maximale = 6
        campagne.save()
        participer_et_payer(connecte, ama, campagne, quantite=5)
        reponse = connecte(yao).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 3},
            format="json",
        )
        assert reponse.status_code == 400
        assert "1 pièce" in str(reponse.data)


class TestPaiementSimule:
    def test_le_paiement_consigne_au_sequestre_et_delivre_le_code(
        self, connecte, campagne, ama
    ):
        donnees = participer_et_payer(connecte, ama, campagne, quantite=5)
        part = donnees["participation"]

        assert part["statut"] == "payee"
        assert len(part["code_retrait"]) == 8
        assert part["charge_qr"] == f"GA|{campagne.id}|{part['code_retrait']}"
        assert donnees["transaction"]["simulee"] is True
        assert donnees["transaction"]["reference"].startswith("SIM-")

        sequestre = Sequestre.objects.get(campagne=campagne)
        assert sequestre.montant_consigne == 90000
        assert sequestre.solde == 90000, "l'argent n'est pas allé au groupeur"

    def test_le_paiement_notifie_l_acheteur_et_le_groupeur(
        self, connecte, campagne, ama, groupeur
    ):
        participer_et_payer(connecte, ama, campagne, quantite=5)

        chez_ama = Notification.objects.filter(destinataire=ama)
        assert chez_ama.filter(genre=Notification.Genre.PAIEMENT_ENREGISTRE).exists()

        chez_groupeur = Notification.objects.filter(destinataire=groupeur)
        suivi = chez_groupeur.get(genre=Notification.Genre.PAIEMENT_RECU)
        assert "Ama Mensah a payé" in suivi.message, "le suivi est nominatif"

    def test_le_minimum_atteint_previent_le_groupeur(
        self, connecte, campagne, ama, groupeur
    ):
        participer_et_payer(connecte, ama, campagne, quantite=10)
        assert Notification.objects.filter(
            destinataire=groupeur, genre=Notification.Genre.MINIMUM_ATTEINT
        ).exists()

    def test_on_ne_paie_pas_deux_fois(self, connecte, campagne, ama):
        api = connecte(ama)
        identifiant = api.post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 2},
            format="json",
        ).data["id"]
        assert api.post(f"/api/participations/{identifiant}/payer/",
                        {}, format="json").status_code == 200
        rejeu = api.post(f"/api/participations/{identifiant}/payer/", {}, format="json")
        assert rejeu.status_code == 400

    def test_la_part_d_un_autre_est_introuvable(self, connecte, campagne, ama, yao):
        identifiant = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        ).data["id"]
        assert connecte(yao).get(
            f"/api/participations/{identifiant}/"
        ).status_code == 404


class TestClotureReussie:
    def test_minimum_atteint_la_campagne_est_financee(
        self, connecte, campagne, ama, yao
    ):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)

        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.FINANCEE
        assert Sequestre.objects.get(campagne=campagne).statut == Sequestre.Statut.BLOQUE
        assert Notification.objects.filter(
            destinataire=ama, genre=Notification.Genre.CAMPAGNE_FINANCEE
        ).exists()


class TestClotureEchouee:
    """Minimum manqué : la collecte se ferme, **l'argent ne bouge pas**.

    Ce test affirmait l'inverse — remboursement immédiat à la clôture.
    C'était une erreur de conception : un groupeur peut vouloir maintenir
    la commande malgré le nombre, et rembourser d'office la lui retirerait.
    Le remboursement demande désormais une décision.
    """

    def test_la_cloture_laisse_l_argent_consigne(self, connecte, campagne, ama, yao):
        participer_et_payer(connecte, ama, campagne, quantite=3)
        participer_et_payer(connecte, yao, campagne, quantite=2)

        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.MINIMUM_NON_ATTEINT

        for acheteur in (ama, yao):
            part = Participation.objects.get(acheteur=acheteur)
            assert part.statut == Participation.Statut.PAYEE
            assert Notification.objects.filter(
                destinataire=acheteur,
                genre=Notification.Genre.GROUPAGE_NON_ABOUTI,
            ).exists()

        sequestre = Sequestre.objects.get(campagne=campagne)
        assert sequestre.solde == 90000, "rien ne doit sortir du séquestre"
        assert not Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).exists()

    def test_le_remboursement_suit_la_decision_du_groupeur(
        self, connecte, campagne, ama, yao
    ):
        participer_et_payer(connecte, ama, campagne, quantite=3)
        participer_et_payer(connecte, yao, campagne, quantite=2)

        api = connecte(campagne.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json")
        api.post(f"/api/groupeur/campagnes/{campagne.id}/annuler/", {}, format="json")

        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.ANNULEE

        for acheteur in (ama, yao):
            part = Participation.objects.get(acheteur=acheteur)
            assert part.statut == Participation.Statut.REMBOURSEE
            assert Notification.objects.filter(
                destinataire=acheteur, genre=Notification.Genre.REMBOURSEMENT
            ).exists()

        sequestre = Sequestre.objects.get(campagne=campagne)
        assert sequestre.montant_rembourse == 90000
        assert sequestre.solde == 0, "le séquestre doit être vidé"
        assert sequestre.statut == Sequestre.Statut.REMBOURSE
        assert Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).count() == 2


class TestDecaissement:
    @pytest.fixture
    def campagne_financee(self, connecte, campagne, ama, yao):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        campagne.refresh_from_db()
        return campagne

    def test_le_groupeur_retire_tout_moins_les_frais_fixes(
        self, connecte, campagne_financee
    ):
        reponse = connecte(campagne_financee.groupeur).post(
            f"/api/groupeur/campagnes/{campagne_financee.id}/demander-retrait/",
            {}, format="json",
        )
        assert reponse.status_code == 201, reponse.data
        assert reponse.data["montant_brut"] == 180000
        assert reponse.data["frais"] == 1500
        assert reponse.data["montant_net"] == 178500
        assert reponse.data["numero_mobile_money"] == "90001122"

    def test_un_seul_decaissement_par_campagne(self, connecte, campagne_financee):
        api = connecte(campagne_financee.groupeur)
        chemin = f"/api/groupeur/campagnes/{campagne_financee.id}/demander-retrait/"
        assert api.post(chemin, {}, format="json").status_code == 201
        assert api.post(chemin, {}, format="json").status_code == 400

    def test_l_administrateur_libere_les_fonds(
        self, connecte, campagne_financee, administrateur
    ):
        connecte(campagne_financee.groupeur).post(
            f"/api/groupeur/campagnes/{campagne_financee.id}/demander-retrait/",
            {}, format="json",
        )
        decaissement = Decaissement.objects.get()
        reponse = connecte(administrateur).post(
            f"/api/admin/decaissements/{decaissement.id}/executer/", {}, format="json"
        )
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["statut"] == "execute"

        sequestre = Sequestre.objects.get(campagne=campagne_financee)
        assert sequestre.montant_libere == 180000
        assert sequestre.solde == 0
        campagne_financee.refresh_from_db()
        assert campagne_financee.statut == Campagne.Statut.APPROVISIONNEMENT

    def test_une_campagne_non_financee_ne_se_decaisse_pas(self, connecte, campagne):
        reponse = connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/demander-retrait/", {},
            format="json",
        )
        assert reponse.status_code == 400


class TestDistributionEtRetrait:
    @pytest.fixture
    def campagne_a_distribuer(self, connecte, campagne, ama, yao, administrateur):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)
        api = connecte(campagne.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json")
        api.post(f"/api/groupeur/campagnes/{campagne.id}/demander-retrait/", {},
                 format="json")
        connecte(administrateur).post(
            f"/api/admin/decaissements/{Decaissement.objects.get().id}/executer/",
            {}, format="json",
        )
        campagne.refresh_from_db()
        return campagne

    def test_la_mise_a_disposition_notifie_tous_les_participants(
        self, connecte, campagne_a_distribuer, ama, yao
    ):
        reponse = connecte(campagne_a_distribuer.groupeur).post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
            {"point_remise": "Boutique Abalo, Bè-Kpota"}, format="json",
        )
        assert reponse.status_code == 200
        assert reponse.data["participants_notifies"] == 2

        for acheteur in (ama, yao):
            avis = Notification.objects.get(
                destinataire=acheteur,
                genre=Notification.Genre.MARCHANDISE_DISPONIBLE,
            )
            part = Participation.objects.get(acheteur=acheteur)
            assert "Bè-Kpota" in avis.message, "le point de remise est rappelé"
            assert part.code_retrait in avis.message, "le code est rappelé"
            assert part.statut == Participation.Statut.PRETE

    def test_le_retrait_au_code_dicte(self, connecte, campagne_a_distribuer, ama):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        code = Participation.objects.get(acheteur=ama).code_retrait

        reponse = api.post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/",
            {"code": code.lower()}, format="json",
        )
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["acheteur"] == "Ama Mensah"

        part = Participation.objects.get(acheteur=ama)
        assert part.statut == Participation.Statut.RETIREE
        assert part.remise_par == campagne_a_distribuer.groupeur

    def test_le_retrait_au_qr_scanne(self, connecte, campagne_a_distribuer, ama):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        charge = Participation.objects.get(acheteur=ama).charge_qr

        reponse = api.post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/",
            {"code": charge}, format="json",
        )
        assert reponse.status_code == 200, reponse.data

    def test_un_qr_d_une_autre_campagne_est_refuse(
        self, connecte, campagne_a_distribuer, ama
    ):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        code = Participation.objects.get(acheteur=ama).code_retrait

        reponse = api.post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/",
            {"code": f"GA|999|{code}"}, format="json",
        )
        assert reponse.status_code == 400
        assert "ne concerne pas cette campagne" in reponse.data["detail"]

    def test_un_code_ne_sert_qu_une_fois(self, connecte, campagne_a_distribuer, ama):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        code = Participation.objects.get(acheteur=ama).code_retrait
        chemin = f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/"

        assert api.post(chemin, {"code": code}, format="json").status_code == 200
        rejeu = api.post(chemin, {"code": code}, format="json")
        assert rejeu.status_code == 400
        assert "déjà retiré" in rejeu.data["detail"]

    def test_le_dernier_colis_termine_la_campagne_et_note_le_groupeur(
        self, connecte, campagne_a_distribuer, ama, yao
    ):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        chemin = f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/"

        api.post(chemin, {"code": Participation.objects.get(acheteur=ama).code_retrait},
                 format="json")
        campagne_a_distribuer.refresh_from_db()
        assert campagne_a_distribuer.statut == Campagne.Statut.DISTRIBUTION

        api.post(chemin, {"code": Participation.objects.get(acheteur=yao).code_retrait},
                 format="json")
        campagne_a_distribuer.refresh_from_db()
        assert campagne_a_distribuer.statut == Campagne.Statut.TERMINEE

        reputation = Reputation.objects.get(groupeur=campagne_a_distribuer.groupeur)
        assert reputation.campagnes_terminees == 1
        assert reputation.participants_servis == 2
        assert reputation.note == 5

    def test_un_litige_est_clos_par_le_code_valide(
        self, connecte, campagne_a_distribuer, ama
    ):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        part = Participation.objects.get(acheteur=ama)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/",
                 {"code": part.code_retrait}, format="json")

        reponse = connecte(ama).post(
            "/api/litiges/",
            {"participation": part.id, "motif": "non_livre",
             "description": "Je n'ai rien reçu."},
            format="json",
        )
        assert reponse.status_code == 400
        assert "preuve" in str(reponse.data) or "clos" in str(reponse.data)


class TestAccesEspaceGroupeur:
    def test_un_dossier_en_attente_ferme_l_espace(self, connecte, groupeur_en_attente):
        api = connecte(groupeur_en_attente)
        assert api.get("/api/groupeur/campagnes/").status_code == 403
        assert api.get("/api/groupeur/tableau-de-bord/").status_code == 403

    def test_mais_l_etat_du_dossier_reste_consultable(
        self, connecte, groupeur_en_attente
    ):
        reponse = connecte(groupeur_en_attente).get("/api/groupeur/etat/")
        assert reponse.status_code == 200
        assert reponse.data["acces"] is False
        assert reponse.data["raison"] == "en_attente"

    def test_un_acheteur_n_entre_pas_dans_l_espace_groupeur(self, connecte, ama):
        assert connecte(ama).get("/api/groupeur/campagnes/").status_code == 403

    def test_l_espace_s_ouvre_une_fois_le_dossier_valide(self, connecte, groupeur):
        assert connecte(groupeur).get("/api/groupeur/campagnes/").status_code == 200


class TestCampagneFigee:
    def test_une_campagne_deja_payee_ne_se_modifie_plus(
        self, connecte, campagne, ama
    ):
        participer_et_payer(connecte, ama, campagne, quantite=2)
        reponse = connecte(campagne.groupeur).patch(
            f"/api/groupeur/campagnes/{campagne.id}/",
            {"prix_unitaire": 25000}, format="json",
        )
        assert reponse.status_code == 409
        campagne.refresh_from_db()
        assert campagne.prix_unitaire == 18000
