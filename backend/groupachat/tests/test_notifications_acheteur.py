# -*- coding: utf-8 -*-
"""La cloche de l'acheteur : ce qui la remplit, et ce qui n'y entre jamais.

La cloche était dessinée dans les deux en-têtes acheteur, **pastille
comprise**, et ne faisait rien : le compteur était la constante `1` écrite
dans le routeur. Elle promettait donc en permanence une information qui
n'existait pas.

⚠️ **Le point que ces tests protègent avant tout : ce n'est pas une
messagerie.** Le groupeur *déclenche* une notification, il n'en rédige jamais
le texte, et il n'apprend rien sur qui l'a reçue. Si cette règle tombe, la
cloche devient le canal privé que le produit refuse — et elle le deviendrait
sans que rien ne casse, ce qui est la pire façon de perdre une règle.

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
from ..commandes.models import Commande, annuler_campagne, cloturer_campagne
from ..comptes.models import Acheteur, Groupeur
from ..echanges.models import Notification, Question


def _un_groupeur(telephone: str) -> Groupeur:
    # ⚠️ Le pseudonyme est unique en base : il dérive du numéro, sinon deux
    # groupeurs dans un même test se marchent dessus.
    return Groupeur.objects.create(
        pseudonyme=f"Mama Gro {telephone[-3:]}",
        nom_complet="Afi Mensah",
        telephone=telephone,
        statut_kyc=Groupeur.StatutKyc.VALIDE,
    )


def _une_campagne(groupeur: Groupeur) -> Campagne:
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


def _une_commande(campagne, acheteur, cle: str) -> Commande:
    return Commande.objects.create(
        campagne=campagne,
        acheteur=acheteur,
        quantite=1,
        montant_parts=Decimal("4000"),
        frais_livraison=Decimal("1000"),
        total=Decimal("5000"),
        quartier="Tokoin",
        repere="Face à la pharmacie",
        telephone=acheteur.telephone,
        cle_idempotence=cle,
        # ⚠️ Unique en base, donc une valeur distincte par commande : le
        # laisser vide fait passer la deuxième insertion pour un doublon.
        code_livraison=cle.upper(),
    )


class LaClotureNotifieLesParticipants(APITestCase):
    """L'événement que l'acheteur attend le plus : le groupeur a été payé."""

    def setUp(self):
        self.campagne = _une_campagne(_un_groupeur("+22890000010"))
        self.un = Acheteur.objects.create(telephone="+22891000010", nom="Akosua Doe")
        self.deux = Acheteur.objects.create(telephone="+22891000011", nom="Kofi A")
        _une_commande(self.campagne, self.un, "cl-1")
        _une_commande(self.campagne, self.deux, "cl-2")

    def test_chaque_participant_est_prevenu(self):
        cloturer_campagne(self.campagne)

        self.assertEqual(
            Notification.objects.filter(
                nature=Notification.Nature.GROUPAGE_CLOTURE
            ).count(),
            2,
        )

    def test_la_notification_ne_dit_pas_que_l_argent_reste_detenu(self):
        """⚠️ §1.7 — à la clôture, le groupeur **a déjà été payé**.

        C'est la garantie de Group Achat qui porte à partir de ce moment, pas
        la détention des fonds. Écrire « votre argent est bloqué jusqu'à la
        livraison » ici serait faux, et c'est la formulation la plus tentante.
        """
        cloturer_campagne(self.campagne)
        corps = Notification.objects.first().corps

        self.assertNotIn("bloqué", corps)
        self.assertIn("garantit votre livraison", corps)

    def test_deux_commandes_d_une_meme_personne_ne_font_qu_une_notification(self):
        """Elle parle du groupage, pas de la commande."""
        _une_commande(self.campagne, self.un, "cl-3")

        cloturer_campagne(self.campagne)

        self.assertEqual(
            Notification.objects.filter(destinataire=self.un).count(), 1
        )


class LAnnulationNotifieLeRemboursement(APITestCase):
    def setUp(self):
        self.campagne = _une_campagne(_un_groupeur("+22890000011"))
        self.acheteuse = Acheteur.objects.create(
            telephone="+22891000012", nom="Akosua Doe"
        )
        _une_commande(self.campagne, self.acheteuse, "an-1")

    def test_le_montant_rembourse_est_dit_en_clair(self):
        """Un « vous avez été remboursé » sans chiffre n'aide personne.

        Et le montant est **livraison comprise** : aucun frais n'est prélevé
        sur un groupage annulé (§7). Un chiffre hors livraison ferait croire à
        une retenue.
        """
        annuler_campagne(self.campagne)
        corps = Notification.objects.get(
            nature=Notification.Nature.GROUPAGE_ANNULE
        ).corps

        self.assertIn("5 000 F", corps)
        self.assertIn("livraison compris", corps)

    def test_la_notification_part_bien_malgre_le_changement_de_statut(self):
        """⚠️ **Le piège de cette fonction.**

        ``annuler_campagne`` met les commandes à ``remboursee``. Lire les
        destinataires *après* cet ``update`` ne renverrait plus personne — un
        remboursement annoncé nulle part, qui est exactement le cas où
        l'acheteur appelle. On les lit donc avant, et ce test le vérifie.
        """
        annuler_campagne(self.campagne)

        self.assertEqual(
            Notification.objects.filter(destinataire=self.acheteuse).count(), 1
        )


class LAnnonceDeLArrivee(APITestCase):
    """Écran 15 — le groupeur déclenche, la plateforme écrit."""

    def setUp(self):
        self.groupeur = _un_groupeur("+22890000012")
        self.campagne = _une_campagne(self.groupeur)
        self.acheteuse = Acheteur.objects.create(
            telephone="+22891000013", nom="Akosua Doe"
        )
        _une_commande(self.campagne, self.acheteuse, "ar-1")
        self.url = reverse(
            "espace-groupeur-annoncer-l-arrivee", args=[self.campagne.pk]
        )

    def _cloturer(self):
        cloturer_campagne(self.campagne)
        self.campagne.refresh_from_db()
        Notification.objects.all().delete()

    def test_apres_la_cloture_les_participants_sont_prevenus(self):
        self._cloturer()

        reponse = self.client.post(
            self.url, {"telephone": self.groupeur.telephone}, format="json"
        )

        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertEqual(reponse.data["prevenus"], 1)
        notification = Notification.objects.get(
            nature=Notification.Nature.PRODUIT_ARRIVE
        )
        self.assertEqual(notification.destinataire, self.acheteuse)

    def test_la_reponse_ne_renvoie_qu_un_compte(self):
        """⚠️ **La règle qui rend cette fonctionnalité acceptable.**

        Le groupeur ne voit ni nom, ni numéro, ni quartier : il annonce un
        fait, nous le distribuons. Une liste de destinataires lui donnerait
        exactement le fichier de clients que l'anonymat lui refuse partout
        ailleurs.
        """
        self._cloturer()

        reponse = self.client.post(
            self.url, {"telephone": self.groupeur.telephone}, format="json"
        )

        self.assertEqual(set(reponse.data), {"prevenus", "deja_annonce", "annonce_le"})
        texte = str(reponse.data)
        self.assertNotIn("Akosua", texte)
        self.assertNotIn("91000013", texte)
        self.assertNotIn("Tokoin", texte)

    def test_le_groupeur_ne_redige_aucun_texte(self):
        """Un champ libre vers ses acheteurs serait une messagerie.

        On envoie un texte dans la requête : il doit être purement et
        simplement ignoré, et le corps rester celui de la plateforme.
        """
        self._cloturer()

        self.client.post(
            self.url,
            {
                "telephone": self.groupeur.telephone,
                "corps": "Appelez-moi au 90 11 22 33",
                "texte": "Appelez-moi au 90 11 22 33",
            },
            format="json",
        )

        corps = Notification.objects.get(
            nature=Notification.Nature.PRODUIT_ARRIVE
        ).corps
        self.assertNotIn("90 11 22 33", corps)
        self.assertIn("Votre livraison est en préparation", corps)

    def test_annoncer_deux_fois_n_envoie_qu_une_notification(self):
        """Une cloche qui répète perd le droit d'être regardée."""
        self._cloturer()

        premier = self.client.post(
            self.url, {"telephone": self.groupeur.telephone}, format="json"
        )
        second = self.client.post(
            self.url, {"telephone": self.groupeur.telephone}, format="json"
        )

        self.assertEqual(premier.data["prevenus"], 1)
        # ⚠️ 200 et non une erreur : de son point de vue, c'est bien annoncé.
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["prevenus"], 0)
        self.assertTrue(second.data["deja_annonce"])
        self.assertEqual(
            Notification.objects.filter(
                nature=Notification.Nature.PRODUIT_ARRIVE
            ).count(),
            1,
        )

    def test_on_n_annonce_pas_l_arrivee_d_un_groupage_encore_ouvert(self):
        """« Le produit est arrivé » avant la clôture n'a pas de sens."""
        reponse = self.client.post(
            self.url, {"telephone": self.groupeur.telephone}, format="json"
        )

        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(Notification.objects.count(), 0)

    def test_on_n_annonce_pas_sur_le_groupage_d_un_autre(self):
        autre = _un_groupeur("+22890000013")
        self._cloturer()

        reponse = self.client.post(
            self.url, {"telephone": autre.telephone}, format="json"
        )

        self.assertEqual(reponse.status_code, 404)
        self.assertEqual(Notification.objects.count(), 0)


class LaReponseAUneQuestionNotifieSonAuteur(APITestCase):
    def setUp(self):
        self.groupeur = _un_groupeur("+22890000014")
        self.campagne = _une_campagne(self.groupeur)
        self.auteur = Acheteur.objects.create(
            telephone="+22891000014", nom="Akosua Doe"
        )
        self.question = Question.objects.create(
            campagne=self.campagne,
            auteur=self.auteur,
            texte="Est-ce que la garantie couvre un défaut de fabrication ?",
        )
        self.url = reverse("espace-groupeur-repondre", args=[self.question.pk])

    def test_l_auteur_est_prevenu(self):
        """Sans cette notification, une réponse n'était lue par presque
        personne : il fallait revenir de soi-même sur la fiche du produit."""
        reponse = self.client.post(
            self.url,
            {"telephone": self.groupeur.telephone, "reponse": "Oui, six mois."},
            format="json",
        )

        self.assertEqual(reponse.status_code, 200, reponse.data)
        notification = Notification.objects.get(
            nature=Notification.Nature.REPONSE_QUESTION
        )
        self.assertEqual(notification.destinataire, self.auteur)
        self.assertIn("Oui, six mois.", notification.corps)
        self.assertEqual(notification.question, self.question)

    def test_une_reponse_refusee_par_la_moderation_ne_notifie_personne(self):
        """⚠️ **Le trou qu'il ne faut pas ouvrir.**

        Le §15 filtre les deux sens. Si la notification partait avant le
        filtre — ou malgré son refus — la cloche distribuerait le numéro que
        le fil public, lui, bloque encore. Ce serait un contournement complet
        de la modération par une route qui n'a pas l'air d'en être une.
        """
        reponse = self.client.post(
            self.url,
            {
                "telephone": self.groupeur.telephone,
                "reponse": "Appelez-moi au 90112233",
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(Notification.objects.count(), 0)


class LaRouteDeLaCloche(APITestCase):
    def setUp(self):
        self.campagne = _une_campagne(_un_groupeur("+22890000015"))
        connecter(self.client, "91000015", nom="Akosua Doe")
        self.acheteuse = Acheteur.objects.get(telephone="+22891000015")
        _une_commande(self.campagne, self.acheteuse, "cl-10")
        cloturer_campagne(self.campagne)

    def test_elle_sert_ses_notifications(self):
        reponse = self.client.get(reverse("notification-list"))

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 1)
        self.assertFalse(reponse.data[0]["lue"])
        self.assertEqual(reponse.data[0]["campagne_titre"], self.campagne.titre)

    def test_elle_ne_sert_pas_celles_des_autres(self):
        """Elles portent ce qu'on a commandé et combien on a été remboursé."""
        autre = APIClient()
        connecter(autre, "91000016", nom="Kofi B")

        reponse = autre.get(reverse("notification-list"))

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data, [])

    def test_sans_session_elle_renvoie_401(self):
        """401 et non 403 : l'écran rouvre la feuille de connexion."""
        anonyme = APIClient()

        self.assertEqual(anonyme.get(reverse("notification-list")).status_code, 401)

    def test_tout_lu_eteint_la_pastille(self):
        reponse = self.client.post(reverse("notification-tout-lu"))

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["lues"], 1)
        self.assertEqual(
            Notification.objects.filter(
                destinataire=self.acheteuse, lue_le__isnull=True
            ).count(),
            0,
        )

    def test_tout_lu_sur_une_cloche_deja_vide_ne_fait_rien(self):
        self.client.post(reverse("notification-tout-lu"))

        second = self.client.post(reverse("notification-tout-lu"))

        self.assertEqual(second.data["lues"], 0)
