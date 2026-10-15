# -*- coding: utf-8 -*-
"""Les campagnes — ce que l'acheteur appelle « un groupage ».

Le mot diffère volontairement entre le code et l'écran : « campagne » est le
terme interne, « groupage » est celui que l'utilisateur emploie déjà. Les
sérialiseurs ne traduisent pas, c'est l'interface qui écrit le mot visible.
"""

from __future__ import annotations

import math
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .. import domaine

#: Combien de medias une fiche produit peut porter.
#:
#: **Quatre images et deux videos.** Ce ne sont pas des reglages techniques :
#: ce sont deux decisions de produit, et elles vont dans deux directions
#: opposees.
#:
#: Quatre images, parce qu'un acheteur qui ne voit qu'une photo ne demande pas
#: la deuxieme — il passe au groupage suivant. Les faces, l'echelle, le
#: contenu reel d'une part : c'est ce qui fait acheter.
#:
#: Deux videos, parce que le public vise a un **forfait data limite** (§18.1).
#: Une video pese cent fois une photo, et la troisieme ne convainc plus
#: personne : elle ne fait que couter de l'argent a celui qui la regarde.
#: C'est pour cette raison qu'aucune ne se lance toute seule ici.
MAX_IMAGES = 4
MAX_VIDEOS = 2

#: Les deux natures de media. Rien d'autre n'est accepte.
TYPE_IMAGE = "image"
TYPE_VIDEO = "video"
TYPES_MEDIA = (TYPE_IMAGE, TYPE_VIDEO)


class Campagne(models.Model):
    """Une campagne de groupage.

    ## ⚠️ ``objectif_participants`` est un but, pas un plafond ni un minimum

    Le groupeur déclare **combien de personnes il veut** pour son groupage, et
    ce nombre est obligatoire : c'est ce qui donne un dénominateur à la barre
    de progression des cartes (§2.5).

    Trois choses qu'il **ne fait pas**, et qui doivent rester vraies :

    - il **ne limite pas** les commandes. Dépasser l'objectif est permis et
      normal — une campagne à 24 sur 20 continue de prendre des commandes.
      Aucun écran ne doit donc écrire « places disponibles » ni « complet » ;
    - il **n'impose aucun minimum**. La plateforme n'en impose pas (§7 du
      cahier des charges) : à la clôture, c'est le groupeur qui décide de
      maintenir ou d'annuler, objectif atteint ou non. Un groupage à 14 sur 20
      peut parfaitement aboutir ;
    - il **ne déclenche rien automatiquement**. Atteindre l'objectif ne clôture
      pas le groupage ; seule la date le fait.

    Autrement dit, c'est une information, pas une règle. Le jour où elle
    devient une règle, c'est le §7 qu'il faut rouvrir d'abord.

    ⚠️ **Aucun champ « prix de détail ».** Il n'y a aucun prix barré dans
    l'application (§3), et le meilleur moyen de ne pas en afficher un est de ne
    pas le stocker.
    """

    class Statut(models.TextChoices):
        OUVERTE = "ouverte", "Ouverte"
        A_DECIDER = "a-decider", "À décider"
        EN_COURS = "en-cours", "Commande en cours"
        LIVREE = "livree", "Livrée"
        ANNULEE = "annulee", "Annulée"

    class Categorie(models.TextChoices):
        ALIMENTAIRE = "alimentaire", "Alimentaire"
        VETEMENTS = "vetements", "Vêtements"
        CHAUSSURES = "chaussures", "Chaussures"
        HYGIENE = "hygiene", "Hygiène"
        MAISON = "maison", "Maison"
        ELECTRONIQUE = "electronique", "Électronique"

    groupeur = models.ForeignKey(
        "comptes.Groupeur",
        on_delete=models.PROTECT,
        related_name="campagnes",
        verbose_name="groupeur",
    )

    titre = models.CharField("titre", max_length=160)
    description = models.TextField("description")
    contenu_part = models.CharField("ce que contient une part", max_length=240)
    categorie = models.CharField(
        "catégorie", max_length=20, choices=Categorie.choices
    )

    prix_part = models.DecimalField(
        "prix d'une part",
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal("1"))],
    )

    #: Combien de personnes le groupeur veut reunir. **Obligatoire.**
    #:
    #: ⚠️ C'est le denominateur de la barre de progression, et **rien d'autre**
    #: — ni plafond, ni minimum, ni declencheur. Voir le docstring de la
    #: classe, qui dit les trois choses que ce champ ne fait pas.
    objectif_participants = models.PositiveIntegerField(
        "objectif de participants",
        validators=[MinValueValidator(1)],
    )

    #: Les medias de la fiche, **dans l'ordre d'affichage**.
    #:
    #: Chaque entree vaut `{"type": "image"|"video", "url": ..., "alt": ...}`,
    #: et une video peut porter en plus `"affiche"` — l'image montree avant
    #: qu'on la lance.
    #:
    #: ⚠️ **Des adresses, pas des fichiers deposes.** Le stockage objet reste a
    #: choisir (§18 du cahier des charges, « Stockage des medias : a definir »),
    #: et tant qu'il n'existe pas un depot de fichier n'aurait nulle part ou
    #: aller. Le jour ou il existera, c'est cette liste qui portera les
    #: adresses produites par le depot : **sa forme ne changera pas**.
    #:
    #: Du JSON plutot qu'une table liee, pour la raison qui vaut deja pour
    #: `caracteristiques` : ces lignes ne sont **jamais interrogees ni
    #: filtrees**, seulement affichees avec leur campagne, et l'ordre compte.
    #: Une table imposerait une jointure, un champ de rang a maintenir et une
    #: page d'administration de plus, pour un gain nul.
    medias = models.JSONField("médias", default=list, blank=True)

    # ── Ce que l'ecran 3 affiche, et que le modele ne portait pas ──────────
    #
    # Ces quatre champs existaient depuis le debut dans les constantes du
    # front, mais pas en base : l'ecran produit etait donc impossible a servir
    # par l'API. Les ajouter est ce qui permet au catalogue de quitter le
    # TypeScript.

    #: Le tableau de caracteristiques de l'ecran 3 : `[{"cle": …, "valeur": …}]`.
    #:
    #: Du JSON plutot qu'une table liee, et c'est un choix : ces lignes ne sont
    #: **jamais interrogees ni filtrees**, seulement affichees avec leur
    #: campagne. Une table imposerait une jointure et une page
    #: d'administration de plus pour un gain nul.
    caracteristiques = models.JSONField(
        "caractéristiques", default=list, blank=True
    )

    #: La variante **obligatoire avant de commander** — « Taille » pour C2.
    #:
    #: Vide quand il n'y en a pas, ce qui est le cas de la plupart des
    #: groupages. L'ecran 5 ne montre le selecteur que si `variante_libelle`
    #: est rempli.
    variante_libelle = models.CharField(
        "libellé de la variante", max_length=60, blank=True
    )
    variante_options = models.JSONField(
        "options de la variante", default=list, blank=True
    )

    #: Le point de remise. **Un repere public, jamais une adresse d'acheteur.**
    #:
    #: ⚠️ `blank=True` en base, **obligatoire a l'ecran**. Les deux ne disent
    #: pas la meme chose et la difference est voulue : une campagne creee par
    #: l'ecran 14 porte toujours un point de remise — le formulaire l'exige —
    #: mais le modele doit pouvoir representer les lignes qui existaient avant
    #: ces champs, et celles qu'un script d'import cree en deux temps.
    #:
    #: Le refuser en base aurait oblige a inventer une valeur de repli du genre
    #: « a preciser », qui aurait fini affichee a un acheteur.
    quartier_remise = models.CharField(
        "quartier de remise", max_length=40, blank=True
    )
    point_remise = models.CharField("point de remise", max_length=200, blank=True)
    remise_le = models.DateField("remise prévue le", null=True, blank=True)

    date_fin = models.DateTimeField("date de clôture")
    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.OUVERTE
    )

    cree_le = models.DateTimeField("créée le", auto_now_add=True)

    class Meta:
        verbose_name = "campagne"
        verbose_name_plural = "campagnes"
        ordering = ("date_fin",)
        indexes = [models.Index(fields=["statut", "date_fin"])]

    def __str__(self) -> str:
        return self.titre

    # ── Ce que l'interface affiche ──────────────────────────────────────────

    @property
    def acheteurs_confirmes(self) -> int:
        """Le nombre d'acheteurs ayant payé.

        « Acheteurs confirmés », jamais « participants » ni « commandes » :
        « confirmés » dit que ces gens ont payé, c'est rassurant, et c'est vrai.
        """
        return self.commandes.filter(statut__in=Statut_PAYANTS).count()

    #: Quand le groupeur a annoncé que le produit était arrivé (écran 15).
    #:
    #: ⚠️ **C'est un garde-fou, pas une date d'affichage.** L'arrivée est un
    #: fait unique : un groupeur qui appuie deux fois ne doit pas envoyer deux
    #: notifications. Une cloche qui répète le même message perd en une
    #: semaine le droit d'être regardée, et c'est le genre de dégât qu'on ne
    #: répare pas en retirant la répétition ensuite.
    arrivee_annoncee_le = models.DateTimeField(
        "arrivée annoncée le", null=True, blank=True
    )

    @property
    def progression(self) -> int:
        """Où en est le groupage, en pourcentage de son objectif, **plafonné à 100**.

        ⚠️ **Le plafond est dans l'affichage, pas dans le compte.** Une barre
        remplie à 120 % déborderait de sa gouttière, alors qu'un groupage qui
        dépasse son objectif est une bonne nouvelle. La barre s'arrête donc à
        plein, et le nombre écrit à côté continue de monter : « 24 personnes
        sur 20 ». C'est la seule façon de montrer un dépassement sans laisser
        croire à une limite.

        Un objectif à zéro ne devrait pas exister — le champ le refuse — mais
        la division est protégée quand même : une ancienne ligne mal reprise ne
        doit pas faire tomber le fil entier.
        """
        if not self.objectif_participants:
            return 0
        part = self.acheteurs_confirmes / self.objectif_participants
        # ⚠️ **Arrondi vers le bas, pas au plus proche.** Une barre ne doit
        # jamais surestimer : afficher 100 % à 39 acheteurs sur 40 ferait
        # croire l'objectif atteint alors qu'il manque quelqu'un. Et
        # `round` de Python arrondit 2,5 à **2** (arrondi au pair), là où le
        # `Math.round` de JavaScript donne 3 : les deux côtés auraient affiché
        # des pourcentages differents sur le meme groupage.
        return min(100, math.floor(part * 100))

    @property
    def objectif_atteint(self) -> bool:
        """L'objectif est-il atteint ?

        ⚠️ **Ne conditionne rien.** Sert à écrire « objectif atteint » sur une
        carte, pas à autoriser ou refuser quoi que ce soit.
        """
        return self.acheteurs_confirmes >= self.objectif_participants

    @property
    def collecte_sur_les_parts(self) -> Decimal:
        """La collecte **hors frais de livraison**.

        C'est l'assiette du retrait du groupeur, et c'est pour ça qu'elle exclut les
        frais : ceux-ci vont au transporteur et ne passent pas par le groupeur.
        """
        total = self.commandes.filter(statut__in=Statut_PAYANTS).aggregate(
            total=models.Sum("montant_parts")
        )["total"]
        return domaine.arrondir(total or Decimal("0"))

    @property
    def heures_restantes(self) -> int:
        """Le temps restant, en heures, jamais négatif.

        **C'est le seul élément de pression de l'application** (§2.4) : il n'y
        a ni minimum ni places limitées, donc c'est lui qui crée l'urgence.
        """
        delta = self.date_fin - timezone.now()
        return max(0, int(delta.total_seconds() // 3600))

    @property
    def nombre_de_questions(self) -> int:
        """Les questions **publiees**, celles que tout le monde voit.

        ⚠️ Pas `questions.count()` : les questions en verification ne sont
        visibles que de leur auteur (§1.5, ecran 10), et une en attente de
        moderation ne doit pas gonfler le compteur public — surtout si elle
        finit refusee.
        """
        return self.questions.filter(etat="publiee").count()

    @property
    def est_ouverte(self) -> bool:
        return self.statut == self.Statut.OUVERTE and self.heures_restantes > 0

    # ── Les medias ──────────────────────────────────────────────────────────

    @property
    def images(self) -> list[dict]:
        return [m for m in self.medias if m.get("type") == TYPE_IMAGE]

    @property
    def videos(self) -> list[dict]:
        return [m for m in self.medias if m.get("type") == TYPE_VIDEO]

    @property
    def media(self) -> str:
        """L'image de couverture — celle des cartes, du fil et des listes.

        ⚠️ **Toujours une image, jamais une video**, et c'est le §1.6 qui le
        veut : « une image d'abord, toujours ». Une carte dont la couverture
        serait une video resterait vide le temps du chargement, c'est-a-dire
        exactement pendant la seconde ou l'acheteur decide de s'arreter ou de
        faire defiler.

        A defaut d'image, l'affiche de la premiere video fait l'affaire : c'est
        une image, elle aussi.
        """
        images = self.images
        if images:
            return images[0].get("url", "")
        for video in self.videos:
            if video.get("affiche"):
                return video["affiche"]
        return ""

    @property
    def media_alt(self) -> str:
        """Ce que la couverture montre vraiment.

        Vide plutot qu'invente : l'interface retombe alors sur le titre du
        produit, qui est toujours plus juste qu'un texte alternatif devine.
        """
        images = self.images
        return images[0].get("alt", "") if images else ""

    def _verifier_les_medias(self) -> None:
        """Les regles de la fiche produit. Voir `MAX_IMAGES` et `MAX_VIDEOS`.

        ⚠️ **Ici et pas dans le formulaire.** Un champ grise ne protege de
        rien : il suffit d'une requete directe pour deposer trente videos, et
        c'est la facture de donnees des acheteurs qui les payerait.
        """
        if not isinstance(self.medias, list):
            raise ValidationError({"medias": "Les médias doivent être une liste."})

        for rang, media in enumerate(self.medias, start=1):
            if not isinstance(media, dict):
                raise ValidationError(
                    {"medias": f"Le média n° {rang} n'est pas un objet."}
                )
            if media.get("type") not in TYPES_MEDIA:
                raise ValidationError(
                    {
                        "medias": f"Le média n° {rang} doit être une image "
                        f"ou une vidéo."
                    }
                )
            if not str(media.get("url", "")).strip():
                raise ValidationError(
                    {"medias": f"Le média n° {rang} n'a pas d'adresse."}
                )

        images, videos = len(self.images), len(self.videos)

        if images > MAX_IMAGES:
            raise ValidationError(
                {
                    "medias": f"Une fiche porte au plus {MAX_IMAGES} images — "
                    f"celle-ci en a {images}."
                }
            )
        if videos > MAX_VIDEOS:
            raise ValidationError(
                {
                    "medias": f"Une fiche porte au plus {MAX_VIDEOS} vidéos — "
                    f"celle-ci en a {videos}."
                }
            )

        # ⚠️ Une video sans image laisse les cartes et le fil sans couverture
        # (§1.6). On accepte l'affiche de la video a la place : c'est une
        # image, et elle remplit le meme office.
        if videos and not images and not any(v.get("affiche") for v in self.videos):
            raise ValidationError(
                {
                    "medias": "Une vidéo ne suffit pas seule : ajoutez une "
                    "photo, sinon les cartes et le fil restent sans image."
                }
            )

    def clean(self) -> None:
        super().clean()
        if self.groupeur_id and not self.groupeur.peut_lancer_une_campagne:
            raise ValidationError(
                "Ce groupeur n'a pas de dossier KYC validé : il ne peut pas "
                "lancer de campagne."
            )
        self._verifier_les_medias()

    # ⚠️ **Le plafond de collecte n'est plus contrôlé ici**, et c'est une
    # correction, pas un relâchement.
    #
    # Il l'était, et ça produisait deux défauts opposés :
    #
    # - **il ne bornait rien.** À la création, la collecte vaut zéro : le
    #   contrôle passait toujours. Or le §10.4 lui donne un rôle précis —
    #   « borner le montant maximal d'un sinistre » — qui ne vaut qu'au moment
    #   où l'argent entre ;
    # - **il rendait la campagne immodifiable** dès qu'elle dépassait le
    #   plafond. `clean` s'exécute à chaque `save`, donc clôturer une campagne
    #   qui avait bien marché échouait avec « dépasserait le plafond » — un
    #   message qui n'a aucun sens au moment de clôturer. C'est le même piège
    #   que le contrôle n° 2 sur le groupeur (voir `Groupeur.save`) : une règle
    #   de saisie appliquée à toute écriture.
    #
    # Le contrôle vit désormais dans `enregistrer_paiement`, là où il borne
    # réellement l'exposition : **un paiement qui ferait dépasser le plafond
    # est refusé.**

    def collecte_prevue(self) -> Decimal:
        """La collecte déjà réalisée. Lue par le contrôle de plafond (§10.4)."""
        return self.collecte_sur_les_parts if self.pk else Decimal("0")

    def save(self, *args, **kwargs):
        """⚠️ **``full_clean`` est appelé ici, et il ne doit pas en partir.**

        Django **n'appelle pas** ``clean`` depuis ``save`` : seuls les
        formulaires et les sérialiseurs le font. Sans cette ligne, les deux
        contrôles de ``clean`` ne s'appliquent qu'aux chemins qui passent par
        un formulaire, et ``Campagne.objects.create(...)`` les traverse sans
        rien déclencher — c'est-à-dire que :

        - un groupeur **dont le dossier KYC n'est pas validé** peut lancer un
          groupage, et nous garantirions alors « vous êtes livré, ou
          remboursé » sur l'argent de quelqu'un dont nous ne savons rien ;
        - son **plafond de collecte** (§10.4) ne borne plus rien, alors que son
          seul rôle est de limiter le montant maximal d'un sinistre.

        Les deux règles vivent sur le modèle plutôt que dans une vue pour cette
        raison exacte : un bouton grisé dans l'interface ne protège de rien, il
        suffit d'une requête directe pour le contourner. ``Groupeur.save``
        porte la même ligne, pour le contrôle n° 2 du §10.5.

        ``validate_unique=False`` laisse la contrainte d'unicité à la base, qui
        la vérifie de toute façon et sans requête supplémentaire.
        """
        self.full_clean(exclude=None, validate_unique=False)
        return super().save(*args, **kwargs)


#: Les statuts de commande qui comptent comme « l'acheteur a payé ».
#:
#: Défini ici plutôt qu'importé depuis ``commandes`` pour éviter un import
#: circulaire ; le test ``test_statuts_payants_restent_synchronises`` garantit
#: que les deux listes ne divergent pas.
Statut_PAYANTS = (
    "payee",
    "cloturee",
    "chez-le-groupeur",
    "en-livraison",
    "livree",
)
