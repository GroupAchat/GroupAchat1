# -*- coding: utf-8 -*-
"""Espace acheteur : rejoindre une campagne, payer, suivre ses parts."""

from __future__ import annotations

from django.db import models
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from groupachat.commandes.models import Avis, Participation, Reclamation
from groupachat.commandes.serialiseurs import (
    CreationParticipationSerialiseur,
    AvisSerialiseur,
    ReponseAvisSerialiseur,
    PaiementSerialiseur,
    ParticipationSerialiseur,
    ReclamationSerialiseur,
    CreationReclamationSerialiseur,
)
from groupachat.paiements.services import ErreurPaiement, encaisser
from groupachat.echanges.models import Notification
from groupachat.noyau.permissions import (
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
    permission_classes = [LectureLibreEcritureVerifiee]

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
                {"detail": "Seul l'OAG concerné peut répondre."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serialiseur = ReponseAvisSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)

        avis.reponse = serialiseur.validated_data["reponse"]
        avis.repondu_le = timezone.now()
        avis.save(update_fields=["reponse", "repondu_le"])
        return Response(AvisSerialiseur(avis, context=self.get_serializer_context()).data)


class ReclamationVueEnsemble(viewsets.ModelViewSet):
    """/api/reclamations/ — gestion des réclamations en 5 étapes selon le nouveau cahier des charges."""

    permission_classes = [NumeroVerifie]

    def get_queryset(self):
        user = self.request.user
        qs = Reclamation.objects.select_related(
            "participation",
            "participation__campagne",
            "participation__acheteur",
            "auteur",
        )
        if user.is_staff or getattr(user, "est_equipe", False):
            return qs
        # Si c'est un OAG, il voit les réclamations sur ses campagnes + celles qu'il a éventuellement ouvertes
        if getattr(user, "est_groupeur_valide", False):
            return qs.filter(
                models.Q(auteur=user) | models.Q(participation__campagne__groupeur=user)
            )
        # Sinon l'acheteur ne voit que les siennes
        return qs.filter(auteur=user)

    def get_serializer_class(self):
        if self.action == "create":
            return CreationReclamationSerialiseur
        return ReclamationSerialiseur

    def create(self, requete, *args, **kwargs):
        serialiseur = self.get_serializer(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        participation = serialiseur.validated_data["participation"]
        numero = Reclamation.engendrer_numero(participation.id)
        reclamation = serialiseur.save(
            auteur=self.request.user,
            numero_dossier=numero,
            etape=Reclamation.Etape.ACCUSE_RECEPTION,
        )
        # Notifier l'acheteur (accusé de réception)
        Notification.objects.create(
            destinataire=self.request.user,
            genre=Notification.Genre.SYSTEME,
            titre=f"Dossier {numero} ouvert",
            message=f"Votre réclamation pour « {participation.campagne.titre} » a été enregistrée. Elle est en cours d'examen.",
            campagne=participation.campagne,
            lien=f"/mes-achats/{participation.id}",
        )
        # Notifier l'OAG (phase contradictoire)
        Notification.objects.create(
            destinataire=participation.campagne.groupeur,
            genre=Notification.Genre.SYSTEME,
            titre=f"Réclamation ouverte : {numero}",
            message=f"Une réclamation ({reclamation.get_motif_display()}) a été déposée sur votre commande. Vous pouvez apporter vos explications.",
            campagne=participation.campagne,
            lien=f"/groupeur/campagnes/{participation.campagne.id}",
        )
        return Response(
            ReclamationSerialiseur(
                reclamation, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def repondre_oag(self, requete, pk=None):
        """L'OAG apporte ses éléments contradictoires."""
        reclamation = self.get_object()
        if reclamation.participation.campagne.groupeur != requete.user and not requete.user.is_staff:
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)
        reponse = requete.data.get("reponse_oag", "").strip()
        if not reponse:
            return Response({"detail": "La réponse ne peut pas être vide."}, status=status.HTTP_400_BAD_REQUEST)
        reclamation.reponse_oag = reponse
        reclamation.etape = Reclamation.Etape.ANALYSE
        reclamation.save(update_fields=["reponse_oag", "etape", "mis_a_jour_le"])
        return Response(ReclamationSerialiseur(reclamation, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def trancher(self, requete, pk=None):
        """L'administrateur ou gestionnaire litiges rend sa décision motivée et accorde un éventuel remboursement."""
        if not requete.user.is_staff and not getattr(requete.user, "est_equipe", False):
            return Response({"detail": "Réservé à l'équipe."}, status=status.HTTP_403_FORBIDDEN)
        reclamation = self.get_object()
        decision = requete.data.get("decision", "").strip()
        remboursement = int(requete.data.get("remboursement_accorde", 0))
        reclamation.decision = decision
        reclamation.remboursement_accorde = max(0, remboursement)
        reclamation.etape = Reclamation.Etape.DECISION
        reclamation.save(update_fields=["decision", "remboursement_accorde", "etape", "mis_a_jour_le"])

        # Notifier l'acheteur
        Notification.objects.create(
            destinataire=reclamation.auteur,
            genre=Notification.Genre.SYSTEME,
            titre=f"Décision rendue : {reclamation.numero_dossier}",
            message=f"Décision : {decision}" + (f" Remboursement de {remboursement} FCFA accordé." if remboursement > 0 else ""),
            campagne=reclamation.participation.campagne,
            lien=f"/mes-achats/{reclamation.participation.id}",
        )
        return Response(ReclamationSerialiseur(reclamation, context=self.get_serializer_context()).data)

