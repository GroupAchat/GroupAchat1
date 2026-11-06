# -*- coding: utf-8 -*-
"""Le parrainage : amener quelqu'un, et etre paye quand il achete.

Un clic ne vaut rien, une inscription sans achat ne vaut rien. C'est le seul
endroit du produit ou l'on pourrait creer de la valeur sans rien apporter, et
ces tests sont la pour le fermer.
"""

from __future__ import annotations

import pytest

from groupachat.comptes.models import CompteurPoints, Utilisateur
from groupachat.comptes.parrainage import Parrainage, bilan, code_de

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cache_propre():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def commander(api, campagne, **extra):
    return api.post(
        "/api/participations/",
        {
            "campagne": campagne.id,
            "quantite": 2,
            "bureau_poste": "Bureau de poste de Tokoin",
            **extra,
        },
        format="json",
    )


def payer(api, reponse):
    return api.post(
        f"/api/participations/{reponse.data['id']}/payer/",
        {"operateur": "tmoney"},
        format="json",
    )


def cumules(utilisateur) -> int:
    compteur, _ = CompteurPoints.objects.get_or_create(utilisateur=utilisateur)
    return compteur.cumules


class TestLeCode:
    def test_il_apparait_au_premier_besoin(self, connecte, ama):
        """Pas a l'inscription : la plupart des comptes ne parraineront jamais."""
        ama.refresh_from_db()
        assert ama.code_parrainage is None

        donnees = connecte(ama).get("/api/comptes/parrainage/").data
        assert len(donnees["code"]) == 6
        ama.refresh_from_db()
        assert ama.code_parrainage == donnees["code"]

    def test_il_ne_change_pas_d_un_appel_a_l_autre(self, connecte, ama):
        api = connecte(ama)
        premier = api.get("/api/comptes/parrainage/").data["code"]
        assert api.get("/api/comptes/parrainage/").data["code"] == premier

    def test_il_ne_se_devine_pas(self, connecte, ama):
        """Un `?p=42` se devine, se change, et dit combien de comptes existent."""
        code = connecte(ama).get("/api/comptes/parrainage/").data["code"]
        assert str(ama.id) not in code
        assert ama.telephone not in code

    def test_le_bilan_part_de_zero(self, connecte, ama):
        donnees = connecte(ama).get("/api/comptes/parrainage/").data
        assert donnees["filleuls"] == 0
        assert donnees["points_gagnes"] == 0
        assert donnees["points_par_filleul"] == 2


class TestCeQuiNeRapporteRien:
    def test_une_commande_sans_paiement_ne_rapporte_rien(
        self, connecte, campagne, ama, yao
    ):
        """« Un clic, une inscription sans paiement : aucun point. »"""
        code = code_de(ama)
        avant = cumules(ama)

        commander(connecte(yao), campagne, code_parrainage=code)

        assert Parrainage.objects.filter(parrain=ama, filleul=yao).exists()
        assert Parrainage.objects.get().valide_le is None
        assert cumules(ama) == avant

    def test_un_code_inconnu_n_empeche_pas_d_acheter(
        self, connecte, campagne, yao
    ):
        """Un lien se partage sans savoir ce qu'il devient : un code mort ne
        doit pas faire echouer la commande de celui qui l'a suivi."""
        reponse = commander(connecte(yao), campagne, code_parrainage="XXXXXX")
        assert reponse.status_code == 201, reponse.data
        assert not Parrainage.objects.exists()

    def test_on_ne_se_parraine_pas_soi_meme(self, connecte, campagne, yao):
        reponse = commander(connecte(yao), campagne, code_parrainage=code_de(yao))
        assert reponse.status_code == 201
        assert not Parrainage.objects.exists()

    def test_le_second_parrain_arrive_trop_tard(
        self, connecte, campagne, ama, yao
    ):
        """Un filleul n'a qu'un parrain : le premier qui l'amene.

        Sans cette regle, deux personnes se disputeraient le meme merite, et
        le meme compte servirait de filleul a tout un reseau.
        """
        autre = Utilisateur.objects.create_user(
            "97001122", "mdpSolide2026", nom="Koffi", prenom="Dede",
            telephone_verifie=True,
        )
        commander(connecte(yao), campagne, code_parrainage=code_de(ama))
        commander(connecte(yao), campagne, code_parrainage=code_de(autre))

        assert Parrainage.objects.count() == 1
        assert Parrainage.objects.get().parrain == ama


class TestLePaiementValide:
    def test_deux_points_au_parrain(self, connecte, campagne, ama, yao):
        avant = cumules(ama)
        reponse = commander(connecte(yao), campagne, code_parrainage=code_de(ama))
        assert payer(connecte(yao), reponse).status_code == 200

        assert cumules(ama) == avant + 2
        lien = Parrainage.objects.get()
        assert lien.valide_le is not None
        assert lien.campagne == campagne

    def test_le_filleul_garde_ses_propres_points_d_achat(
        self, connecte, campagne, ama, yao
    ):
        """Le parrainage s'ajoute, il ne remplace pas : le filleul touche ses
        dix points d'achat comme n'importe quel acheteur."""
        avant = cumules(yao)
        reponse = commander(connecte(yao), campagne, code_parrainage=code_de(ama))
        payer(connecte(yao), reponse)
        assert cumules(yao) == avant + 10

    def test_un_second_achat_ne_repaie_pas_le_parrain(
        self, connecte, campagne, ama, yao
    ):
        """Le parrainage paie l'arrivee d'une personne, pas chacun de ses achats."""
        payer(connecte(yao), commander(connecte(yao), campagne,
                                       code_parrainage=code_de(ama)))
        apres_premier = cumules(ama)

        payer(connecte(yao), commander(connecte(yao), campagne,
                                       code_parrainage=code_de(ama)))
        assert cumules(ama) == apres_premier

    def test_deux_filleuls_rapportent_deux_fois(
        self, connecte, campagne, ama, yao
    ):
        troisieme = Utilisateur.objects.create_user(
            "97112233", "mdpSolide2026", nom="Adjo", prenom="Sena",
            telephone_verifie=True,
        )
        avant = cumules(ama)
        code = code_de(ama)
        payer(connecte(yao), commander(connecte(yao), campagne,
                                       code_parrainage=code))
        payer(connecte(troisieme), commander(connecte(troisieme), campagne,
                                             code_parrainage=code))
        assert cumules(ama) == avant + 4

    def test_le_bilan_suit(self, connecte, campagne, ama, yao):
        payer(connecte(yao), commander(connecte(yao), campagne,
                                       code_parrainage=code_de(ama)))
        donnees = connecte(ama).get("/api/comptes/parrainage/").data
        assert donnees["filleuls"] == 1
        assert donnees["filleuls_valides"] == 1
        assert donnees["en_attente"] == 0
        assert donnees["points_gagnes"] == 2

    def test_le_parrainage_fait_monter_en_grade_comme_le_reste(
        self, connecte, campagne, ama, yao
    ):
        """Les points de parrainage sont des points : ils comptent au cumul."""
        compteur, _ = CompteurPoints.objects.get_or_create(utilisateur=ama)
        CompteurPoints.objects.filter(pk=compteur.pk).update(
            cumules=498, solde=498
        )
        payer(connecte(yao), commander(connecte(yao), campagne,
                                       code_parrainage=code_de(ama)))
        compteur.refresh_from_db()
        assert compteur.cumules == 500
        assert compteur.grade == "argent"


class TestCeQueLeParrainageNeDitPas:
    def test_le_bilan_ne_nomme_pas_les_filleuls(self, connecte, campagne, ama, yao):
        """Qui a accepte l'invitation ne regarde que l'invite.

        Le parrain a droit au nombre et aux points ; pas a la liste de ceux
        qui ont achete, ni a ce qu'ils ont achete.
        """
        payer(connecte(yao), commander(connecte(yao), campagne,
                                       code_parrainage=code_de(ama)))
        donnees = str(connecte(ama).get("/api/comptes/parrainage/").data)
        assert yao.telephone not in donnees
        assert yao.nom_complet not in donnees


class TestLeCodeNeFuitPas:
    def test_il_n_apparait_pas_sur_le_profil_public_d_un_oag(
        self, client, groupeur, produit
    ):
        """Le code sert a inviter, pas a identifier : il reste prive."""
        code_de(groupeur)
        vignette = client.get("/api/catalogue/campagnes/").data["results"]
        assert "code_parrainage" not in str(vignette)

    def test_ni_dans_le_bilan_d_un_autre(self, connecte, ama, yao):
        code_ama = code_de(ama)
        donnees = connecte(yao).get("/api/comptes/parrainage/").data
        assert donnees["code"] != code_ama
