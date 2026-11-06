# -*- coding: utf-8 -*-
"""Espace communautaire, Contact Privé et notifications.

Les demandes de produit renversent le sens habituel : ce ne sont plus les
OAG qui proposent, ce sont les acheteurs qui réclament. Le compteur
d'intérêt sert de signal aux OAG en quête d'une campagne à lancer.

⚠️ **Il n'existe aucune discussion publique.** Le fil ouvert sous une
campagne a été retiré : il laissait convenir d'un arrangement direct à la vue
de tous, et hors de la plateforme ni le séquestre ni l'assurance ne jouent.
Le seul échange possible passe par le Contact Privé, payant, et c'est lui qui
ouvre l'identité de l'OAG — voir `contact_prive.py`.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from groupachat.catalogue.models import Campagne


class DemandeProduit(models.Model):
    """Un produit qu'un acheteur aimerait voir proposé en achat groupé."""

    class Statut(models.TextChoices):
        OUVERTE = "ouverte", "Ouverte"
        PRISE_EN_CHARGE = "prise_en_charge", "Prise en charge par un groupeur"
        SATISFAITE = "satisfaite", "Satisfaite"
        FERMEE = "fermee", "Fermée"

    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="demandes_produit",
        verbose_name="auteur",
    )
    titre = models.CharField("produit recherché", max_length=160)
    description = models.TextField("précisions", blank=True)
    categorie = models.ForeignKey(
        "catalogue.Categorie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes",
        verbose_name="catégorie",
    )
    budget_indicatif = models.PositiveIntegerField(
        "budget indicatif (FCFA)", null=True, blank=True
    )
    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.OUVERTE
    )

    # Dénormalisé : l'espace communautaire se trie par intérêt décroissant, et
    # compter les intérêts à chaque tri coûterait une jointure par ligne.
    nombre_interets = models.PositiveIntegerField("intéressés", default=0)

    campagne_issue = models.ForeignKey(
        Campagne,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes_a_l_origine",
        verbose_name="campagne issue de la demande",
    )
    cree_le = models.DateTimeField("publiée le", default=timezone.now)

    class Meta:
        verbose_name = "demande de produit"
        verbose_name_plural = "demandes de produit"
        ordering = ["-nombre_interets", "-cree_le"]

    def __str__(self) -> str:
        return self.titre


class InteretDemande(models.Model):
    """Le « moi aussi » d'un acheteur sur une demande."""

    demande = models.ForeignKey(
        DemandeProduit,
        on_delete=models.CASCADE,
        related_name="interets",
        verbose_name="demande",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interets_demandes",
        verbose_name="utilisateur",
    )
    cree_le = models.DateTimeField("marqué le", default=timezone.now)

    class Meta:
        verbose_name = "intérêt"
        verbose_name_plural = "intérêts"
        constraints = [
            models.UniqueConstraint(
                fields=["demande", "utilisateur"], name="un_seul_interet_par_personne"
            )
        ]

    def __str__(self) -> str:
        return f"{self.utilisateur.nom_complet} → {self.demande.titre}"


class Notification(models.Model):
    """Message adressé à un utilisateur à une étape qui le concerne.

    Stockées même en mode prototype : la démonstration doit montrer la cloche
    se remplir quand le groupeur annonce que la marchandise est arrivée.
    """

    class Genre(models.TextChoices):
        PAIEMENT_ENREGISTRE = "paiement_enregistre", "Paiement enregistré"
        PAIEMENT_RECU = "paiement_recu", "Paiement reçu sur votre campagne"
        MINIMUM_ATTEINT = "minimum_atteint", "Minimum de pièces atteint"
        CAMPAGNE_FINANCEE = "campagne_financee", "Campagne financée"
        MARCHANDISE_DISPONIBLE = "marchandise_disponible", "Marchandise à disposition"
        RETRAIT_CONFIRME = "retrait_confirme", "Retrait confirmé"
        CAMPAGNE_ANNULEE = "campagne_annulee", "Campagne annulée"
        GROUPAGE_NON_ABOUTI = (
            "groupage_non_abouti",
            "Le groupage n'a pas abouti",
        )
        DECISION_ATTENDUE = (
            "decision_attendue",
            "Votre décision est attendue",
        )
        CAMPAGNE_MAINTENUE = (
            "campagne_maintenue",
            "L'OAG maintient la commande",
        )
        REMBOURSEMENT = "remboursement", "Remboursement effectué"
        KYC_DECIDE = "kyc_decide", "Décision sur votre dossier"
        RELANCE_RETRAIT = "relance_retrait", "Rappel : colis à retirer"
        NOUVEL_AVIS = "nouvel_avis", "Un acheteur vous a noté"
        # Le fil public n'existe plus ; ce qui le remplace est privé.
        MESSAGE_PRIVE = "message_prive", "Nouveau message privé"
        CONTACT_PRIVE = "contact_prive", "Contact Privé"
        SYSTEME = "systeme", "Information"

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="destinataire",
    )
    genre = models.CharField("type", max_length=30, choices=Genre.choices)
    titre = models.CharField("titre", max_length=160)
    message = models.TextField("message")

    # Chemin dans l'application plutôt qu'URL absolue : les deux interfaces
    # ne sont pas servies depuis le même domaine.
    lien = models.CharField("lien", max_length=200, blank=True)

    campagne = models.ForeignKey(
        Campagne,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="campagne concernée",
    )
    cree_le = models.DateTimeField("envoyée le", default=timezone.now)
    lue_le = models.DateTimeField("lue le", null=True, blank=True)

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-cree_le"]
        indexes = [models.Index(fields=["destinataire", "lue_le"])]

    def __str__(self) -> str:
        return f"{self.titre} → {self.destinataire.telephone}"


# Déclarés dans un module à part — ils forment un sujet à eux seuls — mais
# réexportés ici, parce que c'est `models` que Django inspecte.
from groupachat.echanges.contact_prive import (  # noqa: E402
    AbonnementContactPrive,
    Conversation,
    Message,
)

__all__ = [
    "DemandeProduit",
    "InteretDemande",
    "Notification",
    "AbonnementContactPrive",
    "Conversation",
    "Message",
]
