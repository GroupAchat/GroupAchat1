# -*- coding: utf-8 -*-
"""Sérialiseurs des comptes, de la vérification et du KYC."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import password_validation
from rest_framework import serializers

from groupachat.comptes.models import DossierKYC, Reputation, Utilisateur


class ReputationSerialiseur(serializers.ModelSerializer):
    class Meta:
        model = Reputation
        fields = [
            "note",
            "campagnes_terminees",
            "campagnes_annulees",
            "avis_recus",
            "participants_servis",
        ]


class GroupeurPublicSerialiseur(serializers.ModelSerializer):
    """Ce qu'un visiteur voit d'un groupeur sur une fiche campagne.

    Ni numéro, ni e-mail, ni pièce d'identité : la confiance se prouve par le
    badge et la réputation, pas en exposant les coordonnées de quelqu'un.
    """

    nom_complet = serializers.CharField(read_only=True)
    badge_confiance = serializers.BooleanField(
        source="est_groupeur_valide", read_only=True
    )
    reputation = ReputationSerialiseur(read_only=True)
    nom_commerce = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "nom_complet",
            "badge_confiance",
            "reputation",
            "nom_commerce",
            "date_inscription",
        ]

    def get_nom_commerce(self, groupeur) -> str:
        dossier = getattr(groupeur, "dossier_kyc", None)
        return dossier.nom_commerce if dossier else ""


class UtilisateurSerialiseur(serializers.ModelSerializer):
    """Le compte tel que son titulaire le voit."""

    nom_complet = serializers.CharField(read_only=True)
    est_groupeur_valide = serializers.BooleanField(read_only=True)
    statut_kyc = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "telephone",
            "nom",
            "prenom",
            "nom_complet",
            "email",
            "role",
            "telephone_verifie",
            "est_groupeur_valide",
            "statut_kyc",
            "est_equipe",
            "date_inscription",
        ]
        read_only_fields = ["telephone", "role", "telephone_verifie", "est_equipe"]

    def get_statut_kyc(self, utilisateur) -> str | None:
        dossier = getattr(utilisateur, "dossier_kyc", None)
        return dossier.statut if dossier else None


class InscriptionSerialiseur(serializers.Serializer):
    """Création d'un compte : nom, prénom, numéro, mot de passe, e-mail au choix."""

    nom = serializers.CharField(max_length=80)
    prenom = serializers.CharField(max_length=80)
    telephone = serializers.CharField(max_length=20)
    mot_de_passe = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=[Utilisateur.Role.ACHETEUR, Utilisateur.Role.GROUPEUR],
        default=Utilisateur.Role.ACHETEUR,
    )

    def validate_telephone(self, valeur: str) -> str:
        # On normalise avant de chercher le doublon : sinon « +228 90 00 11 22 »
        # passerait alors que « 90001122 » existe déjà.
        numero = Utilisateur.objects.normaliser_telephone(valeur)
        if len(numero) != 8:
            raise serializers.ValidationError(
                "Numéro invalide : huit chiffres attendus."
            )
        if Utilisateur.objects.filter(telephone=numero).exists():
            raise serializers.ValidationError("Ce numéro a déjà un compte.")
        return numero

    def validate_mot_de_passe(self, valeur: str) -> str:
        password_validation.validate_password(valeur)
        return valeur

    def create(self, donnees_validees) -> Utilisateur:
        return Utilisateur.objects.create_user(
            telephone=donnees_validees["telephone"],
            mot_de_passe=donnees_validees["mot_de_passe"],
            nom=donnees_validees["nom"],
            prenom=donnees_validees["prenom"],
            email=donnees_validees.get("email", ""),
            role=donnees_validees["role"],
        )


class ConnexionSerialiseur(serializers.Serializer):
    telephone = serializers.CharField(max_length=20)
    mot_de_passe = serializers.CharField(write_only=True)


class VerificationSerialiseur(serializers.Serializer):
    telephone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6, min_length=6)


class RenvoiCodeSerialiseur(serializers.Serializer):
    telephone = serializers.CharField(max_length=20)


class DossierKYCSerialiseur(serializers.ModelSerializer):
    """Dépôt et consultation d'un dossier de confiance."""

    utilisateur = UtilisateurSerialiseur(read_only=True)
    decide_par = serializers.StringRelatedField(read_only=True)

    # Déclaré à la main : repris du modèle, il hériterait de son max_length=8
    # et refuserait « +228 90 00 11 22 » avant même la normalisation.
    numero_mobile_money = serializers.CharField(max_length=20)

    # ⚠️ **En écriture seule.** Rendus tels quels, ces champs donneraient
    # l'URL du fichier sous « /medias/kyc/… », lisible par quiconque la
    # devine. Ils servent à déposer ; ce sont `lien_recto` et `lien_verso`
    # qui servent à relire, et ils passent par une vue qui vérifie qui
    # demande.
    piece_recto = serializers.ImageField(write_only=True, required=False)
    piece_verso = serializers.ImageField(write_only=True, required=False)
    lien_recto = serializers.SerializerMethodField()
    lien_verso = serializers.SerializerMethodField()

    def _lien(self, dossier, cote: str) -> str | None:
        fichier = dossier.piece_recto if cote == "recto" else dossier.piece_verso
        if not fichier:
            return None
        chemin = f"/pieces/{dossier.pk}/{cote}/"
        requete = self.context.get("request")
        return requete.build_absolute_uri(chemin) if requete else chemin

    def get_lien_recto(self, dossier) -> str | None:
        return self._lien(dossier, "recto")

    def get_lien_verso(self, dossier) -> str | None:
        return self._lien(dossier, "verso")

    class Meta:
        model = DossierKYC
        fields = [
            "id",
            "utilisateur",
            "type_piece",
            "numero_piece",
            "piece_recto",
            "piece_verso",
            "lien_recto",
            "lien_verso",
            "numero_mobile_money",
            "nom_commerce",
            "statut",
            "motif_rejet",
            "depose_le",
            "decide_le",
            "decide_par",
        ]
        read_only_fields = ["statut", "motif_rejet", "depose_le", "decide_le"]

    def _verifier_piece(self, fichier):
        """Refuse une pièce trop lourde.

        Le plafond global de Django porte sur la requête entière ; celui-ci
        donne un message compréhensible sur le bon champ, au lieu d'une
        erreur de requête trop grande sans indication.
        """
        if fichier and fichier.size > settings.TAILLE_MAX_PIECE_OCTETS:
            maximum = settings.TAILLE_MAX_PIECE_OCTETS // (1024 * 1024)
            raise serializers.ValidationError(
                f"Image trop lourde : {maximum} Mo au maximum."
            )
        return fichier

    def validate_piece_recto(self, fichier):
        return self._verifier_piece(fichier)

    def validate_piece_verso(self, fichier):
        return self._verifier_piece(fichier)

    def validate_numero_mobile_money(self, valeur: str) -> str:
        numero = Utilisateur.objects.normaliser_telephone(valeur)
        if len(numero) != 8:
            raise serializers.ValidationError(
                "Numéro invalide : huit chiffres attendus."
            )
        return numero


class DecisionKYCSerialiseur(serializers.Serializer):
    """Verdict de l'administrateur sur un dossier."""

    decision = serializers.ChoiceField(choices=["valider", "rejeter"])
    motif = serializers.CharField(required=False, allow_blank=True)

    def validate(self, donnees):
        # Un rejet sans motif laisse le groupeur sans rien à corriger : il
        # redéposera le même dossier, et l'administrateur le rejettera encore.
        if donnees["decision"] == "rejeter" and not donnees.get("motif"):
            raise serializers.ValidationError(
                {"motif": "Indiquez ce que le groupeur doit corriger."}
            )
        return donnees
