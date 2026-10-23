# -*- coding: utf-8 -*-
"""Catalogue : catégories, produits et campagnes d'achat groupé.

Trois niveaux, et pas un de plus :

- la **catégorie** range le catalogue et sert à la navigation ;
- le **produit** décrit la chose achetée, indépendamment de qui la propose ;
- la **campagne** est l'offre d'un groupeur sur ce produit — son prix, son
  minimum de pièces, sa date limite, son point de remise.

Séparer produit et campagne est ce qui fait la place de marché : deux
groupeurs peuvent proposer le même sac de riz à deux prix et deux dates, et
l'acheteur compare. Tout confondre dans la campagne aurait rendu cette
comparaison impossible.

Une campagne porte **un seul produit** : c'est ce que décrit le parcours — un
minimum de pièces, une part par participant — et c'est ce qui reste lisible
sur un écran de téléphone. Le volume se traduit en **paliers de prix
dégressifs**.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Categorie(models.Model):
    """Rayon du catalogue, éventuellement subdivisé en sous-rayons.

    Un seul niveau de sous-catégorie est prévu — « Électronique » puis
    « Téléphonie » suffit à ranger un catalogue de cette taille, et une
    profondeur libre obligerait à parcourir l'arbre à chaque affichage.
    """

    nom = models.CharField("nom", max_length=80)
    slug = models.SlugField("identifiant d'URL", max_length=90, unique=True, blank=True)
    description = models.CharField("description", max_length=200, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sous_categories",
        verbose_name="catégorie parente",
    )
    # Nom d'icône choisi côté interface, pas un fichier : les rayons
    # s'affichent en grille sur l'accueil et une image par rayon alourdirait
    # la première page pour rien.
    icone = models.CharField("icône", max_length=40, blank=True)
    ordre = models.PositiveSmallIntegerField("ordre d'affichage", default=0)
    active = models.BooleanField("visible au catalogue", default=True)

    class Meta:
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"
        ordering = ["ordre", "nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "nom"], name="categorie_unique_sous_son_parent"
            )
        ]

    def __str__(self) -> str:
        return f"{self.parent.nom} › {self.nom}" if self.parent_id else self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)[:90]
        super().save(*args, **kwargs)

    @property
    def est_rayon_principal(self) -> bool:
        return self.parent_id is None


class Produit(models.Model):
    """Ce qui est acheté, indépendamment de l'offre qui le propose.

    Créé par le groupeur au moment de lancer sa campagne — le sourcing est
    libre, aucun catalogue fournisseur n'est imposé. Un produit déjà saisi
    peut être repris par un autre groupeur plutôt que recréé en double.
    """

    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name="produits",
        verbose_name="catégorie",
    )
    nom = models.CharField("nom", max_length=160)
    slug = models.SlugField("identifiant d'URL", max_length=180, unique=True, blank=True)
    marque = models.CharField("marque", max_length=80, blank=True)
    description = models.TextField("description", blank=True)

    # Caractéristiques libres (taille, coloris, capacité…). Un schéma fixe ne
    # tiendrait pas : on va du sac de riz au smartphone.
    caracteristiques = models.JSONField("caractéristiques", default=dict, blank=True)

    propose_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produits_proposes",
        verbose_name="saisi par",
    )
    actif = models.BooleanField("visible au catalogue", default=True)
    cree_le = models.DateTimeField("créé le", default=timezone.now)

    class Meta:
        verbose_name = "produit"
        verbose_name_plural = "produits"
        ordering = ["nom"]
        indexes = [models.Index(fields=["categorie", "actif"])]

    def __str__(self) -> str:
        return f"{self.marque} {self.nom}".strip()

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.marque} {self.nom}")[:170] or "produit"
            slug, suffixe = base, 2
            while Produit.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{suffixe}"
                suffixe += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def image_principale(self):
        # ``all()`` puis indexation, et non ``first()`` : celui-ci relance une
        # requête même quand les images viennent d'être préchargées.
        images = list(self.images.all())
        return images[0] if images else None


class ImageProduit(models.Model):
    """Photo de référence du produit. La première sert de vignette."""

    produit = models.ForeignKey(
        Produit, on_delete=models.CASCADE, related_name="images", verbose_name="produit"
    )
    image = models.ImageField("image", upload_to="produits/")
    legende = models.CharField("légende", max_length=160, blank=True)
    ordre = models.PositiveSmallIntegerField("ordre d'affichage", default=0)

    class Meta:
        verbose_name = "image de produit"
        verbose_name_plural = "images de produit"
        ordering = ["ordre", "id"]

    def __str__(self) -> str:
        return self.legende or f"Image {self.ordre} de {self.produit.nom}"


class Campagne(models.Model):
    """L'offre d'un groupeur sur un produit : prix, minimum, date, lieu."""

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_COURS = "en_cours", "Collecte en cours"
        FINANCEE = "financee", "Financée"
        DECAISSEE = "decaissee", "Fonds remis au groupeur"
        APPROVISIONNEMENT = "approvisionnement", "Approvisionnement"
        DISTRIBUTION = "distribution", "Distribution en cours"
        TERMINEE = "terminee", "Terminée"
        ANNULEE = "annulee", "Annulée"

    # Les états où la collecte est jouée : plus aucun paiement n'est accepté.
    STATUTS_COLLECTE_CLOSE = {
        Statut.FINANCEE,
        Statut.DECAISSEE,
        Statut.APPROVISIONNEMENT,
        Statut.DISTRIBUTION,
        Statut.TERMINEE,
        Statut.ANNULEE,
    }

    produit = models.ForeignKey(
        Produit,
        on_delete=models.PROTECT,
        related_name="campagnes",
        verbose_name="produit",
    )
    groupeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="campagnes",
        verbose_name="groupeur",
    )

    # Titre de l'offre, pas du produit : « Riz Délice 25 kg — arrivage de
    # novembre ». Rempli d'office avec le nom du produit si le groupeur n'en
    # donne pas.
    titre = models.CharField("titre de l'offre", max_length=160, blank=True)
    description = models.TextField(
        "conditions de l'offre",
        blank=True,
        help_text="Provenance, état, garantie, modalités de remise.",
    )

    prix_unitaire = models.PositiveIntegerField("prix unitaire affiché (FCFA)")
    quantite_minimale = models.PositiveIntegerField(
        "minimum de pièces",
        help_text="En dessous, la campagne est annulée et tout le monde est remboursé.",
    )
    quantite_maximale = models.PositiveIntegerField(
        "maximum de pièces", null=True, blank=True
    )
    objectif_participants = models.PositiveIntegerField(
        "objectif de participants", null=True, blank=True
    )

    date_limite = models.DateTimeField("date limite de la collecte")
    point_remise = models.CharField("point de remise", max_length=200)

    statut = models.CharField(
        "statut", max_length=25, choices=Statut.choices, default=Statut.BROUILLON
    )
    cree_le = models.DateTimeField("créée le", default=timezone.now)
    publiee_le = models.DateTimeField("publiée le", null=True, blank=True)
    cloturee_le = models.DateTimeField("collecte close le", null=True, blank=True)

    # Point de départ du délai de quatorze jours au bout duquel la livraison
    # est réputée acquise.
    mise_a_disposition_le = models.DateTimeField(
        "marchandise à disposition depuis", null=True, blank=True
    )
    motif_annulation = models.TextField("motif de l'annulation", blank=True)

    class Meta:
        verbose_name = "campagne"
        verbose_name_plural = "campagnes"
        ordering = ["-publiee_le", "-cree_le"]
        indexes = [
            models.Index(fields=["statut", "date_limite"]),
            models.Index(fields=["groupeur", "statut"]),
            models.Index(fields=["produit", "statut"]),
        ]

    def __str__(self) -> str:
        return self.titre or self.produit.nom

    def save(self, *args, **kwargs):
        if not self.titre:
            self.titre = str(self.produit)[:160]
        super().save(*args, **kwargs)

    @property
    def categorie(self) -> Categorie:
        return self.produit.categorie

    # ── Avancement de la collecte ───────────────────────────────────────────
    #
    # Ces propriétés interrogent la base. Les vues de liste doivent les
    # précalculer par agrégat plutôt que de les lire vignette par vignette.

    @property
    def quantite_reservee(self) -> int:
        """Nombre de pièces effectivement payées."""
        from groupachat.commandes.models import Participation

        return (
            self.participations.filter(statut__in=Participation.STATUTS_PAYES).aggregate(
                total=models.Sum("quantite")
            )["total"]
            or 0
        )

    @property
    def montant_collecte(self) -> int:
        from groupachat.commandes.models import Participation

        return (
            self.participations.filter(statut__in=Participation.STATUTS_PAYES).aggregate(
                total=models.Sum("montant_total")
            )["total"]
            or 0
        )

    @property
    def minimum_atteint(self) -> bool:
        return self.quantite_reservee >= self.quantite_minimale

    @property
    def collecte_ouverte(self) -> bool:
        return self.statut == self.Statut.EN_COURS and timezone.now() < self.date_limite

    def prix_pour_quantite(self, quantite_totale: int) -> int:
        """Prix unitaire applicable une fois ce volume atteint.

        Le palier le plus avantageux dont le seuil est franchi l'emporte ;
        sans palier franchi, c'est le prix affiché.

        Le tri se fait **en mémoire, sur ``all()``**, et non par un ``filter()``
        en base : la vue précharge les paliers, et un filtre repartirait en
        base en ignorant ce préchargement — une requête de plus par vignette
        du catalogue.
        """
        franchis = [p for p in self.paliers.all() if p.quantite_min <= quantite_totale]
        if not franchis:
            return self.prix_unitaire
        return max(franchis, key=lambda p: p.quantite_min).prix_unitaire


class PalierPrix(models.Model):
    """Prix dégressif accordé à partir d'un certain volume.

    C'est l'argument qui fait venir les acheteurs : plus on est nombreux,
    moins chacun paie.
    """

    campagne = models.ForeignKey(
        Campagne, on_delete=models.CASCADE, related_name="paliers", verbose_name="campagne"
    )
    quantite_min = models.PositiveIntegerField("à partir de (pièces)")
    prix_unitaire = models.PositiveIntegerField("prix unitaire (FCFA)")

    class Meta:
        verbose_name = "palier de prix"
        verbose_name_plural = "paliers de prix"
        ordering = ["quantite_min"]
        constraints = [
            models.UniqueConstraint(
                fields=["campagne", "quantite_min"], name="palier_unique_par_seuil"
            )
        ]

    def __str__(self) -> str:
        return f"≥ {self.quantite_min} pièces : {self.prix_unitaire} FCFA"


class MediaCampagne(models.Model):
    """Photo du lot réellement proposé par le groupeur.

    Distincte des images du produit : celles-ci montrent la référence, celle-là
    montre la marchandise de cette campagne. C'est un gage de sérieux.
    """

    campagne = models.ForeignKey(
        Campagne, on_delete=models.CASCADE, related_name="medias", verbose_name="campagne"
    )
    image = models.ImageField("image", upload_to="campagnes/")
    legende = models.CharField("légende", max_length=160, blank=True)
    ordre = models.PositiveSmallIntegerField("ordre d'affichage", default=0)

    class Meta:
        verbose_name = "média"
        verbose_name_plural = "médias"
        ordering = ["ordre", "id"]

    def __str__(self) -> str:
        return self.legende or f"Image {self.ordre} de {self.campagne}"
