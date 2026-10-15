# -*- coding: utf-8 -*-
"""Les médias d'une fiche produit — quatre images, deux vidéos.

Ces deux nombres ne protègent pas la même chose, et c'est pour ça qu'ils sont
différents :

- **quatre images**, parce qu'une seule photo ne vend pas. C'est une limite de
  confort, large exprès ;
- **deux vidéos**, parce que le public visé a un forfait de données limité
  (§18.1). C'est une limite de coût, et c'est l'acheteur qui paie le
  dépassement — pas nous.

⚠️ **Les règles sont vérifiées sur le modèle, pas dans le formulaire**, et le
dernier test de ce fichier est là pour que ça le reste : un champ grisé ne
protège de rien, il suffit d'une requête directe pour le contourner.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from groupachat.catalogue.models import MAX_IMAGES, MAX_VIDEOS, Campagne
from groupachat.comptes.models import Groupeur


def image(numero: int) -> dict:
    return {
        "type": "image",
        "url": f"https://exemple.tg/photo-{numero}.jpg",
        "alt": f"Le produit, vue {numero}",
    }


def video(numero: int, affiche: str = "") -> dict:
    media = {"type": "video", "url": f"https://exemple.tg/film-{numero}.mp4"}
    if affiche:
        media["affiche"] = affiche
    return media


class SocleCampagne(TestCase):
    def setUp(self) -> None:
        self.groupeur = Groupeur.objects.create(
            pseudonyme="Mama Gro",
            nom_complet="Akossiwa Mensah",
            telephone="+22891000001",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            titulaire_mobile_money="Akossiwa Mensah",
            numero_mobile_money="+22891000001",
        )

    def creer(self, medias: list[dict]) -> Campagne:
        return Campagne.objects.create(
            groupeur=self.groupeur,
            titre="Écouteurs filaires avec micro",
            description="Un lot de cent.",
            contenu_part="Une paire",
            categorie=Campagne.Categorie.ELECTRONIQUE,
            prix_part=Decimal("4000"),
            objectif_participants=40,
            date_fin=timezone.now() + timedelta(days=2),
            medias=medias,
        )


class LimitesTest(SocleCampagne):
    """Ce qui passe, et ce qui est refusé."""

    def test_quatre_images_et_deux_videos_passent(self):
        """Le maximum exact. C'est la limite haute qui doit être acceptée."""
        campagne = self.creer(
            [image(1), image(2), image(3), image(4), video(1), video(2)]
        )
        self.assertEqual(len(campagne.images), MAX_IMAGES)
        self.assertEqual(len(campagne.videos), MAX_VIDEOS)

    def test_une_cinquieme_image_est_refusee(self):
        with self.assertRaises(ValidationError) as refus:
            self.creer([image(n) for n in range(1, 6)])
        self.assertIn("4 images", str(refus.exception))

    def test_une_troisieme_video_est_refusee(self):
        with self.assertRaises(ValidationError) as refus:
            self.creer([image(1), video(1), video(2), video(3)])
        self.assertIn("2 vidéos", str(refus.exception))

    def test_aucun_media_reste_permis(self):
        """Une campagne sans photo doit pouvoir exister.

        Le modèle doit représenter ce que les scripts d'import créent en deux
        temps, et ce que les campagnes d'avant cette liste portaient. C'est le
        formulaire de l'écran 14 qui exige une photo, pas la base.
        """
        self.assertEqual(self.creer([]).medias, [])

    def test_une_video_seule_est_refusee(self):
        """§1.6 — « une image d'abord, toujours ».

        Sans image, la carte du fil et les lignes de liste n'ont rien à
        montrer tant que la vidéo charge, c'est-à-dire exactement pendant la
        seconde où l'acheteur décide de s'arrêter ou de passer.
        """
        with self.assertRaises(ValidationError) as refus:
            self.creer([video(1)])
        self.assertIn("photo", str(refus.exception))

    def test_une_video_avec_son_affiche_se_suffit(self):
        """L'affiche **est** une image : elle remplit le même office."""
        campagne = self.creer([video(1, affiche="https://exemple.tg/a.jpg")])
        self.assertEqual(campagne.media, "https://exemple.tg/a.jpg")


class FormeTest(SocleCampagne):
    """Ce qui entre dans la liste doit être lisible par l'interface."""

    def test_un_type_inconnu_est_refuse(self):
        with self.assertRaises(ValidationError):
            self.creer([{"type": "audio", "url": "https://exemple.tg/a.mp3"}])

    def test_un_media_sans_adresse_est_refuse(self):
        """Une entrée vide produirait une image cassée sur la fiche."""
        with self.assertRaises(ValidationError):
            self.creer([{"type": "image", "url": "   ", "alt": "rien"}])

    def test_une_liste_de_chaines_est_refusee(self):
        """L'erreur de reprise la plus probable : l'ancien format."""
        with self.assertRaises(ValidationError):
            self.creer(["https://exemple.tg/photo.jpg"])


class CouvertureTest(SocleCampagne):
    """`media` et `media_alt` — ce que les cartes et le fil affichent."""

    def test_la_couverture_est_la_premiere_image(self):
        campagne = self.creer([image(1), image(2)])
        self.assertEqual(campagne.media, "https://exemple.tg/photo-1.jpg")
        self.assertEqual(campagne.media_alt, "Le produit, vue 1")

    def test_la_couverture_saute_les_videos(self):
        """Même posée en premier, une vidéo n'est jamais la couverture.

        L'ordre de la liste décide de l'affichage sur la fiche, mais la
        couverture, elle, doit rester une image : c'est le §1.6.
        """
        campagne = self.creer(
            [video(1, affiche="https://exemple.tg/a.jpg"), image(2)]
        )
        self.assertEqual(campagne.media, "https://exemple.tg/photo-2.jpg")

    def test_sans_media_la_couverture_est_vide(self):
        """Vide, et non une image de remplacement.

        L'interface retombe alors sur le titre du produit, qui est toujours
        plus juste qu'un visuel générique.
        """
        self.assertEqual(self.creer([]).media, "")


class ContournementTest(SocleCampagne):
    """⚠️ Le test qui garde la règle là où elle protège vraiment."""

    def test_la_limite_tient_hors_de_tout_formulaire(self):
        """`objects.create` ne passe par aucun sérialiseur ni formulaire.

        C'est le chemin qu'emprunterait une requête directe, un script
        d'import ou une console. Si ce test tombe, la limite n'est plus qu'une
        suggestion d'interface — et trente vidéos entrent en base.
        """
        with self.assertRaises(ValidationError):
            Campagne.objects.create(
                groupeur=self.groupeur,
                titre="Trente vidéos",
                description="Par la porte de derrière.",
                contenu_part="Une paire",
                categorie=Campagne.Categorie.ELECTRONIQUE,
                prix_part=Decimal("4000"),
                objectif_participants=40,
                date_fin=timezone.now() + timedelta(days=2),
                medias=[image(1)] + [video(n) for n in range(30)],
            )
