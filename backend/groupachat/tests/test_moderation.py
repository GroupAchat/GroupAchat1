# -*- coding: utf-8 -*-
"""Le filtre des messages publics et les contrôles KYC côté base.

⚠️ Ces tests vérifient le filtre **côté serveur**, pas côté React. Le client
prévient l'utilisateur avant l'envoi ; le serveur protège la base. Un client
modifié, une requête forgée ou un appel direct à l'API contournent le premier
et pas le second — et c'est exactement ce que ces tests simulent.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.tests.aides import connecter

from groupachat import moderation
from groupachat.catalogue.models import Campagne
from groupachat.comptes.models import Acheteur, Groupeur
from groupachat.echanges.models import Question


class FiltreLexicalTest(TestCase):
    """Ce que le filtre doit arrêter, et ce qu'il doit laisser passer."""

    def test_une_vraie_question_passe(self):
        for message in (
            "C'est quelle marque d'écouteurs ?",
            "La livraison va jusqu'à Adidogomé ?",
            "On peut prendre 2 écouteurs ?",
            "Le bidon fait bien 20 litres ?",
            "Garantie 3 mois, c'est pièces et main d'œuvre ?",
        ):
            self.assertTrue(moderation.verifier(message).publiable, message)

    def test_un_numero_est_arrete(self):
        for message in (
            "Appelez-moi au 90 12 34 56",
            "+228 90 12 34 56",
            "mon 90.12.34.56",
            "90-12-34-56 svp",
        ):
            verdict = moderation.verifier(message)
            self.assertFalse(verdict.publiable, message)

    def test_les_petits_nombres_ne_declenchent_rien(self):
        """« 20 litres » et « 2 paires » doivent passer.

        Un filtre qui bloque les quantités rendrait la moitié des questions
        légitimes impossibles.
        """
        for message in ("Il en faut 20 litres", "2 paires taille 42", "25 kg ?"):
            self.assertTrue(moderation.verifier(message).publiable, message)

    def test_les_autres_canaux_sont_arretes(self):
        for message in (
            "Mon WhatsApp est dispo",
            "ajoutez-moi sur Telegram",
            "envoyez un e-mail",
        ):
            self.assertFalse(moderation.verifier(message).publiable, message)

    def test_la_vente_hors_plateforme_est_arretee(self):
        for message in (
            "on peut faire ça hors du site",
            "directement avec vous ça coûte moins",
            "sans passer par la plateforme",
        ):
            self.assertFalse(moderation.verifier(message).publiable, message)

    def test_une_longue_suite_de_chiffres_est_arretee(self):
        """Un faux positif assume, et il vaut mieux l'ecrire que le subir.

        Huit chiffres d'affilee suffisent a declencher le filtre. Une
        reference produit a dix chiffres — « reference 1234567890 » — est donc
        bloquee alors qu'elle est legitime.

        **C'est le bon arbitrage.** Laisser passer un numero coute le modele
        economique ; bloquer une reference coute une reformulation. Et le
        message dit a l'auteur quel passage corriger, donc il s'en sort.

        Si ce cas devient frequent, la reponse n'est pas de relacher le seuil
        mais d'ajouter un champ « reference » au formulaire, ou le filtre ne
        s'applique pas.
        """
        self.assertFalse(moderation.verifier("reference 1234567890").publiable)
        # Sept chiffres passent : c'est en dessous de la longueur d'un numero
        # togolais, qui en compte huit.
        self.assertTrue(moderation.verifier("reference 1234567").publiable)

    def test_le_passage_en_cause_est_renvoye(self):
        """L'auteur doit voir **quoi** corriger, pas seulement qu'il a échoué."""
        verdict = moderation.verifier("Appelez-moi au 90 12 34 56 merci")
        self.assertIsNotNone(verdict.passage)
        self.assertIn("90", verdict.passage or "")


class RedactionTest(TestCase):
    """La copie de refus est contrainte — tableau de l'écran 10.

    C'est la copie la plus sensible du produit. Ces tests l'empêchent d'être
    réécrite « pour faire plus court » par quelqu'un qui n'aura pas lu le
    tableau.
    """

    MOTS_INTERDITS = ("interdit", "violation", "contournement", "fraude")

    def test_aucun_mot_accusateur_cote_acheteur(self):
        """La plupart des gens qui écrivent leur numéro le font de bonne foi.

        Les traiter en fraudeurs est faux, et les fait fuir.
        """
        for motif in (
            moderation.MOTIF_NUMERO,
            moderation.MOTIF_CONTACT,
            moderation.MOTIF_HORS_PLATEFORME,
        ):
            texte = " ".join(moderation.expliquer(motif, role="acheteur").values())
            for mot in self.MOTS_INTERDITS:
                self.assertNotIn(mot, texte.lower(), f"{motif} / {mot}")

    def test_le_refus_est_au_futur(self):
        """« ne **sera** pas publié » : rien n'est encore parti."""
        explication = moderation.expliquer(moderation.MOTIF_NUMERO)
        self.assertIn("ne sera pas publié", explication["titre"])

    def test_on_parle_de_sa_protection_pas_de_notre_reglement(self):
        explication = moderation.expliquer(moderation.MOTIF_NUMERO)
        self.assertIn("vous identifier", explication["corps"])
        self.assertIn("restent anonymes", explication["corps"])

    def test_le_cas_de_bonne_foi_est_traite(self):
        """Celui qui donne son numéro veut être joignable : on lui dit où ça va."""
        explication = moderation.expliquer(moderation.MOTIF_NUMERO)
        self.assertIn("rassurance", explication)
        self.assertIn("livreur", explication["rassurance"])

    def test_la_copie_groupeur_est_plus_ferme(self):
        """La bonne foi y est moins probable : il y gagnerait nos frais."""
        texte = moderation.expliquer(
            moderation.MOTIF_NUMERO, role="groupeur"
        )["corps"]
        self.assertIn("enregistrée", texte)
        self.assertIn("suspension", texte)


class FiltreEnBaseTest(TestCase):
    """Le filtre s'applique à l'enregistrement, pas seulement à l'affichage."""

    def setUp(self) -> None:
        groupeur = Groupeur.objects.create(
            pseudonyme="Mama Gro",
            nom_complet="Akossiwa Mensah",
            telephone="+22891000001",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            titulaire_mobile_money="Akossiwa Mensah",
        )
        self.campagne = Campagne.objects.create(
            groupeur=groupeur,
            titre="Écouteurs filaires avec micro",
            description="Écouteurs avec micro.",
            contenu_part="1 écouteur",
            categorie=Campagne.Categorie.ELECTRONIQUE,
            prix_part=Decimal("4000"),
            objectif_participants=40,
            date_fin=timezone.now() + timedelta(days=2),
        )
        self.acheteuse = Acheteur.objects.create(
            telephone="+22890123456", nom="Akosua Doe"
        )

    def test_une_question_avec_un_numero_n_est_pas_enregistree(self):
        with self.assertRaises(ValidationError):
            Question.objects.create(
                campagne=self.campagne,
                auteur=self.acheteuse,
                texte="Appelez-moi au 90 12 34 56",
            )
        self.assertEqual(Question.objects.count(), 0)

    def test_l_api_refuse_aussi(self):
        """Le contrôle ne dépend pas du client : un appel direct est bloqué.

        **Avec un compte valide**, justement : le filtre n'est pas une
        conséquence de l'absence d'authentification. Quelqu'un de parfaitement
        identifié qui laisse son numéro dans une question publique est
        exactement le cas que le §15 vise.
        """
        client = APIClient()
        connecter(client, "+22890123456")
        reponse = client.post(
            "/api/questions/",
            {
                "campagne": self.campagne.pk,
                "texte": "Mon numéro : 90 12 34 56",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(Question.objects.count(), 0)

    def test_une_vraie_question_est_enregistree(self):
        question = Question.objects.create(
            campagne=self.campagne,
            auteur=self.acheteuse,
            texte="Quelle est la longueur du câble ?",
        )
        self.assertEqual(question.etat, Question.Etat.PUBLIEE)

    def test_l_auteur_n_apparait_que_par_son_prenom_et_son_initiale(self):
        question = Question.objects.create(
            campagne=self.campagne,
            auteur=self.acheteuse,
            texte="Quelle garantie ?",
        )
        self.assertEqual(question.auteur_affiche, "Akosua D.")

    def test_une_reponse_de_groupeur_avec_un_numero_est_refusee(self):
        """Le côté risqué du fil : le groupeur, lui, y gagnerait."""
        question = Question.objects.create(
            campagne=self.campagne,
            auteur=self.acheteuse,
            texte="Vous livrez à Agoè ?",
        )
        question.reponse = "Oui, appelez-moi au 91 00 00 01"
        with self.assertRaises(ValidationError):
            question.save()


class KycEnBaseTest(TestCase):
    """Le contrôle n° 2 bloque à l'enregistrement, pas seulement à l'écran."""

    def test_un_prete_nom_est_refuse(self):
        with self.assertRaises(ValidationError) as contexte:
            Groupeur.objects.create(
                pseudonyme="Chez Sika",
                nom_complet="Sika Adjo",
                telephone="+22891000003",
                titulaire_mobile_money="Kodjo Amegan",
            )
        self.assertIn("titulaire_mobile_money", contexte.exception.message_dict)

    def test_le_meme_nom_ecrit_autrement_passe(self):
        groupeur = Groupeur.objects.create(
            pseudonyme="Lomé Deals",
            nom_complet="Akossiwa Mensah",
            telephone="+22891000004",
            titulaire_mobile_money="MENSAH akossiwa",
        )
        self.assertEqual(groupeur.pseudonyme, "Lomé Deals")

    def test_un_groupeur_sans_dossier_valide_ne_lance_pas_de_campagne(self):
        """C'est ce qui rend tenable « vous êtes livré, ou remboursé »."""
        groupeur = Groupeur.objects.create(
            pseudonyme="Nouveau",
            nom_complet="Kossi Ewe",
            telephone="+22891000005",
        )
        self.assertFalse(groupeur.peut_lancer_une_campagne)

        with self.assertRaises(ValidationError):
            campagne = Campagne(
                groupeur=groupeur,
                titre="Test",
                description="Test",
                contenu_part="1 pièce",
                categorie=Campagne.Categorie.MAISON,
                prix_part=Decimal("1000"),
                objectif_participants=40,
                date_fin=timezone.now() + timedelta(days=1),
            )
            campagne.full_clean()

    def test_le_plafond_suit_le_niveau(self):
        groupeur = Groupeur.objects.create(
            pseudonyme="Confirmé",
            nom_complet="Ama Kplé",
            telephone="+22891000006",
            niveau=Groupeur.Niveau.CONFIRME,
        )
        self.assertEqual(groupeur.plafond, Decimal("600000"))
