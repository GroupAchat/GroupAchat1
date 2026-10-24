# -*- coding: utf-8 -*-
"""Règles d'accès communes à toute l'API."""

from __future__ import annotations

from rest_framework import permissions

from groupachat.comptes.models import Utilisateur


class NumeroVerifie(permissions.BasePermission):
    """Réservé aux comptes dont le numéro a été vérifié par SMS.

    C'est le seuil d'entrée pour tout ce qui engage : commander, commenter,
    déposer un dossier. Lire le catalogue n'en a pas besoin.
    """

    message = "Vérifiez d'abord votre numéro de téléphone."

    def has_permission(self, requete, vue) -> bool:
        utilisateur = requete.user
        return bool(utilisateur.is_authenticated and utilisateur.telephone_verifie)


class GroupeurValide(permissions.BasePermission):
    """Réservé aux groupeurs dont le dossier KYC a été validé.

    Le cahier des charges est net : tant que l'administrateur n'a pas tranché,
    l'espace groupeur n'est pas accessible — pas seulement la publication.
    """

    message = "Votre dossier doit être validé pour accéder à l'espace groupeur."

    def has_permission(self, requete, vue) -> bool:
        return bool(requete.user.is_authenticated and requete.user.est_groupeur_valide)


class EstAdministrateur(permissions.BasePermission):
    """Réservé à l'équipe."""

    message = "Réservé à l'administration."

    def has_permission(self, requete, vue) -> bool:
        utilisateur = requete.user
        return bool(
            utilisateur.is_authenticated
            and (
                utilisateur.est_equipe
                or utilisateur.role == Utilisateur.Role.ADMINISTRATEUR
            )
        )


class LectureLibreEcritureVerifiee(permissions.BasePermission):
    """Tout le monde lit, seuls les numéros vérifiés écrivent.

    C'est la règle du catalogue et du fil de discussion : le visiteur doit
    pouvoir tout consulter sans compte, sinon la plateforme ne rassure
    personne ; écrire demande un numéro vérifié, sinon les faux avis affluent.
    """

    message = "Vérifiez votre numéro de téléphone pour participer."

    def has_permission(self, requete, vue) -> bool:
        if requete.method in permissions.SAFE_METHODS:
            return True
        return bool(requete.user.is_authenticated and requete.user.telephone_verifie)


class EstAuteurOuLectureSeule(permissions.BasePermission):
    """Seul l'auteur modifie son objet ; les autres se contentent de lire.

    Certaines actions écrivent **à côté** de l'objet sans le modifier — aimer
    un message, marquer son intérêt pour une demande. Elles visent justement
    le contenu de quelqu'un d'autre, et la vue les déclare dans
    ``actions_ouvertes`` pour y échapper.
    """

    message = "Vous ne pouvez modifier que vos propres contenus."

    def has_object_permission(self, requete, vue, objet) -> bool:
        if requete.method in permissions.SAFE_METHODS:
            return True
        if getattr(vue, "action", None) in getattr(vue, "actions_ouvertes", ()):
            return True
        proprietaire = getattr(objet, "auteur_id", None) or getattr(
            objet, "acheteur_id", None
        )
        return proprietaire == requete.user.id
