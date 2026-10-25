# -*- coding: utf-8 -*-
"""Sérialiseurs du catalogue : catégories, produits, campagnes."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from groupachat.catalogue.models import (
    Campagne,
    Categorie,
    MediaProduit,
    MediaCampagne,
    PalierPrix,
    Produit,
)
from groupachat.comptes.serialiseurs import GroupeurPublicSerialiseur


class CategorieSerialiseur(serializers.ModelSerializer):
    """Un rayon, avec ses sous-rayons s'il en a."""

    sous_categories = serializers.SerializerMethodField()
    nombre_campagnes = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Categorie
        fields = ["id", "nom", "slug", "description", "icone", "ordre",
                  "sous_categories", "nombre_campagnes"]

    def get_sous_categories(self, categorie) -> list:
        enfants = [e for e in categorie.sous_categories.all() if e.active]
        return CategorieSerialiseur(enfants, many=True, context=self.context).data


class MediaProduitSerialiseur(serializers.ModelSerializer):
    """Une photo ou une vidéo, avec de quoi l'afficher sans deviner.

    Deux adresses et non un chemin de fichier : selon que le média est
    hébergé chez Cloudinary ou posé sur le disque, ce n'est pas la même
    chose à construire, et l'interface n'a pas à le savoir.

    `vignette` évite en plus de choisir entre le média et son image figée
    selon le genre : la règle est décidée ici, une fois.
    """

    adresse = serializers.SerializerMethodField()
    vignette = serializers.SerializerMethodField()

    class Meta:
        model = MediaProduit
        fields = ["id", "genre", "adresse", "vignette", "legende", "ordre"]

    def get_adresse(self, media) -> str | None:
        return self._absolue(media.adresse)

    def get_vignette(self, media) -> str | None:
        return self._absolue(media.adresse_vignette)

    def _absolue(self, url: str | None) -> str | None:
        """Les adresses Cloudinary sont déjà complètes ; les locales, non."""
        if not url or url.startswith("http"):
            return url
        requete = self.context.get("request")
        return requete.build_absolute_uri(url) if requete else url


class ProduitResumeSerialiseur(serializers.ModelSerializer):
    """Ce qu'il faut du produit pour une vignette de campagne."""

    image = serializers.SerializerMethodField()
    categorie_nom = serializers.CharField(source="categorie.nom", read_only=True)
    categorie_slug = serializers.CharField(source="categorie.slug", read_only=True)

    class Meta:
        model = Produit
        fields = ["id", "nom", "slug", "marque", "image",
                  "categorie", "categorie_nom", "categorie_slug"]

    def get_image(self, produit) -> str | None:
        """La vignette carrée du produit dans les listes.

        `image_principale` rend le média, pas son fichier : avec Cloudinary
        l'adresse se construit, elle ne se lit pas sur le disque.
        """
        premiere = produit.image_principale
        if premiere is None:
            return None
        url = premiere.adresse_vignette
        if not url or url.startswith("http"):
            return url
        requete = self.context.get("request")
        return requete.build_absolute_uri(url) if requete else url


class ProduitSerialiseur(serializers.ModelSerializer):
    """La fiche produit complète."""

    medias = MediaProduitSerialiseur(many=True, read_only=True)
    categorie_nom = serializers.CharField(source="categorie.nom", read_only=True)
    campagnes_en_cours = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Produit
        fields = ["id", "nom", "slug", "marque", "description", "caracteristiques",
                  "categorie", "categorie_nom", "medias", "campagnes_en_cours",
                  "cree_le"]


class PalierPrixSerialiseur(serializers.ModelSerializer):
    class Meta:
        model = PalierPrix
        fields = ["id", "quantite_min", "prix_unitaire"]


class MediaCampagneSerialiseur(serializers.ModelSerializer):
    """La photo du lot réellement proposé par le groupeur."""

    adresse = serializers.SerializerMethodField()
    vignette = serializers.SerializerMethodField()

    class Meta:
        model = MediaCampagne
        fields = ["id", "adresse", "vignette", "legende", "ordre"]

    def get_adresse(self, media) -> str | None:
        return self._absolue(media.adresse)

    def get_vignette(self, media) -> str | None:
        return self._absolue(media.adresse_vignette)

    def _absolue(self, url: str | None) -> str | None:
        if not url or url.startswith("http"):
            return url
        requete = self.context.get("request")
        return requete.build_absolute_uri(url) if requete else url


class _AvancementMixin:
    """Lit la jauge sur les agrégats posés par la vue.

    Les propriétés du modèle interrogent la base à chaque appel : les lire ici
    coûterait deux requêtes par vignette. La vue annote la requête une fois
    pour toutes, et on retombe sur les propriétés seulement si l'annotation
    manque — un objet fraîchement créé, par exemple.
    """

    def _pieces(self, campagne) -> int:
        valeur = getattr(campagne, "total_pieces", None)
        return campagne.quantite_reservee if valeur is None else valeur

    def get_quantite_reservee(self, campagne) -> int:
        return self._pieces(campagne)

    def get_montant_collecte(self, campagne) -> int:
        valeur = getattr(campagne, "total_collecte", None)
        return campagne.montant_collecte if valeur is None else valeur

    def get_nombre_participants(self, campagne) -> int:
        valeur = getattr(campagne, "total_participants", None)
        return (
            campagne.participations.filter(
                statut__in=_statuts_payes()
            ).values("acheteur").distinct().count()
            if valeur is None
            else valeur
        )

    def get_pourcentage(self, campagne) -> int:
        if not campagne.quantite_minimale:
            return 0
        return min(100, round(self._pieces(campagne) * 100 / campagne.quantite_minimale))

    def get_minimum_atteint(self, campagne) -> bool:
        return self._pieces(campagne) >= campagne.quantite_minimale

    def get_prix_courant(self, campagne) -> int:
        return campagne.prix_pour_quantite(self._pieces(campagne))

    def get_jours_restants(self, campagne) -> int:
        reste = campagne.date_limite - timezone.now()
        return max(0, reste.days)


def _statuts_payes():
    from groupachat.commandes.models import Participation

    return Participation.STATUTS_PAYES


class CampagneResumeSerialiseur(_AvancementMixin, serializers.ModelSerializer):
    """La vignette du catalogue."""

    produit = ProduitResumeSerialiseur(read_only=True)
    groupeur = GroupeurPublicSerialiseur(read_only=True)
    quantite_reservee = serializers.SerializerMethodField()
    nombre_participants = serializers.SerializerMethodField()
    pourcentage = serializers.SerializerMethodField()
    minimum_atteint = serializers.SerializerMethodField()
    prix_courant = serializers.SerializerMethodField()
    jours_restants = serializers.SerializerMethodField()

    class Meta:
        model = Campagne
        fields = ["id", "titre", "produit", "groupeur", "prix_unitaire", "prix_courant",
                  "quantite_minimale", "quantite_reservee", "nombre_participants",
                  "pourcentage", "minimum_atteint", "date_limite", "jours_restants",
                  "point_remise", "statut", "publiee_le"]


class CampagneDetailSerialiseur(CampagneResumeSerialiseur):
    """La fiche complète d'une campagne."""

    paliers = PalierPrixSerialiseur(many=True, read_only=True)
    medias = MediaCampagneSerialiseur(many=True, read_only=True)
    produit = ProduitSerialiseur(read_only=True)
    montant_collecte = serializers.SerializerMethodField()
    collecte_ouverte = serializers.BooleanField(read_only=True)
    nombre_commentaires = serializers.IntegerField(read_only=True, default=0)

    class Meta(CampagneResumeSerialiseur.Meta):
        fields = CampagneResumeSerialiseur.Meta.fields + [
            "description", "caracteristiques_offre", "quantite_maximale",
            "objectif_participants", "paliers", "medias", "montant_collecte",
            "collecte_ouverte", "mise_a_disposition_le", "motif_annulation",
            "nombre_commentaires", "cree_le",
        ]

    caracteristiques_offre = serializers.SerializerMethodField()

    def get_caracteristiques_offre(self, campagne) -> dict:
        return campagne.produit.caracteristiques or {}


class CampagneEcritureSerialiseur(serializers.ModelSerializer):
    """Création et modification d'une campagne par son groupeur."""

    paliers = PalierPrixSerialiseur(many=True, required=False)

    class Meta:
        model = Campagne
        fields = ["id", "produit", "titre", "description", "prix_unitaire",
                  "quantite_minimale", "quantite_maximale", "objectif_participants",
                  "date_limite", "point_remise", "paliers", "statut"]
        read_only_fields = ["statut"]

    def validate_date_limite(self, valeur):
        if valeur <= timezone.now():
            raise serializers.ValidationError("La date limite doit être à venir.")
        return valeur

    def validate(self, donnees):
        minimum = donnees.get("quantite_minimale", getattr(self.instance, "quantite_minimale", 0))
        maximum = donnees.get("quantite_maximale", getattr(self.instance, "quantite_maximale", None))
        if maximum is not None and maximum < minimum:
            raise serializers.ValidationError(
                {"quantite_maximale": "Le maximum ne peut pas être sous le minimum."}
            )

        # Un palier qui coûte plus cher que le prix affiché n'est pas un
        # palier : l'acheteur verrait le prix monter avec le nombre de
        # participants, soit l'inverse de ce qu'on lui promet.
        prix = donnees.get("prix_unitaire", getattr(self.instance, "prix_unitaire", 0))
        for palier in donnees.get("paliers", []):
            if palier["prix_unitaire"] >= prix:
                raise serializers.ValidationError(
                    {"paliers": "Un palier doit être moins cher que le prix affiché."}
                )
        return donnees

    def _remplacer_paliers(self, campagne, paliers) -> None:
        campagne.paliers.all().delete()
        PalierPrix.objects.bulk_create(
            PalierPrix(campagne=campagne, **palier) for palier in paliers
        )

    def create(self, donnees_validees):
        paliers = donnees_validees.pop("paliers", [])
        campagne = Campagne.objects.create(**donnees_validees)
        self._remplacer_paliers(campagne, paliers)
        return campagne

    def update(self, campagne, donnees_validees):
        paliers = donnees_validees.pop("paliers", None)
        for champ, valeur in donnees_validees.items():
            setattr(campagne, champ, valeur)
        campagne.save()
        if paliers is not None:
            self._remplacer_paliers(campagne, paliers)
        return campagne


class MediaProduitEcritureSerialiseur(serializers.ModelSerializer):
    """Dépôt d'une photo ou d'une vidéo sur un produit.

    Le navigateur a déjà téléversé le fichier chez Cloudinary : il ne reste
    ici qu'à enregistrer l'identifiant rendu. Le champ `fichier` subsiste
    pour le cas sans compte Cloudinary — tests, démonstration, poste de
    développement — mais les deux ne se remplissent jamais ensemble.

    Le plafond est vérifié ici **en plus** du modèle : la validation du
    modèle rend une erreur correcte mais brutale, celle-ci la rattache au
    bon champ et donne un message que l'interface peut afficher.
    """

    class Meta:
        model = MediaProduit
        fields = ["id", "produit", "genre", "public_id", "fichier", "apercu",
                  "legende", "ordre"]

    def validate(self, donnees):
        produit = donnees.get("produit") or getattr(self.instance, "produit", None)
        genre = donnees.get("genre") or getattr(self.instance, "genre", None)
        if produit is None or genre is None:
            return donnees

        deja = MediaProduit.objects.filter(produit=produit, genre=genre)
        if self.instance is not None:
            deja = deja.exclude(pk=self.instance.pk)

        plafond = (
            MediaProduit.MAX_VIDEOS
            if genre == MediaProduit.Genre.VIDEO
            else MediaProduit.MAX_IMAGES
        )
        if deja.count() >= plafond:
            libelle = "vidéos" if genre == MediaProduit.Genre.VIDEO else "photos"
            raise serializers.ValidationError(
                {"genre": f"Ce produit a déjà {plafond} {libelle}, le maximum."}
            )

        public_id = donnees.get("public_id") or getattr(
            self.instance, "public_id", ""
        )
        fichier = donnees.get("fichier") or getattr(self.instance, "fichier", None)
        if not public_id and not fichier:
            raise serializers.ValidationError(
                {"public_id": "Téléversez le fichier avant de l'enregistrer."}
            )

        # Une vidéo sans image figée apparaît comme un rectangle noir dans la
        # galerie. Chez Cloudinary elle est extraite à la volée ; en local il
        # faut la déposer, et mieux vaut le dire au dépôt qu'à l'écran.
        if (
            genre == MediaProduit.Genre.VIDEO
            and not public_id
            and not (donnees.get("apercu") or getattr(self.instance, "apercu", None))
        ):
            raise serializers.ValidationError(
                {"apercu": "Ajoutez une image d'aperçu pour la vidéo."}
            )
        return donnees


class ProduitEcritureSerialiseur(serializers.ModelSerializer):
    """Saisie d'un produit par un groupeur."""

    class Meta:
        model = Produit
        fields = ["id", "categorie", "nom", "marque", "description",
                  "caracteristiques", "slug"]
        read_only_fields = ["slug"]
