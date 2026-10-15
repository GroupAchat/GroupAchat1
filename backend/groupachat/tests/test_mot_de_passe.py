# -*- coding: utf-8 -*-
"""Le mot de passe acheteur — la seconde voie d'entrée.

Le compte acheteur n'est plus « un truc de code SMS » : il porte un mot de
passe, et un courriel facultatif. Mais **le code SMS n'a pas disparu**, et
c'est tout l'équilibre de ce fichier : les deux voies coexistent, la seconde
est verrouillable, la première jamais — c'est elle qui garantit qu'un mot de
passe oublié ne ferme pas un compte.

Les règles les plus coûteuses à perdre, et les tests qui les tiennent :

| Règle | Ce qu'on perd en la perdant | Test |
|---|---|---|
| Le mot de passe ne crée pas de compte | Un compte ouvert sur le numéro d'un autre | ``test_la_voie_du_mot_de_passe_ne_cree_jamais_de_compte`` |
| Cinq échecs, puis quinze minutes | Huit chiffres se devinent à la machine | ``test_cinq_echecs_verrouillent_la_voie`` |
| Le code SMS lève le verrou | Un acheteur enfermé dehors par un tiers | ``test_le_code_sms_leve_le_verrou`` |
| L'empreinte ne sort jamais de l'API | Une attaque hors ligne, sans verrou ni limite | ``test_l_empreinte_ne_sort_jamais`` |
| Changer exige l'ancien mot de passe | Un téléphone prêté cinq minutes = compte perdu | ``test_changer_exige_l_ancien_mot_de_passe`` |
"""

from __future__ import annotations

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.comptes.models import Acheteur
from groupachat.comptes.sessions import ECHECS_AVANT_VERROU
from groupachat.tests.aides import connecter

NUMERO = "+22890123456"
SECRET = "akosua-tokoin-2026"


class SocleMotDePasse(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def connecter_par_sms(self, telephone: str = NUMERO) -> str:
        return connecter(self.client, telephone, nom="Akosua Doe")

    def poser_un_mot_de_passe(self, clair: str = SECRET, **extra):
        return self.client.post(
            "/api/comptes/moi/mot-de-passe/",
            {"mot_de_passe": clair, **extra},
            format="json",
        )

    def entrer_par_mot_de_passe(self, clair: str, telephone: str = NUMERO):
        # Un client neuf : on vérifie bien une connexion, pas la session
        # déjà armée par `connecter`.
        return APIClient().post(
            "/api/comptes/session-mot-de-passe/",
            {"telephone": telephone, "mot_de_passe": clair},
            format="json",
        )


class ParQuelleVoie(SocleMotDePasse):
    """``preparer/`` — ce que l'écran doit afficher, sans envoyer de SMS."""

    def test_un_numero_inconnu_n_a_ni_compte_ni_mot_de_passe(self) -> None:
        reponse = self.client.post(
            "/api/comptes/preparer/", {"telephone": NUMERO}, format="json"
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(reponse.data["compte_existe"])
        self.assertFalse(reponse.data["a_un_mot_de_passe"])

    def test_elle_n_envoie_aucun_code(self) -> None:
        """C'est sa raison d'être.

        Sans cette route, l'écran devait envoyer un SMS **pour savoir quoi
        afficher** : un acheteur qui connaît son mot de passe recevait un code
        inutile. Le jour où un fournisseur sera branché, ce sera un SMS facturé
        à chaque ouverture de la feuille de connexion.
        """
        from groupachat.comptes.models import CodeConnexion

        self.client.post(
            "/api/comptes/preparer/", {"telephone": NUMERO}, format="json"
        )
        self.assertEqual(CodeConnexion.objects.count(), 0)

    def test_elle_annonce_le_mot_de_passe_quand_il_existe(self) -> None:
        self.connecter_par_sms()
        self.assertEqual(self.poser_un_mot_de_passe().status_code, 200)

        reponse = APIClient().post(
            "/api/comptes/preparer/", {"telephone": NUMERO}, format="json"
        )
        self.assertTrue(reponse.data["compte_existe"])
        self.assertTrue(reponse.data["a_un_mot_de_passe"])


class PoserLeMotDePasse(SocleMotDePasse):
    def test_il_faut_une_session(self) -> None:
        """401 et non 403 : l'écran doit rouvrir la feuille de connexion."""
        reponse = self.poser_un_mot_de_passe()
        self.assertEqual(reponse.status_code, 401)

    def test_la_premiere_definition_ne_demande_rien_de_plus(self) -> None:
        """La session a été ouverte par un code SMS : le numéro est prouvé."""
        self.connecter_par_sms()
        reponse = self.poser_un_mot_de_passe()

        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.data["a_un_mot_de_passe"])

        acheteur = Acheteur.objects.get(telephone=NUMERO)
        self.assertTrue(acheteur.mot_de_passe)
        # Haché, jamais en clair. C'est `make_password` qui le garantit, et
        # ce test est là pour le jour où quelqu'un « simplifierait ».
        self.assertNotIn(SECRET, acheteur.mot_de_passe)

    def test_l_empreinte_ne_sort_jamais(self) -> None:
        """Ni de ``moi/``, ni de la réponse de définition, ni d'une session.

        La publier offrirait de quoi l'attaquer **hors ligne**, sans limite
        d'essais ni verrou — c'est-à-dire en contournant exactement la
        protection que ce fichier met en place ailleurs.
        """
        self.connecter_par_sms()
        empreinte = self.poser_un_mot_de_passe().data
        profil = self.client.get("/api/comptes/moi/").data
        entree = self.entrer_par_mot_de_passe(SECRET).data

        for reponse in (empreinte, profil, entree.get("acheteur", {})):
            self.assertNotIn("mot_de_passe", reponse)
            self.assertIn("a_un_mot_de_passe", reponse)

    def test_trop_court_est_refuse(self) -> None:
        """Huit caractères, et c'est ``AUTH_PASSWORD_VALIDATORS`` qui le dit.

        La règle vit dans ``settings.py``, pas ici : ce test vérifie qu'elle
        est **appliquée**, pas sa valeur. Durcir la politique est une
        modification de la configuration, et ce test continuera de passer.
        """
        self.connecter_par_sms()
        reponse = self.poser_un_mot_de_passe("court")
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("mot_de_passe", reponse.data)

    def test_le_numero_ne_peut_pas_servir_de_mot_de_passe(self) -> None:
        """C'est la valeur que l'attaquant possède déjà : elle identifie le compte.

        Et c'est le premier choix de quelqu'un à qui on demande huit
        caractères. ``validate_password`` ne peut pas connaître cette règle,
        donc elle est écrite à la main.
        """
        self.connecter_par_sms()
        for propose in ("90123456", "+22890123456", "22890123456"):
            with self.subTest(propose=propose):
                reponse = self.poser_un_mot_de_passe(propose)
                self.assertEqual(reponse.status_code, 400, propose)

    def test_changer_exige_l_ancien_mot_de_passe(self) -> None:
        """La session suffirait techniquement. Elle ne suffit pas, et c'est voulu.

        Le jeton vit dans le ``localStorage`` et survit à la fermeture de
        l'onglet : « qui a l'appareil déverrouillé a le compte ». La différence
        est celle entre **voir** les commandes de quelqu'un et **lui prendre
        son compte définitivement** — sans l'ancien mot de passe, un téléphone
        prêté cinq minutes suffit à verrouiller le titulaire dehors pour de
        bon.
        """
        self.connecter_par_sms()
        self.poser_un_mot_de_passe()

        sans_ancien = self.poser_un_mot_de_passe("un-autre-secret-2026")
        self.assertEqual(sans_ancien.status_code, 400)
        self.assertIn("ancien_mot_de_passe", sans_ancien.data)

        # L'ancien est resté valable : le refus n'a rien changé.
        self.assertEqual(self.entrer_par_mot_de_passe(SECRET).status_code, 201)

        avec_ancien = self.poser_un_mot_de_passe(
            "un-autre-secret-2026", ancien_mot_de_passe=SECRET
        )
        self.assertEqual(avec_ancien.status_code, 200)
        self.assertEqual(
            self.entrer_par_mot_de_passe("un-autre-secret-2026").status_code, 201
        )

    def test_un_ancien_mot_de_passe_faux_ne_change_rien(self) -> None:
        self.connecter_par_sms()
        self.poser_un_mot_de_passe()

        reponse = self.poser_un_mot_de_passe(
            "un-autre-secret-2026", ancien_mot_de_passe="pas-le-bon-du-tout"
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(self.entrer_par_mot_de_passe(SECRET).status_code, 201)


class EntrerParMotDePasse(SocleMotDePasse):
    def test_le_jeton_delivre_ouvre_bien_le_compte(self) -> None:
        self.connecter_par_sms()
        self.poser_un_mot_de_passe()

        entree = self.entrer_par_mot_de_passe(SECRET)
        self.assertEqual(entree.status_code, 201)
        self.assertFalse(entree.data["compte_cree"])

        autre = APIClient()
        autre.credentials(HTTP_AUTHORIZATION=f"Jeton {entree.data['jeton']}")
        profil = autre.get("/api/comptes/moi/")
        self.assertEqual(profil.status_code, 200)
        self.assertEqual(profil.data["telephone"], NUMERO)

    def test_la_voie_du_mot_de_passe_ne_cree_jamais_de_compte(self) -> None:
        """La différence de fond avec ``session/``, et elle n'est pas négociable.

        Un compte naît d'un numéro **prouvé** par un code SMS. Laisser un mot
        de passe le créer reviendrait à ouvrir un compte sur le numéro de
        quelqu'un d'autre, et à recevoir à sa place les notifications de
        livraison.
        """
        reponse = self.entrer_par_mot_de_passe(SECRET, telephone="+22899887766")
        self.assertEqual(reponse.status_code, 400)
        self.assertFalse(Acheteur.objects.filter(telephone="+22899887766").exists())

    def test_un_compte_sans_mot_de_passe_renvoie_vers_le_sms(self) -> None:
        """Et **pas** « mot de passe incorrect ».

        Les deux phrases n'envoient pas l'acheteur au même endroit : celle-ci
        vers le code SMS, l'autre vers une nouvelle tentative. Répondre
        « incorrect » à quelqu'un qui n'a jamais défini de mot de passe le
        laisse chercher un secret qui n'existe pas.
        """
        self.connecter_par_sms()  # compte créé, sans mot de passe
        reponse = self.entrer_par_mot_de_passe(SECRET)
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("SMS", str(reponse.data["mot_de_passe"]))

    def test_cinq_echecs_verrouillent_la_voie(self) -> None:
        """Sans quoi cette voie serait plus faible que celle qu'elle complète.

        ``CodeConnexion`` meurt au bout de trois essais. Un mot de passe sans
        limite se devine à la machine, et un numéro togolais tient en huit
        chiffres — l'attaquant n'a même pas besoin de connaître sa cible.
        """
        self.connecter_par_sms()
        self.poser_un_mot_de_passe()

        for essai in range(ECHECS_AVANT_VERROU):
            refus = self.entrer_par_mot_de_passe("mauvais-secret-%d" % essai)
            self.assertEqual(refus.status_code, 400)

        # ⚠️ Le **bon** mot de passe est refusé lui aussi : c'est bien un
        # verrou, pas un simple compteur de messages.
        verrouille = self.entrer_par_mot_de_passe(SECRET)
        self.assertEqual(verrouille.status_code, 400)

        acheteur = Acheteur.objects.get(telephone=NUMERO)
        self.assertIsNotNone(acheteur.bloque_jusqu_a)
        self.assertGreater(acheteur.bloque_jusqu_a, timezone.now())

    def test_le_code_sms_leve_le_verrou(self) -> None:
        """La voie de secours, et elle est structurante.

        Deux choses en dépendent. Un mot de passe oublié ou verrouillé ne ferme
        jamais un compte — il n'y a donc **aucun parcours « mot de passe
        oublié » à écrire**, ni lien à durée de vie, ni courriel que la moitié
        du public ne consulte pas. Et le verrou peut être sévère sans offrir à
        un tiers le moyen d'enfermer dehors l'acheteur de son choix, en se
        trompant exprès cinq fois sur un numéro qui n'est pas le sien.
        """
        self.connecter_par_sms()
        self.poser_un_mot_de_passe()
        for essai in range(ECHECS_AVANT_VERROU):
            self.entrer_par_mot_de_passe("mauvais-secret-%d" % essai)
        self.assertEqual(self.entrer_par_mot_de_passe(SECRET).status_code, 400)

        # Prouver qu'on a le téléphone vaut mieux que le mot de passe.
        self.connecter_par_sms()

        acheteur = Acheteur.objects.get(telephone=NUMERO)
        self.assertEqual(acheteur.echecs_connexion, 0)
        self.assertIsNone(acheteur.bloque_jusqu_a)
        self.assertEqual(self.entrer_par_mot_de_passe(SECRET).status_code, 201)

    def test_un_verrou_expire_rend_cinq_nouveaux_essais(self) -> None:
        """Un defaut trouve en relisant ma propre logique, pas en la testant.

        Le compteur restait a cinq apres la fin du blocage. La premiere faute
        de frappe suivante faisait donc six, et re-verrouillait aussitot pour
        un quart d'heure : quelqu'un ayant ete verrouille une fois n'avait plus
        jamais droit a *un seul* essai manque, pour toute la vie du compte.

        Et ``bloque_jusqu_a`` gardait une date passee, donc vraie au sens
        booleen — le test place apres l'incrementation la prenait pour un
        verrou neuf et annoncait un blocage que personne n'avait pose.
        """
        self.connecter_par_sms()
        self.poser_un_mot_de_passe()
        for essai in range(ECHECS_AVANT_VERROU):
            self.entrer_par_mot_de_passe("mauvais-secret-%d" % essai)

        # Le quart d'heure est passe.
        acheteur = Acheteur.objects.get(telephone=NUMERO)
        acheteur.bloque_jusqu_a = timezone.now() - timedelta(minutes=1)
        acheteur.save(update_fields=["bloque_jusqu_a"])

        refus = self.entrer_par_mot_de_passe("encore-faux-celui-la")
        self.assertEqual(refus.status_code, 400)
        self.assertNotIn("Trop d'essais", str(refus.data["mot_de_passe"]))
        self.assertIsNone(
            Acheteur.objects.get(telephone=NUMERO).bloque_jusqu_a
        )

        self.assertEqual(self.entrer_par_mot_de_passe(SECRET).status_code, 201)

    def test_une_reussite_remet_le_compteur_a_zero(self) -> None:
        """Les échecs comptés sont **consécutifs**.

        Sinon quatre fautes de frappe étalées sur six mois verrouilleraient
        quelqu'un qui connaît son mot de passe.
        """
        self.connecter_par_sms()
        self.poser_un_mot_de_passe()

        for essai in range(ECHECS_AVANT_VERROU - 1):
            self.entrer_par_mot_de_passe("mauvais-secret-%d" % essai)
        self.assertEqual(self.entrer_par_mot_de_passe(SECRET).status_code, 201)

        self.assertEqual(
            Acheteur.objects.get(telephone=NUMERO).echecs_connexion, 0
        )

        for essai in range(ECHECS_AVANT_VERROU - 1):
            self.entrer_par_mot_de_passe("mauvais-secret-%d" % essai)
        self.assertEqual(self.entrer_par_mot_de_passe(SECRET).status_code, 201)


class LeCourriel(SocleMotDePasse):
    """Facultatif, et jamais demandé pour commander."""

    def test_il_se_renseigne_depuis_le_profil(self) -> None:
        self.connecter_par_sms()
        self.assertEqual(self.client.get("/api/comptes/moi/").data["courriel"], "")

        reponse = self.client.patch(
            "/api/comptes/moi/profil/",
            {"courriel": "akosua@example.tg"},
            format="json",
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["courriel"], "akosua@example.tg")

    def test_il_n_identifie_pas_le_compte(self) -> None:
        """Deux comptes peuvent le partager — une famille, une boutique.

        Rien ne casse, précisément parce qu'on ne s'en sert jamais pour
        retrouver qui que ce soit : c'est le numéro qui identifie, et lui seul
        est ``unique``.
        """
        self.connecter_par_sms()
        self.client.patch(
            "/api/comptes/moi/profil/",
            {"courriel": "famille@example.tg"},
            format="json",
        )

        autre = APIClient()
        connecter(autre, "+22899887766", nom="Kofi Doe")
        reponse = autre.patch(
            "/api/comptes/moi/profil/",
            {"courriel": "famille@example.tg"},
            format="json",
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(
            Acheteur.objects.filter(courriel="famille@example.tg").count(), 2
        )
