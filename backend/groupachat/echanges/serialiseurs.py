# -*- coding: utf-8 -*-
"""Sérialiseurs du fil de discussion, des demandes et des notifications."""

from __future__ import annotations

from rest_framework import serializers

from groupachat.echanges.models import (
    Commentaire,
    DemandeProduit,
    InteretDemande,
    Notification,
)


class AuteurSerialiseur(serializers.Serializer):
    """L'auteur tel qu'il apparaît publiquement sous un message.

    Prénom et initiale du nom : assez pour reconnaître quelqu'un dans un fil,
    pas assez pour l'identifier à partir d'un avis qu'il a laissé.
    """

    id = serializers.IntegerField(read_only=True)
    nom_affiche = serializers.SerializerMethodField()

    def get_nom_affiche(self, utilisateur) -> str:
        initiale = f"{utilisateur.nom[:1]}." if utilisateur.nom else ""
        return f"{utilisateur.prenom} {initiale}".strip()


class CommentaireSerialiseur(serializers.ModelSerializer):
    """Un message du fil, avec ses réponses."""

    auteur = AuteurSerialiseur(read_only=True)
    est_du_groupeur = serializers.BooleanField(read_only=True)
    reponses = serializers.SerializerMethodField()
    jaime_par_moi = serializers.SerializerMethodField()

    class Meta:
        model = Commentaire
        fields = ["id", "campagne", "auteur", "texte", "reponse_a", "reponses",
                  "nombre_jaime", "jaime_par_moi", "est_du_groupeur", "cree_le"]
        read_only_fields = ["nombre_jaime", "campagne"]

    def get_reponses(self, commentaire) -> list:
        # Un seul niveau : on ne redescend pas dans les réponses des réponses.
        if commentaire.reponse_a_id is not None:
            return []
        visibles = [r for r in commentaire.reponses.all() if r.masque_le is None]
        return CommentaireSerialiseur(
            visibles, many=True, context=self.context
        ).data

    def get_jaime_par_moi(self, commentaire) -> bool:
        aimes = self.context.get("commentaires_aimes")
        if aimes is None:
            return False
        return commentaire.id in aimes

    def validate_reponse_a(self, parent):
        if parent is None:
            return parent
        if parent.reponse_a_id is not None:
            raise serializers.ValidationError(
                "On ne répond pas à une réponse : le fil resterait illisible."
            )
        # Sans ce contrôle, une réponse « accrochée » à un message d'une autre
        # campagne était acceptée, et la notification renvoyait son auteur
        # vers la mauvaise campagne. Le contexte n'a pas de campagne hors du
        # fil (modération admin, lecture seule) : rien à comparer alors.
        campagne_id = self.context.get("campagne_id")
        if campagne_id is not None and parent.campagne_id != campagne_id:
            raise serializers.ValidationError(
                "Ce message n'appartient pas à la discussion de cette campagne."
            )
        return parent


class DemandeProduitSerialiseur(serializers.ModelSerializer):
    """Une demande de l'espace communautaire."""

    auteur = AuteurSerialiseur(read_only=True)
    categorie_nom = serializers.CharField(source="categorie.nom", read_only=True)
    interesse = serializers.SerializerMethodField()

    class Meta:
        model = DemandeProduit
        fields = ["id", "auteur", "titre", "description", "categorie",
                  "categorie_nom", "budget_indicatif", "statut", "nombre_interets",
                  "interesse", "campagne_issue", "cree_le"]
        read_only_fields = ["statut", "nombre_interets", "campagne_issue"]

    def get_interesse(self, demande) -> bool:
        interets = self.context.get("demandes_interessees")
        if interets is None:
            return False
        return demande.id in interets


class NotificationSerialiseur(serializers.ModelSerializer):
    genre_libelle = serializers.CharField(source="get_genre_display", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "genre", "genre_libelle", "titre", "message", "lien",
                  "campagne", "cree_le", "lue_le"]
        read_only_fields = fields
