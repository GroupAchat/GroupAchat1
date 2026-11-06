# -*- coding: utf-8 -*-
"""Le droit de publier : abonnement ou pack.

Publier un groupage se paie, et l'OAG choisit comment. L'**abonnement** —
2 000 FCFA le mois — s'adresse à celui qui publie régulièrement ; le **pack**
— 500 FCFA pour cinq publications — à celui qui essaie, ou qui lance un
groupage de loin en loin.

**Les deux compteurs sont indépendants.** Un OAG dont l'abonnement expire
garde les publications de ses packs : il a payé pour elles, et un mois qui
s'achève n'est pas une raison de les lui prendre. C'est aussi pour ça qu'un
pack n'expire pas — ce qui reste reste.

**La publication se consomme à la mise en ligne**, jamais à la création du
brouillon : un groupage abandonné avant publication ne coûte rien. Et elle
n'est pas rendue si le groupage échoue — elle paie la mise en ligne, pas la
réussite.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Sum
from django.utils import timezone

PRIX_ABONNEMENT_FCFA = 2000
DUREE_ABONNEMENT_JOURS = 30
PRIX_PACK_FCFA = 100
PUBLICATIONS_PAR_PACK = 10
PRIX_TICKET_FCFA = 100
PUBLICATIONS_PAR_TICKET = 10
POINTS_PAR_TICKET = 2


class DroitDePublierEpuise(Exception):
    """Ni abonnement en cours, ni publication en réserve."""


class AbonnementPublication(models.Model):
    """Un mois de publications illimitées."""

    oag = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abonnements_publication",
        verbose_name="OAG",
    )
    montant = models.PositiveIntegerField(
        "montant (FCFA)", default=PRIX_ABONNEMENT_FCFA
    )
    debute_le = models.DateTimeField("débute le", default=timezone.now)
    expire_le = models.DateTimeField("expire le")
    reference_paiement = models.CharField(
        "référence du paiement", max_length=60, blank=True
    )

    class Meta:
        verbose_name = "abonnement de publication"
        verbose_name_plural = "abonnements de publication"
        ordering = ["-expire_le"]
        indexes = [models.Index(fields=["oag", "expire_le"])]

    def __str__(self) -> str:
        return f"{self.oag.nom_public} — publications jusqu'au {self.expire_le:%d/%m/%Y}"

    @property
    def actif(self) -> bool:
        return self.expire_le > timezone.now()

    @classmethod
    def actif_pour(cls, oag):
        return (
            cls.objects.filter(oag=oag, expire_le__gt=timezone.now())
            .order_by("-expire_le")
            .first()
        )

    @classmethod
    def prochaine_echeance(cls, oag) -> tuple:
        """Renouveler tôt **ajoute** trente jours à ceux qui restent.

        Sinon renouveler la veille de l'échéance coûterait moins cher que
        renouveler trois jours avant, et personne ne renouvellerait tôt.
        """
        maintenant = timezone.now()
        en_cours = cls.actif_pour(oag)
        depart = en_cours.expire_le if en_cours else maintenant
        return maintenant, depart + timedelta(days=DUREE_ABONNEMENT_JOURS)


class PackPublication(models.Model):
    """Cinq publications achetées d'avance, qui n'expirent pas."""

    oag = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="packs_publication",
        verbose_name="OAG",
    )
    montant = models.PositiveIntegerField("montant (FCFA)", default=PRIX_PACK_FCFA)
    publications_offertes = models.PositiveIntegerField(
        "publications offertes", default=PUBLICATIONS_PAR_PACK
    )
    publications_restantes = models.PositiveIntegerField(
        "publications restantes", default=PUBLICATIONS_PAR_PACK
    )
    achete_le = models.DateTimeField("acheté le", default=timezone.now)
    reference_paiement = models.CharField(
        "référence du paiement", max_length=60, blank=True
    )

    class Meta:
        verbose_name = "pack de publication"
        verbose_name_plural = "packs de publication"
        ordering = ["achete_le"]
        indexes = [models.Index(fields=["oag", "publications_restantes"])]
        constraints = [
            # On ne consomme pas plus que ce qui a été acheté : une réserve
            # négative se traduirait par des publications gratuites, et rien
            # dans les écrans ne le ferait voir.
            models.CheckConstraint(
                condition=models.Q(
                    publications_restantes__lte=models.F("publications_offertes")
                ),
                name="un_pack_ne_rend_pas_plus_qu_il_ne_contient",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.oag.nom_public} — {self.publications_restantes}"
            f"/{self.publications_offertes} publications"
        )


def publications_en_reserve(oag) -> int:
    """Ce qui reste dans tous les packs confondus — ils s'additionnent."""
    return (
        PackPublication.objects.filter(oag=oag).aggregate(
            total=Sum("publications_restantes")
        )["total"]
        or 0
    )


def droit_de_publier(oag) -> dict:
    """Ce que l'interface a besoin de savoir avant d'offrir « Publier »."""
    abonnement = AbonnementPublication.actif_pour(oag)
    reserve = publications_en_reserve(oag)
    return {
        "abonnement_actif": abonnement is not None,
        "expire_le": abonnement.expire_le if abonnement else None,
        "publications_restantes": reserve,
        "peut_publier": abonnement is not None or reserve > 0,
        "prix_abonnement": PRIX_ABONNEMENT_FCFA,
        "duree_jours": DUREE_ABONNEMENT_JOURS,
        "prix_pack": PRIX_PACK_FCFA,
        "publications_par_pack": PUBLICATIONS_PAR_PACK,
        "prix_ticket": PRIX_TICKET_FCFA,
        "publications_par_ticket": PUBLICATIONS_PAR_TICKET,
        "points_par_ticket": POINTS_PAR_TICKET,
    }


@transaction.atomic
def consommer_une_publication(oag) -> str:
    """Prélève une publication, et dit sur quoi elle a été prise.

    L'abonnement passe **avant** les packs : il est illimité, et entamer la
    réserve d'un abonné lui ferait payer deux fois le même mois. Ce qu'il a
    acheté d'avance l'attendra à l'échéance.
    """
    if AbonnementPublication.actif_pour(oag) is not None:
        return "abonnement"

    # `select_for_update` : deux publications lancées en même temps lisaient
    # la même réserve et passaient toutes les deux avec une seule unité.
    pack = (
        PackPublication.objects.select_for_update()
        .filter(oag=oag, publications_restantes__gt=0)
        .order_by("achete_le")
        .first()
    )
    if pack is None:
        raise DroitDePublierEpuise(
            "Publier demande un abonnement ou un pack de publications."
        )

    PackPublication.objects.filter(pk=pack.pk).update(
        publications_restantes=F("publications_restantes") - 1
    )
    return "pack"


@transaction.atomic
def rendre_une_publication(oag) -> bool:
    """Rend une publication au pack le plus récemment entamé.

    Appelé quand la plateforme **refuse** une mise en ligne : la publication
    paie la mise en ligne, et celle-ci n'a pas eu lieu. Un groupage qui
    échoue après coup, lui, est bien allé en vitrine — rien n'est rendu.

    Rien à rendre à un abonné : son mois n'a rien consommé. Rend `True`
    seulement quand une unité a effectivement été recréditée.
    """
    pack = (
        PackPublication.objects.select_for_update()
        .filter(oag=oag, publications_restantes__lt=F("publications_offertes"))
        .order_by("-achete_le")
        .first()
    )
    if pack is None:
        return False

    PackPublication.objects.filter(pk=pack.pk).update(
        publications_restantes=F("publications_restantes") + 1
    )
    return True
