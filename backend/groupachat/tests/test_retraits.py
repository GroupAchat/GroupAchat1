# -*- coding: utf-8 -*-
"""Le solde, le retrait, et les 1 500 F — §9 et §10 du cahier des charges.

L'argent de l'acheteur est inscrit au **portefeuille du groupeur** dès son
paiement. La plateforme ne verse plus rien : elle tient le compte, et elle
exécute les retraits qu'il demande.

**Trois moments, et ces tests protègent chacun d'eux :**

| Moment | Ce qui est vrai |
|---|---|
| Groupage ouvert | Le solde est à lui, mais **détenu jusqu'à la clôture** |
| Clôture maintenue | Il devient **retirable**, 1 500 F de frais arrêtés |
| Retrait | Il demande, **nous ne pouvons pas refuser**, nous exécutons |

⚠️ **Le test le plus contre-intuitif de ce fichier est
``test_sans_devis_le_retrait_part_quand_meme``**, et il est là exprès. Le devis
fournisseur bloquait le versement dans le modèle précédent ; il ne bloque plus
rien. Si quelqu'un rétablit ce verrou un jour sans toucher au cahier des
charges, c'est ce test qui le dira — et le §9.1 dit franchement ce que cette
perte de levier nous coûte.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import (
    Justificatif,
    PlafondAtteint,
    Retrait,
    cloturer_campagne,
    enregistrer_paiement,
)
from groupachat.comptes.models import Acheteur, Groupeur

#: Le jeton d'administration employé par ces tests.
#:
#: ⚠️ Posé par ``override_settings``, **et non dans ``os.environ``** : la
#: permission le lit dans ``settings.JETON_ADMIN``, qui est résolu une seule
#: fois au chargement des réglages. Écrire dans l'environnement après ce
#: moment-là n'a aucun effet — et le symptôme est un 403 incompréhensible,
#: avec une variable qui porte pourtant la bonne valeur.
JETON = "jeton-de-test"


@override_settings(JETON_ADMIN=JETON)
class SocleArgent(TestCase):
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
        # Le fil rouge du §3 : 32 commandes à 4 000 F.
        for numero in range(32):
            acheteur = Acheteur.objects.create(telephone=f"+2289010{numero:04d}")
            enregistrer_paiement(
                campagne=self.campagne,
                acheteur=acheteur,
                quantite=1,
                quartier="Tokoin",
                repere="Pharmacie Sodji",
                telephone=acheteur.telephone,
                cle_idempotence=f"fil-rouge-{numero}",
            )

    def entete(self) -> dict:
        return {"HTTP_X_JETON_ADMIN": JETON}

    def numero(self) -> dict:
        return {"telephone": "+22891000001"}


class LeMontantEstArreteALaCloture(SocleArgent):
    def test_les_chiffres_du_fil_rouge_tombent_juste(self) -> None:
        """128 000 collectés, 1 500 F de frais, 126 500 retirables.

        **Un jury vérifie ces chiffres d'un écran à l'autre.**
        """
        retrait = cloturer_campagne(self.campagne)

        self.assertEqual(retrait.collecte, Decimal("128000"))
        self.assertEqual(retrait.frais_plateforme, Decimal("1500"))
        self.assertEqual(retrait.net, Decimal("126500"))
        # 32 × 1 000 F de livraison, **jamais touchés par les frais** : ils
        # vont au transporteur, pas au groupeur.
        # Plus aucun frais de livraison collecte : seuls les 1 500 F
        # de la plateforme sont retenus.
        self.assertEqual(retrait.frais_livraison_collectes, Decimal("0"))

    def test_les_frais_ne_dependent_pas_du_montant_collecte(self) -> None:
        """⚠️ **C'est tout l'intérêt d'un montant fixe**, et c'est fragile.

        Quelqu'un qui remet un pourcentage « parce que c'était comme ça
        avant » ne casserait aucun autre test de ce fichier : les deux
        groupages ci-dessous n'ont pas la même collecte, et pourtant ils
        doivent porter exactement les mêmes frais.
        """
        petit = cloturer_campagne(self.campagne)

        gros = Campagne.objects.create(
            groupeur=self.groupeur,
            titre="Sacs de riz parfumé",
            description="Un lot.",
            contenu_part="Un sac",
            categorie=Campagne.Categorie.ALIMENTAIRE,
            prix_part=Decimal("14500"),
            objectif_participants=40,
            date_fin=timezone.now() + timedelta(days=2),
        )
        # Huit parts : 116 000 F, sous le plafond de 150 000 F du niveau
        # Entree (§10.4). Ce qui compte ici est que la collecte differe de
        # celle des ecouteurs, pas qu'elle soit grosse.
        for numero in range(8):
            acheteur = Acheteur.objects.create(telephone=f"+2289030{numero:04d}")
            enregistrer_paiement(
                campagne=gros,
                acheteur=acheteur,
                quantite=1,
                quartier="Tokoin",
                repere="Carrefour",
                telephone=acheteur.telephone,
                cle_idempotence=f"riz-{numero}",
            )
        gros_retrait = cloturer_campagne(gros)

        self.assertEqual(gros_retrait.collecte, Decimal("116000"))
        self.assertEqual(gros_retrait.frais_plateforme, Decimal("1500"))
        self.assertEqual(
            petit.frais_plateforme, gros_retrait.frais_plateforme
        )

    def test_le_retrait_est_retirable_des_la_cloture(self) -> None:
        """La clôture ouvre le retrait, elle ne fait partir aucun argent.

        Le groupeur **sait** ce qu'il touche, et il peut le prendre quand il
        veut. Rien n'est encore sorti de la plateforme.
        """
        retrait = cloturer_campagne(self.campagne)
        self.assertEqual(retrait.etat, Retrait.Etat.RETIRABLE)
        self.assertTrue(retrait.retirable)
        self.assertFalse(retrait.executable)
        self.assertIsNone(retrait.demande_le)
        self.assertIsNone(retrait.libere_le)


class LeRetraitDuGroupeur(SocleArgent):
    """Écran 18 — le bouton « Retirer mes fonds », et ce qu'il déclenche."""

    def test_rien_a_retirer_tant_que_le_groupage_est_ouvert(self) -> None:
        """⚠️ **La règle qui rend le remboursement possible.**

        Le solde est à lui dès le paiement de ses acheteurs, mais il est
        **détenu jusqu'à la clôture**. S'il pouvait retirer avant, un groupage
        annulé n'aurait plus rien à rendre aux acheteurs.
        """
        reponse = self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        self.assertEqual(reponse.status_code, 400)

    def test_il_retire_et_les_1_500_F_sont_annonces(self) -> None:
        """La confirmation de l'écran 18 a besoin des deux chiffres."""
        cloturer_campagne(self.campagne)
        reponse = self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertEqual(reponse.data["groupages"], 1)
        self.assertEqual(reponse.data["frais_plateforme"], 1500)
        self.assertEqual(reponse.data["montant"], 126500)

        retrait = Retrait.objects.get(campagne=self.campagne)
        self.assertEqual(retrait.etat, Retrait.Etat.DEMANDE)
        self.assertIsNotNone(retrait.demande_le)
        # ⚠️ L'argent n'est pas encore parti : c'est un ordre, pas un virement.
        self.assertIsNone(retrait.libere_le)

    def test_un_second_retrait_ne_trouve_plus_rien(self) -> None:
        """Un double appui ne doit pas demander deux fois le même argent."""
        cloturer_campagne(self.campagne)
        premier = self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        second = self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        self.assertEqual(premier.status_code, 200)
        self.assertEqual(second.status_code, 400)

    def test_le_portefeuille_distingue_le_retirable_du_retire(self) -> None:
        """Deux chiffres, et les confondre ferait croire à un double paiement."""
        retrait = cloturer_campagne(self.campagne)

        avant = self.client.get(
            "/api/espace-groupeur/portefeuille/", self.numero()
        )
        self.assertEqual(avant.data["disponible"], 126500)
        self.assertEqual(avant.data["retire"], 0)

        self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        self.client.post(
            f"/api/administration/{retrait.pk}/executer/",
            {"decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )

        apres = self.client.get(
            "/api/espace-groupeur/portefeuille/", self.numero()
        )
        self.assertEqual(apres.data["disponible"], 0)
        self.assertEqual(apres.data["retire"], 126500)


class LeDevisNeBloquePlusRien(SocleArgent):
    def test_sans_devis_le_retrait_part_quand_meme(self) -> None:
        """⚠️ **Le test le plus important de ce fichier**, et il dit une perte.

        Dans le modèle précédent, l'absence de devis fournisseur interdisait de
        libérer l'argent, et c'était le dernier contrôle du dispositif. Le
        portefeuille du groupeur l'a supprimé : son solde est à lui, et le lui
        refuser serait indéfendable.

        **Ce test existe pour que ce choix reste visible.** S'il casse un jour,
        c'est que quelqu'un a rétabli le verrou — ce qui demande de rouvrir le
        §9.1 et le §10.2 du cahier des charges, pas seulement ce fichier.
        """
        retrait = cloturer_campagne(self.campagne)
        self.assertIsNone(retrait.devis)

        self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        reponse = self.client.post(
            f"/api/administration/{retrait.pk}/executer/",
            {"decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )
        self.assertEqual(reponse.status_code, 200, reponse.data)

        retrait.refresh_from_db()
        self.assertEqual(retrait.etat, Retrait.Etat.EFFECTUE)

    def test_le_devis_est_enregistre_et_consultable(self) -> None:
        """Il constate : on sait chez qui il achète, et pour combien."""
        cloturer_campagne(self.campagne)
        reponse = self.client.post(
            f"/api/espace-groupeur/{self.campagne.pk}/justificatif/",
            {
                **self.numero(),
                "nature": "devis",
                "fournisseur": "Importateur Lomé Électronique",
                "montant": "95000",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)

        retrait = Retrait.objects.get(campagne=self.campagne)
        self.assertEqual(
            retrait.devis.fournisseur, "Importateur Lomé Électronique"
        )

    def test_on_n_execute_pas_un_retrait_qu_il_n_a_pas_demande(self) -> None:
        """⚠️ **Le seul contrôle qui reste de notre côté.**

        Exécuter un retrait qu'il n'a pas déclenché reviendrait à sortir son
        argent de la plateforme à sa place.
        """
        retrait = cloturer_campagne(self.campagne)
        reponse = self.client.post(
            f"/api/administration/{retrait.pk}/executer/",
            {"decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )
        self.assertEqual(reponse.status_code, 400)

        retrait.refresh_from_db()
        self.assertEqual(retrait.etat, Retrait.Etat.RETIRABLE)

    def test_l_execution_est_tracee(self) -> None:
        """⚠️ **Toute action sur l'argent est tracée et motivée** (§18.3).

        Qui, quand, sur quel groupage. C'est la contrepartie du fait qu'un
        jeton partagé ne distingue pas deux administrateurs : si on ne sait pas
        *qui* au sens fort, on sait au moins ce qui a été fait et sous quel nom.
        """
        retrait = cloturer_campagne(self.campagne)
        self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        self.client.post(
            f"/api/administration/{retrait.pk}/executer/",
            {"decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )

        retrait.refresh_from_db()
        self.assertEqual(retrait.etat, Retrait.Etat.EFFECTUE)
        self.assertEqual(retrait.libere_par, "Kephira")
        self.assertIsNotNone(retrait.libere_le)

    def test_on_n_execute_pas_deux_fois(self) -> None:
        """Un double appui ne doit pas envoyer l'argent deux fois."""
        retrait = cloturer_campagne(self.campagne)
        self.client.post(
            "/api/espace-groupeur/retirer/", self.numero(), format="json"
        )
        premiere = self.client.post(
            f"/api/administration/{retrait.pk}/executer/",
            {"decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )
        seconde = self.client.post(
            f"/api/administration/{retrait.pk}/executer/",
            {"decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )
        self.assertEqual(premiere.status_code, 200)
        self.assertEqual(seconde.status_code, 400)

    def test_redeposer_un_devis_remplace_le_precedent(self) -> None:
        """Sinon l'administrateur examine une pile et ne sait plus lequel vaut."""
        cloturer_campagne(self.campagne)
        for fournisseur in ("Premier", "Second"):
            self.client.post(
                f"/api/espace-groupeur/{self.campagne.pk}/justificatif/",
                {
                    **self.numero(),
                    "nature": "devis",
                    "fournisseur": fournisseur,
                    "montant": "1000",
                },
                format="json",
            )

        devis = Justificatif.objects.filter(
            campagne=self.campagne, nature=Justificatif.Nature.DEVIS
        )
        self.assertEqual(devis.count(), 1)
        self.assertEqual(devis.get().fournisseur, "Second")

    def test_le_devis_d_un_autre_groupeur_est_refuse(self) -> None:
        autre = Groupeur.objects.create(
            pseudonyme="Chez Sika",
            nom_complet="Sika Adjo",
            telephone="+22891000002",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            titulaire_mobile_money="Sika Adjo",
            numero_mobile_money="+22891000002",
        )
        reponse = self.client.post(
            f"/api/espace-groupeur/{self.campagne.pk}/justificatif/",
            {
                "telephone": autre.telephone,
                "nature": "devis",
                "fournisseur": "X",
                "montant": "1",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 404)


class UnGroupageAnnule(SocleArgent):
    def test_aucun_frais_sur_un_groupage_annule(self) -> None:
        """§7 — et le retrait qui attendait est annulé avec lui.

        Un groupage qui n'aboutit pas ne rapporte rien à personne. C'est ce qui
        rend « vous êtes livré, ou remboursé » tenable.
        """
        cloturer_campagne(self.campagne)
        reponse = self.client.post(
            f"/api/espace-groupeur/{self.campagne.pk}/annuler/",
            self.numero(),
            format="json",
        )
        self.assertEqual(reponse.status_code, 200, reponse.data)

        retrait = Retrait.objects.get(campagne=self.campagne)
        self.assertEqual(retrait.etat, Retrait.Etat.ANNULE)
        self.assertIsNone(retrait.libere_le)

    def test_les_acheteurs_sont_rembourses(self) -> None:
        cloturer_campagne(self.campagne)
        self.client.post(
            f"/api/espace-groupeur/{self.campagne.pk}/annuler/",
            self.numero(),
            format="json",
        )
        self.assertEqual(
            self.campagne.commandes.filter(statut="remboursee").count(), 32
        )


class LeTableauDeBordAdmin(SocleArgent):
    def test_il_est_ferme_sans_jeton(self) -> None:
        """Il porte les montants détenus et les noms des groupeurs."""
        reponse = self.client.get("/api/administration/tableau-de-bord/")
        self.assertEqual(reponse.status_code, 403)

    def test_les_files_mettent_l_argent_en_tete(self) -> None:
        """**Du plus coûteux au moins coûteux.**

        Un dossier KYC qui traîne coûte un groupeur. Un retrait qui traîne
        coûte une livraison et la confiance de dizaines d'acheteurs.
        """
        reponse = self.client.get(
            "/api/administration/tableau-de-bord/", **self.entete()
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["files"][0]["id"], "retraits")
        self.assertTrue(reponse.data["files"][0]["argent_expose"])

    def test_l_argent_detenu_est_le_premier_indicateur(self) -> None:
        """C'est le seul chiffre de l'écran qui engage la structure."""
        reponse = self.client.get(
            "/api/administration/tableau-de-bord/", **self.entete()
        )
        indicateurs = reponse.data["indicateurs"]
        self.assertEqual(indicateurs[0]["id"], "detenu")
        self.assertEqual(indicateurs[0]["valeur"], 128000)

    def test_le_nombre_d_inscrits_n_y_est_pas(self) -> None:
        """C'est la mesure qui flatte et n'engage à rien.

        Ce qui compte est le nombre de groupages allés jusqu'à la livraison.
        """
        reponse = self.client.get(
            "/api/administration/tableau-de-bord/", **self.entete()
        )
        identifiants = [i["id"] for i in reponse.data["indicateurs"]]
        self.assertNotIn("inscrits", identifiants)
        self.assertIn("aboutissement", identifiants)

    def test_la_courbe_couvre_quatorze_jours(self) -> None:
        """Y compris les jours sans vente — sinon la courbe ment sur le rythme."""
        reponse = self.client.get(
            "/api/administration/tableau-de-bord/", **self.entete()
        )
        serie = reponse.data["serie_collecte"]
        self.assertEqual(len(serie), 14)
        self.assertEqual(sum(point["montant"] for point in serie), 128000)

    def test_on_filtre_les_groupages_par_etat(self) -> None:
        """Clôturés, annulés, non aboutis : trois choses différentes."""
        cloturer_campagne(self.campagne)
        reponse = self.client.get(
            "/api/administration/groupages/",
            {"statut": "en-cours"},
            **self.entete(),
        )
        self.assertEqual(len(reponse.data), 1)
        self.assertEqual(reponse.data[0]["retrait_etat"], "retirable")

    def test_la_file_des_retraits_part_du_plus_ancien(self) -> None:
        """Un groupeur qui attend ne peut pas acheter ce qu'il a vendu."""
        cloturer_campagne(self.campagne)
        reponse = self.client.get(
            "/api/administration/retraits/", **self.entete()
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 1)
        self.assertEqual(reponse.data[0]["groupeur"], "Mama Gro")
        # L'administration voit le vrai nom : on ne vire pas à un pseudonyme.
        self.assertEqual(reponse.data[0]["groupeur_nom"], "Akossiwa Mensah")


class LePlafondDeCollecte(TestCase):
    """§10.4 — il borne le montant maximal d'un sinistre.

    ⚠️ **Il se contrôle au paiement, pas à la création de la campagne.** Il
    l'était, et ça produisait deux défauts opposés : à la création la collecte
    vaut zéro, donc le contrôle passait toujours — et comme `clean` s'exécute
    à chaque écriture, clôturer une campagne qui avait bien marché échouait
    avec « dépasserait le plafond », un message sans aucun sens à ce moment-là.
    """

    def setUp(self) -> None:
        self.groupeur = Groupeur.objects.create(
            pseudonyme="Nouveau",
            nom_complet="Afi Kossi",
            telephone="+22891000009",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            # Niveau Entrée : 150 000 F par groupage.
            niveau=Groupeur.Niveau.ENTREE,
            titulaire_mobile_money="Afi Kossi",
            numero_mobile_money="+22891000009",
        )
        self.campagne = Campagne.objects.create(
            groupeur=self.groupeur,
            titre="Sacs de riz",
            description="Un lot.",
            contenu_part="Un sac",
            categorie=Campagne.Categorie.ALIMENTAIRE,
            prix_part=Decimal("50000"),
            objectif_participants=40,
            date_fin=timezone.now() + timedelta(days=3),
        )

    def payer(self, numero: int):
        acheteur = Acheteur.objects.create(telephone=f"+2289020{numero:04d}")
        return enregistrer_paiement(
            campagne=self.campagne,
            acheteur=acheteur,
            quantite=1,
            quartier="Tokoin",
            repere="Pharmacie Sodji",
            telephone=acheteur.telephone,
            cle_idempotence=f"plafond-{numero}",
        )

    def test_le_paiement_qui_ferait_depasser_est_refuse(self) -> None:
        """Trois parts à 50 000 F passent, la quatrième non."""
        for numero in range(3):
            self.payer(numero)
        self.assertEqual(self.campagne.collecte_sur_les_parts, Decimal("150000"))

        with self.assertRaises(PlafondAtteint):
            self.payer(3)

        self.assertEqual(self.campagne.commandes.count(), 3)

    def test_le_message_parle_a_l_acheteur_pas_de_nos_regles(self) -> None:
        """Il n'a rien fait de mal et n'a pas à comprendre nos plafonds.

        « Ce groupage est complet » est vrai de son point de vue ; « le
        groupeur a atteint son plafond de collecte » l'inquiéterait sur le
        groupeur pour une raison qui ne le regarde pas.
        """
        for numero in range(3):
            self.payer(numero)
        with self.assertRaises(PlafondAtteint) as leve:
            self.payer(3)

        message = str(leve.exception)
        self.assertIn("complet", message.lower())
        self.assertNotIn("plafond", message.lower())
        self.assertNotIn("groupeur", message.lower())

    def test_une_campagne_qui_a_bien_marche_reste_cloturable(self) -> None:
        """⚠️ **Le défaut qui a révélé le problème.**

        La campagne a collecté jusqu'à son plafond. Clôturer écrit sur la
        ligne — et échouait, parce que `clean` revérifiait le plafond à chaque
        écriture.
        """
        for numero in range(3):
            self.payer(numero)
        retrait = cloturer_campagne(self.campagne)
        self.assertEqual(retrait.collecte, Decimal("150000"))

    def test_au_niveau_etabli_il_n_y_a_pas_de_plafond(self) -> None:
        """« Au cas par cas » (§10.4) : `None`, et on n'invente pas un chiffre."""
        self.groupeur.niveau = Groupeur.Niveau.ETABLI
        self.groupeur.save()
        for numero in range(5):
            self.payer(numero)
        self.assertEqual(self.campagne.commandes.count(), 5)
