# -*- coding: utf-8 -*-
"""C-064 : la tuile « Consigné en séquestre » du groupeur montre le détenu.

Le détenu est consigné − libéré − remboursé, comme sur le tableau de bord de
l'administration ; le cumul des parts payées ne baisse jamais, même après
un versement, et affichait donc plus que ce qui reste réellement consigné.
"""

from __future__ import annotations

import pytest

from groupachat.commandes.tests import participer_et_payer
from groupachat.paiements.models import Sequestre

pytestmark = pytest.mark.django_db

TABLEAU = "/api/groupeur/tableau-de-bord/"


class TestMontantDetenu:
    def test_le_tableau_de_bord_groupeur_affiche_le_detenu_et_non_le_cumul_des_parts(
        self, connecte, campagne, ama
    ):
        participer_et_payer(connecte, ama, campagne, quantite=10)
        sequestre = Sequestre.objects.get(campagne=campagne)
        Sequestre.objects.filter(pk=sequestre.pk).update(montant_libere=40000)

        collecte = connecte(campagne.groupeur).get(TABLEAU).data["collecte"]

        assert collecte["montant_detenu"] == sequestre.montant_consigne - 40000
        assert collecte["montant_consigne"] > collecte["montant_detenu"]

    def test_le_detenu_ignore_les_fonds_rembourses(self, connecte, campagne, ama):
        participer_et_payer(connecte, ama, campagne, quantite=10)
        sequestre = Sequestre.objects.get(campagne=campagne)
        Sequestre.objects.filter(pk=sequestre.pk).update(
            montant_rembourse=sequestre.montant_consigne
        )

        collecte = connecte(campagne.groupeur).get(TABLEAU).data["collecte"]

        assert collecte["montant_detenu"] == 0

    def test_le_detenu_est_nul_sans_campagne(self, connecte, groupeur):
        reponse = connecte(groupeur).get(TABLEAU)

        assert reponse.status_code == 200
        assert reponse.data["collecte"]["montant_detenu"] == 0

    def test_le_detenu_ne_compte_pas_les_campagnes_d_un_autre_groupeur(
        self, connecte, campagne, ama
    ):
        participer_et_payer(connecte, ama, campagne, quantite=10)
        # Un second groupeur validé, sans aucune campagne.
        from groupachat.comptes.models import DossierKYC, Utilisateur

        autre = Utilisateur.objects.create_user(
            "93009999", "mdpSolide2026", nom="Autre", prenom="Groupeur",
            telephone_verifie=True, role=Utilisateur.Role.GROUPEUR)
        DossierKYC.objects.create(
            utilisateur=autre, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-9", numero_mobile_money="93009999",
            nom_commerce="Autre", statut=DossierKYC.Statut.VALIDE)

        assert connecte(autre).get(TABLEAU).data["collecte"]["montant_detenu"] == 0
        assert connecte(campagne.groupeur).get(TABLEAU).data["collecte"]["montant_detenu"] > 0
