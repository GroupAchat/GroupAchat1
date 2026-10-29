# -*- coding: utf-8 -*-
"""Parcours d'inscription, de vérification et de dépôt de dossier."""

from __future__ import annotations

import os
from io import BytesIO
from unittest import mock

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from groupachat.comptes.models import CodeVerification, DossierKYC, Utilisateur

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_jetable(settings, tmp_path):
    """Les pièces déposées vont dans un dossier jeté, jamais dans `medias/`."""
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture(autouse=True)
def cache_propre():
    """La limite de dépôts vit dans le cache : un test n'hérite pas du précédent."""
    cache.clear()
    yield
    cache.clear()


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


def octets_image(format_image="JPEG", taille_px=8) -> bytes:
    tampon = BytesIO()
    Image.new("RGB", (taille_px, taille_px), "white").save(tampon, format=format_image)
    return tampon.getvalue()


def piece(nom="piece.jpg", format_image="JPEG", type_mime="image/jpeg"):
    return SimpleUploadedFile(nom, octets_image(format_image), content_type=type_mime)


def deposer(client, recto=..., verso=..., **surcharge):
    """Dépôt multipart ; ``None`` retire le champ, ``...`` met une photo valide."""
    charge = {**DOSSIER, **surcharge}
    if recto is not None:
        charge["piece_recto"] = piece() if recto is ... else recto
    if verso is not None:
        charge["piece_verso"] = piece() if verso is ... else verso
    return client.post("/api/comptes/dossier/", charge, format="multipart")


def fichiers_stockes(dossier_media) -> list[str]:
    dossier = dossier_media / "kyc"
    return sorted(f.name for f in dossier.iterdir()) if dossier.exists() else []


class TestDossierKYC:
    def test_un_numero_non_verifie_ne_peut_pas_deposer(self, client):
        inscrire(client)
        client.post("/api/comptes/connexion/",
                    {"telephone": "91002233", "mot_de_passe": "mdpSolide2026"},
                    format="json")
        assert deposer(client).status_code == 403

    def test_le_depot_bascule_le_role_sans_ouvrir_l_acces(self, client_verifie):
        reponse = deposer(client_verifie)
        assert reponse.status_code == 201
        assert reponse.data["statut"] == "en_attente"
        assert reponse.data["numero_mobile_money"] == "91002233"

        ama = Utilisateur.objects.get(telephone="91002233")
        assert ama.role == Utilisateur.Role.GROUPEUR
        assert ama.est_groupeur_valide is False

    def test_second_depot_refuse_pendant_l_examen(self, client_verifie):
        deposer(client_verifie)
        reponse = deposer(client_verifie)
        assert reponse.status_code == 409
        assert reponse.data["detail"] == "Un dossier est déjà en cours d'examen."

    def test_redepot_apres_rejet_efface_le_motif(self, client_verifie):
        deposer(client_verifie)
        dossier = DossierKYC.objects.get()
        dossier.statut = DossierKYC.Statut.REJETE
        dossier.motif_rejet = "Pièce illisible"
        dossier.save()

        reponse = deposer(client_verifie)
        assert reponse.status_code == 201
        assert reponse.data["statut"] == "en_attente"
        assert reponse.data["motif_rejet"] == ""
        assert DossierKYC.objects.count() == 1, "le dossier est réécrit, pas doublonné"

    def test_l_acces_s_ouvre_a_la_validation(self, client_verifie):
        deposer(client_verifie)
        dossier = DossierKYC.objects.get()
        dossier.statut = DossierKYC.Statut.VALIDE
        dossier.save()

        ama = Utilisateur.objects.get(telephone="91002233")
        assert ama.est_groupeur_valide is True


# ── Dépôt avec pièces obligatoires (F-011) ──────────────────────────────────


class TestDepotAvecPieces:
    @pytest.mark.parametrize("format_image,type_mime", [
        ("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp"),
    ])
    def test_un_depot_complet_cree_un_dossier_en_attente_avec_ses_pieces(
        self, client_verifie, media_jetable, format_image, type_mime
    ):
        extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[format_image]
        reponse = deposer(
            client_verifie,
            recto=piece(f"recto.{extension}", format_image, type_mime),
            verso=piece(f"verso.{extension}", format_image, type_mime),
        )

        assert reponse.status_code == 201, reponse.data
        assert reponse.data["statut"] == "en_attente"
        assert "piece_recto" not in reponse.data and "piece_verso" not in reponse.data
        dossier = DossierKYC.objects.get()
        assert reponse.data["lien_recto"].endswith(f"/pieces/{dossier.pk}/recto/")
        assert reponse.data["lien_verso"].endswith(f"/pieces/{dossier.pk}/verso/")
        assert len(fichiers_stockes(media_jetable)) == 2
        assert Utilisateur.objects.get(telephone="91002233").role == "groupeur"

    def test_le_candidat_relit_ses_pieces_par_le_lien_protege(
        self, client_verifie
    ):
        envoye = octets_image("PNG", taille_px=12)
        deposer(client_verifie, recto=SimpleUploadedFile(
            "r.png", envoye, content_type="image/png"))
        dossier = DossierKYC.objects.get()

        reponse = client_verifie.get(f"/pieces/{dossier.pk}/recto/")
        assert reponse.status_code == 200
        assert reponse["Content-Type"].startswith("image/")
        assert reponse["Cache-Control"] == "private, no-store"
        assert b"".join(reponse.streaming_content) == envoye

    def test_le_fichier_stocke_perd_le_nom_du_telephone_et_suit_le_vrai_format(
        self, client_verifie, media_jetable
    ):
        # Un PNG nommé .jpg : l'extension stockée suit le contenu, pas le nom.
        trompeur = SimpleUploadedFile(
            "CNI_Komlan_Mensah.jpg", octets_image("PNG"), content_type="image/jpeg")
        deposer(client_verifie, recto=trompeur)

        dossier = DossierKYC.objects.get()
        assert "Komlan" not in dossier.piece_recto.name
        assert "CNI_" not in dossier.piece_recto.name
        assert dossier.piece_recto.name.startswith("kyc/")
        assert dossier.piece_recto.name.endswith(".png")
        assert all("Komlan" not in nom for nom in fichiers_stockes(media_jetable))

    def test_le_nom_stocke_n_apparait_dans_aucune_reponse_de_l_api(
        self, client_verifie
    ):
        creation = deposer(client_verifie)
        relecture = client_verifie.get("/api/comptes/dossier/")
        nom = DossierKYC.objects.get().piece_recto.name.split("/")[-1]
        assert nom not in creation.content.decode()
        assert nom not in relecture.content.decode()

    def test_le_dossier_kyc_n_est_pas_servi_par_medias(self, client_verifie, client):
        deposer(client_verifie)
        nom = DossierKYC.objects.get().piece_recto.name
        anonyme = APIClient()
        assert anonyme.get(f"/medias/{nom}").status_code == 404

    def test_un_tiers_et_un_anonyme_ne_lisent_pas_les_pieces(
        self, client_verifie, yao
    ):
        deposer(client_verifie)
        dossier = DossierKYC.objects.get()
        chemin = f"/pieces/{dossier.pk}/recto/"

        tiers = APIClient()
        tiers.force_login(yao)
        assert tiers.get(chemin).status_code == 404
        assert APIClient().get(chemin).status_code == 404

    def test_le_depot_n_appelle_pas_cloudinary(self, client_verifie):
        with mock.patch("groupachat.noyau.hebergement.signer_envoi") as signer, \
             mock.patch("cloudinary.uploader.upload") as televerser, \
             mock.patch("groupachat.noyau.hebergement._configurer") as configurer:
            assert deposer(client_verifie).status_code == 201

        signer.assert_not_called()
        televerser.assert_not_called()
        configurer.assert_not_called()


class TestDepotRefuse:
    """Chaque refus laisse la base, le disque et le rôle intacts."""

    def _rien_n_est_ecrit(self, media_jetable):
        assert DossierKYC.objects.count() == 0
        assert fichiers_stockes(media_jetable) == []
        assert Utilisateur.objects.get(telephone="91002233").role == "acheteur"

    def test_un_depot_sans_recto_est_refuse(self, client_verifie, media_jetable):
        reponse = deposer(client_verifie, recto=None)
        assert reponse.status_code == 400
        assert reponse.data["piece_recto"] == ["Joignez la photo du recto de votre pièce."]
        self._rien_n_est_ecrit(media_jetable)

    def test_un_depot_sans_verso_est_refuse(self, client_verifie, media_jetable):
        reponse = deposer(client_verifie, verso=None)
        assert reponse.status_code == 400
        assert reponse.data["piece_verso"] == ["Joignez la photo du verso de votre pièce."]
        self._rien_n_est_ecrit(media_jetable)

    def test_un_depot_json_sans_fichier_est_refuse(self, client_verifie, media_jetable):
        reponse = client_verifie.post("/api/comptes/dossier/", DOSSIER, format="json")
        assert reponse.status_code == 400
        assert "piece_recto" in reponse.data and "piece_verso" in reponse.data
        self._rien_n_est_ecrit(media_jetable)

    def test_des_pieces_vides_en_json_sont_refusees(self, client_verifie, media_jetable):
        reponse = client_verifie.post(
            "/api/comptes/dossier/",
            {**DOSSIER, "piece_recto": "", "piece_verso": None}, format="json")
        assert reponse.status_code == 400
        assert "piece_recto" in reponse.data and "piece_verso" in reponse.data
        self._rien_n_est_ecrit(media_jetable)

    @pytest.mark.parametrize("nom,contenu,type_mime", [
        ("recto.pdf", b"%PDF-1.4 fichier pdf", "application/pdf"),
        ("recto.jpg", b"ceci est du texte, pas une photo", "image/jpeg"),
        ("recto.gif", octets_image("GIF"), "image/gif"),
        ("recto.bmp", octets_image("BMP"), "image/bmp"),
        ("recto.tiff", octets_image("TIFF"), "image/tiff"),
        ("recto.jpg", b"", "image/jpeg"),
    ], ids=["pdf", "texte-renomme-jpg", "gif", "bmp", "tiff", "vide"])
    def test_un_fichier_qui_n_est_pas_jpeg_png_ou_webp_est_refuse(
        self, client_verifie, media_jetable, nom, contenu, type_mime
    ):
        fichier = SimpleUploadedFile(nom, contenu, content_type=type_mime)
        reponse = deposer(client_verifie, recto=fichier)

        assert reponse.status_code == 400
        assert reponse.data["piece_recto"] == [
            "Ce fichier n'est pas une photo lisible (JPEG, PNG ou WebP)."]
        self._rien_n_est_ecrit(media_jetable)

    def test_une_piece_de_plus_de_huit_mo_est_refusee_avec_le_message_attendu(
        self, client_verifie, media_jetable
    ):
        # Du bruit ne se compresse pas : un PNG de cette taille dépasse 8 Mo.
        tampon = BytesIO()
        Image.frombytes("RGB", (1700, 1700), os.urandom(1700 * 1700 * 3)).save(
            tampon, format="PNG")
        assert tampon.tell() > 8 * 1024 * 1024
        lourde = SimpleUploadedFile(
            "lourde.png", tampon.getvalue(), content_type="image/png")

        reponse = deposer(client_verifie, recto=lourde)

        assert reponse.status_code == 400
        assert reponse.data["piece_recto"] == ["Image trop lourde : 8 Mo au maximum."]
        self._rien_n_est_ecrit(media_jetable)

    def test_une_piece_pile_a_la_limite_est_acceptee_un_octet_de_plus_refusee(
        self, client_verifie, media_jetable, settings
    ):
        octets = octets_image("PNG", taille_px=40)

        def envoi():
            fichier = SimpleUploadedFile("r.png", octets, content_type="image/png")
            return deposer(client_verifie, recto=fichier, verso=SimpleUploadedFile(
                "v.png", octets, content_type="image/png"))

        settings.TAILLE_MAX_PIECE_OCTETS = len(octets) - 1
        trop = envoi()
        assert trop.status_code == 400
        assert trop.data["piece_recto"][0].startswith("Image trop lourde")
        assert trop.data["piece_verso"][0].startswith("Image trop lourde")
        self._rien_n_est_ecrit(media_jetable)

        settings.TAILLE_MAX_PIECE_OCTETS = len(octets)
        assert envoi().status_code == 201

    def test_la_limite_par_defaut_est_de_huit_mo(self, settings):
        assert settings.TAILLE_MAX_PIECE_OCTETS == 8 * 1024 * 1024

    @pytest.mark.parametrize("champ,valeur", [
        ("numero_piece", ""),
        ("numero_mobile_money", "9000112"),
        ("type_piece", "permis"),
    ])
    def test_une_erreur_de_champ_ne_conserve_pas_les_pieces(
        self, client_verifie, media_jetable, champ, valeur
    ):
        reponse = deposer(client_verifie, **{champ: valeur})
        assert reponse.status_code == 400
        assert champ in reponse.data
        self._rien_n_est_ecrit(media_jetable)

    def test_un_anonyme_ne_depose_pas(self, client, media_jetable):
        assert deposer(client).status_code in (401, 403)
        assert DossierKYC.objects.count() == 0
        assert fichiers_stockes(media_jetable) == []

    def test_le_depot_sans_jeton_csrf_est_refuse(self, ama, media_jetable):
        strict = APIClient(enforce_csrf_checks=True)
        strict.force_login(ama)
        reponse = deposer(strict)
        assert reponse.status_code == 403
        assert DossierKYC.objects.count() == 0
        assert fichiers_stockes(media_jetable) == []


class TestDepotApresDecision:
    def test_un_groupeur_valide_ne_redepose_pas(self, connecte, groupeur, media_jetable):
        dossier = DossierKYC.objects.get(utilisateur=groupeur)
        reponse = deposer(connecte(groupeur))

        assert reponse.status_code == 409
        assert reponse.data["detail"] == "Votre dossier est déjà validé."
        dossier.refresh_from_db()
        assert dossier.statut == DossierKYC.Statut.VALIDE
        assert fichiers_stockes(media_jetable) == []

    def test_un_dossier_valide_sans_piece_reste_valide(self, groupeur):
        # Les dossiers d'avant F-011 n'ont pas de pièce : ils ne sont ni
        # invalidés ni purgés.
        dossier = DossierKYC.objects.get(utilisateur=groupeur)
        assert not dossier.piece_recto and not dossier.piece_verso
        dossier.full_clean()
        assert groupeur.est_groupeur_valide is True

    def test_redepot_apres_rejet_remplace_les_pieces_et_supprime_les_anciennes(
        self, client_verifie, media_jetable, django_capture_on_commit_callbacks
    ):
        deposer(client_verifie)
        dossier = DossierKYC.objects.get()
        anciens = [dossier.piece_recto.name, dossier.piece_verso.name]
        dossier.statut = DossierKYC.Statut.REJETE
        dossier.motif_rejet = "Pièce illisible"
        dossier.save()

        nouveau = octets_image("PNG", taille_px=20)
        with django_capture_on_commit_callbacks(execute=True):
            reponse = deposer(client_verifie, recto=SimpleUploadedFile(
                "n.png", nouveau, content_type="image/png"))

        assert reponse.status_code == 201
        dossier.refresh_from_db()
        assert DossierKYC.objects.count() == 1
        for ancien in anciens:
            assert not (media_jetable / ancien).exists(), "ancienne pièce restée sur le disque"
        assert len(fichiers_stockes(media_jetable)) == 2
        assert (media_jetable / dossier.piece_recto.name).read_bytes() == nouveau

    def test_redepot_apres_rejet_sans_nouvelles_pieces_est_refuse(
        self, client_verifie, media_jetable
    ):
        deposer(client_verifie)
        dossier = DossierKYC.objects.get()
        anciens = fichiers_stockes(media_jetable)
        dossier.statut = DossierKYC.Statut.REJETE
        dossier.save()

        reponse = deposer(client_verifie, recto=None, verso=None)
        assert reponse.status_code == 400
        dossier.refresh_from_db()
        assert dossier.statut == DossierKYC.Statut.REJETE
        assert fichiers_stockes(media_jetable) == anciens

    def test_un_redepot_invalide_garde_les_anciennes_pieces(
        self, client_verifie, media_jetable, django_capture_on_commit_callbacks
    ):
        deposer(client_verifie)
        dossier = DossierKYC.objects.get()
        anciens = fichiers_stockes(media_jetable)
        dossier.statut = DossierKYC.Statut.REJETE
        dossier.save()

        with django_capture_on_commit_callbacks(execute=True):
            reponse = deposer(client_verifie, numero_piece="")
        assert reponse.status_code == 400
        assert fichiers_stockes(media_jetable) == anciens


def _rejeter(dossier):
    dossier.statut = DossierKYC.Statut.REJETE
    dossier.save()


class TestLimiteDesDepots:
    """5 dépôts qui écrivent par jour, 30 tentatives de toute sorte."""

    def test_cinq_depots_invalides_ne_bloquent_pas_un_sixieme_depot_valide(
        self, client_verifie, media_jetable
    ):
        for _ in range(5):
            assert deposer(client_verifie, numero_piece="").status_code == 400

        reponse = deposer(client_verifie)
        assert reponse.status_code == 201, reponse.data
        assert len(fichiers_stockes(media_jetable)) == 2

    def test_les_refus_409_ne_comptent_pas_dans_les_cinq_depots(self, client_verifie):
        deposer(client_verifie)
        for _ in range(6):
            assert deposer(client_verifie).status_code == 409
        _rejeter(DossierKYC.objects.get())
        assert deposer(client_verifie).status_code == 201

    def test_le_sixieme_depot_reussi_de_la_journee_est_freine_en_francais(
        self, client_verifie, media_jetable
    ):
        for _ in range(5):
            assert deposer(client_verifie).status_code == 201
            _rejeter(DossierKYC.objects.get())
        anciens = fichiers_stockes(media_jetable)

        sixieme = deposer(client_verifie)
        assert sixieme.status_code == 429
        assert sixieme.data["detail"] == (
            "Trop de dépôts aujourd'hui. Réessayez demain ou contactez le support.")
        assert fichiers_stockes(media_jetable) == anciens, "le 6e dépôt n'écrit rien"

    def test_la_trente_et_unieme_tentative_est_freinee_en_francais(self, client_verifie):
        for _ in range(30):
            assert deposer(client_verifie, numero_piece="").status_code == 400

        reponse = deposer(client_verifie, numero_piece="")
        assert reponse.status_code == 429
        assert reponse.data["detail"] == (
            "Trop de tentatives aujourd'hui. Réessayez demain ou contactez le support.")

    def test_relire_son_dossier_n_est_pas_limite(self, client_verifie):
        deposer(client_verifie)
        for _ in range(40):
            assert client_verifie.get("/api/comptes/dossier/").status_code == 200

    def test_la_limite_est_propre_a_chaque_compte(self, client_verifie, connecte, yao):
        for _ in range(31):
            deposer(client_verifie, numero_piece="")
        autre = APIClient()
        autre.force_authenticate(user=yao)
        assert deposer(autre).status_code == 201


class TestFormatEtDimensionsDesPieces:
    """Seul le contenu décide : le nom envoyé ne prouve rien."""

    @pytest.mark.parametrize("nom", ["photo", "IMG.heic", "x.html", "PHOTO.JPG", ".jpg."])
    def test_une_vraie_image_est_acceptee_quel_que_soit_son_nom(
        self, client_verifie, media_jetable, nom
    ):
        fichier = SimpleUploadedFile(nom, octets_image("PNG"), content_type="image/png")
        reponse = deposer(client_verifie, recto=fichier)

        assert reponse.status_code == 201, reponse.data
        dossier = DossierKYC.objects.get()
        assert dossier.piece_recto.name.endswith(".png"), "extension tirée du format"
        assert nom not in dossier.piece_recto.name

    def test_un_texte_nomme_png_est_refuse_sans_message_anglais(
        self, client_verifie, media_jetable
    ):
        fichier = SimpleUploadedFile("x.png", b"du texte", content_type="image/png")
        reponse = deposer(client_verifie, recto=fichier)

        assert reponse.status_code == 400
        assert reponse.data["piece_recto"] == [
            "Ce fichier n'est pas une photo lisible (JPEG, PNG ou WebP)."]
        assert reponse.data["piece_recto"][0].code == "invalid_image"

    @pytest.mark.parametrize("largeur,hauteur,accepte", [
        (5000, 5000, True),      # 25 Mpx pile
        (5000, 5001, False),     # un pixel de plus d'une ligne
        (10000, 10000, False),   # 100 Mpx : avertissement Pillow, pas erreur
        (20000, 15000, False),   # 300 Mpx : erreur Pillow
    ])
    def test_le_plafond_de_25_megapixels(
        self, client_verifie, media_jetable, largeur, hauteur, accepte
    ):
        tampon = BytesIO()
        Image.new("1", (largeur, hauteur)).save(tampon, format="PNG")
        fichier = SimpleUploadedFile("p.png", tampon.getvalue(), content_type="image/png")
        reponse = deposer(client_verifie, recto=fichier)

        if accepte:
            assert reponse.status_code == 201, reponse.data
        else:
            assert reponse.status_code == 400
            assert reponse.data["piece_recto"] == [
                "Ce fichier n'est pas une photo lisible (JPEG, PNG ou WebP)."]
            assert DossierKYC.objects.count() == 0
            assert fichiers_stockes(media_jetable) == []


class TestEchecDuBasculementDeRole:
    def test_un_echec_apres_ecriture_efface_les_nouvelles_pieces_et_garde_les_anciennes(
        self, client_verifie, media_jetable
    ):
        deposer(client_verifie)
        dossier = DossierKYC.objects.get()
        anciens = fichiers_stockes(media_jetable)
        dossier.statut = DossierKYC.Statut.REJETE
        dossier.motif_rejet = "Pièce illisible"
        dossier.save()
        # Le basculement n'a lieu que si le compte n'est pas déjà groupeur.
        Utilisateur.objects.update(role=Utilisateur.Role.ACHETEUR)

        with mock.patch.object(Utilisateur, "save", side_effect=RuntimeError("panne")):
            with pytest.raises(RuntimeError):
                deposer(client_verifie, numero_piece="NOUVEAU-1")

        assert fichiers_stockes(media_jetable) == anciens
        dossier.refresh_from_db()
        assert dossier.statut == DossierKYC.Statut.REJETE
        assert dossier.motif_rejet == "Pièce illisible"
        assert dossier.numero_piece == "CNI-9087", "rien n'est écrit en base"


class TestPiecesDeLaDemonstration:
    def test_le_dossier_en_attente_de_la_demo_a_ses_deux_pieces(self, media_jetable):
        from django.core.management import call_command

        call_command("charger_demo", synchroniser=True)

        dossier = DossierKYC.objects.get(utilisateur__telephone="90009988")
        assert dossier.statut == DossierKYC.Statut.EN_ATTENTE
        assert dossier.piece_recto and dossier.piece_verso
        for fichier in (dossier.piece_recto, dossier.piece_verso):
            assert fichier.name.startswith("kyc/")
            assert (media_jetable / fichier.name).exists()
            with Image.open(media_jetable / fichier.name) as image:
                assert image.format == "PNG"
