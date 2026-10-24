# -*- coding: utf-8 -*-
"""Fil de discussion, espace communautaire et cloche de notifications."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import F, Prefetch
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from groupachat.catalogue.models import Campagne
from groupachat.echanges.models import (
    Commentaire,
    DemandeProduit,
    InteretDemande,
    Notification,
)
from groupachat.echanges.serialiseurs import (
    CommentaireSerialiseur,
    DemandeProduitSerialiseur,
    NotificationSerialiseur,
)
from groupachat.permissions import (
    EstAuteurOuLectureSeule,
    LectureLibreEcritureVerifiee,
)


class CommentaireVueEnsemble(viewsets.ModelViewSet):
    """/api/campagnes/<campagne>/commentaires/ — le fil public d'une campagne.

    Lisible par tout le monde, y compris sans compte : c'est ce fil qui
    rassure l'acheteur hésitant. Écrire demande un numéro vérifié.
    """

    serializer_class = CommentaireSerialiseur
    permission_classes = [LectureLibreEcritureVerifiee, EstAuteurOuLectureSeule]

    # Aimer le message d'un autre est le but : cette action échappe à la
    # règle d'auteur, qui ne vaut que pour la modification du message.
    actions_ouvertes = ("jaime",)

    @property
    def campagne_id(self):
        return self.kwargs["campagne_pk"]

    def get_queryset(self):
        return (
            Commentaire.objects.filter(
                campagne_id=self.campagne_id,
                masque_le__isnull=True,
                reponse_a__isnull=True,
            )
            .select_related("auteur", "campagne")
            .prefetch_related(
                Prefetch(
                    "reponses",
                    queryset=Commentaire.objects.filter(
                        masque_le__isnull=True
                    ).select_related("auteur"),
                )
            )
        )

    def get_serializer_context(self):
        contexte = super().get_serializer_context()
        # Les « j'aime » du lecteur sont chargés en une fois : sans ça, le fil
        # poserait une requête par message pour savoir s'il l'a déjà aimé.
        if self.request.user.is_authenticated:
            contexte["commentaires_aimes"] = set(
                self.request.user.commentaires_aimes.filter(
                    commentaire__campagne_id=self.campagne_id
                ).values_list("commentaire_id", flat=True)
            )
        return contexte

    def perform_create(self, serialiseur):
        campagne = Campagne.objects.get(pk=self.campagne_id)
        commentaire = serialiseur.save(
            auteur=self.request.user, campagne=campagne
        )
        self._notifier(campagne, commentaire)

    def _notifier(self, campagne, commentaire) -> None:
        if commentaire.reponse_a_id and commentaire.reponse_a.auteur_id != commentaire.auteur_id:
            Notification.objects.create(
                destinataire=commentaire.reponse_a.auteur,
                genre=Notification.Genre.REPONSE_COMMENTAIRE,
                titre="Réponse à votre message",
                message=commentaire.texte[:160],
                campagne=campagne,
                lien=f"/campagnes/{campagne.id}",
            )
        elif campagne.groupeur_id != commentaire.auteur_id:
            Notification.objects.create(
                destinataire=campagne.groupeur,
                genre=Notification.Genre.NOUVEAU_COMMENTAIRE,
                titre="Nouveau message sur votre campagne",
                message=commentaire.texte[:160],
                campagne=campagne,
                lien=f"/groupeur/campagnes/{campagne.id}",
            )

    def perform_update(self, serialiseur):
        serialiseur.save(modifie_le=timezone.now())

    def perform_destroy(self, commentaire):
        # L'auteur efface son propre message : là, c'est bien un masquage
        # aussi, pour que le fil garde sa cohérence (une réponse orpheline
        # n'aurait plus de sens) et la trace en cas de litige.
        commentaire.masque_le = timezone.now()
        commentaire.masque_par = self.request.user
        commentaire.motif_masquage = "Retiré par son auteur"
        commentaire.save(update_fields=["masque_le", "masque_par", "motif_masquage"])

    @action(detail=True, methods=["post"])
    def jaime(self, requete, pk=None, campagne_pk=None):
        """Aime un message, ou retire son « j'aime »."""
        commentaire = self.get_object()
        try:
            with transaction.atomic():
                InteretCommentaire = commentaire.jaime.model
                InteretCommentaire.objects.create(
                    commentaire=commentaire, utilisateur=requete.user
                )
                Commentaire.objects.filter(pk=commentaire.pk).update(
                    nombre_jaime=F("nombre_jaime") + 1
                )
            aime = True
        except IntegrityError:
            # Déjà aimé : le même geste retire le « j'aime ».
            commentaire.jaime.filter(utilisateur=requete.user).delete()
            Commentaire.objects.filter(pk=commentaire.pk, nombre_jaime__gt=0).update(
                nombre_jaime=F("nombre_jaime") - 1
            )
            aime = False

        commentaire.refresh_from_db()
        return Response({"jaime_par_moi": aime,
                         "nombre_jaime": commentaire.nombre_jaime})


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
