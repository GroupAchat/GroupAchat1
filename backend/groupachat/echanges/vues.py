# -*- coding: utf-8 -*-
"""Espace communautaire et cloche de notifications.

Le fil public sous les campagnes a été retiré : il laissait convenir
d'un arrangement direct à la vue de tous, et hors de la plateforme ni le
séquestre ni l'assurance ne jouent. Ce qui le remplace est le Contact
Privé — payant, privé, tracé — dans `vues_contact.py`.
"""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import F, Prefetch
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from groupachat.catalogue.models import Campagne
from groupachat.echanges.models import (
    DemandeProduit,
    InteretDemande,
    Notification,
)
from groupachat.echanges.serialiseurs import (
    DemandeProduitSerialiseur,
    NotificationSerialiseur,
)
from groupachat.noyau.permissions import (
    EstAuteurOuLectureSeule,
    LectureLibreEcritureVerifiee,
)


class DemandeProduitVueEnsemble(viewsets.ModelViewSet):
    """/api/demandes/ — l'espace communautaire.

    Les acheteurs réclament, les groupeurs piochent. C'est le sens inverse du
    catalogue habituel, et le compteur d'intérêt sert de signal.
    """

    serializer_class = DemandeProduitSerialiseur
    permission_classes = [LectureLibreEcritureVerifiee, EstAuteurOuLectureSeule]
    actions_ouvertes = ("moi_aussi",)

    def get_queryset(self):
        demandes = DemandeProduit.objects.select_related("auteur", "categorie")
        parametres = self.request.query_params
        if (statut := parametres.get("statut")):
            demandes = demandes.filter(statut=statut)
        if (categorie := parametres.get("categorie")):
            demandes = demandes.filter(categorie__slug=categorie)
        if parametres.get("mes_demandes") and self.request.user.is_authenticated:
            demandes = demandes.filter(auteur=self.request.user)
        return demandes

    def get_serializer_context(self):
        contexte = super().get_serializer_context()
        if self.request.user.is_authenticated:
            contexte["demandes_interessees"] = set(
                self.request.user.interets_demandes.values_list(
                    "demande_id", flat=True
                )
            )
        return contexte

    def perform_create(self, serialiseur):
        serialiseur.save(auteur=self.request.user)

    @action(detail=True, methods=["post"], url_path="moi-aussi")
    def moi_aussi(self, requete, pk=None):
        """Marque son intérêt, ou le retire."""
        demande = self.get_object()
        try:
            with transaction.atomic():
                InteretDemande.objects.create(demande=demande, utilisateur=requete.user)
                DemandeProduit.objects.filter(pk=demande.pk).update(
                    nombre_interets=F("nombre_interets") + 1
                )
            interesse = True
        except IntegrityError:
            InteretDemande.objects.filter(
                demande=demande, utilisateur=requete.user
            ).delete()
            DemandeProduit.objects.filter(pk=demande.pk, nombre_interets__gt=0).update(
                nombre_interets=F("nombre_interets") - 1
            )
            interesse = False

        demande.refresh_from_db()
        return Response({"interesse": interesse,
                         "nombre_interets": demande.nombre_interets})


class NotificationVueEnsemble(
    mixins.ListModelMixin, viewsets.GenericViewSet
):
    """/api/notifications/ — la cloche."""

    # Explicite, même si la valeur par défaut suffisait : une permission
    # héritée est une permission qu'on oublie de relire le jour où la
    # valeur par défaut change.
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerialiseur

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Notification.objects.none()
        notifications = Notification.objects.filter(destinataire=self.request.user)
        if self.request.query_params.get("non_lues"):
            notifications = notifications.filter(lue_le__isnull=True)
        return notifications

    @action(detail=False, methods=["get"], url_path="non-lues")
    def nombre_non_lues(self, requete):
        if not requete.user.is_authenticated:
            return Response({"non_lues": 0})
        return Response(
            {
                "non_lues": Notification.objects.filter(
                    destinataire=requete.user, lue_le__isnull=True
                ).count()
            }
        )

    @action(detail=True, methods=["post"], url_path="marquer-lue")
    def marquer_lue(self, requete, pk=None):
        notification = self.get_object()
        if notification.lue_le is None:
            notification.lue_le = timezone.now()
            notification.save(update_fields=["lue_le"])
        return Response(NotificationSerialiseur(notification).data)

    @action(detail=False, methods=["post"], url_path="tout-marquer-lu")
    def tout_marquer_lu(self, requete):
        if not requete.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        nombre = Notification.objects.filter(
            destinataire=requete.user, lue_le__isnull=True
        ).update(lue_le=timezone.now())
        return Response({"marquees": nombre})
