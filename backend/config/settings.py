# -*- coding: utf-8 -*-
"""Réglages de Group Achat.

**PostgreSQL dès que ``DATABASE_URL`` est renseignée**, y compris pour les
tests. Le cahier des charges l'impose, et le moteur de test doit être celui de
la production : SQLite et PostgreSQL diffèrent sur les transactions, les
contraintes et les types, et une suite verte sur l'un peut échouer sur l'autre.

**SQLite reste le secours**, quand aucune ``DATABASE_URL`` n'est définie. C'est
ce qui permet de cloner le dépôt et de lancer les tests sans rien installer —
mais ce n'est pas la configuration de référence, et une suite qui n'aurait
jamais tourné sur PostgreSQL ne prouverait pas grand-chose.

Pour forcer SQLite malgré une ``DATABASE_URL`` présente — par exemple pour un
essai rapide hors ligne — mettre ``DJANGO_FORCER_SQLITE=1``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# ── La configuration vient d'un seul fichier ────────────────────────────────
#
# `.env` **a la racine du depot**, et nulle part ailleurs. C'est le meme
# fichier que lisent Docker Compose et Vite (`envDir: ".."` dans les deux
# configurations du front).
#
# ⚠️ **Il y en avait trois**, et c'etait le probleme : `backend/.env` pour
# Django, `frontend/.env.local` pour Vite, `.env` pour Compose. Les memes
# valeurs recopiees trois fois, sans rien pour garantir qu'elles concordent —
# un `DATABASE_URL` corrige dans l'un et oublie dans l'autre est une panne qui
# ne se voit qu'au deploiement. Et `CORS_ORIGINES` devait rester d'accord avec
# `VITE_API_URL`, qui vivait dans un autre fichier.
#
# `BASE_DIR` vaut `backend/`, donc le parent est la racine du depot.
#
# `override=False` (le defaut) : une variable **deja presente dans
# l'environnement gagne sur le fichier**. C'est ce qui permet a Compose de
# passer ses propres valeurs au conteneur — ou le fichier n'existe meme pas,
# `.dockerignore` le tenant dehors pour que les secrets ne se retrouvent pas
# en clair dans une couche d'image.
load_dotenv(BASE_DIR.parent / ".env")

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# ── La clé de signature ─────────────────────────────────────────────────────
#
# ⚠️ **Elle n'a plus de valeur de repli utilisable hors ``DEBUG``, et c'est
# volontaire.** Le réglage précédent fournissait
# ``"dev-seulement-a-remplacer-en-production"`` quelle que soit la situation :
# un déploiement qui oubliait ``DJANGO_SECRET_KEY`` démarrait donc
# normalement, avec une clé publique, inscrite dans le dépôt. Les signatures
# de session et les jetons de réinitialisation devenaient falsifiables par
# quiconque a lu ce fichier, **sans aucun message pour le signaler**.
#
# Désormais le serveur refuse de démarrer. Une panne au démarrage se voit et
# se corrige ; une clé par défaut en production ne se voit pas.
#
# Le repli reste en ``DEBUG``, pour que cloner le dépôt et lancer les tests ne
# demande aucune configuration — c'est ce que ``backend/README.md`` promet.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-seulement-jamais-en-production"
    else:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY est absente et DJANGO_DEBUG vaut 0. "
            "Renseignez-la dans le .env de la racine. Pour en generer une : "
            'python -c "import secrets; print(secrets.token_urlsafe(50))"'
        )
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "groupachat.comptes",
    "groupachat.catalogue",
    "groupachat.commandes",
    "groupachat.echanges",
]

# ── Qui a le droit d'appeler cette API, et depuis ou ────────────────────────
#
# Le front et l'API sont **deux serveurs differents** : la boutique sur 5173,
# l'administration sur 5174, Django sur 8000. Pour un navigateur, ce sont trois
# origines distinctes, et il bloque les appels de l'une vers l'autre tant que
# le serveur appele ne dit pas explicitement qu'il les accepte.
#
# ⚠️ **`CorsMiddleware` doit rester tout en haut de cette liste.** Il doit
# repondre aux requetes de controle (`OPTIONS`) que le navigateur envoie
# *avant* la vraie requete, et il ne le peut que s'il passe avant les
# middlewares qui pourraient rediriger ou rejeter.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # ⚠️ **Il sert les fichiers statiques quand ``DEBUG`` est faux**, ce que
    # Django ne fait pas tout seul : hors DEBUG, ``runserver`` comme Gunicorn
    # renvoient 404 sur ``/static/``. Sans cette ligne, l'admin Django — qui
    # est *l'*outil d'administration du §13.6 — s'afficherait sans aucune
    # feuille de style ni script dans le conteneur.
    #
    # Sa place est imposee : **apres** ``SecurityMiddleware`` et **avant** tout
    # le reste, pour repondre sans traverser les sessions ni le CSRF. Il reste
    # derriere ``CorsMiddleware``, qui doit rester premier (voir ci-dessus).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_FORCER_SQLITE = os.environ.get("DJANGO_FORCER_SQLITE") == "1"

if _FORCER_SQLITE or os.environ.get("DATABASE_URL") is None:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "TEST": {"NAME": ":memory:"},
        }
    }
    MOTEUR_UTILISE = "sqlite"
else:
    import urllib.parse as _url

    _parse = _url.urlparse(os.environ["DATABASE_URL"])
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _parse.path.lstrip("/"),
            "USER": _parse.username or "",
            "PASSWORD": _parse.password or "",
            "HOST": _parse.hostname or "localhost",
            "PORT": str(_parse.port or 5432),
            # Django cree et detruit `test_<nom>` autour de chaque execution.
            "TEST": {"NAME": f"test_{_parse.path.lstrip('/')}"},
        }
    }
    MOTEUR_UTILISE = "postgresql"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Lome"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

#: Ou ``collectstatic`` depose les fichiers que WhiteNoise servira.
#:
#: **Il n'existait pas, et ``collectstatic`` echouait donc** — ce qui ne se
#: voyait pas tant qu'on ne travaillait qu'en ``DEBUG=1``, ou Django sert les
#: statiques lui-meme depuis les dossiers des applications.
#:
#: Le dossier est hors du depot (ignore par git) : c'est un produit de
#: construction, reconstruit a chaque image, jamais edite a la main.
STATIC_ROOT = BASE_DIR / "staticfiles"

#: Compression et empreinte dans le nom des fichiers.
#:
#: Les deux comptent pour le §5 du cahier des charges, qui part d'un forfait de
#: donnees limite : les fichiers sont servis en gzip et en brotli quand le
#: navigateur les accepte, et leur nom porte une empreinte, donc ils peuvent
#: etre mis en cache **pour un an** sans risquer de servir une version
#: perimee.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Messagerie ──────────────────────────────────────────────────────────────
#
# Elle ne sert aujourd'hui qu'à une chose, mais qui compte : **annoncer à un
# groupeur la décision prise sur son dossier KYC** (§10.5). Voir
# ``groupachat/notifications.py`` pour les textes et
# ``groupachat/comptes/annonces.py`` pour l'envoi.
#
# ⚠️ **Par défaut, rien ne sort de la machine.** Le backend console écrit le
# message dans le terminal de ``runserver``. C'est le bon défaut en
# développement : on relit la formulation exacte qu'un groupeur recevrait, sans
# risquer d'écrire à quelqu'un depuis un jeu de démonstration.
#
# Pour envoyer réellement, renseigner ``SMTP_HOTE`` dans le ``.env`` de la
# racine — le seul que ce fichier lise, voir plus haut —
# avec l'identifiant, le mot de passe et le port du fournisseur. Group Achat
# n'en a pas encore : c'est un des manques listés dans ``backend/README.md``.
if os.environ.get("SMTP_HOTE"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["SMTP_HOTE"]
    EMAIL_PORT = int(os.environ.get("SMTP_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("SMTP_UTILISATEUR", "")
    EMAIL_HOST_PASSWORD = os.environ.get("SMTP_MOT_DE_PASSE", "")
    EMAIL_USE_TLS = os.environ.get("SMTP_TLS", "1") == "1"
else:
    # ⚠️ **Dans un fichier, pas dans la console**, et c'est une correction et
    # non une préférence : le backend console écrit sur la sortie standard,
    # qui sous Windows est en cp1252. Le message de validation contient une
    # **espace insécable fine** (U+202F) dans « 150 000 F » — celle que le
    # produit emploie partout ailleurs — et cp1252 ne sait pas l'encoder. Le
    # courriel partait donc en ``UnicodeEncodeError``, soit une erreur 500 sur
    # une décision KYC par ailleurs correctement enregistrée.
    #
    # Trois corrections étaient possibles : retirer l'espace fine du message,
    # forcer l'encodage du terminal, ou écrire dans un fichier. La première
    # abîmerait la typographie pour une raison qui n'a rien à voir avec elle,
    # la seconde dépend de variables d'environnement qu'on ne contrôle pas
    # chez les autres. La troisième écrit en UTF-8, et donne en prime un
    # fichier relisable — ce qu'on veut justement faire de ces messages.
    #
    # Un fichier par courriel, dans `backend/.courriels/` (ignoré par git :
    # ces messages portent des noms et des adresses).
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / ".courriels"

#: L'expéditeur. Une adresse à laquelle **on peut répondre** : les messages de
#: refus invitent explicitement le groupeur à répondre s'il conteste, et une
#: adresse « ne-pas-repondre » contredirait cette invitation.
DEFAULT_FROM_EMAIL = os.environ.get(
    "COURRIEL_EXPEDITEUR", "Group Achat <bonjour@groupachat.tg>"
)

# ── SMS ─────────────────────────────────────────────────────────────────────
#
# Il ne sert qu'à une chose : **le code à quatre chiffres qui ouvre un compte
# acheteur** (§10.4 bis). Group Achat n'a pas encore de fournisseur.
#
# Trois valeurs possibles, et il faut les distinguer :
#
# | Valeur | Ce qui se passe |
# |---|---|
# | *(vide)* | ⚠️ **La connexion répond 503.** Pas de SMS, pas de compte |
# | `demonstration` | Le code vaut 1234 et s'affiche à l'écran |
# | *un fournisseur* | Un code aléatoire est tiré — l'envoi reste à écrire |
#
# ⚠️ **Le vide échoue fermé, et ce n'est pas négociable.** Un code fixe mis en
# ligne pour de vrai donnerait à n'importe qui le compte de n'importe quel
# numéro. `demonstration` existe pour qu'une démonstration déployée reste
# utilisable — le conteneur tourne avec `DEBUG=0`, qui est le bon réglage —
# mais c'est un **opt-in écrit à la main**, visible dans la configuration de
# déploiement. Un défaut part en production par oubli ; une valeur écrite à la
# main y part par décision.
SMS_FOURNISSEUR = os.environ.get("SMS_FOURNISSEUR", "")

#: Le code servi en mode démonstration. Jamais employé autrement.
CODE_SMS_DEMONSTRATION = os.environ.get("CODE_SMS_DEMONSTRATION", "1234")

# ⚠️ **Une liste d'origines, jamais `CORS_ALLOW_ALL_ORIGINS`.** Le reglage
# « tout ouvert » est commode en developpement et se retrouve en production
# une fois sur deux. Il laisserait n'importe quel site ouvert dans le
# navigateur d'un administrateur appeler `/api/dossiers/` — avec le jeton que
# cet administrateur vient de saisir, puisque le navigateur le joindrait.
#
# `CORS_ORIGINES` se renseigne dans `.env` au deploiement, avec le vrai nom de
# domaine. Le defaut ne couvre que les ports de developpement local.
CORS_ALLOWED_ORIGINS = [
    origine.strip()
    for origine in os.environ.get(
        "CORS_ORIGINES",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174",
    ).split(",")
    if origine.strip()
]

#: L'en-tete du jeton d'administration doit etre explicitement autorise.
#:
#: Un en-tete que le navigateur ne connait pas n'est pas transmis par defaut :
#: sans cette ligne, `X-Jeton-Admin` serait silencieusement retire et toutes
#: les requetes de l'ecran A2 reviendraient en 403 — sans rien dans les
#: journaux qui dise pourquoi.
CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-jeton-admin",
)

#: **Le mode démonstration.** Il suspend l'examen des dossiers de groupeur.
#:
#: Quand il est allumé, un dossier déposé est **validé sur-le-champ** : on
#: traverse l'inscription et on arrive dans l'espace groupeur, sans attendre
#: qu'un administrateur se connecte. C'est ce qu'il faut pour montrer le
#: produit à quelqu'un ; ce n'est pas ce qu'il faut en ligne.
#:
#: ⚠️ **Ce qu'il suspend est le contrôle central du modèle.** Le §10.5 pose
#: trois vérifications, et « vous êtes livré, ou remboursé » s'affiche à
#: l'acheteur sur presque chaque écran. C'est **nous** qui remboursons : le
#: groupeur retire l'argent à la clôture, donc avant la livraison, et le seul
#: recours qui reste ce jour-là est un dossier opposable. Allumé en
#: production, ce réglage ferait garantir des sommes au nom de gens dont
#: personne n'a rien vérifié.
#:
#: D'où le défaut : **éteint, et il faut l'écrire pour l'allumer**. Le faire
#: suivre ``DEBUG`` semblait pratique et c'était un piège — la suite de tests
#: aurait tourné avec la validation automatique, c'est-à-dire sans jamais
#: exercer l'examen des dossiers, qui est précisément ce qu'elle protège.
#: Six tests sont tombés en une fois, et ils avaient raison.
#:
#: C'est le même choix que ``SMS_FOURNISSEUR`` : on demande la démonstration,
#: elle ne s'invite pas.
#:
#: ⚠️ **Et elle ne s'applique jamais à la suite de tests**, quoi que dise le
#: ``.env`` de la machine. Sans cette condition, allumer la démonstration pour
#: montrer le produit éteindrait du même coup sept tests du recrutement — ils
#: passeraient au vert sans rien vérifier, ce qui est pire que de les voir
#: tomber. Un test qui veut ce mode l'obtient par ``override_settings``, et
#: c'est écrit dans ``test_recrutement.py``.
_EN_TEST = "test" in sys.argv
DEMONSTRATION = not _EN_TEST and os.environ.get("DEMONSTRATION", "") == "1"

#: ⚠️⚠️ **`JETON_ADMIN` a été retiré d'ici, et il ne doit pas revenir.**
#:
#: Les routes d'administration étaient gardées par ce **jeton unique et
#: partagé**, posé dans le `.env` du serveur et recopié à la main par chaque
#: administrateur. Elles exigent maintenant une **session ouverte contre un mot
#: de passe**, adossée aux comptes `User` de Django filtrés sur `is_staff`.
#:
#: **Aucun repli n'a été laissé**, et c'est le point : accepter encore un
#: secret partagé « au cas où » aurait rendu le reste décoratif, puisqu'il
#: suffit du plus faible des deux chemins pour entrer.
#:
#: On crée un administrateur par `python manage.py createsuperuser`, et on le
#: révoque en décochant `is_staff` — ce qui ferme ses sessions en cours à la
#: requête suivante, sans attendre leur expiration.
#:
#: Voir `groupachat/comptes/sessions_admin.py`.

REST_FRAMEWORK = {
    # ⚠️ **Aucun mur d'authentification** (§1.5) : on parcourt le catalogue
    # librement. Les points d'entrée qui engagent quelque chose — payer,
    # poser une question, déposer une demande — le vérifient eux-mêmes.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 24,
}


# ── La securite du transport, hors developpement ───────────────────────────
#
# ⚠️ **La CI disait : « Les avertissements restants concernent tous HTTPS, qui
# se regle au reverse-proxy et non ici. »** C'etait vrai pour deux d'entre eux
# et faux pour les deux autres : `SESSION_COOKIE_SECURE` et
# `CSRF_COOKIE_SECURE` sont des reglages **Django**, qu'aucun proxy ne pose a
# sa place. Ils sont donc poses ici.
#
# ⚠️ **Tous sont conditionnes a `not DEBUG`**, et c'est indispensable : en
# developpement on sert en clair sur `localhost`, et un cookie marque `secure`
# n'y serait **jamais renvoye par le navigateur**. On se retrouverait
# deconnecte a chaque requete, sans message, sur un symptome qui ressemble a
# une panne de session.
if not DEBUG:
    #: Les cookies ne partent que sur une connexion chiffree.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    #: Un cookie de session n'a aucune raison d'etre lisible en JavaScript.
    SESSION_COOKIE_HTTPONLY = True

    #: ⚠️ **Celui-ci depend du proxy, et il faut le savoir.** Django ne voit
    #: que du HTTP en clair derriere un reverse-proxy qui termine le TLS : sans
    #: cet en-tete, il croit la connexion non chiffree et `SECURE_SSL_REDIRECT`
    #: provoquerait une **boucle de redirection infinie**.
    #:
    #: Le proxy **doit** donc envoyer `X-Forwarded-Proto`. nginx le fait avec
    #: `proxy_set_header X-Forwarded-Proto $scheme;`. S'il ne le fait pas,
    #: retirer les deux lignes ci-dessous plutot que de se demander pourquoi
    #: le site boucle.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_HTTPS", "1") == "1"

    #: HSTS : le navigateur refusera le HTTP pour ce domaine pendant un an.
    #:
    #: ⚠️ **A n'activer qu'une fois le certificat en place et verifie.** Un
    #: HSTS pose trop tot rend le site **inaccessible** jusqu'a expiration du
    #: delai, et il n'y a aucun moyen de le retirer a distance : le navigateur
    #: du visiteur s'en souvient. D'ou le drapeau, qui vaut `0` par defaut.
    if os.environ.get("DJANGO_HSTS", "0") == "1":
        SECURE_HSTS_SECONDS = 31536000
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True
