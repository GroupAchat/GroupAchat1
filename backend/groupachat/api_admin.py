# -*- coding: utf-8 -*-
"""L'API de l'administration : l'état du service, et ce qui attend une décision.

**Derrière le jeton d'administration**, comme ``api_kyc.py`` — ces routes
voient tout : les montants détenus, les groupeurs, les campagnes échouées.

## Ce que l'écran A1 doit répondre, et dans quel ordre

Un administrateur qui ouvre cette page le matin a **une** question : qu'est-ce
qui attend une décision ? Pas « comment ça s'est passé ». Les routes suivent
cet ordre :

1. **ce qui bloque de l'argent** — les **retraits demandés**, parce que le
   groupeur, lui, attend son argent pour pouvoir acheter ;
2. **ce qui bloque un recrutement** — les dossiers KYC (``api_kyc.py``) ;
3. **ce qui a échoué** — groupages annulés, non aboutis : à comprendre, pas à
   décider ;
4. **les chiffres** — en dernier, parce qu'ils ne demandent rien.

⚠️ **Aucune route ne déplace d'argent sans trace.** Exécuter un retrait écrit
qui, quand et sur quel groupage (§18.3). C'est la contrepartie du fait qu'un
jeton partagé ne distingue pas deux administrateurs : si on ne sait pas *qui*
au sens fort, on sait au moins *ce qui a été fait et sous quel nom*.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from .api_kyc import JetonAdmin
from .comptes import sessions_admin
from .catalogue.models import Campagne
from .commandes.models import (
    Commande,
    Justificatif,
    Retrait,
    executer_le_retrait,
)
from .comptes.models import Groupeur
from .echanges.models import Question


class JustificatifSerializer(serializers.ModelSerializer):
    class Meta:
        model = Justificatif
        fields = (
            "id",
            "nature",
            "fournisseur",
            "montant",
            "reference",
            "etat",
            "motif_refus",
            "depose_le",
        )


class RetraitSerializer(serializers.ModelSerializer):
    """Un retrait, avec de quoi exécuter le transfert.

    Il porte **le pseudonyme du groupeur et son vrai nom** : l'administration
    est le seul endroit où les deux se voient ensemble, et c'est nécessaire —
    on ne vire pas de l'argent à un pseudonyme.

    ⚠️ ``devis`` est là pour être **lu**, pas pour autoriser. Le retrait part
    même sans lui (§10.2), et l'administration le constate plutôt qu'elle ne le
    contrôle.
    """

    campagne_titre = serializers.CharField(source="campagne.titre", read_only=True)
    groupeur = serializers.CharField(
        source="campagne.groupeur.pseudonyme", read_only=True
    )
    groupeur_nom = serializers.CharField(
        source="campagne.groupeur.nom_complet", read_only=True
    )
    groupeur_mobile_money = serializers.CharField(
        source="campagne.groupeur.numero_mobile_money", read_only=True
    )
    devis = JustificatifSerializer(read_only=True)
    executable = serializers.BooleanField(read_only=True)
    jours_d_attente = serializers.SerializerMethodField()

    class Meta:
        model = Retrait
        fields = (
            "id",
            "campagne",
            "campagne_titre",
            "groupeur",
            "groupeur_nom",
            "groupeur_mobile_money",
            "collecte",
            "frais_plateforme",
            "net",
            "frais_livraison_collectes",
            "etat",
            "demande_le",
            "libere_le",
            "libere_par",
            "effectue_le",
            "devis",
            "executable",
            "jours_d_attente",
        )

    def get_jours_d_attente(self, retrait: Retrait) -> int:
        """Depuis combien de jours le groupeur attend son argent.

        ⚠️ **On compte depuis sa demande, pas depuis la clôture.** Un solde
        retirable qu'il n'a pas réclamé ne fait attendre personne ; c'est le
        jour où il appuie sur « Retirer mes fonds » que le compteur démarre.
        Tant qu'il n'a rien demandé, la réponse est 0.
        """
        depart = retrait.demande_le
        if depart is None:
            return 0
        return max(0, (timezone.now() - depart).days)


class CampagneAdminSerializer(serializers.ModelSerializer):
    """Une campagne, vue de l'administration. Tout est visible ici."""

    groupeur = serializers.CharField(
        source="groupeur.pseudonyme", read_only=True
    )
    acheteurs_confirmes = serializers.IntegerField(read_only=True)
    objectif_participants = serializers.IntegerField(read_only=True)
    progression = serializers.IntegerField(read_only=True)
    collecte = serializers.DecimalField(
        source="collecte_sur_les_parts",
        max_digits=12,
        decimal_places=0,
        read_only=True,
    )
    heures_restantes = serializers.IntegerField(read_only=True)
    retrait_etat = serializers.SerializerMethodField()
    rembourses = serializers.SerializerMethodField()

    class Meta:
        model = Campagne
        fields = (
            "id",
            "titre",
            "categorie",
            "prix_part",
            "statut",
            "groupeur",
            "acheteurs_confirmes",
            "objectif_participants",
            "progression",
            "collecte",
            "heures_restantes",
            "date_fin",
            "cree_le",
            "retrait_etat",
            "rembourses",
        )

    def get_retrait_etat(self, campagne: Campagne) -> str | None:
        retrait = getattr(campagne, "retrait", None)
        return retrait.etat if retrait else None

    def get_rembourses(self, campagne: Campagne) -> dict | None:
        """Les dégâts d'un groupage annulé : combien de gens, pour combien.

        ⚠️ **Sans ça, un groupage annulé affiche « 0 acheteur, 0 F ».**
        C'est exact — plus personne n'a payé, les commandes sont passées à
        « remboursée » — et c'est l'information la moins utile qu'on puisse
        donner à quelqu'un qui regarde précisément les échecs.

        Ce que l'administration veut savoir d'un groupage qui n'a pas abouti,
        c'est **combien de personnes ont été déçues**. C'est ce chiffre qui dit
        si l'annulation était bénigne ou coûteuse, et c'est lui qui pèsera sur
        le plafond du groupeur (§10.4).
        """
        if campagne.statut != Campagne.Statut.ANNULEE:
            return None

        remboursees = campagne.commandes.filter(statut="remboursee")
        total = remboursees.aggregate(
            parts=Sum("montant_parts"), frais=Sum("frais_livraison")
        )
        return {
            "acheteurs": remboursees.count(),
            "montant": int(
                (total["parts"] or 0) + (total["frais"] or 0)
            ),
        }


class AdministrationViewSet(viewsets.GenericViewSet):
    """Tout ce que l'écran A1 et ses sous-écrans interrogent."""

    permission_classes = [JetonAdmin]
    #: Pas d'authentification acheteur ici : c'est un autre mécanisme et un
    #: autre public. Voir ``api_kyc.DossierViewSet`` pour le raisonnement.
    #: ⚠️ **``SchemaAdmin`` n'authentifie personne** — elle ne fournit que
    #: l'en-tête ``WWW-Authenticate``, sans laquelle DRF répond **403 au lieu
    #: de 401** à une session absente ou expirée. La distinction commande deux
    #: écrans, et ``api/client.ts`` l'exploite déjà avec
    #: ``estNonAuthentifie()`` : **401** rouvre la feuille de connexion,
    #: **403** affiche un refus. Un administrateur dont la session a expiré au
    #: milieu d'un examen de dossier doit retomber sur la feuille, pas sur un
    #: « accès refusé » qui ne lui laisse aucun moyen de revenir.
    authentication_classes = [sessions_admin.SchemaAdmin]
    serializer_class = CampagneAdminSerializer
    queryset = Campagne.objects.none()

    # ── L'état du service ───────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="tableau-de-bord")
    def tableau_de_bord(self, request):
        """Les files, les chiffres, et de quoi tracer les courbes."""
        maintenant = timezone.now()
        campagnes = Campagne.objects.all()

        ouvertes = [c for c in campagnes if c.est_ouverte]
        detenu = sum(
            (c.collecte_sur_les_parts for c in ouvertes), Decimal("0")
        )

        retraits = Retrait.objects.select_related("campagne", "campagne__groupeur")
        demandes = [r for r in retraits if r.etat == Retrait.Etat.DEMANDE]
        # Retirables sans que le groupeur ait rien demandé : personne n'attend,
        # mais le devis manquant s'y lit quand même.
        dormants = [r for r in retraits if r.etat == Retrait.Etat.RETIRABLE]

        return Response(
            {
                "files": self._files(demandes, dormants),
                "indicateurs": self._indicateurs(campagnes, detenu, retraits),
                "alertes": self._alertes(demandes),
                "serie_collecte": self._serie_collecte(),
                "repartition_statuts": self._repartition(campagnes),
                "activite": self._activite(maintenant),
            }
        )

    def _files(
        self, demandes: list[Retrait], dormants: list[Retrait]
    ) -> list[dict]:
        """Ce qui attend une décision, **du plus coûteux au moins coûteux**.

        Les retraits d'abord : c'est la seule file où quelqu'un attend son
        argent pour pouvoir travailler. Un dossier KYC qui traîne coûte un
        groupeur ; un retrait qui traîne coûte une livraison et la confiance de
        dizaines d'acheteurs.

        ⚠️ **La seconde file n'est plus un blocage, c'est une relance.** Avant,
        « devis attendus » listait des versements qu'on refusait de libérer ;
        désormais le groupeur retire sans nous demander, et cette file ne sert
        qu'à constater qui n'a rien déposé — et à compter les récidives (§10.2).
        """
        sans_devis = [r for r in demandes + dormants if r.devis is None]

        kyc = Groupeur.objects.filter(
            statut_kyc=Groupeur.StatutKyc.EN_VERIFICATION
        )
        questions = Question.objects.filter(
            etat=Question.Etat.PUBLIEE, reponse=""
        )
        recus_manquants = Campagne.objects.filter(
            statut=Campagne.Statut.EN_COURS
        ).exclude(justificatifs__nature=Justificatif.Nature.RECU)

        return [
            {
                "id": "retraits",
                "libelle": "Retraits à exécuter",
                "nombre": len(demandes),
                "detail": "Un groupeur attend son argent",
                "argent_expose": True,
                "plus_ancien_jours": max(
                    (
                        (timezone.now() - r.demande_le).days
                        for r in demandes
                        if r.demande_le is not None
                    ),
                    default=0,
                ),
            },
            {
                "id": "devis-manquants",
                "libelle": "Devis manquants",
                "nombre": len(sans_devis),
                "detail": "Clôturés, aucun devis déposé — à relancer",
                "argent_expose": False,
                "plus_ancien_jours": max(
                    (
                        (timezone.now() - r.effectue_le).days
                        for r in sans_devis
                    ),
                    default=0,
                ),
            },
            {
                "id": "kyc",
                "libelle": "Dossiers KYC à valider",
                "nombre": kyc.count(),
                "detail": "Le recrutement est le goulot d'étranglement",
                "argent_expose": False,
                "plus_ancien_jours": self._anciennete(kyc, "cree_le"),
            },
            {
                "id": "recus",
                "libelle": "Reçus d'achat manquants",
                "nombre": recus_manquants.count(),
                "detail": "Payés, mais rien ne prouve qu'ils ont acheté",
                "argent_expose": True,
                "plus_ancien_jours": 0,
            },
            {
                "id": "questions",
                "libelle": "Questions sans réponse",
                "nombre": questions.count(),
                "detail": "Sur une fiche produit, elles inquiètent",
                "argent_expose": False,
                "plus_ancien_jours": self._anciennete(questions, "posee_le"),
            },
        ]

    def _anciennete(self, queryset, champ: str) -> int:
        plus_ancien = queryset.order_by(champ).first()
        if plus_ancien is None:
            return 0
        return max(0, (timezone.now() - getattr(plus_ancien, champ)).days)

    def _indicateurs(self, campagnes, detenu: Decimal, retraits) -> list[dict]:
        """Quatre chiffres, et pas un de plus.

        ⚠️ **« Argent détenu pour les groupeurs » est le premier**, et c'est lui qu'on
        rapproche du solde bancaire réel. C'est le seul chiffre de cet écran qui
        engage la responsabilité de la structure.

        ⚠️ **Le nombre d'inscrits n'y figure pas.** C'est la mesure qui flatte
        et n'engage à rien. Ce qui compte est le nombre de groupages allés
        jusqu'à la livraison.
        """
        livrees = campagnes.filter(statut=Campagne.Statut.LIVREE).count()
        annulees = campagnes.filter(statut=Campagne.Statut.ANNULEE).count()
        terminees = livrees + annulees

        frais = retraits.filter(etat=Retrait.Etat.EFFECTUE).aggregate(
            total=Sum("frais_plateforme")
        )["total"] or Decimal("0")
        aboutis = retraits.filter(etat=Retrait.Etat.EFFECTUE).count()

        return [
            {
                "id": "detenu",
                "libelle": "Argent détenu pour les groupeurs",
                "valeur": int(detenu),
                "unite": "F",
                "detail": "À rapprocher du solde bancaire",
                "ton": "neutre",
            },
            {
                "id": "a-executer",
                "libelle": "Retraits demandés",
                "valeur": int(
                    retraits.filter(etat=Retrait.Etat.DEMANDE).aggregate(
                        total=Sum("net")
                    )["total"]
                    or 0
                ),
                "unite": "F",
                "detail": "Des groupeurs attendent pour acheter",
                "ton": "attention",
            },
            {
                "id": "aboutissement",
                "libelle": "Groupages aboutis",
                "valeur": (
                    round(livrees / terminees * 100) if terminees else 0
                ),
                "unite": "%",
                "detail": f"{livrees} livrés, {annulees} annulés",
                "ton": "succes" if terminees and livrees >= annulees else "neutre",
            },
            {
                "id": "frais",
                "libelle": "Frais encaissés",
                "valeur": int(frais),
                "unite": "F",
                "detail": f"1 500 F par groupage abouti · {aboutis} groupage"
                + ("s" if aboutis > 1 else ""),
                "ton": "neutre",
            },
        ]

    def _alertes(self, demandes: list[Retrait]) -> list[dict]:
        """Ce qui remonte tout seul. **Par gravité, pas par date.**"""
        alertes = []

        for retrait in demandes:
            if retrait.demande_le is None:
                continue
            jours = (timezone.now() - retrait.demande_le).days
            if jours >= 3:
                alertes.append(
                    {
                        "id": f"retrait-{retrait.pk}",
                        "gravite": "danger",
                        "texte": (
                            f"{retrait.campagne.groupeur.pseudonyme} attend "
                            f"son retrait depuis {jours} jours — "
                            f"{int(retrait.net):,} F".replace(",", " ")
                        ),
                        "destination": "retraits",
                    }
                )

        # Le signal d'alerte numéro un du §10.5 : un compte de retrait qui
        # n'est plus au nom du groupeur.
        from . import domaine

        for groupeur in Groupeur.objects.exclude(titulaire_mobile_money=""):
            if not domaine.noms_concordent(
                groupeur.nom_complet, groupeur.titulaire_mobile_money
            ):
                alertes.append(
                    {
                        "id": f"mobile-money-{groupeur.pk}",
                        "gravite": "danger",
                        "texte": (
                            f"{groupeur.pseudonyme} : le compte Mobile Money "
                            f"n'est pas à son nom"
                        ),
                        "destination": "dossiers",
                    }
                )

        return alertes

    def _serie_collecte(self) -> list[dict]:
        """La collecte des quatorze derniers jours, pour la courbe.

        ⚠️ **Calculée depuis les commandes payées**, pas depuis un compteur
        tenu à part : un compteur se désynchronise, et personne ne s'en aperçoit
        avant de comparer au relevé bancaire.
        """
        aujourdhui = timezone.now().date()
        debut = aujourdhui - timedelta(days=13)

        par_jour = {
            ligne["jour"]: ligne["total"]
            for ligne in Commande.objects.filter(
                statut__in=Commande.STATUTS_PAYANTS, passee_le__date__gte=debut
            )
            .annotate(jour=TruncDate("passee_le"))
            .values("jour")
            .annotate(total=Sum("montant_parts"))
        }

        return [
            {
                "jour": (debut + timedelta(days=decalage)).isoformat(),
                "montant": int(
                    par_jour.get(debut + timedelta(days=decalage), 0) or 0
                ),
            }
            for decalage in range(14)
        ]

    def _repartition(self, campagnes) -> list[dict]:
        """Combien de groupages dans chaque état. Alimente le camembert."""
        comptes = campagnes.values("statut").annotate(nombre=Count("id"))
        par_statut = {ligne["statut"]: ligne["nombre"] for ligne in comptes}
        return [
            {"statut": statut, "libelle": libelle, "nombre": par_statut.get(statut, 0)}
            for statut, libelle in Campagne.Statut.choices
        ]

    def _activite(self, maintenant) -> list[dict]:
        """Ce qui s'est passé. **En dernier, et c'est voulu** : ça n'engage rien."""
        lignes = []

        for retrait in Retrait.objects.select_related("campagne")[:6]:
            # Deux libellés, et la différence compte : un solde devenu
            # retirable n'est pas de l'argent parti.
            if retrait.etat == Retrait.Etat.EFFECTUE:
                texte = f"{retrait.campagne.titre} — retrait exécuté, {{montant}} F"
            elif retrait.etat == Retrait.Etat.DEMANDE:
                texte = f"{retrait.campagne.titre} — retrait demandé, {{montant}} F"
            else:
                texte = f"{retrait.campagne.titre} — clôturé, {{montant}} F retirables"

            lignes.append(
                {
                    "date": retrait.effectue_le.date().isoformat(),
                    "texte": texte.format(
                        montant=f"{int(retrait.net):,}".replace(",", " ")
                    ),
                }
            )

        for campagne in Campagne.objects.filter(
            statut=Campagne.Statut.ANNULEE
        ).order_by("-cree_le")[:4]:
            lignes.append(
                {
                    "date": campagne.cree_le.date().isoformat(),
                    "texte": f"{campagne.titre} — groupage annulé, remboursements",
                }
            )

        return sorted(lignes, key=lambda ligne: ligne["date"], reverse=True)[:10]

    # ── Les groupages ───────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="groupages")
    def groupages(self, request):
        """Tous les groupages, filtrables par état.

        C'est ici qu'on voit les **clôturés**, ceux qui **n'ont pas abouti** et
        ceux que les groupeurs ont **annulés** — trois choses différentes qu'un
        seul filtre ``statut`` distingue.
        """
        campagnes = (
            Campagne.objects.select_related("groupeur", "retrait")
            .prefetch_related("commandes")
            .order_by("-cree_le")
        )

        statut = request.query_params.get("statut")
        if statut:
            campagnes = campagnes.filter(statut=statut)

        return Response(CampagneAdminSerializer(campagnes, many=True).data)

    # ── Les retraits ────────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="retraits")
    def retraits(self, request):
        """Les retraits, du plus ancien au plus récent.

        **Du plus ancien**, parce qu'un groupeur qui attend depuis cinq jours
        ne peut pas acheter la marchandise qu'il a vendue, et que ce sont ses
        acheteurs qui attendront ensuite.
        """
        retraits = Retrait.objects.select_related(
            "campagne", "campagne__groupeur"
        ).order_by("effectue_le")

        etat = request.query_params.get("etat")
        if etat:
            retraits = retraits.filter(etat=etat)

        return Response(RetraitSerializer(retraits, many=True).data)

    @action(detail=True, methods=["post"], url_path="executer")
    def executer(self, request, pk=None):
        """Fait partir l'argent que le groupeur a demandé.

        ⚠️ **Refuse ce qu'il n'a pas demandé**, et rien d'autre. Le devis
        fournisseur n'entre plus dans ce contrôle : son solde est à lui, et le
        §9.1 du cahier des charges assume cette perte de levier au lieu de la
        masquer derrière un refus qu'on ne pourrait pas justifier.

        ⚠️ Aucun virement réel n'est émis : le paiement est simulé jusqu'à
        l'agrément d'un agrégateur (§18.2). Cette route note que l'argent
        **doit** partir, et qui l'a exécuté.
        """
        retrait = Retrait.objects.filter(pk=pk).first()
        if retrait is None:
            raise NotFound("Retrait introuvable.")

        par = (request.data.get("decide_par") or "Administration").strip()
        try:
            executer_le_retrait(retrait, par=par)
        except DjangoValidationError as erreur:
            raise ValidationError({"detail": erreur.messages}) from erreur

        return Response(RetraitSerializer(retrait).data)
