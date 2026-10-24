# syntax=docker/dockerfile:1
#
# Group Achat : une seule image pour l'API **et** les deux applications.
#
# **Pas de serveur web devant, et pas de conteneur par application.** Coolify
# termine le TLS et route par domaine ; WhiteNoise, déjà installé, sert les
# fichiers compilés. Un nginx n'ajouterait qu'une image à construire et à
# tenir à jour.
#
# Conséquence heureuse : la boutique, la console et l'API partagent une
# origine. Ni CORS, ni cookie tiers, ni variable d'adresse d'API à régler.
#
# ⚠️ Le contexte de construction est **la racine du dépôt**, pas `backend/` :
# cette image a besoin des deux. Voir `docker-compose.yml`.

# ── 1. Les applications ─────────────────────────────────────────────────────
FROM node:22-alpine AS front

WORKDIR /front

# Les manifestes d'abord, le code ensuite : tant que les dépendances ne
# bougent pas, Docker réutilise la couche d'installation. Les trois espaces
# de travail sont déclarés ici, sinon `npm ci` refuse de résoudre les liens
# entre eux.
COPY frontend/package.json frontend/package-lock.json ./
COPY frontend/commun/package.json commun/
COPY frontend/boutique/package.json boutique/
COPY frontend/admin/package.json admin/
RUN npm ci

COPY frontend/tsconfig.base.json ./
COPY frontend/commun/ commun/
COPY frontend/boutique/ boutique/
COPY frontend/admin/ admin/

# Vite inscrit les variables VITE_* **dans le code compilé** : ce sont des
# arguments de construction, pas des variables d'exécution. Laissé vide, le
# client vise « /api » sur sa propre origine — ce qu'on veut.
ARG VITE_API_URL=""
ARG VITE_DEMONSTRATION="1"
ENV VITE_API_URL=$VITE_API_URL     VITE_DEMONSTRATION=$VITE_DEMONSTRATION

RUN npm run build --workspace boutique     && npm run build --workspace admin

# Les deux applications se rejoignent dans un seul dossier. Les fichiers de
# la console portent le préfixe « admin- », ils n'écrasent donc rien ; seule
# sa page d'entrée doit être renommée, puisque les deux s'appellent
# `index.html` dans leur dossier d'origine.
RUN mkdir -p /web/assets     && cp -r boutique/dist/. /web/     && cp -r admin/dist/assets/. /web/assets/     && cp admin/dist/index.html /web/admin.html     && ls /web/index.html /web/admin.html


# ── 2. L'API ────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS application

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /application

# Image « slim » et non « alpine » : psycopg et Pillow publient des roues
# précompilées pour la glibc, pas pour la musl d'Alpine. Sur Alpine, pip les
# recompilerait depuis les sources — plusieurs minutes et une chaîne de
# compilation à embarquer, pour une image à peine plus légère.
COPY backend/requirements.txt ./
# `--retries` et `--timeout` : une coupure passagere chez PyPI faisait echouer
# toute la construction sur un paquet a moitie telecharge.
RUN pip install --no-cache-dir --retries 5 --timeout 60 -r requirements.txt

# `pg_isready` sert à l'entrypoint pour attendre la base.
RUN apt-get update \
    && apt-get install --no-install-recommends -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/ ./
COPY --from=front /web /application/web

RUN mkdir -p /application/medias /application/statiques

# Le bit d'exécution ne survit pas toujours au passage par un hôte Windows :
# on le repose ici plutôt que de dépendre de ce que le dépôt a conservé.
RUN chmod +x /application/entrypoint.sh

# Ne pas tourner en root : une faille dans Django ne doit pas donner la main
# sur le conteneur.
RUN useradd --create-home --uid 10001 groupachat \
    && chown -R groupachat:groupachat /application
USER groupachat

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/catalogue/categories/', timeout=4).status < 500 else 1)"

ENTRYPOINT ["/application/entrypoint.sh"]
