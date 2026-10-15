# -*- coding: utf-8 -*-
"""L'API du recrutement des groupeurs : dépôt, examen, décision, annonce.

Un module séparé de ``api.py``, et pas par souci de taille de fichier : **ce
sont les seules routes du projet qui transportent des identités**. ``api.py``
est construit autour de la règle inverse — n'y laisser sortir aucun nom vers un
groupeur (§1.7). Mélanger les deux reviendrait à relire, à chaque modification,
un fichier où la moitié des sérialiseurs doivent cacher ce que l'autre moitié
doit montrer. Séparés, chacun porte une règle unique, et le fichier le dit dès
sa première ligne.

## Le parcours, de bout en bout

    Groupeur                      Administrateur                Groupeur
    ────────                      ──────────────                ────────
    POST /api/groupeurs/     ──▶  GET /api/dossiers/
    (dossier + pièces)            (la file d'attente)
                                        │
                                  GET /api/dossiers/{id}/
                                  (il étudie les pièces)
                                        │
                                  POST .../decision/      ──▶  courriel
                                  (valide / à compléter /      ou appel
                                   refuse + motif + canal)
                                        │
                                  POST .../annonce-faite/
                                  (si c'était un appel)
                                        │
    GET /api/groupeurs/dossier/ ◀───────┘
    (il voit la décision et son motif)

**Aucune transition n'est automatique.** Le §10.5 confie la décision à un
humain, et c'est le produit lui-même : « vous êtes livré, ou remboursé »
s'affiche à l'acheteur sur presque chaque écran, et c'est **nous** qui
remboursons. Le jour d'un litige, notre seul recours contre le groupeur est le
dossier — il ne vaut donc que si quelqu'un l'a réellement regardé.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from . import domaine, notifications
from .demonstration import peupler
from .api import ChampTelephone
from .comptes.annonces import annoncer
from .comptes.models import DecisionKyc, Groupeur, PieceKyc


# ── Le garde-fou de l'administration ────────────────────────────────────────


class JetonAdmin(BasePermission):
    """Un jeton partagé, lu dans l'en-tête ``X-Jeton-Admin``.

    ⚠️ **Ce n'est pas de l'authentification, et il ne faut pas le prendre pour
    telle.** Un jeton unique ne distingue pas deux administrateurs, ne se
    révoque pas individuellement, et se retrouve dans un historique de shell le
    jour où quelqu'un le colle dans un ``curl``. Le champ ``decide_par`` des
    décisions repose d'ailleurs, pour la même raison, sur la bonne foi de celui
    qui le remplit.

    Il est quand même là, et c'est mieux que le ``AllowAny`` global du §1.5 :
    ces routes transportent **des noms, des numéros de téléphone, des numéros
    de pièce d'identité et des références de pièces déposées**. C'est le point
    d'entrée le plus sensible du projet. Le laisser ouvert parce que
    « l'authentification viendra plus tard » serait un choix, pas un oubli.

    **Il échoue fermé** : jeton absent de l'environnement, routes inaccessibles.
    L'inverse — ouvrir faute de configuration — est l'erreur classique, et elle
    s'installe silencieusement en production, le jour où le fichier
    d'environnement n'est pas déployé.
    """

    message = (
        "Ces données sont réservées à l'administration. Jeton absent ou "
        "invalide."
    )

    def has_permission(self, request, view) -> bool:
        # Par les réglages, et non par `os.environ` : c'est `config/settings.py`
        # qui charge le `.env` de la racine, donc lui seul voit la valeur dans
        # tous les contextes d'import.
        attendu = settings.JETON_ADMIN
        if not attendu:
            raise PermissionDenied(
                "JETON_ADMIN n'est pas configuré sur le serveur : "
                "l'administration des dossiers KYC est fermée. Renseignez-le "
                "dans le .env de la racine du dépôt."
            )
        return request.headers.get("X-Jeton-Admin") == attendu


# ── Ce que le groupeur dépose ───────────────────────────────────────────────


class PieceSerializer(serializers.ModelSerializer):
    """Une pièce déposée.

    ⚠️ ``reference`` est une **clé dans un stockage à accès restreint**, pas
    une URL. Voir ``PieceKyc`` : le §10.5 interdit que les pièces d'identité et
    les selfies partagent le stockage des photos de produits, et ce stockage
    reste à mettre en place.
    """

    class Meta:
        model = PieceKyc
        fields = ("nature", "reference", "depose_le")
        read_only_fields = ("depose_le",)


class InscriptionSerializer(serializers.ModelSerializer):
    """Le dossier de niveau Entrée — contrôles 1, 2 et 3 du §10.5.

    **Trois contrôles et non sept.** Demander le registre de commerce et deux
    références dès la première minute ferait fuir exactement les commerçants
    recherchés : la plupart des bons groupeurs sont dans l'informel. Le reste
    vient au niveau Confirmé, après trois groupages livrés.
    """

    pieces = PieceSerializer(many=True, write_only=True)
    # Même normalisation que du côté acheteur : le téléphone est l'identifiant
    # de compte, et deux formes feraient deux comptes pour la même personne.
    telephone = ChampTelephone(max_length=20)
    numero_mobile_money = ChampTelephone(max_length=20)

    class Meta:
        model = Groupeur
        fields = (
            "id",
            "pseudonyme",
            "nom_complet",
            "telephone",
            "courriel",
            "titulaire_mobile_money",
            "numero_mobile_money",
            "pieces",
        )

    def validate(self, donnees: dict) -> dict:
        """Contrôle n° 2 — et il arrête tout.

        Le modèle le vérifie déjà dans ``clean``, mais une erreur de modèle
        remonte en 500 si personne ne l'intercepte. Ici, elle remonte en 400
        sur le bon champ, et l'interface sait l'afficher sous la bonne case.

        Le message dit **pourquoi** plutôt que « champ invalide » : quelqu'un
        qui a saisi le compte de son conjoint doit comprendre que ce n'est pas
        une tracasserie administrative mais la raison même pour laquelle un
        acheteur accepte de payer d'avance.
        """
        if not domaine.noms_concordent(
            donnees.get("nom_complet", ""),
            donnees.get("titulaire_mobile_money", ""),
        ):
            raise ValidationError(
                {
                    "titulaire_mobile_money": (
                        "Le titulaire du compte Mobile Money doit porter le "
                        "même nom que votre pièce d'identité. L'argent des "
                        "acheteurs ne peut pas partir sur le compte de "
                        "quelqu'un d'autre."
                    )
                }
            )

        natures = [piece["nature"] for piece in donnees.get("pieces", [])]
        manquantes = _PIECES_EXIGEES - set(natures)
        if manquantes:
            raise ValidationError(
                {
                    "pieces": (
                        "Dossier incomplet : il manque "
                        + ", ".join(
                            sorted(
                                PieceKyc.Nature(nature).label.lower()
                                for nature in manquantes
                            )
                        )
                        + "."
                    )
                }
            )

        if len(natures) != len(set(natures)):
            raise ValidationError(
                {"pieces": "Une seule pièce par nature."}
            )

        return donnees


#: Les trois pièces sans lesquelles un dossier n'est pas examinable.
#:
#: Le selfie en fait partie, et ce n'est pas une formalité : **sans lui, une
#: pièce d'identité volée suffit** à passer le contrôle n° 1.
_PIECES_EXIGEES = {
    PieceKyc.Nature.PIECE_RECTO,
    PieceKyc.Nature.PIECE_VERSO,
    PieceKyc.Nature.SELFIE,
}


# ── Ce que le groupeur peut relire de son propre dossier ────────────────────


class MonDossierSerializer(serializers.ModelSerializer):
    """L'état de son dossier, tel que le groupeur le voit.

    Il porte **le motif en clair** quand le dossier n'est pas validé. Afficher
    « refusé » sans dire pourquoi est une porte fermée sans poignée, et c'est
    aussi ce qui génère l'appel au support qu'on cherchait à éviter.
    """

    etat = serializers.CharField(source="statut_kyc", read_only=True)
    plafond = serializers.SerializerMethodField()
    peut_lancer_une_campagne = serializers.BooleanField(read_only=True)
    motif = serializers.SerializerMethodField()
    decide_le = serializers.SerializerMethodField()

    class Meta:
        model = Groupeur
        fields = (
            "id",
            "pseudonyme",
            "etat",
            "niveau",
            "plafond",
            "peut_lancer_une_campagne",
            "motif",
            "decide_le",
        )

    def get_plafond(self, groupeur: Groupeur) -> int | None:
        """``None`` au niveau Établi : il se décide au cas par cas (§10.4).

        On renvoie bien ``null`` plutôt qu'un grand nombre : l'interface doit
        écrire « fixé avec vous », pas afficher un plafond inventé.
        """
        plafond = groupeur.plafond
        return int(plafond) if plafond is not None else None

    def get_motif(self, groupeur: Groupeur) -> str:
        """Le motif **destiné au groupeur**, pas la note interne.

        La distinction est dans ``notifications.MOTIFS`` : « doute sérieux sur
        l'identité » se note en interne, il ne se dit pas à l'intéressé — le
        lui dire lui apprendrait quoi corriger pour recommencer.
        """
        decision = groupeur.derniere_decision
        if decision is None or not decision.motif:
            return ""
        return notifications.MOTIFS[decision.motif]["public"]

    def get_decide_le(self, groupeur: Groupeur):
        decision = groupeur.derniere_decision
        return decision.decide_le if decision else None


# ── Ce que l'administrateur voit ────────────────────────────────────────────


class DecisionSerializer(serializers.ModelSerializer):
    libelle_motif = serializers.CharField(read_only=True)

    class Meta:
        model = DecisionKyc
        fields = (
            "id",
            "issue",
            "motif",
            "libelle_motif",
            "niveau_accorde",
            "decide_par",
            "decide_le",
            "canal",
            "notifie_le",
        )


class DossierSerializer(serializers.ModelSerializer):
    """Le dossier complet, nom compris. **Derrière le jeton d'administration.**

    C'est l'exact inverse de ``GroupeurPublicSerializer``, qui ne laisse sortir
    qu'un pseudonyme vers les acheteurs. Les deux sérialiseurs décrivent le
    même modèle et doivent rester lisibles côte à côte pour qu'on ne confonde
    jamais l'un avec l'autre — d'où leurs noms, et d'où les deux fichiers.
    """

    pieces = PieceSerializer(many=True, read_only=True)
    decisions_kyc = DecisionSerializer(many=True, read_only=True)
    concordance_noms = serializers.SerializerMethodField()
    campagnes_livrees = serializers.SerializerMethodField()

    class Meta:
        model = Groupeur
        fields = (
            "id",
            "pseudonyme",
            "nom_complet",
            "telephone",
            "courriel",
            "titulaire_mobile_money",
            "numero_mobile_money",
            "niveau",
            "statut_kyc",
            "cree_le",
            "pieces",
            "decisions_kyc",
            "concordance_noms",
            "campagnes_livrees",
        )

    def get_concordance_noms(self, groupeur: Groupeur) -> bool:
        """Le contrôle n° 2, recalculé à l'affichage.

        Il est déjà vérifié au dépôt, mais l'administrateur doit le **voir**
        plutôt que de le supposer : le compte Mobile Money peut avoir changé
        depuis — et c'est le signal d'alerte numéro un du §10.5.
        """
        return domaine.noms_concordent(
            groupeur.nom_complet, groupeur.titulaire_mobile_money
        )

    def get_campagnes_livrees(self, groupeur: Groupeur) -> int:
        """Ce qui conditionne son passage au niveau Confirmé (3 groupages)."""
        return groupeur.campagnes.filter(statut="livree").count()


class TrancherSerializer(serializers.Serializer):
    """Ce que l'administrateur envoie pour trancher.

    ``motif`` est contrôlé contre la liste fermée de ``notifications.MOTIFS``
    plutôt que laissé libre. Un champ libre contiendrait, au bout de six mois,
    quarante formulations du même refus : on ne pourrait plus compter pourquoi
    les dossiers échouent, donc plus corriger le formulaire qui les fait
    échouer.
    """

    issue = serializers.ChoiceField(choices=DecisionKyc.Issue.choices)
    motif = serializers.ChoiceField(
        choices=sorted(notifications.MOTIFS), required=False, allow_blank=True
    )
    niveau = serializers.ChoiceField(
        choices=Groupeur.Niveau.choices, required=False
    )
    canal = serializers.ChoiceField(choices=DecisionKyc.Canal.choices)
    decide_par = serializers.CharField(max_length=120)

    def validate(self, donnees: dict) -> dict:
        try:
            notifications.verifier(donnees["issue"], donnees.get("motif"))
        except notifications.MotifRequis:
            raise ValidationError(
                {
                    "motif": (
                        "Un motif est obligatoire dès que le dossier n'est pas "
                        "validé : sans lui, le groupeur ne peut pas savoir quoi "
                        "corriger, et personne ne pourra relire la décision "
                        "dans six mois."
                    )
                }
            )
        return donnees


# ── Les vues ────────────────────────────────────────────────────────────────


class GroupeurViewSet(viewsets.GenericViewSet):
    """Le côté groupeur : il dépose son dossier, puis il en suit l'état.

    Ouvert sans jeton — c'est le formulaire d'inscription publique. Ce qui en
    sort est en revanche limité : un dépôt ne renvoie que l'identifiant et
    l'état, jamais le dossier relu.
    """

    queryset = Groupeur.objects.all()
    serializer_class = InscriptionSerializer

    def create(self, request):
        """Dépose un dossier et le met en file d'attente, en une requête.

        Les deux gestes sont indissociables : un dossier créé mais non soumis
        n'apparaît dans la file de personne, et le groupeur, lui, croit avoir
        terminé. C'est la panne la plus coûteuse qu'on puisse installer ici —
        invisible des deux côtés.
        """
        entree = self.get_serializer(data=request.data)
        entree.is_valid(raise_exception=True)
        pieces = entree.validated_data.pop("pieces")

        try:
            groupeur = Groupeur.objects.create(**entree.validated_data)
        except DjangoValidationError as erreur:
            raise ValidationError(erreur.message_dict)

        PieceKyc.objects.bulk_create(
            PieceKyc(groupeur=groupeur, **piece) for piece in pieces
        )
        groupeur.soumettre_le_dossier()

        # ⚠️ **Mode démonstration : le dossier est validé sur-le-champ.**
        #
        # L'examen par un humain est le cœur du §10.5 : c'est lui qui rend
        # opposable le dossier sur lequel repose « vous êtes livré, ou
        # remboursé ». On ne le saute que pour montrer le produit, jamais en
        # ligne : le réglage suit
        # ``DEBUG`` et s'éteint seul en production (voir ``settings.py``).
        #
        # La décision est **tracée comme les autres**, avec son auteur écrit en
        # clair. Une validation anonyme dans la base serait indiscernable d'un
        # vrai examen, et c'est précisément ce qu'il ne faut pas laisser.
        if getattr(settings, "DEMONSTRATION", False):
            groupeur.trancher(
                issue="valide",
                decide_par="Mode démonstration",
                canal=DecisionKyc.Canal.COURRIEL,
            )
            groupeur.refresh_from_db()

            # ⚠️ **On n'efface plus les démonstrations précédentes ici.**
            #
            # Ce nettoyage existait pour garder le catalogue propre : six
            # groupages publics par inscription, cinq passages, trente
            # doublons. Mais il détruisait aussi **la session que quelqu'un
            # était en train d'utiliser** : son espace se vidait d'un coup,
            # sans rien dire, parce qu'un autre s'était inscrit entre-temps.
            #
            # Un catalogue encombré se range en une commande
            # (`manage.py nettoyer_demonstration`). Un espace vidé sous les
            # yeux de celui qui s'en sert ne se rattrape pas.

            # On lui donne un passé : sans campagnes ni commandes, chacun
            # de ses écrans afficherait « 0 », ce qui est exact et ne montre
            # rien du produit. Voir `demonstration.peupler`.
            peupler(groupeur)

        return Response(
            MonDossierSerializer(groupeur).data, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"], url_path="dossier")
    def dossier(self, request):
        """L'état de son dossier, retrouvé par son numéro de téléphone.

        ⚠️ **Même faiblesse que le côté acheteur** : qui connaît le numéro lit
        l'état du dossier. Ce qui sort ici est volontairement pauvre — un
        pseudonyme, un état, un motif, aucun document, aucune pièce
        d'identité — mais ça reste une information sur une personne nommée. À
        remplacer par un compte authentifié, c'est l'un des manques listés dans
        ``backend/README.md``.
        """
        telephone = request.query_params.get("telephone", "").strip()
        if not telephone:
            raise ValidationError({"telephone": "Numéro manquant."})
        try:
            # La lecture normalise comme l'écriture : voir `CommandeViewSet`.
            telephone = domaine.normaliser_telephone(telephone)
        except domaine.NumeroInvalide as erreur:
            raise ValidationError({"telephone": str(erreur)}) from erreur

        groupeur = self.get_queryset().filter(telephone=telephone).first()
        if groupeur is None:
            # 404 plutôt qu'un 200 avec un corps vide : « ce dossier n'existe
            # pas » et « ce dossier existe et attend » sont deux écrans
            # différents, l'interface doit pouvoir les distinguer.
            return Response(
                {"detail": "Aucun dossier à ce numéro."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(MonDossierSerializer(groupeur).data)


class DossierViewSet(viewsets.ReadOnlyModelViewSet):
    """Le côté administrateur : la file d'attente, l'examen, la décision.

    C'est l'écran A2 du cahier des charges (§13.6), que le §10.5 décrivait
    comme tenu « à la main, dans l'admin Django ». Il y reste possible —
    ``admin.py`` enregistre les trois modèles — mais ces routes existent pour
    que l'écran d'administration du produit puisse faire le même travail sans
    passer par une page Django générique.
    """

    serializer_class = DossierSerializer
    permission_classes = [JetonAdmin]

    #: ⚠️ **Aucune classe d'authentification, et c'est délibéré.**
    #:
    #: L'authentification par défaut du projet reconnaît un **acheteur** à son
    #: jeton de session. Elle n'a rien à faire ici : ces routes sont gardées
    #: par un jeton d'administration, qui est un tout autre mécanisme.
    #:
    #: La laisser s'appliquer avait une conséquence concrète et trompeuse : un
    #: appel sans `X-Jeton-Admin` revenait en **401 avec un en-tête
    #: `WWW-Authenticate: Jeton`**, c'est-à-dire en invitant l'appelant à se
    #: connecter comme acheteur — ce qui ne lui ouvrirait évidemment rien. Le
    #: **403** dit la vérité : « je ne vous laisserai pas entrer », pas
    #: « présentez-vous ».
    authentication_classes: list = []

    def get_queryset(self):
        """La file, **du plus ancien au plus récent**.

        L'ordre n'est pas cosmétique : un dossier qui attend depuis six jours
        est un groupeur qui s'en va. Trier du plus récent mettrait en haut
        ceux qui attendent le moins.
        """
        dossiers = Groupeur.objects.prefetch_related(
            "pieces", "decisions_kyc"
        ).order_by("cree_le")

        etat = self.request.query_params.get("etat")
        if etat:
            return dossiers.filter(statut_kyc=etat)
        return dossiers

    @action(detail=True, methods=["post"], url_path="decision")
    def decision(self, request, pk=None):
        """Tranche un dossier, et sort la décision par le canal choisi.

        Deux comportements selon le canal, parce que les deux ne se terminent
        pas au même instant :

        - **courriel** : il part, la décision est marquée annoncée, la réponse
          porte le texte envoyé — l'administrateur voit ce que le groupeur a
          reçu, mot pour mot ;
        - **appel** : la réponse porte **le script à lire**, et la décision
          reste *non annoncée* jusqu'à ``annonce-faite``. Un journal ne doit
          pas prétendre qu'on a téléphoné quand personne n'a décroché (§18.3).
        """
        groupeur = self.get_object()
        entree = TrancherSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        try:
            decision = groupeur.trancher(
                issue=donnees["issue"],
                decide_par=donnees["decide_par"],
                canal=donnees["canal"],
                motif=donnees.get("motif") or None,
                niveau=donnees.get("niveau"),
            )
        except DjangoValidationError as erreur:
            raise ValidationError(
                getattr(erreur, "message_dict", {"detail": erreur.messages})
            )

        try:
            annonce = annoncer(decision)
        except Exception as erreur:  # noqa: BLE001 - voir ci-dessous
            # ⚠️ **``except Exception`` est volontaire ici, et il doit rester
            # large.** La décision est déjà prise et tracée : seule l'annonce a
            # échoué. Laisser remonter l'erreur produirait un 500, et
            # l'administrateur en conclurait que rien n'a été enregistré —
            # alors que le dossier est tranché et a quitté sa file d'attente.
            # Il ne le reprendrait donc jamais, et le groupeur attendrait une
            # réponse qui ne viendrait pas. C'est la panne silencieuse de ce
            # parcours.
            #
            # Les causes sont trop variées pour être listées : fournisseur
            # injoignable, adresse refusée, encodage du terminal, quota
            # dépassé. Ce qui compte n'est pas laquelle, c'est que
            # l'administrateur apprenne **les deux faits à la fois** — décision
            # enregistrée, annonce à refaire. Le dossier reste visible dans le
            # journal, filtré sur « annonce non faite ».
            #
            # On ne revient pas en arrière sur la décision : l'administrateur a
            # bien décidé, il lui reste à joindre la personne autrement — et
            # pour un refus, par téléphone, c'est souvent préférable.
            messages = getattr(erreur, "messages", None)
            return Response(
                {
                    "decision": DecisionSerializer(decision).data,
                    "annonce": False,
                    "probleme": (
                        messages[0]
                        if messages
                        else f"{type(erreur).__name__} : {erreur}"
                    ),
                    "a_refaire": (
                        "La décision est enregistrée, mais le groupeur n'a pas "
                        "été prévenu. Appelez-le au besoin, puis actez "
                        "l'annonce."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "decision": DecisionSerializer(decision).data,
                "annonce": annonce.annonce,
                "canal": annonce.canal,
                "script": annonce.script,
                "sujet": annonce.sujet,
                "corps": annonce.corps,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="annonce-faite")
    def annonce_faite(self, request, pk=None):
        """L'administrateur acte qu'il a réellement téléphoné.

        ⚠️ **À ne cocher qu'après avoir appelé.** C'est une déclaration
        humaine, que rien ne vérifie — et c'est précisément pour ça qu'elle est
        un geste explicite et séparé de la décision, plutôt qu'une case
        pré-cochée dans le formulaire.
        """
        groupeur = self.get_object()
        decision = groupeur.derniere_decision
        if decision is None:
            raise ValidationError(
                {"detail": "Aucune décision à annoncer sur ce dossier."}
            )
        if decision.notifie_le is not None:
            # Idempotent : un double appui ne doit pas réécrire la date de
            # l'annonce, qui est une donnée de journal.
            return Response(DecisionSerializer(decision).data)

        decision.marquer_notifie()
        return Response(DecisionSerializer(decision).data)
