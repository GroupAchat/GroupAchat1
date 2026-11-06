# -*- coding: utf-8 -*-
"""Le parrainage : amener quelqu'un, et être payé quand il achète.

**Un clic ne vaut rien.** Le parrainage n'est validé que lorsque la personne
invitée a rejoint un groupage *et* payé sa part. Récompenser l'ouverture du
lien ferait fabriquer des liens, pas des acheteurs : c'est le seul endroit du
produit où l'on peut créer de la valeur sans rien apporter, et il faut le
fermer d'avance.

Le lien porte un **code court** plutôt que l'identifiant du parrain : un
`?p=42` se devine, se change, et dit combien de comptes existent.
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

# Même alphabet que les codes de retrait : ni 0/O ni 1/I/L, parce qu'un code
# de parrainage se dicte au téléphone autant qu'il se clique.
ALPHABET_CODE = "34679ACDEFGHJKMNPQRTUVWXY"
LONGUEUR_CODE = 6

POINTS_PARRAIN = 2


def engendrer_code() -> str:
    return "".join(secrets.choice(ALPHABET_CODE) for _ in range(LONGUEUR_CODE))


class Parrainage(models.Model):
    """Le lien entre celui qui a invité et celui qui est venu.

    **Un filleul n'a qu'un parrain, et pour toujours** — le premier qui
    l'amène. Sans cette unicité, le même compte servirait de filleul à tout
    un réseau, et deux personnes se disputeraient le même mérite.
    """

    parrain = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="filleuls",
        verbose_name="parrain",
    )
    filleul = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parrainage",
        verbose_name="filleul",
    )
    # La campagne par laquelle il est arrivé : c'est ce qui permet de dire au
    # parrain *ce* qui a marché, et non seulement combien.
    campagne = models.ForeignKey(
        "catalogue.Campagne",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parrainages",
        verbose_name="campagne d'arrivée",
    )
    cree_le = models.DateTimeField("rattaché le", default=timezone.now)
    valide_le = models.DateTimeField("validé le", null=True, blank=True)

    class Meta:
        verbose_name = "parrainage"
        verbose_name_plural = "parrainages"
        ordering = ["-cree_le"]
        indexes = [models.Index(fields=["parrain", "valide_le"])]
        constraints = [
            # On ne se parraine pas soi-même. La règle est en base et pas
            # seulement dans la vue : c'est la fraude la plus simple à tenter,
            # et elle ne doit pas dépendre du chemin emprunté.
            models.CheckConstraint(
                condition=~models.Q(parrain=models.F("filleul")),
                name="on_ne_se_parraine_pas_soi_meme",
            ),
        ]

    def __str__(self) -> str:
        etat = "validé" if self.valide_le else "en attente"
        return f"{self.parrain.nom_public} → {self.filleul.nom_public} ({etat})"

    @property
    def valide(self) -> bool:
        return self.valide_le is not None


def code_de(utilisateur) -> str:
    """Le code du parrain, créé au premier besoin.

    Il n'est pas attribué à l'inscription : la plupart des comptes ne
    parraineront jamais, et une colonne remplie pour tout le monde fait croire
    que tout le monde a essayé.
    """
    if utilisateur.code_parrainage:
        return utilisateur.code_parrainage

    for _ in range(10):
        candidat = engendrer_code()
        if not type(utilisateur).objects.filter(code_parrainage=candidat).exists():
            utilisateur.code_parrainage = candidat
            utilisateur.save(update_fields=["code_parrainage"])
            return candidat
    raise RuntimeError("Impossible d'attribuer un code de parrainage libre.")


def parrain_du_code(code: str):
    """Le parrain désigné par un code, ou `None` si le code ne dit rien."""
    from groupachat.comptes.models import Utilisateur

    propre = (code or "").strip().upper()
    if not propre:
        return None
    return Utilisateur.objects.filter(code_parrainage=propre).first()


@transaction.atomic
def rattacher(filleul, code: str, campagne=None) -> Parrainage | None:
    """Enregistre le lien à la **première commande** du filleul.

    Rien n'est crédité ici : le parrainage attend le paiement. On le crée
    quand même dès la commande, parce que c'est à ce moment-là qu'on sait
    encore d'où vient la personne — le code vit dans son navigateur, et il
    n'y survivra pas forcément jusqu'au paiement.

    Rend `None` quand il n'y a rien à faire : code inconnu, auto-parrainage,
    ou filleul déjà rattaché. Aucun de ces cas n'est une erreur à remonter —
    un lien de parrainage se partage sans savoir qui l'a déjà utilisé.
    """
    parrain = parrain_du_code(code)
    if parrain is None or parrain.id == filleul.id:
        return None
    if Parrainage.objects.filter(filleul=filleul).exists():
        return None

    return Parrainage.objects.create(
        parrain=parrain, filleul=filleul, campagne=campagne
    )


@transaction.atomic
def valider_au_paiement(participation) -> Parrainage | None:
    """Valide le parrainage du payeur, et crédite son parrain.

    Appelée à l'encaissement. Le paiement est la seule preuve qui compte :
    une inscription sans achat ne rapporte rien, et un paiement refusé
    n'arrive jamais ici.
    """
    from groupachat.comptes import points

    lien = (
        Parrainage.objects.select_for_update()
        .filter(filleul=participation.acheteur, valide_le__isnull=True)
        .first()
    )
    if lien is None:
        return None

    lien.valide_le = timezone.now()
    if lien.campagne_id is None:
        lien.campagne = participation.campagne
    lien.save(update_fields=["valide_le", "campagne"])

    # L'origine est le parrainage lui-même : rejouer un paiement ne crédite
    # pas deux fois, et un second filleul rapporte bien ses propres points.
    points.attribuer(
        lien.parrain,
        points.Motif.PARRAINAGE,
        "parrainage",
        lien.id,
        points=POINTS_PARRAIN,
    )
    return lien


def bilan(utilisateur) -> dict:
    """Ce que l'écran du parrain affiche : son code, et ce qu'il a obtenu."""
    liens = Parrainage.objects.filter(parrain=utilisateur)
    valides = liens.filter(valide_le__isnull=False).count()
    return {
        "code": code_de(utilisateur),
        "filleuls": liens.count(),
        "filleuls_valides": valides,
        "en_attente": liens.filter(valide_le__isnull=True).count(),
        "points_gagnes": valides * POINTS_PARRAIN,
        "points_par_filleul": POINTS_PARRAIN,
    }
