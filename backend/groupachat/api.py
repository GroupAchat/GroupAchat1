# -*- coding: utf-8 -*-
"""Point d'entrée de l'API.

Les routes sont regroupées par espace : comptes, catalogue public, acheteur,
groupeur, administration. Chaque espace vit dans son application, et la
permission qui le garde est déclarée sur ses vues, jamais ici — une route ne
doit pas pouvoir devenir publique par oubli dans ce fichier.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from groupachat.espaces import administration as vues_admin
from groupachat.espaces import groupeur as vues_groupeur
from groupachat.catalogue import vues as vues_catalogue
from groupachat.commandes import vues as vues_commandes
from groupachat.comptes import vues as vues_comptes
from groupachat.echanges import vues as vues_echanges

routeur = DefaultRouter()

# ── Catalogue public ────────────────────────────────────────────────────────
routeur.register("catalogue/categories", vues_catalogue.CategorieVueEnsemble,
                 basename="categorie")
routeur.register("catalogue/produits", vues_catalogue.ProduitVueEnsemble,
                 basename="produit")
routeur.register("catalogue/campagnes", vues_catalogue.CampagneVueEnsemble,
                 basename="campagne")

# ── Acheteur ────────────────────────────────────────────────────────────────
routeur.register("participations", vues_commandes.ParticipationVueEnsemble,
                 basename="participation")
routeur.register("avis", vues_commandes.AvisVueEnsemble, basename="avis")

# ── Espace communautaire et cloche ──────────────────────────────────────────
routeur.register("demandes", vues_echanges.DemandeProduitVueEnsemble,
                 basename="demande")
routeur.register("notifications", vues_echanges.NotificationVueEnsemble,
                 basename="notification")

# ── Groupeur ────────────────────────────────────────────────────────────────
routeur.register("groupeur/campagnes", vues_groupeur.CampagneGroupeurVueEnsemble,
                 basename="campagne-groupeur")
routeur.register("groupeur/produits", vues_groupeur.ProduitGroupeurVueEnsemble,
                 basename="produit-groupeur")
routeur.register("groupeur/medias", vues_groupeur.MediaProduitVueEnsemble,
                 basename="media-groupeur")

# ── Administration ──────────────────────────────────────────────────────────
routeur.register("admin/dossiers", vues_admin.DossierKYCAdminVueEnsemble,
                 basename="dossier-admin")
routeur.register("admin/decaissements", vues_admin.DecaissementAdminVueEnsemble,
                 basename="decaissement-admin")
routeur.register("admin/commentaires", vues_admin.ModerationVueEnsemble,
                 basename="moderation")

# Le fil de discussion est imbriqué sous sa campagne : un commentaire n'existe
# pas hors du produit qu'il commente. Les routes sont écrites à la main plutôt
# que d'ajouter une dépendance pour un seul niveau d'imbrication.
commentaires = vues_echanges.CommentaireVueEnsemble
routes_commentaires = [
    path(
        "campagnes/<int:campagne_pk>/commentaires/",
        commentaires.as_view({"get": "list", "post": "create"}),
        name="commentaires",
    ),
    path(
        "campagnes/<int:campagne_pk>/commentaires/<int:pk>/",
        commentaires.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="commentaire",
    ),
    path(
        "campagnes/<int:campagne_pk>/commentaires/<int:pk>/jaime/",
        commentaires.as_view({"post": "jaime"}),
        name="commentaire-jaime",
    ),
]

urlpatterns = [
    # ── Comptes ─────────────────────────────────────────────────────────────
    path("comptes/inscription/", vues_comptes.InscriptionVue.as_view(), name="inscription"),
    path("comptes/verification/", vues_comptes.VerificationVue.as_view(), name="verification"),
    path("comptes/renvoyer-code/", vues_comptes.RenvoiCodeVue.as_view(), name="renvoyer-code"),
    path("comptes/connexion/", vues_comptes.ConnexionVue.as_view(), name="connexion"),
    path("comptes/deconnexion/", vues_comptes.DeconnexionVue.as_view(), name="deconnexion"),
    path("comptes/moi/", vues_comptes.MoiVue.as_view(), name="moi"),
    path("comptes/dossier/", vues_comptes.DossierKYCVue.as_view(), name="dossier-kyc"),

    # ── Groupeur, hors ressources ───────────────────────────────────────────
    # Doit rester **avant** l'inclusion du routeur, en fin de liste : la route
    # de détail « groupeur/medias/<pk>/ » accepte n'importe quel segment et
    # prendrait « signature » pour un identifiant de média.
    path("groupeur/medias/signature/", vues_groupeur.SignatureEnvoiVue.as_view(),
         name="signature-envoi"),
    path("groupeur/etat/", vues_groupeur.EtatGroupeurVue.as_view(), name="etat-groupeur"),
    path("groupeur/tableau-de-bord/", vues_groupeur.TableauDeBordGroupeurVue.as_view(),
         name="tableau-groupeur"),

    # ── Administration, hors ressources ─────────────────────────────────────
    path("admin/tableau-de-bord/", vues_admin.TableauDeBordAdminVue.as_view(),
         name="tableau-admin"),
    path("admin/campagnes/<int:pk>/cloturer/", vues_admin.CampagneAdminVue.as_view(),
         name="cloturer-campagne"),

    *routes_commentaires,
    path("", include(routeur.urls)),
]
