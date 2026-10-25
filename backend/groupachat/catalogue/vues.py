# -*- coding: utf-8 -*-
"""Catalogue public : rayons, produits et campagnes, consultables sans compte.

Le catalogue s'explore **librement**. C'est une décision du cahier des
charges : demander un compte pour simplement regarder ferait fuir l'acheteur
qu'on cherche justement à rassurer.
"""

from __future__ import annotations

from django.db.models import Count, Prefetch, Q, Sum
from django.utils import timezone
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

# ⚠️ **Deux listes, et la distinction compte.**
#
# `STATUTS_LISTES` décide de ce qui s'affiche au catalogue : une
# campagne dont le délai est passé n'y a plus sa place, on ne peut
# plus la rejoindre.
#
# `STATUTS_CONSULTABLES` décide de ce qui reste **ouvrable par son
# adresse**. Une participante qui a payé doit pouvoir rouvrir la fiche
# depuis son historique — y retrouver le produit, le point de remise
# et les messages échangés avec le groupeur — même si le groupage n'a
# pas abouti. Renvoyer 404 lui effacerait sa propre commande.
STATUTS_LISTES = [
    Campagne.Statut.EN_COURS,
    Campagne.Statut.FINANCEE,
    Campagne.Statut.DECAISSEE,
    Campagne.Statut.APPROVISIONNEMENT,
    Campagne.Statut.DISTRIBUTION,
    Campagne.Statut.TERMINEE,
]

STATUTS_CONSULTABLES = STATUTS_LISTES + [
    Campagne.Statut.MINIMUM_NON_ATTEINT,
    Campagne.Statut.ANNULEE,
]

_PAYEES = Q(participations__statut__in=Participation.STATUTS_PAYES)


def campagnes_avec_avancement():
    """Campagnes publiques, jauge comprise, en une seule requête.

    Les agrégats sont posés ici plutôt que lus sur le modèle : sans eux,
    afficher vingt vignettes coûterait quarante requêtes de plus.
    """
    return (
        Campagne.objects.filter(statut__in=STATUTS_CONSULTABLES)
        .select_related("produit", "produit__categorie", "groupeur",
                        "groupeur__reputation", "groupeur__dossier_kyc")
        .prefetch_related("produit__medias", "paliers", "medias")
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
            .prefetch_related("medias")
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

        # La fiche s'ouvre quel que soit le sort de la campagne ; seul
        # un brouillon reste privé, et son groupeur a son propre espace.
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
        campagnes = (
            campagnes.filter(statut__in=STATUTS_LISTES)
            if statut == "tous"
            else campagnes.filter(statut=statut)
        )

        # ⚠️ Une collecte dépassée doit quitter la liste **tout de
        # suite**, sans attendre la tâche horaire de clôture. Sinon
        # elle reste visible jusqu'à une heure après son échéance, et
        # quelqu'un peut encore tenter d'y participer.
        if statut == Campagne.Statut.EN_COURS:
            campagnes = campagnes.filter(date_limite__gt=timezone.now())

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
