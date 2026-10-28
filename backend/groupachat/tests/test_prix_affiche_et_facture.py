# -*- coding: utf-8 -*-
"""C-013 : le prix que l'écran annonce est celui que le serveur facture.

L'écran (`frontend/commun/src/outils/prix.ts`) reprend la règle de
`Campagne.prix_pour_quantite` : palier atteint en comptant les pièces déjà
payées **plus** la quantité demandée. Les valeurs attendues sont écrites en dur
ici, sans passer par le modèle : si le serveur change sa règle, ce test casse et
rappelle qu'il faut changer `prix.ts` dans le même passage.
"""

from __future__ import annotations

import pytest

from groupachat.catalogue.models import PalierPrix
from groupachat.commandes.models import Participation
from groupachat.commandes.tests import participer_et_payer

pytestmark = pytest.mark.django_db

# (pièces demandées, prix unitaire facturé, montant total) pour une campagne à
# 7 000 FCFA, paliers 10 pièces -> 6 500 et 20 pièces -> 6 000, 8 pièces déjà
# payées par d'autres.
CAS_DU_PALIER = [
    pytest.param(1, 7000, 7000, id="juste-sous-le-premier-palier"),
    pytest.param(2, 6500, 13000, id="pile-au-premier-palier"),
    pytest.param(3, 6500, 19500, id="entre-les-deux-paliers"),
    pytest.param(12, 6000, 72000, id="franchit-le-second-palier"),
]


@pytest.fixture
def campagne_a_paliers(campagne, yao):
    """7 000 FCFA la pièce, deux paliers, 8 pièces déjà consignées."""
    campagne.prix_unitaire = 7000
    campagne.save(update_fields=["prix_unitaire"])
    PalierPrix.objects.create(campagne=campagne, quantite_min=10, prix_unitaire=6500)
    PalierPrix.objects.create(campagne=campagne, quantite_min=20, prix_unitaire=6000)
    Participation.objects.create(
        campagne=campagne, acheteur=yao, quantite=8,
        prix_unitaire_applique=7000, montant_total=56000,
        statut=Participation.Statut.PAYEE, code_retrait="CODEPAYE",
    )
    return campagne


class TestPrixAfficheEtFacture:
    @pytest.mark.parametrize("quantite, prix_attendu, total_attendu", CAS_DU_PALIER)
    def test_le_prix_facture_suit_le_palier_atteint_avec_la_quantite_demandee(
        self, connecte, campagne_a_paliers, ama, quantite, prix_attendu, total_attendu
    ):
        reponse = connecte(ama).post(
            "/api/participations/",
            {"campagne": campagne_a_paliers.id, "quantite": quantite},
            format="json",
        )

        assert reponse.status_code == 201, reponse.data
        assert reponse.data["prix_unitaire_applique"] == prix_attendu
        assert reponse.data["montant_total"] == total_attendu

    @pytest.mark.parametrize("quantite, prix_attendu, total_attendu", CAS_DU_PALIER)
    def test_le_paiement_consigne_le_montant_annonce_a_la_creation(
        self, connecte, campagne_a_paliers, ama, quantite, prix_attendu, total_attendu
    ):
        paiement = participer_et_payer(connecte, ama, campagne_a_paliers, quantite=quantite)

        assert paiement["participation"]["montant_total"] == total_attendu
        ligne = connecte(ama).get("/api/participations/").data["results"][0]
        assert ligne["prix_unitaire_applique"] == prix_attendu
        assert ligne["montant_total"] == total_attendu

    def test_le_prix_paye_reste_fige_quand_un_palier_est_franchi_apres(
        self, connecte, campagne_a_paliers, ama, yao
    ):
        """Le prix figé à la commande : un palier plus bas atteint ensuite ne réécrit rien."""
        participer_et_payer(connecte, ama, campagne_a_paliers, quantite=2)
        participer_et_payer(connecte, yao, campagne_a_paliers, quantite=12)

        ligne = connecte(ama).get("/api/participations/").data["results"][0]

        assert ligne["prix_unitaire_applique"] == 6500
        assert ligne["montant_total"] == 13000

    def test_une_campagne_sans_palier_facture_le_prix_unitaire(
        self, connecte, campagne, ama
    ):
        reponse = connecte(ama).post(
            "/api/participations/",
            {"campagne": campagne.id, "quantite": 5},
            format="json",
        )

        assert reponse.status_code == 201, reponse.data
        assert reponse.data["prix_unitaire_applique"] == 18000
        assert reponse.data["montant_total"] == 90000
