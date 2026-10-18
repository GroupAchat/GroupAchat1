# -*- coding: utf-8 -*-
"""La connexion à l'administration.

Ces tests couvrent ce que le jeton partagé ne savait pas faire. Il valait
pourtant mieux que rien — il fermait des routes que le ``AllowAny`` du §1.5
aurait laissées ouvertes — mais sa propre documentation l'admettait : *« ce
n'est pas de l'authentification, et il ne faut pas le prendre pour telle »*.

Ce qui est vérifié ici, et pourquoi chacun compte :

| | Ce que ça protège |
|---|---|
| Un mot de passe est exigé | l'accès ne tient plus à une chaîne recopiée dans un ``.env`` |
| ``is_staff`` est exigé, et **revérifié** | on révoque une personne sans changer le secret des autres |
| Le message d'erreur est unique | il ne dit pas quels identifiants existent |
| Cinq essais, puis quinze minutes | l'essai systématique devient inutile |
| ``décidé par`` vient du compte | le journal d'une décision KYC prouve quelque chose |

Le dernier est le plus important, et ce n'est pas de la sécurité pour la
sécurité : le §10.5 confie la validation d'un dossier à un humain parce que, le
jour d'un litige, **ce dossier est notre seul recours contre le groupeur**.
"""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.comptes import sessions_admin
from groupachat.comptes.models import SessionAdmin, VerrouAdmin

MOT_DE_PASSE = "mot-de-passe-de-test"


class SocleConnexion(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.compte = get_user_model().objects.create_user(
            username="ama",
            password=MOT_DE_PASSE,
            first_name="Ama",
            last_name="Koffi",
            is_staff=True,
        )

    def connexion(self, identifiant="ama", mot_de_passe=MOT_DE_PASSE):
        return self.client.post(
            "/api/session-admin/connexion/",
            {"identifiant": identifiant, "mot_de_passe": mot_de_passe},
            format="json",
        )


class LaConnexion(SocleConnexion):
    def test_un_compte_valide_recoit_un_jeton(self) -> None:
        reponse = self.connexion()
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertTrue(reponse.data["jeton"])
        # Le nom complet plutôt que l'identifiant : ce champ part dans le
        # journal des décisions, et « Ama Koffi » se relit mieux que « ama ».
        self.assertEqual(reponse.data["nom"], "Ama Koffi")

    def test_le_jeton_ne_se_devine_pas(self) -> None:
        """``token_urlsafe(32)`` — 256 bits tirés par ``secrets``.

        Ce n'est pas de la coquetterie : c'est ce qui distingue ce jeton du
        secret partagé qu'il remplace, lequel était choisi à la main par celui
        qui remplissait le ``.env``.
        """
        jeton = self.connexion().data["jeton"]
        self.assertGreaterEqual(len(jeton), 40)

    def test_le_jeton_ouvre_les_dossiers_kyc(self) -> None:
        jeton = self.connexion().data["jeton"]
        reponse = self.client.get(
            "/api/dossiers/", **{"HTTP_X_JETON_ADMIN": jeton}
        )
        self.assertEqual(reponse.status_code, 200)

    def test_un_mot_de_passe_faux_est_refuse(self) -> None:
        self.assertEqual(self.connexion(mot_de_passe="faux").status_code, 401)

    def test_un_identifiant_inconnu_est_refuse(self) -> None:
        self.assertEqual(self.connexion(identifiant="kofi").status_code, 401)

    def test_les_deux_refus_disent_exactement_la_meme_chose(self) -> None:
        """⚠️ **Le test le moins spectaculaire et l'un des plus utiles.**

        Distinguer « cet identifiant n'existe pas » de « mauvais mot de passe »
        dirait à qui essaie **quels identifiants existent**, et lui permettrait
        de n'attaquer que ceux-là. C'est la différence entre deviner deux
        secrets et n'en deviner qu'un.
        """
        inconnu = self.connexion(identifiant="kofi")
        faux = self.connexion(mot_de_passe="faux")
        self.assertEqual(
            str(inconnu.data["detail"]), str(faux.data["detail"])
        )

    def test_un_compte_sans_is_staff_ne_passe_pas(self) -> None:
        """Et il est refusé **avec le même message** que les deux autres.

        Un compte qui existe, dont le mot de passe est juste, mais qui n'est
        pas administrateur : lui répondre autre chose confirmerait à la fois
        l'identifiant et le mot de passe.
        """
        self.compte.is_staff = False
        self.compte.save(update_fields=["is_staff"])
        reponse = self.connexion()
        self.assertEqual(reponse.status_code, 401)
        self.assertIn("incorrect", str(reponse.data["detail"]).lower())

    def test_un_compte_desactive_ne_passe_pas(self) -> None:
        self.compte.is_active = False
        self.compte.save(update_fields=["is_active"])
        self.assertEqual(self.connexion().status_code, 401)

    def test_le_mot_de_passe_n_est_pas_ampute_de_ses_espaces(self) -> None:
        """⚠️ DRF coupe les espaces de bord d'un ``CharField`` par défaut.

        C'est juste pour un identifiant et faux pour un secret : un mot de
        passe qui se termine par une espace est un mot de passe valide, et le
        couper rendrait la connexion impossible sans rien expliquer. D'où
        ``trim_whitespace=False``.
        """
        self.compte.set_password("avec une espace ")
        self.compte.save()
        self.assertEqual(
            self.connexion(mot_de_passe="avec une espace ").status_code, 201
        )
        # Et la version coupée ne doit pas passer, sinon le test précédent
        # réussirait même avec le défaut de DRF.
        self.assertEqual(
            self.connexion(mot_de_passe="avec une espace").status_code, 401
        )

    def test_l_identifiant_tolere_une_espace_collee(self) -> None:
        """L'inverse pour l'identifiant : on ne refuse personne pour un
        copier-coller. Ce n'est pas un secret, le couper ne perd rien."""
        self.assertEqual(self.connexion(identifiant=" ama ").status_code, 201)


class LeVerrou(SocleConnexion):
    def test_cinq_echecs_puis_le_verrou(self) -> None:
        for _ in range(4):
            self.assertEqual(self.connexion(mot_de_passe="faux").status_code, 401)
        # Le cinquième pose le verrou.
        self.assertEqual(self.connexion(mot_de_passe="faux").status_code, 429)
        # Et le bon mot de passe ne passe plus : sinon le verrou ne servirait
        # à rien, puisque c'est précisément le mot de passe qu'on cherche.
        self.assertEqual(self.connexion().status_code, 429)

    def test_le_verrou_expire_et_le_compteur_repart_de_zero(self) -> None:
        """⚠️ **Le défaut que j'ai introduit puis corrigé côté acheteur.**

        Un compteur laissé à son maximum fait que la première faute de frappe
        après l'expiration du verrou le repose aussitôt, pour un quart d'heure,
        indéfiniment. Le verrou est la sanction des cinq échecs ; une fois
        purgé, on repart de zéro.
        """
        for _ in range(5):
            self.connexion(mot_de_passe="faux")

        verrou = VerrouAdmin.objects.get(identifiant="ama")
        verrou.bloque_jusqu_a = timezone.now() - timedelta(seconds=1)
        verrou.save(update_fields=["bloque_jusqu_a"])

        # Une faute de frappe de plus doit redonner 401, pas 429.
        self.assertEqual(self.connexion(mot_de_passe="faux").status_code, 401)
        self.assertEqual(self.connexion().status_code, 201)

    def test_un_identifiant_inconnu_est_verrouille_aussi(self) -> None:
        """⚠️ **Le verrou porte sur l'identifiant saisi, pas sur le compte.**

        Compter les échecs sur le compte trouvé ne protégerait que les comptes
        qui existent : un identifiant inconnu n'aurait aucune limite, et
        l'écart de comportement entre « inconnu, essaie encore » et « connu,
        verrouillé » révélerait quels identifiants existent — exactement ce que
        le message d'erreur unique vient de masquer.
        """
        for _ in range(4):
            self.assertEqual(self.connexion(identifiant="kofi").status_code, 401)
        self.assertEqual(self.connexion(identifiant="kofi").status_code, 429)

    def test_une_connexion_reussie_efface_les_echecs(self) -> None:
        """Sinon quatre fautes de frappe étalées sur un mois finiraient par
        verrouiller quelqu'un qui n'a jamais échoué deux fois de suite."""
        for _ in range(4):
            self.connexion(mot_de_passe="faux")
        self.assertEqual(self.connexion().status_code, 201)
        self.assertEqual(VerrouAdmin.objects.get(identifiant="ama").echecs, 0)


class LaSessionOuverte(SocleConnexion):
    def setUp(self) -> None:
        super().setUp()
        self.jeton = self.connexion().data["jeton"]

    def entete(self) -> dict:
        return {"HTTP_X_JETON_ADMIN": self.jeton}

    def test_moi_dit_qui_est_connecte(self) -> None:
        reponse = self.client.get("/api/session-admin/moi/", **self.entete())
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["nom"], "Ama Koffi")
        self.assertEqual(reponse.data["identifiant"], "ama")

    def test_moi_est_ferme_sans_session(self) -> None:
        """C'est ce que l'écran appelle au chargement pour savoir si un jeton
        gardé dans le ``sessionStorage`` vaut encore quelque chose."""
        self.assertEqual(
            self.client.get("/api/session-admin/moi/").status_code, 401
        )

    def test_la_deconnexion_ferme_cette_session(self) -> None:
        self.assertEqual(
            self.client.post(
                "/api/session-admin/deconnexion/", **self.entete()
            ).status_code,
            204,
        )
        self.assertEqual(
            self.client.get("/api/dossiers/", **self.entete()).status_code, 401
        )

    def test_la_deconnexion_laisse_vivre_les_autres_sessions(self) -> None:
        """Fermer l'onglet du poste partagé ne doit pas déconnecter la même
        personne de son propre téléphone."""
        autre = self.connexion().data["jeton"]
        self.client.post("/api/session-admin/deconnexion/", **self.entete())
        self.assertEqual(
            self.client.get(
                "/api/dossiers/", **{"HTTP_X_JETON_ADMIN": autre}
            ).status_code,
            200,
        )

    def test_un_jeton_invente_ne_passe_pas(self) -> None:
        self.assertEqual(
            self.client.get(
                "/api/dossiers/", **{"HTTP_X_JETON_ADMIN": "faux-jeton"}
            ).status_code,
            401,
        )

    def test_une_session_expiree_ne_passe_plus(self) -> None:
        """Douze heures fermes, et **elle ne glisse pas**.

        ⚠️ ``SessionAcheteur`` dure trente jours glissants, et c'est justifié
        là-bas : refaire un code SMS à chaque visite ferait perdre des
        acheteurs. Ici le raisonnement s'inverse — ces routes montrent des
        noms, des numéros et des références de pièces d'identité.
        """
        session = SessionAdmin.objects.get(jeton=self.jeton)
        session.expire_le = timezone.now() - timedelta(minutes=1)
        session.save(update_fields=["expire_le"])
        self.assertEqual(
            self.client.get("/api/dossiers/", **self.entete()).status_code, 401
        )

    def test_l_echeance_ne_glisse_pas_a_l_usage(self) -> None:
        """``marquer_usage`` note le dernier usage **sans** repousser
        l'échéance, à la différence de ``SessionAcheteur.prolonger``."""
        avant = SessionAdmin.objects.get(jeton=self.jeton).expire_le
        self.client.get("/api/dossiers/", **self.entete())
        self.assertEqual(
            SessionAdmin.objects.get(jeton=self.jeton).expire_le, avant
        )

    def test_retirer_is_staff_ferme_la_session_sans_attendre(self) -> None:
        """⚠️ **Ce que le jeton partagé ne savait pas faire du tout.**

        On ne pouvait retirer l'accès à une personne qu'en changeant le jeton
        de tout le monde. ``is_staff`` est donc revérifié à chaque requête, et
        pas seulement à la connexion : sans cela, décocher la case laisserait
        la session vivre jusqu'à douze heures.
        """
        self.compte.is_staff = False
        self.compte.save(update_fields=["is_staff"])
        self.assertEqual(
            self.client.get("/api/dossiers/", **self.entete()).status_code, 401
        )


class LeJournalDesDecisions(SocleConnexion):
    """``décidé par`` vient du compte authentifié, et non du formulaire."""

    def test_la_decision_est_signee_par_le_compte_connecte(self) -> None:
        """⚠️ **``decide_par`` était un champ de texte libre envoyé par le
        client** : n'importe quel nom pouvait signer n'importe quelle décision.

        Ce n'est pas un détail de forme. Le §10.5 confie la validation d'un
        dossier à un humain parce que, le jour d'un litige, ce dossier est
        notre seul recours contre le groupeur. Un journal dont l'auteur est
        déclaratif ne prouve rien.
        """
        from groupachat.tests.test_recrutement import dossier_complet

        self.client.post("/api/groupeurs/", dossier_complet(), format="json")
        from groupachat.comptes.models import Groupeur

        groupeur = Groupeur.objects.get(pseudonyme="Chez Sika")
        jeton = self.connexion().data["jeton"]

        reponse = self.client.post(
            f"/api/dossiers/{groupeur.pk}/decision/",
            # On envoie exprès un `decide_par` menteur : il doit être ignoré.
            {
                "issue": "valide",
                "canal": "courriel",
                "decide_par": "Quelqu un d autre",
            },
            format="json",
            **{"HTTP_X_JETON_ADMIN": jeton},
        )
        self.assertEqual(reponse.status_code, 200, reponse.data)

        decision = groupeur.decisions_kyc.latest("decide_le")
        self.assertEqual(decision.decide_par, "Ama Koffi")

    def test_sans_nom_complet_le_journal_porte_l_identifiant(self) -> None:
        """Un journal se lit : le nom complet s'il existe, l'identifiant
        sinon — mais jamais rien."""
        self.compte.first_name = ""
        self.compte.last_name = ""
        self.compte.save(update_fields=["first_name", "last_name"])
        session = sessions_admin.connecter("ama", MOT_DE_PASSE)
        self.assertEqual(sessions_admin.nom_pour_le_journal(session), "ama")
