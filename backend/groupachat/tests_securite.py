# -*- coding: utf-8 -*-
"""Les protections contre l'abus, et les accès aux pièces d'identité.

Ces tests ne décrivent pas une fonctionnalité : ils verrouillent des
décisions de sécurité. Un test qui tombe ici veut dire qu'une porte s'est
rouverte.
"""

from __future__ import annotations

from datetime import timedelta
from io import BytesIO

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from groupachat.comptes.models import (
    CodeVerification,
    DossierKYC,
    TropDeCodes,
    Utilisateur,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def cache_propre():
    """Les limites vivent dans le cache : un test ne doit pas hériter du précédent."""
    cache.clear()
    yield
    cache.clear()


def image_de(taille_px: int = 8) -> SimpleUploadedFile:
    tampon = BytesIO()
    Image.new("RGB", (taille_px, taille_px), "white").save(tampon, format="PNG")
    return SimpleUploadedFile("piece.png", tampon.getvalue(), content_type="image/png")


class TestPlafondDesCodes:
    """La limite qui empêche de deviner un code à six chiffres."""

    def test_un_compte_ne_recoit_pas_plus_de_cinq_codes_par_heure(self, ama):
        for _ in range(CodeVerification.MAX_CODES_PAR_HEURE):
            CodeVerification.emettre(ama)

        with pytest.raises(TropDeCodes):
            CodeVerification.emettre(ama)

    def test_le_plafond_se_relache_apres_une_heure(self, ama):
        for _ in range(CodeVerification.MAX_CODES_PAR_HEURE):
            CodeVerification.emettre(ama)

        # On vieillit les codes au lieu d'attendre : le plafond glisse.
        CodeVerification.objects.filter(utilisateur=ama).update(
            cree_le=timezone.now() - timedelta(hours=2)
        )
        assert CodeVerification.emettre(ama) is not None

    def test_le_plafond_est_par_compte(self, ama, yao):
        for _ in range(CodeVerification.MAX_CODES_PAR_HEURE):
            CodeVerification.emettre(ama)
        # Saturer un numéro ne doit pas priver les autres.
        assert CodeVerification.emettre(yao) is not None

    def test_l_api_refuse_poliment_au_lieu_de_planter(self, client):
        inscription = client.post(
            "/api/comptes/inscription/",
            {"nom": "M", "prenom": "A", "telephone": "91002233",
             "mot_de_passe": "mdpSolide2026"},
            format="json",
        )
        assert inscription.status_code == 201

        # Le premier code vient de l'inscription : il en reste quatre.
        for _ in range(CodeVerification.MAX_CODES_PAR_HEURE - 1):
            client.post("/api/comptes/renvoyer-code/", {"telephone": "91002233"},
                        format="json")

        refus = client.post("/api/comptes/renvoyer-code/", {"telephone": "91002233"},
                            format="json")
        # Deux gardes couvrent ce cas — la limite de débit et le plafond en
        # base. Lequel parle en premier importe peu ; ce qui compte est que
        # la demande soit refusée, et poliment.
        assert refus.status_code == 429


class TestLimitationDeDebit:
    def test_la_connexion_finit_par_etre_freinee(self, client, ama):
        codes = set()
        for essai in range(70):
            reponse = client.post(
                "/api/comptes/connexion/",
                {"telephone": ama.telephone, "mot_de_passe": f"faux{essai}"},
                format="json",
            )
            codes.add(reponse.status_code)
            if reponse.status_code == 429:
                break
        assert 429 in codes, "la force brute sur la connexion doit finir par être bloquée"

    def test_la_limite_de_renvoi_suit_le_numero_pas_l_adresse(self, client):
        """Changer d'adresse ne doit pas remettre le compteur à zéro."""
        client.post(
            "/api/comptes/inscription/",
            {"nom": "M", "prenom": "A", "telephone": "91002233",
             "mot_de_passe": "mdpSolide2026"},
            format="json",
        )
        chemin = "/api/comptes/renvoyer-code/"
        charge = {"telephone": "91002233"}

        vu = set()
        for essai in range(12):
            # Une adresse différente à chaque appel : seule la limite par
            # numéro peut encore arrêter la série.
            reponse = client.post(chemin, charge, format="json",
                                  REMOTE_ADDR=f"41.207.{essai}.10")
            vu.add(reponse.status_code)
            if reponse.status_code == 429:
                break
        assert 429 in vu


class TestPiecesKYC:
    @pytest.fixture
    def dossier(self, ama) -> DossierKYC:
        return DossierKYC.objects.create(
            utilisateur=ama, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-1", numero_mobile_money="91002233",
            piece_recto=image_de(),
        )

    def test_une_piece_n_est_pas_servie_par_l_adresse_publique(self, client, dossier):
        """Le chemin public doit refuser le dossier des pièces d'identité."""
        reponse = client.get(f"/medias/{dossier.piece_recto.name}")
        assert reponse.status_code == 404

    def test_un_anonyme_n_y_accede_pas(self, client, dossier):
        assert client.get(f"/pieces/{dossier.pk}/recto/").status_code == 404

    def test_un_autre_acheteur_n_y_accede_pas(self, client, dossier, yao):
        client.force_login(yao)
        assert client.get(f"/pieces/{dossier.pk}/recto/").status_code == 404

    def test_le_proprietaire_y_accede(self, client, dossier, ama):
        # `force_login` et non `force_authenticate` : cette vue n'est pas une
        # vue DRF, elle lit la session comme le ferait un navigateur.
        client.force_login(ama)
        reponse = client.get(f"/pieces/{dossier.pk}/recto/")
        assert reponse.status_code == 200
        assert reponse["Cache-Control"] == "private, no-store"

    def test_l_equipe_y_accede(self, client, dossier, administrateur):
        client.force_login(administrateur)
        assert client.get(f"/pieces/{dossier.pk}/recto/").status_code == 200

    def test_le_dossier_rendu_par_l_api_ne_donne_pas_le_chemin_du_fichier(
        self, connecte, dossier, ama
    ):
        reponse = connecte(ama).get("/api/comptes/dossier/")
        assert reponse.status_code == 200
        lien = reponse.data["lien_recto"]
        assert "/medias/" not in lien, "le chemin brut exposerait la pièce"
        assert f"/pieces/{dossier.pk}/recto/" in lien


class TestCloisonnement:
    def test_les_notifications_exigent_un_compte(self, client):
        assert client.get("/api/notifications/").status_code in (401, 403)

    def test_une_piece_trop_lourde_est_refusee(self, connecte, ama, settings):
        settings.TAILLE_MAX_PIECE_OCTETS = 1024
        reponse = connecte(ama).post(
            "/api/comptes/dossier/",
            {"type_piece": "cni", "numero_piece": "CNI-9",
             "numero_mobile_money": "91002233", "piece_recto": image_de(600)},
            format="multipart",
        )
        assert reponse.status_code == 400
        assert "trop lourde" in str(reponse.data).lower()


class TestJeuDeDemonstration:
    """Le rechargement au déploiement, et ce qu'il ne doit pas casser.

    Ces tests gardent une promesse précise : **une poussée qui change le jeu
    de données le fait apparaître**, et une poussée qui n'y touche pas
    laisse la démonstration en place.
    """

    def executer(self, **options):
        from django.core.management import call_command

        call_command("charger_demo", **options)

    def test_le_premier_chargement_pose_la_version(self):
        from groupachat.catalogue.management.commands.charger_demo import VERSION_DEMO
        from groupachat.catalogue.models import Campagne, EtatDemonstration

        self.executer(synchroniser=True)
        assert Campagne.objects.exists()
        assert EtatDemonstration.objects.get().version == VERSION_DEMO

    def test_a_version_egale_rien_ne_bouge(self):
        """Un redéploiement sans changement ne doit rien détruire."""
        from groupachat.catalogue.models import Campagne
        from groupachat.comptes.models import Utilisateur

        self.executer(synchroniser=True)
        campagnes = Campagne.objects.count()

        # Quelqu'un s'inscrit pendant la démonstration : son compte doit
        # survivre au redéploiement suivant.
        Utilisateur.objects.create_user(
            "90999999", "mdpSolide2026", nom="Visiteur", prenom="De passage",
            telephone_verifie=True,
        )

        self.executer(synchroniser=True)
        assert Campagne.objects.count() == campagnes
        assert Utilisateur.objects.filter(telephone="90999999").exists()

    def test_une_version_differente_remet_le_jeu_a_plat(self, monkeypatch):
        """Et surtout : sans lever d'erreur d'intégrité.

        L'effacement traverse des relations protégées — `Transaction`
        protège `Participation`, `Decaissement` protège `Campagne`, et un
        sous-rayon protège son parent. Dans le désordre, il laisserait la
        base à moitié vidée.
        """
        from groupachat.catalogue.management.commands import charger_demo
        from groupachat.catalogue.models import Campagne, Categorie, EtatDemonstration
        from groupachat.comptes.models import Utilisateur

        self.executer(synchroniser=True)
        Utilisateur.objects.create_user(
            "90999999", "mdpSolide2026", nom="Visiteur", prenom="De passage",
            telephone_verifie=True,
        )

        monkeypatch.setattr(charger_demo, "VERSION_DEMO", "version-suivante")
        self.executer(synchroniser=True)

        assert EtatDemonstration.objects.get().version == "version-suivante"
        assert Campagne.objects.exists(), "le jeu doit être rechargé, pas seulement effacé"
        assert Categorie.objects.filter(parent__isnull=False).exists()
        assert not Utilisateur.objects.filter(telephone="90999999").exists()

    def test_l_equipe_survit_a_un_rechargement(self, administrateur, monkeypatch):
        """Effacer les comptes de l'équipe couperait l'accès à la console."""
        from groupachat.catalogue.management.commands import charger_demo
        from groupachat.comptes.models import Utilisateur

        self.executer(synchroniser=True)
        monkeypatch.setattr(charger_demo, "VERSION_DEMO", "version-suivante")
        self.executer(synchroniser=True)

        assert Utilisateur.objects.filter(pk=administrateur.pk).exists()
