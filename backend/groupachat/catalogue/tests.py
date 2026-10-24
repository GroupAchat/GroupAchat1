# -*- coding: utf-8 -*-
"""Consultation du catalogue, filtres et jauge d'avancement."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.catalogue.models import (
    Campagne,
    Categorie,
    MediaProduit,
    PalierPrix,
    Produit,
)
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


class TestMediasProduit:
    """Trois photos, deux vidéos — pas une de plus."""

    def fichier_image(self, nom="photo.png"):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        tampon = BytesIO()
        Image.new("RGB", (12, 12), "white").save(tampon, format="PNG")
        return SimpleUploadedFile(nom, tampon.getvalue(), content_type="image/png")

    def fichier_video(self, nom="clip.mp4"):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Le contenu importe peu : c'est le plafond qu'on vérifie, pas le codec.
        return SimpleUploadedFile(nom, b"\x00\x00\x00\x18ftypmp42", content_type="video/mp4")

    @pytest.fixture
    def produit_du_groupeur(self, groupeur, rayons):
        return Produit.objects.create(
            categorie=rayons["alimentation"], nom="Sac de riz", propose_par=groupeur
        )

    def deposer(self, client, produit, genre="image"):
        charge = {"produit": produit.id, "genre": genre}
        if genre == "video":
            charge["fichier"] = self.fichier_video()
            charge["apercu"] = self.fichier_image("apercu.png")
        else:
            charge["fichier"] = self.fichier_image()
        return client.post("/api/groupeur/medias/", charge, format="multipart")

    def test_trois_photos_passent_la_quatrieme_non(self, client, groupeur, produit_du_groupeur):
        client.force_authenticate(user=groupeur)
        for rang in range(MediaProduit.MAX_IMAGES):
            reponse = self.deposer(client, produit_du_groupeur)
            assert reponse.status_code == 201, (rang, reponse.data)

        refus = self.deposer(client, produit_du_groupeur)
        assert refus.status_code == 400
        assert "maximum" in str(refus.data)

    def test_deux_videos_passent_la_troisieme_non(self, client, groupeur, produit_du_groupeur):
        client.force_authenticate(user=groupeur)
        for _ in range(MediaProduit.MAX_VIDEOS):
            assert self.deposer(client, produit_du_groupeur, "video").status_code == 201

        refus = self.deposer(client, produit_du_groupeur, "video")
        assert refus.status_code == 400

    def test_les_deux_plafonds_sont_independants(self, client, groupeur, produit_du_groupeur):
        """Saturer les photos ne doit pas bloquer les vidéos."""
        client.force_authenticate(user=groupeur)
        for _ in range(MediaProduit.MAX_IMAGES):
            self.deposer(client, produit_du_groupeur)
        assert self.deposer(client, produit_du_groupeur, "video").status_code == 201

    def test_une_video_sans_apercu_est_refusee(self, client, groupeur, produit_du_groupeur):
        client.force_authenticate(user=groupeur)
        reponse = client.post(
            "/api/groupeur/medias/",
            {"produit": produit_du_groupeur.id, "genre": "video",
             "fichier": self.fichier_video()},
            format="multipart",
        )
        assert reponse.status_code == 400
        assert "apercu" in reponse.data

    def test_le_plafond_tient_aussi_hors_de_l_api(self, produit_du_groupeur):
        """Un script qui contourne le sérialiseur reste bloqué par le modèle."""
        from django.core.exceptions import ValidationError

        for _ in range(MediaProduit.MAX_IMAGES):
            MediaProduit.objects.create(produit=produit_du_groupeur, fichier="produits/x.png")

        surnumeraire = MediaProduit(produit=produit_du_groupeur, fichier="produits/y.png")
        with pytest.raises(ValidationError):
            surnumeraire.clean()

    def test_on_ne_depose_pas_sur_le_produit_d_un_autre(
        self, client, produit_du_groupeur, yao
    ):
        from groupachat.comptes.models import DossierKYC, Utilisateur

        autre = Utilisateur.objects.create_user(
            "94445566", "mdpSolide2026", nom="Autre", prenom="Groupeur",
            role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
        )
        DossierKYC.objects.create(
            utilisateur=autre, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-9", numero_mobile_money="94445566",
            statut=DossierKYC.Statut.VALIDE,
        )
        client.force_authenticate(user=autre)
        assert self.deposer(client, produit_du_groupeur).status_code == 403

    def test_la_vignette_du_catalogue_reste_une_photo(self, produit_du_groupeur):
        """Une vidéo ne fait pas une vignette."""
        MediaProduit.objects.create(
            produit=produit_du_groupeur, genre=MediaProduit.Genre.VIDEO,
            fichier="produits/clip.mp4", apercu="produits/apercus/a.png", ordre=0,
        )
        photo = MediaProduit.objects.create(
            produit=produit_du_groupeur, fichier="produits/photo.png", ordre=1,
        )
        produit_du_groupeur.refresh_from_db()
        assert produit_du_groupeur.image_principale.name == photo.fichier.name
