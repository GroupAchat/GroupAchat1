# -*- coding: utf-8 -*-
"""Les liens des notifications mènent tous à un écran qui existe (F-008).

Défaut d'origine : « Paiement enregistré » et « Votre produit est arrivé »
pointaient vers `/participations/<id>`, qui n'est qu'une route d'API ; la
boutique répondait « page introuvable » au clic.

Le serveur ne peut pas lire le routeur React. `ROUTES_DE_LA_BOUTIQUE` est donc
une **copie des routes de `frontend/boutique/src/App.tsx`** (les chemins des
`<Route>`, paramètres `:id` remplacés par un entier). Quand on ajoute ou
renomme une route de ce fichier, ou qu'une notification change de lien, ce
tableau est à tenir à jour : c'est le prix d'un garde-fou sans dépendance.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Participation
from groupachat.comptes.models import DossierKYC
from groupachat.echanges.models import Notification
from groupachat.paiements.services import cloturer_les_echus

pytestmark = pytest.mark.django_db

# Copie de App.tsx. `:id` devient un entier ; `/groupeur/*` reprend les routes
# imbriquées sous <Route path="/groupeur">.
ROUTES_DE_LA_BOUTIQUE = [
    re.compile(motif)
    for motif in (
        r"^/$",
        r"^/catalogue$",
        r"^/campagnes/\d+$",
        r"^/communaute$",
        r"^/mes-achats$",
        r"^/mes-achats/\d+$",
        r"^/notifications$",
        r"^/profil$",
        r"^/profil/devenir-groupeur$",
        r"^/connexion$",
        r"^/inscription$",
        r"^/groupeur$",
        r"^/groupeur/campagnes$",
        r"^/groupeur/campagnes/nouvelle$",
        r"^/groupeur/campagnes/\d+$",
    )
]


def _route_existe(lien: str) -> bool:
    return any(motif.match(lien) for motif in ROUTES_DE_LA_BOUTIQUE)


def _participer(api, campagne, quantite) -> dict:
    part = api.post("/api/participations/",
                    {"campagne": campagne.id, "quantite": quantite},
                    format="json").data
    api.post(f"/api/participations/{part['id']}/payer/", {}, format="json")
    return part


def _lien(destinataire, genre, titre=None) -> str:
    filtre = {"destinataire": destinataire, "genre": genre}
    if titre:
        filtre["titre"] = titre
    return Notification.objects.get(**filtre).lien


class TestLiensDeLAcheteur:
    def test_le_paiement_pointe_vers_la_commande_de_l_acheteur(
        self, connecte, campagne, ama
    ):
        part = _participer(connecte(ama), campagne, 3)

        assert _lien(ama, "paiement_enregistre") == f"/mes-achats/{part['id']}"
        # Le lien désigne une ressource qui existe, et que l'acheteur lit.
        detail = connecte(ama).get(f"/api/participations/{part['id']}/")
        assert detail.status_code == 200
        assert detail.data["code_retrait"]
        assert "charge_qr" in detail.data

    def test_un_paiement_refuse_ne_cree_pas_de_notification(
        self, connecte, campagne, ama
    ):
        part = _participer(connecte(ama), campagne, 3)
        avant = Notification.objects.count()

        # Part déjà payée : le second paiement est refusé.
        reponse = connecte(ama).post(
            f"/api/participations/{part['id']}/payer/", {}, format="json"
        )

        assert reponse.status_code == 400
        assert Notification.objects.count() == avant

    def test_le_lien_de_la_commande_ne_sert_qu_a_son_proprietaire(
        self, connecte, client, campagne, ama, yao
    ):
        part = _participer(connecte(ama), campagne, 3)
        adresse = f"/api/participations/{part['id']}/"

        autre = connecte(yao).get(adresse)
        assert autre.status_code == 404
        assert "code_retrait" not in autre.data

        client.force_authenticate(user=None)
        assert client.get(adresse).status_code in (401, 403)
        assert client.get("/api/notifications/").status_code in (401, 403)

    def test_on_ne_marque_pas_lue_la_notification_d_un_autre(
        self, connecte, campagne, ama, yao
    ):
        _participer(connecte(ama), campagne, 3)
        notification = Notification.objects.get(
            destinataire=ama, genre="paiement_enregistre"
        )

        reponse = connecte(yao).post(
            f"/api/notifications/{notification.id}/marquer-lue/", {}, format="json"
        )

        assert reponse.status_code == 404
        notification.refresh_from_db()
        assert notification.lue_le is None


class TestParcoursComplet:
    def test_le_produit_arrive_et_le_retrait_pointent_vers_la_commande(
        self, connecte, administrateur, campagne, ama
    ):
        part = _financer_et_livrer(connecte, administrateur, campagne, ama)

        assert _lien(ama, "marchandise_disponible") == f"/mes-achats/{part['id']}"
        assert _lien(ama, "retrait_confirme") == f"/mes-achats/{part['id']}"
        assert Participation.objects.get(pk=part["id"]).statut == "retiree"

    def test_les_fonds_verses_pointent_vers_la_campagne_du_groupeur(
        self, connecte, administrateur, campagne, ama
    ):
        _financer_et_livrer(connecte, administrateur, campagne, ama)

        lien = _lien(campagne.groupeur, "campagne_financee", titre="Fonds versés")
        assert lien == f"/groupeur/campagnes/{campagne.id}"

    def test_chaque_lien_de_notification_correspond_a_une_route_de_la_boutique(
        self, connecte, client, administrateur, campagne, ama, yao,
        groupeur_en_attente, produit
    ):
        # Campagne 1 : jusqu'au retrait, puis un avis et un commentaire.
        _financer_et_livrer(connecte, administrateur, campagne, ama)
        connecte(ama).post(
            f"/api/campagnes/{campagne.id}/commentaires/",
            {"texte": "Merci pour la livraison"}, format="json",
        )
        premier = campagne.commentaires.get()
        connecte(campagne.groupeur).post(
            f"/api/campagnes/{campagne.id}/commentaires/",
            {"texte": "Avec plaisir", "reponse_a": premier.id}, format="json",
        )
        part = Participation.objects.get(acheteur=ama)
        connecte(ama).post("/api/avis/", {"participation": part.id, "note": 5},
                           format="json")

        # Campagne 2 : sous le minimum, maintenue ; campagne 3 : annulée.
        for decision in ("maintenir", "annuler"):
            autre = Campagne.objects.create(
                produit=produit, groupeur=campagne.groupeur,
                titre=f"Autre {decision}", prix_unitaire=18000,
                quantite_minimale=10,
                date_limite=timezone.now() + timedelta(days=5),
                statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now(),
            )
            _participer(connecte(yao), autre, 2)
            Campagne.objects.filter(pk=autre.pk).update(
                date_limite=timezone.now() - timedelta(hours=1)
            )
            cloturer_les_echus()
            connecte(campagne.groupeur).post(
                f"/api/groupeur/campagnes/{autre.id}/{decision}/", {}, format="json"
            )

        # Décision sur un dossier KYC.
        dossier = DossierKYC.objects.get(utilisateur=groupeur_en_attente)
        connecte(administrateur).post(
            f"/api/admin/dossiers/{dossier.id}/decision/",
            {"decision": "valider"}, format="json",
        )

        genres = set(Notification.objects.values_list("genre", flat=True))
        # Le parcours doit réellement produire les genres qu'on prétend contrôler.
        assert genres >= {
            "paiement_enregistre", "paiement_recu", "minimum_atteint",
            "campagne_financee", "marchandise_disponible", "retrait_confirme",
            "groupage_non_abouti", "decision_attendue", "campagne_maintenue",
            "campagne_annulee", "nouveau_commentaire", "reponse_commentaire",
            "nouvel_avis", "kyc_decide",
        }
        for notification in Notification.objects.exclude(lien=""):
            assert _route_existe(notification.lien), (
                f"« {notification.titre} » ({notification.genre}) mène à "
                f"{notification.lien}, que la boutique ne sert pas"
            )


def _financer_et_livrer(connecte, administrateur, campagne, ama) -> dict:
    """Paiement du minimum, clôture, décaissement, arrivée, retrait."""
    part = _participer(connecte(ama), campagne, campagne.quantite_minimale)
    groupeur = connecte(campagne.groupeur)
    groupeur.post(f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json")
    groupeur.post(f"/api/groupeur/campagnes/{campagne.id}/demander-retrait/", {},
                  format="json")
    admin = connecte(administrateur)
    decaissement = admin.get("/api/admin/decaissements/").data["results"][0]
    admin.post(f"/api/admin/decaissements/{decaissement['id']}/executer/", {},
               format="json")

    groupeur = connecte(campagne.groupeur)
    groupeur.post(f"/api/groupeur/campagnes/{campagne.id}/mise-a-disposition/", {},
                  format="json")
    code = Participation.objects.get(pk=part["id"]).code_retrait
    reponse = groupeur.post(f"/api/groupeur/campagnes/{campagne.id}/retrait/",
                            {"code": code}, format="json")
    assert reponse.status_code == 200, reponse.data
    return part
