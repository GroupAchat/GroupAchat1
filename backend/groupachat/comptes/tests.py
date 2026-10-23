# -*- coding: utf-8 -*-
"""Parcours d'inscription, de vérification et de dépôt de dossier."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from groupachat.comptes.models import CodeVerification, DossierKYC, Utilisateur

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def inscrire(client, telephone="+228 91 00 22 33", **extra):
    charge = {
        "nom": "Mensah",
        "prenom": "Ama",
        "telephone": telephone,
        "mot_de_passe": "mdpSolide2026",
    }
    charge.update(extra)
    return client.post("/api/comptes/inscription/", charge, format="json")


class TestInscription:
    def test_le_numero_est_normalise(self, client):
        reponse = inscrire(client)
        assert reponse.status_code == 201, reponse.data
        assert reponse.data["utilisateur"]["telephone"] == "91002233"
        assert reponse.data["utilisateur"]["telephone_verifie"] is False

    def test_le_code_est_rendu_tant_que_le_sms_est_simule(self, client):
        reponse = inscrire(client)
        verification = reponse.data["verification"]
        assert verification["sms_simule"] is True
        assert len(verification["code_affiche"]) == 6

    def test_le_doublon_est_vu_malgre_une_autre_ecriture(self, client):
        inscrire(client, telephone="91002233")
        reponse = inscrire(client, telephone="+228 91 00 22 33")
        assert reponse.status_code == 400
        assert "telephone" in reponse.data

    def test_mot_de_passe_trop_faible_refuse(self, client):
        reponse = inscrire(client, mot_de_passe="12345678")
        assert reponse.status_code == 400
        assert "mot_de_passe" in reponse.data

    def test_numero_trop_court_refuse(self, client):
        reponse = inscrire(client, telephone="9100")
        assert reponse.status_code == 400


class TestVerification:
    def test_le_bon_code_verifie_et_ouvre_la_session(self, client):
        code = inscrire(client).data["verification"]["code_affiche"]
        reponse = client.post(
            "/api/comptes/verification/",
            {"telephone": "91002233", "code": code},
            format="json",
        )
        assert reponse.status_code == 200
        assert reponse.data["utilisateur"]["telephone_verifie"] is True
        # Session ouverte dans la foulée : pas de mot de passe à ressaisir.
        assert client.get("/api/comptes/moi/").status_code == 200

    def test_un_mauvais_code_decompte_les_essais(self, client):
        inscrire(client)
        reponse = client.post(
            "/api/comptes/verification/",
            {"telephone": "91002233", "code": "000000"},
            format="json",
        )
        assert reponse.status_code == 400
        assert reponse.data["essais_restants"] == CodeVerification.MAX_TENTATIVES - 1

    def test_le_code_est_a_usage_unique(self, client):
        code = inscrire(client).data["verification"]["code_affiche"]
        client.post(
            "/api/comptes/verification/",
            {"telephone": "91002233", "code": code},
            format="json",
        )
        rejeu = client.post(
            "/api/comptes/verification/",
            {"telephone": "91002233", "code": code},
            format="json",
        )
        assert rejeu.data["detail"] == "Ce numéro est déjà vérifié."

    def test_un_code_neuf_perime_le_precedent(self, client):
        ancien = inscrire(client).data["verification"]["code_affiche"]
        client.post("/api/comptes/renvoyer-code/", {"telephone": "91002233"},
                    format="json")
        reponse = client.post(
            "/api/comptes/verification/",
            {"telephone": "91002233", "code": ancien},
            format="json",
        )
        assert reponse.status_code == 400

    def test_numero_inconnu_ne_dit_pas_qu_il_est_inconnu(self, client):
        """Cette route ne doit pas servir d'annuaire des inscrits."""
        reponse = client.post(
            "/api/comptes/renvoyer-code/", {"telephone": "99999999"}, format="json"
        )
        assert reponse.status_code == 200
        assert "code_affiche" not in reponse.data


class TestConnexion:
    def test_connexion_puis_deconnexion(self, client):
        code = inscrire(client).data["verification"]["code_affiche"]
        client.post("/api/comptes/verification/",
                    {"telephone": "91002233", "code": code}, format="json")
        assert client.post("/api/comptes/deconnexion/").status_code == 204
        assert client.get("/api/comptes/moi/").status_code in (401, 403)

        reponse = client.post(
            "/api/comptes/connexion/",
            {"telephone": "+22891002233", "mot_de_passe": "mdpSolide2026"},
            format="json",
        )
        assert reponse.status_code == 200
        assert client.get("/api/comptes/moi/").status_code == 200

    def test_mauvais_mot_de_passe_refuse(self, client):
        inscrire(client)
        reponse = client.post(
            "/api/comptes/connexion/",
            {"telephone": "91002233", "mot_de_passe": "faux"},
            format="json",
        )
        assert reponse.status_code == 401

    def test_un_compte_non_verifie_recoit_un_code_a_la_connexion(self, client):
        inscrire(client)
        reponse = client.post(
            "/api/comptes/connexion/",
            {"telephone": "91002233", "mot_de_passe": "mdpSolide2026"},
            format="json",
        )
        assert reponse.status_code == 200
        assert "code_affiche" in reponse.data["verification"]


@pytest.fixture
def client_verifie(client) -> APIClient:
    code = inscrire(client).data["verification"]["code_affiche"]
    client.post("/api/comptes/verification/",
                {"telephone": "91002233", "code": code}, format="json")
    return client


DOSSIER = {
    "type_piece": "cni",
    "numero_piece": "CNI-9087",
    "numero_mobile_money": "+228 91 00 22 33",
    "nom_commerce": "Ama Import",
}


class TestDossierKYC:
    def test_un_numero_non_verifie_ne_peut_pas_deposer(self, client):
        inscrire(client)
        client.post("/api/comptes/connexion/",
                    {"telephone": "91002233", "mot_de_passe": "mdpSolide2026"},
                    format="json")
        assert client.post("/api/comptes/dossier/", DOSSIER,
                           format="json").status_code == 403

    def test_le_depot_bascule_le_role_sans_ouvrir_l_acces(self, client_verifie):
        reponse = client_verifie.post("/api/comptes/dossier/", DOSSIER, format="json")
        assert reponse.status_code == 201
        assert reponse.data["statut"] == "en_attente"
        assert reponse.data["numero_mobile_money"] == "91002233"

        ama = Utilisateur.objects.get(telephone="91002233")
        assert ama.role == Utilisateur.Role.GROUPEUR
        assert ama.est_groupeur_valide is False

    def test_second_depot_refuse_pendant_l_examen(self, client_verifie):
        client_verifie.post("/api/comptes/dossier/", DOSSIER, format="json")
        reponse = client_verifie.post("/api/comptes/dossier/", DOSSIER, format="json")
        assert reponse.status_code == 409

    def test_redepot_apres_rejet_efface_le_motif(self, client_verifie):
        client_verifie.post("/api/comptes/dossier/", DOSSIER, format="json")
        dossier = DossierKYC.objects.get()
        dossier.statut = DossierKYC.Statut.REJETE
        dossier.motif_rejet = "Pièce illisible"
        dossier.save()

        reponse = client_verifie.post("/api/comptes/dossier/", DOSSIER, format="json")
        assert reponse.status_code == 201
        assert reponse.data["statut"] == "en_attente"
        assert reponse.data["motif_rejet"] == ""
        assert DossierKYC.objects.count() == 1, "le dossier est réécrit, pas doublonné"

    def test_l_acces_s_ouvre_a_la_validation(self, client_verifie):
        client_verifie.post("/api/comptes/dossier/", DOSSIER, format="json")
        dossier = DossierKYC.objects.get()
        dossier.statut = DossierKYC.Statut.VALIDE
        dossier.save()

        ama = Utilisateur.objects.get(telephone="91002233")
        assert ama.est_groupeur_valide is True
