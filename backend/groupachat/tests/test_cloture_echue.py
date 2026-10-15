# -*- coding: utf-8 -*-
"""« Seule la date clôture » — et il fallait que quelque chose le fasse.

La règle est non négociable côté produit. Elle ne l'était pas dans le code :
``cloturer_campagne`` n'avait que deux appelants, le bouton du groupeur et les
chargeurs de démonstration. Un groupage dont la date tombait restait donc
``ouverte`` indéfiniment, **et toutes les conséquences étaient silencieuses** :

- il disparaissait du catalogue, donc plus personne ne le voyait ;
- aucun ``Retrait`` n'était créé, donc l'argent déjà encaissé ne devenait
  jamais retirable — portefeuille à zéro sur une collecte réelle ;
- les commandes restaient ``payee``, donc l'écran 9 promettait encore
  « détenu jusqu'à la clôture » sur un groupage échu ;
- et la notification de clôture ne partait jamais.

Un groupeur qui oubliait un bouton bloquait l'argent de ses acheteurs sans que
personne ne soit averti. Chaque test porte le nom de la règle qu'il protège.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from ..catalogue.models import Campagne
from ..commandes.models import Commande, Retrait
from ..comptes.models import Acheteur, Groupeur
from ..echanges.models import Notification


def _un_groupeur(telephone: str) -> Groupeur:
    return Groupeur.objects.create(
        pseudonyme=f"Mama Gro {telephone[-3:]}",
        nom_complet="Afi Mensah",
        telephone=telephone,
        statut_kyc=Groupeur.StatutKyc.VALIDE,
    )


class LaClotureDesGroupagesEchus(APITestCase):
    def setUp(self):
        self.groupeur = _un_groupeur("+22890000020")
        self.campagne = Campagne.objects.create(
            groupeur=self.groupeur,
            titre="Écouteurs filaires avec micro",
            description="Écouteurs filaires avec micro intégré.",
            contenu_part="1 écouteur",
            categorie=Campagne.Categorie.ELECTRONIQUE,
            prix_part=Decimal("4000"),
            objectif_participants=30,
            date_fin=timezone.now() + timedelta(days=2),
        )
        self.acheteuse = Acheteur.objects.create(
            telephone="+22891000020", nom="Akosua Doe"
        )
        self.commande = Commande.objects.create(
            campagne=self.campagne,
            acheteur=self.acheteuse,
            quantite=1,
            montant_parts=Decimal("4000"),
            frais_livraison=Decimal("1000"),
            total=Decimal("5000"),
            quartier="Tokoin",
            repere="Face à la pharmacie",
            telephone="+22891000020",
            cle_idempotence="ech-1",
            code_livraison="ECH-001",
        )

    def _faire_passer_la_date(self):
        """⚠️ Par ``update``, pas par ``save``.

        ``Campagne.save`` repasse par ``full_clean``, qui refuse une date de
        fin dans le passé — avec raison, puisqu'on ne crée pas un groupage
        déjà échu. Le temps qui passe, lui, est légitime.
        """
        Campagne.objects.filter(pk=self.campagne.pk).update(
            date_fin=timezone.now() - timedelta(hours=1)
        )
        self.campagne.refresh_from_db()

    def test_un_groupage_echu_est_cloture(self):
        self._faire_passer_la_date()

        call_command("cloturer_les_groupages_echus", stdout=StringIO())

        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.statut, Campagne.Statut.EN_COURS)

    def test_l_argent_devient_retirable(self):
        """C'est la conséquence la plus grave de l'oubli : un portefeuille à
        zéro sur une collecte réelle."""
        self._faire_passer_la_date()

        call_command("cloturer_les_groupages_echus", stdout=StringIO())

        retrait = Retrait.objects.get(campagne=self.campagne)
        self.assertEqual(retrait.collecte, Decimal("4000"))
        self.assertEqual(retrait.frais_plateforme, Decimal("1500"))
        self.assertEqual(retrait.net, Decimal("2500"))
        self.assertEqual(retrait.etat, Retrait.Etat.RETIRABLE)

    def test_les_commandes_passent_a_cloturee(self):
        """Sinon l'écran 9 promet « détenu jusqu'à la clôture » après la
        clôture — une formulation interdite au §1.7 à ce stade."""
        self._faire_passer_la_date()

        call_command("cloturer_les_groupages_echus", stdout=StringIO())

        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.CLOTUREE)

    def test_les_participants_sont_prevenus(self):
        self._faire_passer_la_date()

        call_command("cloturer_les_groupages_echus", stdout=StringIO())

        self.assertEqual(
            Notification.objects.filter(
                destinataire=self.acheteuse,
                nature=Notification.Nature.GROUPAGE_CLOTURE,
            ).count(),
            1,
        )

    def test_un_groupage_encore_ouvert_n_est_pas_touche(self):
        """La date n'est pas passée : il n'y a rien à clôturer."""
        call_command("cloturer_les_groupages_echus", stdout=StringIO())

        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.statut, Campagne.Statut.OUVERTE)
        self.assertFalse(Retrait.objects.filter(campagne=self.campagne).exists())

    def test_relancer_la_commande_ne_cloture_pas_deux_fois(self):
        """⚠️ **Le risque d'une tâche planifiée : elle repasse.**

        Une seconde clôture créerait un second ``Retrait`` — donc 1 500 F de
        frais prélevés deux fois — et renverrait la notification. Le filtre
        sur ``statut=OUVERTE`` suffit, et ce test est là pour qu'il y reste.
        """
        self._faire_passer_la_date()

        call_command("cloturer_les_groupages_echus", stdout=StringIO())
        call_command("cloturer_les_groupages_echus", stdout=StringIO())

        self.assertEqual(Retrait.objects.filter(campagne=self.campagne).count(), 1)
        self.assertEqual(
            Notification.objects.filter(
                nature=Notification.Nature.GROUPAGE_CLOTURE
            ).count(),
            1,
        )

    def test_un_groupage_sous_son_objectif_se_cloture_quand_meme(self):
        """⚠️ **L'objectif n'est ni un plafond, ni un minimum, ni un
        déclencheur.**

        Une seule commande sur un objectif de trente : le groupage se clôture,
        et il peut aboutir. Annuler ici serait réintroduire un seuil que le
        produit refuse — et priver le groupeur d'une collecte qu'il a faite.
        """
        self._faire_passer_la_date()

        call_command("cloturer_les_groupages_echus", stdout=StringIO())

        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.statut, Campagne.Statut.EN_COURS)
        self.assertNotEqual(self.campagne.statut, Campagne.Statut.ANNULEE)

    def test_a_blanc_n_ecrit_rien(self):
        """Pouvoir regarder avant d'agir, sur une opération qui touche de
        l'argent et envoie des messages."""
        self._faire_passer_la_date()

        sortie = StringIO()
        call_command("cloturer_les_groupages_echus", "--a-blanc", stdout=sortie)

        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.statut, Campagne.Statut.OUVERTE)
        self.assertFalse(Retrait.objects.exists())
        self.assertEqual(Notification.objects.count(), 0)
        self.assertIn("à blanc", sortie.getvalue())

    def test_un_groupage_en_defaut_ne_retient_pas_les_autres(self):
        """Une transaction par groupage, et non une pour toutes.

        Si la vingtième échoue, les dix-neuf premières doivent rester
        clôturées : ce sont des opérations indépendantes, et une clôture a
        déjà envoyé ses notifications — les rejouer enverrait deux fois le
        même message.
        """
        autre = Campagne.objects.create(
            groupeur=_un_groupeur("+22890000021"),
            titre="Baskets homme, pointures 39-45",
            description="Baskets homme en toile, pointures 39 à 45.",
            contenu_part="1 paire",
            categorie=Campagne.Categorie.CHAUSSURES,
            prix_part=Decimal("9800"),
            objectif_participants=20,
            date_fin=timezone.now() + timedelta(days=2),
        )
        Campagne.objects.filter(pk__in=[self.campagne.pk, autre.pk]).update(
            date_fin=timezone.now() - timedelta(hours=1)
        )

        call_command(
            "cloturer_les_groupages_echus", stdout=StringIO(), stderr=StringIO()
        )

        self.assertEqual(Retrait.objects.count(), 2)
