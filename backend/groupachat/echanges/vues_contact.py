# -*- coding: utf-8 -*-
"""Les vues du Contact Privé.

L'abonnement est vérifié **à l'écriture, pas à la lecture**. Un acheteur dont
le mois s'achève garde l'accès à son historique : ce sont ses échanges, et
les lui retirer parce qu'il n'a pas renouvelé reviendrait à effacer la preuve
de ce qui a été convenu. Ce qu'il perd, c'est le droit d'écrire.

L'OAG, lui, répond **sans abonnement**. Il ne paie pas pour parler à ses
propres acheteurs, et un fil où seul l'un des deux peut écrire ne vaut rien.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from groupachat.catalogue.models import Campagne
from groupachat.comptes import points
from groupachat.comptes.models import Utilisateur
from groupachat.echanges.contact_prive import (
    DUREE_JOURS,
    PRIX_MENSUEL_FCFA,
    SEUIL_POINTS,
    AbonnementContactPrive,
    Conversation,
    Message,
)
from groupachat.echanges.models import Notification
from groupachat.echanges.serialiseurs_contact import (
    AbonnementSerialiseur,
    ConversationSerialiseur,
    MessageSerialiseur,
    OuvertureConversationSerialiseur,
)
from groupachat.noyau.permissions import NumeroVerifie

POINTS_PAR_MOIS = points.BAREME[points.Motif.CONTACT_PRIVE]


def _etat(utilisateur) -> dict:
    abonnement = AbonnementContactPrive.actif_pour(utilisateur)
    # Lecture seule : `_etat` est appelé sur un GET, il ne doit pas créer de
    # compteur pour un compte qui n'en a pas encore.
    compteur = getattr(utilisateur, "points", None)
    cumules = compteur.cumules if compteur else 0
    return {
        "actif": abonnement is not None,
        "expire_le": abonnement.expire_le if abonnement else None,
        "prix": PRIX_MENSUEL_FCFA,
        "duree_jours": DUREE_JOURS,
        "points_par_mois": POINTS_PAR_MOIS,
        "points_cumules": cumules,
        "points_minimum": 0,
        "eligible": True,
    }


class ContactPriveVue(APIView):
    """GET /api/contact-prive/ — l'état de mon abonnement."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, requete):
        return Response(_etat(requete.user))


class SouscriptionVue(APIView):
    """POST /api/contact-prive/souscrire/ — payer un mois (2 000 FCFA).

    Ouvre la messagerie avec les OAG pendant 30 jours (1 mois).
    Renouvelable à tout moment, et chaque abonnement / renouvellement
    rapporte des points de fidélité (+10 points).
    """

    permission_classes = [NumeroVerifie]

    @transaction.atomic
    def post(self, requete):
        debut, fin = AbonnementContactPrive.prochaine_echeance(requete.user)
        abonnement = AbonnementContactPrive.objects.create(
            abonne=requete.user,
            montant=PRIX_MENSUEL_FCFA,
            debute_le=debut,
            expire_le=fin,
        )

        # L'abonnement ne coûte aucun point : il en rapporte.
        # À chaque abonnement ou renouvellement, l'acheteur gagne des points.
        points.attribuer(
            requete.user,
            points.Motif.CONTACT_PRIVE,
            "abonnement_contact_prive",
            abonnement.id,
        )

        Notification.objects.create(
            destinataire=requete.user,
            genre=Notification.Genre.SYSTEME,
            titre="Contact Privé activé",
            message=(
                f"Vous pouvez écrire aux OAG jusqu'au "
                f"{fin:%d/%m/%Y}. +{POINTS_PAR_MOIS} points fidélité crédités."
            ),
            lien="/messages",
        )

        return Response(
            {
                "abonnement": AbonnementSerialiseur(abonnement).data,
                "etat": _etat(requete.user),
            },
            status=status.HTTP_201_CREATED,
        )


class ConversationVueEnsemble(viewsets.GenericViewSet):
    """Les fils privés de la personne connectée."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerialiseur

    def get_queryset(self):
        moi = self.request.user
        return (
            Conversation.objects.filter(Q(acheteur=moi) | Q(groupeur=moi))
            .select_related("acheteur", "groupeur", "campagne_initiale")
            .prefetch_related(
                Prefetch("messages", queryset=Message.objects.order_by("-envoye_le"))
            )
        )

    def get_serializer_context(self):
        contexte = super().get_serializer_context()
        contexte["abonnement_actif"] = (
            AbonnementContactPrive.actif_pour(self.request.user) is not None
        )
        return contexte

    def list(self, requete):
        fils = self.get_queryset()
        return Response(
            ConversationSerialiseur(
                fils, many=True, context=self.get_serializer_context()
            ).data
        )

    @action(detail=True, methods=["get"])
    def messages(self, requete, pk=None):
        """L'historique d'un fil, lisible même sans abonnement en cours."""
        fil = self.get_queryset().filter(pk=pk).first()
        if fil is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        visibles = fil.messages.filter(masque_le__isnull=True).select_related("auteur")
        # Marquer lu à la lecture : un compteur de non-lus qui ne retombe
        # jamais à zéro cesse vite d'être regardé.
        fil.messages.filter(lu_le__isnull=True).exclude(auteur=requete.user).update(
            lu_le=timezone.now()
        )
        return Response(
            {
                "conversation": ConversationSerialiseur(
                    fil, context=self.get_serializer_context()
                ).data,
                "messages": MessageSerialiseur(
                    visibles, many=True, context={"request": requete}
                ).data,
            }
        )

    @action(detail=True, methods=["post"])
    def repondre(self, requete, pk=None):
        fil = self.get_queryset().filter(pk=pk).first()
        if fil is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        refus = _refus_d_ecrire(requete.user, fil)
        if refus is not None:
            return refus

        texte = (requete.data.get("texte") or "").strip()
        if not texte:
            return Response(
                {"texte": "Le message est vide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = _ecrire(fil, requete.user, texte)
        return Response(
            MessageSerialiseur(message, context={"request": requete}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="signaler-message")
    def signaler_message(self, requete, pk=None):
        fil = self.get_queryset().filter(pk=pk).first()
        if fil is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        message = fil.messages.filter(pk=requete.data.get("message")).first()
        if message is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        message.signale_le = timezone.now()
        message.save(update_fields=["signale_le"])
        return Response(MessageSerialiseur(message, context={"request": requete}).data)


class OuvertureConversationVue(APIView):
    """POST /api/conversations/ouvrir/ — écrire à un OAG pour la première fois."""

    permission_classes = [NumeroVerifie]

    @transaction.atomic
    def post(self, requete):
        entree = OuvertureConversationSerialiseur(data=requete.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        destinataire = Utilisateur.objects.filter(
            pk=donnees["groupeur"], role=Utilisateur.Role.GROUPEUR
        ).first()
        if destinataire is None or not destinataire.est_groupeur_valide:
            return Response(
                {"groupeur": "Cet OAG n'existe pas ou n'est pas validé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if destinataire == requete.user:
            return Response(
                {"groupeur": "Vous ne pouvez pas vous écrire à vous-même."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fil, _ = Conversation.objects.get_or_create(
            acheteur=requete.user,
            groupeur=destinataire,
            defaults={
                "campagne_initiale": Campagne.objects.filter(
                    pk=donnees.get("campagne")
                ).first()
            },
        )

        refus = _refus_d_ecrire(requete.user, fil)
        if refus is not None:
            return refus

        _ecrire(fil, requete.user, donnees["texte"])
        contexte = {
            "request": requete,
            "abonnement_actif": AbonnementContactPrive.actif_pour(requete.user)
            is not None,
        }
        return Response(
            ConversationSerialiseur(fil, context=contexte).data,
            status=status.HTTP_201_CREATED,
        )


def _refus_d_ecrire(auteur, fil):
    """`None` si la personne a le droit d'écrire, sinon la réponse de refus.

    L'OAG répond toujours. L'acheteur a besoin d'un abonnement en cours :
    c'est lui qui achète le droit d'ouvrir le pont.
    """
    if auteur == fil.groupeur:
        return None
    if AbonnementContactPrive.actif_pour(auteur) is not None:
        return None
    return Response(
        {
            "detail": (
                "Écrire à un OAG demande l'abonnement Contact Privé — "
                f"{PRIX_MENSUEL_FCFA} FCFA par mois."
            ),
            "abonnement_requis": True,
            "prix": PRIX_MENSUEL_FCFA,
        },
        status=status.HTTP_402_PAYMENT_REQUIRED,
    )


def _ecrire(fil, auteur, texte: str) -> Message:
    message = Message.objects.create(conversation=fil, auteur=auteur, texte=texte)
    fil.dernier_message_le = message.envoye_le
    fil.save(update_fields=["dernier_message_le"])

    destinataire = fil.interlocuteur_de(auteur)
    Notification.objects.create(
        destinataire=destinataire,
        genre=Notification.Genre.SYSTEME,
        titre="Nouveau message privé",
        message=f"{auteur.nom_public} vous a écrit.",
        lien=f"/messages/{fil.id}",
    )
    return message
