# -*- coding: utf-8 -*-
"""Le compte acheteur : code SMS, session, profil.

**C'est le seul endroit du projet qui délivre une identité.** Tout ce qui lit
les commandes, les demandes et les questions d'un acheteur passe désormais par
le jeton qu'il produit, et non plus par un numéro de téléphone en paramètre
d'URL.

## Le parcours, et où il s'insère

    Il navigue librement — aucun compte (§1.5)
      │
      ├─ il choisit sa quantité, sa taille, son adresse
      │
      └─ il appuie sur « Payer »
            │
            ├─ POST /api/comptes/code/      { telephone }
            ├─ POST /api/comptes/session/   { telephone, code, nom, adresse }
            │        └─▶ { jeton }  ─── gardé par le navigateur
            │
            └─ le paiement **reprend tout seul**, avec le jeton

À la visite suivante, `GET /api/comptes/moi/` avec le jeton rend le profil :
plus de code SMS, plus de saisie d'adresse.

## ⚠️ Ce qui a été retiré, et pourquoi il ne faut pas le remettre

``?telephone=`` **n'identifie plus personne.** Les routes qui l'acceptaient —
commandes, demandes — exigent maintenant le jeton. Le laisser « pour
compatibilité » laisserait la porte ouverte juste à côté de la serrure qu'on
vient de poser : il suffisait de connaître un numéro, et huit chiffres se
devinent.

Le côté groupeur garde ce fonctionnement pour l'instant (``api_groupeur.py``),
et c'est un reste à traiter — pas un choix.

## Où est quoi

Ce fichier ne porte que **les routes**. La mécanique — génération du code,
jeton, reconnaissance de l'acheteur, classe d'authentification DRF — vit dans
``comptes/sessions.py``, et la séparation n'est pas esthétique : DRF importe la
classe d'authentification à la première requête, et si elle habitait ici, cet
import tomberait au milieu du chargement de ce module.
"""

from __future__ import annotations

from django.contrib.auth.hashers import check_password
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import domaine
from .comptes.models import Acheteur, CodeConnexion
from .comptes.sessions import (
    AucunMotDePasse,
    AuthentificationSession,
    CodeSmsNonConfigure,
    ConnexionVerrouillee,
    MotDePasseInvalide,
    acheteur_de_la_requete,
    definir_le_mot_de_passe,
    envoyer_le_code,
    oublier_les_echecs,
    ouvrir_une_session,
    session_de_la_requete,
    valider_le_mot_de_passe,
    verifier_le_mot_de_passe,
)


# ── Les sérialiseurs ────────────────────────────────────────────────────────


class ChampTelephone(serializers.CharField):
    """Un numéro ramené à ``+228XXXXXXXX``. Voir ``domaine.normaliser_telephone``."""

    def to_internal_value(self, data):
        brut = super().to_internal_value(data)
        try:
            return domaine.normaliser_telephone(brut)
        except domaine.NumeroInvalide as erreur:
            raise ValidationError(str(erreur)) from erreur


class DemandeDeCodeSerializer(serializers.Serializer):
    telephone = ChampTelephone(max_length=20)


class OuvertureDeSessionSerializer(serializers.Serializer):
    telephone = ChampTelephone(max_length=20)
    code = serializers.CharField(min_length=4, max_length=4)
    #: Demandé seulement à la création du compte — l'écran le sait.
    nom = serializers.CharField(max_length=120, required=False, allow_blank=True)
    #: Facultatif, et il le reste : voir le modèle ``Acheteur``.
    courriel = serializers.EmailField(required=False, allow_blank=True)
    #: ⚠️ **Rempli par l'inscription, jamais par une reconnexion.**
    #:
    #: L'inscription classique récolte tout en un écran, puis vérifie le numéro
    #: par un code. Le mot de passe voyage donc avec le code, et il n'est posé
    #: **qu'à la création** du compte — la vue refuse un numéro déjà inscrit,
    #: parce qu'accepter reviendrait à faire du code SMS une remise à zéro
    #: silencieuse du mot de passe, là où en changer exige l'ancien.
    mot_de_passe = serializers.CharField(
        trim_whitespace=False, required=False, allow_blank=True
    )
    #: L'adresse que l'acheteur vient de saisir à l'écran de commande.
    quartier = serializers.CharField(
        max_length=40, required=False, allow_blank=True
    )
    repere = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )


class ControleInscriptionSerializer(serializers.Serializer):
    """Le formulaire d'inscription, vérifié **avant** l'envoi du code.

    ⚠️ **Le mot de passe est facultatif ici, et ce n'est pas un relâchement.**
    Le formulaire d'inscription n'en demande plus : il récolte un prénom, un
    numéro et un courriel facultatif, puis vérifie le numéro par SMS. Le mot
    de passe se pose **plus tard, depuis la page Profil**, quand plus rien
    n'est en jeu.

    Le champ reste accepté parce que la route doit pouvoir valider un
    formulaire qui en porte un — et parce que, s'il est fourni, il est
    vérifié pour de bon par `valider_le_mot_de_passe`. Un champ facultatif
    qu'on ne contrôlerait pas serait pire que pas de champ du tout.
    """

    telephone = ChampTelephone(max_length=20)
    nom = serializers.CharField(max_length=120)
    courriel = serializers.EmailField(required=False, allow_blank=True)
    mot_de_passe = serializers.CharField(
        trim_whitespace=False, required=False, allow_blank=True
    )


class ConnexionParMotDePasseSerializer(serializers.Serializer):
    telephone = ChampTelephone(max_length=20)
    #: Pas de ``max_length`` : on ne tronque pas un secret avant de le
    #: comparer. Un mot de passe trop long échoue, il ne devient pas un autre
    #: mot de passe.
    mot_de_passe = serializers.CharField(trim_whitespace=False)


class DefinitionDuMotDePasseSerializer(serializers.Serializer):
    mot_de_passe = serializers.CharField(trim_whitespace=False)
    #: Exigé **seulement** si le compte en a déjà un — voir la vue.
    ancien_mot_de_passe = serializers.CharField(
        trim_whitespace=False, required=False, allow_blank=True
    )


class ProfilSerializer(serializers.ModelSerializer):
    """Ce que l'acheteur sait de lui-même.

    Il porte son numéro — c'est le sien, et l'écran 6 le pré-remplit pour le
    paiement Mobile Money (§6 point 5).

    ⚠️ **``mot_de_passe`` n'est pas dans ``fields``, et ne doit jamais y
    entrer.** C'est une empreinte, pas un secret en clair, mais la publier
    offrirait à qui lit la réponse de quoi l'attaquer hors ligne, sans limite
    d'essais ni verrou — c'est-à-dire en contournant exactement la protection
    que ``verifier_le_mot_de_passe`` met en place. Les champs sont énumérés un
    par un pour cette raison : un ``__all__`` distrait le ferait sortir.

    À la place, ``a_un_mot_de_passe`` — un booléen, qui suffit à l'écran pour
    écrire « Définir » ou « Modifier ».
    """

    a_un_mot_de_passe = serializers.SerializerMethodField()

    class Meta:
        model = Acheteur
        fields = (
            "id",
            "telephone",
            "nom",
            "courriel",
            "quartier",
            "repere",
            "a_un_mot_de_passe",
        )

    def get_a_un_mot_de_passe(self, acheteur: Acheteur) -> bool:
        return bool(acheteur.mot_de_passe)


# ── La vue ──────────────────────────────────────────────────────────────────


class CompteViewSet(viewsets.GenericViewSet):
    """Code SMS, session, profil, déconnexion."""

    serializer_class = ProfilSerializer
    queryset = Acheteur.objects.none()

    #: ⚠️ Les routes ``moi/`` et ``deconnexion/`` en ont besoin ; ``code/`` et
    #: ``session/`` sont forcement anonymes — c'est leur raison d'etre. La
    #: classe **reconnait sans exiger**, donc la declarer pour tout le jeu de
    #: routes ne ferme rien : ce sont les vues qui appellent
    #: ``acheteur_de_la_requete`` qui exigent une session.
    authentication_classes = [AuthentificationSession]

    @action(detail=False, methods=["post"], url_path="code")
    def code(self, request):
        """Envoie un code de connexion.

        Renvoie ``compte_existe`` pour que l'écran sache s'il devra demander le
        nom à l'étape suivante. **Ce n'est pas une fuite d'information
        exploitable** : savoir qu'un numéro a déjà commandé chez nous n'apprend
        rien qu'on puisse monnayer, et l'alternative — demander son nom à
        quelqu'un qui l'a déjà donné — est une friction gratuite au pire moment.
        """
        entree = DemandeDeCodeSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        telephone = entree.validated_data["telephone"]

        try:
            _, clair = envoyer_le_code(telephone)
        except CodeSmsNonConfigure:
            return Response(
                {
                    "detail": (
                        "L'envoi de SMS n'est pas configuré sur ce serveur. "
                        "La connexion est impossible pour l'instant."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "envoye": True,
                "compte_existe": Acheteur.objects.filter(
                    telephone=telephone
                ).exists(),
                # ⚠️ Rempli **uniquement en mode démonstration** — `DEBUG`,
                # ou `SMS_FOURNISSEUR=demonstration` écrit à la main. Hors de
                # là, `envoyer_le_code` a déjà levé si rien ne peut l'envoyer.
                "code_de_demonstration": clair,
            }
        )

    @action(detail=False, methods=["post"], url_path="session")
    def session(self, request):
        """Vérifie le code et délivre un jeton. **Crée le compte s'il manque.**

        ⚠️ **Aucun second bouton « Créer un compte ».** Si le numéro est
        inconnu, le compte se crée ici, et l'écran demande le nom — rien
        d'autre. Faire choisir entre « se connecter » et « s'inscrire » à
        quelqu'un qui veut juste payer est une question dont il n'a pas la
        réponse : il ne sait pas s'il a déjà un compte chez nous.
        """
        entree = OuvertureDeSessionSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        code = (
            CodeConnexion.objects.filter(
                telephone=donnees["telephone"], consomme=False
            )
            .order_by("-cree_le")
            .first()
        )
        if code is None or not code.utilisable:
            raise ValidationError(
                {"code": "Ce code n'est plus valable. Demandez-en un nouveau."}
            )

        if not check_password(donnees["code"], code.code_hache):
            # ⚠️ Le compteur monte **avant** la réponse, et il est enregistré
            # même quand on refuse : sinon trois essais deviendraient une
            # infinité, et quatre chiffres se devinent en dix mille coups.
            code.essais += 1
            code.save(update_fields=["essais"])
            restants = max(0, CodeConnexion.ESSAIS_MAXIMUM - code.essais)
            raise ValidationError(
                {
                    "code": (
                        f"Code incorrect. {restants} essai"
                        f"{'s' if restants > 1 else ''} restant"
                        f"{'s' if restants > 1 else ''}."
                        if restants
                        else "Code incorrect. Demandez-en un nouveau."
                    )
                }
            )

        code.consomme = True
        code.save(update_fields=["consomme"])

        acheteur, cree = Acheteur.objects.get_or_create(
            telephone=donnees["telephone"],
            defaults={
                "nom": donnees.get("nom", ""),
                "courriel": donnees.get("courriel", ""),
                "quartier": donnees.get("quartier", ""),
                "repere": donnees.get("repere", ""),
            },
        )

        mot_de_passe = donnees.get("mot_de_passe") or ""
        if mot_de_passe:
            # ⚠️ **Un mot de passe ne se pose qu'à la création, et le refus
            # ci-dessous n'est pas de la rigidité.**
            #
            # L'accepter sur un compte existant ferait du code SMS une remise
            # à zéro silencieuse du mot de passe. Or en changer exige l'ancien
            # (``moi/mot-de-passe/``), précisément pour qu'un téléphone prêté
            # cinq minutes ne suffise pas à prendre un compte. Laisser cette
            # porte ouverte annulerait cette protection par un autre chemin.
            if not cree:
                raise ValidationError(
                    {
                        "telephone": (
                            "Ce numéro a déjà un compte. Connectez-vous, puis "
                            "changez votre mot de passe depuis votre profil."
                        )
                    }
                )
            try:
                definir_le_mot_de_passe(acheteur, mot_de_passe)
            except MotDePasseInvalide as erreur:
                # Le compte vient d'être créé et son mot de passe est refusé :
                # on ne laisse pas derrière nous un compte à moitié inscrit, que
                # son titulaire ne pourrait plus inscrire puisque le numéro
                # serait désormais « déjà pris ».
                acheteur.delete()
                raise ValidationError(
                    {"mot_de_passe": str(erreur)}
                ) from erreur

        if not cree:
            # ⚠️ **On complète, on n'écrase pas.** Quelqu'un qui se reconnecte
            # depuis un autre appareil n'envoie ni nom ni adresse ; les
            # remplacer par du vide effacerait ce qu'il a déjà donné. Et s'il
            # fournit une nouvelle adresse, elle devient la valeur par défaut :
            # c'est la dernière utilisée qui sert à pré-remplir.
            champs = []
            for champ in ("nom", "quartier", "repere"):
                valeur = donnees.get(champ, "")
                if valeur and valeur != getattr(acheteur, champ):
                    setattr(acheteur, champ, valeur)
                    champs.append(champ)
            if champs:
                acheteur.save(update_fields=champs)

        # ⚠️ **Le code SMS lève le verrou du mot de passe**, et c'est ce qui
        # fait de lui la voie de secours : prouver qu'on a le téléphone vaut
        # mieux que connaître le mot de passe. Sans cette ligne, un acheteur
        # verrouillé devrait attendre quinze minutes **après** s'être
        # reconnecté par SMS avant de pouvoir se servir de son mot de passe.
        oublier_les_echecs(acheteur)

        session = ouvrir_une_session(acheteur)

        return Response(
            {
                "jeton": session.jeton,
                "expire_le": session.expire_le,
                "acheteur": ProfilSerializer(acheteur).data,
                "compte_cree": cree,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="moi")
    def moi(self, request):
        """Le profil, au lancement. **C'est la reconnexion automatique.**

        L'application appelle cette route au démarrage avec le jeton retenu :
        si elle répond, l'acheteur est connecté sans rien faire ; si elle
        répond 401, le jeton est périmé et on l'oublie.
        """
        return Response(ProfilSerializer(acheteur_de_la_requete(request)).data)

    @action(detail=False, methods=["patch"], url_path="moi/profil")
    def modifier_le_profil(self, request):
        """Complète son profil — le nom, l'adresse.

        ⚠️ **Elle existe pour une raison précise de parcours.** Le nom est
        demandé *après* le code, pas avant : prouver qu'on a le téléphone est
        la seule chose qui engage, et un formulaire posé avant cette preuve
        serait rempli par n'importe qui. Mais une fois le code validé, la
        session est déjà ouverte — et le code, consommé. Il faut donc un
        second appel, authentifié celui-là, pour poser le nom.

        **Seuls les champs fournis changent.** Un appel qui ne porte que le
        nom n'efface pas l'adresse : voir le même raisonnement à l'ouverture
        de session.
        """
        acheteur = acheteur_de_la_requete(request)

        # `courriel` est modifiable ici et nulle part ailleurs : il n'est
        # jamais demandé à la création du compte (voir le modèle).
        champs = []
        for champ in ("nom", "courriel", "quartier", "repere"):
            valeur = request.data.get(champ)
            if valeur is not None and valeur != getattr(acheteur, champ):
                setattr(acheteur, champ, valeur)
                champs.append(champ)
        if champs:
            acheteur.save(update_fields=champs)

        return Response(ProfilSerializer(acheteur).data)

    @action(detail=False, methods=["post"], url_path="preparer")
    def preparer(self, request):
        """**Par quelle voie ce numéro peut-il entrer ?** Aucun SMS envoyé.

        C'est la première étape de la feuille de connexion depuis que le compte
        a un mot de passe. Elle existe pour une raison très concrète : sans
        elle, l'écran devait **envoyer un SMS pour savoir quoi afficher**. Un
        acheteur qui a posé un mot de passe et s'en souvient recevait donc un
        code dont il n'avait aucun besoin — une notification inutile, et, le
        jour où un fournisseur sera branché, un SMS facturé à chaque
        connexion.

        ## ⚠️ Ce que cette route divulgue, et pourquoi on l'accepte

        Elle dit si un numéro a un compte chez nous, et s'il a un mot de passe.
        C'est une énumération possible, et il faut l'écrire plutôt que de faire
        comme si elle n'existait pas.

        Trois raisons de la tolérer. ``code/`` divulguait déjà
        ``compte_existe``, donc la surface n'augmente que du booléen de mot de
        passe. Ce que l'attaquant apprend — « ce numéro a commandé chez
        nous » — ne se monnaie pas et ne débloque rien, puisque les deux voies
        restent limitées. Et l'alternative, une réponse uniforme, obligerait
        à afficher les deux champs à tout le monde : un champ de mot de passe
        posé devant quelqu'un qui n'en a jamais défini est une question sans
        réponse, au pire moment du parcours.

        ⚠️ **Ce qui manque vraiment ici, c'est une limite de débit HTTP**, et
        elle n'existe pas encore — ni sur cette route, ni sur ``code/``. Sur
        ``code/`` c'est le plus coûteux : chaque appel enverra un SMS payant.
        À traiter avec le branchement du fournisseur (§18.2).
        """
        entree = DemandeDeCodeSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        acheteur = Acheteur.objects.filter(
            telephone=entree.validated_data["telephone"]
        ).first()

        return Response(
            {
                "compte_existe": acheteur is not None,
                "a_un_mot_de_passe": bool(acheteur and acheteur.mot_de_passe),
            }
        )

    @action(detail=False, methods=["post"], url_path="inscription/controler")
    def controler_l_inscription(self, request):
        """Le formulaire est-il bon ? **Aucun compte créé, aucun SMS envoyé.**

        ## ⚠️ Pourquoi cette route existe

        L'inscription classique récolte nom, numéro, courriel et mot de passe en
        un écran, puis vérifie le numéro par un code SMS. Sans contrôle
        préalable, un mot de passe trop court ne serait refusé qu'**après**
        l'envoi du code : l'acheteur aurait reçu un SMS, serait arrivé sur
        l'écran des quatre cases, et devrait revenir en arrière corriger un
        champ. C'est la façon sûre de faire abandonner une inscription — et,
        le jour où un fournisseur sera branché, de payer un SMS pour rien.

        Elle refuse aussi un numéro **déjà inscrit**, et l'écran envoie alors
        vers la connexion. C'est le prix du modèle classique : deux parcours
        distincts existent, donc il faut dire à l'acheteur lequel est le sien
        plutôt que de le deviner à sa place.

        ⚠️ **Elle ne remplace aucun contrôle.** Tout est revérifié à
        l'ouverture de session : celle-ci est un confort d'écran, et un confort
        d'écran se contourne par un appel direct.
        """
        entree = ControleInscriptionSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        if Acheteur.objects.filter(telephone=donnees["telephone"]).exists():
            raise ValidationError(
                {
                    "telephone": (
                        "Ce numéro a déjà un compte. Connectez-vous plutôt."
                    )
                }
            )

        # Seulement s'il y en a un : le formulaire n'en demande plus.
        if donnees.get("mot_de_passe"):
            try:
                valider_le_mot_de_passe(
                    donnees["mot_de_passe"], donnees["telephone"]
                )
            except MotDePasseInvalide as erreur:
                raise ValidationError({"mot_de_passe": str(erreur)}) from erreur

        return Response({"valide": True})

    @action(detail=False, methods=["post"], url_path="session-mot-de-passe")
    def session_par_mot_de_passe(self, request):
        """La seconde voie d'entrée. **Elle ne crée aucun compte.**

        C'est la différence de fond avec ``session/``, et elle n'est pas
        négociable : un compte naît d'un numéro **prouvé** par un code SMS.
        Laisser un mot de passe créer le compte reviendrait à ouvrir un compte
        sur le numéro de quelqu'un d'autre, et à recevoir à sa place les
        notifications de livraison.

        Les trois refus possibles sont distincts, et mènent l'écran à trois
        endroits différents :

        | Refus | Ce que l'écran doit faire |
        |---|---|
        | Numéro inconnu, ou sans mot de passe | Basculer sur le code SMS |
        | Mot de passe incorrect | Laisser réessayer |
        | Verrouillé | Proposer le code SMS, qui lève le verrou |
        """
        entree = ConnexionParMotDePasseSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        acheteur = Acheteur.objects.filter(
            telephone=donnees["telephone"]
        ).first()

        # ⚠️ **Numéro inconnu et compte sans mot de passe donnent la même
        # réponse**, parce que l'écran doit faire la même chose dans les deux
        # cas : passer au code SMS. C'est aussi ce qui évite de distinguer ici
        # ce que ``preparer/`` dit déjà en une seule requête.
        if acheteur is None or not acheteur.mot_de_passe:
            raise ValidationError(
                {
                    "mot_de_passe": (
                        "Ce numéro n'a pas de mot de passe. "
                        "Demandez un code par SMS."
                    )
                }
            )

        try:
            verifier_le_mot_de_passe(acheteur, donnees["mot_de_passe"])
        except AucunMotDePasse as erreur:
            # Course possible : le mot de passe a été retiré entre les deux
            # lectures. Même réponse que ci-dessus.
            raise ValidationError(
                {
                    "mot_de_passe": (
                        "Ce numéro n'a pas de mot de passe. "
                        "Demandez un code par SMS."
                    )
                }
            ) from erreur
        except ConnexionVerrouillee as erreur:
            raise ValidationError(
                {
                    "mot_de_passe": (
                        f"{erreur} Vous pouvez aussi demander un code par SMS, "
                        "qui fonctionne tout de suite."
                    )
                }
            ) from erreur
        except MotDePasseInvalide as erreur:
            raise ValidationError({"mot_de_passe": str(erreur)}) from erreur

        session = ouvrir_une_session(acheteur)

        return Response(
            {
                "jeton": session.jeton,
                "expire_le": session.expire_le,
                "acheteur": ProfilSerializer(acheteur).data,
                # Jamais : cette voie ne crée pas de compte. La clé est
                # présente pour que l'écran traite les deux réponses de session
                # de la même façon.
                "compte_cree": False,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="moi/mot-de-passe")
    def definir_mon_mot_de_passe(self, request):
        """Poser un mot de passe, ou en changer. **Session obligatoire.**

        ## ⚠️ L'ancien mot de passe est exigé dès qu'il y en a un

        On pourrait s'en passer : la session est déjà ouverte, donc celui qui
        appelle a déjà accès au compte. Mais le jeton vit dans le
        ``localStorage`` et ne s'oublie pas à la fermeture de l'onglet
        (``api/session.ts`` l'assume : « qui a l'appareil déverrouillé a le
        compte »). La différence est celle entre **voir** les commandes de
        quelqu'un et **lui prendre son compte définitivement** : sans l'ancien
        mot de passe, un téléphone prêté cinq minutes suffit à verrouiller le
        titulaire dehors pour de bon.

        À la **première** définition, rien n'est demandé d'autre : la session
        a été ouverte par un code SMS, donc le numéro a été prouvé.
        """
        acheteur = acheteur_de_la_requete(request)

        entree = DefinitionDuMotDePasseSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        if acheteur.mot_de_passe:
            ancien = donnees.get("ancien_mot_de_passe") or ""
            if not ancien:
                raise ValidationError(
                    {
                        "ancien_mot_de_passe": (
                            "Entrez votre mot de passe actuel pour en changer."
                        )
                    }
                )
            try:
                verifier_le_mot_de_passe(acheteur, ancien)
            except (ConnexionVerrouillee, MotDePasseInvalide) as erreur:
                raise ValidationError(
                    {"ancien_mot_de_passe": str(erreur)}
                ) from erreur

        try:
            definir_le_mot_de_passe(acheteur, donnees["mot_de_passe"])
        except MotDePasseInvalide as erreur:
            raise ValidationError({"mot_de_passe": str(erreur)}) from erreur

        return Response(ProfilSerializer(acheteur).data)

    @action(detail=False, methods=["post"], url_path="deconnexion")
    def deconnexion(self, request):
        """Révoque **cette** session, pas toutes celles de l'acheteur.

        Se déconnecter du téléphone d'un ami ne doit pas déconnecter le sien.
        Une révocation globale aurait sa place dans un écran « mes appareils »,
        qui n'existe pas encore.
        """
        session = session_de_la_requete(request)
        if session is not None:
            session.delete()
        # 204 même sans session : se déconnecter deux fois n'est pas une erreur.
        return Response(status=status.HTTP_204_NO_CONTENT)
