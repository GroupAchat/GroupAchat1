# -*- coding: utf-8 -*-
"""Séquestre, mouvements d'argent et décaissements.

En mode prototype aucun franc ne bouge réellement : les opérateurs Mobile
Money ne sont pas branchés, et ce sont des actions de l'interface qui font
avancer les états. La **comptabilité est en revanche tenue pour de vrai**, de
sorte que brancher un agrégateur plus tard ne touche qu'à l'exécution.

Règle d'or : un séquestre ne doit jamais libérer plus qu'il n'a consigné.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Participation


class Operateur(models.TextChoices):
    TMONEY = "tmoney", "T-Money (Togocom)"
    FLOOZ = "flooz", "Flooz (Moov Africa)"
    ESPECES = "especes", "Espèces"


class Sequestre(models.Model):
    """Le compte de consignation d'une campagne.

    Un séquestre par campagne, et non un solde global : c'est ce qui permet
    de dire, à tout instant, de quelle campagne provient chaque franc détenu.
    """

    class Statut(models.TextChoices):
        OUVERT = "ouvert", "Ouvert, collecte en cours"
        BLOQUE = "bloque", "Bloqué, collecte close"
        LIBERE = "libere", "Libéré au groupeur"
        REMBOURSE = "rembourse", "Remboursé aux participants"

    campagne = models.OneToOneField(
        Campagne,
        on_delete=models.CASCADE,
        related_name="sequestre",
        verbose_name="campagne",
    )
    montant_consigne = models.PositiveIntegerField("montant consigné (FCFA)", default=0)
    montant_libere = models.PositiveIntegerField("montant libéré (FCFA)", default=0)
    montant_rembourse = models.PositiveIntegerField("montant remboursé (FCFA)", default=0)
    statut = models.CharField(
        "statut", max_length=15, choices=Statut.choices, default=Statut.OUVERT
    )
    ouvert_le = models.DateTimeField("ouvert le", default=timezone.now)
    solde_le = models.DateTimeField("soldé le", null=True, blank=True)

    class Meta:
        verbose_name = "séquestre"
        verbose_name_plural = "séquestres"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    montant_libere__lte=models.F("montant_consigne"),
                ),
                name="sequestre_ne_libere_pas_plus_que_consigne",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    montant_rembourse__lte=models.F("montant_consigne"),
                ),
                name="sequestre_ne_rembourse_pas_plus_que_consigne",
            ),
        ]

    def __str__(self) -> str:
        return f"Séquestre de « {self.campagne.titre} » — {self.solde} FCFA"

    @property
    def solde(self) -> int:
        """Ce qui reste détenu pour le compte de la campagne."""
        return self.montant_consigne - self.montant_libere - self.montant_rembourse


class Transaction(models.Model):
    """Un mouvement d'argent rattaché à une participation.

    Encaissement quand l'acheteur paie sa part, remboursement quand la
    campagne échoue. Les deux sens vivent dans la même table : c'est le
    journal qui doit se relire d'un seul tenant en cas de contestation.
    """

    class Sens(models.TextChoices):
        ENCAISSEMENT = "encaissement", "Encaissement"
        REMBOURSEMENT = "remboursement", "Remboursement"

    class Statut(models.TextChoices):
        INITIEE = "initiee", "Initiée"
        CONFIRMEE = "confirmee", "Confirmée"
        ECHOUEE = "echouee", "Échouée"

    participation = models.ForeignKey(
        Participation,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="participation",
    )
    sens = models.CharField("sens", max_length=15, choices=Sens.choices)
    montant = models.PositiveIntegerField("montant (FCFA)")
    operateur = models.CharField("opérateur", max_length=10, choices=Operateur.choices)
    numero = models.CharField("numéro Mobile Money", max_length=8, blank=True)

    # Référence rendue par l'opérateur. En prototype, une référence factice
    # est fabriquée pour que les écrans montrent un vrai justificatif.
    reference = models.CharField("référence", max_length=40, blank=True)
    simulee = models.BooleanField(
        "transaction simulée",
        default=True,
        help_text="Vrai tant qu'aucun opérateur réel n'est branché.",
    )

    statut = models.CharField(
        "statut", max_length=12, choices=Statut.choices, default=Statut.INITIEE
    )
    cree_le = models.DateTimeField("créée le", default=timezone.now)
    confirmee_le = models.DateTimeField("confirmée le", null=True, blank=True)
    motif_echec = models.TextField("motif de l'échec", blank=True)

    class Meta:
        verbose_name = "transaction"
        verbose_name_plural = "transactions"
        ordering = ["-cree_le"]
        indexes = [models.Index(fields=["participation", "sens", "statut"])]

    def __str__(self) -> str:
        return f"{self.get_sens_display()} de {self.montant} FCFA — {self.get_statut_display()}"


class Decaissement(models.Model):
    """Remise des fonds d'une campagne au groupeur.

    Un seul décaissement par campagne : le groupeur retire **100 % en une
    fois**, moins les frais fixes. Les frais sont recopiés ici plutôt que lus
    dans les réglages à l'affichage, pour qu'un changement de tarif ne
    réécrive pas l'histoire des retraits déjà faits.
    """

    class Statut(models.TextChoices):
        DEMANDE = "demande", "Demandé par le groupeur"
        APPROUVE = "approuve", "Approuvé"
        EXECUTE = "execute", "Exécuté"
        REFUSE = "refuse", "Refusé"

    campagne = models.OneToOneField(
        Campagne,
        on_delete=models.PROTECT,
        related_name="decaissement",
        verbose_name="campagne",
    )
    montant_brut = models.PositiveIntegerField("montant collecté (FCFA)")
    frais = models.PositiveIntegerField("frais de plateforme (FCFA)")
    montant_net = models.PositiveIntegerField("montant versé (FCFA)")
    numero_mobile_money = models.CharField("numéro destinataire", max_length=8)
    operateur = models.CharField("opérateur", max_length=10, choices=Operateur.choices)

    statut = models.CharField(
        "statut", max_length=12, choices=Statut.choices, default=Statut.DEMANDE
    )
    demande_le = models.DateTimeField("demandé le", default=timezone.now)
    execute_le = models.DateTimeField("exécuté le", null=True, blank=True)
    execute_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decaissements_executes",
        verbose_name="exécuté par",
    )
    reference = models.CharField("référence", max_length=40, blank=True)
    motif_refus = models.TextField("motif du refus", blank=True)

    class Meta:
        verbose_name = "décaissement"
        verbose_name_plural = "décaissements"
        ordering = ["-demande_le"]

    def __str__(self) -> str:
        return f"Décaissement de « {self.campagne.titre} » — {self.montant_net} FCFA"

    @staticmethod
    def calculer(montant_brut: int) -> tuple[int, int]:
        """Rend (frais, montant net) pour un montant collecté.

        Si la collecte est inférieure aux frais — cas théorique, mais le
        calcul ne doit pas rendre de net négatif — les frais sont ramenés au
        montant disponible.
        """
        frais = min(settings.FRAIS_PLATEFORME_FCFA, montant_brut)
        return frais, montant_brut - frais
