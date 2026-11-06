# -*- coding: utf-8 -*-
"""Qui remet le colis, et ce qu'il voit.

**C'est le livreur partenaire qui scanne — La Poste, Gozem — et lui seul.**
L'OAG confie le lot en bloc a l'agence et ne rencontre jamais ses acheteurs.
S'il validait lui-meme les retraits, celui qui doit livrer signerait sa
propre livraison, et le code ne prouverait plus rien.
"""

from __future__ import annotations

import pytest

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import Participation
from groupachat.comptes.models import Utilisateur
from groupachat.echanges.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cache_propre():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def livreur() -> Utilisateur:
    return Utilisateur.objects.create_user(
        "95551122", "mdpSolide2026", nom="Agbeko", prenom="Komlan",
        role=Utilisateur.Role.LIVREUR, telephone_verifie=True,
        transporteur=Utilisateur.Transporteur.POSTE,
    )


@pytest.fixture
def a_remettre(connecte, campagne, ama, yao, administrateur):
    """Une campagne en distribution : deux colis prets, deux destinations."""
    from groupachat.commandes.tests import participer_et_payer

    participer_et_payer(connecte, ama, campagne, quantite=6,
                        bureau_poste="Bureau de poste de Tokoin")
    participer_et_payer(connecte, yao, campagne, quantite=4,
                        mode_retrait="livraison",
                        adresse_livraison="Agoe, rue des Cocotiers")

    oag = connecte(campagne.groupeur)
    oag.post(f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json")
    oag.post(f"/api/groupeur/campagnes/{campagne.id}/demander-retrait/", {},
             format="json")
    admin = connecte(administrateur)
    from groupachat.paiements.models import Decaissement

    admin.post(
        f"/api/admin/decaissements/{Decaissement.objects.get().id}/executer/",
        {}, format="json",
    )
    connecte(campagne.groupeur).post(
        f"/api/groupeur/campagnes/{campagne.id}/mise-a-disposition/", {},
        format="json",
    )
    campagne.refresh_from_db()
    return campagne


def code_de(acheteur) -> str:
    return Participation.objects.get(acheteur=acheteur).code_retrait


class TestLeScanAppartientAuLivreur:
    def test_il_remet_le_colis(self, connecte, a_remettre, livreur, ama):
        reponse = connecte(livreur).post(
            "/api/livraison/retrait/", {"code": code_de(ama)}, format="json"
        )
        assert reponse.status_code == 200, reponse.data
        part = Participation.objects.get(acheteur=ama)
        assert part.statut == Participation.Statut.RETIREE
        assert part.remise_par == livreur

    def test_l_oag_ne_peut_plus_scanner(self, connecte, a_remettre, ama):
        """La route a disparu de son espace : il signerait sa propre livraison."""
        reponse = connecte(a_remettre.groupeur).post(
            f"/api/groupeur/campagnes/{a_remettre.id}/retrait/",
            {"code": code_de(ama)}, format="json",
        )
        assert reponse.status_code == 404

    def test_ni_l_acheteur_lui_meme(self, connecte, a_remettre, ama):
        """Sinon chacun declarerait avoir recu, ou n'avoir rien recu."""
        reponse = connecte(ama).post(
            "/api/livraison/retrait/", {"code": code_de(ama)}, format="json"
        )
        assert reponse.status_code == 403

    def test_ni_un_oag(self, connecte, a_remettre, ama):
        reponse = connecte(a_remettre.groupeur).post(
            "/api/livraison/retrait/", {"code": code_de(ama)}, format="json"
        )
        assert reponse.status_code == 403


class TestLeCodeSeSuffitALuiMeme:
    def test_pas_besoin_de_savoir_de_quel_groupage(
        self, connecte, a_remettre, livreur, yao
    ):
        """Le livreur a un paquet et un code, pas le nom du groupage."""
        reponse = connecte(livreur).post(
            "/api/livraison/retrait/", {"code": code_de(yao)}, format="json"
        )
        assert reponse.status_code == 200

    def test_le_qr_scanne_marche_aussi(self, connecte, a_remettre, livreur, ama):
        part = Participation.objects.get(acheteur=ama)
        reponse = connecte(livreur).post(
            "/api/livraison/retrait/", {"code": part.charge_qr}, format="json"
        )
        assert reponse.status_code == 200

    def test_un_code_inconnu_est_refuse(self, connecte, a_remettre, livreur):
        reponse = connecte(livreur).post(
            "/api/livraison/retrait/", {"code": "ZZZZ9999"}, format="json"
        )
        assert reponse.status_code == 400

    def test_un_code_ne_sert_qu_une_fois(self, connecte, a_remettre, livreur, ama):
        """Toute la valeur de la preuve de livraison tient dans cette ligne."""
        code = code_de(ama)
        assert connecte(livreur).post(
            "/api/livraison/retrait/", {"code": code}, format="json"
        ).status_code == 200
        seconde = connecte(livreur).post(
            "/api/livraison/retrait/", {"code": code}, format="json"
        )
        assert seconde.status_code == 400
        assert "déjà remis" in seconde.data["detail"]


class TestCeQueLeScanDeclenche:
    def test_l_oag_apprend_la_remise(self, connecte, a_remettre, livreur, ama):
        """Sans cette notification, il faudrait appeler l'agence pour savoir."""
        connecte(livreur).post(
            "/api/livraison/retrait/", {"code": code_de(ama)}, format="json"
        )
        avis = Notification.objects.filter(
            destinataire=a_remettre.groupeur,
            genre=Notification.Genre.RETRAIT_CONFIRME,
        ).first()
        assert avis is not None
        assert ama.nom_public in avis.message
        assert "La Poste" in avis.message

    def test_l_acheteur_sait_qui_lui_a_remis(
        self, connecte, a_remettre, livreur, ama
    ):
        connecte(livreur).post(
            "/api/livraison/retrait/", {"code": code_de(ama)}, format="json"
        )
        avis = Notification.objects.filter(
            destinataire=ama, genre=Notification.Genre.RETRAIT_CONFIRME
        ).first()
        assert avis is not None
        assert "La Poste" in avis.message

    def test_le_dernier_colis_termine_la_campagne(
        self, connecte, a_remettre, livreur, ama, yao
    ):
        api = connecte(livreur)
        api.post("/api/livraison/retrait/", {"code": code_de(ama)}, format="json")
        a_remettre.refresh_from_db()
        assert a_remettre.statut == Campagne.Statut.DISTRIBUTION

        api.post("/api/livraison/retrait/", {"code": code_de(yao)}, format="json")
        a_remettre.refresh_from_db()
        assert a_remettre.statut == Campagne.Statut.TERMINEE


class TestLaTournee:
    def test_elle_donne_l_adresse_et_le_numero(
        self, connecte, a_remettre, livreur
    ):
        """On ne livre pas un pseudonyme : il faut sonner et appeler."""
        tournee = connecte(livreur).get("/api/livraison/tournee/")
        assert tournee.status_code == 200
        assert len(tournee.data) == 2

        entier = str(tournee.data)
        assert "Cocotiers" in entier
        assert "Bureau de poste de Tokoin" in entier
        assert "91002233" in entier, "le numéro sert à prévenir de l'arrivée"

    def test_elle_ne_dit_rien_de_l_oag_ni_des_montants(
        self, connecte, a_remettre, livreur
    ):
        """Porter un colis n'a pas besoin de savoir qui l'a groupé, ni le prix."""
        entier = str(connecte(livreur).get("/api/livraison/tournee/").data)
        assert "Faya" not in entier
        assert "montant" not in entier
        assert a_remettre.groupeur.telephone not in entier

    def test_elle_se_filtre_par_mode(self, connecte, a_remettre, livreur):
        """Deposer au bureau et livrer a domicile ne sont pas la meme journee."""
        api = connecte(livreur)
        poste = api.get("/api/livraison/tournee/?mode=poste").data
        livraison = api.get("/api/livraison/tournee/?mode=livraison").data
        assert len(poste) == 1 and len(livraison) == 1
        assert poste[0]["mode_retrait"] == "poste"
        assert livraison[0]["mode_retrait"] == "livraison"

    def test_un_colis_remis_sort_de_la_tournee(
        self, connecte, a_remettre, livreur, ama
    ):
        api = connecte(livreur)
        api.post("/api/livraison/retrait/", {"code": code_de(ama)}, format="json")
        assert len(api.get("/api/livraison/tournee/").data) == 1

    def test_personne_d_autre_ne_voit_la_tournee(
        self, connecte, a_remettre, ama
    ):
        """Elle porte les adresses : c'est exactement ce qu'on ne montre pas."""
        assert connecte(ama).get("/api/livraison/tournee/").status_code == 403
        assert connecte(a_remettre.groupeur).get(
            "/api/livraison/tournee/"
        ).status_code == 403
