# -*- coding: utf-8 -*-
"""Espace communautaire et notifications.

Les demandes de produit renversent le sens habituel : ce ne sont plus les
groupeurs qui proposent, ce sont les acheteurs qui réclament. Le compteur
d'intérêt sert de signal aux groupeurs en quête d'une campagne à lancer.
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


class Commentaire(models.Model):
    """Message public laissé sous une campagne.

    Le fil est **lisible par tout le monde, sans compte** : c'est lui qui
    rassure l'acheteur hésitant, et le cacher derrière une inscription le
    priverait de sa raison d'être. Écrire, en revanche, demande un numéro
    vérifié — sinon le fil se remplit de faux avis en une nuit.

    Un seul niveau de réponse. Au-delà, un fil devient illisible sur un écran
    de téléphone, et l'affichage demanderait une récursion dont le produit n'a
    pas besoin.
    """

    campagne = models.ForeignKey(
        Campagne,
        on_delete=models.CASCADE,
        related_name="commentaires",
        verbose_name="campagne",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="commentaires",
        verbose_name="auteur",
    )
    texte = models.TextField("message", max_length=1000)
    reponse_a = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reponses",
        verbose_name="en réponse à",
    )

    # Dénormalisé, comme les intérêts : le fil se trie par popularité et
    # compter les « j'aime » ligne par ligne coûterait une jointure par
    # commentaire.
    nombre_jaime = models.PositiveIntegerField("j'aime", default=0)

    cree_le = models.DateTimeField("publié le", default=timezone.now)
    modifie_le = models.DateTimeField("modifié le", null=True, blank=True)

    # Modération : on masque plutôt que de supprimer, pour garder une trace
    # en cas de contestation — un commentaire effacé ne se prouve pas.
    masque_le = models.DateTimeField("masqué le", null=True, blank=True)
    masque_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commentaires_masques",
        verbose_name="masqué par",
    )
    motif_masquage = models.CharField("motif du masquage", max_length=200, blank=True)

    class Meta:
        verbose_name = "commentaire"
        verbose_name_plural = "commentaires"
        ordering = ["-cree_le"]
        indexes = [
            models.Index(fields=["campagne", "masque_le", "-cree_le"]),
            models.Index(fields=["reponse_a", "cree_le"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(reponse_a=models.F("id")),
                name="commentaire_pas_reponse_a_lui_meme",
            )
        ]

    def __str__(self) -> str:
        return f"{self.auteur.nom_complet} sur « {self.campagne.titre} »"

    @property
    def est_visible(self) -> bool:
        return self.masque_le is None

    @property
    def est_du_groupeur(self) -> bool:
        """Sert à distinguer la réponse du vendeur dans le fil."""
        return self.auteur_id == self.campagne.groupeur_id


class JaimeCommentaire(models.Model):
    """Le « j'aime » d'un utilisateur sur un commentaire."""

    commentaire = models.ForeignKey(
        Commentaire,
        on_delete=models.CASCADE,
        related_name="jaime",
        verbose_name="commentaire",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="commentaires_aimes",
        verbose_name="utilisateur",
    )
    cree_le = models.DateTimeField("aimé le", default=timezone.now)

    class Meta:
        verbose_name = "j'aime"
        verbose_name_plural = "j'aime"
        constraints = [
            models.UniqueConstraint(
                fields=["commentaire", "utilisateur"], name="un_seul_jaime_par_personne"
            )
        ]

    def __str__(self) -> str:
        return f"{self.utilisateur.nom_complet} aime #{self.commentaire_id}"


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
            "Le groupeur maintient la commande",
        )
        REMBOURSEMENT = "remboursement", "Remboursement effectué"
        KYC_DECIDE = "kyc_decide", "Décision sur votre dossier"
        RELANCE_RETRAIT = "relance_retrait", "Rappel : colis à retirer"
        NOUVEAU_COMMENTAIRE = "nouveau_commentaire", "Nouveau message sur votre campagne"
        NOUVEL_AVIS = "nouvel_avis", "Un acheteur vous a noté"
        REPONSE_COMMENTAIRE = "reponse_commentaire", "Réponse à votre message"
        LIVRAISON_REPUTEE = "livraison_reputee", "Livraison réputée acquise"
        CAMPAGNE_TERMINEE = "campagne_terminee", "Campagne terminée"

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
