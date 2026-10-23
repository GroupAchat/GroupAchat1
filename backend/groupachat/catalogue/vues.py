# -*- coding: utf-8 -*-
"""Catalogue public : rayons, produits et campagnes, consultables sans compte.

Le catalogue s'explore **librement**. C'est une décision du cahier des
charges : demander un compte pour simplement regarder ferait fuir l'acheteur
qu'on cherche justement à rassurer.
"""

from __future__ import annotations

from django.db.models import Count, Prefetch, Q, Sum
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from groupachat.catalogue.models import Campagne, Categorie, Produit
from groupachat.catalogue.serialiseurs import (
    CampagneDetailSerialiseur,
    CampagneResumeSerialiseur,
    CategorieSerialiseur,
    ProduitSerialiseur,
)
from groupachat.commandes.models import Participation

# Une campagne n'apparaît au catalogue qu'une fois publiée : un brouillon
# n'est l'affaire que de son groupeur.
STATUTS_PUBLICS = [
    Campagne.Statut.EN_COURS,
    Campagne.Statut.FINANCEE,
    Campagne.Statut.DECAISSEE,
    Campagne.Statut.APPROVISIONNEMENT,
    Campagne.Statut.DISTRIBUTION,
    Campagne.Statut.TERMINEE,
]

_PAYEES = Q(participations__statut__in=Participation.STATUTS_PAYES)


def campagnes_avec_avancement():
    """Campagnes publiques, jauge comprise, en une seule requête.

    Les agrégats sont posés ici plutôt que lus sur le modèle : sans eux,
    afficher vingt vignettes coûterait quarante requêtes de plus.
    """
    return (
        Campagne.objects.filter(statut__in=STATUTS_PUBLICS)
        .select_related("produit", "produit__categorie", "groupeur",
                        "groupeur__reputation", "groupeur__dossier_kyc")
        .prefetch_related("produit__images", "paliers", "medias")
        .annotate(
            total_pieces=Sum("participations__quantite", filter=_PAYEES, default=0),
            total_collecte=Sum("participations__montant_total", filter=_PAYEES, default=0),
            total_participants=Count(
                "participations__acheteur", filter=_PAYEES, distinct=True
            ),
        )
    )


class CategorieVueEnsemble(viewsets.ReadOnlyModelViewSet):
    """GET /api/catalogue/categories/ — les rayons, en arbre."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CategorieSerialiseur
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        # Seuls les rayons principaux sont listés ; les sous-rayons sont
        # rendus à l'intérieur de leur parent.
        return (
            Categorie.objects.filter(active=True, parent__isnull=True)
            .prefetch_related(
                Prefetch(
                    "sous_categories",
                    queryset=Categorie.objects.filter(active=True),
                )
            )
            .annotate(
                nombre_campagnes=Count(
                    "produits__campagnes",
                    filter=Q(produits__campagnes__statut=Campagne.Statut.EN_COURS),
                    distinct=True,
                )
            )
        )


class ProduitVueEnsemble(viewsets.ReadOnlyModelViewSet):
    """GET /api/catalogue/produits/ — les fiches produit."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProduitSerialiseur
    lookup_field = "slug"

    def get_queryset(self):
        produits = (
            Produit.objects.filter(actif=True)
            .select_related("categorie")
            .prefetch_related("images")
            .annotate(
                campagnes_en_cours=Count(
                    "campagnes",
                    filter=Q(campagnes__statut=Campagne.Statut.EN_COURS),
                    distinct=True,
                )
            )
        )

        parametres = self.request.query_params
        if (categorie := parametres.get("categorie")):
            # Choisir un rayon principal doit remonter aussi ses sous-rayons,
            # sinon « Électronique » paraît vide alors que tout est rangé dans
            # « Téléphonie ».
            produits = produits.filter(
                Q(categorie__slug=categorie) | Q(categorie__parent__slug=categorie)
            )
        if (recherche := parametres.get("recherche")):
            produits = produits.filter(
                Q(nom__icontains=recherche)
                | Q(marque__icontains=recherche)
                | Q(description__icontains=recherche)
            )
        return produits

    @action(detail=True, methods=["get"])
    def campagnes(self, requete, slug=None):
        """Les offres en cours sur ce produit, pour les comparer."""
        offres = campagnes_avec_avancement().filter(
            produit__slug=slug, statut=Campagne.Statut.EN_COURS
        ).order_by("prix_unitaire")
        return Response(
            CampagneResumeSerialiseur(
                offres, many=True, context=self.get_serializer_context()
            ).data
        )


class CampagneVueEnsemble(viewsets.ReadOnlyModelViewSet):
    """GET /api/catalogue/campagnes/ — les campagnes visibles de tous."""

    permission_classes = [permissions.AllowAny]

    TRIS = {
        "recent": "-publiee_le",
        "fin_proche": "date_limite",
        "prix": "prix_unitaire",
        "populaire": "-total_participants",
    }

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CampagneDetailSerialiseur
        return CampagneResumeSerialiseur

    def get_queryset(self):
        campagnes = campagnes_avec_avancement()
        parametres = self.request.query_params

        if self.action == "retrieve":
            return campagnes.annotate(
                nombre_commentaires=Count(
                    "commentaires",
                    filter=Q(commentaires__masque_le__isnull=True),
                    distinct=True,
                )
            )

        # Par défaut on ne montre que ce à quoi on peut encore participer :
        # une liste ouverte sur les campagnes terminées donnerait l'impression
        # d'une place de marché morte.
        statut = parametres.get("statut", Campagne.Statut.EN_COURS)
        if statut != "tous":
            campagnes = campagnes.filter(statut=statut)

        if (categorie := parametres.get("categorie")):
            campagnes = campagnes.filter(
                Q(produit__categorie__slug=categorie)
                | Q(produit__categorie__parent__slug=categorie)
            )
        if (produit := parametres.get("produit")):
            campagnes = campagnes.filter(produit__slug=produit)
        if (groupeur := parametres.get("groupeur")):
            campagnes = campagnes.filter(groupeur_id=groupeur)
        if (recherche := parametres.get("recherche")):
            campagnes = campagnes.filter(
                Q(titre__icontains=recherche)
                | Q(produit__nom__icontains=recherche)
                | Q(produit__marque__icontains=recherche)
            )

        tri = self.TRIS.get(parametres.get("tri", "recent"), "-publiee_le")
        return campagnes.order_by(tri, "-id")
