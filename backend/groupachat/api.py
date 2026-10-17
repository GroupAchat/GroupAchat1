# -*- coding: utf-8 -*-
"""L'API REST — sérialiseurs et vues.

⚠️ **C'est ici que la règle d'anonymat est tenue ou perdue** (§1.7). Deux
sérialiseurs décrivent la même commande :

- ``CommandeAcheteurSerializer`` — tout, c'est la sienne ;
- ``CommandeGroupeurSerializer`` — **un code et un quartier, rien d'autre**.

Aucun ``fields = "__all__"`` dans ce fichier, et c'est délibéré : c'est par là
que la fuite arrive. Un champ ajouté au modèle doit être ajouté explicitement
ici pour sortir, et les tests vérifient qu'aucune identité ne passe du côté
groupeur.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from rest_framework import parsers, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from . import domaine
from .catalogue.models import Campagne
from .commandes.models import (
    Commande,
    PlafondAtteint,
    enregistrer_paiement,
)
from .comptes.sessions import AuthentificationSession, acheteur_de_la_requete
from .comptes.models import Groupeur
from .echanges.models import (
    Demande,
    Notification,
    Question,
    SignalementQuestion,
)


# ── Catalogue ───────────────────────────────────────────────────────────────


class CampagneSerializer(serializers.ModelSerializer):
    """Ce que l'acheteur voit d'une campagne.

    **Le groupeur n'y apparaît que par son pseudonyme** : ni son nom, ni son
    téléphone, ni son numéro Mobile Money ne sortent par cette API.
    """

    groupeur = serializers.CharField(source="groupeur.pseudonyme", read_only=True)
    acheteurs_confirmes = serializers.IntegerField(read_only=True)
    #: Le denominateur de la barre de progression des cartes (§2.5).
    #:
    #: ⚠️ **Ni plafond ni minimum** : c'est le nombre de personnes que le
    #: groupeur veut reunir, et le depasser est permis. Aucun ecran ne doit
    #: s'en servir pour ecrire « places disponibles » ou « complet ».
    objectif_participants = serializers.IntegerField(read_only=True)
    #: Le pourcentage, **plafonne a 100** cote serveur — voir
    #: ``Campagne.progression`` pour la raison. Servi calcule plutot que
    #: laisse au client : les cartes, le fil, la liste et le detail
    #: l'affichent, et quatre ecrans ne doivent pas refaire le meme arrondi
    #: chacun a sa facon.
    progression = serializers.IntegerField(read_only=True)
    heures_restantes = serializers.IntegerField(read_only=True)
    #: Les questions **publiées** seulement : celles qui attendent la
    #: modération ne sont visibles que de leur auteur (§1.5), et une question
    #: qui finira refusée ne doit pas gonfler le compteur public.
    nombre_de_questions = serializers.IntegerField(read_only=True)
    #: La variante, regroupée pour l'interface : `null` quand il n'y en a pas.
    #:
    #: Deux champs plats (`variante_libelle`, `variante_options`) obligeraient
    #: chaque écran à retester lequel des deux fait foi. Un objet ou `null`
    #: ne laisse qu'une seule question à poser.
    variante = serializers.SerializerMethodField()
    #: Les deux dernieres questions **repondues**, affichees sur l'ecran 3.
    #:
    #: ⚠️ Repondues seulement : une question sans reponse, posee sur la fiche
    #: d'un produit qu'on hesite a acheter, inquiete plutot qu'elle ne
    #: rassure — elle dit que le groupeur ne repond pas.
    questions_recentes = serializers.SerializerMethodField()
    #: Annoncés « à partir de », jamais comme un tarif unique : à ce stade
    #: l'acheteur n'a pas dit où il est.
    frais_livraison_a_partir_de = serializers.SerializerMethodField()

    #: Les dernieres personnes qui ont rejoint — **sans aucun nom**.
    #:
    #: ⚠️ **C'est la seule facon de rendre l'ambiance du marche sans trahir
    #: l'anonymat.** Au marche, on voit qui prend et combien, et c'est ce qui
    #: donne envie d'y aller. Ici on montre **un quartier, une quantite, un
    #: delai** — jamais un nom, jamais un numero, jamais un pseudonyme.
    #:
    #: ⚠️ **Et ce n'est pas la meme chose qu'un avis ou une note.** Il n'y a
    #: rien a ecrire, rien a moderer, rien a falsifier : chaque ligne est une
    #: commande payee. C'est une preuve, pas un temoignage.
    #:
    #: Le quartier seul reste large — Tokoin compte des dizaines de milliers
    #: d'habitants — et c'est deja ce que le groupeur voit de ses acheteurs
    #: (§1.7). La liste est bornee a huit : au-dela elle devient un journal,
    #: et un journal se lit comme une base de donnees.
    participants_recents = serializers.SerializerMethodField()

    #: La grille dégressive, **vide la plupart du temps**.
    #:
    #: ⚠️ **Ce n'est pas un prix barré** (§3). Il n'y a aucun prix de
    #: référence inventé : chaque ligne est un prix réellement pratiqué, et
    #: celui qu'on paie dépend de la quantité qu'on prend. C'est la définition
    #: du prix de gros — le produit lui-même.
    #:
    #: ⚠️ **Le seuil porte sur la quantité de l'acheteur**, jamais sur le
    #: nombre de participants : ce serait un déclencheur collectif, et le prix
    #: ne serait pas connu au moment de payer.
    paliers = serializers.SerializerMethodField()

    class Meta:
        model = Campagne
        fields = (
            "id",
            "titre",
            "description",
            "contenu_part",
            "categorie",
            "prix_part",
            # La liste complete : jusqu'a 4 images et 2 videos, dans l'ordre
            # ou le groupeur les a posees.
            "medias",
            # ⚠️ **Et la couverture a part, qui en est deduite.** Elle n'est
            # pas une redite : les cartes, le fil et les listes n'ont besoin
            # que d'elle, et leur faire parcourir la liste pour retrouver la
            # premiere image serait repeter la meme regle dans cinq ecrans.
            # Le serveur la calcule une fois (voir `Campagne.media`).
            "media",
            "media_alt",
            "date_fin",
            "statut",
            "groupeur",
            "acheteurs_confirmes",
            "objectif_participants",
            "progression",
            "heures_restantes",
            "frais_livraison_a_partir_de",
            "paliers",
            "participants_recents",
            "caracteristiques",
            "variante",
            "quartier_remise",
            "point_remise",
            "remise_le",
            "nombre_de_questions",
            "questions_recentes",
        )

    def get_frais_livraison_a_partir_de(self, _obj) -> str:
        return str(domaine.FRAIS_LIVRAISON_PROVISOIRES)

    def get_participants_recents(self, obj) -> list[dict]:
        """Les huit dernieres commandes payees : quartier, quantite, delai.

        ⚠️ **Aucun champ identifiant ne traverse cette route.** Pas
        d'``acheteur``, pas de ``telephone``, pas de ``code_livraison`` — ce
        dernier identifie une commande precise et sert a la remise. Les trois
        champs servis sont ceux que le groupeur voit deja, moins le code.

        ``only`` n'est pas une optimisation cosmetique : il **garantit** que
        rien d'autre n'est charge, donc que rien d'autre ne peut etre serialise
        par distraction.
        """
        from django.utils import timezone

        from .commandes.models import Commande

        maintenant = timezone.now()
        lignes = (
            Commande.objects.filter(
                campagne=obj, statut__in=Commande.STATUTS_PAYANTS
            )
            .only("quartier", "quantite", "passee_le")
            .order_by("-passee_le")[:8]
        )

        return [
            {
                "quartier": ligne.quartier,
                "quantite": ligne.quantite,
                # En heures : l'ecran decide s'il ecrit « il y a 2 h » ou
                # « hier ». Lui servir une phrase toute faite l'empecherait de
                # la traduire ou de l'abreger selon la place.
                "heures": int(
                    (maintenant - ligne.passee_le).total_seconds() // 3600
                ),
            }
            for ligne in lignes
        ]

    def get_paliers(self, obj) -> list[dict]:
        """Les paliers, du plus petit seuil au plus grand.

        L'ordre vient de ``PalierPrix.Meta.ordering`` : l'écran l'affiche tel
        quel, et n'a donc aucun tri à refaire — une seconde règle de tri dans
        l'interface finirait par diverger de celle du serveur.
        """
        return [
            {"quantite_min": p.quantite_min, "prix_part": str(p.prix_part)}
            for p in obj.paliers.all()
        ]

    def get_questions_recentes(self, campagne: Campagne) -> list[dict]:
        """Les deux dernieres questions-reponses publiques.

        ⚠️ Lit `campagne.recentes`, **pose par le `Prefetch` de la vue** — et
        non `campagne.questions.filter(...)`, qui relancerait une requete par
        ligne du catalogue. Sur une page de 24 campagnes, la difference est de
        24 requetes a zero.
        """
        return [
            {"question": question.texte, "reponse": question.reponse}
            for question in getattr(campagne, "recentes", [])[:2]
        ]

    def get_variante(self, campagne: Campagne) -> dict | None:
        """`{"libelle": …, "options": [...]}`, ou `null`.

        `null` et non un objet vide : l'écran 5 n'affiche le sélecteur que
        s'il y a une variante, et « absent » se teste mieux que « présent mais
        vide ».
        """
        if not campagne.variante_libelle:
            return None
        return {
            "libelle": campagne.variante_libelle,
            "options": campagne.variante_options,
        }


class CampagneViewSet(viewsets.ReadOnlyModelViewSet):
    """Le catalogue. **Lisible sans compte** (§1.5).

    ## ⚠️ Un groupage clôturé n'est plus au catalogue

    La liste ne sert que les groupages **ouverts et dont la date n'est pas
    passée**. Un groupage clôturé, livré ou annulé n'a plus rien à y faire : on
    ne peut plus le rejoindre, donc l'afficher ne fait que trois choses, toutes
    mauvaises — il occupe la place d'un groupage auquel on peut encore
    participer, il donne l'impression d'un catalogue plus fourni qu'il ne
    l'est, et il mène à une fiche dont le bouton est mort.

    ⚠️ **Le filtre est ici, pas dans l'interface.** Un écran qui masquerait les
    clôturés ne protégerait de rien : l'API les servirait encore, et la
    recherche, les filtres et le compteur de résultats les compteraient
    toujours.

    ## Pourquoi `retrieve` ne filtre pas, lui

    La fiche d'un groupage clôturé reste accessible **par son identifiant**.
    C'est voulu : un acheteur qui a payé garde un lien vers ce qu'il a acheté,
    et le lui refuser en 404 lui ferait croire que sa commande a disparu. Il ne
    le trouve simplement plus en parcourant.
    """

    serializer_class = CampagneSerializer

    def get_queryset(self):
        # ⚠️ Les deux `annotate` evitent une requete par ligne a l'affichage
        # d'une liste de 24 campagnes — soit 48 requetes au lieu de 1. Sur la
        # connexion visee par le §5, ce n'est pas une optimisation de confort.
        #
        # `distinct=True` est **indispensable** des qu'il y a deux agregats sur
        # des relations differentes : sans lui, la jointure multiplie les
        # lignes et chaque compteur est gonfle par le cardinal de l'autre.
        queryset = (
            Campagne.objects.select_related("groupeur")
            .prefetch_related(
                # Les questions deja repondues, les plus recentes d'abord, pour
                # l'encart de la fiche produit. Un `Prefetch` nomme plutot
                # qu'un acces direct : il porte **son propre filtre et son
                # propre tri**, que le `related_name` par defaut ne saurait pas
                # exprimer.
                Prefetch(
                    "questions",
                    queryset=Question.objects.filter(
                        etat=Question.Etat.PUBLIEE
                    )
                    .exclude(reponse="")
                    .order_by("-posee_le"),
                    to_attr="recentes",
                )
            )
            .annotate(
                nb_acheteurs=Count(
                    "commandes",
                    filter=Q(commandes__statut__in=Commande.STATUTS_PAYANTS),
                    distinct=True,
                ),
                nb_questions=Count(
                    "questions",
                    filter=Q(questions__etat="publiee"),
                    distinct=True,
                ),
            )
            .order_by("date_fin")
        )

        # ⚠️ **Seulement en liste.** `retrieve` doit continuer de servir un
        # groupage cloture, par son identifiant — voir le docstring de la
        # classe. D'ou ce test sur l'action plutot qu'un filtre pose sur tout
        # le queryset.
        if self.action == "list":
            queryset = queryset.filter(
                statut=Campagne.Statut.OUVERTE, date_fin__gt=timezone.now()
            )

        categorie = self.request.query_params.get("categorie")
        if categorie:
            queryset = queryset.filter(categorie=categorie)

        statut = self.request.query_params.get("statut")
        if statut:
            queryset = queryset.filter(statut=statut)

        recherche = self.request.query_params.get("q")
        if recherche:
            queryset = queryset.filter(
                Q(titre__icontains=recherche) | Q(contenu_part__icontains=recherche)
            )

        return queryset

    @action(detail=True, methods=["get"], url_path="commandes")
    def commandes_du_groupeur(self, request, pk=None):
        """La liste des commandes **telle que le groupeur la voit**.

        ⚠️ Ni nom, ni numéro, ni adresse : un code et un quartier. L'écran 4
        promet à l'acheteur que ses coordonnées ne sont pas communiquées au
        groupeur, et c'est ce point d'entrée qui tient la promesse.
        """
        campagne = self.get_object()
        commandes = campagne.commandes.filter(statut__in=Commande.STATUTS_PAYANTS)
        return Response(CommandeGroupeurSerializer(commandes, many=True).data)


# ── Commandes ───────────────────────────────────────────────────────────────


class CommandeAcheteurSerializer(serializers.ModelSerializer):
    """La commande vue par celui qui l'a passée. Il a droit à tout."""

    campagne_titre = serializers.CharField(source="campagne.titre", read_only=True)
    groupeur = serializers.CharField(
        source="campagne.groupeur.pseudonyme", read_only=True
    )

    class Meta:
        model = Commande
        fields = (
            "id",
            "campagne",
            "campagne_titre",
            "groupeur",
            "quantite",
            "variante",
            "montant_parts",
            "frais_livraison",
            "total",
            "quartier",
            "repere",
            "telephone",
            "code_livraison",
            "statut",
            "passee_le",
        )


class CommandeGroupeurSerializer(serializers.ModelSerializer):
    """La commande vue par le groupeur.

    ⚠️ **Quatre champs, et pas un de plus.** Le code identifie la commande, le
    quartier sert à organiser les tournées ; c'est tout ce dont il a besoin
    pour emballer et compter. Ajouter ``acheteur``, ``repere`` ou ``telephone``
    ici lui permettrait de se constituer un fichier de clients et de les servir
    hors plateforme — autrement dit de nous supprimer du circuit.
    """

    class Meta:
        model = Commande
        fields = ("code_livraison", "quantite", "variante", "montant_parts", "quartier")


class ChampTelephone(serializers.CharField):
    """Un numéro, ramené à ``+228XXXXXXXX`` **dès la validation**.

    ⚠️ **Le faire ici et nulle part ailleurs.** Si la normalisation vivait
    dans les vues, il suffirait d'oublier un appel pour recréer deux comptes
    pour la même personne — et ça ne se verrait qu'au moment où quelqu'un ne
    retrouve plus ses commandes, soit longtemps après. Rattachée au champ,
    elle s'applique partout où le champ est employé.
    """

    def to_internal_value(self, data):
        brut = super().to_internal_value(data)
        try:
            return domaine.normaliser_telephone(brut)
        except domaine.NumeroInvalide as erreur:
            raise ValidationError(str(erreur)) from erreur


class PaiementSerializer(serializers.Serializer):
    """Ce que le client envoie pour payer."""

    campagne = serializers.PrimaryKeyRelatedField(queryset=Campagne.objects.all())
    #: Le numéro **de livraison**, facultatif : celui du compte par défaut.
    #: Ce n'est pas lui qui identifie l'acheteur — c'est la session.
    telephone = ChampTelephone(max_length=20, required=False, allow_blank=True)
    quantite = serializers.IntegerField(min_value=1)
    variante = serializers.CharField(max_length=60, required=False, allow_blank=True)
    quartier = serializers.CharField(max_length=40)
    repere = serializers.CharField(max_length=200)
    #: Générée par le client **avant** l'appel : deux appuis portent la même
    #: clé, et le serveur n'encaisse qu'une fois.
    cle_idempotence = serializers.CharField(max_length=80)


class CommandeViewSet(viewsets.GenericViewSet):
    """Les commandes de l'acheteur, identifié par **sa session**.

    ⚠️ **``?telephone=`` n'identifie plus personne, et ne doit pas revenir.**
    C'était commode et c'était un trou : huit chiffres se devinent, donc
    n'importe qui pouvait lire les commandes de n'importe qui. Le jeton de
    session le remplace — voir ``api_comptes.py`` pour ce que ça change
    exactement.

    Le laisser « pour compatibilité » laisserait la porte ouverte juste à côté
    de la serrure qu'on vient de poser.
    """

    serializer_class = CommandeAcheteurSerializer
    #: ⚠️ **Declaree ici, et non dans ``REST_FRAMEWORK``.**
    #:
    #: Un reglage global aurait ete plus court d'une ligne par vue, et moins
    #: lisible : rien, en ouvrant ce fichier, ne dirait que ces routes
    #: exigent une session. Ici, la dependance se voit a l'endroit ou elle
    #: s'applique.
    #:
    #: Elle sert a deux choses. Elle **reconnait** l'acheteur a son jeton, et
    #: surtout elle fait repondre DRF **401 — et non 403** quand il n'y en a
    #: pas : l'ecran doit rouvrir la feuille de connexion, pas afficher
    #: « acces refuse » a quelqu'un dont la session a simplement expire.
    authentication_classes = [AuthentificationSession]

    def get_queryset(self):
        return (
            Commande.objects.filter(
                acheteur=acheteur_de_la_requete(self.request)
            )
            .select_related("campagne", "campagne__groupeur")
            .order_by("-passee_le")
        )

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="refuser")
    def refuser(self, request, pk=None):
        """L'acheteur refuse le colis à la remise. Écran 9.

        Le bouton « Refuser le colis » était dessiné, visible pendant la seule
        livraison, et **ne faisait rien** : quelqu'un à qui on présentait un
        produit qui n'était pas le sien appuyait dessus et n'obtenait aucune
        trace. C'est le pire endroit du produit pour un bouton mort, parce que
        c'est le moment où la garantie « vous êtes livré, ou remboursé » est
        mise à l'épreuve pour de vrai.

        ⚠️ **Le refus ouvre un litige ; il ne rembourse pas.** La spec de
        l'écran 9 promet exactement ceci : « Group Achat examine votre dossier
        sous 48 h et vous rembourse **si le refus est justifié** ». Et il faut
        l'assumer : le groupeur a déjà retiré son argent à la clôture, donc un
        remboursement automatique se paierait sur notre trésorerie, à chaque
        refus déclaré, vrai ou non.

        ⚠️ **Pas de photo.** La spec en prévoit, et elles seraient utiles pour
        instruire le dossier — mais le stockage de fichiers est reporté au
        déploiement sur le VPS, par décision explicite. Un champ de dépôt qui
        perd les photos serait pire que son absence : l'acheteur croirait
        avoir fourni sa preuve. Le motif et la description partent, la photo
        suivra avec le stockage.
        """
        commande = self.get_object()
        try:
            commande.refuser_le_colis(
                motif=request.data.get("motif", ""),
                description=request.data.get("description", ""),
            )
        except DjangoValidationError as erreur:
            raise ValidationError(
                erreur.message_dict if hasattr(erreur, "message_dict") else erreur.messages
            ) from erreur

        return Response(self.get_serializer(commande).data)

    @action(detail=False, methods=["post"], url_path="payer")
    def payer(self, request):
        """Encaisse une commande.

        **C'est le seul point d'entrée qui exige un compte** (§1.5), et il le
        crée lui-même : un numéro suffit, pas d'inscription séparée. Choisir
        une quantité et saisir une adresse n'engagent rien ; payer engage.

        ⚠️ Le paiement est **simulé** jusqu'à l'agrément d'un agrégateur
        (§18.2). La commande est enregistrée comme si l'encaissement avait
        réussi.
        """
        entree = PaiementSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        # ⚠️ **L'acheteur vient de la session, jamais du corps de la requête.**
        # Accepter un numéro ici laisserait payer au nom d'un autre — et donc
        # faire livrer chez soi une commande inscrite au compte de quelqu'un
        # d'autre.
        acheteur = acheteur_de_la_requete(request)

        # L'adresse qu'il vient de saisir devient son adresse par défaut, pour
        # pré-remplir la prochaine commande. On ne lui a rien demandé de plus :
        # elle était déjà dans le formulaire.
        if (
            donnees["quartier"] != acheteur.quartier
            or donnees["repere"] != acheteur.repere
        ):
            acheteur.quartier = donnees["quartier"]
            acheteur.repere = donnees["repere"]
            acheteur.save(update_fields=["quartier", "repere"])

        try:
            commande, creee = enregistrer_paiement(
                campagne=donnees["campagne"],
                acheteur=acheteur,
                quantite=donnees["quantite"],
                quartier=donnees["quartier"],
                repere=donnees["repere"],
                # Le numéro **de livraison**, qui peut différer de celui du
                # compte : on se fait livrer chez sa sœur sans changer de
                # compte. Par défaut c'est celui du compte.
                telephone=donnees.get("telephone") or acheteur.telephone,
                variante=donnees.get("variante", ""),
                cle_idempotence=donnees["cle_idempotence"],
            )
        except domaine.ZoneNonDesservie as erreur:
            raise ValidationError({"quartier": str(erreur)}) from erreur
        except PlafondAtteint as erreur:
            # ⚠️ Sur `campagne`, et non `detail` : le refus porte sur le
            # groupage, pas sur la saisie de l'acheteur — qui n'a rien fait de
            # mal. L'écran l'affiche à côté du produit, pas sous un champ.
            raise ValidationError({"campagne": str(erreur)}) from erreur
        except DjangoValidationError as erreur:
            raise ValidationError(erreur.message_dict or erreur.messages) from erreur

        return Response(
            CommandeAcheteurSerializer(commande).data,
            # 200 et non 201 sur un rejeu : rien n'a été créé cette fois-ci.
            status=status.HTTP_201_CREATED if creee else status.HTTP_200_OK,
        )


# ── Échanges ────────────────────────────────────────────────────────────────


class QuestionSerializer(serializers.ModelSerializer):
    """Une question publique.

    L'auteur n'apparaît que par son prénom et son initiale : « Akosua D. ».
    """

    auteur = serializers.CharField(source="auteur_affiche", read_only=True)

    class Meta:
        model = Question
        fields = ("id", "campagne", "texte", "auteur", "etat", "posee_le", "reponse")
        read_only_fields = ("etat", "posee_le", "reponse")


class QuestionViewSet(viewsets.ModelViewSet):
    """Les questions publiques. **Lire est libre, écrire demande un compte.**"""

    serializer_class = QuestionSerializer
    http_method_names = ["get", "post", "head", "options"]
    #: ⚠️ **Declaree ici, et non dans ``REST_FRAMEWORK``.**
    #:
    #: Un reglage global aurait ete plus court d'une ligne par vue, et moins
    #: lisible : rien, en ouvrant ce fichier, ne dirait que ces routes
    #: exigent une session. Ici, la dependance se voit a l'endroit ou elle
    #: s'applique.
    #:
    #: Elle sert a deux choses. Elle **reconnait** l'acheteur a son jeton, et
    #: surtout elle fait repondre DRF **401 — et non 403** quand il n'y en a
    #: pas : l'ecran doit rouvrir la feuille de connexion, pas afficher
    #: « acces refuse » a quelqu'un dont la session a simplement expire.
    authentication_classes = [AuthentificationSession]

    def get_queryset(self):
        queryset = Question.objects.select_related("auteur", "campagne")
        campagne = self.request.query_params.get("campagne")
        if campagne:
            queryset = queryset.filter(campagne_id=campagne)
        # Les questions en vérification ne sont visibles que de leur auteur :
        # elles ne sortent pas de la liste publique.
        return queryset.filter(etat=Question.Etat.PUBLIEE)

    def create(self, request, *args, **kwargs):
        # Poser une question demande un compte ; la lire, non (§1.5).
        acheteur = acheteur_de_la_requete(request)

        entree = self.get_serializer(data=request.data)
        entree.is_valid(raise_exception=True)
        try:
            question = Question.objects.create(
                campagne=entree.validated_data["campagne"],
                auteur=acheteur,
                texte=entree.validated_data["texte"],
            )
        except DjangoValidationError as erreur:
            raise ValidationError(erreur.message_dict or erreur.messages) from erreur

        return Response(
            self.get_serializer(question).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="signaler")
    def signaler(self, request, pk=None):
        """Signale une question déjà publiée. §15, niveau 3.

        L'icône de drapeau de l'écran 10 n'allait nulle part : le filtre
        automatique du §15 couvre les niveaux 1 et 2, et le niveau 3 — **un
        humain, après publication** — n'avait aucun moyen d'être saisi. Un
        message qui passe le filtre et qu'un lecteur voit pourtant comme un
        numéro de téléphone déguisé restait donc en ligne sans recours.

        ⚠️ **La question reste publiée.** Dépublier sur signalement donnerait
        à n'importe qui le pouvoir de faire taire n'importe qui — il
        suffirait de signaler la question gênante pour l'effacer du seul
        canal public du produit. On remplit une file ; un administrateur
        tranche dans l'admin Django, comme le prévoit le §15.

        ⚠️ **Elle répond 200 et non 201 sur un second signalement du même
        lecteur.** La contrainte d'unicité l'empêche d'en déposer deux, mais
        le lui dire par une erreur serait absurde : de son point de vue le
        geste a réussi la première fois, et il ne doit pas croire que son
        signalement n'a pas été pris.
        """
        acheteur = acheteur_de_la_requete(request)
        question = self.get_object()

        motif = request.data.get("motif")
        if motif not in SignalementQuestion.Motif.values:
            raise ValidationError(
                {
                    "motif": "Choisissez un motif parmi ceux proposés.",
                }
            )

        _, cree = SignalementQuestion.objects.get_or_create(
            question=question, auteur=acheteur, defaults={"motif": motif}
        )
        return Response(
            {
                "signale": True,
                # Ce que l'écran affiche : on ne promet pas une suppression,
                # on promet un examen.
                "message": (
                    "Votre signalement est enregistré. Group Achat examine ce "
                    "message."
                ),
            },
            status=status.HTTP_201_CREATED if cree else status.HTTP_200_OK,
        )


class NotificationSerializer(serializers.ModelSerializer):
    """Ce que la cloche affiche, et de quoi ouvrir le bon écran au clic."""

    #: ⚠️ **Le titre du groupage n'est pas dans ``corps``.** Le corps est figé
    #: à l'envoi ; ce champ-ci est relu à chaque affichage et sert à la ligne
    #: secondaire de la liste. Les deux ne disent pas la même chose : si le
    #: groupeur renomme son groupage, le corps garde l'ancien nom — qui est ce
    #: qu'on a réellement annoncé ce jour-là — et cette ligne montre le nom
    #: actuel, qui est celui qu'on retrouvera au catalogue.
    campagne_titre = serializers.CharField(
        source="campagne.titre", read_only=True, default=""
    )
    lue = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "nature",
            "titre",
            "corps",
            "campagne",
            "campagne_titre",
            "commande",
            "question",
            "creee_le",
            "lue",
        )

    def get_lue(self, notification) -> bool:
        return notification.lue_le is not None


class NotificationViewSet(viewsets.ViewSet):
    """La cloche de l'acheteur.

    ## Pourquoi cette route existe

    La cloche était dessinée dans les deux en-têtes acheteur, **pastille
    comprise**, et ne faisait rien : le compteur était la constante ``1``
    écrite dans le routeur. Elle promettait donc en permanence une
    information qui n'existait pas.

    ## ⚠️ Lire ses notifications exige une session

    Elles portent ce qu'on a commandé et combien on a été remboursé. Un
    paramètre d'URL — un numéro de téléphone, un identifiant — rendrait la
    liste devinable, et c'est le trou qu'on vient de fermer ailleurs
    (``api_comptes.py``). La réponse est **401 et non 403** quand la session
    manque : l'écran doit rouvrir la feuille de connexion, pas afficher
    « accès refusé » à quelqu'un dont la session a simplement expiré.
    """

    authentication_classes = [AuthentificationSession]
    serializer_class = NotificationSerializer

    def list(self, request):
        """Ses cinquante dernières notifications, les plus récentes d'abord.

        ⚠️ **Pas de pagination, une borne.** Une cloche ne se parcourt pas :
        on la regarde pour voir ce qu'on a manqué, et ce qui a plus de
        cinquante notifications d'âge ne sera pas lu. Le plafond évite surtout
        qu'un compte ancien fasse descendre une liste de plusieurs centaines
        de lignes sur un forfait de données limité (§5).
        """
        acheteur = acheteur_de_la_requete(request)
        notifications = (
            Notification.objects.filter(destinataire=acheteur)
            .select_related("campagne")
            .order_by("-creee_le")[:50]
        )
        return Response(NotificationSerializer(notifications, many=True).data)

    @action(detail=False, methods=["post"], url_path="tout-lu")
    def tout_lu(self, request):
        """Marque tout comme lu — c'est le seul geste de lecture offert.

        ⚠️ **Tout, et pas une par une.** Marquer chaque ligne séparément
        demanderait un appel par notification à l'ouverture du panneau, ce qui
        est exactement le contraire de ce qu'on veut sur un réseau lent. Et le
        geste réel est celui-là : on ouvre la cloche, on voit, c'est lu.

        Renvoie le nombre de lignes qui viennent de passer à lu, ce qui permet
        à l'écran de ne rien faire quand il n'y avait rien.
        """
        acheteur = acheteur_de_la_requete(request)
        lues = Notification.objects.filter(
            destinataire=acheteur, lue_le__isnull=True
        ).update(lue_le=timezone.now())
        return Response({"lues": lues, "non_lues": 0})


class DemandeSerializer(serializers.ModelSerializer):
    """Ce que l'écran 11 envoie et ce que l'écran 12 relit.

    ⚠️ **``photo`` n'est pas dans ``fields``**, et c'est voulu : les octets ne
    doivent jamais partir dans une liste JSON. Cent demandes sérialisées
    feraient trente mégaoctets de réponse, et le navigateur n'en a pas
    l'usage — il veut une adresse d'image, qu'il demandera si elle entre dans
    le cadre. D'où ``photo_url``, qui ne pèse rien.
    """

    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Demande
        fields = (
            "id",
            "produit",
            "quantite",
            "quartier",
            "budget_maximum",
            "precisions",
            "photo_url",
            "statut",
            "campagne",
            "deposee_le",
        )
        read_only_fields = ("statut", "campagne", "deposee_le")

    def get_photo_url(self, demande: Demande) -> str | None:
        """L'adresse de la photo, ou ``None`` s'il n'y en a pas.

        ``photo_type`` sert de test de présence : le lire ne charge pas les
        octets, contrairement à ``demande.photo``.
        """
        if not demande.photo_type:
            return None
        requete = self.context.get("request")
        chemin = f"/api/demandes/{demande.pk}/photo/"
        return requete.build_absolute_uri(chemin) if requete else chemin


class DemandeViewSet(viewsets.ModelViewSet):
    """Les demandes de produit. La demande crée l'offre."""

    serializer_class = DemandeSerializer
    http_method_names = ["get", "post", "head", "options"]
    #: ⚠️ **Declaree ici, et non dans ``REST_FRAMEWORK``.**
    #:
    #: Un reglage global aurait ete plus court d'une ligne par vue, et moins
    #: lisible : rien, en ouvrant ce fichier, ne dirait que ces routes
    #: exigent une session. Ici, la dependance se voit a l'endroit ou elle
    #: s'applique.
    #:
    #: Elle sert a deux choses. Elle **reconnait** l'acheteur a son jeton, et
    #: surtout elle fait repondre DRF **401 — et non 403** quand il n'y en a
    #: pas : l'ecran doit rouvrir la feuille de connexion, pas afficher
    #: « acces refuse » a quelqu'un dont la session a simplement expire.
    authentication_classes = [AuthentificationSession]

    def get_queryset(self):
        # Comme les commandes : la session, jamais un numéro en URL.
        return Demande.objects.filter(acheteur=acheteur_de_la_requete(self.request))

    #: ⚠️ **Nécessaire pour recevoir la photo.** Sans ``MultiPartParser``, DRF
    #: ne lit que du JSON et ``request.FILES`` reste vide : le dépôt
    #: répondrait 201 en jetant la photo en silence, ce qui est pire qu'une
    #: erreur. ``JSONParser`` reste, parce qu'une demande sans photo n'a
    #: aucune raison de passer en multipart.
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def create(self, request, *args, **kwargs):
        acheteur = acheteur_de_la_requete(request)
        entree = self.get_serializer(data=request.data)
        entree.is_valid(raise_exception=True)

        octets, nature = self._lire_la_photo(request)

        demande = Demande.objects.create(
            acheteur=acheteur,
            photo=octets,
            photo_type=nature,
            **entree.validated_data,
        )
        return Response(
            self.get_serializer(demande).data, status=status.HTTP_201_CREATED
        )

    @staticmethod
    def _lire_la_photo(request) -> tuple[bytes | None, str]:
        """Valide le fichier joint. Facultatif ; invalide, il est **refusé**.

        ⚠️ **Deux contrôles, et le second est le vrai.** La taille d'abord,
        parce qu'on refuse avant de lire. La **signature** ensuite : le
        ``Content-Type`` du formulaire est déclaré par le client, donc
        n'importe quel fichier peut se présenter comme une image. Seuls les
        premiers octets ne mentent pas.

        Une photo invalide n'est pas ignorée en silence : l'acheteur a attendu
        son téléversement sur un forfait limité, et le laisser croire sa
        demande partie avec la photo alors qu'elle est partie sans serait un
        mensonge que rien à l'écran ne corrigerait.
        """
        fichier = request.FILES.get("photo")
        if fichier is None:
            return None, ""

        if fichier.size > domaine.PHOTO_DEMANDE_MAX_OCTETS:
            maximum = domaine.PHOTO_DEMANDE_MAX_OCTETS // 1024
            raise ValidationError(
                {
                    "photo": (
                        f"La photo dépasse {maximum} ko. "
                        "Choisissez-en une plus légère."
                    )
                }
            )

        octets = fichier.read()
        nature = domaine.nature_de_la_photo(octets)
        if nature is None:
            raise ValidationError(
                {"photo": "Ce fichier n'est pas une image JPEG, PNG ou WebP."}
            )
        return octets, nature

    @action(detail=True, methods=["get"])
    def photo(self, request, pk=None):
        """Sert les octets de la photo.

        ⚠️ **``get_object`` passe par ``get_queryset``**, qui filtre sur
        l'acheteur de la session : la photo d'un autre renvoie donc 404, et
        non 403. C'est la réponse correcte — répondre « interdit »
        confirmerait que la demande existe.
        """
        demande = self.get_object()
        if not demande.photo_type:
            raise NotFound("Cette demande n'a pas de photo.")

        reponse = HttpResponse(bytes(demande.photo), content_type=demande.photo_type)
        # Les octets ne changent jamais : une demande déposée ne se modifie
        # pas. Un cache long est donc sans risque, et il compte sur un forfait
        # limité — la vignette de l'écran 12 ne se retélécharge pas à chaque
        # visite. `private` parce que la réponse est propre à une session.
        reponse["Cache-Control"] = "private, max-age=86400"
        return reponse


# ── Groupeurs ───────────────────────────────────────────────────────────────


class GroupeurPublicSerializer(serializers.ModelSerializer):
    """Ce que l'acheteur peut savoir d'un groupeur : son pseudonyme.

    ⚠️ Pas de nom, pas de quartier, pas de date d'inscription, pas de photo.
    Le §1.7 est explicite sur ce que cette fiche ne doit **pas** contenir, et la
    liste est courte parce que le pseudonyme suffit.
    """

    class Meta:
        model = Groupeur
        fields = ("id", "pseudonyme")
