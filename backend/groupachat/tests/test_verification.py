# -*- coding: utf-8 -*-
"""La relecture avant vitrine, selon le grade.

Bronze systematiquement, Argent une fois sur quatre, Or jamais. C'est le seul
filtre entre un OAG tout neuf et la vitrine : le dossier KYC dit qui il est,
il ne dit rien de ce qu'il publie.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.catalogue.publication import PackPublication, publications_en_reserve
from groupachat.comptes.models import CompteurPoints

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cache_propre():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def brouillon(groupeur, produit):
    def _creer(titre="Un groupage a publier"):
        return Campagne.objects.create(
            produit=produit, groupeur=groupeur, titre=titre,
            prix_unitaire=18000, quantite_minimale=10,
            date_limite=timezone.now() + timedelta(days=10),
            statut=Campagne.Statut.BROUILLON,
        )

    return _creer


@pytest.fixture
def droit(connecte, groupeur):
    """Un pack, pour que publier soit possible."""
    connecte(groupeur).post("/api/groupeur/publication/pack/", {}, format="json")
    return None


def grader(utilisateur, cumules: int):
    compteur, _ = CompteurPoints.objects.get_or_create(utilisateur=utilisateur)
    CompteurPoints.objects.filter(pk=compteur.pk).update(
        cumules=cumules, solde=cumules
    )


def publier(api, campagne):
    return api.post(f"/api/groupeur/campagnes/{campagne.id}/publier/", {},
                    format="json")


class TestSelonLeGrade:
    def test_en_bronze_tout_passe_en_verification(
        self, connecte, groupeur, brouillon, droit
    ):
        reponse = publier(connecte(groupeur), brouillon())
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["statut"] == "en_verification"

    def test_en_or_la_publication_est_libre(
        self, connecte, groupeur, brouillon, droit
    ):
        grader(groupeur, 940)
        reponse = publier(connecte(groupeur), brouillon())
        assert reponse.data["statut"] == "en_cours"
        assert reponse.data["publiee_le"] is not None

    def test_en_argent_une_sur_quatre(self, connecte, groupeur, brouillon, droit):
        """Un sondage, et non une relecture systematique.

        Le compte porte sur les mises en ligne passees : la premiere tombe
        sur le sondage, les trois suivantes passent.
        """
        grader(groupeur, 560)
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")

        statuts = [
            publier(api, brouillon(f"Groupage {rang}")).data["statut"]
            for rang in range(5)
        ]
        assert statuts[0] == "en_verification"
        assert statuts[1:4] == ["en_cours"] * 3
        assert statuts[4] == "en_verification"


class TestCeQueLaVerificationEmpeche:
    def test_la_campagne_n_est_pas_au_catalogue(
        self, client, connecte, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)

        resultats = client.get("/api/catalogue/campagnes/").data["results"]
        assert campagne.id not in [c["id"] for c in resultats]

    def test_sa_fiche_n_est_pas_ouvrable(
        self, client, connecte, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        assert client.get(f"/api/catalogue/campagnes/{campagne.id}/").status_code == 404

    def test_on_ne_peut_pas_y_participer(
        self, connecte, groupeur, brouillon, droit, ama
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        reponse = connecte(ama).post(
            "/api/participations/",
            {"campagne": campagne.id, "quantite": 1,
             "bureau_poste": "Bureau de poste de Tokoin"},
            format="json",
        )
        assert reponse.status_code == 400

    def test_aucun_sequestre_n_est_ouvert_avant_la_vitrine(
        self, connecte, groupeur, brouillon, droit
    ):
        """Rien a consigner tant que personne ne peut payer."""
        from groupachat.paiements.models import Sequestre

        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        assert not Sequestre.objects.filter(campagne=campagne).exists()


class TestLaDecisionDeLAdministration:
    def test_elle_voit_la_file(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        campagne = brouillon("A relire")
        publier(connecte(groupeur), campagne)

        file = connecte(administrateur).get("/api/admin/campagnes/a-verifier/")
        assert file.status_code == 200
        assert [c["id"] for c in file.data] == [campagne.id]
        # De quoi juger : le prix, le bareme, le produit, l'OAG sous pseudo.
        assert file.data[0]["produit"]["nom"]
        assert file.data[0]["groupeur"]["nom_utilisateur"]

    def test_le_tableau_de_bord_la_compte(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        publier(connecte(groupeur), brouillon())
        bord = connecte(administrateur).get("/api/admin/tableau-de-bord/").data
        assert bord["a_traiter"]["campagnes_a_verifier"] == 1

    def test_valider_met_en_vitrine(
        self, client, connecte, administrateur, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)

        reponse = connecte(administrateur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "valider"}, format="json",
        )
        assert reponse.status_code == 200
        assert reponse.data["statut"] == "en_cours"

        resultats = client.get("/api/catalogue/campagnes/").data["results"]
        assert campagne.id in [c["id"] for c in resultats]

    def test_refuser_renvoie_au_brouillon_avec_le_motif(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)

        reponse = connecte(administrateur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "refuser", "motif": "La photo ne montre pas le lot."},
            format="json",
        )
        assert reponse.status_code == 200
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.BROUILLON
        assert "photo" in campagne.motif_annulation

    def test_un_refus_sans_motif_est_refuse(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        """Un refus sans motif ne se corrige pas."""
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        reponse = connecte(administrateur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "refuser"}, format="json",
        )
        assert reponse.status_code == 400

    def test_le_refus_rend_la_publication(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        """Elle paie la mise en ligne, et la mise en ligne n'a pas eu lieu."""
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        assert publications_en_reserve(groupeur) == 4

        connecte(administrateur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "refuser", "motif": "Prix incoherent."}, format="json",
        )
        assert publications_en_reserve(groupeur) == 5

    def test_la_validation_ne_rend_rien(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        connecte(administrateur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "valider"}, format="json",
        )
        assert publications_en_reserve(groupeur) == 4

    def test_l_oag_est_prevenu_dans_les_deux_cas(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        from groupachat.echanges.models import Notification

        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        assert Notification.objects.filter(
            destinataire=groupeur, titre="Groupage en vérification"
        ).exists()

        connecte(administrateur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "refuser", "motif": "Photo volee."}, format="json",
        )
        avis = Notification.objects.filter(
            destinataire=groupeur, titre="Groupage à corriger"
        ).first()
        assert avis is not None
        assert "Photo volee" in avis.message
        assert "rendue" in avis.message

    def test_une_decision_sans_sens_est_refusee(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        reponse = connecte(administrateur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "peut-etre"}, format="json",
        )
        assert reponse.status_code == 400

    def test_une_campagne_deja_tranchee_ne_se_retranche_pas(
        self, connecte, administrateur, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        chemin = f"/api/admin/campagnes/{campagne.id}/verification/"
        connecte(administrateur).post(chemin, {"decision": "valider"},
                                      format="json")
        assert connecte(administrateur).post(
            chemin, {"decision": "valider"}, format="json"
        ).status_code == 404


class TestCloisonnement:
    def test_l_oag_ne_valide_pas_ses_propres_groupages(
        self, connecte, groupeur, brouillon, droit
    ):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        reponse = connecte(groupeur).post(
            f"/api/admin/campagnes/{campagne.id}/verification/",
            {"decision": "valider"}, format="json",
        )
        assert reponse.status_code == 403
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.EN_VERIFICATION

    def test_un_acheteur_ne_voit_pas_la_file(self, connecte, ama):
        assert connecte(ama).get(
            "/api/admin/campagnes/a-verifier/"
        ).status_code == 403
