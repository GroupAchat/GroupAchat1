# -*- coding: utf-8 -*-
"""Le compte acheteur : code SMS, session, reconnexion automatique.

**C'est le fichier qui garde la seule vraie protection du produit.** Jusqu'ici
l'API identifiait un acheteur par son numéro de téléphone passé en paramètre
d'URL : huit chiffres, donc n'importe qui pouvait lire les commandes de
n'importe qui. Le jeton de session referme ça.

Les quatre règles les plus coûteuses à perdre, et les tests qui les tiennent :

| Règle | Ce qu'on perd en la perdant | Test |
|---|---|---|
| Un numéro n'identifie plus personne | Tout le bénéfice du changement | ``test_le_numero_seul_n_ouvre_plus_rien`` |
| Un code fixe ne part pas en production | Le compte de n'importe qui | ``test_sans_fournisseur_sms_la_production_refuse`` |
| Trois essais, puis le code meurt | 10 000 possibilités à essayer | ``test_le_code_meurt_apres_trois_essais`` |
| Un code ne sert qu'une fois | Un code lu par-dessus l'épaule resservirait | ``test_un_code_ne_sert_qu_une_fois`` |
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.catalogue.models import Campagne
from groupachat.comptes.models import Acheteur, CodeConnexion, SessionAcheteur
from groupachat.comptes.sessions import ouvrir_une_session
from groupachat.tests.aides import connecter


class SocleCompte(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def demander_un_code(self, telephone: str = "+22890123456"):
        with override_settings(DEBUG=True):
            return self.client.post(
                "/api/comptes/code/", {"telephone": telephone}, format="json"
            )


class DemandeDeCode(SocleCompte):
    def test_le_code_est_envoye_et_le_compte_signale(self) -> None:
        """``compte_existe`` évite de redemander son nom à qui l'a déjà donné."""
        reponse = self.demander_un_code()
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.data["envoye"])
        self.assertFalse(reponse.data["compte_existe"])

        Acheteur.objects.create(telephone="+22890123456", nom="Akosua Doe")
        self.assertTrue(self.demander_un_code().data["compte_existe"])

    @override_settings(DEBUG=False, SMS_FOURNISSEUR="demonstration")
    def test_le_mode_demonstration_est_un_opt_in_explicite(self) -> None:
        """Pour qu'une démonstration déployée reste utilisable.

        Le conteneur tourne avec ``DEBUG=0`` — c'est le bon réglage — et sans
        fournisseur SMS. Sans ce mode, le jury verrait un catalogue qu'on ne
        peut pas acheter.

        ⚠️ **C'est un opt-in, pas un repli.** Il faut écrire le mot
        ``demonstration`` dans le fichier d'environnement, et il reste visible
        dans la configuration de déploiement. Un défaut part en production par
        oubli ; une valeur écrite à la main y part par décision.
        """
        reponse = self.client.post(
            "/api/comptes/code/", {"telephone": "+22890123456"}, format="json"
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["code_de_demonstration"], "1234")

    @override_settings(DEBUG=False, SMS_FOURNISSEUR="")
    def test_sans_fournisseur_sms_la_production_refuse(self) -> None:
        """⚠️ **Le garde-fou le plus important de ce parcours.**

        Un code fixe mis en ligne donnerait à n'importe qui le compte de
        n'importe quel numéro. Ce réglage de développement ne doit pas pouvoir
        partir en production par simple oubli : il faut que quelque chose
        l'arrête, et c'est le serveur lui-même.

        **Il échoue fermé** : pas de SMS, pas de connexion — plutôt que pas de
        SMS, connexion pour tout le monde.
        """
        reponse = self.client.post(
            "/api/comptes/code/", {"telephone": "+22890123456"}, format="json"
        )
        self.assertEqual(reponse.status_code, 503)
        self.assertFalse(SessionAcheteur.objects.exists())

    def test_le_code_n_est_pas_rendu_en_clair_hors_developpement(self) -> None:
        """Il n'est lisible dans la réponse qu'en développement."""
        with override_settings(DEBUG=True):
            clair = self.client.post(
                "/api/comptes/code/", {"telephone": "+22890123456"}, format="json"
            ).data["code_de_demonstration"]
        self.assertEqual(clair, "1234")

        with override_settings(DEBUG=False, SMS_FOURNISSEUR="un-fournisseur"):
            reponse = self.client.post(
                "/api/comptes/code/", {"telephone": "+22890123456"}, format="json"
            )
        self.assertIsNone(reponse.data["code_de_demonstration"])

    def test_le_code_n_est_jamais_stocke_en_clair(self) -> None:
        self.demander_un_code()
        code = CodeConnexion.objects.latest("cree_le")
        self.assertNotIn("1234", code.code_hache)

    def test_demander_un_nouveau_code_tue_le_precedent(self) -> None:
        """Sinon, en redemander un multiplierait les codes en vol."""
        self.demander_un_code()
        premier = CodeConnexion.objects.latest("cree_le")
        self.demander_un_code()
        premier.refresh_from_db()
        self.assertTrue(premier.consomme)


class OuvertureDeSession(SocleCompte):
    def ouvrir(self, code: str = "1234", **extra):
        return self.client.post(
            "/api/comptes/session/",
            {"telephone": "+22890123456", "code": code, **extra},
            format="json",
        )

    def test_le_compte_se_cree_au_passage(self) -> None:
        """**Aucun second bouton « Créer un compte ».**

        Faire choisir entre « se connecter » et « s'inscrire » à quelqu'un qui
        veut juste payer est une question dont il n'a pas la réponse : il ne
        sait pas s'il a déjà un compte chez nous.
        """
        self.demander_un_code()
        reponse = self.ouvrir(
            nom="Akosua Doe", quartier="Tokoin", repere="Pharmacie Sodji"
        )

        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertTrue(reponse.data["compte_cree"])
        self.assertTrue(reponse.data["jeton"])

        acheteur = Acheteur.objects.get(telephone="+22890123456")
        self.assertEqual(acheteur.nom, "Akosua Doe")
        self.assertEqual(acheteur.quartier, "Tokoin")

    def test_le_code_meurt_apres_trois_essais(self) -> None:
        """⚠️ **La seule vraie protection d'un code à quatre chiffres.**

        Dix mille possibilités s'épuisent en quelques secondes. Le hachage n'y
        changerait rien ; le compteur, si.
        """
        self.demander_un_code()
        for essai in range(3):
            reponse = self.ouvrir(code="0000")
            self.assertEqual(reponse.status_code, 400, f"essai {essai + 1}")

        # Même le bon code ne passe plus : il faut en redemander un.
        self.assertEqual(self.ouvrir(code="1234").status_code, 400)
        self.assertFalse(SessionAcheteur.objects.exists())

    def test_le_message_dit_combien_d_essais_restent(self) -> None:
        """Pour qu'on sache qu'on approche du bout, pas qu'on le découvre."""
        self.demander_un_code()
        reponse = self.ouvrir(code="0000")
        self.assertIn("2 essais restants", str(reponse.data["code"]))

    def test_un_code_ne_sert_qu_une_fois(self) -> None:
        """Un code lu par-dessus l'épaule ne doit pas resservir."""
        self.demander_un_code()
        self.assertEqual(self.ouvrir().status_code, 201)
        self.assertEqual(self.ouvrir().status_code, 400)

    def test_un_code_expire(self) -> None:
        self.demander_un_code()
        code = CodeConnexion.objects.latest("cree_le")
        CodeConnexion.objects.filter(pk=code.pk).update(
            expire_le=timezone.now() - timedelta(minutes=1)
        )
        self.assertEqual(self.ouvrir().status_code, 400)

    def test_se_reconnecter_n_efface_pas_ce_qu_on_a_deja_donne(self) -> None:
        """**On complète, on n'écrase pas.**

        Quelqu'un qui se reconnecte depuis un autre appareil n'envoie ni nom ni
        adresse. Les remplacer par du vide effacerait ce qu'il a déjà donné —
        et il découvrirait son adresse perdue au moment de commander.
        """
        self.demander_un_code()
        self.ouvrir(nom="Akosua Doe", quartier="Tokoin", repere="Pharmacie Sodji")

        self.demander_un_code()
        self.ouvrir()

        acheteur = Acheteur.objects.get(telephone="+22890123456")
        self.assertEqual(acheteur.nom, "Akosua Doe")
        self.assertEqual(acheteur.quartier, "Tokoin")

    def test_une_nouvelle_adresse_devient_la_valeur_par_defaut(self) -> None:
        """C'est **la dernière utilisée** qui pré-remplit la prochaine commande."""
        self.demander_un_code()
        self.ouvrir(nom="Akosua Doe", quartier="Tokoin", repere="Pharmacie Sodji")

        self.demander_un_code()
        self.ouvrir(quartier="Agoe", repere="Carrefour Assiyéyé")

        acheteur = Acheteur.objects.get(telephone="+22890123456")
        self.assertEqual(acheteur.quartier, "Agoe")
        self.assertEqual(acheteur.nom, "Akosua Doe")


class CeQueLeJetonProtege(SocleCompte):
    """⚠️ **Les tests pour lesquels tout ce travail a été fait.**"""

    def setUp(self) -> None:
        super().setUp()
        self.akosua = Acheteur.objects.create(
            telephone="+22890123456", nom="Akosua Doe"
        )

    def test_le_numero_seul_n_ouvre_plus_rien(self) -> None:
        """Le défaut d'origine, et sa correction.

        Avant, `?telephone=+22890123456` suffisait. Huit chiffres se devinent,
        se lisent sur un reçu, se retrouvent dans un répertoire.
        """
        reponse = self.client.get("/api/commandes/?telephone=%2B22890123456")
        self.assertEqual(reponse.status_code, 401)

    def test_un_jeton_invente_ne_passe_pas(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Jeton " + "a" * 43)
        self.assertEqual(self.client.get("/api/commandes/").status_code, 401)

    def test_un_jeton_expire_ne_passe_plus(self) -> None:
        session = ouvrir_une_session(self.akosua)
        SessionAcheteur.objects.filter(pk=session.pk).update(
            expire_le=timezone.now() - timedelta(seconds=1)
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Jeton {session.jeton}")
        self.assertEqual(self.client.get("/api/commandes/").status_code, 401)

    def test_c_est_401_et_non_403(self) -> None:
        """La distinction commande deux écrans différents.

        **401** : « je ne sais pas qui vous êtes » → rouvrir la feuille de
        connexion. **403** : « je sais, et c'est non » → afficher un refus. Les
        confondre laisserait quelqu'un dont la session a expiré devant un
        « accès refusé », sans moyen de revenir.
        """
        reponse = self.client.get("/api/commandes/")
        self.assertEqual(reponse.status_code, 401)
        self.assertIn("WWW-Authenticate", reponse)

    def test_on_ne_paie_pas_au_nom_d_un_autre(self) -> None:
        """L'acheteur vient de la session, jamais du corps de la requête.

        Sinon on pourrait faire livrer chez soi une commande inscrite au compte
        de quelqu'un d'autre.
        """
        from groupachat.comptes.models import Groupeur

        groupeur = Groupeur.objects.create(
            pseudonyme="Mama Gro",
            nom_complet="Akossiwa Mensah",
            telephone="+22891000001",
            statut_kyc=Groupeur.StatutKyc.VALIDE,
            titulaire_mobile_money="Akossiwa Mensah",
            numero_mobile_money="+22891000001",
        )
        campagne = Campagne.objects.create(
            groupeur=groupeur,
            titre="Écouteurs filaires avec micro",
            description="Un lot de cent.",
            contenu_part="Une paire",
            categorie=Campagne.Categorie.ELECTRONIQUE,
            prix_part=Decimal("4000"),
            objectif_participants=40,
            date_fin=timezone.now() + timedelta(days=2),
        )

        yawa = Acheteur.objects.create(telephone="+22899999999", nom="Yawa Tete")
        client = APIClient()
        connecter(client, "+22899999999")

        client.post(
            "/api/commandes/payer/",
            {
                "campagne": campagne.pk,
                # On tente d'écrire la commande au compte d'Akosua.
                "telephone": self.akosua.telephone,
                "quantite": 1,
                "quartier": "Tokoin",
                "repere": "Pharmacie Sodji",
                "cle_idempotence": "tentative",
            },
            format="json",
        )

        self.assertEqual(campagne.commandes.count(), 1)
        # La commande appartient à qui a ouvert la session, pas au numéro posté.
        self.assertEqual(campagne.commandes.get().acheteur, yawa)


class ReconnexionAutomatique(SocleCompte):
    def test_le_profil_revient_avec_le_jeton(self) -> None:
        """**C'est ça, la reconnexion automatique.**

        L'application appelle cette route au lancement avec le jeton retenu :
        si elle répond, l'acheteur est connecté sans rien faire.
        """
        client = APIClient()
        connecter(
            client,
            "+22890123456",
            nom="Akosua Doe",
            quartier="Tokoin",
            repere="Pharmacie Sodji",
        )

        reponse = client.get("/api/comptes/moi/")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["nom"], "Akosua Doe")
        self.assertEqual(reponse.data["quartier"], "Tokoin")
        self.assertEqual(reponse.data["repere"], "Pharmacie Sodji")

    def test_sans_jeton_le_profil_repond_401(self) -> None:
        """L'application sait alors qu'elle doit oublier ce qu'elle gardait."""
        self.assertEqual(self.client.get("/api/comptes/moi/").status_code, 401)

    def test_se_deconnecter_revoque_cette_session_seulement(self) -> None:
        """Se déconnecter du téléphone d'un ami ne déconnecte pas le sien."""
        acheteur = Acheteur.objects.create(telephone="+22890123456")
        telephone_a = ouvrir_une_session(acheteur)
        telephone_b = ouvrir_une_session(acheteur)

        self.client.credentials(HTTP_AUTHORIZATION=f"Jeton {telephone_a.jeton}")
        self.assertEqual(
            self.client.post("/api/comptes/deconnexion/").status_code, 204
        )

        self.assertFalse(
            SessionAcheteur.objects.filter(pk=telephone_a.pk).exists()
        )
        self.assertTrue(SessionAcheteur.objects.filter(pk=telephone_b.pk).exists())

    def test_la_session_glisse_a_l_usage(self) -> None:
        """Un acheteur qui commande tous les mois ne refait jamais le code SMS."""
        acheteur = Acheteur.objects.create(telephone="+22890123456")
        session = ouvrir_une_session(acheteur)

        # On la recule : l'échéance approche, et le dernier usage date.
        ancienne_echeance = timezone.now() + timedelta(days=2)
        SessionAcheteur.objects.filter(pk=session.pk).update(
            expire_le=ancienne_echeance,
            dernier_usage=timezone.now() - timedelta(days=5),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Jeton {session.jeton}")
        self.client.get("/api/comptes/moi/")

        session.refresh_from_db()
        self.assertGreater(session.expire_le, ancienne_echeance)

    def test_elle_ne_se_prolonge_pas_a_chaque_requete(self) -> None:
        """Sinon ce serait une écriture en base par vignette affichée.

        L'heure est le compromis : la session glisse bien, et la base n'est pas
        sollicitée pour rien.
        """
        acheteur = Acheteur.objects.create(telephone="+22890123456")
        session = ouvrir_une_session(acheteur)
        self.client.credentials(HTTP_AUTHORIZATION=f"Jeton {session.jeton}")

        self.client.get("/api/comptes/moi/")
        session.refresh_from_db()
        premier = session.dernier_usage

        self.client.get("/api/comptes/moi/")
        session.refresh_from_db()
        self.assertEqual(session.dernier_usage, premier)
