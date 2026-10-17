# -*- coding: utf-8 -*-
"""Les règles d'argent — celles qu'un jury vérifie et qu'un litige oppose.

Chaque test porte le nom de la règle qu'il protège plutôt que celui de la
fonction qu'il appelle : quand l'un d'eux casse, on doit savoir **ce qui ne
tient plus**, pas seulement où.
"""

from decimal import Decimal

from django.test import TestCase

from groupachat import domaine


class FraisDePlateformeTest(TestCase):
    """1 500 F par groupage abouti, à la charge du groupeur, retenus au retrait."""

    def test_le_jeu_de_demonstration_tombe_juste(self):
        """128 000 − 1 500 = 126 500. Un jury refait ce calcul."""
        resultat = domaine.calculer_retrait(Decimal("128000"))
        self.assertEqual(resultat.collecte, Decimal("128000"))
        self.assertEqual(resultat.frais, Decimal("1500"))
        self.assertEqual(resultat.net, Decimal("126500"))

    def test_les_baskets_tombent_juste_aussi(self):
        """41 × 9 800 = 401 800, moins 1 500 = 400 300 (écran 18)."""
        resultat = domaine.calculer_retrait(Decimal("41") * Decimal("9800"))
        self.assertEqual(resultat.collecte, Decimal("401800"))
        self.assertEqual(resultat.frais, Decimal("1500"))
        self.assertEqual(resultat.net, Decimal("400300"))

    def test_le_montant_est_fixe_quelle_que_soit_la_collecte(self):
        """⚠️ **C'est toute la règle**, et c'est elle qui se perd le plus vite.

        Un pourcentage remis « comme avant » passerait inaperçu sur un seul
        groupage. Trois collectes très différentes doivent porter exactement
        les mêmes frais.
        """
        for collecte in ("10000", "128000", "2500000"):
            with self.subTest(collecte=collecte):
                resultat = domaine.calculer_retrait(Decimal(collecte))
                self.assertEqual(resultat.frais, Decimal("1500"))

    def test_les_frais_ne_portent_pas_sur_les_frais_de_livraison(self):
        """La règle la plus facile à casser par distraction.

        Les frais de livraison sont payés par l'acheteur et vont au
        transporteur. Les compter dans l'assiette ferait payer au groupeur des
        frais sur de l'argent qui ne passe pas par lui.

        ⚠️ **Avec un montant fixe, l'assiette ne change plus le prélèvement**,
        et ce test ne peut plus attraper l'erreur par le montant des frais. Ce
        qu'il vérifie désormais est ce qui reste faux dans ce cas : le **net**,
        qui porterait 32 000 F qui ne sont pas au groupeur.
        """
        parts = Decimal("128000")
        livraison = Decimal("32000")  # 32 commandes × 1 000 F

        sur_les_parts = domaine.calculer_retrait(parts)
        avec_la_livraison = domaine.calculer_retrait(parts + livraison)

        self.assertEqual(sur_les_parts.frais, avec_la_livraison.frais)
        self.assertEqual(
            avec_la_livraison.net - sur_les_parts.net, livraison
        )

    def test_jamais_de_net_negatif(self):
        """Un groupage plus petit que les frais ne réclame pas d'argent.

        Le §9.2 tranche ce cas limite : les frais sont ramenés à la collecte,
        et le net vaut zéro. Un retrait négatif serait absurde à l'écran et un
        découvert en base.
        """
        resultat = domaine.calculer_retrait(Decimal("1000"))
        self.assertEqual(resultat.frais, Decimal("1000"))
        self.assertEqual(resultat.net, Decimal("0"))

    def test_aucun_centime_de_franc(self):
        """Le franc CFA n'a pas de subdivision : tout est arrondi au franc.

        Une collecte avec des decimales ne peut venir que d'un calcul en
        amont, mais elle ne doit jamais ressortir en centimes d'ici.
        """
        resultat = domaine.calculer_retrait(Decimal("128000.60"))
        self.assertEqual(resultat.collecte, Decimal("128001"))
        self.assertEqual(resultat.net, Decimal("126501"))
        self.assertEqual(resultat.frais + resultat.net, resultat.collecte)


class FraisDeLivraisonTest(TestCase):
    """Les frais selon la position — §11.1 du cahier des charges."""

    def test_aucun_frais_dans_lome(self):
        resultat = domaine.calculer_frais_livraison("Tokoin")
        self.assertTrue(resultat.desservi)
        # ⚠️ **Zéro, et c'est la règle, pas un cas limite.** Le seul revenu de
        # la plateforme est de 1 500 F par groupage abouti, à la charge du
        # groupeur. L'acheteur ne paie que sa part.
        self.assertEqual(resultat.montant, Decimal("0"))

    def test_insensible_a_la_casse_et_aux_accents(self):
        for ecriture in ("tokoin", "TOKOIN", "Tokoin "):
            self.assertTrue(domaine.calculer_frais_livraison(ecriture).desservi)

    def test_zone_non_desservie(self):
        """Deux réponses possibles, et deux seulement.

        Pas de troisième cas « tarif calculé plus tard » : on ne demande jamais
        à quelqu'un de payer un total qu'on complétera après.
        """
        resultat = domaine.calculer_frais_livraison("Kpalimé")
        self.assertFalse(resultat.desservi)
        self.assertIsNone(resultat.montant)

    def test_le_fil_rouge_fait_bien_quatre_mille(self):
        """4 000 F de part, et rien d'autre.

        ⚠️ **Ce test s'appelait `test_le_fil_rouge_fait_bien_cinq_mille`** et
        vérifiait 4 000 + 1 000 = 5 000. Les frais de livraison facturés à
        l'acheteur ont été supprimés : le total du fil rouge est désormais
        4 000 F. Le nom est reproduit ici parce que ce chiffre circule dans
        les trois documents et qu'un jury le vérifie.

        C'est l'erreur la plus facile à commettre dans ce produit : afficher
        4 000 F là où l'acheteur paie 5 000 F.
        """
        parts, frais, total = domaine.calculer_total_commande(
            Decimal("4000"), 1, "Tokoin"
        )
        self.assertEqual(parts, Decimal("4000"))
        self.assertEqual(frais, Decimal("0"))
        self.assertEqual(total, Decimal("4000"))

    def test_les_frais_restent_nuls_quelle_que_soit_la_quantite(self):
        """Trois parts, toujours aucun frais.

        Le test gardait autrefois une règle utile — *un colis, des frais ;
        deux parts ne font pas deux livraisons* — et elle n'a plus d'objet
        depuis que les frais sont nuls. On le garde quand même : il attrape le
        jour où quelqu'un rebranche un calcul par part.
        """
        parts, frais, total = domaine.calculer_total_commande(
            Decimal("4000"), 3, "Tokoin"
        )
        self.assertEqual(parts, Decimal("12000"))
        self.assertEqual(frais, Decimal("0"))
        self.assertEqual(total, Decimal("12000"))

    def test_zone_non_desservie_leve_une_erreur(self):
        with self.assertRaises(domaine.ZoneNonDesservie):
            domaine.calculer_total_commande(Decimal("4000"), 1, "Kpalimé")


class CodeLivraisonTest(TestCase):
    """Le code à montrer au livreur."""

    def test_la_forme_est_celle_qu_on_dicte(self):
        code = domaine.generer_code_livraison()
        self.assertRegex(code, r"^[A-Z2-9]{3}-[A-Z2-9]{3}$")

    def test_sans_les_caracteres_qu_on_confond(self):
        """Ni I ni 1, ni O ni 0 : le code se dicte au téléphone."""
        codes = "".join(domaine.generer_code_livraison() for _ in range(200))
        for confusion in "IO01":
            self.assertNotIn(confusion, codes)

    def test_les_codes_ne_se_repetent_pas(self):
        """C'est la preuve de livraison : il ne doit pas être devinable."""
        codes = {domaine.generer_code_livraison() for _ in range(500)}
        self.assertGreater(len(codes), 495)


class KycTest(TestCase):
    """Le contrôle n° 2 — §10.5 du cahier des charges."""

    def test_les_noms_identiques_concordent(self):
        self.assertTrue(domaine.noms_concordent("Akossiwa Mensah", "Akossiwa Mensah"))

    def test_l_ordre_la_casse_et_les_accents_sont_tolerés(self):
        """Refuser « MENSAH Akossiwa » serait une perte de temps pour tous."""
        for ecriture in ("MENSAH Akossiwa", "mensah akossiwa", "Akossiwa  MENSAH"):
            self.assertTrue(
                domaine.noms_concordent("Akossiwa Mensah", ecriture), ecriture
            )

    def test_un_nom_different_ne_concorde_pas(self):
        """Le prête-nom : la procédure doit s'arrêter là."""
        self.assertFalse(domaine.noms_concordent("Akossiwa Mensah", "Kodjo Amegan"))

    def test_un_nom_partiel_ne_concorde_pas(self):
        self.assertFalse(domaine.noms_concordent("Akossiwa Mensah", "Mensah"))

    def test_un_nom_vide_ne_concorde_jamais(self):
        """Sinon deux champs vides se « valideraient » mutuellement."""
        self.assertFalse(domaine.noms_concordent("", ""))
        self.assertFalse(domaine.noms_concordent("Akossiwa Mensah", ""))

    def test_les_plafonds_suivent_les_niveaux(self):
        self.assertEqual(domaine.PLAFONDS_KYC["entree"], Decimal("150000"))
        self.assertEqual(domaine.PLAFONDS_KYC["confirme"], Decimal("600000"))
        # Au cas par cas : pas de valeur inventée.
        self.assertIsNone(domaine.PLAFONDS_KYC["etabli"])
