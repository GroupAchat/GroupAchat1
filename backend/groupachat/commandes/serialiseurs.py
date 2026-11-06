# -*- coding: utf-8 -*-
"""Sérialiseurs des participations."""

from __future__ import annotations

from rest_framework import serializers

from groupachat.catalogue.models import Campagne
from groupachat.catalogue.serialiseurs import CampagneResumeSerialiseur
from groupachat.commandes.models import Avis, Participation, Reclamation
from groupachat.comptes import parrainage
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
    mode_retrait_libelle = serializers.CharField(
        source="get_mode_retrait_display", read_only=True
    )
    destination = serializers.CharField(read_only=True)

    class Meta:
        model = Participation
        fields = ["id", "campagne", "quantite", "prix_unitaire_applique",
                  "montant_total", "statut", "statut_libelle", "code_retrait",
                  "code_otp_sms",
                  "charge_qr", "mode_retrait", "mode_retrait_libelle",
                  "bureau_poste", "adresse_livraison", "destination",
                  "cree_le", "payee_le", "retiree_le",
                  "peut_etre_notee", "avis"]
        read_only_fields = fields

    def get_avis(self, participation) -> dict | None:
        avis = getattr(participation, "avis", None)
        return AvisSerialiseur(avis, context=self.context).data if avis else None

    def get_charge_qr(self, participation) -> str | None:
        return participation.charge_qr if participation.code_retrait else None


class ParticipantSerialiseur(serializers.ModelSerializer):
    """La liste des participants que voit le groupeur sur sa campagne.

    **Il ne connaît pas ses acheteurs**, pas plus qu'ils ne le connaissent :
    chacun n'apparaît que sous son nom d'utilisateur. Le groupeur n'a besoin
    de rien de plus pour préparer les lots, et la remise se fait sur
    présentation d'un code, pas d'un carnet d'adresses.

    Il n'a pas non plus le code de retrait : c'est l'acheteur qui le présente,
    et le lui montrer annulerait la preuve de livraison.
    """

    nom_utilisateur = serializers.CharField(source="acheteur.nom_public", read_only=True)
    nom_complet = serializers.CharField(source="acheteur.nom_complet", read_only=True)
    statut_libelle = serializers.CharField(source="get_statut_display", read_only=True)
    # `destination_pour_l_oag` et non `destination` : l'adresse de livraison
    # designe un domicile, et l'OAG ne connait pas ses acheteurs. Un bureau de
    # poste, lui, est un lieu public — le nommer ne dit rien de personne.
    destination = serializers.CharField(
        source="destination_pour_l_oag", read_only=True
    )

    # **Qui** a remis, et non qui a recu : le nom du livreur ne dit rien a
    # l'OAG, celui du transporteur lui dit que l'agence a fait son travail.
    remis_par = serializers.SerializerMethodField()

    class Meta:
        model = Participation
        fields = ["id", "nom_utilisateur", "nom_complet", "quantite", "montant_total",
                  "statut", "statut_libelle", "mode_retrait", "destination",
                  "remis_par", "payee_le", "retiree_le"]
        read_only_fields = fields

    def get_remis_par(self, participation) -> str:
        livreur = participation.remise_par
        if livreur is None:
            return ""
        return livreur.get_transporteur_display() if livreur.transporteur else "l'équipe"


class CreationParticipationSerialiseur(serializers.Serializer):
    """Rejoindre une campagne."""

    campagne = serializers.PrimaryKeyRelatedField(queryset=Campagne.objects.all())
    quantite = serializers.IntegerField(min_value=1, default=1)
    mode_retrait = serializers.ChoiceField(
        choices=Participation.ModeRetrait.choices,
        default=Participation.ModeRetrait.POSTE,
    )
    bureau_poste = serializers.CharField(
        max_length=120, required=False, allow_blank=True
    )
    adresse_livraison = serializers.CharField(
        max_length=250, required=False, allow_blank=True
    )
    # Le code voyage avec la **commande** : c'est le dernier moment où l'on
    # sait encore d'où vient la personne, le code vivant dans son navigateur.
    code_parrainage = serializers.CharField(
        max_length=12, required=False, allow_blank=True
    )

    def validate(self, donnees):
        campagne = donnees["campagne"]
        acheteur = self.context["request"].user

        # La destination est demandee a la commande, et non a la livraison :
        # c'est ce qui decide si l'agence depose au bureau de poste ou passe
        # a la porte, et l'agence prepare sa tournee avant que le lot arrive.
        if donnees["mode_retrait"] == Participation.ModeRetrait.LIVRAISON:
            if not (donnees.get("adresse_livraison") or "").strip():
                raise serializers.ValidationError(
                    {"adresse_livraison": "Dites ou vous faire livrer."}
                )
            donnees["bureau_poste"] = ""
        else:
            if not (donnees.get("bureau_poste") or "").strip():
                raise serializers.ValidationError(
                    {"bureau_poste": "Dites quel bureau de poste vous arrange."}
                )
            donnees["adresse_livraison"] = ""

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

        # Le prix dépend de **ce que cet acheteur prend**, pas du volume déjà
        # collecté : c'est lui qui décide de monter à douze pièces pour passer
        # dans la tranche basse. S'y ajoute la chute éventuelle, selon le
        # nombre de participants du moment — elle pourra encore descendre
        # d'ici la clôture, jamais monter.
        prix = campagne.prix_pour(quantite)
        # Rattaché avant la création de la part, et sans rien créditer : le
        # parrainage attend le paiement (`parrainage.valider_au_paiement`).
        # Un code inconnu ou un auto-parrainage ne fait pas échouer la
        # commande — un lien se partage sans savoir qui l'a déjà utilisé.
        code = (donnees_validees.get("code_parrainage") or "").strip()
        if code:
            parrainage.rattacher(
                self.context["request"].user, code, campagne=campagne
            )

        return Participation.objects.create(
            campagne=campagne,
            acheteur=self.context["request"].user,
            quantite=quantite,
            prix_unitaire_applique=prix,
            montant_total=prix * quantite,
            mode_retrait=donnees_validees["mode_retrait"],
            bureau_poste=donnees_validees.get("bureau_poste", "").strip(),
            adresse_livraison=donnees_validees.get("adresse_livraison", "").strip(),
        )


class PaiementSerialiseur(serializers.Serializer):
    """Règlement d'une part — simulé tant qu'aucun opérateur n'est branché."""

    operateur = serializers.ChoiceField(
        choices=[Operateur.TMONEY, Operateur.FLOOZ], default=Operateur.TMONEY
    )
    numero = serializers.CharField(max_length=20, required=False, allow_blank=True)


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

    def get_auteur(self, avis) -> dict:
        """L'auteur sous son nom d'utilisateur, jamais sous son nom civil."""
        return {"nom_affiche": avis.participation.acheteur.nom_public}

    def validate_participation(self, participation):
        if participation.acheteur_id != self.context["request"].user.id:
            raise serializers.ValidationError("Ce n'est pas votre commande.")
        if not participation.peut_etre_notee:
            raise serializers.ValidationError(
                "Vous pourrez noter cet OAG une fois la collecte close."
            )
        # `OneToOne` l'interdirait de toute façon, mais avec un message
        # illisible. Mieux vaut le dire ici.
        if Avis.objects.filter(participation=participation).exists():
            raise serializers.ValidationError("Vous avez déjà noté cette commande.")
        return participation


class ReponseAvisSerialiseur(serializers.Serializer):
    """Le droit de réponse du groupeur, une fois par avis."""

    reponse = serializers.CharField(max_length=1000)


class ReclamationSerialiseur(serializers.ModelSerializer):
    """Sérialiseur pour la consultation et le suivi des 5 étapes d'une réclamation."""

    motif_libelle = serializers.CharField(source="get_motif_display", read_only=True)
    etape_libelle = serializers.CharField(source="get_etape_display", read_only=True)
    auteur_nom = serializers.CharField(source="auteur.nom_public", read_only=True)
    campagne_titre = serializers.CharField(
        source="participation.campagne.titre", read_only=True
    )

    class Meta:
        model = Reclamation
        fields = [
            "id",
            "numero_dossier",
            "participation",
            "campagne_titre",
            "auteur",
            "auteur_nom",
            "motif",
            "motif_libelle",
            "description",
            "piece_jointe",
            "etape",
            "etape_libelle",
            "reponse_oag",
            "decision",
            "remboursement_accorde",
            "cree_le",
            "mis_a_jour_le",
        ]
        read_only_fields = [
            "numero_dossier",
            "auteur",
            "auteur_nom",
            "campagne_titre",
            "etape",
            "etape_libelle",
            "reponse_oag",
            "decision",
            "remboursement_accorde",
            "cree_le",
            "mis_a_jour_le",
        ]


class CreationReclamationSerialiseur(serializers.ModelSerializer):
    """Ouverture d'un dossier de réclamation par un acheteur."""

    class Meta:
        model = Reclamation
        fields = ["participation", "motif", "description", "piece_jointe"]

    def validate_participation(self, participation):
        user = self.context["request"].user
        if participation.acheteur_id != user.id:
            raise serializers.ValidationError("Cette commande ne vous appartient pas.")
        if participation.statut not in (
            Participation.Statut.PAYEE,
            Participation.Statut.PRETE,
            Participation.Statut.RETIREE,
        ):
            raise serializers.ValidationError(
                "Une réclamation ne peut porter que sur une commande payée."
            )
        return participation

