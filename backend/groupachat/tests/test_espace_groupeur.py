# -*- coding: utf-8 -*-
"""L'espace de travail du groupeur — et ce qu'il ne doit jamais voir.

**La règle de ces routes tient en une phrase : un groupeur voit des codes et
des quartiers, jamais une personne.** C'est ce qui protège le modèle
contre la désintermédiation — un groupeur qui connaîtrait ses gros acheteurs
pourrait leur proposer la même marchandise hors plateforme, au même prix, et
sans nous.

Ces tests sont donc volontairement **méfiants** : ils ne vérifient pas que
l'API renvoie les bons champs, ils vérifient qu'elle n'en renvoie **aucun**
d'interdit — y compris ceux qui n'existent pas encore. Un ``fields = "__all__"``
ajouté par distraction les fait tomber, ce qui est exactement le but.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import enregistrer_paiement
from groupachat.comptes.models import Acheteur, Groupeur
from groupachat.echanges.models import Demande, Question


class SocleGroupeur(TestCase):
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

        # L'acheteuse du fil rouge (§3), avec son nom et son numéro.
        self.acheteuse = Acheteur.objects.create(
            telephone="+22890123456", nom="Akosua Doe"
        )
        enregistrer_paiement(
            campagne=self.campagne,
            acheteur=self.acheteuse,
            quantite=1,
            quartier="Tokoin",
            repere="En face de la pharmacie Sodji",
            telephone="+22890123456",
            cle_idempotence="cle-1",
        )

    def numero(self) -> dict:
        return {"telephone": "+22891000001"}


class AnonymatDesAcheteurs(SocleGroupeur):
    """⚠️ **Les tests les plus importants de ce fichier.**"""

    #: Ce qui ne doit apparaître dans **aucune** réponse de l'espace groupeur.
    #:
    #: Le repère en fait partie : « en face de la pharmacie Sodji » localise
    #: quelqu'un aussi sûrement qu'une adresse, et c'est précisément ce qu'un
    #: quartier seul ne fait pas.
    INTERDITS = (
        "Akosua Doe",
        "+22890123456",
        "90123456",
        "pharmacie Sodji",
    )

    def verifier_aucune_fuite(self, corps: str, ou: str) -> None:
        for interdit in self.INTERDITS:
            self.assertNotIn(interdit, corps, f"{ou} laisse fuir « {interdit} »")

    def test_le_tableau_de_bord_ne_laisse_fuir_aucun_acheteur(self) -> None:
        reponse = self.client.get(
            "/api/espace-groupeur/tableau-de-bord/", self.numero()
        )
        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.verifier_aucune_fuite(str(reponse.data), "le tableau de bord")

    def test_la_liste_des_campagnes_ne_laisse_fuir_aucun_acheteur(self) -> None:
        reponse = self.client.get("/api/espace-groupeur/campagnes/", self.numero())
        self.assertEqual(reponse.status_code, 200)
        self.verifier_aucune_fuite(str(reponse.data), "la liste des campagnes")

    def test_les_commandes_ne_portent_qu_un_code_et_un_quartier(self) -> None:
        """La route existante, re-vérifiée depuis ce fichier.

        Elle est servie par ``api.py`` mais **consommée ici** : c'est l'écran
        15 du groupeur. Un test qui la protège doit se trouver là où on vient
        chercher les règles de ce public.
        """
        reponse = self.client.get(f"/api/campagnes/{self.campagne.pk}/commandes/")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 1)

        ligne = reponse.data[0]
        self.assertEqual(
            set(ligne),
            {"code_livraison", "quantite", "variante", "montant_parts", "quartier"},
        )
        self.verifier_aucune_fuite(str(reponse.data), "les commandes")

    def test_les_demandes_sont_agregees_jamais_nominatives(self) -> None:
        """**Agrégé, et jamais ligne par ligne.**

        Une demande individuelle porte celui qui l'a déposée. La servir au
        groupeur lui donnerait exactement le fichier de clients que l'anonymat
        lui refuse partout ailleurs. Il voit « 2 personnes à Agoè veulent du
        riz » — de quoi décider, rien pour contacter.
        """
        for numero in ("+22890111111", "+22890222222"):
            acheteur = Acheteur.objects.create(telephone=numero, nom="Yawa Tete")
            Demande.objects.create(
                acheteur=acheteur,
                produit="Riz parfumé 25 kg",
                quantite="1 sac",
                quartier="Agoe",
                budget_maximum=Decimal("14000"),
            )

        reponse = self.client.get("/api/espace-groupeur/demandes/", self.numero())
        self.assertEqual(reponse.status_code, 200)

        ligne = next(l for l in reponse.data if l["produit"] == "Riz parfumé 25 kg")
        self.assertEqual(ligne["personnes"], 2)
        self.assertEqual(ligne["quartier"], "Agoe")
        self.assertEqual(ligne["budget_moyen"], 14000)

        corps = str(reponse.data)
        self.assertNotIn("Yawa Tete", corps)
        self.assertNotIn("+22890111111", corps)

    def test_les_questions_ne_montrent_que_le_prenom_et_l_initiale(self) -> None:
        """« Akosua D. », jamais « Akosua Doe » (§1.7)."""
        Question.objects.create(
            campagne=self.campagne,
            auteur=self.acheteuse,
            texte="C'est quelle marque ?",
        )
        reponse = self.client.get("/api/espace-groupeur/questions/", self.numero())
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data[0]["auteur"], "Akosua D.")
        self.assertNotIn("Akosua Doe", str(reponse.data))


class TableauDeBord(SocleGroupeur):
    def test_en_collecte_et_disponible_ne_se_confondent_pas(self) -> None:
        """**La distinction la plus importante de cet écran.**

        *En collecte* est l'argent de ses acheteurs sur des groupages encore
        ouverts : il lui appartient déjà, mais il est **détenu jusqu'à la
        clôture**, donc pas retirable. *Disponible* est ce qu'il peut prendre
        tout de suite.

        Les confondre donnerait un chiffre flatteur et faux, et le premier
        retrait refusé détruirait la crédibilité du tableau de bord.
        """
        reponse = self.client.get(
            "/api/espace-groupeur/tableau-de-bord/", self.numero()
        )
        self.assertEqual(reponse.data["en_collecte"], 4000)
        self.assertEqual(reponse.data["disponible"], 0)

    def test_apres_cloture_l_argent_passe_de_collecte_a_disponible(self) -> None:
        """Et les 1 500 F de frais sont arrêtés au passage, sur les parts seules.

        ⚠️ Ce groupage n'a qu'**une part de 4 000 F**, donc les frais y pèsent
        lourd : 4 000 − 1 500 = 2 500. C'est voulu et c'est le cas limite du
        §9.2 — un groupage minuscule coûte en vérification ce qu'un gros coûte.
        """
        self.client.post(
            f"/api/espace-groupeur/{self.campagne.pk}/cloturer/",
            self.numero(),
            format="json",
        )
        reponse = self.client.get(
            "/api/espace-groupeur/tableau-de-bord/", self.numero()
        )
        self.assertEqual(reponse.data["en_collecte"], 0)
        # 4 000 − 1 500 = 2 500.
        self.assertEqual(reponse.data["disponible"], 2500)

    def test_les_taches_disent_quoi_faire_pas_ce_qui_s_est_passe(self) -> None:
        """Un tableau de bord qui raconte le passé se lit une fois."""
        Question.objects.create(
            campagne=self.campagne, auteur=self.acheteuse, texte="Quelle couleur ?"
        )
        reponse = self.client.get(
            "/api/espace-groupeur/tableau-de-bord/", self.numero()
        )
        destinations = [t["destination"] for t in reponse.data["taches"]]
        self.assertIn("questions", destinations)


class CreationDeCampagne(SocleGroupeur):
    def corps(self, **remplacements) -> dict:
        donnees = {
            "telephone": "+22891000001",
            "titre": "Riz parfumé, sac de 25 kg",
            "description": "Riz long grain, sac scellé.",
            "contenu_part": "1 sac de 25 kg",
            "categorie": "alimentaire",
            "prix_part": "13500",
            # ⚠️ **Obligatoire** : c'est le dénominateur de la barre de
            # progression des cartes (§2.5), et sans lui la barre n'a rien à
            # remplir. Un test ci-dessous vérifie que l'API le réclame.
            "objectif_participants": 20,
            "quartier_remise": "Agoe",
            "point_remise": "Marché d'Agoè, entrée nord",
            "duree_heures": 72,
        }
        donnees.update(remplacements)
        return donnees

    def test_un_groupeur_valide_peut_lancer_un_groupage(self) -> None:
        reponse = self.client.post(
            "/api/espace-groupeur/campagnes/", self.corps(), format="json"
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(reponse.data["produit"], "Riz parfumé, sac de 25 kg")

    def test_un_dossier_non_valide_ne_lance_rien(self) -> None:
        """⚠️ **Le verrou du §10.5, vérifié depuis l'API.**

        Il vit dans ``Campagne.clean`` et non dans cette vue — un bouton grisé
        ne protège de rien, il suffit d'une requête directe. Ce test envoie
        précisément cette requête directe.
        """
        self.groupeur.statut_kyc = Groupeur.StatutKyc.EN_VERIFICATION
        self.groupeur.save()

        reponse = self.client.post(
            "/api/espace-groupeur/campagnes/", self.corps(), format="json"
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("KYC", str(reponse.data))

    def test_l_objectif_de_participants_est_obligatoire(self) -> None:
        """⚠️ **Sans objectif, pas de barre de progression** (§2.5).

        Le champ n'a **aucune valeur par défaut**, ni dans le modèle ni dans le
        sérialiseur, et c'est délibéré : un objectif posé d'office serait
        publié aux acheteurs sans que le groupeur l'ait choisi, et la barre
        afficherait un but qui n'est pas le sien.
        """
        corps = self.corps()
        del corps["objectif_participants"]

        reponse = self.client.post(
            "/api/espace-groupeur/campagnes/", corps, format="json"
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("objectif_participants", reponse.data)

    def test_un_objectif_a_zero_est_refuse(self) -> None:
        """Zéro personne n'est pas un objectif, c'est une division par zéro."""
        reponse = self.client.post(
            "/api/espace-groupeur/campagnes/",
            self.corps(objectif_participants=0),
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)

    def test_la_progression_part_avec_le_groupage(self) -> None:
        """La carte a besoin des deux chiffres, pas seulement du numérateur.

        Les faire calculer au client obligerait quatre écrans — le fil, la
        carte, la ligne et le détail — à refaire le même arrondi chacun à sa
        façon, et deux d'entre eux finiraient par ne plus dire la même chose.
        """
        reponse = self.client.get(
            "/api/espace-groupeur/campagnes/", self.numero()
        )
        premiere = reponse.data[0]
        self.assertEqual(premiere["objectif_participants"], 40)
        # Le socle pose **un** acheteur confirmé sur un objectif de 40.
        self.assertEqual(premiere["commandes"], 1)
        # ⚠️ 1 / 40 = 2,5 %, et l'arrondi est **vers le bas** : une barre ne
        # doit jamais surestimer. C'est aussi ce qui met le serveur et le client
        # d'accord — `round` de Python donnerait 2, le `Math.round` de
        # JavaScript 3, et les deux côtés afficheraient des chiffres
        # différents sur le même groupage.
        self.assertEqual(premiere["progression"], 2)

    def test_le_groupeur_ne_peut_pas_lancer_au_nom_d_un_autre(self) -> None:
        """``groupeur`` n'est pas un champ d'entrée, et ne doit pas le devenir.

        L'accepter depuis le client laisserait n'importe qui lancer une
        campagne au nom d'un autre — et donc encaisser sur sa réputation.
        """
        autre = Groupeur.objects.create(
            pseudonyme="Chez Sika",
            nom_complet="Sika Adjo",
            telephone="+22891000002",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            titulaire_mobile_money="Sika Adjo",
            numero_mobile_money="+22891000002",
        )
        reponse = self.client.post(
            "/api/espace-groupeur/campagnes/",
            self.corps(groupeur=autre.pk),
            format="json",
        )
        self.assertEqual(reponse.status_code, 201)
        self.assertEqual(
            Campagne.objects.get(titre="Riz parfumé, sac de 25 kg").groupeur,
            self.groupeur,
        )


class ReponseAuxQuestions(SocleGroupeur):
    def test_la_reponse_passe_par_le_filtre_de_moderation(self) -> None:
        """⚠️ **Le §15 filtre dans les deux sens.**

        Un groupeur qui glisse son numéro dans une réponse publique contourne
        la plateforme aussi sûrement qu'un acheteur qui le demande — et c'est
        même le cas le plus probable des deux, puisque c'est lui qui y gagne.
        """
        question = Question.objects.create(
            campagne=self.campagne, auteur=self.acheteuse, texte="C'est disponible ?"
        )
        reponse = self.client.post(
            f"/api/espace-groupeur/{question.pk}/repondre/",
            {"telephone": "+22891000001", "reponse": "Appelez-moi au 90 12 34 56"},
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)

        question.refresh_from_db()
        self.assertEqual(question.reponse, "")

    def test_une_reponse_ordinaire_passe(self) -> None:
        question = Question.objects.create(
            campagne=self.campagne, auteur=self.acheteuse, texte="C'est disponible ?"
        )
        reponse = self.client.post(
            f"/api/espace-groupeur/{question.pk}/repondre/",
            {
                "telephone": "+22891000001",
                "reponse": "Oui, il reste des parts jusqu'à la clôture.",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 200, reponse.data)
        question.refresh_from_db()
        self.assertNotEqual(question.reponse, "")

    def test_on_ne_repond_pas_sur_la_campagne_d_un_autre(self) -> None:
        autre = Groupeur.objects.create(
            pseudonyme="Chez Sika",
            nom_complet="Sika Adjo",
            telephone="+22891000002",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            titulaire_mobile_money="Sika Adjo",
            numero_mobile_money="+22891000002",
        )
        question = Question.objects.create(
            campagne=self.campagne, auteur=self.acheteuse, texte="Alors ?"
        )
        reponse = self.client.post(
            f"/api/espace-groupeur/{question.pk}/repondre/",
            {"telephone": autre.telephone, "reponse": "Oui bien sûr."},
            format="json",
        )
        self.assertEqual(reponse.status_code, 404)


class AccesParNumero(SocleGroupeur):
    def test_un_numero_inconnu_donne_404(self) -> None:
        reponse = self.client.get(
            "/api/espace-groupeur/tableau-de-bord/", {"telephone": "+22899999999"}
        )
        self.assertEqual(reponse.status_code, 404)

    def test_le_numero_est_normalise_comme_partout(self) -> None:
        """Les mêmes écritures qu'ailleurs mènent au même groupeur."""
        for ecriture in ("91000001", "+22891000001", "00228 91 00 00 01"):
            with self.subTest(ecriture=ecriture):
                reponse = self.client.get(
                    "/api/espace-groupeur/tableau-de-bord/",
                    {"telephone": ecriture},
                )
                self.assertEqual(reponse.status_code, 200, ecriture)
                self.assertEqual(reponse.data["pseudonyme"], "Mama Gro")
