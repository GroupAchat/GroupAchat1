# -*- coding: utf-8 -*-
"""La photo jointe à une demande de produit (écran 11).

Elle sert au groupeur : « un pagne comme celui-là » se montre en une image et
ne s'écrit pas en trois lignes. Mais une pièce jointe est aussi la porte
d'entrée la plus commode d'une application web, d'où les quatre règles que ces
tests protègent.

Chaque test porte le nom de la règle qu'il protège.
"""

from __future__ import annotations

from rest_framework.test import APIClient, APITestCase

from .aides import connecter
from .. import domaine
from ..echanges.models import Demande

#: Un JPEG minimal : la signature suffit, le reste des octets n'est jamais
#: décodé — la plateforme ne redimensionne pas, elle stocke ce qu'on lui donne.
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"0" * 64


def _fichier(octets: bytes, nom: str = "produit.jpg", type_mime: str = "image/jpeg"):
    """Un fichier téléversé, comme le navigateur l'enverrait."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(nom, octets, content_type=type_mime)


class PhotoDeDemande(APITestCase):
    def setUp(self):
        self.client = APIClient()
        connecter(self.client, "+22890000001", nom="Akosua Doe")

    def _deposer(self, **extra):
        return self.client.post(
            "/api/demandes/",
            {
                "produit": "Pagne wax",
                "quantite": "6 yards",
                "quartier": "Tokoin",
                **extra,
            },
            format="multipart",
        )

    def test_la_photo_est_facultative(self):
        """Le §1.0 plafonne le formulaire à cinq champs : la photo est un
        bonus, pas une condition. Une demande sans photo doit passer."""
        reponse = self.client.post(
            "/api/demandes/",
            {"produit": "Riz parfumé", "quantite": "25 kg", "quartier": "Bè"},
            format="json",
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertIsNone(reponse.data["photo_url"])
        self.assertEqual(Demande.objects.get().photo_type, "")

    def test_une_photo_jointe_est_conservee_et_son_adresse_renvoyee(self):
        reponse = self._deposer(photo=_fichier(JPEG))
        self.assertEqual(reponse.status_code, 201, reponse.data)

        demande = Demande.objects.get()
        self.assertEqual(bytes(demande.photo), JPEG)
        self.assertEqual(demande.photo_type, "image/jpeg")
        self.assertIn(f"/api/demandes/{demande.pk}/photo/", reponse.data["photo_url"])

    def test_les_octets_ne_partent_jamais_dans_la_liste(self):
        """⚠️ La règle qui protège le forfait data du §18.1. Sérialiser les
        octets ferait d'une liste de demandes une réponse de plusieurs
        mégaoctets, pour une image que l'écran n'affichera peut-être pas."""
        self._deposer(photo=_fichier(JPEG))

        liste = self.client.get("/api/demandes/")
        self.assertEqual(liste.status_code, 200)
        self.assertNotIn("photo", liste.data["results"][0])
        self.assertIsNotNone(liste.data["results"][0]["photo_url"])

    def test_la_route_sert_les_octets_avec_leur_type(self):
        self._deposer(photo=_fichier(PNG, "produit.png", "image/png"))
        demande = Demande.objects.get()

        reponse = self.client.get(f"/api/demandes/{demande.pk}/photo/")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse["Content-Type"], "image/png")
        self.assertEqual(reponse.content, PNG)

    def test_le_webp_est_accepte(self):
        """Il commence par ``RIFF``, comme un WAV : c'est l'octet 8 qui
        tranche. Le format compte, c'est le plus léger des trois."""
        reponse = self._deposer(photo=_fichier(WEBP, "p.webp", "image/webp"))
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(Demande.objects.get().photo_type, "image/webp")

    def test_un_fichier_qui_se_dit_image_sans_en_etre_une_est_refuse(self):
        """⚠️ **Le contrôle qui compte.** Le ``Content-Type`` est déclaré par
        le client : il suffit de le mentir. Seuls les premiers octets ne
        mentent pas."""
        reponse = self._deposer(
            photo=_fichier(b"#!/bin/sh\nrm -rf /", "produit.jpg", "image/jpeg")
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("photo", reponse.data)
        self.assertEqual(Demande.objects.count(), 0)

    def test_une_photo_trop_lourde_est_refusee_et_la_demande_nest_pas_creee(self):
        """Elle est **refusée**, pas ignorée. L'acheteur a attendu son
        téléversement : le laisser croire sa demande partie avec la photo
        serait un mensonge que rien à l'écran ne corrigerait."""
        trop = JPEG + b"0" * domaine.PHOTO_DEMANDE_MAX_OCTETS
        reponse = self._deposer(photo=_fichier(trop))

        self.assertEqual(reponse.status_code, 400)
        self.assertIn("ko", str(reponse.data["photo"]))
        self.assertEqual(Demande.objects.count(), 0)

    def test_la_photo_dun_autre_acheteur_repond_404(self):
        """404 et non 403 : « interdit » confirmerait que la demande existe."""
        self._deposer(photo=_fichier(JPEG))
        demande = Demande.objects.get()

        autre = APIClient()
        connecter(autre, "+22890000002", nom="Kofi M.")
        reponse = autre.get(f"/api/demandes/{demande.pk}/photo/")
        self.assertEqual(reponse.status_code, 404)

    def test_la_photo_exige_une_session(self):
        """401 et non 403 : l'écran doit rouvrir la feuille de connexion, pas
        afficher « accès refusé » à quelqu'un dont la session a expiré."""
        self._deposer(photo=_fichier(JPEG))
        demande = Demande.objects.get()

        anonyme = APIClient()
        reponse = anonyme.get(f"/api/demandes/{demande.pk}/photo/")
        self.assertEqual(reponse.status_code, 401)

    def test_une_demande_sans_photo_repond_404_sur_sa_route_photo(self):
        self.client.post(
            "/api/demandes/",
            {"produit": "Savon", "quantite": "10 pains", "quartier": "Tokoin"},
            format="json",
        )
        demande = Demande.objects.get()
        reponse = self.client.get(f"/api/demandes/{demande.pk}/photo/")
        self.assertEqual(reponse.status_code, 404)
