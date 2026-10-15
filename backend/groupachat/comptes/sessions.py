# -*- coding: utf-8 -*-
"""La mécanique de session : code SMS, **mot de passe**, jeton, reconnaissance.

## Deux voies pour entrer, et elles ne sont pas interchangeables

| | Code SMS | Mot de passe |
|---|---|---|
| Disponible | **Toujours** | Seulement s'il en a posé un |
| Crée le compte | **oui** | non, jamais |
| Limite | 3 essais par code | 5 échecs, puis 15 minutes |
| Verrouillable | non | **oui** |

⚠️ **Le code SMS reste la voie de récupération, et c'est structurant.** Un
mot de passe oublié ou verrouillé ne ferme jamais un compte : il reste le SMS.
C'est aussi ce qui autorise un verrou sévère sur le mot de passe sans risquer
d'enfermer quelqu'un dehors — et ce qui évite d'avoir à écrire un parcours
« mot de passe oublié », un formulaire, un lien à durée de vie et un courriel
que la moitié du public ne consulte pas.

Séparé de ``api_comptes.py``, qui porte les *routes*. Ce n'est pas un découpage
esthétique : ``settings.REST_FRAMEWORK`` désigne la classe d'authentification
par son chemin, et DRF l'importe **à la première requête**. Si elle vivait dans
le module des vues, cet import tomberait au milieu du chargement de ce même
module — qui est en train d'importer DRF pour définir ses sérialiseurs — et
Python rendrait un module à moitié construit, où la classe n'existe pas encore.

Ici, ce fichier ne définit aucune vue et aucun sérialiseur : il n'importe de
DRF que ``BaseAuthentication``, et la boucle n'existe pas.
"""

from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ValidationDjango
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import NotAuthenticated

from .models import Acheteur, CodeConnexion, SessionAcheteur


class CodeSmsNonConfigure(Exception):
    """Pas de fournisseur SMS, et on n'est pas en développement."""


def mode_demonstration() -> bool:
    """Le code est-il fixe et montré à l'écran ?

    Vrai dans deux cas, et deux seulement :

    - ``DEBUG`` — on développe ;
    - ``SMS_FOURNISSEUR=demonstration``, **écrit à la main** dans le fichier
      d'environnement.

    ## Pourquoi ce second cas existe

    Parce que sans lui, une démonstration déployée ne peut prendre aucune
    commande. Le conteneur tourne avec ``DEBUG=0`` — c'est le bon réglage, il
    évite d'exposer les traces et les variables d'environnement — et aucun
    fournisseur SMS n'est branché, donc la connexion répondrait 503. Un jury
    verrait un catalogue qu'on ne peut pas acheter.

    ⚠️ **C'est un opt-in, pas un repli.** Il faut écrire le mot
    ``demonstration`` dans ``.env``, et il reste visible dans la configuration
    de déploiement. La différence avec un défaut silencieux est toute la
    différence : un défaut part en production par oubli, une valeur écrite à
    la main y part par décision.
    """
    if settings.DEBUG:
        return True
    return getattr(settings, "SMS_FOURNISSEUR", "") == "demonstration"


def envoyer_le_code(telephone: str) -> tuple[CodeConnexion, str | None]:
    """Crée un code, et le « transmet ».

    Renvoie ``(code, valeur_en_clair)``. ``valeur_en_clair`` n'est rempli
    **qu'en mode démonstration**, pour que l'écran puisse l'afficher au lieu de
    laisser chercher.

    ⚠️ **Sans fournisseur SMS et hors démonstration, cette fonction lève.**
    C'est délibéré et c'est le point le plus important de ce fichier : un code
    fixe mis en ligne pour de vrai donnerait à n'importe qui le compte de
    n'importe quel numéro. Un réglage de développement ne doit pas pouvoir
    partir en production par simple oubli — il faut que quelque chose
    l'arrête, et c'est ici.
    """
    if not getattr(settings, "SMS_FOURNISSEUR", "") and not settings.DEBUG:
        raise CodeSmsNonConfigure

    if mode_demonstration():
        # Fixe, et l'écran le dit. Un code aléatoire qu'on ne recevrait nulle
        # part rendrait l'application inutilisable.
        clair = getattr(settings, "CODE_SMS_DEMONSTRATION", "1234")
    else:
        # `secrets` et non `random` : ce nombre garde un compte.
        clair = f"{secrets.randbelow(10_000):04d}"

    # Les codes précédents de ce numéro meurent : sinon, en redemander un
    # laisserait les anciens valables, et multiplierait les codes en vol.
    CodeConnexion.objects.filter(telephone=telephone, consomme=False).update(
        consomme=True
    )

    code = CodeConnexion.objects.create(
        telephone=telephone,
        code_hache=make_password(clair),
        expire_le=timezone.now() + timedelta(minutes=CodeConnexion.DUREE_MINUTES),
    )

    # ⚠️ C'est ici que partira le SMS, le jour où un fournisseur est branché.
    # Rien n'est envoyé aujourd'hui, et l'API le dit à l'appelant plutôt que de
    # laisser croire le contraire.

    return code, clair if mode_demonstration() else None


def ouvrir_une_session(acheteur: Acheteur) -> SessionAcheteur:
    """Délivre un jeton.

    ``token_urlsafe(32)`` : 256 bits tirés par ``secrets``. Ce n'est pas de la
    coquetterie — c'est précisément ce qui le distingue du numéro de téléphone
    qu'il remplace, lequel se devine en huit chiffres.
    """
    return SessionAcheteur.objects.create(
        acheteur=acheteur,
        jeton=secrets.token_urlsafe(32),
        expire_le=timezone.now() + timedelta(days=SessionAcheteur.DUREE_JOURS),
    )


def session_de_la_requete(request) -> SessionAcheteur | None:
    """Lit l'en-tête ``Authorization: Jeton <…>`` et retrouve la session.

    Renvoie ``None`` plutôt que de lever : on navigue sans compte (§1.5), et
    c'est à chaque point d'entrée de décider s'il l'exige.
    """
    entete = request.headers.get("Authorization", "")
    if not entete.startswith("Jeton "):
        return None

    jeton = entete[len("Jeton ") :].strip()
    if not jeton:
        return None

    session = (
        SessionAcheteur.objects.select_related("acheteur").filter(jeton=jeton).first()
    )
    if session is None or not session.valide:
        return None

    session.prolonger()
    return session


class AuthentificationSession(BaseAuthentication):
    """Reconnaît l'acheteur à son jeton. Déclarée dans ``REST_FRAMEWORK``.

    ## Pourquoi une classe DRF plutôt qu'un simple appel dans chaque vue

    Pour une raison précise : **sans elle, DRF répond 403 au lieu de 401.** Il
    ne sait émettre un 401 que si une classe d'authentification lui fournit
    l'en-tête ``WWW-Authenticate``, et à défaut il suppose que l'appelant est
    identifié mais sans droits.

    La différence n'est pas théorique, l'interface fait deux choses
    différentes :

    | | Ce que l'écran doit faire |
    |---|---|
    | **401** — je ne sais pas qui vous êtes | Rouvrir la feuille de connexion |
    | **403** — je sais, et c'est non | Afficher un refus |

    Un acheteur dont la session a expiré doit retomber sur la feuille, pas sur
    « accès refusé » — sinon il n'a aucun moyen de revenir, et il croit avoir
    perdu son compte.

    ⚠️ **Elle n'exige rien par elle-même.** Un jeton absent laisse passer la
    requête en anonyme, parce que le catalogue se lit sans compte (§1.5). Ce
    sont les points d'entrée qui engagent quelque chose — payer, poser une
    question, lire ses commandes — qui appellent ``acheteur_de_la_requete``.
    """

    #: Le schéma annoncé dans ``WWW-Authenticate``. C'est lui qui transforme le
    #: 403 de DRF en 401.
    mot_cle = "Jeton"

    def authenticate(self, request):
        session = session_de_la_requete(request)
        if session is None:
            return None
        return (session.acheteur, session)

    def authenticate_header(self, request) -> str:
        return self.mot_cle


def acheteur_de_la_requete(request) -> Acheteur:
    """L'acheteur connecté, ou un 401.

    Lit ``request.user``, que ``AuthentificationSession`` a rempli. Le relire
    ici plutôt que de refaire le travail évite une seconde requête en base par
    appel — DRF a déjà résolu la session.
    """
    acheteur = getattr(request, "user", None)
    if not isinstance(acheteur, Acheteur):
        raise NotAuthenticated(
            "Votre session a expiré. Reconnectez-vous avec votre numéro."
        )
    return acheteur


# ── Le mot de passe ─────────────────────────────────────────────────────────
#
# Il ne remplace pas le code SMS, il s'y ajoute : voir l'en-tête du module.

#: Cinq échecs **consécutifs**, puis la voie du mot de passe se ferme.
#:
#: Cinq et non trois, à la différence de `CodeConnexion.ESSAIS_MAXIMUM` : un
#: code à quatre chiffres qu'on vient de recevoir se tape juste, alors qu'un
#: mot de passe se tape de mémoire, sur un clavier de téléphone, parfois avec
#: la casse qui s'en mêle. Trois essais pour un mot de passe produiraient
#: surtout des verrous chez des gens qui connaissent le leur.
ECHECS_AVANT_VERROU = 5

#: La durée du verrou. Quinze minutes suffisent à rendre une attaque par
#: énumération inutile — cinq essais par quart d'heure, soit moins de cinq
#: cents par jour contre un espace de huit caractères — sans transformer une
#: faute de frappe répétée en soirée perdue. Et le code SMS reste ouvert
#: pendant tout ce temps.
DUREE_VERROU_MINUTES = 15


class MotDePasseInvalide(Exception):
    """Le mot de passe proposé ne convient pas. Le message est pour l'écran."""


class ConnexionVerrouillee(Exception):
    """Trop d'échecs. Porte le nombre de minutes à attendre."""

    def __init__(self, minutes: int) -> None:
        self.minutes = minutes
        super().__init__(f"Trop d'essais. Réessayez dans {minutes} minutes.")


class AucunMotDePasse(Exception):
    """Ce compte n'en a pas posé. **À ne pas confondre avec un échec.**

    Les deux cas envoient l'acheteur à des endroits différents : celui-ci vers
    « demandez un code par SMS », l'autre vers « réessayez ». Répondre « mot de
    passe incorrect » à quelqu'un qui n'en a jamais défini le laisserait
    chercher un secret qui n'existe pas.
    """


def valider_le_mot_de_passe(clair: str, telephone: str) -> None:
    """Lève ``MotDePasseInvalide`` si le mot de passe ne convient pas.

    ## Ce qui est vérifié, et par qui

    La longueur passe par ``validate_password``, donc par
    ``AUTH_PASSWORD_VALIDATORS`` du projet — aujourd'hui le seul
    ``MinimumLengthValidator``, soit huit caractères. **On n'invente pas une
    règle ici** : la configuration du projet est le seul endroit où cette
    décision doit vivre, et ses messages sont déjà traduits en français.

    Elle prend un **numéro** et non un acheteur, parce qu'elle est appelée
    avant que le compte existe : l'inscription contrôle le formulaire avant
    d'envoyer le code SMS. Découvrir qu'un mot de passe est trop court *après*
    avoir reçu un code est la façon sûre de faire abandonner une inscription.

    ⚠️ **Un mot de passe entièrement numérique reste donc accepté**, parce que
    ``NumericPasswordValidator`` n'est pas dans la liste du projet. C'est
    volontaire et c'est un arbitrage, pas un oubli : sur un clavier de
    téléphone d'entrée de gamme (§5), exiger des lettres et des chiffres
    pousse à écrire le mot de passe sur un papier. Huit chiffres valent dix
    millions de combinaisons, et la voie est verrouillée au bout de cinq
    essais — l'énumération ne passe pas. Si tu veux durcir, la bonne
    modification est d'ajouter le validateur dans ``settings.py``, pas d'écrire
    un test de plus ici.

    S'y ajoute une seule règle que les validateurs de Django ne peuvent pas
    connaître : **le numéro de téléphone est refusé**. C'est le premier mot de
    passe que choisirait quelqu'un à qui on demande huit caractères, et c'est
    exactement la valeur que l'attaquant possède déjà, puisqu'elle est
    l'identifiant du compte.
    """
    try:
        validate_password(clair)
    except ValidationDjango as erreur:
        raise MotDePasseInvalide(" ".join(erreur.messages)) from erreur

    #: Les chiffres seuls, pour que `90123456` soit refusé aussi bien que
    #: `+22890123456` — c'est le même secret, écrit autrement.
    chiffres_du_numero = "".join(c for c in telephone if c.isdigit())
    chiffres_proposes = "".join(c for c in clair if c.isdigit())
    if chiffres_proposes and chiffres_proposes in chiffres_du_numero:
        raise MotDePasseInvalide(
            "Votre numéro de téléphone ne peut pas servir de mot de passe : "
            "c'est déjà l'identifiant de votre compte."
        )


def definir_le_mot_de_passe(acheteur: Acheteur, clair: str) -> None:
    """Valide, hache, enregistre — et lève le verrou s'il y en avait un.

    ⚠️ **Le compteur d'échecs est remis à zéro.** Quelqu'un qui vient de poser
    un nouveau mot de passe depuis une session déjà ouverte ne doit pas rester
    verrouillé sur l'ancien : le verrou protège contre celui qui devine, pas
    contre le titulaire du compte.
    """
    valider_le_mot_de_passe(clair, acheteur.telephone)
    acheteur.mot_de_passe = make_password(clair)
    acheteur.echecs_connexion = 0
    acheteur.bloque_jusqu_a = None
    acheteur.save(
        update_fields=["mot_de_passe", "echecs_connexion", "bloque_jusqu_a"]
    )


def oublier_les_echecs(acheteur: Acheteur) -> None:
    """Remise à zéro après une connexion réussie, **quelle que soit la voie**.

    Appelée aussi après une connexion par code SMS, et c'est ce qui fait du
    code la voie de secours : un acheteur verrouillé pour avoir mal tapé son
    mot de passe reprend la main avec un SMS, sans attendre les quinze
    minutes. Prouver qu'on a le téléphone vaut mieux que le mot de passe.
    """
    if acheteur.echecs_connexion or acheteur.bloque_jusqu_a:
        acheteur.echecs_connexion = 0
        acheteur.bloque_jusqu_a = None
        acheteur.save(update_fields=["echecs_connexion", "bloque_jusqu_a"])


def verifier_le_mot_de_passe(acheteur: Acheteur, clair: str) -> None:
    """Ne rend rien, et lève dans les trois cas de refus.

    L'ordre des trois contrôles n'est pas indifférent :

    1. **le verrou d'abord.** Le vérifier après coup laisserait un attaquant
       continuer d'éprouver des mots de passe pendant le blocage, ce qui
       viderait le verrou de son sens ;
    2. **l'absence de mot de passe ensuite**, pour renvoyer vers le SMS plutôt
       que vers un secret inexistant ;
    3. **l'empreinte enfin.**
    """
    maintenant = timezone.now()

    if acheteur.bloque_jusqu_a:
        if acheteur.bloque_jusqu_a > maintenant:
            restantes = acheteur.bloque_jusqu_a - maintenant
            # Arrondi au supérieur : annoncer « 0 minute » à quelqu'un qui
            # doit encore attendre quarante secondes le ferait réessayer pour
            # rien.
            minutes = max(1, -(-int(restantes.total_seconds()) // 60))
            raise ConnexionVerrouillee(minutes)

        # ⚠️ **Le blocage est fini : on repart de zéro, et les deux champs
        # doivent bouger ensemble.**
        #
        # Garder le compteur à 5 aurait un effet qu'on ne voit pas en le
        # lisant : la première faute de frappe suivante ferait 6, donc
        # re-verrouillerait aussitôt pour un quart d'heure. Quelqu'un ayant
        # été verrouillé une fois n'aurait plus jamais droit à *un seul* essai
        # manqué, pour toute la vie du compte.
        #
        # Et laisser `bloque_jusqu_a` sur une date passée est pire encore :
        # elle reste vraie au sens booléen, donc le test placé après
        # l'incrémentation plus bas la prendrait pour un verrou neuf et
        # annoncerait un blocage que personne n'a posé.
        acheteur.echecs_connexion = 0
        acheteur.bloque_jusqu_a = None
        acheteur.save(update_fields=["echecs_connexion", "bloque_jusqu_a"])

    if not acheteur.mot_de_passe:
        raise AucunMotDePasse

    if not check_password(clair, acheteur.mot_de_passe):
        # ⚠️ Le compteur monte **et il est enregistré**, même si l'appelant
        # s'apprête à répondre une erreur. Le même raisonnement que pour
        # `CodeConnexion.essais` : sans écriture, cinq essais deviennent une
        # infinité.
        acheteur.echecs_connexion += 1
        champs = ["echecs_connexion"]
        if acheteur.echecs_connexion >= ECHECS_AVANT_VERROU:
            acheteur.bloque_jusqu_a = maintenant + timedelta(
                minutes=DUREE_VERROU_MINUTES
            )
            champs.append("bloque_jusqu_a")
        acheteur.save(update_fields=champs)

        if acheteur.bloque_jusqu_a:
            raise ConnexionVerrouillee(DUREE_VERROU_MINUTES)
        raise MotDePasseInvalide("Mot de passe incorrect.")

    oublier_les_echecs(acheteur)
