# -*- coding: utf-8 -*-
"""Fixtures partagées par toute la suite."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from groupachat.catalogue.models import Campagne, Categorie, Produit
from groupachat.comptes.models import DossierKYC, Reputation, Utilisateur


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def categorie() -> Categorie:
    return Categorie.objects.create(nom="Alimentation", icone="panier")


def _compte(telephone, prenom, nom="Test", **extra) -> Utilisateur:
    return Utilisateur.objects.create_user(
        telephone, "mdpSolide2026", nom=nom, prenom=prenom,
        telephone_verifie=True, **extra
    )


@pytest.fixture
def groupeur() -> Utilisateur:
    """Un groupeur dont le dossier est validé : l'espace lui est ouvert."""
    compte = _compte("90001122", "Koffi", "Abalo", role=Utilisateur.Role.GROUPEUR)
    DossierKYC.objects.create(
        utilisateur=compte, type_piece=DossierKYC.TypePiece.CNI,
        numero_piece="CNI-1", numero_mobile_money="90001122",
        nom_commerce="Abalo Import", statut=DossierKYC.Statut.VALIDE,
    )
    Reputation.objects.create(groupeur=compte)
    return compte


@pytest.fixture
def groupeur_en_attente() -> Utilisateur:
    """Un groupeur dont le dossier n'est pas tranché : porte fermée."""
    compte = _compte("90009988", "Afi", "Doe", role=Utilisateur.Role.GROUPEUR)
    DossierKYC.objects.create(
        utilisateur=compte, type_piece=DossierKYC.TypePiece.CNI,
        numero_piece="CNI-2", numero_mobile_money="90009988",
    )
    return compte


@pytest.fixture
def ama() -> Utilisateur:
    return _compte("91002233", "Ama", "Mensah")


@pytest.fixture
def yao() -> Utilisateur:
    return _compte("92003344", "Yao", "Dossou")


@pytest.fixture
def administrateur() -> Utilisateur:
    return Utilisateur.objects.create_superuser(
        "99000011", "mdpSolide2026", nom="Équipe", prenom="Group Achat"
    )


@pytest.fixture
def produit(categorie) -> Produit:
    return Produit.objects.create(
        categorie=categorie, nom="Sac de riz 25 kg", marque="Délice",
        description="Riz parfumé importé.",
    )


@pytest.fixture
def campagne(groupeur, produit) -> Campagne:
    """Une campagne publiée : 10 pièces minimum à 18 000 FCFA."""
    return Campagne.objects.create(
        produit=produit, groupeur=groupeur, titre="Riz Délice — arrivage de novembre",
        prix_unitaire=18000, quantite_minimale=10,
        date_limite=timezone.now() + timedelta(days=10),
        point_remise="Marché d'Adawlato, Lomé",
        statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now(),
    )


@pytest.fixture
def connecte(client):
    """Ouvre une session pour le compte donné."""

    def _connecter(utilisateur) -> APIClient:
        client.force_authenticate(user=utilisateur)
        return client

    return _connecter
