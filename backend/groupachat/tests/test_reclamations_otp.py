# -*- coding: utf-8 -*-
"""Tests des réclamations et de la validation par code OTP SMS."""

from __future__ import annotations

import pytest
from rest_framework import status

from groupachat.commandes.models import Participation, Reclamation
from groupachat.paiements.services import encaisser, remettre_le_colis

pytestmark = pytest.mark.django_db


def test_code_otp_sms_genere_au_paiement(campagne, ama):
    """Un code OTP SMS est généré dès que la participation est payée."""
    part = Participation.objects.create(
        campagne=campagne,
        acheteur=ama,
        quantite=1,
        prix_unitaire_applique=18000,
        montant_total=18000,
        bureau_poste="Bureau de poste de Tokoin",
        mode_retrait=Participation.ModeRetrait.POSTE,
    )
    assert not part.code_otp_sms
    encaisser(part, "tmoney", ama.telephone)
    part.refresh_from_db()
    assert part.code_retrait
    assert part.code_otp_sms
    assert len(part.code_otp_sms) == 6


def test_remise_avec_code_otp_sms(campagne, ama, groupeur):
    """La remise fonctionne avec le code OTP SMS reçu par l'acheteur."""
    part = Participation.objects.create(
        campagne=campagne,
        acheteur=ama,
        quantite=1,
        prix_unitaire_applique=18000,
        montant_total=18000,
        bureau_poste="Bureau de poste de Tokoin",
        mode_retrait=Participation.ModeRetrait.POSTE,
    )
    encaisser(part, "tmoney", ama.telephone)
    part.refresh_from_db()
    part.statut = Participation.Statut.PRETE
    part.save(update_fields=["statut"])

    # Remise avec le code OTP SMS de secours
    remise = remettre_le_colis(part.code_otp_sms, groupeur)
    assert remise.id == part.id
    assert remise.statut == Participation.Statut.RETIREE


def test_parcours_reclamation_5_etapes(connecte, campagne, ama, groupeur):
    """Ouverture d'une réclamation en 5 étapes."""
    part = Participation.objects.create(
        campagne=campagne,
        acheteur=ama,
        quantite=1,
        prix_unitaire_applique=18000,
        montant_total=18000,
        bureau_poste="Bureau de poste de Tokoin",
        mode_retrait=Participation.ModeRetrait.POSTE,
    )
    encaisser(part, "tmoney", ama.telephone)
    part.refresh_from_db()

    api_ama = connecte(ama)
    rep = api_ama.post(
        "/api/reclamations/",
        {
            "participation": part.id,
            "motif": Reclamation.Motif.NON_CONFORME,
            "description": "Le sac de riz ne correspond pas à la marque commandée.",
        },
        format="json",
    )
    assert rep.status_code == status.HTTP_201_CREATED
    rec_id = rep.data["id"]
    assert rep.data["numero_dossier"].startswith("REC-")
    assert rep.data["etape"] == Reclamation.Etape.ACCUSE_RECEPTION

    # L'OAG répond (phase contradictoire)
    api_oag = connecte(groupeur)
    rep_oag = api_oag.post(
        f"/api/reclamations/{rec_id}/repondre_oag/",
        {"reponse_oag": "Nous avons vérifié le lot avec le grossiste, échange proposé."},
        format="json",
    )
    assert rep_oag.status_code == status.HTTP_200_OK
    assert rep_oag.data["etape"] == Reclamation.Etape.ANALYSE
