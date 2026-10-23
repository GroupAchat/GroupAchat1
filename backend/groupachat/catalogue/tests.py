# -*- coding: utf-8 -*-
"""Consultation du catalogue, filtres et jauge d'avancement."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.catalogue.models import Campagne, Categorie, PalierPrix, Produit
from groupachat.commandes.models import Participation
from groupachat.comptes.models import DossierKYC, Reputation, Utilisateur

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def groupeur() -> Utilisateur:
    compte = Utilisateur.objects.create_user(
        "90001122", "mdpSolide2026", nom="Abalo", prenom="Koffi",
        role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
    )
    DossierKYC.objects.create(
        utilisateur=compte, type_piece=DossierKYC.TypePiece.CNI,
        numero_piece="CNI-1", numero_mobile_money="90001122",
        nom_commerce="Abalo Import", statut=DossierKYC.Statut.VALIDE,
    )
    Reputation.objects.create(groupeur=compte, note=4.5, campagnes_terminees=3)
    return compte


@pytest.fixture
def rayons() -> dict:
    alimentation = Categorie.objects.create(nom="Alimentation", icone="panier", ordre=1)
    electronique = Categorie.objects.create(nom="Électronique", icone="puce", ordre=2)
    telephonie = Categorie.objects.create(nom="Téléphonie", parent=electronique)
    return {"alimentation": alimentation, "electronique": electronique,
            "telephonie": telephonie}


def creer_campagne(groupeur, categorie, nom, prix, minimum=10, **extra):
    produit = Produit.objects.create(categorie=categorie, nom=nom, marque=extra.pop("marque", ""))
    defauts = {
        "produit": produit, "groupeur": groupeur, "prix_unitaire": prix,
        "quantite_minimale": minimum,
        "date_limite": timezone.now() + timedelta(days=10),
        "point_remise": "Adawlato, Lomé",
        "statut": Campagne.Statut.EN_COURS, "publiee_le": timezone.now(),
    }
    defauts.update(extra)
    return Campagne.objects.create(**defauts)


class TestCategories:
    def test_les_rayons_sortent_en_arbre(self, client, rayons):
        reponse = client.get("/api/catalogue/categories/")
        assert reponse.status_code == 200
        noms = [r["nom"] for r in reponse.data]
        assert noms == ["Alimentation", "Électronique"], "les sous-rayons ne sont pas à la racine"
        electronique = next(r for r in reponse.data if r["nom"] == "Électronique")
        assert [s["nom"] for s in electronique["sous_categories"]] == ["Téléphonie"]

    def test_un_rayon_inactif_disparait(self, client, rayons):
        rayons["alimentation"].active = False
        rayons["alimentation"].save()
        reponse = client.get("/api/catalogue/categories/")
        assert [r["nom"] for r in reponse.data] == ["Électronique"]

    def test_le_slug_est_fabrique_tout_seul(self, rayons):
        assert rayons["electronique"].slug == "electronique"


class TestCatalogueSansCompte:
    def test_le_catalogue_se_consulte_sans_compte(self, client, groupeur, rayons):
        creer_campagne(groupeur, rayons["alimentation"], "Sac de riz 25 kg", 18000)
        reponse = client.get("/api/catalogue/campagnes/")
        assert reponse.status_code == 200
        assert reponse.data["count"] == 1

    def test_un_brouillon_reste_invisible(self, client, groupeur, rayons):
        creer_campagne(groupeur, rayons["alimentation"], "Caché", 1000,
                       statut=Campagne.Statut.BROUILLON, publiee_le=None)
        assert client.get("/api/catalogue/campagnes/").data["count"] == 0

    def test_la_vignette_porte_le_badge_et_la_note_du_groupeur(self, client, groupeur, rayons):
        creer_campagne(groupeur, rayons["alimentation"], "Riz", 18000)
        vignette = client.get("/api/catalogue/campagnes/").data["results"][0]
        assert vignette["groupeur"]["badge_confiance"] is True
        assert vignette["groupeur"]["nom_commerce"] == "Abalo Import"
        assert vignette["groupeur"]["reputation"]["note"] == "4.50"

    def test_le_numero_du_groupeur_ne_fuite_pas(self, client, groupeur, rayons):
        creer_campagne(groupeur, rayons["alimentation"], "Riz", 18000)
        vignette = client.get("/api/catalogue/campagnes/").data["results"][0]
        assert "telephone" not in vignette["groupeur"]
        assert "email" not in vignette["groupeur"]


class TestFiltres:
    def test_un_rayon_principal_remonte_ses_sous_rayons(self, client, groupeur, rayons):
        creer_campagne(groupeur, rayons["telephonie"], "Smartphone", 95000)
        creer_campagne(groupeur, rayons["alimentation"], "Riz", 18000)

        reponse = client.get("/api/catalogue/campagnes/?categorie=electronique")
        assert reponse.data["count"] == 1, "le sous-rayon doit compter dans son parent"
        assert reponse.data["results"][0]["produit"]["nom"] == "Smartphone"

    def test_recherche_sur_le_nom_du_produit(self, client, groupeur, rayons):
        creer_campagne(groupeur, rayons["alimentation"], "Sac de riz 25 kg", 18000)
        creer_campagne(groupeur, rayons["alimentation"], "Bidon d'huile", 12000)
        reponse = client.get("/api/catalogue/campagnes/?recherche=riz")
        assert reponse.data["count"] == 1

    def test_tri_par_prix(self, client, groupeur, rayons):
        creer_campagne(groupeur, rayons["alimentation"], "Cher", 50000)
        creer_campagne(groupeur, rayons["alimentation"], "Bon marché", 5000)
        resultats = client.get("/api/catalogue/campagnes/?tri=prix").data["results"]
        assert [c["prix_unitaire"] for c in resultats] == [5000, 50000]

    def test_le_comparateur_d_offres_sur_un_produit(self, client, groupeur, rayons):
        """Deux groupeurs sur le même produit : l'acheteur compare."""
        premiere = creer_campagne(groupeur, rayons["alimentation"], "Sac de riz", 18000)
        autre = Utilisateur.objects.create_user(
            "91112233", "mdpSolide2026", nom="Doe", prenom="Afi",
            role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
        )
        Campagne.objects.create(
            produit=premiere.produit, groupeur=autre, prix_unitaire=16000,
            quantite_minimale=20, date_limite=timezone.now() + timedelta(days=5),
            point_remise="Bè", statut=Campagne.Statut.EN_COURS,
            publiee_le=timezone.now(),
        )
        reponse = client.get(f"/api/catalogue/produits/{premiere.produit.slug}/campagnes/")
        assert [c["prix_unitaire"] for c in reponse.data] == [16000, 18000]


class TestJauge:
    def test_la_jauge_ignore_les_parts_impayees(self, client, groupeur, rayons):
        campagne = creer_campagne(groupeur, rayons["alimentation"], "Riz", 18000, minimum=10)
        acheteur = Utilisateur.objects.create_user(
            "92223344", "mdpSolide2026", nom="Mensah", prenom="Ama",
            telephone_verifie=True,
        )
        Participation.objects.create(
            campagne=campagne, acheteur=acheteur, quantite=4,
            prix_unitaire_applique=18000, montant_total=72000,
        )
        vignette = client.get("/api/catalogue/campagnes/").data["results"][0]
        assert vignette["quantite_reservee"] == 0
        assert vignette["pourcentage"] == 0

    def test_la_jauge_compte_les_parts_payees(self, client, groupeur, rayons):
        campagne = creer_campagne(groupeur, rayons["alimentation"], "Riz", 18000, minimum=10)
        for numero, quantite in (("92223344", 4), ("93334455", 3)):
            acheteur = Utilisateur.objects.create_user(
                numero, "mdpSolide2026", nom="N", prenom="P", telephone_verifie=True
            )
            Participation.objects.create(
                campagne=campagne, acheteur=acheteur, quantite=quantite,
                prix_unitaire_applique=18000, montant_total=quantite * 18000,
                statut=Participation.Statut.PAYEE, code_retrait=f"CODE{numero[:4]}",
            )
        vignette = client.get("/api/catalogue/campagnes/").data["results"][0]
        assert vignette["quantite_reservee"] == 7
        assert vignette["nombre_participants"] == 2
        assert vignette["pourcentage"] == 70
        assert vignette["minimum_atteint"] is False

    def test_le_pourcentage_plafonne_a_cent(self, client, groupeur, rayons):
        campagne = creer_campagne(groupeur, rayons["alimentation"], "Riz", 18000, minimum=2)
        acheteur = Utilisateur.objects.create_user(
            "92223344", "mdpSolide2026", nom="N", prenom="P", telephone_verifie=True
        )
        Participation.objects.create(
            campagne=campagne, acheteur=acheteur, quantite=20,
            prix_unitaire_applique=18000, montant_total=360000,
            statut=Participation.Statut.PAYEE, code_retrait="CODE0001",
        )
        vignette = client.get("/api/catalogue/campagnes/").data["results"][0]
        assert vignette["pourcentage"] == 100
        assert vignette["minimum_atteint"] is True

    def test_le_prix_courant_suit_les_paliers(self, client, groupeur, rayons):
        campagne = creer_campagne(groupeur, rayons["alimentation"], "Riz", 18000, minimum=5)
        PalierPrix.objects.create(campagne=campagne, quantite_min=10, prix_unitaire=16500)
        acheteur = Utilisateur.objects.create_user(
            "92223344", "mdpSolide2026", nom="N", prenom="P", telephone_verifie=True
        )
        Participation.objects.create(
            campagne=campagne, acheteur=acheteur, quantite=12,
            prix_unitaire_applique=18000, montant_total=216000,
            statut=Participation.Statut.PAYEE, code_retrait="CODE0002",
        )
        fiche = client.get(f"/api/catalogue/campagnes/{campagne.id}/").data
        assert fiche["prix_courant"] == 16500
        assert fiche["montant_collecte"] == 216000
        assert [p["quantite_min"] for p in fiche["paliers"]] == [10]


class TestNombreDeRequetes:
    def test_la_liste_coute_le_meme_nombre_de_requetes_quelle_que_soit_sa_taille(
        self, client, groupeur, rayons, django_assert_num_queries
    ):
        """Le garde-fou contre le N+1 du catalogue.

        Les paliers et les images sont préchargés ; le moindre ``filter()``
        ou ``first()`` sur une relation déjà chargée réveillerait une requête
        par vignette, et ce test tomberait.
        """
        def peupler(nombre, depart):
            for index in range(depart, depart + nombre):
                campagne = creer_campagne(
                    groupeur, rayons["alimentation"], f"Produit {index}", 10000
                )
                PalierPrix.objects.create(
                    campagne=campagne, quantite_min=10, prix_unitaire=9000
                )

        peupler(3, 0)
        with django_assert_num_queries(5):
            assert client.get("/api/catalogue/campagnes/?page_size=100").data["count"] == 3

        peupler(25, 3)
        with django_assert_num_queries(5):
            assert client.get("/api/catalogue/campagnes/?page_size=100").data["count"] == 28
