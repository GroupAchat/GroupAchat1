# -*- coding: utf-8 -*-
"""Sérialiseurs des demandes communautaires et des notifications."""

from __future__ import annotations

from rest_framework import serializers

from groupachat.echanges.models import (
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
        return utilisateur.nom_public


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
