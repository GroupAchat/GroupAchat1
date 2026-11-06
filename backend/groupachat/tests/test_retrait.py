# -*- coding: utf-8 -*-
"""Comment le colis arrive chez l'acheteur.

**Le choix est à lui, pas à l'OAG.** Soit il passe au bureau de poste le plus
proche de chez lui, soit il se fait livrer et paie les frais à la remise. Un
point de remise unique, fixé par celui qui groupe, obligeait la moitié de la
ville à traverser Lomé pour un sac de riz.

Et les **frais de livraison ne passent jamais par la plateforme** : ils sont
fixés par l'agence et payés à la livraison. Les encaisser nous obligerait à
les reverser, donc à les connaître d'avance — alors qu'ils dépendent du
quartier et du poids du colis.
"""

from __future__ import annotations

import pytest

from groupachat.commandes.models import Participation

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cache_propre():
    """La limitation de débit compte à travers les tests ; on la remet à zéro."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def commander(api, campagne, **destination):
    return api.post(
        "/api/participations/",
        {"campagne": campagne.id, "quantite": 2, **destination},
        format="json",
    )


def payer(api, reponse):
    assert reponse.status_code == 201, reponse.data
    paiement = api.post(
        f"/api/participations/{reponse.data['id']}/payer/",
        {"operateur": "tmoney"},
        format="json",
    )
    assert paiement.status_code == 200, paiement.data
    return paiement.data


class TestLeChoixDeLAcheteur:
    def test_la_campagne_ne_porte_plus_de_lieu(self, client, campagne):
        """Aucun « Dépôt Agoè » nulle part : ce n'est plus à l'OAG de le dire."""
        fiche = client.get(f"/api/catalogue/campagnes/{campagne.id}/").data
        assert "point_remise" not in fiche

    def test_le_retrait_au_bureau_de_poste(self, connecte, campagne, ama):
        reponse = commander(
            connecte(ama), campagne, bureau_poste="Bureau de poste de Tokoin"
        )
        assert reponse.status_code == 201, reponse.data
        assert reponse.data["mode_retrait"] == "poste"
        assert "Tokoin" in reponse.data["destination"]

    def test_la_livraison_a_l_adresse(self, connecte, campagne, ama):
        reponse = commander(
            connecte(ama),
            campagne,
            mode_retrait="livraison",
            adresse_livraison="Agoe-Nyive, rue des Cocotiers",
        )
        assert reponse.status_code == 201, reponse.data
        assert reponse.data["mode_retrait"] == "livraison"
        assert "Cocotiers" in reponse.data["destination"]

    def test_une_part_sans_destination_est_refusee(self, connecte, campagne, ama):
        """Le colis est déjà parti quand on s'aperçoit qu'on ne sait pas où."""
        reponse = commander(connecte(ama), campagne)
        assert reponse.status_code == 400
        assert "bureau_poste" in reponse.data

    def test_la_livraison_sans_adresse_est_refusee(self, connecte, campagne, ama):
        reponse = commander(connecte(ama), campagne, mode_retrait="livraison")
        assert reponse.status_code == 400
        assert "adresse_livraison" in reponse.data

    def test_changer_de_mode_efface_l_autre_destination(
        self, connecte, campagne, ama
    ):
        """Une adresse laissée derrière un retrait au bureau ferait deux
        destinations pour un colis — et c'est l'agence qui trancherait."""
        reponse = commander(
            connecte(ama),
            campagne,
            mode_retrait="poste",
            bureau_poste="Bureau de poste de Be-Kpota",
            adresse_livraison="Nyekonakpoe, derriere la pharmacie",
        )
        assert reponse.status_code == 201, reponse.data
        part = Participation.objects.get(pk=reponse.data["id"])
        assert part.adresse_livraison == ""


class TestLOagNeVoitPasOuDortSonAcheteur:
    def test_il_voit_le_bureau_de_poste_mais_jamais_l_adresse(
        self, connecte, campagne, ama, yao
    ):
        """Un bureau de poste est un lieu public ; une adresse, un domicile.

        L'OAG ne connaît pas ses acheteurs — c'est toute la règle de la
        plateforme. Lui servir l'adresse de livraison la contournerait par la
        logistique.
        """
        # Les parts doivent etre **payees** : l'OAG ne voit que celles-la,
        # une commande impayee n'etant pas encore un colis a preparer.
        payer(connecte(ama), commander(
            connecte(ama), campagne, bureau_poste="Bureau de poste de Tokoin"
        ))
        payer(connecte(yao), commander(
            connecte(yao),
            campagne,
            mode_retrait="livraison",
            adresse_livraison="Agoe-Nyive, rue des Cocotiers",
        ))

        participants = connecte(campagne.groupeur).get(
            f"/api/groupeur/campagnes/{campagne.id}/participants/"
        )
        assert participants.status_code == 200, participants.data
        entier = str(participants.data)

        assert "Bureau de poste de Tokoin" in entier
        assert "Cocotiers" not in entier, "l'adresse ne sort pas"
        assert "Livraison par l'agence" in entier
