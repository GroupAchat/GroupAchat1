# -*- coding: utf-8 -*-
"""Console d'administration : KYC, séquestres, décaissements, modération.

L'administrateur est le tiers de confiance. Il valide les groupeurs, détient
les fonds et les libère. Rien ici n'est automatique : chaque geste engageant
est tracé avec son auteur.
"""

from __future__ import annotations

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Litige, Participation
from groupachat.comptes.models import DossierKYC, Reputation, Utilisateur
from groupachat.comptes.serialiseurs import (
    DecisionKYCSerialiseur,
    DossierKYCSerialiseur,
)
from groupachat.echanges.models import Commentaire, Notification
from groupachat.echanges.serialiseurs import CommentaireSerialiseur
from groupachat.paiements.models import Decaissement, Sequestre, Transaction
from groupachat.paiements.services import (
    ErreurPaiement,
    cloturer,
    executer_decaissement,
)
from groupachat.noyau.permissions import EstAdministrateur


class DossierKYCAdminVueEnsemble(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """/api/admin/dossiers/ — les demandes de badge de confiance."""

    permission_classes = [EstAdministrateur]
    serializer_class = DossierKYCSerialiseur

    def get_queryset(self):
        dossiers = DossierKYC.objects.select_related("utilisateur", "decide_par")
        # Le filtre ne vaut que pour la liste. Appliqué aussi aux accès par
        # identifiant, il ferait disparaître un dossier dès qu'il est tranché,
        # et l'administrateur ne pourrait plus le relire.
        if self.action != "list":
            return dossiers
        statut = self.request.query_params.get("statut", DossierKYC.Statut.EN_ATTENTE)
        return dossiers if statut == "tous" else dossiers.filter(statut=statut)

    @action(detail=True, methods=["post"])
    def decision(self, requete, pk=None):
        """Valide ou rejette un dossier, et ouvre ou non l'espace groupeur."""
        dossier = self.get_object()
        if dossier.statut != DossierKYC.Statut.EN_ATTENTE:
            return Response(
                {"detail": "Ce dossier a déjà été tranché."},
                status=status.HTTP_409_CONFLICT,
            )

        serialiseur = DecisionKYCSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        valide = serialiseur.validated_data["decision"] == "valider"

        dossier.statut = (
            DossierKYC.Statut.VALIDE if valide else DossierKYC.Statut.REJETE
        )
        dossier.motif_rejet = "" if valide else serialiseur.validated_data["motif"]
        dossier.decide_le = timezone.now()
        dossier.decide_par = requete.user
        dossier.save(update_fields=["statut", "motif_rejet", "decide_le", "decide_par"])

        if valide:
            # La réputation naît avec le badge, à zéro : elle se gagne.
            Reputation.objects.get_or_create(groupeur=dossier.utilisateur)

        Notification.objects.create(
            destinataire=dossier.utilisateur,
            genre=Notification.Genre.KYC_DECIDE,
            titre="Dossier validé" if valide else "Dossier à corriger",
            message=(
                "Votre badge de confiance est actif : vous pouvez créer vos campagnes."
                if valide
                else f"Votre dossier a été refusé — {dossier.motif_rejet}"
            ),
            lien="/groupeur",
        )
        return Response(DossierKYCSerialiseur(dossier).data)


class DecaissementAdminVueEnsemble(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """/api/admin/decaissements/ — les fonds à libérer."""

    permission_classes = [EstAdministrateur]

    def get_queryset(self):
        demandes = Decaissement.objects.select_related(
            "campagne", "campagne__groupeur", "execute_par"
        )
        statut = self.request.query_params.get("statut", "tous")
        if statut != "tous":
            demandes = demandes.filter(statut=statut)
        return demandes

    def get_serializer_class(self):
        from rest_framework import serializers

        class _Serialiseur(serializers.ModelSerializer):
            campagne_titre = serializers.CharField(
                source="campagne.titre", read_only=True
            )
            groupeur = serializers.CharField(
                source="campagne.groupeur.nom_complet", read_only=True
            )

            class Meta:
                model = Decaissement
                fields = ["id", "campagne", "campagne_titre", "groupeur",
                          "montant_brut", "frais", "montant_net",
                          "numero_mobile_money", "operateur", "statut",
                          "demande_le", "execute_le", "reference", "motif_refus"]

        return _Serialiseur

    @action(detail=True, methods=["post"])
    def executer(self, requete, pk=None):
        """Libère les fonds vers le groupeur."""
        decaissement = self.get_object()
        try:
            executer_decaissement(decaissement, requete.user)
        except ErreurPaiement as erreur:
            return Response({"detail": str(erreur)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(decaissement).data)


class ModerationVueEnsemble(
    mixins.ListModelMixin, viewsets.GenericViewSet
):
    """/api/admin/commentaires/ — modération du fil."""

    permission_classes = [EstAdministrateur]
    serializer_class = CommentaireSerialiseur

    def get_queryset(self):
        commentaires = Commentaire.objects.select_related("auteur", "campagne")
        # Même raison que pour les dossiers : filtrer hors de la liste
        # rendrait « rétablir » impossible, puisqu'un message masqué ne
        # serait plus trouvable par son identifiant.
        if self.action != "list":
            return commentaires
        if self.request.query_params.get("masques"):
            return commentaires.filter(masque_le__isnull=False)
        return commentaires.filter(masque_le__isnull=True)

    @action(detail=True, methods=["post"])
    def masquer(self, requete, pk=None):
        """Retire un message du fil sans l'effacer."""
        commentaire = self.get_object()
        commentaire.masque_le = timezone.now()
        commentaire.masque_par = requete.user
        commentaire.motif_masquage = requete.data.get("motif", "")[:200]
        commentaire.save(
            update_fields=["masque_le", "masque_par", "motif_masquage"]
        )
        return Response({"detail": "Message masqué.", "id": commentaire.id})

    @action(detail=True, methods=["post"])
    def retablir(self, requete, pk=None):
        commentaire = self.get_object()
        commentaire.masque_le = None
        commentaire.masque_par = None
        commentaire.motif_masquage = ""
        commentaire.save(
            update_fields=["masque_le", "masque_par", "motif_masquage"]
        )
        return Response({"detail": "Message rétabli.", "id": commentaire.id})


class CampagneAdminVue(APIView):
    """POST /api/admin/campagnes/<id>/cloturer/ — clôture forcée."""

    permission_classes = [EstAdministrateur]

    def post(self, requete, pk):
        campagne = Campagne.objects.filter(pk=pk).first()
        if campagne is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({"statut": cloturer(campagne)})


class TableauDeBordAdminVue(APIView):
    """GET /api/admin/tableau-de-bord/ — l'état de la plateforme."""

    permission_classes = [EstAdministrateur]

    def get(self, requete):
        sequestres = Sequestre.objects.aggregate(
            consigne=Sum("montant_consigne", default=0),
            libere=Sum("montant_libere", default=0),
            rembourse=Sum("montant_rembourse", default=0),
        )
        detenu = (
            sequestres["consigne"] - sequestres["libere"] - sequestres["rembourse"]
        )
        return Response(
            {
                "comptes": {
                    "acheteurs": Utilisateur.objects.filter(
                        role=Utilisateur.Role.ACHETEUR
                    ).count(),
                    "groupeurs": Utilisateur.objects.filter(
                        role=Utilisateur.Role.GROUPEUR
                    ).count(),
                    "groupeurs_valides": DossierKYC.objects.filter(
                        statut=DossierKYC.Statut.VALIDE
                    ).count(),
                },
                "a_traiter": {
                    "dossiers_kyc": DossierKYC.objects.filter(
                        statut=DossierKYC.Statut.EN_ATTENTE
                    ).count(),
                    "decaissements": Decaissement.objects.filter(
                        statut=Decaissement.Statut.DEMANDE
                    ).count(),
                    "litiges": Litige.objects.filter(
                        statut__in=[Litige.Statut.OUVERT, Litige.Statut.EN_EXAMEN]
                    ).count(),
                },
                "campagnes": Campagne.objects.aggregate(
                    en_cours=Count("id", filter=Q(statut=Campagne.Statut.EN_COURS)),
                    financees=Count("id", filter=Q(statut=Campagne.Statut.FINANCEE)),
                    terminees=Count("id", filter=Q(statut=Campagne.Statut.TERMINEE)),
                    annulees=Count("id", filter=Q(statut=Campagne.Statut.ANNULEE)),
                ),
                "sequestre": {
                    "montant_detenu": detenu,
                    "total_consigne": sequestres["consigne"],
                    "total_libere": sequestres["libere"],
                    "total_rembourse": sequestres["rembourse"],
                },
                "revenus": {
                    "frais_encaisses": Decaissement.objects.filter(
                        statut=Decaissement.Statut.EXECUTE
                    ).aggregate(total=Sum("frais", default=0))["total"],
                },
                "transactions_simulees": Transaction.objects.filter(
                    simulee=True
                ).count(),
                "participations": Participation.objects.count(),
            }
        )
