# -*- coding: utf-8 -*-
"""Le droit de publier : abonnement ou pack.

C'est la recette de la plateforme autant que la commission, et la seule
barriere a l'entree du catalogue. Les regles tiennent en quatre phrases : la
publication se consomme a la mise en ligne, l'abonnement est illimite, les
packs s'additionnent et n'expirent pas, et rien n'est rendu si le groupage
echoue.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.catalogue.publication import (
    AbonnementPublication,
    PackPublication,
    publications_en_reserve,
)
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
    """Une campagne prete a publier, et rien de plus."""

    def _creer(titre="Un groupage a publier"):
        return Campagne.objects.create(
            produit=produit, groupeur=groupeur, titre=titre,
            prix_unitaire=18000, quantite_minimale=10,
            date_limite=timezone.now() + timedelta(days=10),
            statut=Campagne.Statut.BROUILLON,
        )

    return _creer


def publier(api, campagne):
    return api.post(f"/api/groupeur/campagnes/{campagne.id}/publier/", {},
                    format="json")


def points_de(utilisateur) -> tuple[int, int]:
    compteur, _ = CompteurPoints.objects.get_or_create(utilisateur=utilisateur)
    return compteur.cumules, compteur.solde


class TestSansDroitOnNePubliePas:
    def test_le_catalogue_se_merite(self, connecte, groupeur, brouillon):
        """Publier sans avoir paye : refuse, et le prix est dit.

        Un refus qui ne dit pas combien ca coute oblige a chercher ailleurs,
        et on ne cherche pas : on abandonne.
        """
        reponse = publier(connecte(groupeur), brouillon())
        assert reponse.status_code == 402
        assert reponse.data["droit_requis"] is True
        assert reponse.data["prix_abonnement"] == 2000
        assert reponse.data["prix_pack"] == 100

    def test_la_campagne_reste_en_brouillon(self, connecte, groupeur, brouillon):
        campagne = brouillon()
        publier(connecte(groupeur), campagne)
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.BROUILLON

    def test_l_etat_dit_ce_qu_il_faut_pour_decider(self, connecte, groupeur):
        etat = connecte(groupeur).get("/api/groupeur/publication/").data
        assert etat["peut_publier"] is False
        assert etat["publications_restantes"] == 0
        assert etat["publications_par_pack"] == 10
        assert etat["duree_jours"] == 30


class TestLePack:
    def test_il_donne_dix_publications_et_deux_points(self, connecte, groupeur):
        avant_cumules, _ = points_de(groupeur)
        reponse = connecte(groupeur).post("/api/groupeur/publication/pack/", {},
                                         format="json")
        assert reponse.status_code == 201
        assert reponse.data["publications_restantes"] == 10
        assert reponse.data["peut_publier"] is True

        apres_cumules, apres_solde = points_de(groupeur)
        assert apres_cumules == avant_cumules + 2

    def test_les_packs_s_additionnent(self, connecte, groupeur):
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        reponse = api.post("/api/groupeur/publication/pack/", {}, format="json")
        assert reponse.data["publications_restantes"] == 20

    def test_mais_les_points_ne_sont_donnes_qu_une_fois(self, connecte, groupeur):
        """« 2 points, une seule fois » : le dixieme pack ne rapporte rien."""
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        apres_premier, _ = points_de(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        apres_second, _ = points_de(groupeur)
        assert apres_second == apres_premier

    def test_publier_consomme_une_unite(self, connecte, groupeur, brouillon):
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")

        reponse = publier(api, brouillon())
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["publication_payee_par"] == "pack"
        assert reponse.data["droit_de_publier"]["publications_restantes"] == 9

    def test_le_brouillon_ne_coute_rien(self, connecte, groupeur, brouillon):
        """Un groupage abandonne avant publication ne se paie pas."""
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        brouillon("Jamais publie")
        brouillon("Jamais publie non plus")
        assert publications_en_reserve(groupeur) == 10

    def test_la_reserve_s_epuise(self, connecte, groupeur, brouillon):
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        for rang in range(10):
            assert publier(api, brouillon(f"Groupage {rang}")).status_code == 200
        assert publier(api, brouillon("Le onzieme")).status_code == 402

    def test_un_pack_n_expire_pas(self, connecte, groupeur, brouillon):
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        PackPublication.objects.update(
            achete_le=timezone.now() - timedelta(days=400)
        )
        assert publier(api, brouillon()).status_code == 200


class TestLAbonnement:
    def test_il_ouvre_un_mois_illimite_et_dix_points(self, connecte, groupeur):
        avant, _ = points_de(groupeur)
        reponse = connecte(groupeur).post(
            "/api/groupeur/publication/abonnement/", {}, format="json"
        )
        assert reponse.status_code == 201
        assert reponse.data["abonnement_actif"] is True
        assert reponse.data["peut_publier"] is True

        apres, _ = points_de(groupeur)
        assert apres == avant + 10

    def test_publier_ne_consomme_rien(self, connecte, groupeur, brouillon):
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        api.post("/api/groupeur/publication/abonnement/", {}, format="json")

        for rang in range(7):
            reponse = publier(api, brouillon(f"Groupage {rang}"))
            assert reponse.status_code == 200, reponse.data
            assert reponse.data["publication_payee_par"] == "abonnement"

        # Les deux compteurs sont independants : entamer la reserve d'un
        # abonne lui ferait payer deux fois le meme mois.
        assert publications_en_reserve(groupeur) == 10

    def test_renouveler_tot_ajoute_les_jours_restants(self, connecte, groupeur):
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/abonnement/", {}, format="json")
        premiere = AbonnementPublication.actif_pour(groupeur).expire_le
        api.post("/api/groupeur/publication/abonnement/", {}, format="json")
        seconde = AbonnementPublication.actif_pour(groupeur).expire_le
        assert (seconde - premiere).days == 30

    def test_a_l_echeance_les_packs_restent(self, connecte, groupeur, brouillon):
        """Il a paye ces publications ; un mois qui s'acheve ne les lui prend pas."""
        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        api.post("/api/groupeur/publication/abonnement/", {}, format="json")
        publier(api, brouillon("Pendant l'abonnement"))

        AbonnementPublication.objects.update(
            expire_le=timezone.now() - timedelta(days=1)
        )
        etat = api.get("/api/groupeur/publication/").data
        assert etat["abonnement_actif"] is False
        assert etat["publications_restantes"] == 10
        assert etat["peut_publier"] is True

        reponse = publier(api, brouillon("Apres l'echeance"))
        assert reponse.status_code == 200
        assert reponse.data["publication_payee_par"] == "pack"


class TestCeQuiNEstPasRendu:
    def test_un_groupage_qui_echoue_ne_rembourse_pas_la_publication(
        self, connecte, groupeur, brouillon
    ):
        """Elle paie la mise en ligne, pas la reussite."""
        from groupachat.paiements.services import cloturer

        api = connecte(groupeur)
        api.post("/api/groupeur/publication/pack/", {}, format="json")
        campagne = brouillon()
        publier(api, campagne)
        assert publications_en_reserve(groupeur) == 9

        campagne.refresh_from_db()
        Campagne.objects.filter(pk=campagne.pk).update(
            date_limite=timezone.now() - timedelta(hours=1)
        )
        campagne.refresh_from_db()
        cloturer(campagne)

        campagne.refresh_from_db()
        assert campagne.statut != Campagne.Statut.EN_COURS
        assert publications_en_reserve(groupeur) == 9


class TestCloisonnement:
    def test_un_acheteur_n_achete_pas_de_publications(self, connecte, ama):
        api = connecte(ama)
        assert api.get("/api/groupeur/publication/").status_code == 403
        assert api.post("/api/groupeur/publication/pack/", {},
                        format="json").status_code == 403

    def test_la_reserve_d_un_oag_n_est_pas_celle_d_un_autre(
        self, connecte, groupeur, groupeur_en_attente
    ):
        connecte(groupeur).post("/api/groupeur/publication/pack/", {}, format="json")
        assert publications_en_reserve(groupeur) == 10
        assert publications_en_reserve(groupeur_en_attente) == 0
