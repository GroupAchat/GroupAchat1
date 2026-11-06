# -*- coding: utf-8 -*-
"""Espace du livreur partenaire : sa tournée, et son scan.

**C'est le livreur qui remet le colis, et lui seul.** L'OAG confie le lot en
bloc à l'agence — La Poste, Gozem — et ne rencontre jamais ses acheteurs.
S'il validait lui-même les retraits, celui qui doit livrer signerait sa
propre livraison, et le code ne prouverait plus rien.

Le livreur est le **seul** à voir où va chaque colis : l'adresse de
livraison désigne un domicile, et c'est précisément ce qu'on ne montre ni à
l'OAG ni à personne d'autre. Il voit aussi le nom et le numéro de l'acheteur,
parce qu'on ne livre pas un pseudonyme : il faut sonner et appeler.

En revanche il ne sait **rien de l'OAG** ni des montants : porter un colis
n'a pas besoin de savoir qui l'a groupé, ni ce qu'il a coûté.
"""

from __future__ import annotations

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from groupachat.commandes.models import Participation
from groupachat.noyau.permissions import EstLivreur
from groupachat.paiements.services import ErreurPaiement, remettre_le_colis


class ColisSerialiseur(serializers.ModelSerializer):
    """Un colis de la tournée, vu par celui qui le porte."""

    produit = serializers.CharField(source="campagne.produit.nom", read_only=True)
    groupage = serializers.CharField(source="campagne.titre", read_only=True)
    destinataire = serializers.CharField(
        source="acheteur.nom_complet", read_only=True
    )
    telephone = serializers.CharField(source="acheteur.telephone", read_only=True)
    mode_retrait_libelle = serializers.CharField(
        source="get_mode_retrait_display", read_only=True
    )
    destination = serializers.CharField(read_only=True)

    class Meta:
        model = Participation
        fields = ["id", "produit", "groupage", "quantite", "destinataire",
                  "telephone", "mode_retrait", "mode_retrait_libelle",
                  "bureau_poste", "adresse_livraison", "destination"]
        read_only_fields = fields


class TourneeVue(APIView):
    """GET /api/livraison/tournee/ — les colis prêts, en attente de remise.

    Tous les colis prêts, et non ceux d'une campagne : un livreur en porte de
    plusieurs groupages dans la même tournée. Le filtre `mode` sépare ce qui
    se dépose au bureau de poste de ce qui se livre à domicile — ce ne sont
    pas les mêmes journées.
    """

    permission_classes = [EstLivreur]

    def get(self, requete):
        colis = (
            Participation.objects.filter(statut=Participation.Statut.PRETE)
            .select_related("acheteur", "campagne", "campagne__produit")
            .order_by("mode_retrait", "bureau_poste", "cree_le")
        )
        mode = requete.query_params.get("mode")
        if mode in dict(Participation.ModeRetrait.choices):
            colis = colis.filter(mode_retrait=mode)
        return Response(ColisSerialiseur(colis, many=True).data)


class RemiseSerialiseur(serializers.Serializer):
    """Le code, dicté ou lu dans le QR."""

    code = serializers.CharField(max_length=40)


class RemiseVue(APIView):
    """POST /api/livraison/retrait/ — le scan qui vaut preuve de livraison.

    Le code est cherché **sur toute la plateforme**, pas dans une campagne :
    le livreur a un paquet et un code, pas le nom du groupage. Les codes sont
    uniques, la recherche directe suffit.
    """

    permission_classes = [EstLivreur]

    def post(self, requete):
        entree = RemiseSerialiseur(data=requete.data)
        entree.is_valid(raise_exception=True)
        try:
            participation = remettre_le_colis(
                entree.validated_data["code"], requete.user
            )
        except ErreurPaiement as erreur:
            return Response({"detail": str(erreur)},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "Colis remis.",
                "colis": ColisSerialiseur(participation).data,
                "remis_le": participation.retiree_le,
            }
        )
