# Group Achat — lancer, préparer et vérifier le projet en local.
#
#   make            liste les cibles
#   make preparer-presentation    la veille
#   make servir                   le jour J (les builds existent déjà)
#
# Tout se règle par variables : `make lancer PORT=8100`.

SHELL := /bin/bash

PORT           ?= 8000
PYTHON_SYSTEME ?= python3
VENV           ?= backend/.venv
PY             := $(abspath $(VENV))/bin/python
BACKEND        := backend
FRONTEND       := frontend
# Le dossier que Django sert à la racine des URL (RACINE_WEB dans settings.py).
WEB            ?= $(BACKEND)/web

# Réglages « sur ma machine ». Ils passent par l'environnement du processus,
# qui l'emporte sur le `.env` (load_dotenv n'écrase pas) : le `.env` n'est
# jamais modifié, et `.env.exemple` copié tel quel (DEBUG=0, pas de clé) ne
# bloque pas le démarrage.
#  - DEBUG=1 : en HTTP, un cookie « secure » ne serait jamais renvoyé et
#    personne ne pourrait se connecter.
#  - SQLITE=1 : aucun serveur PostgreSQL à démarrer la veille d'une
#    présentation. `SQLITE=0` rend la main à la DATABASE_URL du .env.
DJANGO_DEBUG ?= 1
SQLITE       ?= 1
# Les tests et la vérification n'ont besoin que des deux premiers : un .env
# fraîchement copié de .env.exemple (DEBUG=0, aucune clé) fait échouer Django
# dès l'import des réglages.
ENV_BASE  = DJANGO_DEBUG=$(DJANGO_DEBUG) DJANGO_FORCER_SQLITE=$(SQLITE)
ENV_LOCAL = $(ENV_BASE) \
            DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,admin.localhost \
            DJANGO_ORIGINES_SURES=http://localhost:$(PORT),http://127.0.0.1:$(PORT),http://admin.localhost:$(PORT) \
            SMS_FOURNISSEUR=$${SMS_FOURNISSEUR:-demonstration}
# VITE_API_URL vide : le client retombe sur /api, même origine. L'exemple du
# .env porte une adresse absolue qui rouvrirait le CORS dans le paquet compilé.
ENV_FRONT = VITE_API_URL=
# Écrite une seule fois : `lancer`, `servir` et `dev` démarraient Django par
# trois copies de cette ligne, qui auraient fini par diverger.
RUNSERVER = cd $(BACKEND) && $(ENV_LOCAL) $(PY) manage.py runserver 127.0.0.1:$(PORT)

MAKEFLAGS += --no-print-directory
.DEFAULT_GOAL := aide
.PHONY: aide installer migrer demo construire lancer servir dev verifier \
        verifier-rapide tests preparer-presentation _adresses

aide: ## Liste les cibles
	@echo "Group Achat — cibles disponibles (PORT=$(PORT)) :"
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | \
	  awk -F':.*## ' '{printf "  make %-22s %s\n", $$1, $$2}'

installer: ## Crée le venv Python, installe les dépendances Python et npm, crée .env s'il manque
	@test -x $(PY) || $(PYTHON_SYSTEME) -m venv $(VENV)
	$(PY) -m pip install --quiet -r $(BACKEND)/requirements.txt
	cd $(FRONTEND) && npm ci
	@if [ -f .env ]; then echo ".env existe déjà : laissé tel quel."; \
	 else cp .env.exemple .env && echo ".env créé depuis .env.exemple (les réglages locaux de ce Makefile le complètent)."; fi

migrer: ## Applique les migrations de la base
	cd $(BACKEND) && $(ENV_LOCAL) $(PY) manage.py migrate

demo: ## Charge le jeu de démonstration (sans effet s'il est déjà à jour)
	cd $(BACKEND) && $(ENV_LOCAL) $(PY) manage.py charger_demo --synchroniser

# Django sert les builds plutôt que Vite : c'est la production en miniature
# (une origine, le domaine choisit l'interface, aucun proxy ni CORS) et un
# seul processus à surveiller devant un public. Même assemblage que le
# Dockerfile : boutique à la racine, admin.html et ses assets à côté.
construire: ## Compile la boutique et la console, et les range là où Django les sert
	@# `rm -rf` sur un WEB vide, « . », « frontend » ou « backend/web/.. »
	@# effacerait bien plus que le build : seul un dossier directement sous
	@# backend/ dont le nom commence par « web » est accepté.
	@base="$(abspath $(WEB))"; \
	 case "$${base##*/}" in web*) ok=1;; *) ok=0;; esac; \
	 if [ "$$ok" = 1 ] && [ "$${base%/*}" = "$(CURDIR)/$(BACKEND)" ]; then :; \
	 else echo "WEB=\"$(WEB)\" refusé : il doit désigner un dossier web* directement sous $(BACKEND)/."; exit 1; fi
	cd $(FRONTEND) && $(ENV_FRONT) npm run build:tout
	rm -rf $(WEB) && mkdir -p $(WEB)/assets
	cp -r $(FRONTEND)/boutique/dist/. $(WEB)/
	cp -r $(FRONTEND)/admin/dist/assets/. $(WEB)/assets/
	cp $(FRONTEND)/admin/dist/index.html $(WEB)/admin.html

# Récursif plutôt que deux prérequis : sous `make -j`, construire (qui vide
# WEB) et servir (qui le lit) partiraient ensemble.
lancer: ## Mode présentation : compile puis lance Django seul (API + boutique + console)
	@$(MAKE) construire && $(MAKE) servir

# Le jour J : les builds existent déjà, inutile de recompiler (ni de risquer
# un échec de compilation devant le public).
servir: ## Lance Django seul sur les builds existants, sans recompiler
	@test -f $(WEB)/index.html || { echo "Aucun build dans $(WEB). Lancez d'abord make construire"; exit 1; }
	@$(MAKE) _adresses
	$(RUNSERVER) --noreload

_adresses:
	@echo ""
	@echo "  Boutique : http://localhost:$(PORT)/"
	@echo "  Console  : http://admin.localhost:$(PORT)/   (admin.localhost se résout sur la machine elle-même)"
	@echo "  Comptes de démonstration : README.md, section « Comptes de démonstration »"
	@echo "  Arrêt : Ctrl+C"
	@echo ""

# Les deux Vite relaient /api vers 127.0.0.1:8000 (en dur dans leurs
# configurations) : ce mode exige donc PORT=8000. `kill 0` arrête les trois
# processus ensemble à Ctrl+C, sans quoi un Vite orphelin garde son port.
dev: ## Mode développement : Django (8000) + Vite boutique (5173) + Vite console (5174)
	@test "$(PORT)" = "8000" || { echo "make dev exige PORT=8000 : les Vite relaient vers ce port."; exit 1; }
	@echo "  Boutique : http://localhost:5173/   Console : http://localhost:5174/   (Ctrl+C pour tout arrêter)"
	@trap 'kill 0' EXIT INT TERM; \
	 ($(RUNSERVER)) & \
	 (cd $(FRONTEND) && $(ENV_FRONT) npm run dev) & \
	 (cd $(FRONTEND) && $(ENV_FRONT) npm run dev:admin) & \
	 wait

verifier: ## Vérification complète (migrations, toute la suite pytest, typage) — SQLite par défaut (SQLITE=0 : base du .env) ; compter 25 à 35 minutes
	$(ENV_BASE) bash .claude/skills/verify/scripts/check.sh complet

verifier-rapide: ## Vérification rapide (migrations, typage, tests des sujets modifiés)
	$(ENV_BASE) bash .claude/skills/verify/scripts/check.sh rapide

tests: ## Lance la suite pytest depuis backend/
	cd $(BACKEND) && $(ENV_BASE) $(PY) -m pytest

preparer-presentation: ## La veille : installe si besoin, migre, charge la démo, compile
	@test -x $(PY) -a -d $(FRONTEND)/node_modules || $(MAKE) installer
	$(MAKE) migrer
	$(MAKE) demo
	$(MAKE) construire
	@echo ""
	@echo "Prêt. Lancez le jour J : make servir PORT=$(PORT)"
