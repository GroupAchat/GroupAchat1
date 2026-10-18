# -*- coding: utf-8 -*-
"""Les trois routes de la connexion à l'administration.

Un module minuscule et séparé, pour une raison de sûreté plutôt que de style :
**la route de connexion est la seule route d'administration qui doit être
ouverte**, puisqu'on l'appelle précisément avant d'avoir une session. La poser
au milieu d'``api_admin.py``, dont le viewset déclare
``permission_classes = [JetonAdmin]`` pour tout le fichier, obligerait à
rouvrir une exception dans une classe entièrement fermée — et une exception
dans un garde-fou est ce qui se relit le moins bien six mois plus tard.

Ici l'inverse est vrai : le fichier est ouvert par défaut, et les deux routes
qui doivent être fermées le déclarent chacune.
"""

from __future__ import annotations

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .api_kyc import JetonAdmin
from .comptes import sessions_admin


class ConnexionSerializer(serializers.Serializer):
    """Ce que le formulaire envoie.

    ⚠️ **``trim_whitespace=False`` sur le mot de passe.** DRF coupe les espaces
    de bord par défaut sur un ``CharField``, ce qui est juste pour un
    identifiant et faux pour un secret : un mot de passe qui se termine par une
    espace est un mot de passe valide, et le couper rendrait la connexion
    impossible sans rien expliquer. L'identifiant, lui, est bien coupé — on ne
    refuse pas quelqu'un pour une espace collée par un copier-coller.
    """

    identifiant = serializers.CharField(max_length=150)
    mot_de_passe = serializers.CharField(
        max_length=200, trim_whitespace=False, style={"input_type": "password"}
    )


class SessionAdminViewSet(viewsets.GenericViewSet):
    """Ouvrir, lire et fermer une session d'administration."""

    permission_classes = [AllowAny]
    #: Comme ``api_kyc.DossierViewSet`` : l'authentification acheteur n'a rien
    #: à faire ici. Laisser ses classes s'appliquer rendait un acheteur
    #: connecté « authentifié » aux yeux de DRF sur des routes qui ne parlent
    #: pas de lui.
    #:
    #: ⚠️ **Ce n'est pas la liste vide pour autant.** ``SchemaAdmin``
    #: n'authentifie personne — elle n'est là que pour fournir l'en-tête
    #: ``WWW-Authenticate``, sans laquelle DRF répond **403 au lieu de 401** à
    #: un mot de passe refusé. Huit tests sont tombés sur ce point exact.
    authentication_classes = [sessions_admin.SchemaAdmin]
    serializer_class = ConnexionSerializer
    queryset = None

    @action(detail=False, methods=["post"], url_path="connexion")
    def connexion(self, request):
        """Identifiant + mot de passe contre un jeton de session.

        Les erreurs viennent de ``sessions_admin.connecter`` : **401** pour un
        refus, **429** pour un verrou. La distinction compte pour l'écran —
        « réessayez » et « attendez quinze minutes » ne se disent pas pareil.
        """
        entree = self.get_serializer(data=request.data)
        entree.is_valid(raise_exception=True)

        session = sessions_admin.connecter(
            entree.validated_data["identifiant"],
            entree.validated_data["mot_de_passe"],
        )

        return Response(
            {
                "jeton": session.jeton,
                "nom": sessions_admin.nom_pour_le_journal(session),
                "expire_le": session.expire_le,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="moi",
        permission_classes=[JetonAdmin],
    )
    def moi(self, request):
        """Qui est connecté, et jusqu'à quand.

        ⚠️ **Cette docstring annonçait que l'écran l'appelait au chargement.
        C'était faux**, et le paquet construit le prouvait : `session-admin/moi`
        n'y figurait pas, alors que `connexion` et `deconnexion` y figuraient.

        L'écran n'en a pas besoin. La première chose qu'il fait après
        l'ouverture est de charger son tableau de bord ; si la session est
        morte, cet appel revient en 401 et la feuille de connexion se rouvre.
        Appeler `moi/` d'abord serait **une requête de plus pour apprendre ce
        que la suivante allait dire de toute façon**.

        Elle reste parce qu'elle sert à autre chose : vérifier qu'une session
        vit encore, à la main, **sans ouvrir une route qui transporte des noms
        et des pièces d'identité**. Diagnostiquer un 401 en appelant
        `/api/dossiers/` ferait défiler des dossiers réels dans un terminal.
        """
        session = request.session_admin
        return Response(
            {
                "nom": sessions_admin.nom_pour_le_journal(session),
                "identifiant": session.utilisateur.get_username(),
                "expire_le": session.expire_le,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="deconnexion",
        permission_classes=[JetonAdmin],
    )
    def deconnexion(self, request):
        """Ferme cette session. Les autres sessions du compte survivent.

        ⚠️ **``POST`` et non ``DELETE``**, alors que la sémantique appellerait
        ``DELETE`` : le routeur de DRF ne câble ``DELETE`` que sur une route de
        détail, et il n'y a pas d'identifiant à mettre dans l'URL — la session
        à fermer est celle de l'en-tête. Mettre son jeton dans le chemin
        l'inscrirait dans les journaux du serveur et du reverse-proxy, pour un
        gain de pureté nul.
        """
        sessions_admin.deconnecter(request.session_admin)
        return Response(status=status.HTTP_204_NO_CONTENT)
