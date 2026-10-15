# -*- coding: utf-8 -*-
"""L'API du groupeur — ses campagnes, son portefeuille, ses questions.

Un troisième module, et le découpage suit **la règle d'anonymat** plutôt que
la taille des fichiers :

| Module | Ce qu'il laisse sortir |
|---|---|
| ``api.py`` | Le catalogue public. **Aucun nom**, le pseudonyme du groupeur |
| ``api_kyc.py`` | Les identités, derrière le jeton d'administration |
| ``api_groupeur.py`` | Ce qu'un groupeur voit : **des codes et des quartiers** |

Chaque fichier porte une règle unique, énoncée dès sa première ligne. Les
mélanger obligerait à relire, à chaque modification, un fichier où la moitié
des sérialiseurs doivent cacher ce que l'autre moitié doit montrer.

## ⚠️ La règle de ce fichier-ci

**Un groupeur ne voit jamais un nom, un numéro ni une adresse d'acheteur.** Il
voit un code de livraison et un quartier — de quoi emballer et compter, rien
de plus. Ce n'est pas une précaution de confort : c'est ce qui protège la
modèle contre la désintermédiation. Un groupeur qui connaîtrait ses gros
acheteurs pourrait leur proposer la même marchandise hors plateforme, au même
prix, et sans nous.

``CommandeGroupeurSerializer`` dans ``api.py`` porte déjà cette règle pour la
liste des commandes d'une campagne, et un test la vérifie champ par champ.

## ⚠️ Et sa faiblesse, qui est la même que partout

Le groupeur est identifié par **son numéro de téléphone**, passé en paramètre.
Qui connaît le numéro voit le portefeuille et les campagnes. C'est acceptable
le temps d'une démonstration sur données fictives, et **plus du tout ensuite** :
c'est l'authentification qui réglera ça, pas un correctif ici.
"""

from __future__ import annotations

from datetime import timedelta
from collections import Counter
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from django.db.models import Case, Count, IntegerField, Sum, Value, When
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from . import domaine
from .catalogue.models import Campagne
from .demonstration import peupler
from .commandes.models import (
    Commande,
    Justificatif,
    Retrait,
    demander_le_retrait,
    annuler_campagne,
    cloturer_campagne,
)
from .comptes.models import Groupeur
from .echanges.models import (
    Demande,
    Question,
    prevenir_d_une_reponse,
    prevenir_de_l_arrivee,
)


def groupeur_depuis_la_requete(request) -> Groupeur:
    """Retrouve le groupeur par son numéro, ou refuse.

    Centralisé pour que toutes les routes de ce module appliquent la **même**
    normalisation. Un numéro écrit autrement ferait sinon un 404 incompréhensible
    sur une partie des routes seulement — le genre de panne qu'on met longtemps
    à reproduire.
    """
    brut = request.query_params.get("telephone") or request.data.get("telephone")
    if not brut:
        raise ValidationError({"telephone": "Numéro manquant."})
    try:
        telephone = domaine.normaliser_telephone(str(brut))
    except domaine.NumeroInvalide as erreur:
        raise ValidationError({"telephone": str(erreur)}) from erreur

    groupeur = Groupeur.objects.filter(telephone=telephone).first()
    if groupeur is None:
        raise NotFound("Aucun groupeur à ce numéro.")

    # ⚠️ **En démonstration, un espace vide se remplit ici** — et pas
    # seulement à l'inscription.
    #
    # Le peuplement était posé au dépôt du dossier, ce qui ne couvrait qu'un
    # cas : celui de quelqu'un qui vient de s'inscrire. Tous les autres
    # restaient à zéro — un compte créé avant que cette fonction existe, un
    # groupeur du jeu de données qui n'a pas de campagne, une session reprise
    # après une remise à neuf de la base. On ouvrait alors un tableau de bord
    # qui affichait « 0 campagne, 0 commande, 0 F », exact et inutile.
    #
    # Ce point de passage est le seul par lequel **toutes** les routes de
    # l'espace groupeur passent : le remplissage est donc garanti quel que
    # soit l'écran par lequel on entre.
    if getattr(settings, "DEMONSTRATION", False):
        peupler(groupeur)

    return groupeur


# ── Les campagnes du groupeur ──────────────────────────────────────────────


class CampagneDuGroupeurSerializer(serializers.ModelSerializer):
    """Une campagne, vue par celui qui l'a lancée.

    Elle porte **plus** que la version acheteur — la collecte, le nombre de
    commandes — parce que ce sont ses chiffres à lui. Elle ne porte en
    revanche **aucune identité d'acheteur**, et c'est toute la règle de ce
    fichier.
    """

    produit = serializers.CharField(source="titre", read_only=True)
    prix_part = serializers.DecimalField(
        max_digits=12, decimal_places=0, read_only=True
    )
    commandes = serializers.IntegerField(
        source="acheteurs_confirmes", read_only=True
    )
    collecte = serializers.DecimalField(
        source="collecte_sur_les_parts",
        max_digits=12,
        decimal_places=0,
        read_only=True,
    )
    heures_restantes = serializers.IntegerField(read_only=True)
    photo = serializers.CharField(source="media", read_only=True)
    objectif_participants = serializers.IntegerField(read_only=True)
    progression = serializers.IntegerField(read_only=True)

    class Meta:
        model = Campagne
        fields = (
            "id",
            "produit",
            "categorie",
            "prix_part",
            "commandes",
            "collecte",
            "objectif_participants",
            "progression",
            "heures_restantes",
            "statut",
            "photo",
            # ⚠️ Sert à **éteindre le bouton d'annonce**, pas à afficher une
            # date. L'arrivée est un fait unique : sans ce champ, l'écran
            # proposerait de l'annoncer une seconde fois et le serveur
            # répondrait « déjà annoncé » — un bouton qui ne fait rien, ce
            # qu'on vient justement de corriger partout.
            "arrivee_annoncee_le",
        )


class CreationCampagneSerializer(serializers.ModelSerializer):
    """Ce que l'écran 14 envoie pour lancer un groupage.

    ⚠️ ``groupeur`` n'est **pas** dans les champs, et c'est délibéré : il est
    déduit du numéro de téléphone côté serveur. L'accepter depuis le client
    laisserait n'importe qui lancer une campagne au nom d'un autre — et donc
    encaisser sur sa réputation.
    """

    #: Reçu en heures, parce que c'est ce que l'écran 14 demande : « combien de
    #: temps laissez-vous aux acheteurs ? ». Une date absolue obligerait
    #: l'interface à la calculer, et à gérer le fuseau de Lomé.
    duree_heures = serializers.IntegerField(min_value=1, max_value=24 * 30)

    #: Combien de personnes il veut reunir. **Obligatoire**, et c'est voulu :
    #: la barre de progression des cartes n'a pas de denominateur sans lui.
    #:
    #: ⚠️ **Le maximum n'est pas une limite de produit**, c'est un garde-fou de
    #: saisie. Un objectif a 100 000 viendrait d'un doigt qui a glisse sur le
    #: pave numerique, et la barre afficherait 0 % pendant toute la vie du
    #: groupage — ce qui ressemble a une panne.
    objectif_participants = serializers.IntegerField(min_value=1, max_value=5000)

    class Meta:
        model = Campagne
        fields = (
            "titre",
            "description",
            "contenu_part",
            "categorie",
            "prix_part",
            "medias",
            "caracteristiques",
            "variante_libelle",
            "variante_options",
            "quartier_remise",
            "point_remise",
            "remise_le",
            "objectif_participants",
            "duree_heures",
        )


class DepotJustificatifSerializer(serializers.Serializer):
    """Ce que l'écran 17 envoie.

    ``fournisseur`` et ``montant`` ne sont pas décoratifs : ce sont les deux
    seules choses que l'administrateur regarde pour décider de libérer
    l'argent, et les deux qu'on recoupera plus tard avec le relevé bancaire.
    """

    nature = serializers.ChoiceField(choices=Justificatif.Nature.choices)
    fournisseur = serializers.CharField(max_length=160)
    montant = serializers.DecimalField(max_digits=12, decimal_places=0)
    reference = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )


class GroupeurViewSet(viewsets.GenericViewSet):
    """Tout ce que le groupeur consulte et fait depuis son application."""

    serializer_class = CampagneDuGroupeurSerializer

    # ── Écran 13 — le tableau de bord ───────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="tableau-de-bord")
    def tableau_de_bord(self, request):
        """Les quatre chiffres du haut, et ce qui attend une décision.

        ⚠️ **« Disponible » et « en collecte » ne sont pas la même chose**, et
        les confondre serait un mensonge coûteux :

        - *en collecte* est l'argent de ses acheteurs sur des groupages encore
          ouverts. **Il lui appartient déjà** — l'argent est inscrit à son
          portefeuille dès le paiement (§9) — mais il est **détenu jusqu'à la
          clôture**, donc pas retirable ;
        - *disponible* est ce qu'il peut retirer tout de suite, frais déduits.

        Afficher la collecte comme un solde disponible donnerait un chiffre
        flatteur et faux, et le premier retrait refusé détruirait la crédibilité
        du tableau de bord.
        """
        groupeur = groupeur_depuis_la_requete(request)
        campagnes = groupeur.campagnes.all()

        en_collecte = sum(
            (c.collecte_sur_les_parts for c in campagnes if c.est_ouverte),
            Decimal("0"),
        )
        # ⚠️ **Seulement ce qui est encore retirable.** Sommer tous les
        # retraits, y compris ceux déjà partis, affichait comme « disponible »
        # de l'argent qu'il avait déjà touché — le chiffre ne baissait jamais.
        disponible = Retrait.objects.filter(
            campagne__groupeur=groupeur, etat=Retrait.Etat.RETIRABLE
        ).aggregate(total=Sum("net"))["total"] or Decimal("0")

        return Response(
            {
                "pseudonyme": groupeur.pseudonyme,
                "niveau": groupeur.niveau,
                "plafond": (
                    int(groupeur.plafond) if groupeur.plafond is not None else None
                ),
                "campagnes_ouvertes": sum(1 for c in campagnes if c.est_ouverte),
                "commandes": Commande.objects.filter(
                    campagne__groupeur=groupeur,
                    statut__in=Commande.STATUTS_PAYANTS,
                ).count(),
                "en_collecte": int(en_collecte),
                "disponible": int(disponible),
                "par_quartier": self._par_quartier(groupeur),
                "taches": self._taches(groupeur),
            }
        )

    def _par_quartier(self, groupeur: Groupeur) -> list[dict]:
        """D'où viennent ses commandes — **la donnée la plus actionnable**.

        Elle lui dit où ses acheteurs sont, donc où organiser sa remise et sur
        quel quartier insister. Il ne l'a nulle part ailleurs.

        ⚠️ **Agrégée ici, en une requête.** L'écran la calculait autrefois en
        lisant les commandes de chaque campagne, c'est-à-dire une requête par
        campagne depuis le téléphone d'un commerçant sur un forfait limité
        (§5) — il avait donc renoncé, et la table s'affichait vide avec ses
        seuls en-têtes. Une base agrège cela sans effort ; un téléphone non.

        ⚠️ **Un quartier n'identifie personne** (§1.7) : c'est précisément ce
        qui autorise à le montrer au groupeur, alors que le nom, le numéro et
        le repère de l'acheteur ne sortent jamais de ce côté.
        """
        lignes = (
            Commande.objects.filter(
                campagne__groupeur=groupeur,
                statut__in=Commande.STATUTS_PAYANTS,
            )
            .values("quartier")
            .annotate(commandes=Count("id"))
            .order_by("-commandes")
        )

        total = sum(ligne["commandes"] for ligne in lignes)
        return [
            {
                "quartier": ligne["quartier"],
                "commandes": ligne["commandes"],
                "part": round(ligne["commandes"] * 100 / total) if total else 0,
            }
            for ligne in lignes
        ]

    def _taches(self, groupeur: Groupeur) -> list[dict]:
        """« À faire aujourd'hui » — **ce qui attend une décision**.

        Jamais ce qui s'est passé. Un tableau de bord qui raconte le passé se
        lit une fois ; un tableau de bord qui dit quoi faire s'ouvre tous les
        matins.

        L'ordre est celui de l'urgence réelle, pas celui du volume : une
        campagne à clôturer bloque l'argent de dizaines d'acheteurs, une
        question sans réponse n'en bloque aucun.
        """
        taches: list[dict] = []

        a_decider = [
            campagne
            for campagne in groupeur.campagnes.filter(statut=Campagne.Statut.OUVERTE)
            if campagne.heures_restantes == 0
        ]
        for campagne in a_decider:
            taches.append(
                {
                    "id": f"decision-{campagne.pk}",
                    "urgence": "urgent",
                    "libelle": f"{campagne.titre} — groupage clôturé, décidez",
                    "destination": "decision",
                }
            )

        sans_reponse = Question.objects.filter(
            campagne__groupeur=groupeur,
            etat=Question.Etat.PUBLIEE,
            reponse="",
        ).count()
        if sans_reponse:
            taches.append(
                {
                    "id": "questions",
                    "urgence": "normal",
                    "libelle": (
                        f"{sans_reponse} question"
                        f"{'s' if sans_reponse > 1 else ''} sans réponse"
                    ),
                    "destination": "questions",
                }
            )

        demandes = Demande.objects.filter(
            deposee_le__gte=timezone.now() - timedelta(days=7)
        ).count()
        if demandes:
            taches.append(
                {
                    "id": "demandes",
                    "urgence": "normal",
                    "libelle": (
                        f"{demandes} demande{'s' if demandes > 1 else ''} "
                        "cette semaine"
                    ),
                    "destination": "demandes",
                }
            )

        return taches

    # ── Écrans 14 et 15 — ses campagnes ─────────────────────────────────────

    @action(detail=False, methods=["get", "post"], url_path="campagnes")
    def campagnes(self, request):
        groupeur = groupeur_depuis_la_requete(request)

        if request.method == "GET":
            campagnes = groupeur.campagnes.order_by("-cree_le")
            return Response(
                CampagneDuGroupeurSerializer(campagnes, many=True).data
            )

        entree = CreationCampagneSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = dict(entree.validated_data)
        duree = donnees.pop("duree_heures")

        try:
            campagne = Campagne.objects.create(
                groupeur=groupeur,
                date_fin=timezone.now() + timedelta(hours=duree),
                **donnees,
            )
        except DjangoValidationError as erreur:
            # ⚠️ C'est ici qu'atterrit le refus d'un groupeur **non validé**
            # (§10.5) et le dépassement de plafond (§10.4) : les deux vivent
            # dans `Campagne.clean`. Le message du modèle est explicite, on le
            # laisse passer tel quel plutôt que de le remplacer par « requête
            # invalide ».
            raise ValidationError(
                getattr(erreur, "message_dict", None) or {"detail": erreur.messages}
            ) from erreur

        return Response(
            CampagneDuGroupeurSerializer(campagne).data,
            status=status.HTTP_201_CREATED,
        )

    # ── Écran 16 — clôturer ─────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="cloturer")
    def cloturer(self, request, pk=None):
        """Le groupeur maintient le groupage : **son solde devient retirable**.

        ⚠️ **Rien ne part ici.** La clôture ouvre un retrait, elle ne fait pas
        de virement : l'argent était déjà au groupeur depuis le paiement de ses
        acheteurs, il cesse simplement d'être détenu. Les 1 500 F de frais sont
        calculés dès maintenant pour qu'il voie le chiffre exact au moment de
        décider, mais ils ne sortent de son solde qu'au retrait (§9.2).

        ⚠️ Aucun écran ne doit écrire « votre argent est bloqué jusqu'à la
        livraison » : la formulation autorisée est « détenu jusqu'à la
        clôture ». C'est une règle produit, pas une tournure.
        """
        groupeur = groupeur_depuis_la_requete(request)
        campagne = groupeur.campagnes.filter(pk=pk).first()
        if campagne is None:
            raise NotFound("Cette campagne n'est pas la vôtre.")

        try:
            retrait = cloturer_campagne(campagne)
        except DjangoValidationError as erreur:
            raise ValidationError({"detail": erreur.messages}) from erreur

        return Response(
            {
                "collecte": int(retrait.collecte),
                "frais_plateforme": int(retrait.frais_plateforme),
                "montant_retirable": int(retrait.net),
                "frais_livraison_collectes": int(retrait.frais_livraison_collectes),
            }
        )

    # ── Écran 17 — le justificatif d'achat ─────────────────────────────────

    @action(detail=True, methods=["post"], url_path="justificatif")
    def justificatif(self, request, pk=None):
        """Dépose le devis fournisseur, puis le reçu de paiement (§10.3).

        **Le devis est sa demande de virement.** Tant qu'il n'est pas déposé,
        l'argent de la campagne reste détenu par Group Achat : le §10.3 exige
        de savoir chez qui le groupeur achète *avant* que l'argent ne sorte,
        parce que c'est le dernier moment où un contrôle sert encore à quelque
        chose.

        Le reçu vient après l'achat. Son absence entraîne l'annulation de la
        campagne — et c'est pour ça qu'il est demandé ici plutôt que laissé à
        la bonne volonté.

        ⚠️ **Aucun fichier n'est téléversé.** Le stockage à accès restreint
        n'existe pas encore (même raison que pour les pièces d'identité) : ce
        qui est enregistré, c'est **le fournisseur et le montant**, c'est-à-dire
        ce que l'administrateur lit pour décider.
        """
        groupeur = groupeur_depuis_la_requete(request)
        campagne = groupeur.campagnes.filter(pk=pk).first()
        if campagne is None:
            raise NotFound("Cette campagne n'est pas la vôtre.")

        entree = DepotJustificatifSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        # Redéposer remplace : sinon l'administrateur examine une pile et ne
        # sait plus lequel fait foi.
        justificatif, _ = Justificatif.objects.update_or_create(
            campagne=campagne,
            nature=donnees["nature"],
            defaults={
                "fournisseur": donnees["fournisseur"],
                "montant": donnees["montant"],
                "reference": donnees.get("reference", ""),
                "etat": Justificatif.Etat.EN_ATTENTE,
                "motif_refus": "",
            },
        )

        return Response(
            {
                "id": justificatif.pk,
                "nature": justificatif.nature,
                "fournisseur": justificatif.fournisseur,
                "montant": int(justificatif.montant),
                "etat": justificatif.etat,
            },
            status=status.HTTP_201_CREATED,
        )

    # ── Écran 16 — annuler ─────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="annuler")
    def annuler(self, request, pk=None):
        """Le groupeur renonce : **tous les acheteurs sont remboursés**.

        ⚠️ **Aucun frais n'est prélevé sur un groupage annulé** (§7). La
        fonction ne crée donc aucun retrait, et annule celui qui attendait — un
        groupage qui n'aboutit pas ne rapporte rien à personne, et c'est ce qui
        rend la promesse « vous êtes livré, ou remboursé » tenable.
        """
        groupeur = groupeur_depuis_la_requete(request)
        campagne = groupeur.campagnes.filter(pk=pk).first()
        if campagne is None:
            raise NotFound("Cette campagne n'est pas la vôtre.")

        annuler_campagne(campagne)
        return Response({"statut": campagne.statut})

    # ── Écran 18 — le portefeuille ──────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="portefeuille")
    def portefeuille(self, request):
        """Son solde et l'historique de ses retraits, du plus récent au plus ancien.

        Chaque ligne porte **les frais séparément**. Les fondre dans le montant
        priverait le groupeur du moyen de vérifier les 1 500 F, et c'est
        exactement le genre d'opacité qui fait douter d'une plateforme qui tient
        l'argent des autres.

        ⚠️ **``etat`` part avec chaque ligne**, et l'écran s'en sert pour écrire
        « groupage clôturé » ou « retrait ». Un solde devenu retirable et un
        virement réellement parti ne se ressemblent pas, et un groupeur qui les
        confond croit avoir été payé deux fois.
        """
        groupeur = groupeur_depuis_la_requete(request)
        retraits = (
            Retrait.objects.filter(campagne__groupeur=groupeur)
            .select_related("campagne")
            .order_by("-effectue_le")
        )

        return Response(
            {
                "disponible": int(
                    retraits.filter(etat=Retrait.Etat.RETIRABLE).aggregate(
                        total=Sum("net")
                    )["total"]
                    or Decimal("0")
                ),
                # Ce qu'il a réellement touché, pour la tuile « Retiré ».
                "retire": int(
                    retraits.filter(etat=Retrait.Etat.EFFECTUE).aggregate(
                        total=Sum("net")
                    )["total"]
                    or Decimal("0")
                ),
                "mouvements": [
                    {
                        "id": f"R{retrait.pk}",
                        "date": retrait.effectue_le.date().isoformat(),
                        "campagne": retrait.campagne.titre,
                        "etat": retrait.etat,
                        "collecte": int(retrait.collecte),
                        "frais_plateforme": int(retrait.frais_plateforme),
                        "montant": int(retrait.net),
                    }
                    for retrait in retraits
                ],
            }
        )

    @action(detail=False, methods=["post"], url_path="retirer")
    def retirer(self, request):
        """Le groupeur retire tout ce qui est retirable, d'un geste.

        ⚠️ **Tout, et pas une ligne à la fois.** Le bouton de l'écran 18 porte
        un seul montant — « Retirer mes fonds » — et le découper par groupage
        obligerait à un écran de sélection que personne ne demande. Un retrait
        qui solde trois groupages aboutis porte donc 4 500 F de frais, et la
        réponse le dit pour que la confirmation puisse l'annoncer.

        ⚠️ **Nous ne pouvons pas refuser.** Ce solde lui appartient depuis le
        paiement de ses acheteurs (§9.1) : la seule condition est la clôture.
        """
        groupeur = groupeur_depuis_la_requete(request)
        retirables = list(
            Retrait.objects.filter(
                campagne__groupeur=groupeur, etat=Retrait.Etat.RETIRABLE
            ).select_related("campagne")
        )

        if not retirables:
            raise ValidationError(
                {"detail": "Vous n'avez rien à retirer pour l'instant."}
            )

        for retrait in retirables:
            demander_le_retrait(retrait)

        return Response(
            {
                "groupages": len(retirables),
                "frais_plateforme": sum(int(r.frais_plateforme) for r in retirables),
                "montant": sum(int(r.net) for r in retirables),
                # Ce qui reste retirable après ce geste : zéro, et le dire
                # évite à l'écran de recalculer pour l'afficher.
                "disponible": 0,
            }
        )

    # ── Écran 19 — les demandes agrégées ────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="demandes")
    def demandes(self, request):
        """Ce que les acheteurs réclament, **regroupé par produit et quartier**.

        ⚠️ **Agrégé, et jamais ligne par ligne.** Une demande individuelle
        porte le numéro de celui qui l'a déposée ; la servir au groupeur lui
        donnerait exactement le fichier de clients que l'anonymat lui refuse
        partout ailleurs. Ici il voit « 14 personnes à Agoè veulent du riz » —
        de quoi décider de lancer un groupage, et rien pour contacter qui que
        ce soit.
        """
        groupeur_depuis_la_requete(request)

        lignes = (
            Demande.objects.values("produit", "quartier")
            .annotate(
                personnes=Count("id"),
                plus_ancienne=Count("id"),
            )
            .order_by("-personnes")[:20]
        )

        agregees = []
        for index, ligne in enumerate(lignes, start=1):
            demandes = Demande.objects.filter(
                produit=ligne["produit"], quartier=ligne["quartier"]
            )
            plus_ancienne = demandes.order_by("deposee_le").first()
            budgets = [d.budget_maximum for d in demandes if d.budget_maximum]
            agregees.append(
                {
                    "id": f"D{index}",
                    "produit": ligne["produit"],
                    "quartier": ligne["quartier"],
                    "personnes": ligne["personnes"],
                    "jours_ecoules": (
                        (timezone.now() - plus_ancienne.deposee_le).days
                        if plus_ancienne
                        else 0
                    ),
                    "budget_moyen": (
                        int(sum(budgets) / len(budgets)) if budgets else 0
                    ),
                    # ⚠️ **La quantité la plus souvent demandée, pas un volume
                    # estimé.** L'écran affichait « Volume estimé » et une
                    # case vide : le calculer supposerait de connaître le
                    # conditionnement du produit, que la demande ne porte pas
                    # — elle n'a qu'une quantité en texte libre.
                    #
                    # Ce qu'on sait, en revanche, c'est ce que les gens ont
                    # écrit. « 1 sac », demandé onze fois sur quatorze, est un
                    # fait, et c'est ce dont le groupeur a besoin pour décider
                    # de ce qu'il achète.
                    "quantite_courante": (
                        Counter(
                            d.quantite for d in demandes if d.quantite.strip()
                        ).most_common(1)[0][0]
                        if demandes.exclude(quantite="").exists()
                        else ""
                    ),
                }
            )

        return Response(agregees)

    # ── Écran 20 — les questions reçues ─────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="questions")
    def questions(self, request):
        """Les questions posées sur ses campagnes, **sans réponse d'abord**.

        L'ordre n'est pas chronologique : ce sont celles qui attendent qui
        demandent une action, et une question sans réponse sur une fiche
        produit inquiète l'acheteur qui hésite — elle dit que le groupeur ne
        répond pas.
        """
        groupeur = groupeur_depuis_la_requete(request)
        questions = (
            Question.objects.filter(
                campagne__groupeur=groupeur, etat=Question.Etat.PUBLIEE
            )
            .select_related("campagne")
            # ⚠️ `Q(reponse="").desc()` n'existe pas : un `Q` est un filtre,
            # pas une expression ordonnable. On annote donc un drapeau, qui a
            # en prime l'avantage de se lire — `order_by("reponse")` trierait
            # aussi les vides en tête, par hasard alphabétique, et personne ne
            # saurait dans six mois si c'était voulu.
            .annotate(
                sans_reponse=Case(
                    When(reponse="", then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("sans_reponse", "-posee_le")
        )

        return Response(
            [
                {
                    "id": question.pk,
                    "campagne": question.campagne.pk,
                    "campagne_titre": question.campagne.titre,
                    # ⚠️ Le prénom et l'initiale, jamais le nom complet (§1.7).
                    "auteur": question.auteur_affiche,
                    "texte": question.texte,
                    "reponse": question.reponse,
                    "posee_le": question.posee_le,
                }
                for question in questions
            ]
        )

    @action(detail=True, methods=["post"], url_path="repondre")
    def repondre(self, request, pk=None):
        """Répond à une question. **La réponse passe par la modération.**

        Le §15 filtre les deux sens : un groupeur qui glisse son numéro dans
        une réponse publique contourne la plateforme aussi sûrement qu'un
        acheteur qui le demande. Le filtre vit dans ``Question.save`` et
        s'applique donc ici sans qu'on ait à y penser — ce qui est le but.
        """
        groupeur = groupeur_depuis_la_requete(request)
        question = Question.objects.filter(
            pk=pk, campagne__groupeur=groupeur
        ).first()
        if question is None:
            raise NotFound("Cette question ne porte pas sur une de vos campagnes.")

        texte = (request.data.get("reponse") or "").strip()
        if not texte:
            raise ValidationError({"reponse": "La réponse est vide."})

        question.reponse = texte
        question.repondue_le = timezone.now()
        try:
            question.save()
        except DjangoValidationError as erreur:
            raise ValidationError(erreur.message_dict) from erreur

        # ⚠️ **Prévenir l'auteur, et c'est tout l'intérêt de répondre.**
        # Sans cette notification, une réponse n'était lue que par quelqu'un
        # qui revenait de lui-même sur la fiche du produit : autant dire
        # presque personne. Le groupeur répondait dans le vide, et le seul
        # canal entre les deux côtés (§1.7) ne fonctionnait qu'à moitié.
        prevenir_d_une_reponse(question)

        return Response({"id": question.pk, "reponse": question.reponse})

    # ── Écran 15 — annoncer que le produit est arrivé ───────────────────────

    @action(detail=True, methods=["post"], url_path="annoncer-l-arrivee")
    def annoncer_l_arrivee(self, request, pk=None):
        """Le groupeur annonce à ses participants qu'il a reçu la marchandise.

        **C'est le groupeur qui déclenche ; c'est la plateforme qui écrit.**
        Il n'y a aucun champ de texte dans cette route, et c'est la condition
        qui rend cette fonctionnalité compatible avec le produit :

        - **pas de messagerie privée** — un champ libre vers ses acheteurs
          serait une messagerie, quel que soit le nom qu'on lui donne ;
        - **l'anonymat tient** — il ne sait pas à qui part la notification. La
          réponse ne lui renvoie **qu'un compte**, jamais une liste ;
        - **rien à modérer** — il n'y a pas de texte libre, donc pas de filtre
          du §15 à brancher sur un envoi groupé, ce qui est précisément le
          genre de filtre qu'on oublie.

        ⚠️ **Une seule fois par groupage.** L'arrivée est un fait unique, et
        une cloche qui répète le même message perd le droit d'être regardée.
        Un second appel répond 200 avec ``prevenus: 0`` plutôt qu'une erreur :
        du point de vue du groupeur, l'annonce est bien faite.

        ⚠️ **Après la clôture seulement.** « Le produit est arrivé » avant la
        clôture n'a pas de sens — la commande n'est pas passée — et le dire
        ferait croire à une livraison imminente sur un groupage encore ouvert.
        """
        groupeur = groupeur_depuis_la_requete(request)
        campagne = Campagne.objects.filter(pk=pk, groupeur=groupeur).first()
        if campagne is None:
            raise NotFound("Ce groupage n'est pas le vôtre.")

        if campagne.statut not in (
            Campagne.Statut.EN_COURS,
            Campagne.Statut.A_DECIDER,
        ):
            raise ValidationError(
                "Vous pourrez l'annoncer une fois le groupage clôturé."
            )

        if campagne.arrivee_annoncee_le is not None:
            return Response(
                {
                    "prevenus": 0,
                    "deja_annonce": True,
                    "annonce_le": campagne.arrivee_annoncee_le,
                }
            )

        prevenus = prevenir_de_l_arrivee(campagne)
        campagne.arrivee_annoncee_le = timezone.now()
        campagne.save(update_fields=["arrivee_annoncee_le"])

        return Response(
            {
                "prevenus": prevenus,
                "deja_annonce": False,
                "annonce_le": campagne.arrivee_annoncee_le,
            }
        )
