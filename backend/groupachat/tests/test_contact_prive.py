# -*- coding: utf-8 -*-
"""Le Contact Privé : le seul pont entre un acheteur et un OAG.

Trois règles portent ce module.

**Il n'existe aucune discussion publique.** Un fil ouvert sous une campagne
laissait convenir d'un arrangement direct à la vue de tous, et hors de la
plateforme ni le séquestre ni l'assurance ne jouent.

**L'abonnement ne coûte aucun point ; il en rapporte.** Les points sont une
récompense, pas un péage. En faire une condition d'accès fermerait la porte à
ceux qui n'ont encore rien acheté — exactement ceux qu'on veut rassurer.

**L'identité de l'OAG ne sort que pour un abonné en cours**, et seulement
dans ce sens : l'OAG ne paie pas pour connaître ses clients.
"""

from __future__ import annotations

import json

import pytest
from django.utils import timezone

from groupachat.comptes import points
from groupachat.echanges.contact_prive import (
    PRIX_MENSUEL_FCFA,
    AbonnementContactPrive,
    Conversation,
)

pytestmark = pytest.mark.django_db


def abonner(api) -> dict:
    reponse = api.post("/api/contact-prive/souscrire/", {}, format="json")
    assert reponse.status_code == 201, reponse.data
    return reponse.data


def ecrire(api, groupeur, texte="Bonjour, le riz est-il parfumé ?", campagne=None):
    corps = {"groupeur": groupeur.id, "texte": texte}
    if campagne is not None:
        corps["campagne"] = campagne.id
    return api.post("/api/conversations/ouvrir/", corps, format="json")


class TestLeFilPublicAEteRetire:
    def test_la_route_des_commentaires_n_existe_plus(self, client, campagne):
        reponse = client.get(f"/api/campagnes/{campagne.id}/commentaires/")
        assert reponse.status_code == 404

    def test_la_fiche_ne_porte_plus_de_compteur_de_commentaires(
        self, client, campagne
    ):
        fiche = client.get(f"/api/catalogue/campagnes/{campagne.id}/").data
        assert "nombre_commentaires" not in fiche


class TestLAbonnement:
    def test_il_coute_deux_mille_francs(self, connecte, ama):
        donnees = abonner(connecte(ama))
        assert donnees["abonnement"]["montant"] == PRIX_MENSUEL_FCFA == 2000

    def test_il_ne_coute_aucun_point_et_en_rapporte(self, connecte, ama):
        """Un acheteur sans le moindre point doit pouvoir s'abonner."""
        assert points.compteur_de(ama).solde == 0

        abonner(connecte(ama))

        compteur = points.compteur_de(ama)
        assert compteur.solde == 10
        assert compteur.cumules == 10

    def test_renouveler_tot_ne_fait_pas_perdre_les_jours_restants(
        self, connecte, ama
    ):
        premier = abonner(connecte(ama))["abonnement"]
        second = abonner(connecte(ama))["abonnement"]
        assert second["debute_le"] == premier["expire_le"]

    def test_l_etat_dit_ce_qu_il_faut_pour_decider(self, connecte, ama):
        avant = connecte(ama).get("/api/contact-prive/").data
        assert avant["actif"] is False
        assert avant["prix"] == 2000
        assert avant["points_par_mois"] == 10

        abonner(connecte(ama))
        apres = connecte(ama).get("/api/contact-prive/").data
        assert apres["actif"] is True


class TestEcrireAUnOAG:
    def test_sans_abonnement_c_est_refuse_et_le_prix_est_dit(
        self, connecte, groupeur, ama
    ):
        reponse = ecrire(connecte(ama), groupeur)
        assert reponse.status_code == 402
        assert reponse.data["abonnement_requis"] is True
        assert reponse.data["prix"] == 2000

    def test_avec_abonnement_le_fil_s_ouvre(self, connecte, groupeur, campagne, ama):
        api = connecte(ama)
        abonner(api)

        reponse = ecrire(api, groupeur, campagne=campagne)
        assert reponse.status_code == 201
        assert Conversation.objects.count() == 1

    def test_un_seul_fil_par_paire_quelle_que_soit_la_campagne(
        self, connecte, groupeur, campagne, ama
    ):
        """L'acheteur parle à quelqu'un, pas à une annonce."""
        api = connecte(ama)
        abonner(api)
        ecrire(api, groupeur, campagne=campagne)
        ecrire(api, groupeur, texte="Et pour le prochain arrivage ?")

        assert Conversation.objects.count() == 1
        fil = Conversation.objects.get()
        assert fil.messages.count() == 2

    def test_l_oag_repond_sans_payer(self, connecte, groupeur, ama):
        api = connecte(ama)
        abonner(api)
        fil = ecrire(api, groupeur).data

        reponse = connecte(groupeur).post(
            f"/api/conversations/{fil['id']}/repondre/",
            {"texte": "Oui, riz jasmin."},
            format="json",
        )
        assert reponse.status_code == 201, reponse.data

    def test_on_ne_s_ecrit_pas_a_soi_meme(self, connecte, groupeur):
        api = connecte(groupeur)
        abonner(api)
        assert ecrire(api, groupeur).status_code == 400


class TestLIdentiteNeSortQuePourUnAbonne:
    def test_l_abonne_voit_qui_est_son_vendeur(self, connecte, groupeur, ama):
        groupeur.nom_utilisateur = "Faya-02"
        groupeur.save()
        api = connecte(ama)
        abonner(api)
        ecrire(api, groupeur)

        fils = api.get("/api/conversations/").data
        interlocuteur = fils[0]["interlocuteur"]
        assert interlocuteur["nom_utilisateur"] == "Faya-02"
        assert interlocuteur["nom_complet"] == "Koffi Abalo"
        assert interlocuteur["telephone"] == "90001122"

    def test_l_abonnement_expire_referme_l_identite(self, connecte, groupeur, ama):
        api = connecte(ama)
        abonner(api)
        ecrire(api, groupeur)

        AbonnementContactPrive.objects.update(
            expire_le=timezone.now() - timezone.timedelta(days=1)
        )

        interlocuteur = api.get("/api/conversations/").data[0]["interlocuteur"]
        assert interlocuteur["nom_complet"] is None
        assert interlocuteur["telephone"] is None

    def test_l_oag_ne_connait_pas_son_acheteur(self, connecte, groupeur, ama):
        """Il ne paie pas pour ça, et il n'a pas à le savoir."""
        api = connecte(ama)
        abonner(api)
        ecrire(api, groupeur)

        fils = connecte(groupeur).get("/api/conversations/")
        texte = json.dumps(fils.data, ensure_ascii=False, default=str)
        assert "Mensah" not in texte
        assert "91002233" not in texte


class TestHistoriqueEtModeration:
    def test_l_historique_reste_lisible_apres_expiration(
        self, connecte, groupeur, ama
    ):
        """Ce sont ses échanges : les retirer effacerait la preuve du convenu."""
        api = connecte(ama)
        abonner(api)
        fil = ecrire(api, groupeur).data
        AbonnementContactPrive.objects.update(
            expire_le=timezone.now() - timezone.timedelta(days=1)
        )

        reponse = api.get(f"/api/conversations/{fil['id']}/messages/")
        assert reponse.status_code == 200
        assert len(reponse.data["messages"]) == 1

    def test_mais_il_ne_peut_plus_ecrire(self, connecte, groupeur, ama):
        api = connecte(ama)
        abonner(api)
        fil = ecrire(api, groupeur).data
        AbonnementContactPrive.objects.update(
            expire_le=timezone.now() - timezone.timedelta(days=1)
        )

        reponse = api.post(
            f"/api/conversations/{fil['id']}/repondre/",
            {"texte": "Toujours là ?"},
            format="json",
        )
        assert reponse.status_code == 402

    def test_le_fil_dit_lui_meme_qui_a_le_droit_d_ecrire(
        self, connecte, groupeur, ama
    ):
        """L'interface n'a pas à redeviner la règle : le fil la porte.

        Une règle recopiée dans l'écran finit par diverger de celle qui
        décide, et l'acheteur découvre le refus après avoir tapé son message.
        """
        acheteur = connecte(ama)
        abonner(acheteur)
        fil = ecrire(acheteur, groupeur).data
        assert fil["je_peux_ecrire"] is True

        # L'OAG répond sans payer : pour lui, c'est toujours vrai.
        cote_oag = connecte(groupeur).get(f"/api/conversations/{fil['id']}/messages/")
        assert cote_oag.data["conversation"]["je_peux_ecrire"] is True

        AbonnementContactPrive.objects.update(
            expire_le=timezone.now() - timezone.timedelta(days=1)
        )
        expire = connecte(ama).get(f"/api/conversations/{fil['id']}/messages/")
        assert expire.data["conversation"]["je_peux_ecrire"] is False

    def test_on_ne_lit_pas_le_fil_des_autres(self, connecte, groupeur, ama, yao):
        api = connecte(ama)
        abonner(api)
        fil = ecrire(api, groupeur).data

        intrus = connecte(yao).get(f"/api/conversations/{fil['id']}/messages/")
        assert intrus.status_code == 404

    def test_la_moderation_ne_voit_que_ce_qui_est_signale(
        self, connecte, groupeur, ama, administrateur
    ):
        # ⚠️ `connecte` réauthentifie le **même** client : chaque appel change
        # qui parle. D'où l'ordre strict ci-dessous, et pas de variable gardée
        # d'un bloc à l'autre.
        api = connecte(ama)
        abonner(api)
        fil = ecrire(api, groupeur).data
        message = connecte(ama).get(
            f"/api/conversations/{fil['id']}/messages/"
        ).data["messages"][0]

        assert connecte(administrateur).get("/api/admin/messages/").data["count"] == 0

        connecte(ama).post(
            f"/api/conversations/{fil['id']}/signaler-message/",
            {"message": message["id"]},
            format="json",
        )

        signales = connecte(administrateur).get("/api/admin/messages/").data
        assert signales["count"] == 1
