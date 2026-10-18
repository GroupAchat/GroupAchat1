# -*- coding: utf-8 -*-
"""Les routes de l'API.

Les noms d'URL suivent le vocabulaire **interne** — « campagnes » et non
« groupages ». Le mot visible est une affaire d'interface, et traduire ici
obligerait à traduire dans les deux sens à chaque bout.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from groupachat.api import (
    CampagneViewSet,
    CommandeViewSet,
    DemandeViewSet,
    NotificationViewSet,
    QuestionViewSet,
)
from groupachat.api_admin import AdministrationViewSet
from groupachat.api_comptes import CompteViewSet
from groupachat.api_groupeur import GroupeurViewSet as EspaceGroupeurViewSet
from groupachat.api_kyc import DossierViewSet, GroupeurViewSet
from groupachat.api_session_admin import SessionAdminViewSet

routeur = DefaultRouter()
# Le compte acheteur : code SMS, session, profil. C'est la seule route qui
# delivre une identite — voir `api_comptes.py`.
routeur.register("comptes", CompteViewSet, basename="compte")
routeur.register("campagnes", CampagneViewSet, basename="campagne")
routeur.register("commandes", CommandeViewSet, basename="commande")
routeur.register("questions", QuestionViewSet, basename="question")
routeur.register(
    "notifications", NotificationViewSet, basename="notification"
)
routeur.register("demandes", DemandeViewSet, basename="demande")

# Le recrutement des groupeurs (§10.5). Deux routes et deux publics :
#
# - `groupeurs/` est **publique** — c'est le formulaire d'inscription, et le
#   groupeur y relit l'etat de son dossier ;
# - `dossiers/` est **fermee par le jeton d'administration** : elle transporte
#   des noms, des numeros et des references de pieces d'identite. C'est le
#   point d'entree le plus sensible du projet, et le seul qui ne suive pas le
#   `AllowAny` du §1.5.
routeur.register("groupeurs", GroupeurViewSet, basename="groupeur")
routeur.register("dossiers", DossierViewSet, basename="dossier")

# L'administration : etat du service, groupages, virements. Derriere le
# meme jeton que `dossiers/` — ces routes voient tout.
routeur.register(
    "administration", AdministrationViewSet, basename="administration"
)

# L'espace de travail du groupeur : ses campagnes, son portefeuille, ses
# questions. Distinct de `groupeurs/`, qui est le **depot de dossier**
# public — les deux publics et les deux regles d'anonymat ne se melangent
# pas. Voir l'en-tete de `api_groupeur.py`.
routeur.register(
    "espace-groupeur", EspaceGroupeurViewSet, basename="espace-groupeur"
)

# La connexion a l'administration : `connexion/`, `moi/`, `deconnexion/`.
#
# ⚠️ **Les routes d'administration etaient gardees par un jeton unique et
# partage**, recopie a la main par chaque administrateur. Elles exigent
# desormais une session ouverte contre un mot de passe. Voir
# `api_session_admin.py` pour les trois routes, et
# `comptes/sessions_admin.py` pour ce qu'elles verifient.
routeur.register(
    "session-admin", SessionAdminViewSet, basename="session-admin"
)

urlpatterns = [
    # Tout le travail d'administration vit ici : fiches, recherche, édition,
    # validation des dossiers KYC (§13.6 du cahier des charges). L'écran A1 du
    # front n'est qu'une vue d'ensemble, pas un remplacement.
    path("admin/", admin.site.urls),
    path("api/", include(routeur.urls)),
]
