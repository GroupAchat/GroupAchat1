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
        ADMINISTRATEUR = "administrateur", "Administrateur"

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

    def __str__(self) -> str:
        return f"{self.prenom} {self.nom} ({self.telephone})"

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

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


class CodeVerification(models.Model):
    """Code à six chiffres envoyé par SMS pour vérifier un numéro.

    En mode prototype il n'est pas envoyé mais affiché à l'écran ; le reste de
    la mécanique — expiration, usage unique, nombre d'essais — est bien réel.
    """

    MAX_TENTATIVES = 5

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
        """Crée un code neuf et périme les précédents du même utilisateur."""
        cls.objects.filter(utilisateur=utilisateur, consomme_le__isnull=True).update(
            expire_le=timezone.now()
        )
        maintenant = timezone.now()
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
    """Note de confiance d'un groupeur, alimentée par son activité réelle.

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
    litiges = models.PositiveIntegerField("litiges constatés", default=0)
    participants_servis = models.PositiveIntegerField("participants servis", default=0)
    note = models.DecimalField("note sur 5", max_digits=3, decimal_places=2, default=0)
    mise_a_jour_le = models.DateTimeField("mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "réputation"
        verbose_name_plural = "réputations"

    def __str__(self) -> str:
        return f"{self.groupeur.nom_complet} — {self.note}/5"
