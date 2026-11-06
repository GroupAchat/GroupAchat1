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

from groupachat.noyau import hebergement


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
        """La photo qui représente le produit dans les listes.

        Une vidéo ne fait pas une vignette : on ne retient que les photos,
        et à défaut l'aperçu d'une vidéo.

        ``all()`` puis filtrage en mémoire, et non un ``filter()`` en base :
        la vue précharge les médias, et un filtre repartirait en base — une
        requête de plus par vignette du catalogue.
        """
        medias = list(self.medias.all())
        for media in medias:
            if media.genre == MediaProduit.Genre.IMAGE:
                return media
        for media in medias:
            if media.adresse_vignette:
                return media
        return None


class MediaProduit(models.Model):
    """Photo ou vidéo d'un produit.

    **Un seul modèle pour les deux**, et non deux tables : une galerie se
    parcourt dans un ordre unique, où photos et vidéos se mêlent. Les
    séparer obligerait à les recoller à l'affichage, et à inventer une règle
    pour trancher les égalités d'ordre.

    Les plafonds — trois photos, deux vidéos — tiennent à l'usage : les
    groupeurs photographient au téléphone, sur une connexion mesurée. Au
    delà, la fiche devient lente à charger pour l'acheteur sans rien lui
    apprendre de plus.
    """

    class Genre(models.TextChoices):
        IMAGE = "image", "Photo"
        VIDEO = "video", "Vidéo"

    MAX_IMAGES = 3
    MAX_VIDEOS = 1

    produit = models.ForeignKey(
        Produit, on_delete=models.CASCADE, related_name="medias", verbose_name="produit"
    )
    genre = models.CharField(
        "type", max_length=10, choices=Genre.choices, default=Genre.IMAGE
    )

    # `FileField` et non `ImageField` : une vidéo n'est pas une image, et
    # Pillow refuserait de l'ouvrir pour la valider.
    #
    # Facultatif depuis que les médias partent chez Cloudinary : le navigateur
    # téléverse là-bas sans passer par l'API, et seul `public_id` revient. Le
    # champ reste pour le jeu de démonstration et pour tourner sans compte
    # Cloudinary — les deux sources ne coexistent jamais sur une même ligne.
    fichier = models.FileField("fichier", upload_to="produits/", blank=True)

    # L'identifiant du fichier chez l'hébergeur. On ne stocke pas l'adresse
    # complète : elle dépend des transformations demandées à l'affichage
    # (vignette carrée, recompression automatique), qui se décident au moment
    # de servir et changeraient sous une adresse figée.
    public_id = models.CharField("identifiant Cloudinary", max_length=255, blank=True)

    # L'image figée qu'on montre avant la lecture. Sans elle, une vidéo
    # apparaît comme un rectangle noir dans la galerie. Chez Cloudinary elle
    # est extraite de la vidéo : une case de moins à remplir au téléphone.
    apercu = models.ImageField(
        "aperçu de la vidéo", upload_to="produits/apercus/", blank=True
    )
    legende = models.CharField("légende", max_length=160, blank=True)
    ordre = models.PositiveSmallIntegerField("ordre d'affichage", default=0)

    class Meta:
        verbose_name = "média de produit"
        verbose_name_plural = "médias de produit"
        ordering = ["ordre", "id"]
        indexes = [models.Index(fields=["produit", "genre", "ordre"])]

    def __str__(self) -> str:
        return self.legende or f"{self.get_genre_display()} de {self.produit.nom}"

    @property
    def est_video(self) -> bool:
        return self.genre == self.Genre.VIDEO

    @property
    def adresse(self) -> str | None:
        """Où aller chercher le média lui-même."""
        if self.public_id:
            return hebergement.adresse(self.public_id, self.genre)
        return self.fichier.url if self.fichier else None

    @property
    def adresse_vignette(self) -> str | None:
        """Ce qu'on affiche dans la bande de vignettes.

        Pour une vidéo, une image figée : chez Cloudinary elle est extraite
        à la volée, en local il faut l'aperçu déposé à la main. Sans rien,
        l'interface dessine un fond de remplacement plutôt qu'une image
        cassée.
        """
        if self.public_id:
            return (
                hebergement.apercu_video(self.public_id)
                if self.est_video
                else hebergement.vignette(self.public_id)
            )
        if self.est_video:
            return self.apercu.url if self.apercu else None
        return self.fichier.url if self.fichier else None

    def clean(self) -> None:
        """Fait respecter les plafonds avant l'enregistrement.

        Posé sur le modèle et pas seulement sur le formulaire : un import,
        une commande d'administration ou un script contournerait un contrôle
        qui ne vivrait que dans le sérialiseur.
        """
        from django.core.exceptions import ValidationError

        if not self.produit_id:
            return
        deja = MediaProduit.objects.filter(
            produit_id=self.produit_id, genre=self.genre
        ).exclude(pk=self.pk).count()
        plafond = self.MAX_VIDEOS if self.est_video else self.MAX_IMAGES
        if deja >= plafond:
            libelle = "vidéos" if self.est_video else "photos"
            raise ValidationError(
                {"genre": f"Ce produit a déjà {plafond} {libelle}, le maximum."}
            )


class Campagne(models.Model):
    """L'offre d'un groupeur sur un produit : prix, minimum, date, lieu."""

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        # Mise en ligne demandée, relue avant d'apparaître. Qui y passe
        # dépend du grade (`catalogue/verification.py`) : systématique en
        # Bronze, une sur quatre en Argent, jamais en Or.
        EN_VERIFICATION = "en_verification", "En vérification"
        EN_COURS = "en_cours", "Collecte en cours"
        # La date limite est passée sans que le minimum soit atteint.
        # La campagne n'est pas morte pour autant : le groupeur peut
        # décider de maintenir la commande. Tant qu'il n'a pas
        # tranché, l'argent reste consigné — il ne repart pas tout
        # seul, c'est une règle du produit.
        MINIMUM_NON_ATTEINT = "minimum_non_atteint", "Minimum non atteint"
        FINANCEE = "financee", "Financée"
        DECAISSEE = "decaissee", "Fonds remis à l'OAG"
        APPROVISIONNEMENT = "approvisionnement", "Approvisionnement"
        DISTRIBUTION = "distribution", "Distribution en cours"
        TERMINEE = "terminee", "Terminée"
        ANNULEE = "annulee", "Annulée"

    # Les états où la collecte est jouée : plus aucun paiement n'est accepté.
    STATUTS_COLLECTE_CLOSE = {
        Statut.MINIMUM_NON_ATTEINT,
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
        help_text="Provenance, état, garantie, délais.",
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

    # Il n'y a **pas** de point de remise sur la campagne : c'est l'acheteur
    # qui choisit, part par part, entre le bureau de poste le plus proche de
    # chez lui et la livraison à son adresse. Un lieu unique imposé par l'OAG
    # obligeait la moitié de la ville à traverser Lomé pour un sac de riz, et
    # ne disait rien à celui qui voulait être livré. Le choix vit donc sur la
    # participation (`Participation.mode_retrait`).

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
    def nombre_participants(self) -> int:
        """Combien de personnes ont payé — pas combien de pièces.

        C'est ce nombre qui déclenche la chute de prix, et non le volume :
        le but est que chacun partage la campagne autour de lui. Dix pièces
        prises par une seule personne ne font pas connaître la campagne.
        """
        from groupachat.commandes.models import Participation

        return self.participations.filter(
            statut__in=Participation.STATUTS_PAYES
        ).count()

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
    def decision_attendue(self) -> bool:
        """Le groupeur doit dire s'il maintient ou s'il annule."""
        return self.statut == self.Statut.MINIMUM_NON_ATTEINT

    @property
    def collecte_ouverte(self) -> bool:
        return self.statut == self.Statut.EN_COURS and timezone.now() < self.date_limite

    def prix_pour(self, quantite: int, participants: int | None = None) -> int:
        """Prix unitaire pour **un acheteur** qui prend cette quantité.

        Deux axes, et il faut les distinguer pour comprendre le produit :

        - **la tranche**, décidée par l'acheteur seul. « La pièce à 25 000,
          à partir de 12 pièces 22 000 » : celui qui en prend 14 paie 22 000,
          celui qui en prend une paie 25 000. Personne d'autre n'y change
          rien.
        - **la chute**, décidée par le nombre de participants. Passé un
          seuil, le groupeur a prévu que chaque tranche descende encore —
          la pièce seule à 23 000, la tranche des douze à 20 000. C'est ce
          qui donne à chacun une raison de faire venir ses amis : la baisse
          profite aussi à ceux qui ont déjà payé.

        On retient **le meilleur prix** parmi les lignes auxquelles l'acheteur
        a droit, et non la dernière franchie. Un groupeur qui saisit ses
        paliers dans le désordre, ou qui donne à la tranche basse une chute
        plus forte qu'à la haute, obtient quand même un barème cohérent :
        l'acheteur n'a jamais à payer plus cher parce qu'il a pris plus.

        Le tri se fait **en mémoire, sur ``all()``**, et non par un ``filter()``
        en base : la vue précharge les paliers, et un filtre repartirait en
        base en ignorant ce préchargement — une requête de plus par vignette
        du catalogue.
        """
        if participants is None:
            participants = self.nombre_participants
        ouverts = [
            palier.prix_unitaire
            for palier in self.paliers.all()
            if palier.quantite_min <= quantite
            and palier.participants_min <= participants
        ]
        return min(ouverts, default=self.prix_unitaire)

    @property
    def prix_courant(self) -> int:
        """Le meilleur prix atteignable aujourd'hui, toutes tranches confondues.

        C'est le « à partir de » des vignettes du catalogue : ce que paierait
        quelqu'un qui prend la plus grosse tranche, au nombre de participants
        du moment. Montrer le prix de la pièce seule donnerait une campagne
        plus chère qu'elle ne l'est ; montrer la chute non atteinte serait un
        mensonge.
        """
        participants = self.nombre_participants
        ouverts = [
            palier.prix_unitaire
            for palier in self.paliers.all()
            if palier.participants_min <= participants
        ]
        return min(ouverts, default=self.prix_unitaire)


class PalierPrix(models.Model):
    """Une case du barème : une tranche, un seuil de participants, un prix.

    **Une seule table pour les deux axes**, et non deux. Le barème est une
    grille — « la pièce seule » et « à partir de 12 » en lignes, « au départ »
    et « à partir de 30 participants » en colonnes — et une grille se range
    dans une table à deux clés. Séparer les tranches des chutes aurait obligé
    à recoller les deux à chaque calcul de prix, et à inventer une règle pour
    les croisements manquants.

    La case « pièce seule, au départ » n'est pas stockée : c'est
    ``Campagne.prix_unitaire``, le prix affiché. Le reste se déclare ici.
    """

    campagne = models.ForeignKey(
        Campagne, on_delete=models.CASCADE, related_name="paliers", verbose_name="campagne"
    )
    quantite_min = models.PositiveIntegerField(
        "à partir de (pièces commandées)",
        help_text="La quantité que prend **un seul** acheteur, pas le total "
                  "de la campagne.",
    )
    participants_min = models.PositiveIntegerField(
        "à partir de (participants)",
        default=0,
        help_text="0 : ce prix s'applique dès le départ. Au-delà, c'est une "
                  "chute : le prix ne descend qu'une fois ce nombre de "
                  "participants atteint, **y compris pour ceux qui ont déjà "
                  "payé**.",
    )
    prix_unitaire = models.PositiveIntegerField("prix unitaire (FCFA)")

    class Meta:
        verbose_name = "palier de prix"
        verbose_name_plural = "paliers de prix"
        ordering = ["participants_min", "quantite_min"]
        constraints = [
            models.UniqueConstraint(
                fields=["campagne", "quantite_min", "participants_min"],
                name="palier_unique_par_case",
            )
        ]

    def __str__(self) -> str:
        tranche = f"≥ {self.quantite_min} pièces"
        if self.participants_min:
            tranche += f", à {self.participants_min} participants"
        return f"{tranche} : {self.prix_unitaire} FCFA"


class MediaCampagne(models.Model):
    """Photo du lot réellement proposé par le groupeur.

    Distincte des images du produit : celles-ci montrent la référence, celle-là
    montre la marchandise de cette campagne. C'est un gage de sérieux — et
    c'est souvent ce qui décide un acheteur hésitant, parce qu'une photo du
    carton posé par terre ne s'emprunte pas à un catalogue.

    Pas de vidéo ici, à dessein : il s'agit de prouver qu'on a la
    marchandise, pas de la mettre en scène. La démonstration du produit a sa
    place sur la fiche produit.
    """

    MAX_IMAGES = 5

    campagne = models.ForeignKey(
        Campagne, on_delete=models.CASCADE, related_name="medias", verbose_name="campagne"
    )
    image = models.ImageField("image", upload_to="campagnes/", blank=True)
    public_id = models.CharField("identifiant Cloudinary", max_length=255, blank=True)
    legende = models.CharField("légende", max_length=160, blank=True)
    ordre = models.PositiveSmallIntegerField("ordre d'affichage", default=0)

    class Meta:
        verbose_name = "média"
        verbose_name_plural = "médias"
        ordering = ["ordre", "id"]

    def __str__(self) -> str:
        return self.legende or f"Image {self.ordre} de {self.campagne}"

    @property
    def adresse(self) -> str | None:
        if self.public_id:
            return hebergement.adresse(self.public_id)
        return self.image.url if self.image else None

    @property
    def adresse_vignette(self) -> str | None:
        if self.public_id:
            return hebergement.vignette(self.public_id)
        return self.image.url if self.image else None

    def clean(self) -> None:
        """Fait respecter le plafond avant l'enregistrement.

        Posé sur le modèle comme pour les médias de produit : un import ou
        un script contournerait un contrôle qui ne vivrait que dans le
        sérialiseur.
        """
        from django.core.exceptions import ValidationError

        if not self.campagne_id:
            return
        deja = (
            MediaCampagne.objects.filter(campagne_id=self.campagne_id)
            .exclude(pk=self.pk)
            .count()
        )
        if deja >= self.MAX_IMAGES:
            raise ValidationError(
                {"image": f"Cette campagne a déjà {self.MAX_IMAGES} photos, le maximum."}
            )


class EtatDemonstration(models.Model):
    """Quelle version du jeu de démonstration est en place.

    Sans ce repère, un redéploiement laissait la base intacte et **les
    nouveautés du jeu de données n'apparaissaient jamais** : la commande de
    chargement s'arrête dès qu'elle trouve des campagnes. On comparait donc
    du code neuf à des données figées au premier démarrage.

    En notant la version chargée, le démarrage sait distinguer deux cas :
    la version du code est la même — on ne touche à rien, les comptes créés
    pendant la démonstration survivent ; elle a changé — on remet le jeu à
    plat et les nouveautés apparaissent, comme si le code venait d'être
    mis à jour.
    """

    version = models.CharField("version du jeu", max_length=40)
    chargee_le = models.DateTimeField("chargée le", default=timezone.now)

    class Meta:
        verbose_name = "état de la démonstration"
        verbose_name_plural = "état de la démonstration"

    def __str__(self) -> str:
        return f"Jeu de démonstration {self.version}"


# Déclarés dans un module à part — le droit de publier est un sujet à lui
# seul — mais réexportés ici, parce que c'est `models` que Django inspecte.
from groupachat.catalogue.publication import (  # noqa: E402
    AbonnementPublication,
    PackPublication,
)

__all__ = [
    "Categorie",
    "Produit",
    "MediaProduit",
    "Campagne",
    "MediaCampagne",
    "PalierPrix",
    "EtatDemonstration",
    "AbonnementPublication",
    "PackPublication",
]
