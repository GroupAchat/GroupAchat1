# -*- coding: utf-8 -*-
"""Espace acheteur : rejoindre une campagne, payer, suivre ses parts."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from groupachat.commandes.models import Avis, Participation
from groupachat.commandes.serialiseurs import (
    CreationParticipationSerialiseur,
    AvisSerialiseur,
    ReponseAvisSerialiseur,
    PaiementSerialiseur,
    ParticipationSerialiseur,
)
from groupachat.paiements.services import ErreurPaiement, encaisser
from groupachat.echanges.models import Notification
from groupachat.noyau.permissions import (
    EstAuteurOuLectureSeule,
    LectureLibreEcritureVerifiee,
    NumeroVerifie,
)
from groupachat.paiements.services import recalculer_reputation


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
                            "campagne__groupeur__reputation", "avis")
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


class AvisVueEnsemble(viewsets.ModelViewSet):
    """/api/avis/ — la note laissée au groupeur.

    **La plateforme n'arbitre pas.** Elle met en relation : un souci sur un
    produit se règle entre l'acheteur et le groupeur, par la discussion
    publique et par cette note. C'est la réputation qui sanctionne un
    mauvais groupeur, pas une décision d'arbitre.

    La lecture est ouverte à tous — un avis qu'on ne pourrait pas lire
    avant d'acheter ne servirait à rien.
    """

    serializer_class = AvisSerialiseur
    permission_classes = [LectureLibreEcritureVerifiee, EstAuteurOuLectureSeule]
    # Le droit de réponse appartient au groupeur, pas à l'auteur : sans cette
    # déclaration, la garde d'auteur lui refuserait de répondre.
    actions_ouvertes = ("repondre",)

    def get_queryset(self):
        avis = Avis.objects.select_related(
            "participation__acheteur", "participation__campagne"
        )
        parametres = self.request.query_params
        if (campagne := parametres.get("campagne")):
            avis = avis.filter(participation__campagne_id=campagne)
        if (groupeur := parametres.get("groupeur")):
            avis = avis.filter(participation__campagne__groupeur_id=groupeur)
        if parametres.get("mes_avis") and self.request.user.is_authenticated:
            avis = avis.filter(participation__acheteur=self.request.user)
        return avis

    def perform_create(self, serialiseur):
        avis = serialiseur.save()
        self._recalculer(avis)
        self._prevenir_le_groupeur(avis)

    def perform_update(self, serialiseur):
        avis = serialiseur.save(modifie_le=timezone.now())
        self._recalculer(avis)

    def perform_destroy(self, avis):
        groupeur = avis.groupeur
        avis.delete()
        recalculer_reputation(groupeur)

    def _recalculer(self, avis) -> None:
        recalculer_reputation(avis.groupeur)

    def _prevenir_le_groupeur(self, avis) -> None:
        Notification.objects.create(
            destinataire=avis.groupeur,
            genre=Notification.Genre.NOUVEL_AVIS,
            titre=f"Nouvel avis : {avis.note}/5",
            message=(avis.commentaire or "Sans commentaire.")[:160],
            campagne=avis.participation.campagne,
            lien=f"/groupeur/campagnes/{avis.participation.campagne_id}",
        )

    @action(detail=True, methods=["post"])
    def repondre(self, requete, pk=None):
        """Le groupeur répond, une fois, sous l'avis.

        Pas un fil de discussion : la conversation a sa place sous la
        campagne. Ici, c'est un droit de réponse.
        """
        avis = self.get_object()
        if avis.groupeur != requete.user:
            return Response(
                {"detail": "Seul le groupeur concerné peut répondre."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serialiseur = ReponseAvisSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)

        avis.reponse = serialiseur.validated_data["reponse"]
        avis.repondu_le = timezone.now()
        avis.save(update_fields=["reponse", "repondu_le"])
        return Response(AvisSerialiseur(avis, context=self.get_serializer_context()).data)
