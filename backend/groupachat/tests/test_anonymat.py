# -*- coding: utf-8 -*-
"""L'acheteur et le groupeur ne se connaissent pas.

C'est la règle dont tout le reste dépend. Le séquestre tient l'argent,
l'assurance couvre le groupage, le contrat notarié encadre le groupeur :
l'acheteur fait confiance au dispositif, pas à une personne. En échange,
personne ne donne son nom ni son numéro, et seul l'abonnement Contact Privé
ouvre le pont.

Une fuite ici ne se voit pas à l'œil nu — un champ de trop dans un
sérialiseur, et le modèle économique entier passe à la trappe sans que rien
ne tombe en panne. D'où des tests qui fouillent la **réponse complète** au
lieu de vérifier un champ à la fois : un champ ajouté demain sera attrapé
aussi.
"""

from __future__ import annotations

import json

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError

from groupachat.comptes import noms
from groupachat.comptes.models import Utilisateur

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cache_propre():
    """La limitation de débit vit dans le cache, et trois inscriptions de
    suite la déclenchent : sans ça, le troisième test de la classe reçoit un
    429 et échoue pour une raison qui n'a rien à voir avec l'anonymat."""
    cache.clear()
    yield
    cache.clear()


def tout_le_texte(reponse) -> str:
    """La réponse entière, à plat, pour y chercher ce qui ne doit pas y être."""
    return json.dumps(reponse.data, ensure_ascii=False, default=str)


# Ce qui ne doit jamais sortir d'une réponse vue par l'autre partie. Le nom
# du commerce en fait partie : le donner permettrait à l'acheteur de se rendre
# à la boutique et de court-circuiter la plateforme dès la deuxième commande.
IDENTITE_DU_GROUPEUR = ["Koffi", "Abalo", "90001122", "Abalo Import"]
IDENTITE_DE_L_ACHETEUR = ["Mensah", "91002233"]


class TestCeQueLAcheteurVoitDuGroupeur:
    def test_la_fiche_ne_donne_ni_nom_ni_numero_ni_enseigne(
        self, client, campagne, groupeur
    ):
        groupeur.nom_utilisateur = "Faya-02"
        groupeur.save()

        reponse = client.get(f"/api/catalogue/campagnes/{campagne.id}/")
        texte = tout_le_texte(reponse)

        assert reponse.status_code == 200
        assert "Faya-02" in texte
        for secret in IDENTITE_DU_GROUPEUR:
            assert secret not in texte, f"« {secret} » a fuité sur la fiche"

    def test_le_catalogue_non_plus(self, client, campagne, groupeur):
        groupeur.nom_utilisateur = "Faya-02"
        groupeur.save()

        texte = tout_le_texte(client.get("/api/catalogue/campagnes/"))
        for secret in IDENTITE_DU_GROUPEUR:
            assert secret not in texte, f"« {secret} » a fuité au catalogue"

    def test_un_groupeur_sans_nom_choisi_ne_montre_que_prenom_et_initiale(
        self, client, campagne
    ):
        """Le repli ne doit pas être une porte dérobée vers le nom civil."""
        texte = tout_le_texte(client.get(f"/api/catalogue/campagnes/{campagne.id}/"))

        assert "Koffi A." in texte
        assert "Abalo" not in texte


class TestCeQueLeGroupeurVoitDeSesAcheteurs:
    def test_la_liste_des_participants_ne_donne_ni_nom_ni_numero(
        self, connecte, campagne, groupeur, ama
    ):
        ama.nom_utilisateur = "AmaK"
        ama.save()
        api = connecte(ama)
        part = api.post(
            "/api/participations/",
            {"campagne": campagne.id, "quantite": 2, "bureau_poste": "Bureau de poste de Tokoin"},
            format="json",
        ).data
        api.post(f"/api/participations/{part['id']}/payer/", {}, format="json")

        reponse = connecte(groupeur).get(f"/api/groupeur/campagnes/{campagne.id}/participants/")
        texte = tout_le_texte(reponse)

        assert reponse.status_code == 200
        assert "AmaK" in texte
        for secret in IDENTITE_DE_L_ACHETEUR:
            assert secret not in texte, f"« {secret} » a fuité vers le groupeur"


class TestLeNomDUtilisateur:
    @pytest.mark.parametrize(
        "demande, motif",
        [
            ("Faya 90112233", "un numéro de téléphone"),
            ("Group Achat Officiel", "la plateforme"),
            ("OAG Certifié Or", "un signal de confiance"),
            ("Faya whatsapp", "une autre messagerie"),
            ("ab", "trop court"),
            ("2026", "aucune lettre"),
        ],
    )
    def test_les_noms_qui_defont_l_anonymat_sont_refuses(self, demande, motif):
        with pytest.raises(ValidationError):
            noms.valider(demande)

    def test_un_nom_ordinaire_passe(self):
        for bon in ["Faya-02", "Le Bon Grain", "kodjo_2026", "Ramatou"]:
            noms.valider(bon)

    def test_deux_noms_qui_se_ressemblent_sont_le_meme_nom(self):
        """« Faya-02 » et « faya02 » : aucun acheteur ne les distinguerait."""
        assert noms.normaliser("Faya-02") == noms.normaliser("faya02")
        assert noms.normaliser("FAYA 02") == noms.normaliser("Faya.02")
        assert noms.normaliser("Rémi") == noms.normaliser("remi")

    def test_la_base_refuse_le_doublon_insensible_a_la_casse(self, groupeur):
        groupeur.nom_utilisateur = "Faya-02"
        groupeur.save()

        with pytest.raises(Exception):
            Utilisateur.objects.create_user(
                "93004455", "mdpSolide2026", nom="Autre", prenom="Kossi",
                nom_utilisateur="faya02",
            )

    def test_le_repli_ne_donne_que_le_prenom_et_une_initiale(self):
        assert noms.nom_de_repli("Ama", "Mensah") == "Ama M."
        assert noms.nom_de_repli("Ama", "") == "Ama"
        assert noms.nom_de_repli("", "") == "Acheteur"


class TestInscription:
    def test_un_groupeur_doit_choisir_son_nom(self, client):
        reponse = client.post(
            "/api/comptes/inscription/",
            {
                "nom": "Abalo", "prenom": "Kodjo", "telephone": "93114455",
                "mot_de_passe": "mdpSolide2026", "role": "groupeur",
            },
            format="json",
        )
        assert reponse.status_code == 400
        assert "nom_utilisateur" in reponse.data

    def test_un_acheteur_peut_s_en_passer(self, client):
        reponse = client.post(
            "/api/comptes/inscription/",
            {
                "nom": "Mensah", "prenom": "Afi", "telephone": "93224455",
                "mot_de_passe": "mdpSolide2026",
            },
            format="json",
        )
        assert reponse.status_code == 201

    def test_un_nom_deja_pris_est_refuse_meme_ecrit_autrement(self, client, groupeur):
        groupeur.nom_utilisateur = "Faya-02"
        groupeur.save()

        reponse = client.post(
            "/api/comptes/inscription/",
            {
                "nom": "Kossi", "prenom": "Yao", "telephone": "93334455",
                "mot_de_passe": "mdpSolide2026", "role": "groupeur",
                "nom_utilisateur": "FAYA 02",
            },
            format="json",
        )
        assert reponse.status_code == 400
        assert "nom_utilisateur" in reponse.data
