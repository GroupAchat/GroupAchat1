# -*- coding: utf-8 -*-
"""Participations à une campagne, codes de retrait et avis.

La **participation** est la pièce maîtresse du produit : c'est elle qui porte
l'argent consigné et le code qui vaut preuve de livraison.
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from groupachat.catalogue.models import Campagne

# Alphabet du code de retrait : chiffres et majuscules, sans les caractères
# qu'on confond à l'oral ou sur un écran fissuré (0/O, 1/I/L, 2/Z, 5/S, 8/B).
ALPHABET_CODE = "34679ACDEFGHJKMNPQRTUVWXY"
LONGUEUR_CODE = 8


def engendrer_code_retrait() -> str:
    return "".join(secrets.choice(ALPHABET_CODE) for _ in range(LONGUEUR_CODE))


class Participation(models.Model):
    """La part d'un acheteur dans une campagne."""

    class ModeRetrait(models.TextChoices):
        """Comment cet acheteur-là récupère son colis.

        **Le choix est à lui, pas à l'OAG.** Un point de remise unique fixé
        par celui qui groupe obligeait la moitié de la ville à traverser Lomé
        pour un sac de riz, et ne disait rien à qui voulait être livré. Deux
        chemins, donc : le bureau de poste le plus proche de chez lui, ou sa
        porte.

        Les **frais de livraison ne passent pas par la plateforme** : ils sont
        fixés par l'agence et payés à la livraison. Les encaisser nous
        obligerait à les reverser, donc à les connaître d'avance — alors
        qu'ils dépendent du quartier et de ce que pèse le colis.
        """

        POSTE = "poste", "Retrait au bureau de poste"
        LIVRAISON = "livraison", "Livraison à l'adresse"

    class Statut(models.TextChoices):
        EN_ATTENTE_PAIEMENT = "en_attente_paiement", "En attente de paiement"
        PAYEE = "payee", "Payée, fonds consignés"
        PRETE = "prete", "Prête à être retirée"
        RETIREE = "retiree", "Retirée"
        REMBOURSEE = "remboursee", "Remboursée"
        ANNULEE = "annulee", "Annulée"

    # Participations dont l'argent est effectivement consigné : ce sont les
    # seules qui comptent dans la jauge et dans le montant collecté.
    STATUTS_PAYES = (Statut.PAYEE, Statut.PRETE, Statut.RETIREE)

    campagne = models.ForeignKey(
        Campagne,
        on_delete=models.PROTECT,
        related_name="participations",
        verbose_name="campagne",
    )
    acheteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="participations",
        verbose_name="acheteur",
    )
    quantite = models.PositiveIntegerField("quantité", default=1)

    # Le prix est figé à la commande plutôt que relu sur la campagne : un
    # palier franchi plus tard ne doit pas changer ce qui a déjà été payé.
    prix_unitaire_applique = models.PositiveIntegerField("prix unitaire appliqué (FCFA)")
    montant_total = models.PositiveIntegerField("montant total (FCFA)")

    statut = models.CharField(
        "statut",
        max_length=25,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE_PAIEMENT,
    )

    mode_retrait = models.CharField(
        "mode de retrait",
        max_length=10,
        choices=ModeRetrait.choices,
        default=ModeRetrait.POSTE,
    )
    bureau_poste = models.CharField(
        "bureau de poste",
        max_length=120,
        blank=True,
        help_text="Le bureau le plus proche de chez l'acheteur.",
    )
    # L'adresse n'est **jamais servie à l'OAG** : il ne connaît pas ses
    # acheteurs, et une adresse de livraison dit où ils dorment. C'est
    # l'agence partenaire qui la reçoit, elle seule.
    adresse_livraison = models.CharField(
        "adresse de livraison", max_length=250, blank=True
    )

    # Le code n'existe qu'une fois la part payée : le créer plus tôt
    # laisserait circuler un code qui ne donne droit à rien.
    code_retrait = models.CharField(
        "code de retrait", max_length=LONGUEUR_CODE, unique=True, null=True, blank=True
    )
    # Le code OTP SMS envoyé à l'acheteur pour valider l'achat et servir
    # de solution de secours à la remise si le QR code ne passe pas.
    code_otp_sms = models.CharField(
        "code OTP SMS", max_length=6, blank=True, default=""
    )

    cree_le = models.DateTimeField("commandée le", default=timezone.now)
    payee_le = models.DateTimeField("payée le", null=True, blank=True)
    retiree_le = models.DateTimeField("retirée le", null=True, blank=True)
    remise_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="remises_effectuees",
        verbose_name="remise par",
        help_text="Qui a validé le code au point de retrait.",
    )

    class Meta:
        verbose_name = "participation"
        verbose_name_plural = "participations"
        ordering = ["-cree_le"]
        indexes = [
            models.Index(fields=["campagne", "statut"]),
            models.Index(fields=["acheteur", "statut"]),
        ]
        constraints = [
            # Une destination vide ne se rattrape pas : le colis est déjà
            # parti quand on s'en aperçoit. La base refuse donc le choix
            # sans son complément, et pas seulement le formulaire.
            models.CheckConstraint(
                condition=(
                    models.Q(mode_retrait="poste") & ~models.Q(bureau_poste="")
                )
                | (
                    models.Q(mode_retrait="livraison")
                    & ~models.Q(adresse_livraison="")
                ),
                name="la_destination_du_colis_est_renseignee",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.acheteur.nom_complet} — {self.quantite} × {self.campagne.titre}"

    def attribuer_code_retrait(self) -> str:
        """Tire un code libre et un code OTP SMS et les attache à la participation."""
        if not self.code_otp_sms:
            self.code_otp_sms = f"{secrets.randbelow(1_000_000):06d}"
        if self.code_retrait:
            return self.code_retrait
        for _ in range(10):
            candidat = engendrer_code_retrait()
            if not Participation.objects.filter(code_retrait=candidat).exists():
                self.code_retrait = candidat
                return candidat
        raise RuntimeError("Impossible d'attribuer un code de retrait libre.")

    @property
    def charge_qr(self) -> str:
        """Ce que contient le QR code présenté au point de retrait.

        Le code seul ne suffirait pas : il faut que le scan dise **de quelle
        campagne** il s'agit, sans quoi un code valide d'une autre campagne
        passerait pour bon devant un groupeur pressé. La charge lie donc le
        produit et le participant, et le lecteur refuse un identifiant de
        campagne qui n'est pas le sien.

        Le code reste lisible à l'œil dans la charge, à dessein : un téléphone
        dont l'appareil photo ne marche pas doit pouvoir le dicter.
        """
        if not self.code_retrait:
            raise ValueError("Pas de QR tant que la part n'est pas payée.")
        return f"GA|{self.campagne_id}|{self.code_retrait}"

    @property
    def peut_etre_notee(self) -> bool:
        """Un avis ne se laisse qu'une fois le groupage joué.

        Avant la clôture il n'y a rien à juger : la campagne n'a pas encore
        montré si elle allait aboutir. Après, il y a toujours quelque chose
        à dire — y compris quand rien n'a été livré, et c'est précisément
        là que la note compte le plus.
        """
        if self.statut == self.Statut.EN_ATTENTE_PAIEMENT:
            return False
        return self.campagne.statut in Campagne.STATUTS_COLLECTE_CLOSE

    @property
    def destination(self) -> str:
        """Où va ce colis, en une ligne, pour l'acheteur et les écrans."""
        if self.mode_retrait == self.ModeRetrait.LIVRAISON:
            return f"Livraison — {self.adresse_livraison}"
        return f"Bureau de poste — {self.bureau_poste}"

    @property
    def destination_pour_l_oag(self) -> str:
        """La même chose, **sans l'adresse**.

        Un bureau de poste est un lieu public : le nommer ne dit rien de
        personne. Une adresse de livraison, elle, désigne un domicile — et
        l'OAG ne connaît pas ses acheteurs. Il n'a pas besoin de plus : c'est
        l'agence qui livre, lui remet le lot en bloc.
        """
        if self.mode_retrait == self.ModeRetrait.LIVRAISON:
            return "Livraison par l'agence"
        return f"Bureau de poste — {self.bureau_poste}"

    @property
    def delai_retrait_depasse(self) -> bool:
        """Quatorze jours après la mise à disposition, la livraison est acquise."""
        depuis = self.campagne.mise_a_disposition_le
        if depuis is None or self.statut != self.Statut.PRETE:
            return False
        return (timezone.now() - depuis).days >= 14


class Avis(models.Model):
    """La note qu'un acheteur laisse à son OAG.

    **Group Achat met en relation, elle n'arbitre pas.** Un souci sur un
    produit se règle entre l'acheteur et l'OAG — par le Contact Privé, et par
    cette note. La plateforme garantit l'argent de la collecte, pas la
    qualité de la marchandise.

    C'est pour cette raison qu'il n'y a pas de dossier de litige à
    instruire : la sanction d'un mauvais OAG n'est pas une décision
    d'arbitre, c'est sa réputation qui baisse et les acheteurs qui le
    voient.

    Un avis est rattaché à **une participation**, et non à une campagne :
    seul quelqu'un qui a payé peut noter, une seule fois, et on sait
    toujours de quelle commande il parle.
    """

    participation = models.OneToOneField(
        Participation,
        on_delete=models.CASCADE,
        related_name="avis",
        verbose_name="participation",
    )
    note = models.PositiveSmallIntegerField(
        "note sur 5",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    commentaire = models.TextField("commentaire", max_length=1000, blank=True)
    cree_le = models.DateTimeField("laissé le", default=timezone.now)
    modifie_le = models.DateTimeField("modifié le", null=True, blank=True)

    # L'OAG répond une fois, sous l'avis. Pas un fil : un droit de réponse.
    # Au-delà, l'échange passe par le Contact Privé — il n'existe aucune
    # discussion publique sous une campagne.
    reponse = models.TextField("réponse de l'OAG", blank=True)
    repondu_le = models.DateTimeField("répondu le", null=True, blank=True)

    class Meta:
        verbose_name = "avis"
        verbose_name_plural = "avis"
        ordering = ["-cree_le"]
        indexes = [models.Index(fields=["-cree_le"])]

    def __str__(self) -> str:
        return f"{self.note}/5 — {self.participation}"

    @property
    def groupeur(self):
        return self.participation.campagne.groupeur


class Reclamation(models.Model):
    """Réclamation ou litige sur une participation.

    Conforme au nouveau cahier des charges : 7 typologies d'incidents
    et procédure de règlement en 5 étapes.
    """

    class Motif(models.TextChoices):
        NON_LIVRAISON = "non_livraison", "Non-livraison"
        RETARD = "retard", "Retard de livraison"
        NON_CONFORME = "non_conforme", "Produit non conforme"
        INCOMPLETE = "incomplete", "Commande incomplète"
        MINIMUM_NON_ATTEINT = "minimum_non_atteint", "Minimum non atteint"
        PAIEMENT_CONTESTE = "paiement_conteste", "Paiement contesté"
        FRAUDE = "fraude", "Suspicion de fraude"

    class Etape(models.TextChoices):
        OUVERTURE = "ouverture", "1. Ouverture"
        ACCUSE_RECEPTION = "accuse_reception", "2. Accusé de réception"
        CONTRADICTOIRE = "contradictoire", "3. Phase contradictoire"
        ANALYSE = "analyse", "4. Analyse du dossier"
        DECISION = "decision", "5. Décision et recours"
        CLOS = "clos", "Clôturé"

    numero_dossier = models.CharField(
        "numéro de dossier", max_length=30, unique=True
    )
    participation = models.ForeignKey(
        Participation,
        on_delete=models.CASCADE,
        related_name="reclamations",
        verbose_name="participation",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reclamations_ouvertes",
        verbose_name="demandeur",
    )
    motif = models.CharField("motif de l'incident", max_length=30, choices=Motif.choices)
    description = models.TextField("description des faits")
    piece_jointe = models.FileField(
        "pièce justificative", upload_to="reclamations/", blank=True
    )
    etape = models.CharField(
        "étape de traitement",
        max_length=30,
        choices=Etape.choices,
        default=Etape.OUVERTURE,
    )
    reponse_oag = models.TextField("réponse et justificatifs de l'OAG", blank=True)
    decision = models.TextField("décision motivée de la plateforme", blank=True)
    remboursement_accorde = models.PositiveIntegerField(
        "remboursement accordé (FCFA)", default=0
    )
    cree_le = models.DateTimeField("ouvert le", default=timezone.now)
    mis_a_jour_le = models.DateTimeField("mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "réclamation"
        verbose_name_plural = "réclamations"
        ordering = ["-cree_le"]

    def __str__(self) -> str:
        return f"{self.numero_dossier} ({self.get_motif_display()}) — {self.participation}"

    @classmethod
    def engendrer_numero(cls, participation_id: int) -> str:
        annee = timezone.now().year
        suffixe = secrets.token_hex(2).upper()
        return f"REC-{annee}-{participation_id:04d}-{suffixe}"


