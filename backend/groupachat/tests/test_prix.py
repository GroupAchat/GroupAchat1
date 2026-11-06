# -*- coding: utf-8 -*-
"""Le barème à deux axes, et la chute qui profite à ceux qui ont déjà payé.

La règle que ces tests protègent : **une baisse de prix obtenue grâce au
nombre revient à tout le monde**, y compris à celui qui a commandé le
premier. Sans cela, partager la campagne punirait celui qui la partage, et
le mécanisme n'aurait aucun sens.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from groupachat.catalogue.models import Campagne, PalierPrix
from groupachat.commandes.models import Participation
from groupachat.commandes.tests import participer_et_payer

pytestmark = pytest.mark.django_db


class TestChuteRetroactive:
    """La baisse profite aussi à ceux qui ont déjà payé.

    C'est tout l'intérêt du mécanisme : si la chute ne concernait que les
    derniers arrivés, celui qui a commandé le premier serait puni d'avoir
    fait venir du monde — exactement celui qu'on veut récompenser.
    """

    @pytest.fixture
    def campagne_a_chute(self, groupeur, produit):
        campagne = Campagne.objects.create(
            produit=produit, groupeur=groupeur, titre="Chute à deux participants",
            prix_unitaire=25000, quantite_minimale=2,
            date_limite=timezone.now() + timedelta(days=5),
            statut=Campagne.Statut.EN_COURS,
            publiee_le=timezone.now(),
        )
        PalierPrix.objects.create(
            campagne=campagne, quantite_min=1, participants_min=2,
            prix_unitaire=23000,
        )
        return campagne

    def test_le_premier_arrive_est_remboursé_de_la_difference(
        self, connecte, campagne_a_chute, ama, yao
    ):
        from groupachat.paiements.services import cloturer

        premiere = participer_et_payer(connecte, ama, campagne_a_chute, quantite=1)[
            "participation"
        ]
        assert premiere["prix_unitaire_applique"] == 25000

        participer_et_payer(connecte, yao, campagne_a_chute, quantite=1)
        cloturer(campagne_a_chute)

        part = Participation.objects.get(id=premiere["id"])
        assert part.prix_unitaire_applique == 23000
        assert part.montant_total == 23000
        # La part reste payée : seule la différence repart.
        assert part.statut in Participation.STATUTS_PAYES

    def test_le_sequestre_sait_que_l_argent_est_reparti(
        self, connecte, campagne_a_chute, ama, yao
    ):
        """Sans quoi le groupeur se verrait décaisser un argent qui n'est
        plus à lui."""
        from groupachat.paiements.models import Sequestre
        from groupachat.paiements.services import cloturer

        participer_et_payer(connecte, ama, campagne_a_chute, quantite=1)
        participer_et_payer(connecte, yao, campagne_a_chute, quantite=1)
        cloturer(campagne_a_chute)

        sequestre = Sequestre.objects.get(campagne=campagne_a_chute)
        assert sequestre.montant_consigne == 50000
        assert sequestre.montant_rembourse == 4000
        assert sequestre.solde == 46000

    def test_le_prix_ne_remonte_jamais(self, connecte, campagne, ama):
        """Une tranche choisie à la commande est acquise, même si le barème
        change ensuite : personne ne se voit réclamer un complément."""
        from groupachat.paiements.services import ajuster_les_prix

        part = participer_et_payer(connecte, ama, campagne, quantite=2)[
            "participation"
        ]
        campagne.prix_unitaire = 99000
        campagne.save(update_fields=["prix_unitaire"])

        assert ajuster_les_prix(campagne) == 0
        inchangee = Participation.objects.get(id=part["id"])
        assert inchangee.prix_unitaire_applique == part["prix_unitaire_applique"]


class TestCommandeAuBareme:
    """Ce que l'acheteur paie réellement en passant commande."""

    @pytest.fixture
    def bareme(self, campagne):
        campagne.prix_unitaire = 25000
        campagne.save(update_fields=["prix_unitaire"])
        PalierPrix.objects.create(
            campagne=campagne, quantite_min=12, participants_min=0,
            prix_unitaire=22000,
        )
        return campagne

    def test_la_commande_applique_la_tranche_de_l_acheteur(
        self, connecte, bareme, ama
    ):
        reponse = connecte(ama).post(
            "/api/participations/", {"campagne": bareme.id, "quantite": 12, "bureau_poste": "Bureau de poste de Tokoin"},
            format="json",
        )
        assert reponse.status_code == 201, reponse.data
        assert reponse.data["prix_unitaire_applique"] == 22000
        assert reponse.data["montant_total"] == 22000 * 12
