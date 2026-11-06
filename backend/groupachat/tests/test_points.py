# -*- coding: utf-8 -*-
"""Les points, les grades, et la commission qui en découle.

Deux règles portent tout le reste.

**Dépenser ne fait pas perdre son grade.** Les points mesurent un parcours
*et* s'échangent contre des avantages ; avec un compteur unique, personne ne
dépenserait jamais rien. D'où `cumules`, qui ne descend pas, et `solde`, qui
descend.

**Un événement n'attribue qu'une fois.** Sans ça, faire échouer puis rejouer
une opération suffirait à monter en grade, et la commission d'un groupeur ne
voudrait plus rien dire.
"""

from __future__ import annotations

import pytest

from groupachat.comptes import grades, points
from groupachat.comptes.models import CompteurPoints
from groupachat.paiements.models import Decaissement

pytestmark = pytest.mark.django_db


class TestLeBareme:
    def test_nouveau_est_le_point_de_depart_et_bronze_a_250(self):
        assert grades.grade_pour(0) == grades.Grade.NOUVEAU
        assert grades.SEUILS[grades.Grade.BRONZE] == 250
        assert grades.SEUILS[grades.Grade.ARGENT] == 400
        assert grades.SEUILS[grades.Grade.OR] == 600

    @pytest.mark.parametrize(
        "cumules, attendu",
        [
            (0, grades.Grade.NOUVEAU),
            (249, grades.Grade.NOUVEAU),
            (250, grades.Grade.BRONZE),
            (399, grades.Grade.BRONZE),
            (400, grades.Grade.ARGENT),
            (599, grades.Grade.ARGENT),
            (600, grades.Grade.OR),
            (5000, grades.Grade.OR),
        ],
    )
    def test_le_grade_suit_les_points_cumules(self, cumules, attendu):
        assert grades.grade_pour(cumules) == attendu

    def test_les_taux_sont_ceux_du_cahier(self):
        assert grades.commission_centiemes(grades.Grade.NOUVEAU) == 400
        assert grades.commission_centiemes(grades.Grade.BRONZE) == 400
        assert grades.commission_centiemes(grades.Grade.ARGENT) == 300
        assert grades.commission_centiemes(grades.Grade.OR) == 200

    def test_la_commission_reste_un_entier_de_francs(self):
        # 4 % de 360 000 : 14 400 FCFA
        assert grades.commission_sur(360_000, 400) == 14_400
        assert grades.commission_sur(360_000, 300) == 10_800
        assert grades.commission_sur(360_000, 200) == 7_200

    def test_l_arrondi_va_en_faveur_du_groupeur(self):
        """Sur un écart d'un franc, c'est la plateforme qui le laisse."""
        assert grades.commission_sur(1_001, 400) == 40

    def test_le_prochain_palier_dit_ce_qu_il_reste(self):
        assert grades.prochain_palier(0) == (grades.Grade.BRONZE, 250)
        assert grades.prochain_palier(250) == (grades.Grade.ARGENT, 150)
        assert grades.prochain_palier(400) == (grades.Grade.OR, 200)
        assert grades.prochain_palier(600) is None


class TestLesDeuxCompteurs:
    def test_depenser_ne_fait_pas_perdre_son_grade(self, groupeur):
        for numero in range(70):
            points.attribuer(
                groupeur, points.Motif.ABONNEMENT_PUBLICATION, "abonnement", numero
            )
        compteur = points.compteur_de(groupeur)
        assert compteur.cumules == 700
        assert compteur.grade == grades.Grade.OR

        points.depenser(groupeur, 400, "mise_en_avant", 1)

        compteur.refresh_from_db()
        assert compteur.solde == 300
        assert compteur.cumules == 700, "les cumulés ne descendent jamais"
        assert compteur.grade == grades.Grade.OR, "le grade survit à la dépense"

    def test_on_ne_depense_pas_ce_qu_on_n_a_pas(self, ama):
        points.attribuer(ama, points.Motif.ACHAT, "participation", 1)
        with pytest.raises(points.SoldeInsuffisant):
            points.depenser(ama, 50, "livraison", 1)

    def test_le_solde_ne_peut_pas_depasser_le_cumul(self, ama):
        points.attribuer(ama, points.Motif.ACHAT, "participation", 1)
        compteur = points.compteur_de(ama)
        assert compteur.solde <= compteur.cumules


class TestIdempotence:
    def test_le_meme_evenement_n_attribue_qu_une_fois(self, ama):
        premier = points.attribuer(ama, points.Motif.ACHAT, "participation", 7)
        second = points.attribuer(ama, points.Motif.ACHAT, "participation", 7)

        assert premier is not None
        assert second is None, "un rejeu ne doit rien créditer"
        assert points.compteur_de(ama).cumules == 5

    def test_deux_evenements_distincts_comptent_chacun(self, ama):
        points.attribuer(ama, points.Motif.ACHAT, "participation", 7)
        points.attribuer(ama, points.Motif.ACHAT, "participation", 8)
        assert points.compteur_de(ama).cumules == 10


class TestLaCommissionAuDecaissement:
    def test_un_groupeur_bronze_paie_4_pour_cent(self):
        frais, net = Decaissement.calculer(360_000, 400)
        assert frais == 14_400
        assert net == 345_600

    def test_le_taux_est_fige_dans_le_decaissement(self, campagne, groupeur, connecte, ama):
        """Monter en grade après coup ne refait pas les comptes déjà faits."""
        from groupachat.paiements import services

        api = connecte(ama)
        part = api.post(
            "/api/participations/",
            {"campagne": campagne.id, "quantite": campagne.quantite_minimale, "bureau_poste": "Bureau de poste de Tokoin"},
            format="json",
        ).data
        api.post(f"/api/participations/{part['id']}/payer/", {}, format="json")

        campagne.refresh_from_db()
        campagne.statut = campagne.Statut.FINANCEE
        campagne.save(update_fields=["statut"])

        decaissement = services.demander_decaissement(campagne)
        assert decaissement.taux_commission == 400

        # Le groupeur passe Or après coup.
        CompteurPoints.objects.update_or_create(
            utilisateur=groupeur, defaults={"cumules": 900, "solde": 900}
        )
        decaissement.refresh_from_db()
        assert decaissement.taux_commission == 400, "un retrait chiffré ne bouge plus"


class TestLesPointsSeGagnentSurLeParcours:
    def test_un_achat_paye_rapporte_cinq_points_a_l_acheteur(
        self, connecte, campagne, ama
    ):
        api = connecte(ama)
        part = api.post(
            "/api/participations/",
            {"campagne": campagne.id, "quantite": 2, "bureau_poste": "Bureau de poste de Tokoin"},
            format="json",
        ).data
        assert points.compteur_de(ama).cumules == 0, "rien avant le paiement"

        api.post(f"/api/participations/{part['id']}/payer/", {}, format="json")
        assert points.compteur_de(ama).cumules == 5
