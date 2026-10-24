# -*- coding: utf-8 -*-
"""Inscription, vérification du numéro, connexion et dossier de confiance."""

from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from groupachat.comptes.models import (
    CodeVerification,
    DossierKYC,
    TropDeCodes,
    Utilisateur,
)
from groupachat.comptes.serialiseurs import (
    ConnexionSerialiseur,
    DossierKYCSerialiseur,
    InscriptionSerialiseur,
    RenvoiCodeSerialiseur,
    UtilisateurSerialiseur,
    VerificationSerialiseur,
)
from groupachat.comptes.services import envoyer_code
from groupachat.noyau.limitation import (
    LimiteConnexion,
    LimiteInscription,
    LimiteRenvoi,
    LimiteVerification,
)
from groupachat.noyau.permissions import NumeroVerifie


def _envoyer_ou_refuser(utilisateur):
    """Émet un code, ou rend la réponse de refus si le plafond est atteint.

    Rend (charge, refus) : l'un des deux vaut ``None``. On distingue les deux
    plutôt que de laisser remonter l'exception, pour que l'interface affiche
    « réessayez dans une heure » au lieu d'une erreur serveur.
    """
    try:
        return _reponse_envoi(envoyer_code(utilisateur)), None
    except TropDeCodes as trop:
        return None, Response(
            {"detail": str(trop)}, status=status.HTTP_429_TOO_MANY_REQUESTS
        )


def _reponse_envoi(resultat) -> dict:
    """Ce qu'on renvoie à l'interface après un envoi de code.

    En mode simulé le code voyage dans la réponse, pour que l'écran puisse
    l'afficher. C'est volontaire et cantonné ici : le jour où une vraie
    passerelle est branchée, ``code_affiche`` vaut ``None`` et la clé
    disparaît sans qu'aucune vue ne change.
    """
    charge = {"sms_simule": resultat.simule}
    if resultat.code_affiche:
        charge["code_affiche"] = resultat.code_affiche
    return charge


class InscriptionVue(APIView):
    """POST /api/comptes/inscription/"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LimiteInscription]

    @transaction.atomic
    def post(self, requete):
        serialiseur = InscriptionSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        utilisateur = serialiseur.save()
        charge, refus = _envoyer_ou_refuser(utilisateur)
        if refus is not None:
            return refus
        return Response(
            {
                "utilisateur": UtilisateurSerialiseur(utilisateur).data,
                "verification": charge,
            },
            status=status.HTTP_201_CREATED,
        )


class VerificationVue(APIView):
    """POST /api/comptes/verification/ — valide le numéro et ouvre la session.

    Vérifier et connecter d'un seul geste : demander au nouvel inscrit de
    ressaisir son mot de passe juste après avoir tapé son code serait une
    étape de trop sur un téléphone.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LimiteVerification]

    @transaction.atomic
    def post(self, requete):
        serialiseur = VerificationSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        numero = Utilisateur.objects.normaliser_telephone(
            serialiseur.validated_data["telephone"]
        )
        utilisateur = Utilisateur.objects.filter(telephone=numero).first()
        if utilisateur is None:
            return Response(
                {"detail": "Aucun compte pour ce numéro."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if utilisateur.telephone_verifie:
            return Response({"detail": "Ce numéro est déjà vérifié."})

        verification = (
            CodeVerification.objects.filter(utilisateur=utilisateur, consomme_le=None)
            .order_by("-cree_le")
            .first()
        )
        if verification is None or not verification.est_utilisable:
            return Response(
                {"detail": "Code expiré. Demandez-en un nouveau."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification.code != serialiseur.validated_data["code"]:
            # On compte l'essai raté : sans ça, un million de tentatives
            # viendraient à bout de n'importe quel code à six chiffres.
            verification.tentatives += 1
            verification.save(update_fields=["tentatives"])
            restants = CodeVerification.MAX_TENTATIVES - verification.tentatives
            return Response(
                {
                    "detail": "Code incorrect.",
                    "essais_restants": max(restants, 0),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.consomme_le = timezone.now()
        verification.save(update_fields=["consomme_le"])
        utilisateur.telephone_verifie = True
        utilisateur.save(update_fields=["telephone_verifie"])

        login(requete, utilisateur, backend="django.contrib.auth.backends.ModelBackend")
        return Response({"utilisateur": UtilisateurSerialiseur(utilisateur).data})


class RenvoiCodeVue(APIView):
    """POST /api/comptes/renvoyer-code/"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LimiteRenvoi]

    def post(self, requete):
        serialiseur = RenvoiCodeSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        numero = Utilisateur.objects.normaliser_telephone(
            serialiseur.validated_data["telephone"]
        )
        utilisateur = Utilisateur.objects.filter(telephone=numero).first()
        # Réponse identique que le compte existe ou non : dire « numéro
        # inconnu » transformerait cette route en annuaire des inscrits.
        if utilisateur is None or utilisateur.telephone_verifie:
            return Response({"sms_simule": True})
        charge, refus = _envoyer_ou_refuser(utilisateur)
        return refus if refus is not None else Response(charge)


class ConnexionVue(APIView):
    """POST /api/comptes/connexion/"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LimiteConnexion]

    def post(self, requete):
        serialiseur = ConnexionSerialiseur(data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        numero = Utilisateur.objects.normaliser_telephone(
            serialiseur.validated_data["telephone"]
        )
        utilisateur = authenticate(
            requete,
            username=numero,
            password=serialiseur.validated_data["mot_de_passe"],
        )
        if utilisateur is None:
            return Response(
                {"detail": "Numéro ou mot de passe incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(requete, utilisateur)
        charge = {"utilisateur": UtilisateurSerialiseur(utilisateur).data}
        if not utilisateur.telephone_verifie:
            # Compte créé mais jamais vérifié : on renvoie un code plutôt que
            # de le laisser devant une interface qui refusera tout.
            verification, refus = _envoyer_ou_refuser(utilisateur)
            if refus is not None:
                return refus
            charge["verification"] = verification
        return Response(charge)


class DeconnexionVue(APIView):
    """POST /api/comptes/deconnexion/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, requete):
        logout(requete)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MoiVue(APIView):
    """GET et PATCH /api/comptes/moi/"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, requete):
        return Response(UtilisateurSerialiseur(requete.user).data)

    def patch(self, requete):
        serialiseur = UtilisateurSerialiseur(
            requete.user, data=requete.data, partial=True
        )
        serialiseur.is_valid(raise_exception=True)
        serialiseur.save()
        return Response(serialiseur.data)


class DossierKYCVue(APIView):
    """GET et POST /api/comptes/dossier/ — devenir groupeur."""

    permission_classes = [NumeroVerifie]

    def get(self, requete):
        dossier = getattr(requete.user, "dossier_kyc", None)
        if dossier is None:
            return Response(
                {"detail": "Aucun dossier déposé."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(DossierKYCSerialiseur(dossier).data)

    @transaction.atomic
    def post(self, requete):
        dossier = getattr(requete.user, "dossier_kyc", None)
        if dossier is not None and dossier.statut != DossierKYC.Statut.REJETE:
            return Response(
                {"detail": "Un dossier est déjà en cours d'examen."},
                status=status.HTTP_409_CONFLICT,
            )

        serialiseur = DossierKYCSerialiseur(dossier, data=requete.data)
        serialiseur.is_valid(raise_exception=True)
        # Un dossier rejeté est réécrit plutôt que doublonné, et repart à
        # zéro : sans remise à blanc, l'ancien motif de rejet resterait
        # affiché sous un dossier pourtant corrigé.
        dossier = serialiseur.save(
            utilisateur=requete.user,
            statut=DossierKYC.Statut.EN_ATTENTE,
            motif_rejet="",
            decide_le=None,
            decide_par=None,
            depose_le=timezone.now(),
        )

        # Le rôle bascule dès le dépôt ; c'est la validation du dossier, pas
        # le rôle, qui ouvre l'espace groupeur.
        if requete.user.role != Utilisateur.Role.GROUPEUR:
            requete.user.role = Utilisateur.Role.GROUPEUR
            requete.user.save(update_fields=["role"])

        return Response(
            DossierKYCSerialiseur(dossier).data, status=status.HTTP_201_CREATED
        )
