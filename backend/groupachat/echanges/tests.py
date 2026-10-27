# -*- coding: utf-8 -*-
"""Fil de discussion, espace communautaire et cloche."""

from __future__ import annotations

import importlib

import pytest
from django.apps import apps as django_apps
from django.db import migrations

from groupachat.echanges.models import Commentaire, DemandeProduit, Notification

pytestmark = pytest.mark.django_db


def fil(campagne) -> str:
    return f"/api/campagnes/{campagne.id}/commentaires/"


class TestFilPublic:
    def test_le_fil_se_lit_sans_compte(self, client, campagne, ama):
        Commentaire.objects.create(campagne=campagne, auteur=ama,
                                   texte="C'est du riz parfumé ?")
        reponse = client.get(fil(campagne))
        assert reponse.status_code == 200
        assert reponse.data["count"] == 1

    def test_mais_on_n_ecrit_pas_sans_compte(self, client, campagne):
        reponse = client.post(fil(campagne), {"texte": "Coucou"}, format="json")
        assert reponse.status_code in (401, 403)

    def test_un_numero_non_verifie_n_ecrit_pas(self, connecte, campagne, ama):
        ama.telephone_verifie = False
        ama.save()
        reponse = connecte(ama).post(fil(campagne), {"texte": "Faux avis"},
                                     format="json")
        assert reponse.status_code == 403

    def test_l_auteur_n_est_pas_identifiable_par_son_numero(
        self, client, campagne, ama
    ):
        Commentaire.objects.create(campagne=campagne, auteur=ama, texte="Bonjour")
        message = client.get(fil(campagne)).data["results"][0]
        assert message["auteur"]["nom_affiche"] == "Ama M."
        assert "telephone" not in message["auteur"]

    def test_la_reponse_du_groupeur_se_distingue(
        self, connecte, campagne, ama, groupeur
    ):
        question = connecte(ama).post(fil(campagne), {"texte": "Quelle origine ?"},
                                      format="json").data
        connecte(groupeur).post(
            fil(campagne), {"texte": "Thaïlande.", "reponse_a": question["id"]},
            format="json",
        )
        racine = connecte(ama).get(fil(campagne)).data["results"][0]
        assert racine["est_du_groupeur"] is False
        assert racine["reponses"][0]["est_du_groupeur"] is True

    def test_on_ne_repond_pas_a_une_reponse(self, connecte, campagne, ama, groupeur):
        question = connecte(ama).post(fil(campagne), {"texte": "Origine ?"},
                                      format="json").data
        reponse = connecte(groupeur).post(
            fil(campagne), {"texte": "Thaïlande.", "reponse_a": question["id"]},
            format="json",
        ).data
        trop_loin = connecte(ama).post(
            fil(campagne), {"texte": "Merci", "reponse_a": reponse["id"]},
            format="json",
        )
        assert trop_loin.status_code == 400

    def test_un_message_notifie_le_groupeur(self, connecte, campagne, ama, groupeur):
        connecte(ama).post(fil(campagne), {"texte": "Disponible en 50 kg ?"},
                           format="json")
        assert Notification.objects.filter(
            destinataire=groupeur, genre=Notification.Genre.NOUVEAU_COMMENTAIRE
        ).exists()

    def test_une_reponse_notifie_l_auteur_du_message(
        self, connecte, campagne, ama, groupeur
    ):
        question = connecte(ama).post(fil(campagne), {"texte": "Origine ?"},
                                      format="json").data
        connecte(groupeur).post(
            fil(campagne), {"texte": "Thaïlande.", "reponse_a": question["id"]},
            format="json",
        )
        assert Notification.objects.filter(
            destinataire=ama, genre=Notification.Genre.REPONSE_COMMENTAIRE
        ).exists()

    def test_on_ne_modifie_pas_le_message_d_un_autre(
        self, connecte, campagne, ama, yao
    ):
        message = connecte(ama).post(fil(campagne), {"texte": "À moi"},
                                     format="json").data
        reponse = connecte(yao).patch(
            f"{fil(campagne)}{message['id']}/", {"texte": "Détourné"}, format="json"
        )
        assert reponse.status_code == 403

    def test_retirer_son_message_le_masque_sans_l_effacer(
        self, connecte, campagne, ama
    ):
        message = connecte(ama).post(fil(campagne), {"texte": "Oups"},
                                     format="json").data
        connecte(ama).delete(f"{fil(campagne)}{message['id']}/")
        assert connecte(ama).get(fil(campagne)).data["count"] == 0
        assert Commentaire.objects.filter(id=message["id"]).exists()


class TestJaime:
    def test_aimer_puis_retirer_son_jaime(self, connecte, campagne, ama, yao):
        message = connecte(ama).post(fil(campagne), {"texte": "Bon prix !"},
                                     format="json").data
        chemin = f"{fil(campagne)}{message['id']}/jaime/"

        premier = connecte(yao).post(chemin, {}, format="json")
        assert premier.data == {"jaime_par_moi": True, "nombre_jaime": 1}

        second = connecte(yao).post(chemin, {}, format="json")
        assert second.data == {"jaime_par_moi": False, "nombre_jaime": 0}

    def test_le_compteur_ne_compte_chaque_personne_qu_une_fois(
        self, connecte, campagne, ama, yao
    ):
        message = connecte(ama).post(fil(campagne), {"texte": "Bon prix !"},
                                     format="json").data
        chemin = f"{fil(campagne)}{message['id']}/jaime/"
        connecte(yao).post(chemin, {}, format="json")
        connecte(ama).post(chemin, {}, format="json")
        assert connecte(ama).get(fil(campagne)).data["results"][0]["nombre_jaime"] == 2

    def test_le_lecteur_voit_ce_qu_il_a_deja_aime(self, connecte, campagne, ama, yao):
        message = connecte(ama).post(fil(campagne), {"texte": "Bon prix !"},
                                     format="json").data
        connecte(yao).post(f"{fil(campagne)}{message['id']}/jaime/", {}, format="json")
        vu_par_yao = connecte(yao).get(fil(campagne)).data["results"][0]
        assert vu_par_yao["jaime_par_moi"] is True


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


class TestCorrectionDesAnciensLiens:
    """F-008 : la migration 0004 répare les liens écrits avant le correctif."""

    def _migration(self):
        return importlib.import_module(
            "groupachat.echanges.migrations.0004_corriger_liens_des_notifications"
        )

    def _creer(self, ama, lien):
        return Notification.objects.create(
            destinataire=ama, genre="paiement_enregistre", titre="t",
            message="m", lien=lien,
        )

    def test_l_ancien_lien_de_la_commande_est_reecrit(self, ama):
        ancienne = self._creer(ama, "/participations/7")
        self._migration().corriger(django_apps, None)
        ancienne.refresh_from_db()
        assert ancienne.lien == "/mes-achats/7"

    def test_les_autres_liens_ne_sont_pas_touches(self, ama):
        intacts = ["", "/campagnes/7", "/groupeur/campagnes/7", "/groupeur",
                   "/participations/7/x", "/api/participations/7",
                   "/participations/abc", "/mes-achats/7"]
        lignes = [self._creer(ama, lien) for lien in intacts]
        self._migration().corriger(django_apps, None)
        for ligne, lien in zip(lignes, intacts):
            ligne.refresh_from_db()
            assert ligne.lien == lien

    def test_la_correction_se_rejoue_sans_effet(self, ama):
        ligne = self._creer(ama, "/participations/12")
        self._migration().corriger(django_apps, None)
        self._migration().corriger(django_apps, None)
        ligne.refresh_from_db()
        assert ligne.lien == "/mes-achats/12"

    def test_le_retour_de_la_migration_ne_touche_a_rien(self, ama):
        """Le retour est neutre : il ne doit pas casser un lien correct."""
        ligne = self._creer(ama, "/mes-achats/9")
        operation = self._migration().Migration.operations[0]
        assert operation.reverse_code is migrations.RunPython.noop
        operation.reverse_code(django_apps, None)
        ligne.refresh_from_db()
        assert ligne.lien == "/mes-achats/9"
