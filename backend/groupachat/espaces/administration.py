# -*- coding: utf-8 -*-
"""Console d'administration : KYC, séquestres, décaissements, modération.

L'administrateur est le tiers de confiance. Il valide les groupeurs, détient
les fonds et les libère. Rien ici n'est automatique : chaque geste engageant
est tracé avec son auteur.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from groupachat.catalogue.models import Campagne
from groupachat.catalogue.publication import (
    AbonnementPublication,
    PackPublication,
    rendre_une_publication,
)
from groupachat.catalogue.serialiseurs import CampagneDetailSerialiseur
from groupachat.commandes.models import Participation
from groupachat.comptes.models import DossierKYC, Reputation, Utilisateur
from groupachat.comptes.serialiseurs import (
    DecisionKYCSerialiseur,
    DossierKYCSerialiseur,
)
from groupachat.echanges.models import Message, Notification
from groupachat.echanges.serialiseurs_contact import MessageSerialiseur
from groupachat.paiements.models import Decaissement, Sequestre, Transaction
from groupachat.paiements.services import (
    ErreurPaiement,
    cloturer,
    executer_decaissement,
    sequestre_de,
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
    """/api/admin/messages/ — modération des messages privés signalés.

    **Par défaut, la liste ne montre que ce qui a été signalé.** Les
    conversations sont privées ; les parcourir sans motif reviendrait à lire
    le courrier de tout le monde. Un signalement est ce motif, et la vue
    complète d'un fil reste accessible par son identifiant quand il faut
    instruire.

    Masquer n'efface pas : un message effacé sans trace empêcherait
    d'instruire le signalement suivant du même compte.
    """

    permission_classes = [EstAdministrateur]
    serializer_class = MessageSerialiseur

    def get_queryset(self):
        messages = Message.objects.select_related(
            "auteur", "conversation", "conversation__acheteur",
            "conversation__groupeur",
        )
        # Même raison que pour les dossiers : filtrer hors de la liste
        # rendrait « rétablir » impossible, puisqu'un message masqué ne
        # serait plus trouvable par son identifiant.
        if self.action != "list":
            return messages
        if self.request.query_params.get("masques"):
            return messages.filter(masque_le__isnull=False)
        return messages.filter(signale_le__isnull=False, masque_le__isnull=True)

    @action(detail=True, methods=["post"])
    def masquer(self, requete, pk=None):
        """Retire un message du fil sans l'effacer."""
        message = self.get_object()
        message.masque_le = timezone.now()
        message.motif_masquage = requete.data.get("motif", "")[:200]
        message.save(update_fields=["masque_le", "motif_masquage"])
        return Response({"detail": "Message masqué.", "id": message.id})

    @action(detail=True, methods=["post"])
    def retablir(self, requete, pk=None):
        message = self.get_object()
        message.masque_le = None
        message.motif_masquage = ""
        message.save(update_fields=["masque_le", "motif_masquage"])
        return Response({"detail": "Message rétabli.", "id": message.id})


class CampagneAdminVue(APIView):
    """POST /api/admin/campagnes/<id>/cloturer/ — clôture forcée."""

    permission_classes = [EstAdministrateur]

    def post(self, requete, pk):
        campagne = Campagne.objects.filter(pk=pk).first()
        if campagne is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({"statut": cloturer(campagne)})


class VerificationCampagnesVue(APIView):
    """La file des groupages à relire avant vitrine.

    GET  /api/admin/campagnes/a-verifier/
    POST /api/admin/campagnes/<id>/verification/ — `decision` et `motif`.

    **Un refus rend la publication consommée.** Elle paie la mise en ligne ;
    si la plateforme la refuse, la mise en ligne n'a pas eu lieu, et la
    facturer serait indéfendable. Ce n'est pas le cas d'un groupage qui
    échoue après coup : celui-là est bien allé en vitrine.
    """

    permission_classes = [EstAdministrateur]

    def get(self, requete):
        a_verifier = (
            Campagne.objects.filter(statut=Campagne.Statut.EN_VERIFICATION)
            .select_related("produit", "groupeur", "groupeur__points")
            .prefetch_related("paliers", "medias")
            .order_by("cree_le")
        )
        return Response(
            CampagneDetailSerialiseur(a_verifier, many=True).data
        )

    @transaction.atomic
    def post(self, requete, pk):
        campagne = Campagne.objects.filter(
            pk=pk, statut=Campagne.Statut.EN_VERIFICATION
        ).first()
        if campagne is None:
            return Response(
                {"detail": "Ce groupage n'est pas en vérification."},
                status=status.HTTP_404_NOT_FOUND,
            )

        decision = requete.data.get("decision")
        if decision not in ("valider", "refuser"):
            return Response(
                {"decision": "Valider ou refuser, il n'y a pas d'autre issue."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if decision == "valider":
            if campagne.date_limite <= timezone.now():
                return Response(
                    {"detail": "La date limite est passée pendant l'examen : "
                               "l'OAG doit la repousser."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            campagne.statut = Campagne.Statut.EN_COURS
            campagne.publiee_le = timezone.now()
            campagne.save(update_fields=["statut", "publiee_le"])
            sequestre_de(campagne)
            titre = "Groupage publié"
            message = f"« {campagne.titre} » est au catalogue."
        else:
            motif = (requete.data.get("motif") or "").strip()
            if not motif:
                return Response(
                    {"motif": "Un refus sans motif ne se corrige pas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            campagne.statut = Campagne.Statut.BROUILLON
            campagne.motif_annulation = motif
            campagne.save(update_fields=["statut", "motif_annulation"])
            rendre_une_publication(campagne.groupeur)
            titre = "Groupage à corriger"
            message = (
                f"« {campagne.titre} » n'est pas passé : {motif} "
                "Votre publication vous est rendue."
            )

        Notification.objects.create(
            destinataire=campagne.groupeur,
            genre=Notification.Genre.SYSTEME,
            titre=titre,
            message=message,
            campagne=campagne,
            lien=f"/groupeur/campagnes/{campagne.id}",
        )
        return Response(
            {"statut": campagne.statut, "motif": campagne.motif_annulation}
        )


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
        commissions = Decaissement.objects.filter(
            statut=Decaissement.Statut.EXECUTE
        ).aggregate(total=Sum("frais", default=0))["total"]
        abonnements = AbonnementPublication.objects.aggregate(
            total=Sum("montant", default=0)
        )["total"]
        packs = PackPublication.objects.aggregate(
            total=Sum("montant", default=0)
        )["total"]

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
                    "campagnes_a_verifier": Campagne.objects.filter(
                        statut=Campagne.Statut.EN_VERIFICATION
                    ).count(),
                    "dossiers_kyc": DossierKYC.objects.filter(
                        statut=DossierKYC.Statut.EN_ATTENTE
                    ).count(),
                    "decaissements": Decaissement.objects.filter(
                        statut=Decaissement.Statut.DEMANDE
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
                # Deux sources, et non une seule : la commission sur les
                # groupages aboutis **et** le droit de publier. Un tableau de
                # bord qui n'affiche que la commission laisse croire que
                # l'abonnement ne rapporte rien.
                "revenus": {
                    "frais_encaisses": commissions,
                    "publications": abonnements + packs,
                    "total": commissions + abonnements + packs,
                },
                "transactions_simulees": Transaction.objects.filter(
                    simulee=True
                ).count(),
                "participations": Participation.objects.count(),
            }
        )
