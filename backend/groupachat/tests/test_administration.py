# -*- coding: utf-8 -*-
"""Console d'administration : KYC, modération, supervision."""

from __future__ import annotations

import pytest

from groupachat.comptes.models import DossierKYC, Reputation
from groupachat.echanges.models import Commentaire, Notification

pytestmark = pytest.mark.django_db


class TestAccesConsole:
    def test_un_acheteur_n_entre_pas(self, connecte, ama):
        assert connecte(ama).get("/api/admin/dossiers/").status_code == 403

    def test_un_groupeur_valide_non_plus(self, connecte, groupeur):
        assert connecte(groupeur).get("/api/admin/tableau-de-bord/").status_code == 403

    def test_l_administrateur_entre(self, connecte, administrateur):
        assert connecte(administrateur).get("/api/admin/dossiers/").status_code == 200


class TestDecisionKYC:
    def test_la_validation_ouvre_l_espace_et_cree_la_reputation(
        self, connecte, administrateur, groupeur_en_attente
    ):
        dossier = DossierKYC.objects.get(utilisateur=groupeur_en_attente)
        reponse = connecte(administrateur).post(
            f"/api/admin/dossiers/{dossier.id}/decision/",
            {"decision": "valider"}, format="json",
        )
        assert reponse.status_code == 200
        assert reponse.data["statut"] == "valide"

        groupeur_en_attente.refresh_from_db()
        assert groupeur_en_attente.est_groupeur_valide is True
        assert connecte(groupeur_en_attente).get(
            "/api/groupeur/campagnes/"
        ).status_code == 200

        reputation = Reputation.objects.get(groupeur=groupeur_en_attente)
        assert reputation.note == 0, "la note se gagne, elle n'est pas offerte"

    def test_le_rejet_exige_un_motif(self, connecte, administrateur,
                                    groupeur_en_attente):
        dossier = DossierKYC.objects.get(utilisateur=groupeur_en_attente)
        reponse = connecte(administrateur).post(
            f"/api/admin/dossiers/{dossier.id}/decision/",
            {"decision": "rejeter"}, format="json",
        )
        assert reponse.status_code == 400
        assert "motif" in reponse.data

    def test_le_rejet_motive_laisse_la_porte_fermee(
        self, connecte, administrateur, groupeur_en_attente
    ):
        dossier = DossierKYC.objects.get(utilisateur=groupeur_en_attente)
        connecte(administrateur).post(
            f"/api/admin/dossiers/{dossier.id}/decision/",
            {"decision": "rejeter", "motif": "Pièce illisible"}, format="json",
        )
        groupeur_en_attente.refresh_from_db()
        assert groupeur_en_attente.est_groupeur_valide is False
        assert connecte(groupeur_en_attente).get(
            "/api/groupeur/campagnes/"
        ).status_code == 403

    def test_le_groupeur_est_prevenu_de_la_decision(
        self, connecte, administrateur, groupeur_en_attente
    ):
        dossier = DossierKYC.objects.get(utilisateur=groupeur_en_attente)
        connecte(administrateur).post(
            f"/api/admin/dossiers/{dossier.id}/decision/",
            {"decision": "valider"}, format="json",
        )
        assert Notification.objects.filter(
            destinataire=groupeur_en_attente,
            genre=Notification.Genre.KYC_DECIDE,
        ).exists()

    def test_un_dossier_deja_tranche_ne_se_rejuge_pas(
        self, connecte, administrateur, groupeur_en_attente
    ):
        dossier = DossierKYC.objects.get(utilisateur=groupeur_en_attente)
        chemin = f"/api/admin/dossiers/{dossier.id}/decision/"
        api = connecte(administrateur)
        assert api.post(chemin, {"decision": "valider"}, format="json").status_code == 200
        assert api.post(chemin, {"decision": "rejeter", "motif": "Non"},
                        format="json").status_code == 409

    def test_la_liste_montre_les_dossiers_en_attente(
        self, connecte, administrateur, groupeur_en_attente, groupeur
    ):
        resultats = connecte(administrateur).get("/api/admin/dossiers/").data["results"]
        assert len(resultats) == 1, "le dossier déjà validé n'a plus à être traité"
        assert resultats[0]["utilisateur"]["telephone"] == "90009988"


class TestModeration:
    def test_masquer_retire_du_fil_sans_effacer(
        self, connecte, administrateur, campagne, ama
    ):
        message = Commentaire.objects.create(
            campagne=campagne, auteur=ama, texte="Propos déplacés"
        )
        reponse = connecte(administrateur).post(
            f"/api/admin/commentaires/{message.id}/masquer/",
            {"motif": "Propos diffamatoires"}, format="json",
        )
        assert reponse.status_code == 200

        message.refresh_from_db()
        assert message.est_visible is False
        assert message.masque_par == administrateur
        assert message.motif_masquage == "Propos diffamatoires"

        public = connecte(ama).get(f"/api/campagnes/{campagne.id}/commentaires/")
        assert public.data["count"] == 0
        assert Commentaire.objects.filter(id=message.id).exists()

    def test_retablir_le_remet_dans_le_fil(
        self, connecte, administrateur, campagne, ama
    ):
        message = Commentaire.objects.create(campagne=campagne, auteur=ama,
                                             texte="Malentendu")
        api = connecte(administrateur)
        api.post(f"/api/admin/commentaires/{message.id}/masquer/", {}, format="json")
        api.post(f"/api/admin/commentaires/{message.id}/retablir/", {}, format="json")

        message.refresh_from_db()
        assert message.est_visible is True
        assert connecte(ama).get(
            f"/api/campagnes/{campagne.id}/commentaires/"
        ).data["count"] == 1


class TestTableauDeBord:
    def test_il_montre_ce_qu_il_y_a_a_traiter(
        self, connecte, administrateur, groupeur_en_attente, groupeur
    ):
        donnees = connecte(administrateur).get("/api/admin/tableau-de-bord/").data
        assert donnees["a_traiter"]["dossiers_kyc"] == 1
        assert donnees["comptes"]["groupeurs"] == 2
        assert donnees["comptes"]["groupeurs_valides"] == 1

    def test_il_montre_l_argent_detenu_en_sequestre(
        self, connecte, administrateur, campagne, ama
    ):
        api = connecte(ama)
        identifiant = api.post("/api/participations/",
                               {"campagne": campagne.id, "quantite": 5},
                               format="json").data["id"]
        api.post(f"/api/participations/{identifiant}/payer/", {}, format="json")

        donnees = connecte(administrateur).get("/api/admin/tableau-de-bord/").data
        assert donnees["sequestre"]["montant_detenu"] == 90000
        assert donnees["sequestre"]["total_libere"] == 0
        assert donnees["transactions_simulees"] == 1

    def test_il_montre_les_frais_encaisses_apres_decaissement(
        self, connecte, administrateur, campagne, ama
    ):
        api = connecte(ama)
        identifiant = api.post("/api/participations/",
                               {"campagne": campagne.id, "quantite": 10},
                               format="json").data["id"]
        api.post(f"/api/participations/{identifiant}/payer/", {}, format="json")

        groupeur_api = connecte(campagne.groupeur)
        groupeur_api.post(f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {},
                          format="json")
        groupeur_api.post(f"/api/groupeur/campagnes/{campagne.id}/demander-retrait/",
                          {}, format="json")

        admin_api = connecte(administrateur)
        decaissement = admin_api.get("/api/admin/decaissements/").data["results"][0]
        admin_api.post(f"/api/admin/decaissements/{decaissement['id']}/executer/",
                       {}, format="json")

        donnees = admin_api.get("/api/admin/tableau-de-bord/").data
        assert donnees["revenus"]["frais_encaisses"] == 1500
        assert donnees["sequestre"]["montant_detenu"] == 0
