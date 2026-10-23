# -*- coding: utf-8 -*-
"""Espace groupeur : campagnes, suivi des paiements, distribution.

Tout ici est derrière :class:`GroupeurValide`. Tant que l'administrateur n'a
pas validé le dossier, l'espace n'est pas accessible — c'est la règle, et
c'est ce que voit le groupeur en attente : une porte fermée, pas une
interface à moitié utilisable.
"""

from __future__ import annotations

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from groupachat.catalogue.models import Campagne, Produit
from groupachat.catalogue.serialiseurs import (
    CampagneDetailSerialiseur,
    CampagneEcritureSerialiseur,
    ProduitEcritureSerialiseur,
    ProduitSerialiseur,
)
from groupachat.catalogue.vues import campagnes_avec_avancement
from groupachat.commandes.models import Participation
from groupachat.commandes.serialiseurs import (
    ParticipantSerialiseur,
    RetraitSerialiseur,
)
from groupachat.paiements.models import Decaissement
from groupachat.paiements.services import (
    ErreurPaiement,
    cloturer,
    demander_decaissement,
    mettre_a_disposition,
    sequestre_de,
    valider_retrait,
)
from groupachat.permissions import GroupeurValide

_PAYEES = Q(participations__statut__in=Participation.STATUTS_PAYES)


class CampagneGroupeurVueEnsemble(viewsets.ModelViewSet):
    """/api/groupeur/campagnes/ — les campagnes du groupeur connecté."""

    permission_classes = [GroupeurValide]

    def get_queryset(self):
        return (
            Campagne.objects.filter(groupeur=self.request.user)
            .select_related("produit", "produit__categorie", "groupeur",
                            "groupeur__reputation", "groupeur__dossier_kyc")
            .prefetch_related("paliers", "medias", "produit__images")
            .annotate(
                total_pieces=Sum("participations__quantite", filter=_PAYEES, default=0),
                total_collecte=Sum("participations__montant_total",
                                   filter=_PAYEES, default=0),
                total_participants=Count("participations__acheteur",
                                         filter=_PAYEES, distinct=True),
            )
            .order_by("-cree_le")
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CampagneEcritureSerialiseur
        return CampagneDetailSerialiseur

    def perform_create(self, serialiseur):
        serialiseur.save(groupeur=self.request.user)

    def update(self, requete, *args, **kwargs):
        campagne = self.get_object()
        # Une campagne qui a déjà encaissé ne se retouche plus : changer le
        # prix ou le minimum après coup déplacerait le contrat sous les pieds
        # de ceux qui ont déjà payé.
        if campagne.participations.filter(
            statut__in=Participation.STATUTS_PAYES
        ).exists():
            return Response(
                {"detail": "Des participants ont déjà payé : la campagne est figée."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(requete, *args, **kwargs)

    def destroy(self, requete, *args, **kwargs):
        campagne = self.get_object()
        if campagne.statut != Campagne.Statut.BROUILLON:
            return Response(
                {"detail": "Seul un brouillon peut être supprimé."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(requete, *args, **kwargs)

    def _reponse_campagne(self, campagne):
        rafraichie = self.get_queryset().get(pk=campagne.pk)
        return Response(
            CampagneDetailSerialiseur(
                rafraichie, context=self.get_serializer_context()
            ).data
        )

    @action(detail=True, methods=["post"])
    def publier(self, requete, pk=None):
        """Met la campagne au catalogue."""
        campagne = self.get_object()
        if campagne.statut != Campagne.Statut.BROUILLON:
            return Response({"detail": "Cette campagne est déjà publiée."},
                            status=status.HTTP_409_CONFLICT)
        if campagne.date_limite <= timezone.now():
            return Response({"detail": "La date limite est déjà passée."},
                            status=status.HTTP_400_BAD_REQUEST)

        campagne.statut = Campagne.Statut.EN_COURS
        campagne.publiee_le = timezone.now()
        campagne.save(update_fields=["statut", "publiee_le"])
        sequestre_de(campagne)
        return self._reponse_campagne(campagne)

    @action(detail=True, methods=["get"])
    def participants(self, requete, pk=None):
        """Le suivi nominatif qui remplace la liste WhatsApp."""
        campagne = self.get_object()
        parts = (
            campagne.participations.select_related("acheteur")
            .exclude(statut=Participation.Statut.EN_ATTENTE_PAIEMENT)
            .order_by("-payee_le")
        )
        return Response(ParticipantSerialiseur(parts, many=True).data)

    @action(detail=True, methods=["post"])
    def cloturer(self, requete, pk=None):
        """Ferme la collecte avant l'heure, à ses risques."""
        campagne = self.get_object()
        statut = cloturer(campagne)
        return Response({"statut": statut})

    @action(detail=True, methods=["post"], url_path="demander-retrait")
    def demander_retrait(self, requete, pk=None):
        """Réclame les fonds : 100 % moins les frais fixes."""
        campagne = self.get_object()
        try:
            decaissement = demander_decaissement(campagne)
        except ErreurPaiement as erreur:
            return Response({"detail": str(erreur)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "montant_brut": decaissement.montant_brut,
                "frais": decaissement.frais,
                "montant_net": decaissement.montant_net,
                "numero_mobile_money": decaissement.numero_mobile_money,
                "statut": decaissement.statut,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="mise-a-disposition")
    def mise_a_disposition(self, requete, pk=None):
        """Annonce l'arrivée de la marchandise et prévient tout le monde."""
        campagne = self.get_object()
        try:
            notifies = mettre_a_disposition(
                campagne, point_remise=requete.data.get("point_remise", "")
            )
        except ErreurPaiement as erreur:
            return Response({"detail": str(erreur)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({"participants_notifies": notifies,
                         "point_remise": campagne.point_remise})

    @action(detail=True, methods=["post"])
    def retrait(self, requete, pk=None):
        """Valide un code — dicté ou scanné — et remet le colis."""
        campagne = self.get_object()
        serialiseur = RetraitSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        try:
            participation = valider_retrait(
                campagne, serialiseur.validated_data["code"], requete.user
            )
        except ErreurPaiement as erreur:
            return Response({"detail": str(erreur)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "detail": "Retrait confirmé.",
                "acheteur": participation.acheteur.nom_complet,
                "quantite": participation.quantite,
                "retiree_le": participation.retiree_le,
            }
        )


class ProduitGroupeurVueEnsemble(viewsets.ModelViewSet):
    """/api/groupeur/produits/ — saisie libre des produits."""

    permission_classes = [GroupeurValide]

    def get_queryset(self):
        return Produit.objects.filter(propose_par=self.request.user).select_related(
            "categorie"
        )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ProduitSerialiseur
        return ProduitEcritureSerialiseur

    def perform_create(self, serialiseur):
        serialiseur.save(propose_par=self.request.user)


class TableauDeBordGroupeurVue(APIView):
    """GET /api/groupeur/tableau-de-bord/ — l'état de l'activité en un écran."""

    permission_classes = [GroupeurValide]

    def get(self, requete):
        campagnes = Campagne.objects.filter(groupeur=requete.user)
        payees = Participation.objects.filter(
            campagne__groupeur=requete.user,
            statut__in=Participation.STATUTS_PAYES,
        )
        decaisse = Decaissement.objects.filter(
            campagne__groupeur=requete.user, statut=Decaissement.Statut.EXECUTE
        ).aggregate(net=Sum("montant_net", default=0), frais=Sum("frais", default=0))

        reputation = getattr(requete.user, "reputation", None)
        return Response(
            {
                "campagnes": {
                    "total": campagnes.count(),
                    "en_cours": campagnes.filter(
                        statut=Campagne.Statut.EN_COURS
                    ).count(),
                    "a_distribuer": campagnes.filter(
                        statut=Campagne.Statut.DISTRIBUTION
                    ).count(),
                    "terminees": campagnes.filter(
                        statut=Campagne.Statut.TERMINEE
                    ).count(),
                },
                "collecte": {
                    "montant_consigne": payees.aggregate(
                        total=Sum("montant_total", default=0)
                    )["total"],
                    "pieces": payees.aggregate(total=Sum("quantite", default=0))["total"],
                    "participants": payees.values("acheteur").distinct().count(),
                },
                "decaissements": {
                    "montant_recu": decaisse["net"],
                    "frais_payes": decaisse["frais"],
                },
                "reputation": {
                    "note": str(reputation.note) if reputation else "0.00",
                    "campagnes_terminees": (
                        reputation.campagnes_terminees if reputation else 0
                    ),
                    "participants_servis": (
                        reputation.participants_servis if reputation else 0
                    ),
                },
            }
        )


class EtatGroupeurVue(APIView):
    """GET /api/groupeur/etat/ — ce que voit un groupeur en attente.

    La seule route de l'espace ouverte à un dossier non validé : elle dit où
    en est l'examen. Sans elle, l'interface n'aurait qu'un 403 à montrer, et
    le groupeur ne saurait pas s'il doit patienter ou corriger son dossier.
    """

    permission_classes = []

    def get(self, requete):
        if not requete.user.is_authenticated:
            return Response({"acces": False, "raison": "non_connecte"})
        dossier = getattr(requete.user, "dossier_kyc", None)
        if dossier is None:
            return Response({"acces": False, "raison": "aucun_dossier"})
        return Response(
            {
                "acces": requete.user.est_groupeur_valide,
                "raison": dossier.statut,
                "motif_rejet": dossier.motif_rejet,
                "depose_le": dossier.depose_le,
                "decide_le": dossier.decide_le,
            }
        )
