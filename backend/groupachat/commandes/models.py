# -*- coding: utf-8 -*-
"""Participations à une campagne, codes de retrait et litiges.

La **participation** est la pièce maîtresse du produit : c'est elle qui porte
l'argent consigné et le code qui vaut preuve de livraison.
"""

from __future__ import annotations

import secrets

from django.conf import settings
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

    # Le code n'existe qu'une fois la part payée : le créer plus tôt
    # laisserait circuler un code qui ne donne droit à rien.
    code_retrait = models.CharField(
        "code de retrait", max_length=LONGUEUR_CODE, unique=True, null=True, blank=True
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

    def __str__(self) -> str:
        return f"{self.acheteur.nom_complet} — {self.quantite} × {self.campagne.titre}"

    def attribuer_code_retrait(self) -> str:
        """Tire un code libre et l'attache à la participation.

        La collision est très improbable mais pas impossible, et la contrainte
        d'unicité ferait échouer le paiement d'un acheteur innocent : on
        retente quelques fois plutôt que de laisser passer l'erreur.
        """
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
    def delai_retrait_depasse(self) -> bool:
        """Quatorze jours après la mise à disposition, la livraison est acquise."""
        depuis = self.campagne.mise_a_disposition_le
        if depuis is None or self.statut != self.Statut.PRETE:
            return False
        return (timezone.now() - depuis).days >= 14


class Litige(models.Model):
    """Contestation ouverte par un acheteur sur sa participation.

    Un code de retrait validé ferme le litige : c'est la protection promise au
    groupeur contre les fausses réclamations.
    """

    class Motif(models.TextChoices):
        NON_LIVRE = "non_livre", "Produit jamais remis"
        NON_CONFORME = "non_conforme", "Produit non conforme"
        ENDOMMAGE = "endommage", "Produit endommagé"
        AUTRE = "autre", "Autre"

    class Statut(models.TextChoices):
        OUVERT = "ouvert", "Ouvert"
        EN_EXAMEN = "en_examen", "En cours d'examen"
        RESOLU_ACHETEUR = "resolu_acheteur", "Tranché en faveur de l'acheteur"
        RESOLU_GROUPEUR = "resolu_groupeur", "Tranché en faveur du groupeur"
        CLOS = "clos", "Clos"

    participation = models.ForeignKey(
        Participation,
        on_delete=models.CASCADE,
        related_name="litiges",
        verbose_name="participation",
    )
    motif = models.CharField("motif", max_length=20, choices=Motif.choices)
    description = models.TextField("description")
    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.OUVERT
    )
    ouvert_le = models.DateTimeField("ouvert le", default=timezone.now)
    resolu_le = models.DateTimeField("résolu le", null=True, blank=True)
    decision = models.TextField("décision", blank=True)
    arbitre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="litiges_arbitres",
        verbose_name="arbitré par",
    )

    class Meta:
        verbose_name = "litige"
        verbose_name_plural = "litiges"
        ordering = ["-ouvert_le"]

    def __str__(self) -> str:
        return f"Litige {self.get_motif_display()} — {self.participation}"
