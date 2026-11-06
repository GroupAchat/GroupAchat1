# -*- coding: utf-8 -*-
"""Espace communautaire et cloche de notifications.

Le fil public n'existe plus : ce qui le remplace, le Contact Privé, a
ses propres tests dans `groupachat/tests/test_contact_prive.py`.
"""

from __future__ import annotations

import pytest

from groupachat.echanges.models import DemandeProduit, Notification

pytestmark = pytest.mark.django_db


class TestEspaceCommunautaire:
    def test_publier_une_demande_de_produit(self, connecte, ama, categorie):
        reponse = connecte(ama).post(
            "/api/demandes/",
            {"titre": "Panneaux solaires 200 W", "description": "Pour la maison.",
             "categorie": categorie.id, "budget_indicatif": 120000},
            format="json",
        )
        assert reponse.status_code == 201
        assert reponse.data["statut"] == "ouverte"
        assert reponse.data["nombre_interets"] == 0

    def test_les_demandes_se_lisent_sans_compte(self, client, connecte, ama):
        connecte(ama).post("/api/demandes/", {"titre": "Ciment"}, format="json")
        client.force_authenticate(user=None)
        assert client.get("/api/demandes/").data["count"] == 1

    def test_moi_aussi_compte_une_fois_par_personne(self, connecte, ama, yao):
        demande = connecte(ama).post("/api/demandes/", {"titre": "Ciment"},
                                     format="json").data
        chemin = f"/api/demandes/{demande['id']}/moi-aussi/"

        assert connecte(yao).post(chemin, {}, format="json").data == {
            "interesse": True, "nombre_interets": 1
        }
        assert connecte(yao).post(chemin, {}, format="json").data == {
            "interesse": False, "nombre_interets": 0
        }

    def test_les_demandes_sortent_par_interet_decroissant(self, connecte, ama, yao):
        api = connecte(ama)
        peu = api.post("/api/demandes/", {"titre": "Peu demandé"}, format="json").data
        beaucoup = api.post("/api/demandes/", {"titre": "Très demandé"},
                            format="json").data
        connecte(yao).post(f"/api/demandes/{beaucoup['id']}/moi-aussi/", {},
                           format="json")

        titres = [d["titre"] for d in connecte(ama).get("/api/demandes/").data["results"]]
        assert titres == ["Très demandé", "Peu demandé"]
        assert peu["titre"] == "Peu demandé"


class TestCloche:
    def test_chacun_ne_voit_que_ses_notifications(self, connecte, campagne, ama, yao):
        Notification.objects.create(destinataire=ama, genre="paiement_enregistre",
                                    titre="Pour Ama", message="…")
        Notification.objects.create(destinataire=yao, genre="paiement_enregistre",
                                    titre="Pour Yao", message="…")
        resultats = connecte(ama).get("/api/notifications/").data["results"]
        assert [n["titre"] for n in resultats] == ["Pour Ama"]

    def test_le_compteur_de_non_lues(self, connecte, ama):
        for index in range(3):
            Notification.objects.create(destinataire=ama, genre="paiement_enregistre",
                                        titre=f"Avis {index}", message="…")
        api = connecte(ama)
        assert api.get("/api/notifications/non-lues/").data["non_lues"] == 3

        premiere = api.get("/api/notifications/").data["results"][0]["id"]
        api.post(f"/api/notifications/{premiere}/marquer-lue/", {}, format="json")
        assert api.get("/api/notifications/non-lues/").data["non_lues"] == 2

        api.post("/api/notifications/tout-marquer-lu/", {}, format="json")
        assert api.get("/api/notifications/non-lues/").data["non_lues"] == 0
