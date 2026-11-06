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
from groupachat.espaces import livraison as vues_livraison
from groupachat.catalogue import vues as vues_catalogue
from groupachat.commandes import vues as vues_commandes
from groupachat.comptes import vues as vues_comptes
from groupachat.echanges import vues as vues_echanges
from groupachat.echanges import vues_contact

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
routeur.register("reclamations", vues_commandes.ReclamationVueEnsemble,
                 basename="reclamation")

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
routeur.register("groupeur/medias-campagne", vues_groupeur.MediaCampagneVueEnsemble,
                 basename="media-campagne-groupeur")

# ── Administration ──────────────────────────────────────────────────────────
routeur.register("admin/dossiers", vues_admin.DossierKYCAdminVueEnsemble,
                 basename="dossier-admin")
routeur.register("admin/decaissements", vues_admin.DecaissementAdminVueEnsemble,
                 basename="decaissement-admin")
routeur.register("admin/messages", vues_admin.ModerationVueEnsemble,
                 basename="moderation")
routeur.register("conversations", vues_contact.ConversationVueEnsemble,
                 basename="conversation")

urlpatterns = [
    # ── Comptes ─────────────────────────────────────────────────────────────
    path("comptes/inscription/", vues_comptes.InscriptionVue.as_view(), name="inscription"),
    path("comptes/verification/", vues_comptes.VerificationVue.as_view(), name="verification"),
    path("comptes/renvoyer-code/", vues_comptes.RenvoiCodeVue.as_view(), name="renvoyer-code"),
    path("comptes/connexion/", vues_comptes.ConnexionVue.as_view(), name="connexion"),
    path("comptes/deconnexion/", vues_comptes.DeconnexionVue.as_view(), name="deconnexion"),
    path("comptes/moi/", vues_comptes.MoiVue.as_view(), name="moi"),
    path("comptes/dossier/", vues_comptes.DossierKYCVue.as_view(), name="dossier-kyc"),
    path("comptes/parrainage/", vues_comptes.ParrainageVue.as_view(),
         name="parrainage"),

    # ── Groupeur, hors ressources ───────────────────────────────────────────
    # Doit rester **avant** l'inclusion du routeur, en fin de liste : la route
    # de détail « groupeur/medias/<pk>/ » accepte n'importe quel segment et
    # prendrait « signature » pour un identifiant de média.
    path("groupeur/medias/signature/", vues_groupeur.SignatureEnvoiVue.as_view(),
         name="signature-envoi"),
    path("groupeur/etat/", vues_groupeur.EtatGroupeurVue.as_view(), name="etat-groupeur"),

    # L'espace du livreur partenaire. Le scan vit **ici** et non dans
    # l'espace OAG : c'est l'agence qui remet le colis.
    path("livraison/tournee/", vues_livraison.TourneeVue.as_view(), name="tournee"),
    path("livraison/retrait/", vues_livraison.RemiseVue.as_view(), name="remise"),
    # Le droit de publier : ce qu'il reste, et comment en acheter.
    path("groupeur/publication/", vues_groupeur.DroitDePublierVue.as_view(),
         name="droit-de-publier"),
    path("groupeur/publication/abonnement/",
         vues_groupeur.AbonnementPublicationVue.as_view(),
         name="abonnement-publication"),
    path("groupeur/publication/pack/", vues_groupeur.PackPublicationVue.as_view(),
         name="pack-publication"),
    path("groupeur/publication/ticket/", vues_groupeur.PackPublicationVue.as_view(),
         name="ticket-publication"),
    path("groupeur/historique-bancaire/", vues_groupeur.HistoriqueBancaireOagVue.as_view(),
         name="historique-bancaire-oag"),
    path("groupeur/tableau-de-bord/", vues_groupeur.TableauDeBordGroupeurVue.as_view(),
         name="tableau-groupeur"),

    # ── Administration, hors ressources ─────────────────────────────────────
    path("admin/tableau-de-bord/", vues_admin.TableauDeBordAdminVue.as_view(),
         name="tableau-admin"),
    # La file de verification avant vitrine, et la decision.
    path("admin/campagnes/a-verifier/",
         vues_admin.VerificationCampagnesVue.as_view(), name="campagnes-a-verifier"),
    path("admin/campagnes/<int:pk>/verification/",
         vues_admin.VerificationCampagnesVue.as_view(), name="verifier-campagne"),
    path("admin/campagnes/<int:pk>/cloturer/", vues_admin.CampagneAdminVue.as_view(),
         name="cloturer-campagne"),

    # ── Contact Privé ───────────────────────────────────────────────────────
    # « conversations/ouvrir/ » doit précéder le routeur : la route de détail
    # accepte n'importe quel segment et prendrait « ouvrir » pour un
    # identifiant de conversation.
    path("conversations/ouvrir/", vues_contact.OuvertureConversationVue.as_view(),
         name="ouvrir-conversation"),
    path("contact-prive/", vues_contact.ContactPriveVue.as_view(),
         name="contact-prive"),
    path("contact-prive/souscrire/", vues_contact.SouscriptionVue.as_view(),
         name="souscrire-contact-prive"),

    path("", include(routeur.urls)),
]
