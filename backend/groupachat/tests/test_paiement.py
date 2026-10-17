# -*- coding: utf-8 -*-
"""Le paiement, l'idempotence et la clôture.

**C'est le serveur qui fait foi.** Le client calcule pour afficher, le serveur
calcule pour encaisser ; ces tests vérifient qu'une requête forgée ne peut ni
payer moins que le prix, ni commander dans une campagne fermée, ni créer deux
commandes avec la même clé.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.tests.aides import connecter

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import (
    Commande,
    Retrait,
    annuler_campagne,
    cloturer_campagne,
    enregistrer_paiement,
)
from groupachat.comptes.models import Acheteur, Groupeur


def _groupeur() -> Groupeur:
    return Groupeur.objects.create(
        pseudonyme="Mama Gro",
        nom_complet="Akossiwa Mensah",
        telephone="+22891000001",
        statut_kyc=Groupeur.StatutKyc.VALIDE,
        titulaire_mobile_money="Akossiwa Mensah",
        numero_mobile_money="+22891000001",
    )


def _campagne(groupeur: Groupeur, **extra) -> Campagne:
    valeurs = {
        "titre": "Écouteurs filaires avec micro",
        "description": "Écouteurs intra-auriculaires avec micro.",
        "contenu_part": "1 écouteur filaire avec micro",
        "categorie": Campagne.Categorie.ELECTRONIQUE,
        "prix_part": Decimal("4000"),
        # Le fil rouge du §3 : 32 acheteurs pour un objectif de 40.
        "objectif_participants": 40,
        "date_fin": timezone.now() + timedelta(days=2),
    }
    valeurs.update(extra)
    return Campagne.objects.create(groupeur=groupeur, **valeurs)


class IdempotenceTest(TestCase):
    """La clé d'idempotence — §6 du PRD.

    Sans elle, un acheteur qui touche deux fois « Confirmer » sur un réseau
    lent paie deux fois. C'est le cas le plus fréquent, pas un cas limite.
    """

    def setUp(self) -> None:
        self.groupeur = _groupeur()
        self.campagne = _campagne(self.groupeur)
        self.acheteuse = Acheteur.objects.create(
            telephone="+22890123456", nom="Akosua Doe"
        )

    def _payer(self, cle: str):
        return enregistrer_paiement(
            campagne=self.campagne,
            acheteur=self.acheteuse,
            quantite=1,
            quartier="Tokoin",
            repere="rue des Cocotiers",
            telephone="+22890123456",
            cle_idempotence=cle,
        )

    def test_deux_appels_avec_la_meme_cle_ne_creent_qu_une_commande(self):
        premiere, creee_1 = self._payer("idem-abc")
        seconde, creee_2 = self._payer("idem-abc")

        self.assertTrue(creee_1)
        self.assertFalse(creee_2)
        self.assertEqual(premiere.pk, seconde.pk)
        self.assertEqual(Commande.objects.count(), 1)

    def test_le_code_de_livraison_ne_change_pas_au_rejeu(self):
        """Un acheteur qui a noté son code ne doit pas le voir changer."""
        premiere, _ = self._payer("idem-abc")
        seconde, _ = self._payer("idem-abc")
        self.assertEqual(premiere.code_livraison, seconde.code_livraison)

    def test_deux_cles_differentes_creent_deux_commandes(self):
        """L'idempotence protège du double clic, pas de deux achats voulus."""
        self._payer("idem-abc")
        self._payer("idem-def")
        self.assertEqual(Commande.objects.count(), 2)

    def test_l_api_renvoie_201_puis_200(self):
        """Le code HTTP dit ce qui s'est passé : créé, puis rien de neuf."""
        client = APIClient()
        connecter(client, "+22890123456", nom="Akosua Doe")
        corps = {
            "campagne": self.campagne.pk,
            "quantite": 1,
            "quartier": "Tokoin",
            "repere": "rue des Cocotiers",
            "cle_idempotence": "idem-api-1",
        }

        premiere = client.post("/api/commandes/payer/", corps, format="json")
        seconde = client.post("/api/commandes/payer/", corps, format="json")

        self.assertEqual(premiere.status_code, 201)
        self.assertEqual(seconde.status_code, 200)
        self.assertEqual(
            premiere.json()["code_livraison"], seconde.json()["code_livraison"]
        )
        self.assertEqual(Commande.objects.count(), 1)


class MontantsTest(TestCase):
    """Le serveur recalcule. Le client ne fixe pas les prix."""

    def setUp(self) -> None:
        self.campagne = _campagne(_groupeur())
        self.acheteuse = Acheteur.objects.create(telephone="+22890123456")

    def test_le_total_du_fil_rouge(self):
        commande, _ = enregistrer_paiement(
            campagne=self.campagne,
            acheteur=self.acheteuse,
            quantite=1,
            quartier="Tokoin",
            repere="rue des Cocotiers",
            telephone="+22890123456",
            cle_idempotence="idem-1",
        )
        self.assertEqual(commande.montant_parts, Decimal("4000"))
        # Plus de frais factures a l acheteur : le total du fil rouge
        # est 4 000 F, pas 5 000.
        self.assertEqual(commande.frais_livraison, Decimal("0"))
        self.assertEqual(commande.total, Decimal("4000"))

    def test_un_total_fabrique_est_refuse(self):
        """Une requête forgée ne doit pas payer 5 000 F une commande à 50 000."""
        commande = Commande(
            campagne=self.campagne,
            acheteur=self.acheteuse,
            quantite=10,
            montant_parts=Decimal("4000"),  # devrait valoir 40 000
            frais_livraison=Decimal("0"),
            total=Decimal("4000"),
            quartier="Tokoin",
            repere="rue des Cocotiers",
            telephone="+22890123456",
            code_livraison="AAA-111",
            cle_idempotence="idem-forge",
        )
        with self.assertRaises(ValidationError):
            commande.full_clean()

    def test_le_repere_est_obligatoire(self):
        """À Lomé le repère vaut plus que la coordonnée."""
        commande = Commande(
            campagne=self.campagne,
            acheteur=self.acheteuse,
            quantite=1,
            montant_parts=Decimal("4000"),
            frais_livraison=Decimal("0"),
            total=Decimal("4000"),
            quartier="Tokoin",
            repere="   ",
            telephone="+22890123456",
            code_livraison="AAA-222",
            cle_idempotence="idem-sans-repere",
        )
        with self.assertRaises(ValidationError) as contexte:
            commande.full_clean()
        self.assertIn("repere", contexte.exception.message_dict)

    def test_une_zone_non_desservie_est_refusee_par_l_api(self):
        client = APIClient()
        connecter(client, "+22890123456")
        reponse = client.post(
            "/api/commandes/payer/",
            {
                "campagne": self.campagne.pk,
                "quantite": 1,
                "quartier": "Kpalimé",
                "repere": "près du marché",
                "cle_idempotence": "idem-kpalime",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("quartier", reponse.json())

    def test_on_ne_commande_pas_dans_une_campagne_fermee(self):
        campagne = _campagne(
            _groupeur_secondaire(), date_fin=timezone.now() - timedelta(hours=1)
        )
        with self.assertRaises(ValidationError):
            enregistrer_paiement(
                campagne=campagne,
                acheteur=self.acheteuse,
                quantite=1,
                quartier="Tokoin",
                repere="rue des Cocotiers",
                telephone="+22890123456",
                cle_idempotence="idem-fermee",
            )


def _groupeur_secondaire() -> Groupeur:
    return Groupeur.objects.create(
        pseudonyme="Chez Sika",
        nom_complet="Sika Adjo",
        telephone="+22891000002",
        statut_kyc=Groupeur.StatutKyc.VALIDE,
        titulaire_mobile_money="Sika Adjo",
        numero_mobile_money="+22891000002",
    )


class ClotureTest(TestCase):
    """La clôture, le retrait et l'annulation."""

    def setUp(self) -> None:
        self.campagne = _campagne(_groupeur())
        for indice in range(32):
            acheteur = Acheteur.objects.create(telephone=f"+2289000{indice:04d}")
            enregistrer_paiement(
                campagne=self.campagne,
                acheteur=acheteur,
                quantite=1,
                quartier="Tokoin",
                repere="rue des Cocotiers",
                telephone=acheteur.telephone,
                cle_idempotence=f"idem-{indice}",
            )

    def test_le_portefeuille_du_fil_rouge_tombe_juste(self):
        """32 commandes : 128 000 collectés, 1 500 de frais, 126 500 retirables."""
        self.assertEqual(self.campagne.acheteurs_confirmes, 32)
        self.assertEqual(self.campagne.collecte_sur_les_parts, Decimal("128000"))

        retrait = cloturer_campagne(self.campagne)
        self.assertEqual(retrait.collecte, Decimal("128000"))
        self.assertEqual(retrait.frais_plateforme, Decimal("1500"))
        self.assertEqual(retrait.net, Decimal("126500"))

    def test_aucun_frais_de_livraison_n_est_collecte(self):
        """Zéro, et la collecte reste intacte.

        ⚠️ **Ce test s'appelait `test_les_frais_collectes_sont_comptes_a_part`**
        et vérifiait *32 × 1 000 = 32 000 F, reversés au transporteur*. Les
        frais de livraison facturés à l'acheteur ont été supprimés : plus
        rien n'est collecté à ce titre.

        Ce qu'il garde, et qui comptait déjà : **les frais ne touchent pas
        à la collecte du groupeur.** À zéro c'est trivialement vrai, mais le
        test attrape le jour où quelqu'un rebranche un montant et le mélange
        au net.
        """
        retrait = cloturer_campagne(self.campagne)
        self.assertEqual(retrait.frais_livraison_collectes, Decimal("0"))
        # Ils n'entrent ni dans la collecte ni dans le net du groupeur.
        self.assertEqual(retrait.collecte, Decimal("128000"))

    def test_la_cloture_fait_passer_les_commandes_en_cloturee(self):
        cloturer_campagne(self.campagne)
        self.assertEqual(
            self.campagne.commandes.filter(
                statut=Commande.Statut.CLOTUREE
            ).count(),
            32,
        )

    def test_aucun_frais_sur_un_groupage_annule(self):
        """§7 du cahier des charges, et c'est montré à l'écran 18."""
        annuler_campagne(self.campagne)

        self.assertFalse(Retrait.objects.filter(campagne=self.campagne).exists())
        self.assertEqual(
            self.campagne.commandes.filter(
                statut=Commande.Statut.REMBOURSEE
            ).count(),
            32,
        )


class StatutsTest(TestCase):
    """Deux listes de statuts « payants » existent. Elles doivent coïncider."""

    def test_statuts_payants_restent_synchronises(self):
        from groupachat.catalogue.models import Statut_PAYANTS

        self.assertEqual(
            tuple(Statut_PAYANTS),
            tuple(statut.value for statut in Commande.STATUTS_PAYANTS),
            "Les statuts payants du catalogue et des commandes ont divergé : "
            "les compteurs d'acheteurs confirmés et la collecte vont se "
            "contredire.",
        )
