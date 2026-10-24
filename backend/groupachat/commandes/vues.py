# -*- coding: utf-8 -*-
"""Espace acheteur : rejoindre une campagne, payer, suivre ses parts."""

from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from groupachat.commandes.models import Litige, Participation
from groupachat.commandes.serialiseurs import (
    CreationParticipationSerialiseur,
    LitigeSerialiseur,
    PaiementSerialiseur,
    ParticipationSerialiseur,
)
from groupachat.paiements.services import ErreurPaiement, encaisser
from groupachat.permissions import NumeroVerifie


class ParticipationVueEnsemble(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """/api/participations/ — les parts de l'acheteur connecté."""

    permission_classes = [NumeroVerifie]

    def get_queryset(self):
        # Filtré sur l'utilisateur, toujours : une participation porte un
        # code de retrait, et un identifiant deviné ne doit rien donner.
        return (
            Participation.objects.filter(acheteur=self.request.user)
            .select_related("campagne", "campagne__produit",
                            "campagne__produit__categorie", "campagne__groupeur",
                            "campagne__groupeur__reputation")
            .prefetch_related("campagne__paliers", "campagne__produit__medias")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return CreationParticipationSerialiseur
        return ParticipationSerialiseur

    def create(self, requete, *args, **kwargs):
        serialiseur = self.get_serializer(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        participation = serialiseur.save()
        return Response(
            ParticipationSerialiseur(
                participation, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def payer(self, requete, pk=None):
        """Règle la part et consigne les fonds au séquestre."""
        participation = self.get_object()
        serialiseur = PaiementSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)

        try:
            mouvement = encaisser(
                participation,
                operateur=serialiseur.validated_data["operateur"],
                numero=serialiseur.validated_data.get("numero")
                or requete.user.telephone,
            )
        except ErreurPaiement as erreur:
            return Response({"detail": str(erreur)},
                            status=status.HTTP_400_BAD_REQUEST)

        participation.refresh_from_db()
        return Response(
            {
                "participation": ParticipationSerialiseur(
                    participation, context=self.get_serializer_context()
                ).data,
                "transaction": {
                    "reference": mouvement.reference,
                    "montant": mouvement.montant,
                    "operateur": mouvement.operateur,
                    "simulee": mouvement.simulee,
                },
            }
        )


class LitigeVueEnsemble(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """/api/litiges/ — contestation d'une participation."""

    permission_classes = [NumeroVerifie]
    serializer_class = LitigeSerialiseur

    def get_queryset(self):
        return Litige.objects.filter(participation__acheteur=self.request.user)
