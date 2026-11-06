# -*- coding: utf-8 -*-
"""Comptes, vérification du numéro et dossiers KYC.

Le **numéro de téléphone est l'identifiant** : au Togo, tout le monde en a un,
peu de gens ont une adresse e-mail. L'e-mail reste facultatif, utile seulement
pour les reçus et la récupération de mot de passe.

Les montants de toute l'application sont des **entiers de francs CFA** : le
FCFA n'a pas de subdivision, un décimal n'apporterait que des erreurs
d'arrondi.
"""

from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from . import grades, noms

# Numéros togolais : 8 chiffres, éventuellement précédés de l'indicatif +228.
# Volontairement permissif — la vérification par SMS tranche pour de bon.
validateur_telephone = RegexValidator(
    r"^(\+228)?\d{8}$",
    "Numéro invalide : huit chiffres, éventuellement précédés de +228.",
)


class GestionnaireUtilisateur(BaseUserManager):
    """Création des comptes à partir du numéro de téléphone."""

    use_in_migrations = True

    def _creer(self, telephone, mot_de_passe, **champs):
        if not telephone:
            raise ValueError("Le numéro de téléphone est obligatoire.")
        utilisateur = self.model(telephone=self.normaliser_telephone(telephone), **champs)
        utilisateur.set_password(mot_de_passe)
        utilisateur.save(using=self._db)
        return utilisateur

    @staticmethod
    def normaliser_telephone(telephone: str) -> str:
        """Ne garde que les huit chiffres significatifs du numéro.

        Sans ça, « 90001122 » et « +22890001122 » créeraient deux comptes pour
        la même personne, et l'un des deux ne retrouverait jamais ses commandes.
        """
        nu = "".join(c for c in (telephone or "") if c.isdigit())
        return nu[-8:] if len(nu) > 8 else nu

    def create_user(self, telephone, mot_de_passe=None, **champs):
        champs.setdefault("role", Utilisateur.Role.ACHETEUR)
        champs.setdefault("est_equipe", False)
        champs.setdefault("is_superuser", False)
        return self._creer(telephone, mot_de_passe, **champs)

    def create_superuser(self, telephone, mot_de_passe=None, **champs):
        champs.setdefault("role", Utilisateur.Role.ADMINISTRATEUR)
        champs.setdefault("est_equipe", True)
        champs.setdefault("is_superuser", True)
        champs.setdefault("telephone_verifie", True)
        if not champs["est_equipe"] or not champs["is_superuser"]:
            raise ValueError("Un administrateur doit être membre de l'équipe.")
        return self._creer(telephone, mot_de_passe, **champs)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """Un compte, quel que soit le rôle tenu."""

    class Role(models.TextChoices):
        ACHETEUR = "acheteur", "Acheteur"
        GROUPEUR = "groupeur", "Groupeur"
        # Le partenaire qui porte les colis — La Poste, Gozem. C'est lui qui
        # scanne le code de retrait, et personne d'autre : l'OAG remet le lot
        # en bloc à l'agence et ne rencontre jamais ses acheteurs.
        LIVREUR = "livreur", "Livreur partenaire"
        ADMINISTRATEUR = "administrateur", "Administrateur"

    class Transporteur(models.TextChoices):
        POSTE = "poste", "La Poste"
        GOZEM = "gozem", "Gozem"
        AUTRE = "autre", "Autre partenaire"

    telephone = models.CharField(
        "téléphone",
        max_length=8,
        unique=True,
        validators=[validateur_telephone],
    )
    nom = models.CharField("nom", max_length=80)
    prenom = models.CharField("prénom", max_length=80)
    email = models.EmailField("adresse e-mail", blank=True)
    role = models.CharField("rôle", max_length=20, choices=Role.choices, default=Role.ACHETEUR)

    # ── Le nom sous lequel on existe pour l'autre partie ──────────────────
    #
    # Obligatoire pour un groupeur, facultatif pour un acheteur. `null` et non
    # chaîne vide : la contrainte d'unicité doit laisser passer plusieurs
    # acheteurs sans nom, et seul NULL échappe à l'unicité en SQL.
    nom_utilisateur = models.CharField(
        "nom d'utilisateur",
        max_length=noms.LONGUEUR_MAX,
        null=True,
        blank=True,
        unique=True,
        validators=[noms.valider],
    )
    # La forme comparable, tenue à jour par `save()`. Sans elle, « Faya-02 »
    # et « faya02 » passeraient pour deux noms différents alors qu'aucun
    # acheteur ne les distinguerait.
    # Attribué au premier partage, pas à l'inscription : la plupart des
    # comptes ne parraineront jamais (voir `parrainage.code_de`).
    # Rempli pour les seuls livreurs : c'est ce que lit l'acheteur quand son
    # colis est remis — « remis par La Poste » dit quelque chose, le nom d'un
    # livreur inconnu ne dit rien.
    transporteur = models.CharField(
        "transporteur",
        max_length=10,
        choices=Transporteur.choices,
        blank=True,
    )
    code_parrainage = models.CharField(
        "code de parrainage", max_length=12, null=True, blank=True, unique=True
    )
    nom_utilisateur_repere = models.CharField(
        "forme comparable du nom d'utilisateur",
        max_length=noms.LONGUEUR_MAX,
        null=True,
        blank=True,
        unique=True,
        editable=False,
    )

    # Tant que le numéro n'est pas vérifié, le compte existe mais ne peut
    # ni commander ni déposer de dossier KYC.
    telephone_verifie = models.BooleanField("numéro vérifié", default=False)

    est_actif = models.BooleanField("compte actif", default=True)
    est_equipe = models.BooleanField("membre de l'équipe", default=False)
    date_inscription = models.DateTimeField("inscrit le", default=timezone.now)

    objects = GestionnaireUtilisateur()

    USERNAME_FIELD = "telephone"
    REQUIRED_FIELDS = ["nom", "prenom"]

    # Django attend les noms anglais is_active / is_staff un peu partout
    # (admin, permissions, authentification). On les expose en alias plutôt
    # que de renommer les champs, pour garder le français en base.
    @property
    def is_active(self) -> bool:
        return self.est_actif

    @is_active.setter
    def is_active(self, valeur: bool) -> None:
        self.est_actif = valeur

    @property
    def is_staff(self) -> bool:
        return self.est_equipe

    @is_staff.setter
    def is_staff(self, valeur: bool) -> None:
        self.est_equipe = valeur

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["-date_inscription"]

    def save(self, *args, **kwargs):
        # La forme comparable n'est jamais saisie : elle se déduit, toujours,
        # sinon deux enregistrements finiraient par ne plus se correspondre.
        nu = (self.nom_utilisateur or "").strip() or None
        self.nom_utilisateur = nu
        self.nom_utilisateur_repere = noms.normaliser(nu) if nu else None
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.prenom} {self.nom} ({self.telephone})"

    @property
    def nom_complet(self) -> str:
        """Le nom civil. **Réservé à l'intéressé, à l'équipe et au Contact Privé.**

        Il ne doit jamais partir dans une réponse publique : c'est
        `nom_public` qui sert partout ailleurs.
        """
        return f"{self.prenom} {self.nom}".strip()

    @property
    def nom_public(self) -> str:
        """Ce sous quoi on apparaît pour tout le monde.

        Un groupeur a toujours un nom d'utilisateur, validé avec son dossier.
        Un acheteur qui n'en a pas choisi retombe sur son prénom et une
        initiale — assez pour qu'on sache à qui on répond, pas assez pour le
        retrouver.
        """
        return self.nom_utilisateur or noms.nom_de_repli(self.prenom, self.nom)

    @property
    def est_groupeur_valide(self) -> bool:
        """Vrai seulement si le dossier KYC a été validé.

        C'est la condition d'accès à l'espace groupeur : sans elle, l'interface
        n'est pas accessible du tout, pas seulement la publication.
        """
        dossier = getattr(self, "dossier_kyc", None)
        return (
            self.role == self.Role.GROUPEUR
            and dossier is not None
            and dossier.statut == DossierKYC.Statut.VALIDE
        )


class TropDeCodes(Exception):
    """Trop de codes de vérification demandés pour un même numéro."""


class CodeVerification(models.Model):
    """Code à six chiffres envoyé par SMS pour vérifier un numéro.

    En mode prototype il n'est pas envoyé mais affiché à l'écran ; le reste de
    la mécanique — expiration, usage unique, nombre d'essais — est bien réel.
    """

    MAX_TENTATIVES = 5

    # Nombre de codes qu'un compte peut recevoir en une heure.
    #
    # ⚠️ **C'est la limite qui tient réellement.** Celle des cinq essais ne
    # vaut que *par code* : sans ce plafond, il suffisait d'en redemander un
    # neuf pour repartir à zéro, et un code à six chiffres finissait par
    # tomber. Comptée en base, elle résiste au redémarrage et ne dépend pas
    # du nombre de processus, contrairement à une limite tenue en cache.
    MAX_CODES_PAR_HEURE = 5

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="codes_verification",
        verbose_name="utilisateur",
    )
    code = models.CharField("code", max_length=6)
    cree_le = models.DateTimeField("créé le", default=timezone.now)
    expire_le = models.DateTimeField("expire le")
    consomme_le = models.DateTimeField("consommé le", null=True, blank=True)
    tentatives = models.PositiveSmallIntegerField("essais", default=0)

    class Meta:
        verbose_name = "code de vérification"
        verbose_name_plural = "codes de vérification"
        ordering = ["-cree_le"]

    def __str__(self) -> str:
        return f"Code pour {self.utilisateur.telephone}"

    @classmethod
    def emettre(cls, utilisateur) -> "CodeVerification":
        """Crée un code neuf et périme les précédents du même utilisateur.

        Lève :class:`TropDeCodes` au-delà de :attr:`MAX_CODES_PAR_HEURE`.
        """
        maintenant = timezone.now()
        recents = cls.objects.filter(
            utilisateur=utilisateur, cree_le__gte=maintenant - timedelta(hours=1)
        ).count()
        if recents >= cls.MAX_CODES_PAR_HEURE:
            raise TropDeCodes(
                "Trop de codes demandés pour ce numéro. Réessayez dans une heure."
            )

        cls.objects.filter(utilisateur=utilisateur, consomme_le__isnull=True).update(
            expire_le=maintenant
        )
        return cls.objects.create(
            utilisateur=utilisateur,
            # secrets et non random : c'est le seul rempart contre quelqu'un
            # qui chercherait à deviner le code d'un autre numéro.
            code=f"{secrets.randbelow(1_000_000):06d}",
            cree_le=maintenant,
            expire_le=maintenant + timedelta(minutes=settings.VALIDITE_CODE_SMS_MINUTES),
        )

    @property
    def est_utilisable(self) -> bool:
        return (
            self.consomme_le is None
            and self.tentatives < self.MAX_TENTATIVES
            and timezone.now() < self.expire_le
        )


class DossierKYC(models.Model):
    """Pièces justificatives d'un groupeur et décision de l'administrateur."""

    class TypePiece(models.TextChoices):
        CNI = "cni", "Carte nationale d'identité"
        PASSEPORT = "passeport", "Passeport"
        CARTE_CONSULAIRE = "carte_consulaire", "Carte consulaire"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente de vérification"
        VALIDE = "valide", "Validé"
        REJETE = "rejete", "Rejeté"

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dossier_kyc",
        verbose_name="groupeur",
    )
    type_piece = models.CharField("type de pièce", max_length=20, choices=TypePiece.choices)
    numero_piece = models.CharField("numéro de la pièce", max_length=50)
    # Facultatives au niveau du modèle : la démonstration doit pouvoir
    # dérouler un parcours KYC sans qu'on téléverse une vraie pièce
    # d'identité. L'interface, elle, les réclame.
    piece_recto = models.ImageField("pièce (recto)", upload_to="kyc/", blank=True)
    piece_verso = models.ImageField("pièce (verso)", upload_to="kyc/", blank=True)

    # Le numéro qui recevra les décaissements. Souvent différent du numéro de
    # connexion, d'où un champ à part plutôt qu'une réutilisation.
    numero_mobile_money = models.CharField(
        "numéro Mobile Money", max_length=8, validators=[validateur_telephone]
    )
    nom_commerce = models.CharField("nom du commerce", max_length=120, blank=True)

    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    motif_rejet = models.TextField("motif du rejet", blank=True)
    depose_le = models.DateTimeField("déposé le", default=timezone.now)
    decide_le = models.DateTimeField("décidé le", null=True, blank=True)
    decide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dossiers_kyc_decides",
        verbose_name="décidé par",
    )

    class Meta:
        verbose_name = "dossier KYC"
        verbose_name_plural = "dossiers KYC"
        ordering = ["depose_le"]

    def __str__(self) -> str:
        return f"KYC de {self.utilisateur.nom_complet} — {self.get_statut_display()}"


class Reputation(models.Model):
    """Note de confiance d'un groupeur.

    **La note vient des acheteurs, pas de la plateforme.** Group Achat met
    en relation ; elle ne juge pas la qualité d'un produit. Ce qu'elle
    tient, c'est la moyenne des avis et le volume d'activité — à l'acheteur
    de faire la part des choses entre « 5/5 sur un avis » et « 4,2 sur
    quarante ».

    Les compteurs sont stockés plutôt que recalculés à l'affichage : ils
    apparaissent sur chaque vignette du catalogue, et refaire les agrégats à
    chaque fois coûterait une requête par vignette.
    """

    groupeur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reputation",
        verbose_name="groupeur",
    )
    campagnes_terminees = models.PositiveIntegerField("campagnes menées à terme", default=0)
    campagnes_annulees = models.PositiveIntegerField("campagnes annulées", default=0)
    avis_recus = models.PositiveIntegerField("avis reçus", default=0)
    participants_servis = models.PositiveIntegerField("participants servis", default=0)
    note = models.DecimalField("note sur 5", max_digits=3, decimal_places=2, default=0)
    mise_a_jour_le = models.DateTimeField("mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "réputation"
        verbose_name_plural = "réputations"

    def __str__(self) -> str:
        return f"{self.groupeur.nom_complet} — {self.note}/5"


class ChangementNomUtilisateur(models.Model):
    """Trace d'un nom d'utilisateur abandonné.

    Le nom d'utilisateur **ne change pas** une fois validé : la note, les avis
    et le nombre de groupages aboutis y sont attachés, et le laisser changer
    offrirait à un groupeur un moyen simple d'effacer un mauvais historique.
    Un administrateur peut malgré tout le modifier — homonymie, nom retenu par
    erreur, demande justifiée —, et c'est précisément pour ces cas qu'il faut
    pouvoir remonter à l'ancien.
    """

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="anciens_noms",
        verbose_name="utilisateur",
    )
    ancien_nom = models.CharField("ancien nom d'utilisateur", max_length=noms.LONGUEUR_MAX)
    nouveau_nom = models.CharField("nouveau nom d'utilisateur", max_length=noms.LONGUEUR_MAX)
    motif = models.CharField("motif", max_length=200)
    decide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="changements_de_nom_decides",
        verbose_name="décidé par",
    )
    decide_le = models.DateTimeField("décidé le", default=timezone.now)

    class Meta:
        verbose_name = "changement de nom d'utilisateur"
        verbose_name_plural = "changements de nom d'utilisateur"
        ordering = ["-decide_le"]

    def __str__(self) -> str:
        return f"{self.ancien_nom} → {self.nouveau_nom}"


class CompteurPoints(models.Model):
    """Les points d'un compte, tenus sur **deux compteurs et non un seul**.

    Les points servent à deux choses qui ne peuvent pas partager le même
    solde : ils **mesurent** un parcours — c'est le grade du groupeur, c'est
    l'accès de l'acheteur au Contact Privé — et ils **s'échangent** contre des
    avantages. Avec un compteur unique, dépenser ses points ferait perdre son
    grade, et personne ne dépenserait jamais rien.

    D'où la même séparation que les compagnies aériennes font entre les miles
    de statut et les miles à dépenser :

    - `cumules` ne descend jamais et décide du grade ;
    - `solde` monte aux mêmes occasions et baisse à chaque dépense.
    """

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="points",
        verbose_name="utilisateur",
    )
    cumules = models.PositiveIntegerField("points cumulés", default=0)
    solde = models.PositiveIntegerField("solde de points", default=0)
    mise_a_jour_le = models.DateTimeField("mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "compteur de points"
        verbose_name_plural = "compteurs de points"
        constraints = [
            # Le solde ne peut pas dépasser le cumul : il n'existe aucun
            # chemin légitime pour ça, et une telle ligne signalerait un bug
            # d'attribution plutôt qu'un cas métier.
            models.CheckConstraint(
                condition=models.Q(solde__lte=models.F("cumules")),
                name="solde_jamais_superieur_au_cumul",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.utilisateur.nom_public} — {self.solde}/{self.cumules} points"

    @property
    def grade(self) -> str:
        """Le grade que donnent les points cumulés."""
        return grades.grade_pour(self.cumules)

    @property
    def commission_centiemes(self) -> int:
        return grades.commission_centiemes(self.grade)


class MouvementPoints(models.Model):
    """Une attribution ou une dépense de points, et sa cause.

    Chaque mouvement porte **l'événement qui l'a produit**, et une contrainte
    d'unicité interdit qu'un même événement en produise deux. Sans elle, un
    double appel — une requête rejouée, une tâche relancée — doublerait les
    points, et un groupeur pourrait monter en grade en faisant échouer puis
    rejouer un paiement.
    """

    class Motif(models.TextChoices):
        ACHAT = "achat", "Achat payé"
        GROUPAGE_ABOUTI = "groupage_abouti", "Groupage mené à son terme"
        PARRAINAGE = "parrainage", "Parrainage validé"
        ABONNEMENT_PUBLICATION = "abonnement_publication", "Mois de publication payé"
        PACK_PUBLICATION = "pack_publication", "Pack de publication payé"
        CONTACT_PRIVE = "contact_prive", "Mois de Contact Privé payé"
        DEPENSE = "depense", "Dépense de points"
        CORRECTION = "correction", "Correction administrative"

    compteur = models.ForeignKey(
        CompteurPoints,
        on_delete=models.CASCADE,
        related_name="mouvements",
        verbose_name="compteur",
    )
    motif = models.CharField("motif", max_length=30, choices=Motif.choices)
    # Négatif pour une dépense : le signe porte le sens, et la somme des
    # mouvements doit pouvoir se recouper avec le solde.
    points = models.IntegerField("points")

    # L'événement d'origine : « participation », « campagne », « abonnement »…
    # et son identifiant. Deux colonnes plutôt qu'une clé étrangère, parce
    # qu'elles désignent des tables différentes.
    origine_genre = models.CharField("genre de l'origine", max_length=30)
    origine_id = models.PositiveIntegerField("identifiant de l'origine")

    cree_le = models.DateTimeField("enregistré le", default=timezone.now)

    class Meta:
        verbose_name = "mouvement de points"
        verbose_name_plural = "mouvements de points"
        ordering = ["-cree_le"]
        constraints = [
            models.UniqueConstraint(
                fields=["compteur", "motif", "origine_genre", "origine_id"],
                name="un_evenement_n_attribue_qu_une_fois",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.points:+d} points — {self.get_motif_display()}"


# Déclaré à part — le parrainage est un sujet à lui seul — mais réexporté
# ici, parce que c'est `models` que Django inspecte.
from groupachat.comptes.parrainage import Parrainage  # noqa: E402
