# -*- coding: utf-8 -*-
"""Le Contact Privé : le seul pont entre un acheteur et un OAG.

Sur la plateforme, l'acheteur et l'OAG **ne se connaissent pas**. Chacun
n'existe que sous son nom public, et la confiance vient du dispositif —
séquestre, contrat, réclamation — et non de la personne.

L'abonnement ouvre la **messagerie interne** avec les OAG. Il ne transmet
jamais leurs coordonnées : ni téléphone, ni adresse, ni nom civil. C'est une
règle du cahier des charges v2, et elle protège les deux parties — un numéro
qui circule fait sortir la relation du séquestre et de la procédure.

Il ne coûte **aucun point** : les points ne sont pas un péage, ils sont une
récompense. Payer son mois en rapporte. Mais il exige d'en avoir **cumulé
cinquante** : c'est un avantage de fidélité, pas un droit d'entrée. Un
acheteur qui n'a encore rien acheté peut consulter, acheter et laisser un
avis ; il ne peut pas encore écrire.

Il n'existe par ailleurs **aucune discussion publique**. Un fil ouvert sous
une campagne laisse convenir d'un arrangement direct à la vue de tous, et
hors de la plateforme ni le séquestre ni la réclamation ne jouent.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

PRIX_MENSUEL_FCFA = 2000
DUREE_JOURS = 30

# L'abonnement ne requiert aucun seuil de points : n'importe quel acheteur
# peut souscrire pour 2 000 FCFA/mois et gagner des points à chaque abonnement.
SEUIL_POINTS = 0


class AbonnementContactPrive(models.Model):
    """Un mois d'accès au Contact Privé, payé par un acheteur.

    Un enregistrement **par mois payé**, et non un drapeau sur le compte :
    il faut pouvoir dire quand quelqu'un était abonné, pas seulement s'il
    l'est aujourd'hui. Un reçu se conteste des mois plus tard, et un droit
    d'accès qui ne laisse pas de trace ne se prouve pas.
    """

    abonne = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abonnements_contact_prive",
        verbose_name="abonné",
    )
    montant = models.PositiveIntegerField(
        "montant payé (FCFA)", default=PRIX_MENSUEL_FCFA
    )
    debute_le = models.DateTimeField("début", default=timezone.now)
    expire_le = models.DateTimeField("expiration")
    # Recopiée depuis la transaction : le tarif peut changer, un reçu non.
    reference_paiement = models.CharField("référence", max_length=40, blank=True)

    class Meta:
        verbose_name = "abonnement Contact Privé"
        verbose_name_plural = "abonnements Contact Privé"
        ordering = ["-debute_le"]
        indexes = [models.Index(fields=["abonne", "-expire_le"])]

    def __str__(self) -> str:
        return f"{self.abonne.nom_public} — jusqu'au {self.expire_le:%d/%m/%Y}"

    @property
    def actif(self) -> bool:
        return self.expire_le > timezone.now()

    @classmethod
    def actif_pour(cls, utilisateur) -> "AbonnementContactPrive | None":
        """L'abonnement en cours, ou `None`.

        On prend le plus lointain plutôt que le plus récent : deux mois payés
        d'affilée se prolongent, et c'est la date d'expiration la plus
        éloignée qui dit jusqu'à quand le pont reste ouvert.
        """
        if not utilisateur or not utilisateur.is_authenticated:
            return None
        return (
            cls.objects.filter(abonne=utilisateur, expire_le__gt=timezone.now())
            .order_by("-expire_le")
            .first()
        )

    @classmethod
    def prochaine_echeance(cls, utilisateur):
        """Le point de départ du mois acheté.

        Un abonné qui renouvelle avant la fin ne perd pas les jours restants :
        le nouveau mois s'ajoute à l'ancien. Sinon, renouveler tôt coûterait
        plus cher que renouveler tard, et personne ne renouvellerait tôt.
        """
        courant = cls.actif_pour(utilisateur)
        depart = courant.expire_le if courant else timezone.now()
        return depart, depart + timedelta(days=DUREE_JOURS)


class Conversation(models.Model):
    """Un fil privé entre un acheteur et un OAG.

    Un seul fil par paire, quelle que soit la campagne : l'acheteur parle à
    quelqu'un, pas à une annonce. Rattacher le fil à une campagne
    éparpillerait la même conversation en autant de fils que de groupages, et
    l'historique — qui est précisément ce qui protège les deux parties —
    deviendrait illisible.
    """

    acheteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_acheteur",
        verbose_name="acheteur",
    )
    groupeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_groupeur",
        verbose_name="OAG",
    )
    # La campagne d'où part la conversation : elle sert de contexte au
    # premier message, pas de clé de regroupement.
    campagne_initiale = models.ForeignKey(
        "catalogue.Campagne",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
        verbose_name="campagne d'origine",
    )
    ouverte_le = models.DateTimeField("ouverte le", default=timezone.now)
    dernier_message_le = models.DateTimeField(
        "dernier message", default=timezone.now, db_index=True
    )

    class Meta:
        verbose_name = "conversation"
        verbose_name_plural = "conversations"
        ordering = ["-dernier_message_le"]
        constraints = [
            models.UniqueConstraint(
                fields=["acheteur", "groupeur"], name="un_seul_fil_par_paire"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.acheteur.nom_public} ↔ {self.groupeur.nom_public}"

    def interlocuteur_de(self, utilisateur):
        return self.groupeur if utilisateur == self.acheteur else self.acheteur


class Message(models.Model):
    """Un message dans un fil privé."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="conversation",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_prives",
        verbose_name="auteur",
    )
    texte = models.TextField("message", max_length=2000)
    envoye_le = models.DateTimeField("envoyé le", default=timezone.now)
    lu_le = models.DateTimeField("lu le", null=True, blank=True)

    # La modération ne supprime pas : elle masque, et dit pourquoi. Un
    # message effacé sans trace empêcherait d'instruire un signalement.
    signale_le = models.DateTimeField("signalé le", null=True, blank=True)
    masque_le = models.DateTimeField("masqué le", null=True, blank=True)
    motif_masquage = models.CharField("motif du masquage", max_length=200, blank=True)

    class Meta:
        verbose_name = "message privé"
        verbose_name_plural = "messages privés"
        ordering = ["envoye_le"]
        indexes = [models.Index(fields=["conversation", "envoye_le"])]

    def __str__(self) -> str:
        return f"{self.auteur.nom_public} : {self.texte[:40]}"
