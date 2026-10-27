# -*- coding: utf-8 -*-
"""Séquestre et décaissement : la contrainte en base et le contrôle d'anomalies."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection, transaction

from groupachat.catalogue.models import Campagne
from groupachat.paiements.models import Decaissement, Sequestre

pytestmark = pytest.mark.django_db


@pytest.fixture
def sequestre(campagne) -> Sequestre:
    return Sequestre.objects.create(campagne=campagne, montant_consigne=180000)


def _controler() -> str:
    sortie = StringIO()
    call_command("controler_les_sequestres", stdout=sortie)
    return sortie.getvalue()


def _controler_en_echec() -> str:
    sortie = StringIO()
    with pytest.raises(CommandError):
        call_command("controler_les_sequestres", stdout=sortie)
    return sortie.getvalue()


def _decaissement(campagne, statut=Decaissement.Statut.DEMANDE) -> Decaissement:
    return Decaissement.objects.create(
        campagne=campagne, montant_brut=180000, frais=1500, montant_net=178500,
        numero_mobile_money="90001122", operateur="tmoney", statut=statut,
    )


# ── Contrainte C-006 ────────────────────────────────────────────────────────


class TestContrainte:
    def test_la_base_refuse_un_sequestre_qui_rend_plus_que_le_consigne(
        self, sequestre
    ):
        """Chaque montant reste sous le consigné : seule la somme déborde."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Sequestre.objects.filter(pk=sequestre.pk).update(
                    montant_libere=100000, montant_rembourse=100000
                )

    def test_la_base_accepte_un_sequestre_exactement_solde(self, sequestre):
        Sequestre.objects.filter(pk=sequestre.pk).update(
            montant_libere=100000, montant_rembourse=80000
        )
        sequestre.refresh_from_db()
        assert sequestre.solde == 0


# ── Commande de contrôle ────────────────────────────────────────────────────


class TestControleDesSequestres:
    def test_une_base_saine_ne_signale_aucune_anomalie(self, sequestre, campagne):
        sortie = _controler()
        assert "Aucune anomalie." in sortie

    def test_un_decaissement_en_attente_sur_une_campagne_annulee_est_signale(
        self, sequestre, campagne
    ):
        decaissement = _decaissement(campagne)
        Campagne.objects.filter(pk=campagne.pk).update(
            statut=Campagne.Statut.ANNULEE)

        sortie = _controler_en_echec()

        assert "Décaissements en attente sur une campagne non financée : 1" in sortie
        assert f"décaissement {decaissement.pk}" in sortie

    def test_une_campagne_decaissee_est_signalee(self, sequestre, campagne):
        Campagne.objects.filter(pk=campagne.pk).update(
            statut=Campagne.Statut.DECAISSEE)

        sortie = _controler_en_echec()

        assert "Campagnes au statut « decaissee » : 1" in sortie
        assert f"campagne {campagne.pk}" in sortie

    def test_une_campagne_distribuee_au_sequestre_non_solde_est_signalee(
        self, sequestre, campagne
    ):
        Campagne.objects.filter(pk=campagne.pk).update(
            statut=Campagne.Statut.DISTRIBUTION)

        sortie = _controler_en_echec()

        assert "n'est pas soldé : 1" in sortie
        assert "solde 180000" in sortie

    def test_une_campagne_distribuee_au_sequestre_solde_n_est_pas_signalee(
        self, sequestre, campagne
    ):
        Sequestre.objects.filter(pk=sequestre.pk).update(montant_libere=180000)
        Campagne.objects.filter(pk=campagne.pk).update(
            statut=Campagne.Statut.DISTRIBUTION)

        assert "Aucune anomalie." in _controler()

    @pytest.mark.skipif(
        connection.vendor != "postgresql",
        reason="l'éditeur de schéma de SQLite refuse de tourner dans un bloc atomique",
    )
    def test_un_sequestre_qui_rend_plus_que_le_consigne_est_signale(
        self, sequestre
    ):
        contrainte = next(
            c for c in Sequestre._meta.constraints
            if c.name == "sequestre_ne_sort_pas_plus_que_consigne"
        )
        # Les clés étrangères différées de la fixture laissent des événements
        # en attente, que PostgreSQL refuse de croiser avec un ALTER TABLE.
        with connection.cursor() as curseur:
            curseur.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with connection.schema_editor() as editeur:
            editeur.remove_constraint(Sequestre, contrainte)
        Sequestre.objects.filter(pk=sequestre.pk).update(
            montant_libere=100000, montant_rembourse=100000
        )

        sortie = _controler_en_echec()

        assert "Séquestres qui rendent plus que le consigné : 1" in sortie

    def test_la_commande_ne_modifie_rien(self, sequestre, campagne):
        _decaissement(campagne)
        Campagne.objects.filter(pk=campagne.pk).update(
            statut=Campagne.Statut.ANNULEE)
        avant = (
            list(Sequestre.objects.values()), list(Decaissement.objects.values()),
            Campagne.objects.get(pk=campagne.pk).statut,
        )

        _controler_en_echec()

        apres = (
            list(Sequestre.objects.values()), list(Decaissement.objects.values()),
            Campagne.objects.get(pk=campagne.pk).statut,
        )
        assert avant == apres
