# -*- coding: utf-8 -*-
"""La connexion à l'administration : identifiant, mot de passe, session.

Un module séparé de ``sessions.py``, et pour la même raison qui sépare
``api_kyc.py`` de ``api.py`` : **ce sont deux publics et deux mécanismes**, et
les mélanger ferait relire à chaque modification un fichier où la moitié des
fonctions reconnaissent un acheteur et l'autre un administrateur. Le risque
n'est pas théorique — ``api_kyc.DossierViewSet`` déclare
``authentication_classes = []`` précisément pour que l'authentification
acheteur n'ait aucune prise sur ces routes.

## Ce que ce module remplace

⚠️ **L'administration était gardée par un jeton unique et partagé**,
``settings.JETON_ADMIN``, comparé à l'en-tête ``X-Jeton-Admin``. Le code qui le
portait l'admettait : *« ce n'est pas de l'authentification, et il ne faut pas
le prendre pour telle »*. Ce module le remplace par de vrais comptes.

**Les comptes sont les ``User`` de Django**, filtrés sur ``is_staff``. On ne
pose pas de modèle d'administrateur maison : ``User`` apporte déjà le hachage,
les validateurs de ``AUTH_PASSWORD_VALIDATORS``, ``createsuperuser`` et un
écran de gestion dans l'admin Django. En écrire un autre serait refaire tout
cela, moins bien.

## ⚠️ ``is_staff`` et non « le compte existe »

Un ``User`` sans ``is_staff`` ne passe pas. La nuance compte parce que la table
``auth_user`` pourrait un jour servir à autre chose, et parce qu'elle donne la
façon de **révoquer un administrateur sans supprimer son compte** : on décoche
la case, ses sessions tombent à la requête suivante.
"""

from __future__ import annotations

import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, Throttled

from .models import SessionAdmin, VerrouAdmin

#: Le schéma de l'en-tête. ⚠️ **``X-Jeton-Admin`` est conservé**, alors que la
#: valeur qu'il transporte a complètement changé de nature — ce n'est plus un
#: secret partagé mais un jeton de session personnel. Garder le nom évite de
#: toucher les vingt-deux endroits du client qui le posent déjà, et l'en-tête
#: n'a jamais été autre chose qu'un transport.
ENTETE = "X-Jeton-Admin"


def _verrou(identifiant: str) -> VerrouAdmin:
    """Le compteur d'échecs de cet identifiant, créé au besoin."""
    verrou, _ = VerrouAdmin.objects.get_or_create(identifiant=identifiant)
    return verrou


def _throttled(verrou: VerrouAdmin) -> Throttled:
    """L'erreur 429, avec le temps d'attente restant.

    Le délai est annoncé en minutes plutôt qu'en secondes : à ce
    moment-là personne ne compte les secondes, et « réessayez dans 847
    secondes » demande une division à quelqu'un qui est déjà agacé.
    """
    reste = int((verrou.bloque_jusqu_a - timezone.now()).total_seconds())
    return Throttled(
        wait=reste,
        detail=(
            "Trop de tentatives. Réessayez dans "
            f"{max(1, reste // 60)} minute(s)."
        ),
    )


def _echouer(verrou: VerrouAdmin) -> None:
    """Compte un échec, et pose le verrou au cinquième.

    ⚠️ **Le compteur est remis à zéro en posant le verrou**, et non laissé à
    cinq. C'est exactement le défaut que j'ai introduit puis corrigé côté
    acheteur : un compteur resté à son maximum fait que la première faute de
    frappe après l'expiration du verrou le repose aussitôt, pour un quart
    d'heure, indéfiniment. Le verrou est la sanction des cinq échecs ; une fois
    purgé, on repart de zéro.
    """
    verrou.echecs += 1
    atteint = verrou.echecs >= VerrouAdmin.ECHECS_AVANT_VERROU
    if atteint:
        verrou.echecs = 0
        verrou.bloque_jusqu_a = timezone.now() + timedelta(
            minutes=VerrouAdmin.DUREE_VERROU_MINUTES
        )
    verrou.save(update_fields=["echecs", "bloque_jusqu_a"])

    # ⚠️ **Le verrou s'annonce à l'instant où il est posé**, et non à la
    # tentative suivante. C'est une question d'honnêteté d'interface : le
    # cinquième essai répondait « mot de passe incorrect » alors que le compte
    # venait d'être verrouillé, et la personne ne l'apprenait qu'au sixième.
    # Elle aurait passé l'intervalle à chercher un mot de passe qui, de toute
    # façon, n'aurait pas été accepté.
    if atteint:
        raise _throttled(verrou)


def connecter(identifiant: str, mot_de_passe: str) -> SessionAdmin:
    """Vérifie l'identifiant et le mot de passe, puis ouvre une session.

    Lève ``Throttled`` si le verrou est posé, ``AuthenticationFailed`` sinon.

    ## ⚠️ Un seul message d'erreur pour trois causes

    Identifiant inconnu, mot de passe faux, compte sans ``is_staff`` : la même
    phrase. Distinguer « cet identifiant n'existe pas » de « mauvais mot de
    passe » dirait à qui essaie **quels identifiants existent**, et lui
    permettrait de n'attaquer que ceux-là. C'est la différence entre deviner
    deux secrets et n'en deviner qu'un.

    ## ⚠️ Le hachage factice sur un identifiant inconnu

    ``Utilisateur().set_password(...)`` sur un compte inexistant ne sert à rien
    de fonctionnel, et ce n'est pas du zèle : sans lui, un identifiant inconnu
    répondrait **sans hacher**, donc beaucoup plus vite qu'un identifiant
    connu. Le temps de réponse révélerait alors ce que le message d'erreur
    unique vient justement de masquer.
    """
    identifiant = (identifiant or "").strip()
    Utilisateur = get_user_model()

    verrou = _verrou(identifiant)
    if verrou.est_bloque:
        raise _throttled(verrou)

    compte = Utilisateur.objects.filter(
        **{Utilisateur.USERNAME_FIELD: identifiant}
    ).first()

    if compte is None:
        # Voir la note de docstring : on hache dans le vide pour que le temps
        # de réponse ne trahisse pas l'absence du compte.
        Utilisateur().set_password(mot_de_passe)
        _echouer(verrou)
        raise AuthenticationFailed("Identifiant ou mot de passe incorrect.")

    if not compte.check_password(mot_de_passe):
        _echouer(verrou)
        raise AuthenticationFailed("Identifiant ou mot de passe incorrect.")

    if not (compte.is_active and compte.is_staff):
        _echouer(verrou)
        raise AuthenticationFailed("Identifiant ou mot de passe incorrect.")

    # Réussite : le compteur repart de zéro, sinon quatre fautes de frappe
    # étalées sur un mois finiraient par verrouiller quelqu'un qui n'a jamais
    # échoué deux fois de suite.
    verrou.echecs = 0
    verrou.bloque_jusqu_a = None
    verrou.save(update_fields=["echecs", "bloque_jusqu_a"])

    return SessionAdmin.objects.create(
        utilisateur=compte,
        jeton=secrets.token_urlsafe(32),
        expire_le=timezone.now()
        + timedelta(hours=SessionAdmin.DUREE_HEURES),
    )


def session_de_la_requete(request) -> SessionAdmin | None:
    """Retrouve la session d'administration, ou ``None``.

    ⚠️ **``is_staff`` est revérifié à chaque requête**, et pas seulement à la
    connexion. C'est ce qui fait qu'une révocation prend effet tout de suite :
    décocher la case dans l'admin Django ferme les sessions en cours, au lieu
    d'attendre leur expiration — jusqu'à douze heures pendant lesquelles
    quelqu'un qu'on vient de retirer continuerait à lire des pièces d'identité.
    """
    jeton = (request.headers.get(ENTETE) or "").strip()
    if not jeton:
        return None

    session = (
        SessionAdmin.objects.select_related("utilisateur")
        .filter(jeton=jeton)
        .first()
    )
    if session is None or not session.valide:
        return None
    if not (session.utilisateur.is_active and session.utilisateur.is_staff):
        return None

    session.marquer_usage()
    return session


class SchemaAdmin(BaseAuthentication):
    """N'authentifie personne. Elle n'est là que pour le code de statut.

    ⚠️⚠️ **Sans elle, DRF répond 403 au lieu de 401**, et ce n'est pas un
    détail cosmétique : DRF ne sait émettre un 401 que si une classe
    d'authentification lui fournit l'en-tête ``WWW-Authenticate``. À défaut il
    suppose que l'appelant est identifié mais sans droits. Les huit tests du
    verrou et des refus sont tombés sur ce point exact, tous avec
    ``403 != 401``.

    | | Ce que l'écran doit faire |
    |---|---|
    | **401** — je ne sais pas qui vous êtes | rouvrir la feuille de connexion |
    | **403** — je sais, et c'est non | afficher un refus |

    Un administrateur dont la session a expiré doit retomber sur la feuille de
    connexion, pas sur un « accès refusé » qui ne lui laisse aucun moyen de
    revenir. C'est le même raisonnement que ``sessions.AuthentificationSession``
    côté acheteur, et le même remède.

    ⚠️ **``authenticate`` renvoie toujours ``None``, et c'est voulu.** Remplir
    ``request.user`` avec un administrateur ferait croire à tout le reste du
    projet qu'un **acheteur** est connecté — ``acheteur_de_la_requete`` lit
    exactement ce champ. Les deux mécanismes doivent rester séparés : la
    session d'administration vit sur ``request.session_admin``, posée par
    ``api_kyc.JetonAdmin``.
    """

    #: Le schéma annoncé dans ``WWW-Authenticate``. C'est lui, et lui seul, qui
    #: transforme le 403 de DRF en 401.
    mot_cle = "Jeton"

    def authenticate(self, request):
        return None

    def authenticate_header(self, request) -> str:
        return self.mot_cle


def deconnecter(session: SessionAdmin) -> None:
    """Ferme cette session-là, et elle seule.

    Les autres sessions du même compte survivent : fermer l'onglet du poste
    partagé ne doit pas déconnecter la même personne de son propre téléphone.
    """
    session.delete()


def nom_pour_le_journal(session: SessionAdmin) -> str:
    """Ce qu'on écrit dans ``DecisionKyc.decide_par``.

    ⚠️ **C'était un champ de texte libre envoyé par le client**, donc la bonne
    foi de celui qui remplissait le formulaire. C'est maintenant le compte
    authentifié. Le §10.5 confie la validation d'un dossier à un humain parce
    que, le jour d'un litige, ce dossier est notre seul recours contre le
    groupeur — un journal dont l'auteur est déclaratif ne prouve rien.

    Le nom complet s'il est renseigné, l'identifiant sinon : un journal se lit,
    et « Ama Koffi » se lit mieux que « akoffi ».
    """
    compte = session.utilisateur
    return (compte.get_full_name() or "").strip() or compte.get_username()
