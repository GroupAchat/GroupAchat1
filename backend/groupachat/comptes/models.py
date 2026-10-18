# -*- coding: utf-8 -*-
"""Acheteurs, groupeurs et dossiers KYC.

**La règle d'anonymat se joue ici, dans la forme même des modèles** (§1.7 de la
spec des écrans). Un acheteur a un nom et un numéro ; un groupeur a un
pseudonyme. Aucune relation ne permet à un groupeur de remonter d'une commande
vers l'acheteur qui l'a passée : il ne voit que le code de livraison et le
quartier, et c'est ce qui l'empêche de se constituer un fichier de clients à
servir hors plateforme, au même prix, et sans nous.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .. import domaine, notifications


class Acheteur(models.Model):
    """Un acheteur. Créé **à l'ouverture de l'écran de commande** (§1.5).

    ## ⚠️ Ce que ce modèle disait avant, et pourquoi ça a changé

    Il portait : *« Il n'y a ni mot de passe ni e-mail : un numéro et un code
    SMS suffisent. Chaque champ ajouté ici est un acheteur perdu à un écran du
    paiement. »* **C'est faux depuis que le compte acheteur est un vrai
    compte**, et la phrase est reproduite ici pour que personne ne la
    « restaure » en croyant réparer une régression.

    L'argument de fond restait juste, et il est respecté autrement : aucun des
    deux champs ajoutés n'est **demandé** pour commander.

    | Champ | Obligatoire ? | Demandé quand |
    |---|---|---|
    | ``telephone`` | oui | À l'ouverture de l'écran de commande |
    | ``mot_de_passe`` | **non** | Jamais à l'inscription — proposé depuis le profil |
    | ``courriel`` | **non** | Jamais — proposé depuis le profil |

    Le compte naît donc toujours d'un numéro et d'un code SMS, en un seul
    écran. Le mot de passe est ce qui le rend **réutilisable sans SMS** à la
    visite suivante, et le code SMS reste la voie de récupération — ce qui
    garantit qu'un mot de passe oublié ne ferme jamais un compte.

    ## ⚠️ Le mot de passe ne remplace pas le code, il s'y ajoute

    Les deux voies restent ouvertes en permanence. C'est ce qui permet de
    **verrouiller la voie du mot de passe** après quelques échecs (voir
    ``echecs_connexion``) sans jamais enfermer personne dehors : le code SMS,
    lui, a son propre compteur d'essais sur ``CodeConnexion``.

    ## L'adresse par défaut

    ``quartier`` et ``repere`` sont **la dernière adresse de livraison
    utilisée**, pas une adresse de facturation. Elle est enregistrée au moment
    du premier paiement — l'acheteur vient de la saisir à l'écran précédent,
    donc on ne lui demande rien de plus — et sert à pré-remplir les commandes
    suivantes.

    ⚠️ **Elle ne remplace jamais celle de la commande.** Chaque commande garde
    sa propre copie de la position (§6 du PRD) : on se fait livrer ailleurs un
    jour sur dix, et une commande qui lirait l'adresse du compte changerait
    rétroactivement de destination le jour où l'acheteur déménage. Le livreur
    doit voir l'adresse qui valait **au moment de la commande**.
    """

    telephone = models.CharField("téléphone", max_length=20, unique=True)
    nom = models.CharField("nom", max_length=120, blank=True)

    #: Facultatif, et il le restera.
    #:
    #: Le même raisonnement que pour ``Groupeur.courriel`` : une partie du
    #: cœur de cible à Lomé n'a pas d'adresse de messagerie consultée mais
    #: répond au téléphone. L'exiger écarterait ces gens-là, et le numéro
    #: étant obligatoire, l'acheteur reste toujours joignable.
    #:
    #: ⚠️ **Il n'identifie pas le compte et ne sert pas à se connecter.**
    #: C'est le numéro qui identifie, lui seul, et il est ``unique``. Deux
    #: comptes peuvent partager un courriel — une famille, une boutique — sans
    #: que rien ne casse, précisément parce qu'on ne s'en sert jamais pour
    #: retrouver qui que ce soit.
    courriel = models.EmailField("courriel", blank=True)

    #: Le mot de passe **haché**, ou une chaîne vide quand il n'y en a pas.
    #:
    #: Haché par ``django.contrib.auth.hashers.make_password``, donc avec
    #: l'algorithme et les itérations configurés par Django — jamais à la
    #: main. Le même mécanisme que ``CodeConnexion.code_hache``.
    #:
    #: ⚠️ **Vide signifie « aucun mot de passe », et doit être testé
    #: explicitement.** ``check_password`` contre une chaîne vide est faux pour
    #: toute entrée, donc le cas est sûr par accident ; mais le code qui
    #: ouvre une session doit refuser **avant** d'appeler le vérificateur, pour
    #: pouvoir répondre « ce compte n'a pas de mot de passe, demandez un
    #: code » au lieu de « mot de passe incorrect ». Les deux phrases
    #: n'envoient pas l'acheteur au même endroit.
    #:
    #: ``max_length=128`` : la longueur des empreintes de Django, la même que
    #: celle de son propre champ ``password``.
    mot_de_passe = models.CharField("mot de passe", max_length=128, blank=True)

    #: Les échecs **consécutifs** de connexion par mot de passe.
    #:
    #: ⚠️ **Sans ce compteur, la voie du mot de passe serait plus faible que
    #: celle qu'elle complète.** ``CodeConnexion`` meurt au bout de trois
    #: essais ; un mot de passe sans limite se devine à la machine, et un
    #: numéro togolais tient en huit chiffres, donc l'attaquant n'a même pas
    #: besoin de connaître sa cible.
    #:
    #: Remis à zéro à chaque réussite — par mot de passe **comme par code
    #: SMS**. La seconde remise à zéro est ce qui fait du code la voie de
    #: secours : quelqu'un de verrouillé pour avoir mal tapé son mot de passe
    #: reprend la main avec un SMS, sans attendre la fin du délai.
    echecs_connexion = models.PositiveSmallIntegerField(
        "échecs de connexion", default=0
    )

    #: Jusqu'à quand la connexion **par mot de passe** est refusée.
    #:
    #: ``None`` la plupart du temps. Le verrou ne ferme **que cette voie** : le
    #: code SMS reste accepté pendant toute sa durée, et c'est délibéré. Un
    #: verrou qui fermerait les deux voies offrirait à n'importe qui le moyen
    #: d'enfermer l'acheteur de son choix dehors, en se trompant exprès cinq
    #: fois sur un numéro qui n'est pas le sien.
    bloque_jusqu_a = models.DateTimeField(
        "bloqué jusqu'à", null=True, blank=True
    )

    #: La dernière adresse de livraison, pour pré-remplir la prochaine commande.
    quartier = models.CharField("quartier", max_length=40, blank=True)
    repere = models.CharField("repère", max_length=200, blank=True)

    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    #: ⚠️ **Présent pour DRF, qui place cet objet dans ``request.user``.**
    #:
    #: Un acheteur n'est pas un ``django.contrib.auth.User`` — il n'a ni mot de
    #: passe, ni permissions, ni groupes, et il ne doit surtout pas en avoir :
    #: ce sont deux populations différentes, et un acheteur ne doit jamais
    #: pouvoir ouvrir l'admin Django. Mais DRF interroge
    #: ``request.user.is_authenticated`` sur ce qu'une classe
    #: d'authentification lui rend, et sans cet attribut la lecture lève.
    #:
    #: C'est la manière documentée d'employer un modèle qui n'est pas le modèle
    #: utilisateur de Django. Elle vaut `True` en dur : une instance d'acheteur
    #: n'existe dans ``request.user`` que si un jeton valide l'y a mise.
    is_authenticated = True
    is_anonymous = False

    class Meta:
        verbose_name = "acheteur"
        verbose_name_plural = "acheteurs"
        ordering = ("-cree_le",)

    def __str__(self) -> str:
        return self.nom or self.telephone


class Groupeur(models.Model):
    """Un groupeur. **Les acheteurs n'en voient que le pseudonyme.**

    ``nom_complet`` existe pour le dossier KYC et l'administration ; il ne doit
    jamais sortir par une API destinée aux acheteurs. Les sérialiseurs du
    catalogue ne l'exposent pas, et un test le vérifie — c'est le genre de
    fuite qui s'introduit par un ``fields = "__all__"`` distrait.
    """

    class Niveau(models.TextChoices):
        ENTREE = "entree", "Entrée"
        CONFIRME = "confirme", "Confirmé"
        ETABLI = "etabli", "Établi"

    class StatutKyc(models.TextChoices):
        A_COMPLETER = "a-completer", "À compléter"
        EN_VERIFICATION = "en-verification", "En vérification"
        VALIDE = "valide", "Validé"
        REFUSE = "refuse", "Refusé"

    pseudonyme = models.CharField("pseudonyme", max_length=60, unique=True)
    nom_complet = models.CharField("nom complet", max_length=120)
    telephone = models.CharField("téléphone", max_length=20, unique=True)

    #: Par où on lui annonce la décision sur son dossier.
    #:
    #: **Facultatif, et ce n'est pas un oubli.** Une partie du cœur de cible —
    #: des commerçants de Lomé, souvent dans l'informel — n'a pas d'adresse de
    #: messagerie consultée, mais répond au téléphone. Exiger un courriel pour
    #: s'inscrire écarterait exactement ces gens-là, alors que le recrutement
    #: est le goulot d'étranglement du lancement (§10.5).
    #:
    #: Le téléphone étant obligatoire, un groupeur reste toujours joignable par
    #: au moins un canal : l'appel. Voir ``notifications.py``.
    courriel = models.EmailField("courriel", blank=True)

    niveau = models.CharField(
        "niveau de vérification",
        max_length=20,
        choices=Niveau.choices,
        default=Niveau.ENTREE,
    )
    statut_kyc = models.CharField(
        "statut du dossier",
        max_length=20,
        choices=StatutKyc.choices,
        default=StatutKyc.A_COMPLETER,
    )

    #: Le compte qui recevra les retraits. Son titulaire doit porter le même
    #: nom que la pièce d'identité — c'est le contrôle n° 2 du §10.5.
    titulaire_mobile_money = models.CharField(
        "titulaire du compte Mobile Money", max_length=120, blank=True
    )
    numero_mobile_money = models.CharField(
        "numéro Mobile Money", max_length=20, blank=True
    )

    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "groupeur"
        verbose_name_plural = "groupeurs"
        ordering = ("pseudonyme",)

    def __str__(self) -> str:
        return self.pseudonyme

    @property
    def plafond(self) -> Decimal | None:
        """Le plafond de collecte par campagne, déduit du niveau (§10.4).

        ``None`` au niveau Établi : il se décide au cas par cas, et le
        formulaire d'administration doit le demander plutôt que d'en inventer
        un.
        """
        return domaine.PLAFONDS_KYC[self.niveau]

    @property
    def peut_lancer_une_campagne(self) -> bool:
        """Un dossier non validé ne lance rien.

        C'est ce qui rend tenable « vous êtes livré, ou remboursé » : nous
        remboursons l'acheteur, puis nous nous retournons contre le groupeur —
        ce qui suppose un dossier examiné et opposable (§10.5).
        """
        return self.statut_kyc == self.StatutKyc.VALIDE

    @property
    def dossier_en_attente(self) -> bool:
        """Le dossier est déposé et attend un administrateur.

        C'est l'état dans lequel un groupeur passe le plus de temps, et celui
        que l'interface doit savoir dessiner : ni « validé », ni « refusé »,
        mais « quelqu'un regarde, revenez ».
        """
        return self.statut_kyc == self.StatutKyc.EN_VERIFICATION

    @property
    def derniere_decision(self) -> "DecisionKyc | None":
        """La dernière décision prise sur ce dossier, s'il y en a eu une.

        Sert à l'écran du groupeur, qui doit pouvoir afficher le motif d'un
        refus — un refus sans motif visible est une porte fermée sans poignée.
        """
        return self.decisions_kyc.first()

    # ── Le cycle de vie du dossier ──────────────────────────────────────────
    #
    # À compléter ──soumettre()──▶ En vérification ──trancher()──▶ Validé
    #      ▲                             │                        Refusé
    #      └────── trancher("a-completer")┘
    #
    # **Aucune transition n'est automatique.** Le §10.5 confie la décision à un
    # humain, et c'est le produit : « nous sélectionnons nos groupeurs » ne
    # vaut que si quelqu'un a réellement regardé le dossier.

    def soumettre_le_dossier(self) -> None:
        """Le groupeur dépose son dossier : il part en file d'attente.

        Idempotent sur un dossier déjà en vérification — un double appui sur
        « Envoyer » ne doit pas créer deux entrées dans la file de
        l'administrateur.
        """
        if self.statut_kyc == self.StatutKyc.VALIDE:
            raise ValidationError(
                "Ce dossier est déjà validé : il n'y a rien à soumettre."
            )
        if self.statut_kyc == self.StatutKyc.EN_VERIFICATION:
            return
        self.statut_kyc = self.StatutKyc.EN_VERIFICATION
        self.save()

    def trancher(
        self,
        issue: str,
        decide_par: str,
        canal: str,
        motif: str | None = None,
        niveau: str | None = None,
    ) -> "DecisionKyc":
        """Un administrateur décide, et la décision est tracée.

        Trois issues et non deux : ``a-completer`` renvoie le dossier au
        groupeur sans le refuser, et c'est l'issue la plus utile des trois — la
        plupart des dossiers qui échouent le font sur une photo floue, et les
        refuser définitivement pour cela ferait perdre des groupeurs
        recrutables.

        ⚠️ **Le motif est obligatoire dès que ce n'est pas une validation**, et
        la règle est vérifiée dans ``notifications.verifier`` plutôt qu'ici :
        l'interface d'administration l'applique avant même d'enregistrer, et
        les deux chemins doivent dire la même chose.

        La décision est enregistrée **sans être annoncée** : c'est
        ``DecisionKyc.marquer_notifie`` qui l'acte. La raison est écrite au
        long dans ``notifications.py`` — un refus annoncé par appel suppose que
        quelqu'un ait décroché le téléphone, et le journal ne doit pas
        prétendre le contraire.
        """
        if self.statut_kyc != self.StatutKyc.EN_VERIFICATION:
            raise ValidationError(
                "Seul un dossier en vérification peut être tranché."
            )

        notifications.verifier(issue, motif)

        if issue == "valide":
            self.niveau = niveau or self.Niveau.ENTREE
            self.statut_kyc = self.StatutKyc.VALIDE
        elif issue == "a-completer":
            self.statut_kyc = self.StatutKyc.A_COMPLETER
        elif issue == "refuse":
            self.statut_kyc = self.StatutKyc.REFUSE
        else:
            raise ValidationError(f"Issue inconnue : {issue}")

        # ⚠️ Voir `save` : sans ce drapeau, un dossier dont le compte Mobile
        # Money n'est pas au bon nom ne peut pas être refusé — alors que c'est
        # exactement le motif pour lequel on le refuse.
        self.save(verifier_concordance=False)

        return DecisionKyc.objects.create(
            groupeur=self,
            issue=issue,
            motif=motif or "",
            niveau_accorde=self.niveau if issue == "valide" else "",
            decide_par=decide_par,
            canal=canal,
        )

    def clean(self) -> None:
        """Contrôle KYC n° 2 — la procédure s'arrête si les noms divergent.

        ⚠️ **C'est une règle sur ce qu'un groupeur a le droit de *déposer*, pas
        sur ce qu'un administrateur a le droit d'*enregistrer*.** La nuance a
        coûté un bug sérieux, décrit dans ``save``.
        """
        super().clean()
        if self._verifier_concordance and self.titulaire_mobile_money and not domaine.noms_concordent(
            self.nom_complet, self.titulaire_mobile_money
        ):
            raise ValidationError(
                {
                    "titulaire_mobile_money": (
                        "Le titulaire du compte Mobile Money doit porter le même "
                        "nom que la pièce d'identité. L'argent des acheteurs ne "
                        "peut partir que sur un compte au nom du groupeur."
                    )
                }
            )

    #: Drapeau interne lu par ``clean``. Voir ``save``.
    _verifier_concordance = True

    def save(self, *args, verifier_concordance: bool = True, **kwargs):
        """Valide avant d'écrire — sauf quand on enregistre une sanction.

        ``full_clean`` n'est pas appelé automatiquement par ``save`` : sur un
        contrôle qui garde l'argent des acheteurs, on ne compte pas sur le fait
        que tous les appelants penseront à valider.

        ⚠️ **``verifier_concordance=False`` existe à cause d'un vrai bug, et
        il faut comprendre lequel avant d'y toucher.** Le contrôle n° 2 refuse
        un groupeur dont le compte Mobile Money n'est pas à son nom. Comme il
        s'appliquait à *toute* écriture, il rendait la ligne **impossible à
        modifier** une fois ce défaut présent — y compris pour y écrire
        ``statut_kyc = refuse``.

        Autrement dit : **le seul dossier qu'on ne pouvait pas refuser était
        celui qui devait l'être.** L'administrateur recevait un 400 portant le
        message du contrôle n° 2, ce qui avait toutes les apparences d'un refus
        justifié — c'est ce qui rendait le défaut difficile à voir.

        La règle reste donc entière là où elle sert, c'est-à-dire **à la
        saisie** : ``api_kyc.InscriptionSerializer`` la vérifie avant de créer
        quoi que ce soit, et l'interface d'administration la montre en rouge.
        Elle est seulement levée pour ``trancher``, qui n'écrit ni le nom ni le
        compte — seulement l'issue de l'examen.

        Un dossier peut entrer dans cet état de deux façons : par une
        modification du compte après le dépôt — qui est le signal d'alerte
        numéro un du §10.5 — ou par une correction manuelle en base. Dans les
        deux cas, il faut pouvoir le trancher.
        """
        self._verifier_concordance = verifier_concordance
        try:
            self.full_clean(exclude=None, validate_unique=False)
        finally:
            # Remis à la valeur sûre : l'objet peut être ré-enregistré plus
            # tard par un tout autre chemin, qui, lui, doit être contrôlé.
            self._verifier_concordance = True
        return super().save(*args, **kwargs)


class PieceKyc(models.Model):
    """Une pièce déposée par un groupeur — recto, verso, selfie, étal.

    ⚠️ **Aucun ``ImageField`` ici, et c'est délibéré.** Le §10.5 exige que les
    pièces d'identité et les selfies ne se trouvent **pas dans le même
    stockage que les photos de produits**, que l'accès soit restreint à
    l'administrateur, et qu'une durée de conservation soit fixée. Un
    ``ImageField`` les déposerait dans ``MEDIA_ROOT``, c'est-à-dire exactement
    là où elles ne doivent pas être, et sous une URL devinable.

    Ce modèle ne garde donc qu'une **référence opaque** vers un stockage à
    accès restreint, qui reste à mettre en place. Tant qu'il n'existe pas, ce
    champ porte un identifiant de démonstration : **la plateforme ne doit pas
    recevoir de vraie pièce d'identité avant** que le stockage et la durée de
    conservation soient tranchés.

    Durée de conservation : **à définir** (§10.5). Elle conditionne une tâche
    de purge qui n'est pas écrite.
    """

    class Nature(models.TextChoices):
        PIECE_RECTO = "piece-recto", "Pièce d'identité — recto"
        PIECE_VERSO = "piece-verso", "Pièce d'identité — verso"
        SELFIE = "selfie", "Selfie tenant la pièce"
        ETAL = "etal", "Lieu d'activité"
        JUSTIFICATIF = "justificatif", "Justificatif d'activité"

    groupeur = models.ForeignKey(
        Groupeur,
        on_delete=models.CASCADE,
        related_name="pieces",
        verbose_name="groupeur",
    )
    nature = models.CharField("nature", max_length=20, choices=Nature.choices)

    #: La clé dans le stockage à accès restreint. Jamais une URL publique.
    reference = models.CharField("référence de stockage", max_length=200)

    depose_le = models.DateTimeField("déposée le", auto_now_add=True)

    class Meta:
        verbose_name = "pièce KYC"
        verbose_name_plural = "pièces KYC"
        ordering = ("groupeur", "nature")
        # Une pièce par nature : redéposer un recto remplace l'ancien, il ne
        # s'ajoute pas. Sinon l'administrateur examine une pile et ne sait plus
        # laquelle est la bonne.
        constraints = [
            models.UniqueConstraint(
                fields=["groupeur", "nature"], name="une_piece_par_nature"
            )
        ]

    def __str__(self) -> str:
        return f"{self.groupeur.pseudonyme} — {self.get_nature_display()}"


class DecisionKyc(models.Model):
    """Une décision d'administrateur sur un dossier KYC, et son annonce.

    **C'est une pièce de journal, pas un champ d'état.** Le statut courant vit
    sur le groupeur ; ce modèle garde *qui* a décidé, *quand*, *pourquoi*, et
    *par quel canal* le groupeur l'a appris. Le §18.3 l'exige pour les
    mouvements d'argent, et un dossier KYC relève de la même logique : c'est
    lui qu'on relit le jour d'un litige, ou le jour où un groupeur écarté
    revient demander pourquoi.

    Les lignes ne sont **jamais modifiées ni supprimées** : un dossier repris
    produit une nouvelle décision, qui n'effface pas la précédente. L'histoire
    d'un dossier est ce qui permet de voir qu'un groupeur en est à sa troisième
    tentative.
    """

    groupeur = models.ForeignKey(
        Groupeur,
        on_delete=models.CASCADE,
        related_name="decisions_kyc",
        verbose_name="groupeur",
    )

    class Issue(models.TextChoices):
        VALIDE = "valide", "Validé"
        A_COMPLETER = "a-completer", "À compléter"
        REFUSE = "refuse", "Refusé"

    class Canal(models.TextChoices):
        COURRIEL = "courriel", "Courriel"
        APPEL = "appel", "Appel téléphonique"

    issue = models.CharField("issue", max_length=20, choices=Issue.choices)

    #: Un des motifs de ``notifications.MOTIFS``. Vide sur une validation.
    #:
    #: Liste fermée plutôt que texte libre : au bout de six mois, un champ
    #: libre contient quarante formulations du même refus, et on ne peut plus
    #: compter pourquoi les dossiers échouent — donc plus corriger le
    #: formulaire d'inscription qui les fait échouer.
    motif = models.CharField("motif", max_length=40, blank=True)

    niveau_accorde = models.CharField("niveau accordé", max_length=20, blank=True)

    #: Qui a décidé.
    #:
    #: ⚠️ Un nom en clair, parce qu'il n'y a **pas encore d'authentification**
    #: dans ce projet. Le jour où l'administration en aura une, ce champ
    #: devient une clé étrangère vers l'utilisateur, et cette ligne disparaît.
    #: En l'état, il repose sur la bonne foi de celui qui le remplit : ça
    #: suffit pour une démonstration, **pas pour un journal opposable**.
    decide_par = models.CharField("décidé par", max_length=120)

    decide_le = models.DateTimeField("décidé le", auto_now_add=True)

    canal = models.CharField(
        "canal d'annonce", max_length=20, choices=Canal.choices
    )

    #: Quand le groupeur a réellement été prévenu. ``None`` = pas encore.
    #:
    #: Séparé de ``decide_le`` parce que les deux instants diffèrent : le
    #: courriel part dans la seconde, l'appel attend qu'un humain décroche. Un
    #: dossier tranché mais non annoncé est un dossier dont le groupeur ne sait
    #: rien — l'administration doit pouvoir les lister.
    notifie_le = models.DateTimeField("annoncé le", null=True, blank=True)

    class Meta:
        verbose_name = "décision KYC"
        verbose_name_plural = "décisions KYC"
        ordering = ("-decide_le",)

    def __str__(self) -> str:
        return f"{self.groupeur.pseudonyme} — {self.get_issue_display()}"

    @property
    def libelle_motif(self) -> str:
        """Le motif tel que l'administrateur le lit. Vide sur une validation."""
        return notifications.libelle_interne(self.motif) if self.motif else ""

    def composer(self) -> tuple[str, str] | str:
        """Le message à envoyer, ou le script à lire au téléphone.

        Le texte n'est **pas stocké**. Le stocker figerait une formulation
        qu'on corrige encore, et ferait croire qu'on peut relire mot pour mot
        ce qui a été envoyé — ce qui serait faux pour un appel. Ce qui est
        tracé, c'est la décision et son motif ; le texte s'en déduit.
        """
        plafond = self.groupeur.plafond
        plafond_entier = int(plafond) if plafond is not None else None

        if self.canal == self.Canal.APPEL:
            return notifications.script_appel(
                self.groupeur.pseudonyme, self.issue, self.motif or None, plafond_entier
            )
        if self.issue == self.Issue.VALIDE:
            return notifications.message_validation(
                self.groupeur.pseudonyme, plafond_entier
            )
        return notifications.message_decision_negative(
            self.groupeur.pseudonyme, self.issue, self.motif
        )

    def marquer_notifie(self) -> None:
        """Acte que le groupeur a été prévenu.

        ⚠️ **À n'appeler qu'après l'avoir réellement été** — courriel parti, ou
        téléphone décroché. Cocher cette case sans appeler produirait un
        journal qui dit le contraire de ce qui s'est passé, et c'est ce journal
        qu'on produira le jour d'un litige.
        """
        self.notifie_le = timezone.now()
        self.save(update_fields=["notifie_le"])


# ── Les comptes acheteurs : code SMS et session ─────────────────────────────


class CodeConnexion(models.Model):
    """Le code à quatre chiffres envoyé par SMS, et ses garde-fous.

    ## Pourquoi un modèle, et pas une constante

    Parce qu'un code de connexion a trois propriétés que seule une ligne en
    base peut porter : il **expire**, il se **consomme**, et il n'autorise
    qu'un **nombre fini d'essais**. Un code figé dans le code source n'en a
    aucune — et c'est exactement ce qui faisait de l'écran 4 une simulation.

    **Ce qui manque encore est l'envoi**, pas la vérification. Group Achat n'a
    pas de fournisseur SMS (§18.2) : le code est généré, stocké et contrôlé
    pour de bon, mais il ne part nulle part. En développement il vaut
    ``CODE_SMS_DEMONSTRATION`` et l'écran le dit, plutôt que de laisser
    chercher.

    ⚠️ **Le serveur refuse de servir ce code quand ``DEBUG`` est faux.** Mettre
    en ligne avec un code fixe donnerait à n'importe qui le compte de n'importe
    quel numéro — c'est le genre de réglage de développement qui part en
    production parce que rien ne l'arrête. Ici, quelque chose l'arrête.

    ## Sur le hachage

    Le code est haché, et il faut dire franchement ce que ça vaut : **quatre
    chiffres, c'est dix mille possibilités**, qu'un attaquant ayant la base
    épuise instantanément. Le hachage ne protège donc pas d'une fuite de base,
    il évite seulement que des codes en vol traînent en clair dans des
    sauvegardes et des journaux. **La vraie protection est le compteur
    d'essais** : trois, puis le code est mort.
    """

    #: Dix minutes. Assez pour recevoir un SMS et le recopier, trop court pour
    #: qu'un code lu par-dessus l'épaule serve le lendemain.
    DUREE_MINUTES = 10

    #: Trois essais, puis le code est mort et il faut en redemander un.
    ESSAIS_MAXIMUM = 3

    telephone = models.CharField("téléphone", max_length=20, db_index=True)
    code_hache = models.CharField("code haché", max_length=128)
    essais = models.PositiveSmallIntegerField("essais", default=0)
    #: Mis à `True` dès qu'il a ouvert une session : un code ne sert qu'une fois.
    consomme = models.BooleanField("consommé", default=False)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)
    expire_le = models.DateTimeField("expire le")

    class Meta:
        verbose_name = "code de connexion"
        verbose_name_plural = "codes de connexion"
        ordering = ("-cree_le",)

    def __str__(self) -> str:
        return f"{self.telephone} — {self.cree_le:%d/%m %H:%M}"

    @property
    def utilisable(self) -> bool:
        return (
            not self.consomme
            and self.essais < self.ESSAIS_MAXIMUM
            and timezone.now() < self.expire_le
        )


class SessionAcheteur(models.Model):
    """La session qui reconnaît l'acheteur à sa prochaine visite.

    ## Pourquoi un jeton, et pas le numéro de téléphone

    Jusqu'ici l'API identifiait l'acheteur par **son numéro, passé en paramètre
    d'URL**. C'était commode et c'était un trou : qui connaît un numéro lit les
    commandes qui vont avec. Retenir ce numéro dans le navigateur pour
    reconnecter les gens automatiquement aurait rendu ce trou permanent.

    Un jeton change trois choses, et les trois comptent :

    | | Le numéro | Le jeton |
    |---|---|---|
    | Se devine | **oui**, huit chiffres | non, 256 bits |
    | Expire | jamais | oui |
    | Se révoque | impossible | oui, et sans changer de numéro |

    C'est le minimum qu'on doive à quelqu'un dont on garde l'adresse et
    l'historique d'achats.

    ⚠️ **Ce n'est toujours pas un mot de passe.** Le jeton vit dans le
    navigateur ; qui a l'appareil déverrouillé a le compte. C'est le compromis
    assumé d'un produit dont le §1.5 interdit le mur d'authentification — on ne
    peut pas à la fois ne rien demander à l'entrée et exiger un secret à chaque
    visite.
    """

    #: Trente jours **glissants** : chaque usage repousse l'échéance. Un acheteur
    #: qui commande tous les mois n'a jamais à refaire le code SMS ; un appareil
    #: abandonné finit par ne plus ouvrir le compte.
    DUREE_JOURS = 30

    acheteur = models.ForeignKey(
        Acheteur,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="acheteur",
    )
    #: Le jeton lui-même. **Indexé et unique** : il est lu à chaque requête.
    jeton = models.CharField("jeton", max_length=64, unique=True, db_index=True)

    cree_le = models.DateTimeField("ouverte le", auto_now_add=True)
    expire_le = models.DateTimeField("expire le")
    dernier_usage = models.DateTimeField("dernier usage", auto_now_add=True)

    class Meta:
        verbose_name = "session acheteur"
        verbose_name_plural = "sessions acheteurs"
        ordering = ("-dernier_usage",)

    def __str__(self) -> str:
        return f"{self.acheteur} — jusqu'au {self.expire_le:%d/%m/%Y}"

    @property
    def valide(self) -> bool:
        return timezone.now() < self.expire_le

    def prolonger(self) -> None:
        """Repousse l'échéance — la fenêtre glissante.

        ⚠️ **Au plus une écriture par heure.** Prolonger à chaque requête
        ferait un `UPDATE` par appel d'API, soit une écriture pour chaque
        vignette affichée. L'heure est un compromis : la session glisse bien,
        et la base n'est pas sollicitée pour rien.
        """
        maintenant = timezone.now()
        if maintenant - self.dernier_usage < timedelta(hours=1):
            return
        self.dernier_usage = maintenant
        self.expire_le = maintenant + timedelta(days=self.DUREE_JOURS)
        self.save(update_fields=["dernier_usage", "expire_le"])


# ── L'administration, et ses vrais comptes ────────────────────────


class SessionAdmin(models.Model):
    """La session d'un administrateur, ouverte contre un mot de passe.

    ## Ce qu'elle remplace

    ⚠️ **Ces routes étaient gardées par un jeton unique et partagé**, lu dans
    l'en-tête ``X-Jeton-Admin`` et posé dans le ``.env`` du serveur. Le code
    qui le portait le disait lui-même : *« ce n'est pas de l'authentification,
    et il ne faut pas le prendre pour telle »*. Trois défauts concrets :

    | | Le jeton partagé | La session |
    |---|---|---|
    | Distingue deux administrateurs | non | **oui** |
    | Se révoque pour une personne | non — il faut le changer pour tous | **oui** |
    | ``décidé par`` sur une décision KYC | la bonne foi du formulaire | **le compte qui décide** |

    Le troisième est le plus grave, et il n'est pas cosmétique : le §10.5
    confie la validation d'un dossier à un humain parce que, le jour d'un
    litige, **le dossier est notre seul recours contre le groupeur**. Un
    journal dont l'auteur est un champ de texte libre ne prouve rien.

    ## Pourquoi un jeton de session et non la session Django

    Le client d'administration est une application React servie à part, qui
    parle à l'API par ``fetch`` depuis une autre origine. Les cookies de
    session traverseraient, mais au prix de ``SESSION_COOKIE_SAMESITE=None``,
    de CORS avec identifiants et d'une protection CSRF à câbler sur chaque
    écriture. Un jeton porté par un en-tête n'est pas envoyé automatiquement
    par le navigateur : **il n'y a donc pas de CSRF à couvrir.** Et il se lit
    exactement comme la session acheteur, un mécanisme de moins à comprendre.

    ## ⚠️ Douze heures, pas trente jours

    ``SessionAcheteur`` dure trente jours **glissants**, et c'est justifié là :
    refaire un code SMS à chaque visite ferait perdre des acheteurs. Ici le
    raisonnement s'inverse — ces routes montrent **des noms, des numéros de
    téléphone et des références de pièces d'identité**. Une session qui
    survit un mois sur un portable emporté est une fuite qui attend.

    Douze heures couvrent une journée de travail : on se connecte le matin, on
    ne se reconnecte pas à midi. Et **elle ne glisse pas** : l'échéance est
    posée à l'ouverture et ne bouge plus, sinon une session qu'on garde
    ouverte ne finit jamais.
    """

    #: Douze heures fermes. Voir la note de classe : ce n'est pas la durée de
    #: la session acheteur, et l'écart est délibéré.
    DUREE_HEURES = 12

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions_admin",
        verbose_name="administrateur",
    )
    #: Indexé et unique : il est lu à chaque requête d'administration.
    jeton = models.CharField("jeton", max_length=64, unique=True, db_index=True)

    cree_le = models.DateTimeField("ouverte le", auto_now_add=True)
    expire_le = models.DateTimeField("expire le")
    dernier_usage = models.DateTimeField("dernier usage", auto_now_add=True)

    class Meta:
        verbose_name = "session administrateur"
        verbose_name_plural = "sessions administrateurs"
        ordering = ("-dernier_usage",)

    def __str__(self) -> str:
        return f"{self.utilisateur} — jusqu'à {self.expire_le:%d/%m à %Hh%M}"

    @property
    def valide(self) -> bool:
        return timezone.now() < self.expire_le

    def marquer_usage(self) -> None:
        """Note le dernier usage, **sans repousser l'échéance**.

        ⚠️ La différence avec ``SessionAcheteur.prolonger`` est tout le sujet :
        là-bas l'échéance glisse, ici elle est ferme. Ce champ ne sert donc
        qu'à voir, dans l'admin Django, quelles sessions sont actives — ce
        qu'il faut savoir avant d'en révoquer une.

        Au plus une écriture par heure, comme côté acheteur : sinon chaque
        appel d'API coûte un ``UPDATE``.
        """
        maintenant = timezone.now()
        if maintenant - self.dernier_usage < timedelta(hours=1):
            return
        self.dernier_usage = maintenant
        self.save(update_fields=["dernier_usage"])


class VerrouAdmin(models.Model):
    """Le compteur d'échecs de connexion à l'administration.

    ## ⚠️ Pourquoi un modèle séparé, et pas deux champs sur ``User``

    ``Acheteur`` porte ses propres ``echecs_connexion`` et ``bloque_jusqu_a``.
    Ici on ne peut pas : ``User`` est le modèle de Django, et lui ajouter des
    colonnes demanderait de le remplacer par un modèle maison — une migration
    lourde et irréversible, pour deux entiers.

    ## ⚠️ Et pourquoi la clé est l'identifiant **saisi**, pas le compte

    Compter les échecs sur le compte trouvé ne protège que les comptes qui
    existent. Un identifiant inconnu n'aurait alors **aucune limite**, et la
    différence de comportement entre « inconnu, essaie encore » et « connu,
    verrouillé » révélerait quels identifiants existent. En comptant sur la
    chaîne saisie, les deux cas se verrouillent pareil et ne disent rien.

    Conséquence assumée : qui connaît l'identifiant d'un collègue peut le
    verrouiller quinze minutes en se trompant cinq fois exprès. C'est le défaut
    de tout verrou par identifiant, et le prix est plus faible que l'inverse.
    """

    #: Cinq, comme pour l'acheteur — voir ``sessions.ECHECS_AVANT_VERROU`` pour
    #: le raisonnement, qui vaut ici aussi.
    ECHECS_AVANT_VERROU = 5

    #: Quinze minutes. ⚠️ Mais sans la soupape du côté acheteur : là-bas le
    #: code SMS reste ouvert pendant le verrou, donc personne n'est fermé
    #: dehors. Ici **il n'y a pas d'autre porte** : un administrateur
    #: verrouillé attend, ou un autre lui lève le verrou depuis l'admin Django.
    #: C'est pour ça que le verrou est court.
    DUREE_VERROU_MINUTES = 15

    identifiant = models.CharField(
        "identifiant saisi", max_length=150, unique=True, db_index=True
    )
    echecs = models.PositiveSmallIntegerField("échecs consécutifs", default=0)
    bloque_jusqu_a = models.DateTimeField(
        "bloqué jusqu'à", null=True, blank=True
    )

    class Meta:
        verbose_name = "verrou d'administration"
        verbose_name_plural = "verrous d'administration"
        ordering = ("-bloque_jusqu_a",)

    def __str__(self) -> str:
        return f"{self.identifiant} — {self.echecs} échec(s)"

    @property
    def est_bloque(self) -> bool:
        return (
            self.bloque_jusqu_a is not None
            and timezone.now() < self.bloque_jusqu_a
        )
