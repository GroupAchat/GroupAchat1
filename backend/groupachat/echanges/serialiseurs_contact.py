# -*- coding: utf-8 -*-
"""Ce que l'API montre du Contact Privé.

Une seule règle gouverne ce module : **aucune coordonnée ne sort**. Le nom
public et le badge suffisent à savoir à qui l'on parle ; le nom civil, le
téléphone et l'adresse restent dans le dossier. Le laisser fuir par un champ
oublié reviendrait à livrer l'identité que le dispositif protège.
"""

from __future__ import annotations

from rest_framework import serializers

from groupachat.echanges.contact_prive import (
    DUREE_JOURS,
    PRIX_MENSUEL_FCFA,
    AbonnementContactPrive,
    Conversation,
    Message,
)


class AbonnementSerialiseur(serializers.ModelSerializer):
    actif = serializers.BooleanField(read_only=True)

    class Meta:
        model = AbonnementContactPrive
        fields = ["id", "montant", "debute_le", "expire_le", "actif",
                  "reference_paiement"]
        read_only_fields = fields


class EtatContactPriveSerialiseur(serializers.Serializer):
    """Ce que l'interface a besoin de savoir avant d'ouvrir un fil."""

    actif = serializers.BooleanField(read_only=True)
    expire_le = serializers.DateTimeField(read_only=True, allow_null=True)
    prix = serializers.IntegerField(read_only=True, default=PRIX_MENSUEL_FCFA)
    duree_jours = serializers.IntegerField(read_only=True, default=DUREE_JOURS)
    points_par_mois = serializers.IntegerField(read_only=True)


class MessageSerialiseur(serializers.ModelSerializer):
    auteur_nom = serializers.CharField(source="auteur.nom_public", read_only=True)
    de_moi = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "auteur", "auteur_nom", "de_moi", "texte", "envoye_le",
                  "lu_le", "signale_le"]
        read_only_fields = ["auteur", "envoye_le", "lu_le", "signale_le"]

    def get_de_moi(self, message) -> bool:
        demandeur = self.context.get("request")
        return bool(demandeur and message.auteur_id == demandeur.user.id)


class InterlocuteurSerialiseur(serializers.Serializer):
    """L'autre partie du fil, dévoilée selon le droit d'en savoir plus.

    `nom_utilisateur` est toujours là. `nom_complet` et `telephone`
    n'apparaissent que pour un abonné en cours, et seulement de l'OAG vers
    l'acheteur : c'est ce que l'abonnement a acheté, et il ne l'achète que
    dans ce sens — l'OAG, lui, ne paie pas pour connaître ses clients.
    """

    id = serializers.IntegerField(read_only=True)
    nom_utilisateur = serializers.CharField(source="nom_public", read_only=True)
    nom_complet = serializers.SerializerMethodField()
    telephone = serializers.SerializerMethodField()

    def _devoile(self, personne) -> bool:
        return bool(self.context.get("identite_ouverte")) and personne == self.context.get(
            "interlocuteur_devoilable"
        )

    def get_nom_complet(self, personne) -> str | None:
        return personne.nom_complet if self._devoile(personne) else None

    def get_telephone(self, personne) -> str | None:
        return personne.telephone if self._devoile(personne) else None


class ConversationSerialiseur(serializers.ModelSerializer):
    interlocuteur = serializers.SerializerMethodField()
    dernier_message = serializers.SerializerMethodField()
    non_lus = serializers.SerializerMethodField()
    je_peux_ecrire = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "interlocuteur", "campagne_initiale", "dernier_message",
                  "non_lus", "je_peux_ecrire", "ouverte_le", "dernier_message_le"]
        read_only_fields = fields

    def _moi(self):
        demandeur = self.context.get("request")
        return demandeur.user if demandeur else None

    def get_interlocuteur(self, conversation) -> dict:
        moi = self._moi()
        autre = conversation.interlocuteur_de(moi)
        contexte = dict(self.context)
        # Seul l'acheteur abonné voit l'identité, et seulement celle de l'OAG.
        contexte["interlocuteur_devoilable"] = conversation.groupeur
        contexte["identite_ouverte"] = bool(
            self.context.get("abonnement_actif") and moi == conversation.acheteur
        )
        return InterlocuteurSerialiseur(autre, context=contexte).data

    def get_dernier_message(self, conversation) -> dict | None:
        dernier = conversation.messages.order_by("-envoye_le").first()
        return (
            MessageSerialiseur(dernier, context=self.context).data if dernier else None
        )

    def get_je_peux_ecrire(self, conversation) -> bool:
        """La même règle que `_refus_d_ecrire`, dite à l'interface.

        Sans ce champ, l'interface devait deviner son propre rôle dans le fil
        — et une règle recopiée là-bas finit par diverger de celle qui décide
        vraiment, au moment où l'on appuie sur « Envoyer ».
        """
        moi = self._moi()
        if moi is not None and moi == conversation.groupeur:
            return True
        return bool(self.context.get("abonnement_actif"))

    def get_non_lus(self, conversation) -> int:
        moi = self._moi()
        return conversation.messages.filter(lu_le__isnull=True).exclude(
            auteur=moi
        ).count()


class OuvertureConversationSerialiseur(serializers.Serializer):
    """Écrire à un OAG pour la première fois."""

    groupeur = serializers.IntegerField()
    campagne = serializers.IntegerField(required=False, allow_null=True)
    texte = serializers.CharField(max_length=2000)
