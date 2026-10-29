# -*- coding: utf-8 -*-
"""Le parcours complet : participer, payer, clôturer, décaisser, retirer."""

from __future__ import annotations

import pytest
from django.utils import timezone

from groupachat.catalogue.models import Campagne, PalierPrix
from groupachat.commandes.models import Avis, Participation
from groupachat.comptes.models import Reputation
from groupachat.echanges.models import Notification
from groupachat.paiements.models import Decaissement, Sequestre, Transaction

pytestmark = pytest.mark.django_db


def participer_et_payer(connecte, acheteur, campagne, quantite=5):
    api = connecte(acheteur)
    reponse = api.post(
        "/api/participations/",
        {"campagne": campagne.id, "quantite": quantite},
        format="json",
    )
    assert reponse.status_code == 201, reponse.data
    identifiant = reponse.data["id"]
    paiement = api.post(
        f"/api/participations/{identifiant}/payer/",
        {"operateur": "tmoney"},
        format="json",
    )
    assert paiement.status_code == 200, paiement.data
    return paiement.data


class TestParticipation:
    def test_un_numero_non_verifie_ne_peut_pas_participer(
        self, client, campagne, ama
    ):
        ama.telephone_verifie = False
        ama.save()
        client.force_authenticate(user=ama)
        reponse = client.post("/api/participations/",
                              {"campagne": campagne.id, "quantite": 1}, format="json")
        assert reponse.status_code == 403

    def test_le_groupeur_ne_participe_pas_a_sa_propre_campagne(
        self, connecte, campagne, groupeur
    ):
        reponse = connecte(groupeur).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        )
        assert reponse.status_code == 400

    def test_le_prix_est_celui_du_palier_atteint_avec_cette_part(
        self, connecte, campagne, ama
    ):
        PalierPrix.objects.create(campagne=campagne, quantite_min=5, prix_unitaire=16500)
        reponse = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 5},
            format="json",
        )
        assert reponse.data["prix_unitaire_applique"] == 16500
        assert reponse.data["montant_total"] == 82500

    def test_pas_de_code_avant_paiement(self, connecte, campagne, ama):
        reponse = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        )
        assert reponse.data["code_retrait"] is None
        assert reponse.data["charge_qr"] is None

    def test_une_collecte_close_refuse_les_nouvelles_parts(
        self, connecte, campagne, ama
    ):
        campagne.statut = Campagne.Statut.FINANCEE
        campagne.save()
        reponse = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        )
        assert reponse.status_code == 400

    def test_le_maximum_de_pieces_est_respecte(self, connecte, campagne, ama, yao):
        campagne.quantite_maximale = 6
        campagne.save()
        participer_et_payer(connecte, ama, campagne, quantite=5)
        reponse = connecte(yao).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 3},
            format="json",
        )
        assert reponse.status_code == 400
        assert "1 pièce" in str(reponse.data)


class TestPaiementSimule:
    def test_le_paiement_consigne_au_sequestre_et_delivre_le_code(
        self, connecte, campagne, ama
    ):
        donnees = participer_et_payer(connecte, ama, campagne, quantite=5)
        part = donnees["participation"]

        assert part["statut"] == "payee"
        assert len(part["code_retrait"]) == 8
        assert part["charge_qr"] == f"GA|{campagne.id}|{part['code_retrait']}"
        assert donnees["transaction"]["simulee"] is True
        assert donnees["transaction"]["reference"].startswith("SIM-")

        sequestre = Sequestre.objects.get(campagne=campagne)
        assert sequestre.montant_consigne == 90000
        assert sequestre.solde == 90000, "l'argent n'est pas allé au groupeur"

    def test_le_paiement_notifie_l_acheteur_et_le_groupeur(
        self, connecte, campagne, ama, groupeur
    ):
        participer_et_payer(connecte, ama, campagne, quantite=5)

        chez_ama = Notification.objects.filter(destinataire=ama)
        assert chez_ama.filter(genre=Notification.Genre.PAIEMENT_ENREGISTRE).exists()

        chez_groupeur = Notification.objects.filter(destinataire=groupeur)
        suivi = chez_groupeur.get(genre=Notification.Genre.PAIEMENT_RECU)
        assert "Ama Mensah a payé" in suivi.message, "le suivi est nominatif"

    def test_le_minimum_atteint_previent_le_groupeur(
        self, connecte, campagne, ama, groupeur
    ):
        participer_et_payer(connecte, ama, campagne, quantite=10)
        assert Notification.objects.filter(
            destinataire=groupeur, genre=Notification.Genre.MINIMUM_ATTEINT
        ).exists()

    def test_on_ne_paie_pas_deux_fois(self, connecte, campagne, ama):
        api = connecte(ama)
        identifiant = api.post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 2},
            format="json",
        ).data["id"]
        assert api.post(f"/api/participations/{identifiant}/payer/",
                        {}, format="json").status_code == 200
        rejeu = api.post(f"/api/participations/{identifiant}/payer/", {}, format="json")
        assert rejeu.status_code == 400

    def test_la_part_d_un_autre_est_introuvable(self, connecte, campagne, ama, yao):
        identifiant = connecte(ama).post(
            "/api/participations/", {"campagne": campagne.id, "quantite": 1},
            format="json",
        ).data["id"]
        assert connecte(yao).get(
            f"/api/participations/{identifiant}/"
        ).status_code == 404


class TestClotureReussie:
    def test_minimum_atteint_la_campagne_est_financee(
        self, connecte, campagne, ama, yao
    ):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)

        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.FINANCEE
        assert Sequestre.objects.get(campagne=campagne).statut == Sequestre.Statut.BLOQUE
        assert Notification.objects.filter(
            destinataire=ama, genre=Notification.Genre.CAMPAGNE_FINANCEE
        ).exists()


class TestClotureEchouee:
    """Minimum manqué : la collecte se ferme, **l'argent ne bouge pas**.

    Ce test affirmait l'inverse — remboursement immédiat à la clôture.
    C'était une erreur de conception : un groupeur peut vouloir maintenir
    la commande malgré le nombre, et rembourser d'office la lui retirerait.
    Le remboursement demande désormais une décision.
    """

    def test_la_cloture_laisse_l_argent_consigne(self, connecte, campagne, ama, yao):
        participer_et_payer(connecte, ama, campagne, quantite=3)
        participer_et_payer(connecte, yao, campagne, quantite=2)

        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.MINIMUM_NON_ATTEINT

        for acheteur in (ama, yao):
            part = Participation.objects.get(acheteur=acheteur)
            assert part.statut == Participation.Statut.PAYEE
            assert Notification.objects.filter(
                destinataire=acheteur,
                genre=Notification.Genre.GROUPAGE_NON_ABOUTI,
            ).exists()

        sequestre = Sequestre.objects.get(campagne=campagne)
        assert sequestre.solde == 90000, "rien ne doit sortir du séquestre"
        assert not Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).exists()

    def test_le_remboursement_suit_la_decision_du_groupeur(
        self, connecte, campagne, ama, yao
    ):
        participer_et_payer(connecte, ama, campagne, quantite=3)
        participer_et_payer(connecte, yao, campagne, quantite=2)

        api = connecte(campagne.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json")
        api.post(f"/api/groupeur/campagnes/{campagne.id}/annuler/", {}, format="json")

        campagne.refresh_from_db()
        assert campagne.statut == Campagne.Statut.ANNULEE

        for acheteur in (ama, yao):
            part = Participation.objects.get(acheteur=acheteur)
            assert part.statut == Participation.Statut.REMBOURSEE
            assert Notification.objects.filter(
                destinataire=acheteur, genre=Notification.Genre.REMBOURSEMENT
            ).exists()

        sequestre = Sequestre.objects.get(campagne=campagne)
        assert sequestre.montant_rembourse == 90000
        assert sequestre.solde == 0, "le séquestre doit être vidé"
        assert sequestre.statut == Sequestre.Statut.REMBOURSE
        assert Transaction.objects.filter(
            sens=Transaction.Sens.REMBOURSEMENT
        ).count() == 2


class TestDecaissement:
    @pytest.fixture
    def campagne_financee(self, connecte, campagne, ama, yao):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        campagne.refresh_from_db()
        return campagne

    def test_le_groupeur_retire_tout_moins_les_frais_fixes(
        self, connecte, campagne_financee
    ):
        reponse = connecte(campagne_financee.groupeur).post(
            f"/api/groupeur/campagnes/{campagne_financee.id}/demander-retrait/",
            {}, format="json",
        )
        assert reponse.status_code == 201, reponse.data
        assert reponse.data["montant_brut"] == 180000
        assert reponse.data["frais"] == 1500
        assert reponse.data["montant_net"] == 178500
        assert reponse.data["numero_mobile_money"] == "90001122"

    def test_un_seul_decaissement_par_campagne(self, connecte, campagne_financee):
        api = connecte(campagne_financee.groupeur)
        chemin = f"/api/groupeur/campagnes/{campagne_financee.id}/demander-retrait/"
        assert api.post(chemin, {}, format="json").status_code == 201
        assert api.post(chemin, {}, format="json").status_code == 400

    def test_l_administrateur_libere_les_fonds(
        self, connecte, campagne_financee, administrateur
    ):
        connecte(campagne_financee.groupeur).post(
            f"/api/groupeur/campagnes/{campagne_financee.id}/demander-retrait/",
            {}, format="json",
        )
        decaissement = Decaissement.objects.get()
        reponse = connecte(administrateur).post(
            f"/api/admin/decaissements/{decaissement.id}/executer/", {}, format="json"
        )
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["statut"] == "execute"

        sequestre = Sequestre.objects.get(campagne=campagne_financee)
        assert sequestre.montant_libere == 180000
        assert sequestre.solde == 0
        assert sequestre.statut == Sequestre.Statut.LIBERE
        campagne_financee.refresh_from_db()
        assert campagne_financee.statut == Campagne.Statut.APPROVISIONNEMENT
        assert Notification.objects.filter(
            destinataire=campagne_financee.groupeur, titre="Fonds versés",
            lien=f"/groupeur/campagnes/{campagne_financee.id}",
        ).count() == 1

    def test_une_campagne_non_financee_ne_se_decaisse_pas(self, connecte, campagne):
        reponse = connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/demander-retrait/", {},
            format="json",
        )
        assert reponse.status_code == 400


class TestDistributionEtRetrait:
    @pytest.fixture
    def campagne_a_distribuer(self, connecte, campagne, ama, yao, administrateur):
        participer_et_payer(connecte, ama, campagne, quantite=6)
        participer_et_payer(connecte, yao, campagne, quantite=4)
        api = connecte(campagne.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json")
        api.post(f"/api/groupeur/campagnes/{campagne.id}/demander-retrait/", {},
                 format="json")
        connecte(administrateur).post(
            f"/api/admin/decaissements/{Decaissement.objects.get().id}/executer/",
            {}, format="json",
        )
        campagne.refresh_from_db()
        return campagne

    def test_la_mise_a_disposition_notifie_tous_les_participants(
        self, connecte, campagne_a_distribuer, ama, yao
    ):
        reponse = connecte(campagne_a_distribuer.groupeur).post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
            {"point_remise": "Boutique Abalo, Bè-Kpota"}, format="json",
        )
        assert reponse.status_code == 200
        assert reponse.data["participants_notifies"] == 2

        for acheteur in (ama, yao):
            avis = Notification.objects.get(
                destinataire=acheteur,
                genre=Notification.Genre.MARCHANDISE_DISPONIBLE,
            )
            part = Participation.objects.get(acheteur=acheteur)
            assert "Bè-Kpota" in avis.message, "le point de remise est rappelé"
            assert part.code_retrait in avis.message, "le code est rappelé"
            assert part.statut == Participation.Statut.PRETE

    def test_le_retrait_au_code_dicte(self, connecte, campagne_a_distribuer, ama):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        code = Participation.objects.get(acheteur=ama).code_retrait

        reponse = api.post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/",
            {"code": code.lower()}, format="json",
        )
        assert reponse.status_code == 200, reponse.data
        assert reponse.data["acheteur"] == "Ama Mensah"

        part = Participation.objects.get(acheteur=ama)
        assert part.statut == Participation.Statut.RETIREE
        assert part.remise_par == campagne_a_distribuer.groupeur

    def test_le_retrait_au_qr_scanne(self, connecte, campagne_a_distribuer, ama):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        charge = Participation.objects.get(acheteur=ama).charge_qr

        reponse = api.post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/",
            {"code": charge}, format="json",
        )
        assert reponse.status_code == 200, reponse.data

    def test_un_qr_d_une_autre_campagne_est_refuse(
        self, connecte, campagne_a_distribuer, ama
    ):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        code = Participation.objects.get(acheteur=ama).code_retrait

        reponse = api.post(
            f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/",
            {"code": f"GA|999|{code}"}, format="json",
        )
        assert reponse.status_code == 400
        assert "ne concerne pas cette campagne" in reponse.data["detail"]

    def test_un_code_ne_sert_qu_une_fois(self, connecte, campagne_a_distribuer, ama):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        code = Participation.objects.get(acheteur=ama).code_retrait
        chemin = f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/"

        assert api.post(chemin, {"code": code}, format="json").status_code == 200
        rejeu = api.post(chemin, {"code": code}, format="json")
        assert rejeu.status_code == 400
        assert "déjà retiré" in rejeu.data["detail"]

    def test_le_dernier_colis_termine_la_campagne_et_compte_le_volume(
        self, connecte, campagne_a_distribuer, ama, yao
    ):
        api = connecte(campagne_a_distribuer.groupeur)
        api.post(f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/mise-a-disposition/",
                 {}, format="json")
        chemin = f"/api/groupeur/campagnes/{campagne_a_distribuer.id}/retrait/"

        api.post(chemin, {"code": Participation.objects.get(acheteur=ama).code_retrait},
                 format="json")
        campagne_a_distribuer.refresh_from_db()
        assert campagne_a_distribuer.statut == Campagne.Statut.DISTRIBUTION

        api.post(chemin, {"code": Participation.objects.get(acheteur=yao).code_retrait},
                 format="json")
        campagne_a_distribuer.refresh_from_db()
        assert campagne_a_distribuer.statut == Campagne.Statut.TERMINEE

        reputation = Reputation.objects.get(groupeur=campagne_a_distribuer.groupeur)
        assert reputation.campagnes_terminees == 1
        assert reputation.participants_servis == 2

        # Livrer ne donne **pas** d'étoiles : la note est la moyenne des avis
        # laissés par les acheteurs, et personne n'a encore noté. La plateforme
        # ne s'auto-décerne pas la satisfaction de ses utilisateurs.
        assert reputation.note == 0
        assert reputation.avis_recus == 0


class TestAvis:
    """La plateforme ne tranche pas : c'est la note qui sanctionne.

    Group Achat met en relation. Un souci sur un produit se règle entre
    l'acheteur et le groupeur — par la discussion publique et par l'avis.
    """

    def test_on_ne_note_pas_une_collecte_encore_ouverte(
        self, connecte, campagne, ama
    ):
        """Avant la clôture, il n'y a rien à juger."""
        part = participer_et_payer(connecte, ama, campagne, quantite=2)[
            "participation"
        ]
        reponse = connecte(ama).post(
            "/api/avis/", {"participation": part["id"], "note": 5}, format="json"
        )
        assert reponse.status_code == 400
        assert "collecte close" in str(reponse.data)

    def test_la_commande_dit_si_elle_est_notable_et_porte_son_avis(
        self, connecte, campagne, ama
    ):
        """C'est depuis sa commande que l'acheteur note : l'écran a besoin
        de savoir si le bouton a lieu d'être, et ce qui a déjà été écrit."""
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        avant = connecte(ama).get(f"/api/participations/{part['id']}/").data
        assert avant["peut_etre_notee"] is False
        assert avant["avis"] is None

        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        connecte(ama).post(
            "/api/avis/",
            {"participation": part["id"], "note": 3, "commentaire": "Correct."},
            format="json",
        )

        apres = connecte(ama).get(f"/api/participations/{part['id']}/").data
        assert apres["peut_etre_notee"] is True
        assert apres["avis"]["note"] == 3
        assert apres["avis"]["commentaire"] == "Correct."

    def test_l_acheteur_note_son_groupeur(self, connecte, campagne, ama):
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )

        reponse = connecte(ama).post(
            "/api/avis/",
            {"participation": part["id"], "note": 4, "commentaire": "Bien reçu."},
            format="json",
        )
        assert reponse.status_code == 201, reponse.data

        from groupachat.comptes.models import Reputation

        reputation = Reputation.objects.get(groupeur=campagne.groupeur)
        assert float(reputation.note) == 4.0
        assert reputation.avis_recus == 1

    def test_une_mauvaise_note_fait_baisser_la_reputation(
        self, connecte, campagne, ama, yao
    ):
        premiere = participer_et_payer(connecte, ama, campagne, quantite=6)[
            "participation"
        ]
        seconde = participer_et_payer(connecte, yao, campagne, quantite=4)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )

        connecte(ama).post(
            "/api/avis/", {"participation": premiere["id"], "note": 5}, format="json"
        )
        connecte(yao).post(
            "/api/avis/",
            {"participation": seconde["id"], "note": 1,
             "commentaire": "Jamais livré."},
            format="json",
        )

        from groupachat.comptes.models import Reputation

        reputation = Reputation.objects.get(groupeur=campagne.groupeur)
        assert float(reputation.note) == 3.0, "la moyenne doit tomber"

    def test_on_ne_note_qu_une_fois(self, connecte, campagne, ama):
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        charge = {"participation": part["id"], "note": 5}
        assert connecte(ama).post("/api/avis/", charge, format="json").status_code == 201
        assert connecte(ama).post("/api/avis/", charge, format="json").status_code == 400

    def test_on_ne_note_pas_la_commande_d_un_autre(
        self, connecte, campagne, ama, yao
    ):
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        reponse = connecte(yao).post(
            "/api/avis/", {"participation": part["id"], "note": 1}, format="json"
        )
        assert reponse.status_code == 400

    def test_les_avis_se_lisent_sans_compte(self, client, connecte, campagne, ama):
        """Un avis qu'on ne peut pas lire avant d'acheter ne sert à rien."""
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        connecte(ama).post(
            "/api/avis/",
            {"participation": part["id"], "note": 3, "commentaire": "Correct."},
            format="json",
        )

        client.force_authenticate(user=None)
        reponse = client.get(f"/api/avis/?campagne={campagne.id}")
        assert reponse.status_code == 200
        assert reponse.data["count"] == 1
        # Le numéro de l'acheteur n'a rien à faire dans un avis public.
        assert "telephone" not in str(reponse.data["results"][0])

    def test_le_groupeur_a_un_droit_de_reponse(self, connecte, campagne, ama):
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        avis = connecte(ama).post(
            "/api/avis/",
            {"participation": part["id"], "note": 2, "commentaire": "Déçu."},
            format="json",
        ).data

        reponse = connecte(campagne.groupeur).post(
            f"/api/avis/{avis['id']}/repondre/",
            {"reponse": "Désolé, je vous échange l'article."},
            format="json",
        )
        assert reponse.status_code == 200
        assert "échange" in reponse.data["reponse"]

    def test_un_autre_groupeur_ne_repond_pas_a_sa_place(
        self, connecte, campagne, ama, yao
    ):
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        avis = connecte(ama).post(
            "/api/avis/", {"participation": part["id"], "note": 2}, format="json"
        ).data

        assert connecte(yao).post(
            f"/api/avis/{avis['id']}/repondre/", {"reponse": "Pas moi"}, format="json"
        ).status_code == 403


class TestAccesEspaceGroupeur:
    def test_un_dossier_en_attente_ferme_l_espace(self, connecte, groupeur_en_attente):
        api = connecte(groupeur_en_attente)
        assert api.get("/api/groupeur/campagnes/").status_code == 403
        assert api.get("/api/groupeur/tableau-de-bord/").status_code == 403

    def test_mais_l_etat_du_dossier_reste_consultable(
        self, connecte, groupeur_en_attente
    ):
        reponse = connecte(groupeur_en_attente).get("/api/groupeur/etat/")
        assert reponse.status_code == 200
        assert reponse.data["acces"] is False
        assert reponse.data["raison"] == "en_attente"

    def test_un_acheteur_n_entre_pas_dans_l_espace_groupeur(self, connecte, ama):
        assert connecte(ama).get("/api/groupeur/campagnes/").status_code == 403

    def test_l_espace_s_ouvre_une_fois_le_dossier_valide(self, connecte, groupeur):
        assert connecte(groupeur).get("/api/groupeur/campagnes/").status_code == 200


class TestCampagneFigee:
    def test_une_campagne_deja_payee_ne_se_modifie_plus(
        self, connecte, campagne, ama
    ):
        participer_et_payer(connecte, ama, campagne, quantite=2)
        reponse = connecte(campagne.groupeur).patch(
            f"/api/groupeur/campagnes/{campagne.id}/",
            {"prix_unitaire": 25000}, format="json",
        )
        assert reponse.status_code == 409
        campagne.refresh_from_db()
        assert campagne.prix_unitaire == 18000


class TestAvisProteges:
    """D-F010 : seul l'auteur modifie ou supprime son avis ; F-021 : la
    réputation ne bouge donc que par la main de l'auteur."""

    @pytest.fixture
    def avis_d_ama(self, connecte, campagne, ama):
        part = participer_et_payer(connecte, ama, campagne, quantite=10)[
            "participation"
        ]
        connecte(campagne.groupeur).post(
            f"/api/groupeur/campagnes/{campagne.id}/cloturer/", {}, format="json"
        )
        reponse = connecte(ama).post(
            "/api/avis/",
            {"participation": part["id"], "note": 4, "commentaire": "Bien."},
            format="json",
        )
        assert reponse.status_code == 201, reponse.data
        return Avis.objects.get(id=reponse.data["id"])

    @staticmethod
    def _rien_n_a_bouge(avis, campagne):
        avis.refresh_from_db()
        assert avis.note == 4
        assert avis.modifie_le is None
        assert Avis.objects.count() == 1
        reputation = Reputation.objects.get(groupeur=campagne.groupeur)
        assert float(reputation.note) == 4.0
        assert reputation.avis_recus == 1

    def test_l_auteur_modifie_son_avis_et_la_reputation_suit(
        self, connecte, campagne, ama, avis_d_ama
    ):
        reponse = connecte(ama).patch(
            f"/api/avis/{avis_d_ama.id}/",
            {"note": 2, "commentaire": "Finalement décevant"},
            format="json",
        )
        assert reponse.status_code == 200, reponse.data
        avis_d_ama.refresh_from_db()
        assert avis_d_ama.note == 2
        assert avis_d_ama.modifie_le is not None
        reputation = Reputation.objects.get(groupeur=campagne.groupeur)
        assert float(reputation.note) == 2.0
        assert reputation.avis_recus == 1

    def test_l_auteur_supprime_son_avis_et_la_reputation_retombe(
        self, connecte, campagne, ama, avis_d_ama
    ):
        api = connecte(ama)
        assert api.delete(f"/api/avis/{avis_d_ama.id}/").status_code == 204
        assert Avis.objects.count() == 0
        reputation = Reputation.objects.get(groupeur=campagne.groupeur)
        assert float(reputation.note) == 0
        assert reputation.avis_recus == 0
        assert api.get(f"/api/avis/{avis_d_ama.id}/").status_code == 404

    def test_un_autre_acheteur_ne_modifie_ni_ne_supprime_un_avis(
        self, connecte, campagne, yao, avis_d_ama
    ):
        api = connecte(yao)
        assert api.patch(
            f"/api/avis/{avis_d_ama.id}/", {"note": 1}, format="json"
        ).status_code == 403
        assert api.put(
            f"/api/avis/{avis_d_ama.id}/",
            {"participation": avis_d_ama.participation_id, "note": 1},
            format="json",
        ).status_code == 403
        assert api.delete(f"/api/avis/{avis_d_ama.id}/").status_code == 403
        self._rien_n_a_bouge(avis_d_ama, campagne)

    def test_le_groupeur_vise_ne_modifie_ni_ne_supprime_l_avis_qui_le_concerne(
        self, connecte, campagne, avis_d_ama
    ):
        api = connecte(campagne.groupeur)
        assert api.patch(
            f"/api/avis/{avis_d_ama.id}/", {"note": 5}, format="json"
        ).status_code == 403
        assert api.delete(f"/api/avis/{avis_d_ama.id}/").status_code == 403
        self._rien_n_a_bouge(avis_d_ama, campagne)

    def test_sans_session_on_ne_touche_pas_a_un_avis(
        self, client, campagne, avis_d_ama
    ):
        client.force_authenticate(user=None)
        assert client.patch(
            f"/api/avis/{avis_d_ama.id}/", {"note": 1}, format="json"
        ).status_code in (401, 403)
        assert client.delete(f"/api/avis/{avis_d_ama.id}/").status_code in (401, 403)
        self._rien_n_a_bouge(avis_d_ama, campagne)

    def test_un_numero_non_verifie_ne_supprime_pas_un_avis(
        self, connecte, campagne, yao, avis_d_ama
    ):
        yao.telephone_verifie = False
        yao.save()
        assert connecte(yao).delete(f"/api/avis/{avis_d_ama.id}/").status_code == 403
        self._rien_n_a_bouge(avis_d_ama, campagne)

    def test_le_groupeur_garde_son_droit_de_reponse(
        self, connecte, campagne, avis_d_ama
    ):
        reponse = connecte(campagne.groupeur).post(
            f"/api/avis/{avis_d_ama.id}/repondre/", {"reponse": "Merci"},
            format="json",
        )
        assert reponse.status_code == 200, reponse.data
        avis_d_ama.refresh_from_db()
        assert avis_d_ama.reponse == "Merci"
        assert avis_d_ama.repondu_le is not None
        assert avis_d_ama.note == 4
        reputation = Reputation.objects.get(groupeur=campagne.groupeur)
        assert float(reputation.note) == 4.0

    def test_un_tiers_ne_repond_pas_a_la_place_du_groupeur(
        self, connecte, yao, avis_d_ama
    ):
        reponse = connecte(yao).post(
            f"/api/avis/{avis_d_ama.id}/repondre/", {"reponse": "Faux"},
            format="json",
        )
        assert reponse.status_code == 403
        avis_d_ama.refresh_from_db()
        assert avis_d_ama.reponse == ""

    def test_une_seconde_reponse_est_refusee_et_la_premiere_reste(
        self, connecte, campagne, avis_d_ama
    ):
        """C-065 : la seconde réponse écrasait la première (200)."""
        api = connecte(campagne.groupeur)
        adresse = f"/api/avis/{avis_d_ama.id}/repondre/"
        assert api.post(adresse, {"reponse": "Merci"}, format="json").status_code == 200
        avis_d_ama.refresh_from_db()
        date_premiere = avis_d_ama.repondu_le

        reponse = api.post(adresse, {"reponse": "Autre"}, format="json")

        assert reponse.status_code == 400
        assert reponse.data == {"reponse": ["Vous avez déjà répondu à cet avis."]}
        avis_d_ama.refresh_from_db()
        assert avis_d_ama.reponse == "Merci"
        assert avis_d_ama.repondu_le == date_premiere

    def test_une_reponse_vide_est_refusee_sans_rien_ecrire(
        self, connecte, campagne, avis_d_ama
    ):
        reponse = connecte(campagne.groupeur).post(
            f"/api/avis/{avis_d_ama.id}/repondre/", {"reponse": ""}, format="json"
        )
        assert reponse.status_code == 400
        avis_d_ama.refresh_from_db()
        assert avis_d_ama.reponse == ""
        assert avis_d_ama.repondu_le is None

    def test_un_visiteur_ne_repond_pas_a_un_avis(self, client, avis_d_ama):
        reponse = client.post(
            f"/api/avis/{avis_d_ama.id}/repondre/", {"reponse": "Hop"}, format="json"
        )
        assert reponse.status_code in (401, 403)
        avis_d_ama.refresh_from_db()
        assert avis_d_ama.reponse == ""

    def test_on_ne_deplace_pas_un_avis_vers_une_autre_commande(
        self, connecte, campagne, ama, avis_d_ama
    ):
        seconde = Participation.objects.create(
            acheteur=ama, campagne=campagne, quantite=1,
            prix_unitaire_applique=18000, montant_total=18000,
            statut=Participation.Statut.PAYEE,
        )
        connecte(ama).patch(
            f"/api/avis/{avis_d_ama.id}/",
            {"participation": seconde.id, "note": 3},
            format="json",
        )
        avis_d_ama.refresh_from_db()
        assert avis_d_ama.participation_id != seconde.id
        assert not Avis.objects.filter(participation=seconde).exists()

    def test_la_note_hors_bornes_est_refusee_a_la_modification(
        self, connecte, campagne, ama, avis_d_ama
    ):
        api = connecte(ama)
        for note in (0, 6):
            reponse = api.patch(
                f"/api/avis/{avis_d_ama.id}/", {"note": note}, format="json"
            )
            assert reponse.status_code == 400
        self._rien_n_a_bouge(avis_d_ama, campagne)

    def test_avis_inexistant_donne_404(self, connecte, ama):
        api = connecte(ama)
        assert api.patch("/api/avis/999999/", {"note": 3}, format="json").status_code == 404
        assert api.delete("/api/avis/999999/").status_code == 404
