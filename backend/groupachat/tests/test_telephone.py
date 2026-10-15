# -*- coding: utf-8 -*-
"""Un numéro de téléphone, une seule forme en base.

**Le téléphone est l'identifiant de compte de ce MVP.** Il n'y a ni mot de
passe ni session : un acheteur retrouve ses commandes par son numéro, un
groupeur retrouve son dossier KYC par le sien. Deux écritures du même numéro
font donc **deux comptes pour la même personne**, et chaque conséquence
ressemble à autre chose qu'à un problème de format :

| Ce qu'on observe | Ce que c'est vraiment |
|---|---|
| « Mes commandes ont disparu » | Il s'est connecté avec l'autre écriture |
| « Je ne retrouve pas mon dossier » | Même cause, côté groupeur |
| Un redépôt de dossier qui échoue | La contrainte d'unicité, sur l'autre forme |

Le défaut était réel et vivait dans le produit : le formulaire d'inscription du
groupeur envoyait ``+22890777888``, la feuille de connexion de l'acheteur
``90777888``, et les deux atterrissaient en base tels quels.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.tests.aides import connecter

from groupachat import domaine
from groupachat.catalogue.models import Campagne
from groupachat.comptes.models import Acheteur, Groupeur


class Normalisation(TestCase):
    """La fonction seule, sans base ni API."""

    def test_les_ecritures_courantes_donnent_le_meme_numero(self) -> None:
        """On est **tolérant à l'entrée et strict en base**.

        Personne ne doit se demander comment écrire son numéro, et le code ne
        doit jamais avoir à deviner laquelle des cinq formes il manipule.
        """
        for ecriture in (
            "90123456",
            "90 12 34 56",
            "+22890123456",
            "+228 90 12 34 56",
            "00228-90123456",
            "228 90123456",
        ):
            with self.subTest(ecriture=ecriture):
                self.assertEqual(
                    domaine.normaliser_telephone(ecriture), "+22890123456"
                )

    def test_un_numero_trop_court_est_refuse(self) -> None:
        """**On ne complète pas, on ne tronque pas.**

        Un numéro à sept chiffres est une faute de frappe. L'accepter en
        l'état ferait échouer l'appel du livreur le jour de la livraison —
        c'est-à-dire au pire moment, et sans que personne ne comprenne
        pourquoi.
        """
        for mauvais in ("9012345", "901234567", "", "abcdefgh"):
            with self.subTest(mauvais=mauvais):
                with self.assertRaises(domaine.NumeroInvalide):
                    domaine.normaliser_telephone(mauvais)

    def test_le_message_d_erreur_montre_un_exemple(self) -> None:
        """« Format invalide » n'apprend rien ; un exemple, si."""
        with self.assertRaises(domaine.NumeroInvalide) as leve:
            domaine.normaliser_telephone("9012345")
        self.assertIn("90 12 34 56", str(leve.exception))


class MemeNumeroMemeCompte(TestCase):
    """Le cœur du sujet : deux écritures, un seul compte."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.groupeur = Groupeur.objects.create(
            pseudonyme="Mama Gro",
            nom_complet="Akossiwa Mensah",
            telephone="+22891000001",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            titulaire_mobile_money="Akossiwa Mensah",
            numero_mobile_money="+22891000001",
        )
        self.campagne = Campagne.objects.create(
            groupeur=self.groupeur,
            titre="Écouteurs filaires avec micro",
            description="Un lot de cent.",
            contenu_part="Une paire",
            categorie=Campagne.Categorie.ELECTRONIQUE,
            prix_part=Decimal("4000"),
            objectif_participants=40,
            date_fin=timezone.now() + timedelta(days=2),
        )

    def payer(self, telephone: str, cle: str):
        """Se connecte avec cette écriture du numéro, puis paie.

        C'est **la connexion** qui porte le numéro maintenant, plus le
        paiement : la normalisation doit donc tenir à l'ouverture de session.
        """
        client = APIClient()
        connecter(client, telephone, nom="Akosua Doe")
        return client.post(
            "/api/commandes/payer/",
            {
                "campagne": self.campagne.pk,
                "quantite": 1,
                "quartier": "Tokoin",
                "repere": "Pharmacie Sodji",
                "cle_idempotence": cle,
            },
            format="json",
        )

    def test_deux_ecritures_ne_font_pas_deux_acheteurs(self) -> None:
        """**Le défaut tel qu'il se produisait.**

        Un acheteur paie depuis son téléphone, puis se reconnecte en tapant son
        numéro avec l'indicatif. Sans normalisation, il devenait quelqu'un
        d'autre.
        """
        self.assertEqual(self.payer("90123456", "cle-1").status_code, 201)
        self.assertEqual(self.payer("+228 90 12 34 56", "cle-2").status_code, 201)

        self.assertEqual(Acheteur.objects.count(), 1)
        self.assertEqual(Acheteur.objects.get().telephone, "+22890123456")

    def test_on_retrouve_ses_commandes_quelle_que_soit_l_ecriture(self) -> None:
        """La **connexion** normalise, donc on retombe sur le même compte.

        Sans cela, on enregistrerait ``+22890123456`` et on ouvrirait une
        session pour ``90123456`` : deux comptes, et l'acheteur croit ses
        commandes perdues. Un échec silencieux, le pire des trois.
        """
        self.payer("90123456", "cle-1")

        for ecriture in ("90123456", "+22890123456", "90 12 34 56"):
            with self.subTest(ecriture=ecriture):
                client = APIClient()
                connecter(client, ecriture)
                reponse = client.get("/api/commandes/")
                self.assertEqual(len(reponse.data), 1, ecriture)

    def test_un_numero_invalide_est_refuse_a_la_saisie(self) -> None:
        """Et sur le champ ``telephone``, pour s'afficher sous la bonne case."""
        reponse = self.client.post(
            "/api/comptes/code/", {"telephone": "9012345"}, format="json"
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("telephone", reponse.data)

    def test_le_dossier_du_groupeur_se_retrouve_aussi(self) -> None:
        """Les deux côtés emploient la même règle.

        C'est le point : elle est sur le **champ**, pas dans chaque vue. Une
        normalisation posée vue par vue s'oublie à la première route ajoutée,
        et ne se voit que longtemps après.
        """
        depot = self.client.post(
            "/api/groupeurs/",
            {
                "pseudonyme": "Chez Sika",
                "nom_complet": "Sika Adjo",
                "telephone": "90 77 88 99",
                "courriel": "",
                "titulaire_mobile_money": "Sika Adjo",
                "numero_mobile_money": "+228 90 77 88 99",
                "pieces": [
                    {"nature": "piece-recto", "reference": "coffre/a"},
                    {"nature": "piece-verso", "reference": "coffre/b"},
                    {"nature": "selfie", "reference": "coffre/c"},
                ],
            },
            format="json",
        )
        self.assertEqual(depot.status_code, 201, depot.data)

        groupeur = Groupeur.objects.get(pseudonyme="Chez Sika")
        self.assertEqual(groupeur.telephone, "+22890778899")
        # Les deux champs sont normalisés, donc comparables entre eux.
        self.assertEqual(groupeur.numero_mobile_money, "+22890778899")

        for ecriture in ("90778899", "+22890778899", "00228 90 77 88 99"):
            with self.subTest(ecriture=ecriture):
                reponse = self.client.get(
                    "/api/groupeurs/dossier/", {"telephone": ecriture}
                )
                self.assertEqual(reponse.status_code, 200, ecriture)
                self.assertEqual(reponse.data["pseudonyme"], "Chez Sika")
