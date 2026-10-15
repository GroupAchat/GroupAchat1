# -*- coding: utf-8 -*-
"""L'inscription classique de l'acheteur — formulaire, puis vérification SMS.

Le compte acheteur ne naît plus d'un code SMS seul : l'acheteur remplit un
formulaire — nom, numéro, courriel facultatif, mot de passe — puis vérifie son
numéro par un code. Deux écrans, un compte.

⚠️ **La vérification du numéro n'est pas une étape de trop.** Le numéro *est*
l'identifiant du compte, et c'est par lui que partent les notifications de
livraison. Sans preuve, n'importe qui s'inscrit sur le numéro d'un voisin,
choisit le mot de passe, et reçoit à sa place l'annonce que son colis est
arrivé.

Les règles les plus coûteuses à perdre, et les tests qui les tiennent :

| Règle | Ce qu'on perd en la perdant | Test |
|---|---|---|
| Le formulaire est contrôlé avant le SMS | Un abandon, et un SMS payé pour rien | ``test_le_controle_n_envoie_aucun_code`` |
| Un numéro déjà pris est refusé tôt | L'acheteur corrige un champ qui est juste | ``test_un_numero_deja_pris_est_refuse_des_le_controle`` |
| Le mot de passe n'est posé qu'à la création | Le code SMS deviendrait une remise à zéro | ``test_le_mot_de_passe_ne_se_pose_pas_sur_un_compte_existant`` |
| Pas de compte à moitié inscrit | Un numéro « déjà pris » que personne ne possède | ``test_un_mot_de_passe_refuse_ne_laisse_pas_de_compte`` |
"""

from __future__ import annotations

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from groupachat.comptes.models import Acheteur, CodeConnexion

NUMERO = "+22890123456"
SECRET = "akosua-tokoin-2026"

FORMULAIRE = {
    "telephone": NUMERO,
    "nom": "Akosua Doe",
    "courriel": "akosua@example.tg",
    "mot_de_passe": SECRET,
}


class SocleInscription(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def controler(self, **remplace):
        return self.client.post(
            "/api/comptes/inscription/controler/",
            {**FORMULAIRE, **remplace},
            format="json",
        )

    def s_inscrire(self, **remplace):
        """Le parcours complet : contrôle, code, ouverture de session."""
        with override_settings(DEBUG=True):
            controle = self.controler(**remplace)
            assert controle.status_code == 200, controle.data

            demande = self.client.post(
                "/api/comptes/code/",
                {"telephone": remplace.get("telephone", NUMERO)},
                format="json",
            )
            code = demande.data["code_de_demonstration"]

            return self.client.post(
                "/api/comptes/session/",
                {**FORMULAIRE, **remplace, "code": code},
                format="json",
            )


class LeControleDuFormulaire(SocleInscription):
    def test_un_formulaire_valide_passe(self) -> None:
        reponse = self.controler()
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.data["valide"])

    def test_le_controle_n_envoie_aucun_code(self) -> None:
        """C'est sa raison d'être, et elle a deux faces.

        Un mot de passe trop court refusé **après** l'envoi du code laisse
        l'acheteur devant les quatre cases, obligé de revenir corriger un
        champ : c'est la façon sûre de faire abandonner une inscription. Et le
        jour où un fournisseur SMS sera branché (§18.2), c'est un SMS payé pour
        rien.
        """
        self.controler()
        self.assertEqual(CodeConnexion.objects.count(), 0)
        self.assertEqual(Acheteur.objects.count(), 0)

    def test_un_mot_de_passe_trop_court_est_refuse(self) -> None:
        reponse = self.controler(mot_de_passe="court")
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("mot_de_passe", reponse.data)

    def test_le_numero_ne_peut_pas_servir_de_mot_de_passe(self) -> None:
        reponse = self.controler(mot_de_passe="90123456")
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("mot_de_passe", reponse.data)

    def test_le_nom_est_obligatoire(self) -> None:
        """Le livreur en a besoin pour remettre le colis.

        C'est la seule chose que le formulaire exige en plus du numéro et du
        mot de passe : le courriel, lui, reste facultatif.
        """
        reponse = self.controler(nom="")
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("nom", reponse.data)

    def test_le_formulaire_passe_sans_mot_de_passe(self) -> None:
        """⚠️ **C'est le parcours normal**, pas un cas limite.

        Le formulaire d'inscription demande un prénom, un numéro et un
        courriel facultatif — rien d'autre. Le mot de passe se pose plus tard,
        depuis la page Profil, et il reste donc absent de cette route.

        Ce test existe parce que le champ est encore **accepté** par le
        sérialiseur : un ``required=True`` remis par distraction fermerait
        l'inscription à tout le monde, et aucun autre test ne le verrait.
        """
        reponse = self.client.post(
            "/api/comptes/inscription/controler/",
            {
                "telephone": NUMERO,
                "nom": "Akosua",
                "courriel": "akosua@example.tg",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertTrue(reponse.data["valide"])

    def test_un_mot_de_passe_fourni_reste_verifie(self) -> None:
        """Facultatif ne veut pas dire ignoré.

        Un champ qu'on accepte sans le contrôler serait pire que pas de champ
        du tout : il laisserait croire à une protection qui n'existe pas.
        """
        reponse = self.controler(mot_de_passe="court")
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("mot_de_passe", reponse.data)

    def test_le_courriel_reste_facultatif(self) -> None:
        """Une partie du public à Lomé n'a pas d'adresse consultée.

        Le même raisonnement que pour ``Groupeur.courriel`` : l'exiger
        écarterait exactement ces gens-là, et le numéro suffit à joindre.
        """
        self.assertEqual(self.controler(courriel="").status_code, 200)

    def test_un_numero_deja_pris_est_refuse_des_le_controle(self) -> None:
        """Et le message envoie vers la connexion, pas vers une correction.

        Le champ est juste : c'est le parcours qui est le mauvais. C'est le
        prix du modèle classique — deux parcours distincts existent, donc il
        faut dire à l'acheteur lequel est le sien.
        """
        Acheteur.objects.create(telephone=NUMERO, nom="Akosua Doe")
        reponse = self.controler()
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("telephone", reponse.data)
        self.assertIn("Connectez-vous", str(reponse.data["telephone"]))


class LInscription(SocleInscription):
    def test_le_compte_nait_avec_son_mot_de_passe_et_son_courriel(self) -> None:
        reponse = self.s_inscrire()
        self.assertEqual(reponse.status_code, 201)
        self.assertTrue(reponse.data["compte_cree"])
        self.assertTrue(reponse.data["acheteur"]["a_un_mot_de_passe"])
        self.assertEqual(reponse.data["acheteur"]["courriel"], "akosua@example.tg")
        self.assertEqual(reponse.data["acheteur"]["nom"], "Akosua Doe")

        # Et le mot de passe choisi ouvre bien le compte.
        entree = APIClient().post(
            "/api/comptes/session-mot-de-passe/",
            {"telephone": NUMERO, "mot_de_passe": SECRET},
            format="json",
        )
        self.assertEqual(entree.status_code, 201)

    def test_l_empreinte_ne_sort_pas_de_l_inscription(self) -> None:
        reponse = self.s_inscrire()
        self.assertNotIn("mot_de_passe", reponse.data["acheteur"])
        self.assertNotIn(SECRET, str(reponse.data))

    def test_le_mot_de_passe_ne_se_pose_pas_sur_un_compte_existant(self) -> None:
        """Sinon le code SMS serait une remise à zéro silencieuse.

        Or changer de mot de passe exige l'ancien, précisément pour qu'un
        téléphone prêté cinq minutes ne suffise pas à prendre un compte.
        Laisser cette porte ouverte annulerait cette protection par un autre
        chemin.
        """
        Acheteur.objects.create(telephone=NUMERO, nom="Akosua Doe")

        with override_settings(DEBUG=True):
            demande = self.client.post(
                "/api/comptes/code/", {"telephone": NUMERO}, format="json"
            )
            reponse = self.client.post(
                "/api/comptes/session/",
                {**FORMULAIRE, "code": demande.data["code_de_demonstration"]},
                format="json",
            )

        self.assertEqual(reponse.status_code, 400)
        self.assertIn("telephone", reponse.data)
        self.assertEqual(
            Acheteur.objects.get(telephone=NUMERO).mot_de_passe, ""
        )

    def test_la_connexion_par_sms_seule_marche_toujours(self) -> None:
        """⚠️ **L'ancien parcours n'est pas cassé, et il ne doit pas l'être.**

        ``session/`` sans ``mot_de_passe`` reste la reconnexion de quelqu'un
        qui n'en a pas posé, et c'est aussi la voie de récupération de tous les
        autres. Un test ici parce que le sérialiseur a gagné des champs : un
        ``required=True`` posé par distraction sur l'un d'eux fermerait cette
        voie pour tout le monde.
        """
        with override_settings(DEBUG=True):
            demande = self.client.post(
                "/api/comptes/code/", {"telephone": NUMERO}, format="json"
            )
            reponse = self.client.post(
                "/api/comptes/session/",
                {
                    "telephone": NUMERO,
                    "code": demande.data["code_de_demonstration"],
                    "nom": "Akosua Doe",
                },
                format="json",
            )
        self.assertEqual(reponse.status_code, 201)
        self.assertFalse(reponse.data["acheteur"]["a_un_mot_de_passe"])

    def test_un_mot_de_passe_refuse_ne_laisse_pas_de_compte(self) -> None:
        """Pas de compte à moitié inscrit, et c'est un cas réel.

        Le contrôle du formulaire se contourne par un appel direct : rien
        n'empêche d'envoyer un mot de passe trop court à ``session/``. Si le
        compte restait créé, son numéro serait désormais « déjà pris » — par un
        compte sans mot de passe que personne ne peut plus inscrire.
        """
        with override_settings(DEBUG=True):
            demande = self.client.post(
                "/api/comptes/code/", {"telephone": NUMERO}, format="json"
            )
            reponse = self.client.post(
                "/api/comptes/session/",
                {
                    **FORMULAIRE,
                    "mot_de_passe": "court",
                    "code": demande.data["code_de_demonstration"],
                },
                format="json",
            )

        self.assertEqual(reponse.status_code, 400)
        self.assertIn("mot_de_passe", reponse.data)
        self.assertFalse(Acheteur.objects.filter(telephone=NUMERO).exists())
