# -*- coding: utf-8 -*-
"""Les deux gestes de recours : signaler un message, refuser un colis.

Ils avaient un bouton dessiné et **aucun serveur derrière**. Les deux sont des
recours, c'est-à-dire ce qu'on fait quand le reste du produit a échoué : le
filtre de modération a laissé passer un message, ou le colis présenté n'est
pas celui qui a été commandé. Un recours qui ne marche pas est pire qu'un
recours absent, parce qu'on y a cru.

Chaque test porte le nom de la règle qu'il protège.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from .aides import connecter
from ..catalogue.models import Campagne
from ..commandes.models import Commande
from ..comptes.models import Acheteur, Groupeur
from ..echanges.models import Question, SignalementQuestion


def _une_campagne(telephone_groupeur: str) -> Campagne:
    groupeur = Groupeur.objects.create(
        pseudonyme="Mama Gro",
        nom_complet="Afi Mensah",
        telephone=telephone_groupeur,
        statut_kyc=Groupeur.StatutKyc.VALIDE,
    )
    return Campagne.objects.create(
        groupeur=groupeur,
        titre="Écouteurs filaires avec micro",
        description="Écouteurs filaires avec micro intégré.",
        contenu_part="1 écouteur",
        categorie=Campagne.Categorie.ELECTRONIQUE,
        prix_part=Decimal("4000"),
        objectif_participants=30,
        date_fin=timezone.now() + timedelta(days=3),
    )


class LeSignalementDUneQuestion(APITestCase):
    """§15, niveau 3 — un humain, après publication."""

    def setUp(self):
        self.campagne = _une_campagne("+22890000001")
        self.question = Question.objects.create(
            campagne=self.campagne,
            auteur=Acheteur.objects.create(telephone="+22891000002", nom="Kofi A"),
            texte="Est-ce que la garantie couvre un défaut de fabrication ?",
        )
        self.url = reverse("question-signaler", args=[self.question.pk])

    def test_un_lecteur_connecte_peut_signaler(self):
        connecter(self.client, "91000001", nom="Akosua Doe")
        reponse = self.client.post(self.url, {"motif": "coordonnees"}, format="json")

        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertTrue(reponse.data["signale"])
        self.assertEqual(SignalementQuestion.objects.count(), 1)

    def test_signaler_ne_depublie_pas_la_question(self):
        """⚠️ **La règle la plus importante de ce fichier.**

        Dépublier sur signalement donnerait à n'importe qui le pouvoir de
        faire taire n'importe qui : il suffirait de signaler la question
        gênante pour l'effacer du seul canal public du produit. Le §15 confie
        la décision à un humain, après publication.
        """
        connecter(self.client, "91000001", nom="Akosua Doe")
        self.client.post(self.url, {"motif": "inapproprie"}, format="json")

        self.question.refresh_from_db()
        self.assertEqual(self.question.etat, Question.Etat.PUBLIEE)

        # Et elle sort toujours de la liste publique.
        liste = self.client.get(
            reverse("question-list"), {"campagne": self.campagne.pk}
        )
        self.assertEqual(liste.data["count"], 1)

    def test_un_motif_hors_liste_est_refuse(self):
        """Pas de champ libre : la file doit rester triable (§15)."""
        connecter(self.client, "91000001", nom="Akosua Doe")
        reponse = self.client.post(
            self.url, {"motif": "il me déplaît"}, format="json"
        )

        self.assertEqual(reponse.status_code, 400)
        self.assertIn("motif", reponse.data)
        self.assertEqual(SignalementQuestion.objects.count(), 0)

    def test_deux_signalements_du_meme_lecteur_ne_comptent_que_pour_un(self):
        """Sinon un seul lecteur décide de ce qu'un humain regarde en premier."""
        connecter(self.client, "91000001", nom="Akosua Doe")
        premier = self.client.post(self.url, {"motif": "coordonnees"}, format="json")
        second = self.client.post(self.url, {"motif": "coordonnees"}, format="json")

        self.assertEqual(premier.status_code, 201)
        # ⚠️ 200 et non 400 : de son point de vue, le geste a réussi.
        self.assertEqual(second.status_code, 200)
        self.assertEqual(SignalementQuestion.objects.count(), 1)

    def test_deux_lecteurs_differents_comptent_pour_deux(self):
        """C'est le nombre qui fait remonter un message dans la file."""
        connecter(self.client, "91000001", nom="Akosua Doe")
        self.client.post(self.url, {"motif": "coordonnees"}, format="json")

        autre = APIClient()
        connecter(autre, "91000005", nom="Kofi B")
        autre.post(self.url, {"motif": "hors-plateforme"}, format="json")

        self.assertEqual(self.question.signalements.count(), 2)

    def test_signaler_sans_session_renvoie_401(self):
        """401 et non 403 : l'écran doit rouvrir la feuille de connexion."""
        reponse = self.client.post(self.url, {"motif": "coordonnees"}, format="json")
        self.assertEqual(reponse.status_code, 401)


class LeRefusDUnColis(APITestCase):
    """Écran 9 — le moment où la garantie est mise à l'épreuve."""

    def setUp(self):
        self.campagne = _une_campagne("+22890000002")
        connecter(self.client, "91000003", nom="Akosua Doe")
        self.acheteur = Acheteur.objects.get(telephone="+22891000003")
        self.commande = Commande.objects.create(
            campagne=self.campagne,
            acheteur=self.acheteur,
            quantite=1,
            montant_parts=Decimal("4000"),
            frais_livraison=Decimal("1000"),
            total=Decimal("5000"),
            quartier="Tokoin",
            repere="Face à la pharmacie",
            telephone="+22891000003",
            cle_idempotence="refus-1",
            statut=Commande.Statut.EN_LIVRAISON,
        )
        self.url = reverse("commande-refuser", args=[self.commande.pk])

    def test_refuser_pendant_la_livraison_ouvre_un_litige(self):
        reponse = self.client.post(
            self.url,
            {"motif": "pas-le-produit", "description": "Ce ne sont pas les miens."},
            format="json",
        )

        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.LITIGE)
        self.assertEqual(self.commande.motif_de_refus, "pas-le-produit")
        self.assertEqual(
            self.commande.description_du_refus, "Ce ne sont pas les miens."
        )
        self.assertIsNotNone(self.commande.refuse_le)

    def test_le_refus_ne_rembourse_pas_tout_seul(self):
        """⚠️ **« Remboursé si le refus est justifié »**, et un humain juge.

        Rembourser sur déclaration se paierait sur notre trésorerie à chaque
        refus, vrai ou non — le groupeur a déjà retiré son argent à la
        clôture. L'écran 9 promet un examen sous 48 h, pas un virement.
        """
        self.client.post(self.url, {"motif": "abime"}, format="json")

        self.commande.refresh_from_db()
        self.assertNotEqual(self.commande.statut, Commande.Statut.REMBOURSEE)

    def test_on_ne_refuse_pas_avant_la_livraison(self):
        """Il n'y a rien à refuser : le colis n'est pas parti."""
        self.commande.statut = Commande.Statut.PAYEE
        self.commande.save(update_fields=["statut"])

        reponse = self.client.post(self.url, {"motif": "abime"}, format="json")

        self.assertEqual(reponse.status_code, 400)
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.PAYEE)

    def test_on_ne_refuse_plus_une_commande_livree(self):
        """Le code a été donné : c'est une réclamation, pas un refus de colis."""
        self.commande.statut = Commande.Statut.LIVREE
        self.commande.save(update_fields=["statut"])

        reponse = self.client.post(self.url, {"motif": "abime"}, format="json")

        self.assertEqual(reponse.status_code, 400)

    def test_un_motif_hors_liste_est_refuse(self):
        reponse = self.client.post(self.url, {"motif": "pas content"}, format="json")

        self.assertEqual(reponse.status_code, 400)
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.EN_LIVRAISON)

    def test_on_ne_refuse_pas_le_colis_de_quelqu_un_d_autre(self):
        """La commande vient de la session.

        ``get_queryset`` ne sert que les commandes de l'acheteur connecté,
        donc la route répond **404 et non 403** : un 403 confirmerait à un
        inconnu que cette commande existe.
        """
        autre = APIClient()
        connecter(autre, "91000004", nom="Kofi B")

        reponse = autre.post(self.url, {"motif": "abime"}, format="json")

        self.assertEqual(reponse.status_code, 404)
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.EN_LIVRAISON)
