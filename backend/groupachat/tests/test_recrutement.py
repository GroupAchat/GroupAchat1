# -*- coding: utf-8 -*-
"""Le recrutement d'un groupeur : dépôt, examen humain, décision, annonce.

**Ce parcours est le produit.** « Vous êtes livré, ou remboursé » s'affiche à
l'acheteur sur presque chaque écran, et c'est cette phrase qui le décide à
payer d'avance quelqu'un qu'il ne connaît pas.

⚠️ **C'est nous qui remboursons**, et le groupeur a déjà retiré l'argent à la
clôture. Notre seul recours ce jour-là est un **dossier constitué, examiné par
un humain, et opposable** (§10.5). Sans ce parcours, la garantie est une
phrase que personne ne peut honorer.

Chaque test porte le nom de la règle qu'il protège, pas celui de la fonction
qu'il appelle — pour qu'un échec dise ce qui est cassé dans le produit, et pas
seulement où.

Les trois règles les plus coûteuses à perdre, et les tests qui les tiennent :

| Règle | Ce qu'on perd en la perdant | Test |
|---|---|---|
| Rien n'est validé automatiquement | La promesse faite à l'acheteur | ``test_un_dossier_depose_ne_se_valide_pas_tout_seul`` |
| Pas de refus sans motif | Un groupeur qui ne sait pas quoi corriger | ``test_un_refus_sans_motif_est_refuse`` |
| Une décision annoncée l'a vraiment été | Un journal qui mentirait en justice | ``test_un_appel_ne_se_marque_pas_annonce_tout_seul`` |
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.core.exceptions import ValidationError
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat import notifications
from groupachat.catalogue.models import Campagne
from django.contrib.auth import get_user_model

from groupachat.comptes import sessions_admin
from groupachat.comptes.models import DecisionKyc, Groupeur, PieceKyc

#: Le jeton d'administration utilisé par les tests.
#:
#: Posé par ``override_settings``, et non dans ``os.environ``. La permission
#: lisait l'environnement directement ; elle lit désormais les réglages, qui
#: chargent le ``.env`` de la racine une fois pour toutes. Un test qui poserait
#: encore la variable d'environnement passerait à côté.
JETON = "jeton-de-test"


def dossier_complet(**remplacements) -> dict:
    """Un dossier de niveau Entrée valide, pour l'API d'inscription.

    Factorisé parce que la moitié des tests part de ce dossier et n'en change
    **qu'un champ** : écrit en entier à chaque fois, on ne verrait plus lequel.
    """
    donnees = {
        "pseudonyme": "Chez Sika",
        "nom_complet": "Sika Adjo",
        "telephone": "+22890111222",
        "courriel": "sika@example.tg",
        "titulaire_mobile_money": "Sika Adjo",
        "numero_mobile_money": "+22890111222",
        "pieces": [
            {"nature": "piece-recto", "reference": "coffre/sika/recto"},
            {"nature": "piece-verso", "reference": "coffre/sika/verso"},
            {"nature": "selfie", "reference": "coffre/sika/selfie"},
        ],
    }
    donnees.update(remplacements)
    return donnees


# ── Les textes, sans base de données ────────────────────────────────────────


class TextesDesAnnonces(TestCase):
    """``notifications.py`` ne connaît pas Django : on le teste tel quel.

    C'est l'intérêt de l'avoir isolé — ces formulations sont la seule parole de
    Group Achat qui quitte la plateforme, et on peut les relire une par une
    sans monter de base ni de serveur de messagerie.
    """

    def test_un_refus_sans_motif_est_refuse(self) -> None:
        """La règle la plus importante de ce module.

        Un refus sans motif est une porte fermée sans poignée pour le
        groupeur, **et** une ligne illisible six mois plus tard, quand on
        cherche pourquoi tel groupeur a été écarté.
        """
        with self.assertRaises(notifications.MotifRequis):
            notifications.verifier("refuse", None)
        with self.assertRaises(notifications.MotifRequis):
            notifications.verifier("a-completer", "")

    def test_un_motif_hors_liste_est_refuse(self) -> None:
        """La liste est fermée, et c'est ce qui la rend dénombrable.

        Un champ libre contiendrait au bout de six mois quarante formulations
        du même refus : on ne pourrait plus compter pourquoi les dossiers
        échouent, donc plus corriger le formulaire qui les fait échouer.
        """
        with self.assertRaises(notifications.MotifInconnu):
            notifications.verifier("refuse", "parce-que")

    def test_une_validation_n_exige_pas_de_motif(self) -> None:
        notifications.verifier("valide", None)

    def test_la_decision_est_dans_la_premiere_phrase(self) -> None:
        """On ne fait pas lire trois paragraphes avant de dire l'essentiel."""
        _, corps = notifications.message_validation("Chez Sika", 150000)
        premieres_lignes = corps.split("\n\n")[1]
        self.assertIn("validé", premieres_lignes)

        _, corps = notifications.message_decision_negative(
            "Chez Sika", "refuse", "piece-illisible"
        )
        self.assertIn("n'a pas été validé", corps.split("\n\n")[1])

    def test_le_plafond_est_dit_dans_le_message_de_validation(self) -> None:
        """Découvrir son plafond bloqué par une erreur est la pire façon.

        Le chiffre est écrit avec l'espace insécable du reste du produit.
        """
        _, corps = notifications.message_validation("Chez Sika", 150000)
        self.assertIn("150 000 F", corps)

    def test_au_niveau_etabli_aucun_plafond_n_est_invente(self) -> None:
        """``None`` veut dire « au cas par cas » (§10.4), pas « très grand ».

        Le cahier des charges est explicite : quand un chiffre n'est pas connu,
        on écrit qu'il ne l'est pas, on ne l'invente pas.
        """
        _, corps = notifications.message_validation("Lomé Deals", None)
        self.assertIn("fixé avec vous", corps)
        self.assertNotIn(" F", corps.split("Trois choses")[0].replace("Group", ""))

    def test_un_refus_dit_toujours_quoi_faire_ensuite(self) -> None:
        """Pour les sept motifs, sans exception."""
        for motif in notifications.MOTIFS:
            _, corps = notifications.message_decision_negative(
                "Chez Sika", "refuse", motif
            )
            self.assertIn("Ce qu'il faut faire :", corps)
            self.assertNotEqual(notifications.MOTIFS[motif]["suite"], "")

    def test_aucun_motif_ne_repete_le_verdict(self) -> None:
        """Un motif public est **une raison**, pas un second verdict.

        Il est inséré après « Votre dossier n'a pas été validé : ». Un motif
        qui redit « nous ne pouvons pas valider votre dossier » produit la
        tautologie « Votre dossier n'a pas été validé : nous ne pouvons pas
        valider votre dossier » — qui s'entend encore plus mal au téléphone
        qu'elle ne se lit. Défaut réellement présent dans la première version
        de ce module, et invisible aux tests de l'époque.
        """
        for motif, detail in notifications.MOTIFS.items():
            with self.subTest(motif=motif):
                self.assertNotIn("pas valider", detail["public"], motif)
                self.assertNotIn("pas été validé", detail["public"], motif)

    def test_aucune_suite_ne_suppose_un_message_ecrit(self) -> None:
        """Le même texte part en courriel **et** se lit au téléphone.

        « Répondez à ce message » est donc faux dans un cas sur deux : il n'y a
        pas de message dans un appel. Les suites sont rédigées pour les deux
        canaux à la fois.
        """
        for motif, detail in notifications.MOTIFS.items():
            with self.subTest(motif=motif):
                self.assertNotIn("ce message", detail["suite"], motif)

    def test_le_doute_sur_l_identite_ne_dit_pas_ce_qui_l_a_eveille(self) -> None:
        """Le motif interne et le motif public diffèrent, et c'est voulu.

        Dire à quelqu'un *ce qui* a éveillé le soupçon lui apprend quoi
        corriger pour recommencer.
        """
        interne = notifications.MOTIFS["doute-identite"]["interne"]
        public = notifications.MOTIFS["doute-identite"]["public"]
        self.assertIn("Doute", interne)
        self.assertNotIn("doute", public.lower())

    def test_le_script_d_appel_porte_des_indications_de_conduite(self) -> None:
        """Un script d'appel sans conduite n'est qu'un texte lu à voix haute.

        Les crochets ne se prononcent pas : ils disent de se présenter, de
        laisser parler, et de ne pas trancher au téléphone sur un élément
        nouveau.
        """
        script = notifications.script_appel(
            "Chez Sika", "refuse", "doute-identite"
        )
        self.assertIn("[Se présenter", script)
        self.assertIn("rouvrir le dossier", script)

    def test_le_script_de_validation_rappelle_l_anonymat(self) -> None:
        """Il l'apprend au téléphone comme par courriel, pas seulement à l'écran."""
        script = notifications.script_appel("Chez Sika", "valide", None, 150000)
        self.assertIn("pseudonyme", script)
        self.assertIn("1 500 F", script)


# ── Le cycle de vie du dossier ──────────────────────────────────────────────


class CycleDuDossier(TestCase):
    def setUp(self) -> None:
        self.groupeur = Groupeur.objects.create(
            pseudonyme="Chez Sika",
            nom_complet="Sika Adjo",
            telephone="+22890111222",
            courriel="sika@example.tg",
            titulaire_mobile_money="Sika Adjo",
            numero_mobile_money="+22890111222",
        )

    def test_un_dossier_depose_ne_se_valide_pas_tout_seul(self) -> None:
        """**La règle qui porte tout le produit.**

        Le §10.5 confie la décision à un humain. Un dossier soumis attend, et
        son groupeur ne peut rien lancer — faute de quoi « nous sélectionnons
        nos groupeurs » serait un mensonge affiché sur chaque écran acheteur.
        """
        self.groupeur.soumettre_le_dossier()
        self.groupeur.refresh_from_db()

        self.assertEqual(
            self.groupeur.statut_kyc, Groupeur.StatutKyc.EN_VERIFICATION
        )
        self.assertFalse(self.groupeur.peut_lancer_une_campagne)
        self.assertTrue(self.groupeur.dossier_en_attente)

    def test_un_double_depot_ne_cree_pas_deux_entrees_dans_la_file(self) -> None:
        """Un double appui sur « Envoyer » est un geste ordinaire."""
        self.groupeur.soumettre_le_dossier()
        self.groupeur.soumettre_le_dossier()
        self.assertEqual(
            self.groupeur.statut_kyc, Groupeur.StatutKyc.EN_VERIFICATION
        )

    def test_un_dossier_non_soumis_ne_peut_pas_etre_tranche(self) -> None:
        """On ne décide pas d'un dossier que son auteur n'a pas déposé."""
        with self.assertRaises(ValidationError):
            self.groupeur.trancher(
                issue="valide", decide_par="Kephira", canal="courriel"
            )

    def test_une_validation_ouvre_le_droit_de_lancer_un_groupage(self) -> None:
        self.groupeur.soumettre_le_dossier()
        decision = self.groupeur.trancher(
            issue="valide", decide_par="Kephira", canal="courriel"
        )
        self.groupeur.refresh_from_db()

        self.assertTrue(self.groupeur.peut_lancer_une_campagne)
        self.assertEqual(self.groupeur.niveau, Groupeur.Niveau.ENTREE)
        self.assertEqual(self.groupeur.plafond, Decimal("150000"))
        self.assertEqual(decision.issue, "valide")
        self.assertEqual(decision.motif, "")

    def test_un_dossier_a_completer_revient_a_son_auteur_sans_etre_refuse(
        self,
    ) -> None:
        """L'issue la plus utile des trois.

        La plupart des dossiers qui échouent le font sur une photo floue. Les
        refuser définitivement ferait perdre des groupeurs recrutables, alors
        que le recrutement est le goulot d'étranglement du lancement.
        """
        self.groupeur.soumettre_le_dossier()
        self.groupeur.trancher(
            issue="a-completer",
            decide_par="Kephira",
            canal="courriel",
            motif="piece-illisible",
        )
        self.groupeur.refresh_from_db()

        self.assertEqual(
            self.groupeur.statut_kyc, Groupeur.StatutKyc.A_COMPLETER
        )
        self.assertFalse(self.groupeur.peut_lancer_une_campagne)
        # Et il peut redéposer : c'est toute la différence avec un refus.
        self.groupeur.soumettre_le_dossier()
        self.assertTrue(self.groupeur.dossier_en_attente)

    def test_un_refus_empeche_de_lancer_un_groupage(self) -> None:
        """Le verrou se vérifie **au modèle**, pas seulement à l'écran.

        Un bouton grisé dans l'interface ne protège de rien : il suffit d'une
        requête directe pour le contourner.
        """
        self.groupeur.soumettre_le_dossier()
        self.groupeur.trancher(
            issue="refuse",
            decide_par="Kephira",
            canal="appel",
            motif="doute-identite",
        )
        self.groupeur.refresh_from_db()

        with self.assertRaises(ValidationError):
            Campagne.objects.create(
                groupeur=self.groupeur,
                titre="Écouteurs filaires avec micro",
                description="Un lot de cent.",
                contenu_part="Une paire",
                categorie=Campagne.Categorie.ELECTRONIQUE,
                prix_part=Decimal("4000"),
                objectif_participants=40,
                date_fin=timezone.now() + timedelta(days=3),
            )

    def test_un_dossier_aux_noms_divergents_peut_etre_refuse(self) -> None:
        """**Le seul dossier qu'on ne pouvait pas refuser était celui qui devait l'être.**

        Le contrôle n° 2 s'appliquait à toute écriture sur le groupeur, donc
        aussi à celle qui enregistre le refus. La ligne devenait immodifiable
        dès que le compte Mobile Money n'était plus au bon nom — c'est-à-dire
        précisément dans le cas que le §10.5 désigne comme le signal d'alerte
        numéro un.

        Ce test écrit la divergence par ``update``, qui ne passe pas par
        ``save`` : c'est ainsi qu'elle apparaît en vrai, par un compte modifié
        après le dépôt.
        """
        self.groupeur.soumettre_le_dossier()
        Groupeur.objects.filter(pk=self.groupeur.pk).update(
            titulaire_mobile_money="Afi Kossi"
        )
        self.groupeur.refresh_from_db()

        decision = self.groupeur.trancher(
            issue="refuse",
            decide_par="Kephira",
            canal="appel",
            motif="noms-divergents",
        )
        self.groupeur.refresh_from_db()

        self.assertEqual(self.groupeur.statut_kyc, Groupeur.StatutKyc.REFUSE)
        self.assertEqual(decision.motif, "noms-divergents")
        self.assertFalse(self.groupeur.peut_lancer_une_campagne)

    def test_la_concordance_reste_exigee_a_la_saisie(self) -> None:
        """La levée du contrôle ne vaut **que** pour l'enregistrement d'une décision.

        Un enregistrement ordinaire — création, modification du compte — doit
        continuer de le subir, sinon la correction de bug ci-dessus aurait
        supprimé le contrôle le plus rentable du §10.5 au lieu de le cantonner.
        """
        with self.assertRaises(ValidationError):
            Groupeur.objects.create(
                pseudonyme="Prête-nom",
                nom_complet="Yao Komlan",
                telephone="+22890999888",
                titulaire_mobile_money="Afi Kossi",
                numero_mobile_money="+22890999888",
            )

        # Et sur une modification, pas seulement sur une création.
        self.groupeur.titulaire_mobile_money = "Afi Kossi"
        with self.assertRaises(ValidationError):
            self.groupeur.save()

    def test_l_historique_des_decisions_n_est_jamais_ecrase(self) -> None:
        """C'est lui qui montre qu'un groupeur en est à sa troisième tentative.

        Un champ d'état seul perdrait cette information, qui est exactement
        celle qui doit faire hésiter avant de valider.
        """
        self.groupeur.soumettre_le_dossier()
        self.groupeur.trancher(
            issue="a-completer",
            decide_par="Kephira",
            canal="courriel",
            motif="piece-illisible",
        )
        self.groupeur.soumettre_le_dossier()
        self.groupeur.trancher(
            issue="a-completer",
            decide_par="Kephira",
            canal="courriel",
            motif="selfie-non-conforme",
        )
        self.groupeur.soumettre_le_dossier()
        self.groupeur.trancher(
            issue="valide", decide_par="Kephira", canal="courriel"
        )

        self.assertEqual(self.groupeur.decisions_kyc.count(), 3)
        # La plus récente d'abord : c'est ce que l'écran du groupeur affiche.
        self.assertEqual(self.groupeur.derniere_decision.issue, "valide")

    def test_un_dossier_valide_ne_se_resoumet_pas(self) -> None:
        self.groupeur.soumettre_le_dossier()
        self.groupeur.trancher(
            issue="valide", decide_par="Kephira", canal="courriel"
        )
        with self.assertRaises(ValidationError):
            self.groupeur.soumettre_le_dossier()

    def test_une_seule_piece_par_nature(self) -> None:
        """Redéposer un recto remplace l'ancien, il ne s'y ajoute pas.

        Sinon l'administrateur examine une pile et ne sait plus laquelle est la
        bonne — ce qui est pire que de n'avoir qu'une pièce médiocre.
        """
        PieceKyc.objects.create(
            groupeur=self.groupeur, nature="piece-recto", reference="a"
        )
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            PieceKyc.objects.create(
                groupeur=self.groupeur, nature="piece-recto", reference="b"
            )


# ── L'annonce ───────────────────────────────────────────────────────────────


class AnnonceDeLaDecision(TestCase):
    def setUp(self) -> None:
        self.avec_courriel = Groupeur.objects.create(
            pseudonyme="Chez Sika",
            nom_complet="Sika Adjo",
            telephone="+22890111222",
            courriel="sika@example.tg",
            titulaire_mobile_money="Sika Adjo",
            numero_mobile_money="+22890111222",
        )
        self.sans_courriel = Groupeur.objects.create(
            pseudonyme="Lomé Deals",
            nom_complet="Kodjo Amegan",
            telephone="+22890333444",
            titulaire_mobile_money="Kodjo Amegan",
            numero_mobile_money="+22890333444",
        )
        for groupeur in (self.avec_courriel, self.sans_courriel):
            groupeur.soumettre_le_dossier()

    def test_un_courriel_part_et_la_decision_est_marquee_annoncee(self) -> None:
        from groupachat.comptes.annonces import annoncer

        decision = self.avec_courriel.trancher(
            issue="valide", decide_par="Kephira", canal="courriel"
        )
        resultat = annoncer(decision)
        decision.refresh_from_db()

        self.assertTrue(resultat.annonce)
        self.assertIsNotNone(decision.notifie_le)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["sika@example.tg"])
        self.assertIn("validé", mail.outbox[0].subject)

    def test_un_appel_ne_se_marque_pas_annonce_tout_seul(self) -> None:
        """**Le journal ne doit pas prétendre qu'on a téléphoné.**

        C'est ce journal qu'on produira le jour d'un litige (§18.3). Marquer
        l'annonce à l'enregistrement de la décision lui ferait dire le
        contraire de ce qui s'est passé.
        """
        from groupachat.comptes.annonces import annoncer

        decision = self.sans_courriel.trancher(
            issue="refuse",
            decide_par="Kephira",
            canal="appel",
            motif="noms-divergents",
        )
        resultat = annoncer(decision)
        decision.refresh_from_db()

        self.assertFalse(resultat.annonce)
        self.assertIsNone(decision.notifie_le)
        self.assertIn("[Se présenter", resultat.script)
        self.assertEqual(len(mail.outbox), 0)

        # Puis l'administrateur téléphone, et l'acte.
        decision.marquer_notifie()
        decision.refresh_from_db()
        self.assertIsNotNone(decision.notifie_le)

    def test_sans_courriel_le_canal_courriel_est_refuse_clairement(self) -> None:
        """Et le message dit quoi faire : téléphoner.

        Le téléphone étant obligatoire à l'inscription, il n'existe aucune
        décision impossible à annoncer — seulement des décisions à annoncer
        autrement.
        """
        from groupachat.comptes.annonces import annoncer

        decision = self.sans_courriel.trancher(
            issue="valide", decide_par="Kephira", canal="courriel"
        )
        with self.assertRaises(ValidationError) as leve:
            annoncer(decision)
        self.assertIn("téléphone", leve.exception.messages[0])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_le_courriel_de_validation_porte_les_regles_du_produit(self) -> None:
        """Il apprend l'anonymat, les frais et le devis — avant de commencer.

        Un groupeur qui découvre à la clôture qu'il doit déposer un devis
        appelle le support ; celui qui l'a lu à la validation ne le fait pas.
        """
        from groupachat.comptes.annonces import annoncer

        annoncer(
            self.avec_courriel.trancher(
                issue="valide", decide_par="Kephira", canal="courriel"
            )
        )
        corps = mail.outbox[0].body

        self.assertIn("pseudonyme", corps)
        self.assertIn("1 500 F", corps)
        self.assertIn("devis", corps)
        # ⚠️ Plus aucun pourcentage : ce n'est plus une commission.
        self.assertNotIn("5 %", corps)
        # ⚠️ §1.7 : jamais « bloqué jusqu'à la livraison ».
        self.assertNotIn("bloqué", corps)
        self.assertIn("à la clôture", corps)


# ── L'API ───────────────────────────────────────────────────────────────────


class SocleApi(TestCase):
    """Le socle des tests d'API du recrutement.

    ⚠️ **Il portait `@override_settings(JETON_ADMIN="jeton-de-test")`**, avec
    une longue note expliquant qu'il fallait passer par les réglages et non par
    `os.environ` — la panne avait coûté neuf tests tombés d'un coup sur un 403
    inexpliqué. Ce piège n'existe plus : **il n'y a plus de jeton partagé ni de
    réglage à poser.** Les routes exigent une session, ouverte par
    `ouvrir_l_administration`.
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def ouvrir_l_administration(self) -> str:
        """Un compte `is_staff`, une session, et le jeton qui va avec.

        ⚠️ **Ces tests posaient `@override_settings(JETON_ADMIN=...)`** et
        envoyaient la même chaîne dans l'en-tête. Le jeton partagé n'existe
        plus : les routes d'administration exigent une session ouverte contre
        un mot de passe. On passe donc par `sessions_admin.connecter`, c'est-à-
        dire par le chemin réel, plutôt qu'en fabriquant un `SessionAdmin` à la
        main — sinon le test de la connexion serait le seul à l'emprunter.
        """
        get_user_model().objects.create_user(
            username="ama",
            password="mot-de-passe-de-test",
            first_name="Ama",
            last_name="Koffi",
            is_staff=True,
        )
        return sessions_admin.connecter(
            "ama", "mot-de-passe-de-test"
        ).jeton

class InscriptionParApi(SocleApi):
    def test_un_depot_met_le_dossier_en_file_d_attente(self) -> None:
        """Déposer **et** soumettre, en une requête.

        Les deux gestes sont indissociables : un dossier créé mais non soumis
        n'apparaît dans la file de personne, alors que son auteur croit avoir
        terminé. C'est la panne la plus coûteuse de ce parcours, parce qu'elle
        est invisible des deux côtés.
        """
        reponse = self.client.post(
            "/api/groupeurs/", dossier_complet(), format="json"
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(reponse.data["etat"], "en-verification")
        self.assertFalse(reponse.data["peut_lancer_une_campagne"])

        groupeur = Groupeur.objects.get(pseudonyme="Chez Sika")
        self.assertEqual(groupeur.pieces.count(), 3)

    def test_le_mode_demonstration_est_eteint_par_defaut(self) -> None:
        """⚠️ **Le test qui garde le défaut fermé.**

        Le mode démonstration valide les dossiers sur-le-champ. Un réglage
        qui s'allumerait tout seul — en suivant ``DEBUG``, par exemple —
        ferait tourner toute cette suite sans jamais exercer l'examen des
        dossiers, c'est-à-dire sans protéger ce qu'elle est là pour protéger.

        Il a d'abord été écrit ainsi, et six tests sont tombés d'un coup.
        Celui-ci est là pour que cette erreur ne se refasse pas en silence.
        """
        self.assertFalse(
            settings.DEMONSTRATION,
            "La démonstration doit se demander, jamais s'inviter.",
        )

        reponse = self.client.post(
            "/api/groupeurs/", dossier_complet(), format="json"
        )
        self.assertEqual(reponse.data["etat"], "en-verification")

    @override_settings(DEMONSTRATION=True)
    def test_en_demonstration_le_dossier_est_valide_sur_le_champ(self) -> None:
        """Allumé, il ouvre l'espace groupeur immédiatement.

        C'est ce qu'on veut pour montrer le produit : on traverse
        l'inscription et on arrive dans l'espace groupeur, sans attendre qu'un
        administrateur se connecte.

        ⚠️ **La décision reste tracée, et son auteur est écrit en clair.** Une
        validation anonyme en base serait indiscernable d'un vrai examen —
        c'est exactement ce qu'il ne faut pas laisser derrière soi.
        """
        reponse = self.client.post(
            "/api/groupeurs/", dossier_complet(), format="json"
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(reponse.data["etat"], "valide")
        self.assertTrue(reponse.data["peut_lancer_une_campagne"])

        groupeur = Groupeur.objects.get(pseudonyme="Chez Sika")
        decision = groupeur.decisions_kyc.latest("decide_le")
        self.assertEqual(decision.issue, "valide")
        self.assertEqual(decision.decide_par, "Mode démonstration")

    def test_le_depot_ne_renvoie_pas_le_dossier_relu(self) -> None:
        """Pas de nom, pas de numéro de pièce dans la réponse.

        Il n'y a aucune raison de les réémettre : celui qui les a saisis les
        connaît, et chaque sortie d'identité est une sortie de trop.
        """
        reponse = self.client.post(
            "/api/groupeurs/", dossier_complet(), format="json"
        )
        for interdit in ("nom_complet", "telephone", "numero_mobile_money"):
            self.assertNotIn(interdit, reponse.data)

    def test_un_compte_mobile_money_au_nom_d_un_tiers_est_refuse(self) -> None:
        """**Le contrôle n° 2, celui qui arrête tout.**

        Il n'y a pas de bonne raison de recevoir l'argent des acheteurs sur le
        compte de quelqu'un d'autre. Et le message doit dire pourquoi, pas
        « champ invalide » : quelqu'un qui a saisi le compte de son conjoint
        doit comprendre que ce n'est pas une tracasserie.
        """
        reponse = self.client.post(
            "/api/groupeurs/",
            dossier_complet(titulaire_mobile_money="Afi Kossi"),
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("titulaire_mobile_money", reponse.data)
        self.assertIn("acheteurs", str(reponse.data["titulaire_mobile_money"]))
        self.assertFalse(Groupeur.objects.exists())

    def test_la_concordance_tolere_l_ordre_des_mots(self) -> None:
        """« ADJO Sika » et « Sika Adjo » sont la même personne.

        Refuser un dossier pour cela serait une perte de temps pour tout le
        monde, et un refus que le groupeur ne comprendrait pas.
        """
        reponse = self.client.post(
            "/api/groupeurs/",
            dossier_complet(titulaire_mobile_money="ADJO Sika"),
            format="json",
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)

    def test_un_dossier_sans_selfie_n_est_pas_examinable(self) -> None:
        """**Sans selfie, une pièce d'identité volée suffit** (contrôle n° 1).

        Le refus nomme la pièce manquante : « dossier incomplet » tout court
        obligerait le groupeur à deviner.
        """
        dossier = dossier_complet()
        dossier["pieces"] = [
            piece for piece in dossier["pieces"] if piece["nature"] != "selfie"
        ]
        reponse = self.client.post("/api/groupeurs/", dossier, format="json")

        self.assertEqual(reponse.status_code, 400)
        self.assertIn("selfie", str(reponse.data["pieces"]).lower())

    def test_le_courriel_reste_facultatif(self) -> None:
        """Une partie du cœur de cible n'en a pas, mais répond au téléphone.

        L'exiger écarterait exactement les commerçants qu'on cherche.
        """
        reponse = self.client.post(
            "/api/groupeurs/", dossier_complet(courriel=""), format="json"
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)

    def test_un_groupeur_suit_son_dossier_par_son_numero(self) -> None:
        self.client.post("/api/groupeurs/", dossier_complet(), format="json")
        reponse = self.client.get(
            "/api/groupeurs/dossier/", {"telephone": "+22890111222"}
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["etat"], "en-verification")
        self.assertEqual(reponse.data["pseudonyme"], "Chez Sika")
        # Même ici, aucun document ni numéro de pièce ne sort.
        self.assertNotIn("pieces", reponse.data)

    def test_un_numero_inconnu_donne_404_et_non_un_corps_vide(self) -> None:
        """« Ce dossier n'existe pas » et « il attend » sont deux écrans."""
        reponse = self.client.get(
            "/api/groupeurs/dossier/", {"telephone": "+22899999999"}
        )
        self.assertEqual(reponse.status_code, 404)


class ExamenParApi(SocleApi):
    def setUp(self) -> None:
        super().setUp()
        self.client.post("/api/groupeurs/", dossier_complet(), format="json")
        self.groupeur = Groupeur.objects.get(pseudonyme="Chez Sika")
        self.jeton_admin = self.ouvrir_l_administration()

    def entete(self) -> dict:
        return {"HTTP_X_JETON_ADMIN": self.jeton_admin}

    def test_la_file_des_dossiers_est_fermee_sans_jeton(self) -> None:
        """**Le point d'entrée le plus sensible du projet.**

        Il transporte des noms, des numéros de téléphone et des références de
        pièces d'identité. Le laisser sous le ``AllowAny`` du §1.5 parce que
        « l'authentification viendra plus tard » serait un choix, pas un oubli.
        """
        # ⚠️ **401 et non 403**, et la nuance n'est pas cosmétique : c'est
        # « je ne sais pas qui vous êtes », donc l'écran doit rouvrir la
        # feuille de connexion. `api/client.ts` s'appuie dessus avec
        # `estNonAuthentifie()`. Ces assertions attendaient 403, parce que
        # DRF dégrade le 401 en 403 faute de classe d'authentification — voir
        # `sessions_admin.SchemaAdmin`.
        self.assertEqual(self.client.get("/api/dossiers/").status_code, 401)
        self.assertEqual(
            self.client.get(
                "/api/dossiers/", **{"HTTP_X_JETON_ADMIN": "faux-jeton"}
            ).status_code,
            401,
        )

    def test_retirer_is_staff_ferme_les_sessions_en_cours(self) -> None:
        """⚠️ **Ce test en remplace un autre, qui n'a plus d'objet.**

        Il vérifiait que l'administration échouait fermée quand `JETON_ADMIN`
        manquait dans les réglages — le piège classique du secret partagé qui
        **ouvre** faute de configuration, le jour où le `.env` n'est pas
        déployé. Il n'y a plus de variable à oublier.

        Ce qui mérite un test à sa place, c'est la révocation, parce qu'elle
        est la seule chose que le jeton partagé ne savait pas faire : on ne
        pouvait retirer l'accès à une personne qu'en changeant le jeton de
        tout le monde.

        `is_staff` est donc revérifié **à chaque requête**, et pas seulement à
        la connexion. Sans cela, décocher la case laisserait la session vivre
        jusqu'à son expiration — douze heures pendant lesquelles quelqu'un
        qu'on vient de retirer continuerait à lire des pièces d'identité.
        """
        self.assertEqual(
            self.client.get("/api/dossiers/", **self.entete()).status_code, 200
        )

        compte = get_user_model().objects.get(username="ama")
        compte.is_staff = False
        compte.save(update_fields=["is_staff"])

        self.assertEqual(
            self.client.get("/api/dossiers/", **self.entete()).status_code, 401
        )

    def test_la_file_est_triee_du_plus_ancien_au_plus_recent(self) -> None:
        """Un dossier qui attend depuis six jours est un groupeur qui s'en va."""
        self.client.post(
            "/api/groupeurs/",
            dossier_complet(
                pseudonyme="Lomé Deals",
                nom_complet="Kodjo Amegan",
                telephone="+22890333444",
                titulaire_mobile_money="Kodjo Amegan",
                numero_mobile_money="+22890333444",
                courriel="kodjo@example.tg",
            ),
            format="json",
        )
        reponse = self.client.get("/api/dossiers/", **self.entete())
        pseudos = [ligne["pseudonyme"] for ligne in reponse.data["results"]]
        self.assertEqual(pseudos, ["Chez Sika", "Lomé Deals"])

    def test_l_administrateur_voit_la_concordance_sans_ouvrir_la_fiche(
        self,
    ) -> None:
        """Recalculée à l'affichage, pas lue depuis un champ figé au dépôt.

        Le compte Mobile Money peut avoir changé depuis — c'est le signal
        d'alerte numéro un du §10.5.
        """
        reponse = self.client.get(
            f"/api/dossiers/{self.groupeur.pk}/", **self.entete()
        )
        self.assertTrue(reponse.data["concordance_noms"])
        self.assertEqual(len(reponse.data["pieces"]), 3)

        self.groupeur.titulaire_mobile_money = "Afi Kossi"
        # On contourne `save` : le modèle refuserait, et c'est bien le but du
        # contrôle. Ici on simule un compte modifié hors parcours normal.
        Groupeur.objects.filter(pk=self.groupeur.pk).update(
            titulaire_mobile_money="Afi Kossi"
        )
        reponse = self.client.get(
            f"/api/dossiers/{self.groupeur.pk}/", **self.entete()
        )
        self.assertFalse(reponse.data["concordance_noms"])

    def test_une_validation_envoie_le_courriel_et_ouvre_les_droits(self) -> None:
        reponse = self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {"issue": "valide", "canal": "courriel", "decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )

        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertTrue(reponse.data["annonce"])
        self.assertIn("validé", reponse.data["sujet"])
        self.assertEqual(len(mail.outbox), 1)

        self.groupeur.refresh_from_db()
        self.assertTrue(self.groupeur.peut_lancer_une_campagne)

    def test_la_reponse_porte_le_texte_envoye_mot_pour_mot(self) -> None:
        """L'administrateur voit ce que le groupeur a reçu.

        Sans cela, il annonce une décision sans savoir comment elle a été
        formulée — et ne peut pas répondre quand le groupeur rappelle en
        citant le message.
        """
        reponse = self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {"issue": "valide", "canal": "courriel", "decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )
        self.assertEqual(reponse.data["corps"], mail.outbox[0].body)

    def test_un_refus_sans_motif_est_refuse_par_l_api(self) -> None:
        """La même règle qu'au modèle, mais en 400 et sur le bon champ."""
        reponse = self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {"issue": "refuse", "canal": "appel", "decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("motif", reponse.data)
        self.groupeur.refresh_from_db()
        self.assertEqual(
            self.groupeur.statut_kyc, Groupeur.StatutKyc.EN_VERIFICATION
        )

    def test_un_appel_rend_le_script_et_reste_a_annoncer(self) -> None:
        reponse = self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {
                "issue": "a-completer",
                "motif": "piece-illisible",
                "canal": "appel",
                "decide_par": "Kephira",
            },
            format="json",
            **self.entete(),
        )

        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertFalse(reponse.data["annonce"])
        self.assertIn("[Se présenter", reponse.data["script"])
        self.assertIsNone(reponse.data["decision"]["notifie_le"])
        self.assertEqual(len(mail.outbox), 0)

        # L'administrateur téléphone, puis l'acte.
        suite = self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/annonce-faite/",
            format="json",
            **self.entete(),
        )
        self.assertEqual(suite.status_code, 200)
        self.assertIsNotNone(suite.data["notifie_le"])

    def test_acter_deux_fois_l_annonce_ne_reecrit_pas_la_date(self) -> None:
        """Une date de journal ne se réécrit pas sur un double appui."""
        self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {
                "issue": "refuse",
                "motif": "doute-identite",
                "canal": "appel",
                "decide_par": "Kephira",
            },
            format="json",
            **self.entete(),
        )
        premier = self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/annonce-faite/",
            format="json",
            **self.entete(),
        ).data["notifie_le"]
        second = self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/annonce-faite/",
            format="json",
            **self.entete(),
        ).data["notifie_le"]
        self.assertEqual(premier, second)

    def test_le_groupeur_lit_le_motif_de_son_refus(self) -> None:
        """Un « refusé » sans motif est une porte fermée sans poignée.

        Et c'est ce qui génère l'appel au support qu'on cherchait à éviter.
        """
        self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {
                "issue": "a-completer",
                "motif": "selfie-non-conforme",
                "canal": "courriel",
                "decide_par": "Kephira",
            },
            format="json",
            **self.entete(),
        )
        reponse = self.client.get(
            "/api/groupeurs/dossier/", {"telephone": "+22890111222"}
        )

        self.assertEqual(reponse.data["etat"], "a-completer")
        self.assertIn("visibles ensemble", reponse.data["motif"])

    def test_le_groupeur_ne_lit_jamais_la_note_interne(self) -> None:
        """« Doute sérieux sur l'identité » se note, ne se dit pas.

        Le lui dire lui apprendrait quoi corriger pour recommencer.
        """
        self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {
                "issue": "refuse",
                "motif": "doute-identite",
                "canal": "appel",
                "decide_par": "Kephira",
            },
            format="json",
            **self.entete(),
        )
        reponse = self.client.get(
            "/api/groupeurs/dossier/", {"telephone": "+22890111222"}
        )
        self.assertNotIn("doute", reponse.data["motif"].lower())

    def test_la_fiche_publique_du_groupeur_ne_fuit_pas_apres_validation(
        self,
    ) -> None:
        """L'anonymat ne dépend pas de l'état du dossier (§1.7).

        Le courriel est un champ ajouté récemment : ce test existe pour qu'il
        ne se mette pas à sortir par une route acheteur.
        """
        self.client.post(
            f"/api/dossiers/{self.groupeur.pk}/decision/",
            {"issue": "valide", "canal": "courriel", "decide_par": "Kephira"},
            format="json",
            **self.entete(),
        )
        reponse = self.client.get(
            "/api/groupeurs/dossier/", {"telephone": "+22890111222"}
        )
        corps = str(reponse.data)
        for interdit in ("Sika Adjo", "sika@example.tg", "+22890111222"):
            self.assertNotIn(interdit, corps)
