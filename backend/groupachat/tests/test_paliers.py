# -*- coding: utf-8 -*-
"""Les paliers de prix dégressifs — « à partir de 5 parts, 3 500 F ».

C'est la réponse du produit à une question simple : **comment rendre le prix
attirant sans prix barré ?** Le §3 interdit tout prix barré, tout badge de
réduction, tout « au lieu de ». Une grille dégressive n'en est pas un — il n'y
a aucun prix de référence inventé, seulement **plusieurs prix vrais**, et celui
qu'on paie dépend de ce qu'on prend. C'est la définition du prix de gros, qui
est le produit lui-même.

⚠️ **Le palier se déclenche sur la quantité prise par l'acheteur**, jamais sur
le nombre de participants. Le faire dépendre du groupage serait un
**déclencheur collectif** — interdit par la règle de l'objectif (*ni plafond,
ni minimum, ni déclencheur*) — et surtout le prix ne serait **pas connu au
moment de payer** : il baisserait après coup, pour des gens dont l'argent est
déjà parti au portefeuille du groupeur.

| Règle | Ce qu'on perd en la perdant | Test |
|---|---|---|
| La grille s'applique au paiement | Un acheteur facturé au prix fort | ``test_la_commande_paie_le_prix_du_palier`` |
| Un palier ne peut pas renchérir | Payer plus en prenant plus | ``test_un_palier_plus_cher_est_refuse`` |
| Le seuil est d'au moins 2 | Deux sources pour le prix d'une part | ``test_un_palier_a_une_part_est_refuse`` |
| Sans palier, rien ne change | Une régression sur tous les groupages | ``test_sans_palier_le_prix_ne_bouge_pas`` |
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from groupachat.catalogue.models import Campagne, PalierPrix
from groupachat.comptes.models import Groupeur


class SoclePaliers(TestCase):
    def setUp(self) -> None:
        self.groupeuse = Groupeur.objects.create(
            pseudonyme="Mama Gro",
            nom_complet="Afi Mensah",
            telephone="+22891000001",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
        )
        self.campagne = Campagne.objects.create(
            groupeur=self.groupeuse,
            titre="Savon de ménage, lot de 10",
            description="Lot de dix savons.",
            contenu_part="10 savons",
            categorie=Campagne.Categorie.HYGIENE,
            prix_part=Decimal("5000"),
            objectif_participants=20,
            date_fin=timezone.now() + timedelta(days=3),
        )

    def poser_un_palier(self, quantite_min: int, prix: str) -> PalierPrix:
        palier = PalierPrix(
            campagne=self.campagne,
            quantite_min=quantite_min,
            prix_part=Decimal(prix),
        )
        palier.full_clean()
        palier.save()
        return palier


class LaGrille(SoclePaliers):
    def test_sans_palier_le_prix_ne_bouge_pas(self) -> None:
        """⚠️ **Le cas de loin le plus fréquent**, et celui qui doit rester intact.

        Les paliers sont facultatifs. Un groupage qui n'en a pas doit se
        comporter exactement comme avant : un prix, une multiplication. Ce test
        existe pour que l'ajout de la grille ne devienne pas une régression
        silencieuse sur tous les groupages existants.
        """
        for quantite in (1, 2, 5, 40):
            self.assertEqual(
                self.campagne.prix_pour(quantite), Decimal("5000")
            )

    def test_le_prix_baisse_au_seuil(self) -> None:
        self.poser_un_palier(5, "3500")

        self.assertEqual(self.campagne.prix_pour(1), Decimal("5000"))
        self.assertEqual(self.campagne.prix_pour(4), Decimal("5000"))
        # Le seuil est inclusif : « à partir de 5 » veut dire 5 compris.
        self.assertEqual(self.campagne.prix_pour(5), Decimal("3500"))
        self.assertEqual(self.campagne.prix_pour(99), Decimal("3500"))

    def test_plusieurs_paliers_sont_pris_dans_l_ordre(self) -> None:
        """Le dernier seuil atteint gagne, quel que soit l'ordre d'insertion.

        Les paliers sont posés à l'envers exprès : ``Meta.ordering`` doit les
        remettre en ordre croissant, et c'est ce que ``prix_pour`` suppose.
        """
        self.poser_un_palier(20, "2800")
        self.poser_un_palier(5, "3500")

        self.assertEqual(self.campagne.prix_pour(4), Decimal("5000"))
        self.assertEqual(self.campagne.prix_pour(5), Decimal("3500"))
        self.assertEqual(self.campagne.prix_pour(19), Decimal("3500"))
        self.assertEqual(self.campagne.prix_pour(20), Decimal("2800"))

    def test_une_quantite_nulle_leve(self) -> None:
        with self.assertRaises(ValueError):
            self.campagne.prix_pour(0)


class LaGrilleNePeutPasMonter(SoclePaliers):
    """Les deux verrous de ``clean``."""

    def test_un_palier_plus_cher_que_la_part_est_refuse(self) -> None:
        """Sinon l'acheteur paierait **plus cher en prenant plus**.

        Une grille qui monte n'est pas un prix de gros, c'est une pénalité de
        volume — et aucun écran du produit ne saurait la présenter honnêtement.
        """
        with self.assertRaises(ValidationError) as contexte:
            self.poser_un_palier(5, "6000")
        self.assertIn("prix_part", contexte.exception.message_dict)

    def test_un_palier_egal_au_prix_de_la_part_est_refuse(self) -> None:
        """Il n'apporterait rien et ferait croire à une remise."""
        with self.assertRaises(ValidationError):
            self.poser_un_palier(5, "5000")

    def test_un_palier_plus_cher_que_le_precedent_est_refuse(self) -> None:
        self.poser_un_palier(5, "3500")
        with self.assertRaises(ValidationError) as contexte:
            self.poser_un_palier(20, "4000")
        self.assertIn("prix_part", contexte.exception.message_dict)

    def test_un_palier_a_une_part_est_refuse(self) -> None:
        """⚠️ Il remplacerait ``prix_part`` sans le dire.

        On se retrouverait avec **deux sources pour le prix d'une part**, et
        les écrans qui lisent `prix_part` — le fil, la fiche, le sélecteur de
        quantité — afficheraient l'autre.
        """
        with self.assertRaises(ValidationError):
            self.poser_un_palier(1, "3500")

    def test_deux_paliers_au_meme_seuil_sont_refuses(self) -> None:
        """Le prix dépendrait de l'ordre d'insertion en base."""
        self.poser_un_palier(5, "3500")
        with self.assertRaises(Exception):
            PalierPrix.objects.create(
                campagne=self.campagne,
                quantite_min=5,
                prix_part=Decimal("3000"),
            )


class LaCommandePaieLePrixDuPalier(SoclePaliers):
    """⚠️ **Le test qui compte vraiment.**

    Afficher une grille et facturer autre chose serait pire que de ne pas
    l'afficher : l'acheteur verrait 3 500 F et paierait 5 000 F.
    """

    def test_la_commande_paie_le_prix_du_palier(self) -> None:
        from groupachat.commandes.models import enregistrer_paiement
        from groupachat.comptes.models import Acheteur

        self.poser_un_palier(5, "3500")
        acheteuse = Acheteur.objects.create(
            telephone="+22890123456", nom="Akosua"
        )

        commande, _ = enregistrer_paiement(
            campagne=self.campagne,
            acheteur=acheteuse,
            quantite=5,
            variante="",
            quartier="tokoin",
            repere="rue des Cocotiers",
            telephone="+22890123456",
            cle_idempotence="palier-1",
        )

        # 5 × 3 500 = 17 500, et non 5 × 5 000 = 25 000.
        self.assertEqual(commande.montant_parts, Decimal("17500"))
        self.assertEqual(commande.total, Decimal("17500"))

    def test_sous_le_seuil_le_prix_reste_celui_de_la_part(self) -> None:
        from groupachat.commandes.models import enregistrer_paiement
        from groupachat.comptes.models import Acheteur

        self.poser_un_palier(5, "3500")
        acheteuse = Acheteur.objects.create(
            telephone="+22890123457", nom="Kofi"
        )

        commande, _ = enregistrer_paiement(
            campagne=self.campagne,
            acheteur=acheteuse,
            quantite=4,
            variante="",
            quartier="tokoin",
            repere="rue des Cocotiers",
            telephone="+22890123457",
            cle_idempotence="palier-2",
        )

        self.assertEqual(commande.montant_parts, Decimal("20000"))
