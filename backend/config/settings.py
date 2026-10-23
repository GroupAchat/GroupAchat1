# -*- coding: utf-8 -*-
"""Réglages de Group Achat.

La configuration vient d'un **seul** fichier : `.env` à la racine du dépôt,
celui que lisent aussi Docker Compose et Vite. `BASE_DIR` vaut `backend/`, donc
son parent est la racine.

PostgreSQL dès que `DATABASE_URL` est renseignée — y compris pour les tests,
afin que le moteur testé soit celui de la production. SQLite sert de secours
quand aucune `DATABASE_URL` n'est définie, pour pouvoir cloner et lancer la
suite sans rien installer. `DJANGO_FORCER_SQLITE=1` force ce secours.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR.parent / ".env")

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# La clé de signature n'a pas de valeur de repli hors DEBUG : un déploiement
# qui oublie DJANGO_SECRET_KEY doit échouer bruyamment, pas démarrer avec une
# clé publique qui rendrait sessions et jetons falsifiables.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError(
            "DJANGO_SECRET_KEY est obligatoire hors DEBUG : renseignez-la dans .env"
        )
    SECRET_KEY = "cle-de-developpement-a-ne-jamais-deployer"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

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
    "groupachat.paiements",
    "groupachat.echanges",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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


def _base_depuis_url(url: str) -> dict:
    """Traduit une `DATABASE_URL` postgres en configuration Django."""
    morceaux = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": morceaux.path.lstrip("/"),
        "USER": unquote(morceaux.username or ""),
        "PASSWORD": unquote(morceaux.password or ""),
        "HOST": morceaux.hostname or "",
        "PORT": str(morceaux.port or ""),
    }


_url_base = os.environ.get("DATABASE_URL", "")
_forcer_sqlite = os.environ.get("DJANGO_FORCER_SQLITE", "0") == "1"

if _url_base and not _forcer_sqlite:
    DATABASES = {"default": _base_depuis_url(_url_base)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "base-de-secours.sqlite3",
        }
    }

AUTH_USER_MODEL = "comptes.Utilisateur"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Lome"
USE_I18N = True
USE_TZ = True

STATIC_URL = "statiques/"
STATIC_ROOT = BASE_DIR / "statiques"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

MEDIA_URL = "medias/"
MEDIA_ROOT = BASE_DIR / "medias"

# ── Les applications compilees, servies par Django ──────────────────────────
#
# Pas de nginx devant : Coolify fait deja le TLS et le routage par domaine.
# WhiteNoise sert les fichiers construits par Vite, et `ApplicationCompilee`
# rend la page d'entree pour tout le reste.
#
# Les deux applications deposent leurs fichiers dans le meme dossier : leurs
# noms portent une empreinte differente (`index-xxxx.js` contre
# `admin-xxxx.js`), ils ne se marchent donc pas dessus.
RACINE_WEB = Path(os.environ.get("RACINE_WEB", BASE_DIR / "web"))

# WhiteNoise sert ce dossier **a la racine des URL** : `/assets/index-x.js`
# plutot que `/statiques/assets/index-x.js`, ce qu'attendent les pages
# produites par Vite.
WHITENOISE_ROOT = str(RACINE_WEB) if RACINE_WEB.is_dir() else None

# ⚠️ **Faux a dessein.** A `True`, WhiteNoise rendrait lui-meme `index.html`
# sur « / » — toujours le meme, quel que soit le domaine. La boutique
# s'afficherait alors sur `admin.achatgr.com`. On laisse la vue trancher.
WHITENOISE_INDEX_FILE = False

# Les sous-domaines qui montrent la console d'administration.
HOTES_ADMINISTRATION = [
    h.strip()
    for h in os.environ.get("HOTES_ADMINISTRATION", "admin").split(",")
    if h.strip()
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINES", "http://localhost:5173,http://localhost:5174"
    ).split(",")
    if o.strip()
]

# ── Derrière le proxy de Coolify ────────────────────────────────────────────
#
# Coolify termine le TLS et parle à nos conteneurs en clair. Sans ce réglage,
# Django se croirait en HTTP derrière un site en HTTPS : il refuserait toute
# requête POST au motif que l'origine ne correspond pas, et poserait des
# cookies non sécurisés.
#
# ⚠️ Ce réglage **fait confiance à un en-tête**. Il n'est sûr que parce que
# nginx le réécrit systématiquement : un client ne peut pas l'imposer.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


def _origines_sures() -> list[str]:
    """Les origines autorisées à écrire (jeton CSRF).

    Django 4 et au-delà vérifient l'en-tête ``Origin`` sur chaque écriture.
    Oublier cette liste en production donne une panne déroutante : la lecture
    marche, les formulaires échouent tous en 403.

    On la dérive donc d'``ALLOWED_HOSTS`` plutôt que d'attendre une seconde
    variable que personne ne pense à renseigner ; ``DJANGO_ORIGINES_SURES``
    reste là pour les cas particuliers.
    """
    explicites = [
        o.strip() for o in os.environ.get("DJANGO_ORIGINES_SURES", "").split(",")
        if o.strip()
    ]
    if explicites:
        return explicites

    # ⚠️ Les origines portent un **port**, pas ALLOWED_HOSTS. Dérivée du seul
    # ALLOWED_HOSTS, la liste donnait « http://localhost » là où le navigateur
    # annonce « http://localhost:5173 » — et toutes les écritures tombaient en
    # 403 en développement. Les origines CORS, elles, sont déjà complètes.
    derivees = list(CORS_ALLOWED_ORIGINS)
    for hote in ALLOWED_HOSTS:
        if hote in {"*", ""}:
            continue
        schema = "http" if hote.startswith(("localhost", "127.0.0.1")) else "https"
        origine = f"{schema}://{hote}"
        if origine not in derivees:
            derivees.append(origine)
    return derivees


CSRF_TRUSTED_ORIGINS = _origines_sures()

# Hors DEBUG, les cookies ne voyagent qu'en HTTPS. En développement ils
# doivent rester lisibles sur http://localhost, d'où la condition.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if not DEBUG:
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # La redirection vers HTTPS est le travail du proxy : la refaire ici
    # provoquerait une boucle, nginx parlant à Django en clair.
    SECURE_SSL_REDIRECT = False

# ⚠️ **Sans ceci, aucune requête authentifiée ne passe en inter-origines.**
# Le client envoie ses appels avec `credentials: "include"` pour transporter
# le cookie de session ; le navigateur exige alors que la réponse porte
# `Access-Control-Allow-Credentials: true`, que django-cors-headers ne pose
# pas de lui-même. Son absence donne une erreur CORS déroutante, où le
# serveur a pourtant répondu 200.
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ── Règles métier ───────────────────────────────────────────────────────────
#
# Prélevés une seule fois, au décaissement, sur le total collecté.
FRAIS_PLATEFORME_FCFA = int(os.environ.get("FRAIS_PLATEFORME_FCFA", "1500"))

# Durée de validité d'un code de vérification SMS, en minutes.
VALIDITE_CODE_SMS_MINUTES = int(os.environ.get("VALIDITE_CODE_SMS_MINUTES", "10"))

SMS_FOURNISSEUR = os.environ.get("SMS_FOURNISSEUR", "console")

DEMONSTRATION = os.environ.get("DEMONSTRATION", "0") == "1"
