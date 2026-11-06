# -*- coding: utf-8 -*-
"""Sérialiseurs des comptes, de la vérification et du KYC."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import password_validation
from rest_framework import serializers

from groupachat.comptes import grades, noms
from groupachat.comptes.models import DossierKYC, Reputation, Utilisateur


class PointsSerialiseur(serializers.Serializer):
    """Les deux compteurs, et ce qu'ils ouvrent.

    `cumules` décide du grade et des accès, `solde` est la monnaie. Les
    exposer séparément évite qu'une interface présente l'un pour l'autre —
    « il vous reste 120 points » et « vous avez gagné 120 points » ne veulent
    pas dire la même chose.
    """

    cumules = serializers.IntegerField(read_only=True)
    solde = serializers.IntegerField(read_only=True)
    grade = serializers.CharField(read_only=True)
    commission_centiemes = serializers.IntegerField(read_only=True)
    prochain_palier = serializers.SerializerMethodField()

    def get_prochain_palier(self, compteur) -> dict | None:
        suite = grades.prochain_palier(compteur.cumules)
        if suite is None:
            return None
        grade, restant = suite
        return {"grade": grade, "points_restants": restant}


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
    """Ce qu'un acheteur voit d'un groupeur, et rien de plus.

    **L'acheteur et le groupeur ne se connaissent pas.** Le groupeur n'existe
    ici que sous son nom d'utilisateur ; son nom civil, son numéro et
    l'enseigne de son commerce restent dans son dossier. Seul l'abonnement
    Contact Privé ouvre le pont, et il passe par une autre vue que celle-ci.

    Ce que l'acheteur reçoit à la place, c'est de quoi décider : depuis quand
    le groupeur est là, s'il est vérifié, combien de groupages il a menés à
    terme et ce que les autres en ont dit. Aucun de ces éléments ne s'achète.

    L'enseigne a été retirée volontairement : la donner permettrait à
    l'acheteur de se rendre à la boutique et de court-circuiter la plateforme
    dès la deuxième commande — là où ni le séquestre ni l'assurance ne jouent.
    """

    nom_utilisateur = serializers.CharField(source="nom_public", read_only=True)
    badge_confiance = serializers.BooleanField(
        source="est_groupeur_valide", read_only=True
    )
    reputation = ReputationSerialiseur(read_only=True)
    grade = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "nom_utilisateur",
            "badge_confiance",
            "grade",
            "reputation",
            "date_inscription",
        ]

    def get_grade(self, groupeur) -> str:
        """Le grade se voit : c'est un des rares repères dont dispose
        l'acheteur, puisqu'il ne connaît pas son vendeur. Le solde de points,
        lui, ne regarde personne d'autre que son titulaire."""
        compteur = getattr(groupeur, "points", None)
        return compteur.grade if compteur else grades.Grade.NOUVEAU


class UtilisateurSerialiseur(serializers.ModelSerializer):
    """Le compte tel que son titulaire le voit."""

    nom_complet = serializers.CharField(read_only=True)
    nom_public = serializers.CharField(read_only=True)
    est_groupeur_valide = serializers.BooleanField(read_only=True)
    statut_kyc = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "telephone",
            "nom",
            "prenom",
            "nom_complet",
            "nom_utilisateur",
            "nom_public",
            "email",
            "role",
            "telephone_verifie",
            "est_groupeur_valide",
            "statut_kyc",
            "points",
            "est_equipe",
            "date_inscription",
        ]
        # Le nom d'utilisateur ne se modifie pas depuis le profil : la note,
        # les avis et les groupages y sont attachés, et le laisser changer
        # offrirait un moyen simple d'effacer un mauvais historique. Seul un
        # administrateur peut le faire, et le changement laisse une trace.
        read_only_fields = [
            "telephone",
            "role",
            "telephone_verifie",
            "est_equipe",
            "nom_utilisateur",
        ]

    def get_statut_kyc(self, utilisateur) -> str | None:
        dossier = getattr(utilisateur, "dossier_kyc", None)
        return dossier.statut if dossier else None

    def get_points(self, utilisateur) -> dict:
        # `get_or_create` plutôt qu'un défaut vide : un compte qui n'a jamais
        # rien gagné a quand même un compteur, et l'interface n'a pas à
        # distinguer « zéro point » de « pas encore de compteur ».
        from groupachat.comptes.points import compteur_de

        return PointsSerialiseur(compteur_de(utilisateur)).data


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
    # Obligatoire pour un groupeur — c'est sous ce nom qu'il existera pour
    # tout le monde —, facultatif pour un acheteur, qui retombe alors sur son
    # prénom et une initiale.
    nom_utilisateur = serializers.CharField(
        max_length=noms.LONGUEUR_MAX, required=False, allow_blank=True
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

    def validate_nom_utilisateur(self, valeur: str) -> str:
        valeur = (valeur or "").strip()
        if not valeur:
            return ""
        noms.valider(valeur)
        # On compare les formes normalisées, sinon « faya02 » passerait à
        # côté de « Faya-02 » et aucun acheteur ne les distinguerait.
        if Utilisateur.objects.filter(
            nom_utilisateur_repere=noms.normaliser(valeur)
        ).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return valeur

    def validate(self, donnees):
        if donnees["role"] == Utilisateur.Role.GROUPEUR and not donnees.get(
            "nom_utilisateur"
        ):
            raise serializers.ValidationError(
                {
                    "nom_utilisateur": "Un groupeur choisit le nom sous lequel "
                    "les acheteurs le connaîtront."
                }
            )
        return donnees

    def create(self, donnees_validees) -> Utilisateur:
        return Utilisateur.objects.create_user(
            telephone=donnees_validees["telephone"],
            mot_de_passe=donnees_validees["mot_de_passe"],
            nom=donnees_validees["nom"],
            prenom=donnees_validees["prenom"],
            email=donnees_validees.get("email", ""),
            nom_utilisateur=donnees_validees.get("nom_utilisateur") or None,
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

    # Le nom sous lequel les acheteurs connaîtront ce groupeur. Demandé ici
    # et non à l'inscription : on s'inscrit d'abord comme acheteur, et c'est
    # le dépôt du dossier qui fait devenir groupeur. Il est **obligatoire**,
    # parce qu'un groupeur sans nom choisi retomberait sur son prénom et
    # l'initiale de son nom — soit exactement l'identité qu'on protège.
    nom_utilisateur = serializers.CharField(
        max_length=noms.LONGUEUR_MAX, write_only=True, required=False, allow_blank=True
    )

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
            "nom_utilisateur",
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

    def validate_nom_utilisateur(self, valeur: str) -> str:
        valeur = (valeur or "").strip()
        if not valeur:
            return ""
        noms.valider(valeur)
        # On compare les formes normalisées : « faya02 » et « Faya-02 » sont
        # le même nom pour un acheteur, la base doit en dire autant.
        deja_pris = Utilisateur.objects.filter(
            nom_utilisateur_repere=noms.normaliser(valeur)
        )
        demandeur = self.context.get("request")
        if demandeur is not None and demandeur.user.is_authenticated:
            deja_pris = deja_pris.exclude(pk=demandeur.user.pk)
        if deja_pris.exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return valeur

    def validate(self, donnees):
        demandeur = self.context.get("request")
        porteur = demandeur.user if demandeur is not None else None
        if not donnees.get("nom_utilisateur") and not (
            porteur and porteur.nom_utilisateur
        ):
            raise serializers.ValidationError(
                {
                    "nom_utilisateur": "Choisissez le nom sous lequel les "
                    "acheteurs vous connaîtront. Ils ne verront rien d'autre."
                }
            )
        return donnees

    def create(self, donnees_validees):
        # Le nom vit sur le compte, pas sur le dossier : il sert partout,
        # bien au-delà du KYC.
        choisi = donnees_validees.pop("nom_utilisateur", "")
        dossier = super().create(donnees_validees)
        if choisi:
            dossier.utilisateur.nom_utilisateur = choisi
            dossier.utilisateur.save(
                update_fields=["nom_utilisateur", "nom_utilisateur_repere"]
            )
        return dossier

    def update(self, instance, donnees_validees):
        choisi = donnees_validees.pop("nom_utilisateur", "")
        dossier = super().update(instance, donnees_validees)
        # Un dossier en correction peut encore changer de nom : rien n'est
        # encore publié sous celui-ci. Après validation, seul un
        # administrateur le peut.
        if choisi and dossier.statut != DossierKYC.Statut.VALIDE:
            dossier.utilisateur.nom_utilisateur = choisi
            dossier.utilisateur.save(
                update_fields=["nom_utilisateur", "nom_utilisateur_repere"]
            )
        return dossier


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
