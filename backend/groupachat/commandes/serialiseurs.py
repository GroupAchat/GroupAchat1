# -*- coding: utf-8 -*-
"""Sérialiseurs des participations."""

from __future__ import annotations

from rest_framework import serializers

from groupachat.catalogue.models import Campagne
from groupachat.catalogue.serialiseurs import CampagneResumeSerialiseur
from groupachat.commandes.models import Avis, Participation
from groupachat.paiements.models import Operateur


class ParticipationSerialiseur(serializers.ModelSerializer):
    """Ce que l'acheteur voit de sa propre part.

    Le code et le QR n'apparaissent qu'ici, pour son titulaire : les exposer
    ailleurs reviendrait à laisser n'importe qui retirer le colis d'un autre.
    """

    campagne = CampagneResumeSerialiseur(read_only=True)
    charge_qr = serializers.SerializerMethodField()
    statut_libelle = serializers.CharField(source="get_statut_display", read_only=True)

    # L'avis se laisse depuis cette page : il faut donc savoir ici si le
    # bouton a lieu d'être, et si quelque chose a déjà été écrit.
    peut_etre_notee = serializers.BooleanField(read_only=True)
    avis = serializers.SerializerMethodField()

    class Meta:
        model = Participation
        fields = ["id", "campagne", "quantite", "prix_unitaire_applique",
                  "montant_total", "statut", "statut_libelle", "code_retrait",
                  "charge_qr", "cree_le", "payee_le", "retiree_le",
                  "reputee_livree_le", "peut_etre_notee", "avis"]
        read_only_fields = fields

    def get_avis(self, participation) -> dict | None:
        avis = getattr(participation, "avis", None)
        return AvisSerialiseur(avis, context=self.context).data if avis else None

    def get_charge_qr(self, participation) -> str | None:
        return participation.charge_qr if participation.code_retrait else None


class ParticipantSerialiseur(serializers.ModelSerializer):
    """Le suivi nominatif que voit le groupeur sur sa campagne.

    Il a besoin du nom et du numéro — il devra joindre ces gens le jour de la
    remise. Il n'a pas besoin du code de retrait : c'est l'acheteur qui le
    présente, et le lui montrer annulerait la preuve de livraison.
    """

    nom_complet = serializers.CharField(source="acheteur.nom_complet", read_only=True)
    telephone = serializers.CharField(source="acheteur.telephone", read_only=True)
    statut_libelle = serializers.CharField(source="get_statut_display", read_only=True)

    class Meta:
        model = Participation
        fields = ["id", "nom_complet", "telephone", "quantite", "montant_total",
                  "statut", "statut_libelle", "payee_le", "retiree_le",
                  "reputee_livree_le"]
        read_only_fields = fields


class CreationParticipationSerialiseur(serializers.Serializer):
    """Rejoindre une campagne."""

    campagne = serializers.PrimaryKeyRelatedField(queryset=Campagne.objects.all())
    quantite = serializers.IntegerField(min_value=1, default=1)

    def validate(self, donnees):
        campagne = donnees["campagne"]
        acheteur = self.context["request"].user

        if not campagne.collecte_ouverte:
            raise serializers.ValidationError(
                {"campagne": "La collecte de cette campagne est close."}
            )
        if campagne.groupeur_id == acheteur.id:
            raise serializers.ValidationError(
                {"campagne": "On ne participe pas à sa propre campagne."}
            )

        # Une part déjà en attente de paiement bloquerait la suivante : on
        # préfère le dire que de laisser s'empiler des commandes fantômes.
        if Participation.objects.filter(
            campagne=campagne,
            acheteur=acheteur,
            statut=Participation.Statut.EN_ATTENTE_PAIEMENT,
        ).exists():
            raise serializers.ValidationError(
                {"campagne": "Vous avez déjà une part en attente de paiement ici."}
            )

        if campagne.quantite_maximale is not None:
            reste = campagne.quantite_maximale - campagne.quantite_reservee
            if donnees["quantite"] > reste:
                raise serializers.ValidationError(
                    {"quantite": f"Il ne reste que {max(reste, 0)} pièce(s)."}
                )
        return donnees

    def create(self, donnees_validees) -> Participation:
        campagne = donnees_validees["campagne"]
        quantite = donnees_validees["quantite"]

        # Le prix est celui du palier atteint **en comptant cette part** :
        # c'est ce que l'acheteur voit affiché au moment où il valide.
        prix = campagne.prix_pour_quantite(campagne.quantite_reservee + quantite)
        return Participation.objects.create(
            campagne=campagne,
            acheteur=self.context["request"].user,
            quantite=quantite,
            prix_unitaire_applique=prix,
            montant_total=prix * quantite,
        )


class PaiementSerialiseur(serializers.Serializer):
    """Règlement d'une part — simulé tant qu'aucun opérateur n'est branché."""

    operateur = serializers.ChoiceField(
        choices=[Operateur.TMONEY, Operateur.FLOOZ], default=Operateur.TMONEY
    )
    numero = serializers.CharField(max_length=20, required=False, allow_blank=True)


class RetraitSerialiseur(serializers.Serializer):
    """Validation d'un retrait, au code dicté ou au QR scanné."""

    code = serializers.CharField(max_length=40)


class AvisSerialiseur(serializers.ModelSerializer):
    """La note qu'un acheteur laisse, et la réponse du groupeur."""

    auteur = serializers.SerializerMethodField()
    campagne = serializers.IntegerField(
        source="participation.campagne_id", read_only=True
    )
    campagne_titre = serializers.CharField(
        source="participation.campagne.titre", read_only=True
    )

    class Meta:
        model = Avis
        fields = ["id", "participation", "campagne", "campagne_titre", "auteur",
                  "note", "commentaire", "reponse", "repondu_le", "cree_le",
                  "modifie_le"]
        read_only_fields = ["reponse", "repondu_le", "cree_le", "modifie_le"]

    def get_fields(self):
        fields = super().get_fields()
        # Sans ça, l'auteur pouvait déplacer son avis vers une autre commande
        # (et donc vers un autre groupeur) à la modification.
        if self.instance is not None:
            fields["participation"].read_only = True
        return fields

    def get_auteur(self, avis) -> dict:
        """Prénom et initiale : assez pour reconnaître, pas pour identifier."""
        acheteur = avis.participation.acheteur
        initiale = f"{acheteur.nom[:1]}." if acheteur.nom else ""
        return {"nom_affiche": f"{acheteur.prenom} {initiale}".strip()}

    def validate_participation(self, participation):
        if participation.acheteur_id != self.context["request"].user.id:
            raise serializers.ValidationError("Ce n'est pas votre commande.")
        if not participation.peut_etre_notee:
            raise serializers.ValidationError(
                "Vous pourrez noter ce groupeur une fois la collecte close."
            )
        # `OneToOne` l'interdirait de toute façon, mais avec un message
        # illisible. Mieux vaut le dire ici.
        if Avis.objects.filter(participation=participation).exists():
            raise serializers.ValidationError("Vous avez déjà noté cette commande.")
        return participation


class ReponseAvisSerialiseur(serializers.Serializer):
    """Le droit de réponse du groupeur, une fois par avis."""

    reponse = serializers.CharField(max_length=1000)
