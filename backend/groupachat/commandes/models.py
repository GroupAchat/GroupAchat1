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

from groupachat.catalogue.models import DELAI_RETRAIT_JOURS, Campagne

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
        REPUTEE_LIVREE = "reputee_livree", "Non retirée — réputée livrée"
        REMBOURSEE = "remboursee", "Remboursée"
        ANNULEE = "annulee", "Annulée"

    # Participations dont l'argent est effectivement consigné : ce sont les
    # seules qui comptent dans la jauge et dans le montant collecté.
    # Une part réputée livrée en fait partie : son argent a bien été payé puis
    # versé au groupeur. Sans elle, la jauge et le montant collecté baisseraient
    # le jour où le délai de retrait s'écoule.
    STATUTS_PAYES = (
        Statut.PAYEE,
        Statut.PRETE,
        Statut.RETIREE,
        Statut.REPUTEE_LIVREE,
    )

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
    # Distinct de `retiree_le`, qui veut dire « remise prouvée par le code » :
    # c'est précisément ce qui manque à une part réputée livrée. La date reste
    # en trace si le code est présenté plus tard.
    reputee_livree_le = models.DateTimeField(
        "réputée livrée le", null=True, blank=True
    )
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
            # À sens unique, exprès : une part devenue `retiree` après
            # l'échéance garde sa date de réputation comme trace.
            models.CheckConstraint(
                condition=~models.Q(statut="reputee_livree")
                | models.Q(reputee_livree_le__isnull=False),
                name="participation_reputee_livree_datee",
            ),
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
    def delai_retrait_depasse(self) -> bool:
        """Quatorze jours après la mise à disposition, la livraison est acquise."""
        depuis = self.campagne.mise_a_disposition_le
        if depuis is None or self.statut != self.Statut.PRETE:
            return False
        return (timezone.now() - depuis).days >= DELAI_RETRAIT_JOURS


class Avis(models.Model):
    """La note qu'un acheteur laisse à son groupeur.

    **Group Achat met en relation, elle n'arbitre pas.** Un souci sur un
    produit se règle entre l'acheteur et le groupeur — par la discussion
    publique sous la campagne, et par cette note. La plateforme garantit
    l'argent de la collecte, pas la qualité de la marchandise.

    C'est pour cette raison qu'il n'y a pas de dossier de litige à
    instruire : la sanction d'un mauvais groupeur n'est pas une décision
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

    # Le groupeur répond une fois, sous l'avis. Pas un fil : une réponse.
    # Au-delà, la discussion a sa place sous la campagne.
    reponse = models.TextField("réponse du groupeur", blank=True)
    repondu_le = models.DateTimeField("répondu le", null=True, blank=True)

    class Meta:
        verbose_name = "avis"
        verbose_name_plural = "avis"
        ordering = ["-cree_le"]
        indexes = [models.Index(fields=["-cree_le"])]

    def __str__(self) -> str:
        return f"{self.note}/5 — {self.participation}"

    @property
    def auteur_id(self) -> int:
        """L'acheteur qui a écrit l'avis.

        Sans cet attribut, la permission d'auteur du noyau (qui ne connaît
        aucun sujet) ne saurait pas lire le propriétaire d'un avis : il vit
        sur la participation, pas sur l'avis.
        """
        return self.participation.acheteur_id

    @property
    def groupeur(self):
        return self.participation.campagne.groupeur

