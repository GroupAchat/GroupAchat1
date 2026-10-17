# syntax=docker/dockerfile:1

# ╭──────────────────────────────────────────────────────────────────────────╮
# │ Le front — deux applications, une seule construction                     │
# ╰──────────────────────────────────────────────────────────────────────────╯
#
# `npm run build` produit les deux paquets d'un coup : `dist/` pour la boutique
# et `dist-admin/` pour l'administration (voir `vite.config.ts` et
# `vite.admin.config.ts`).
#
# Une seule construction Node pour les deux : les dependances ne s'installent
# qu'une fois, et les deux paquets sortent du meme arbre de fichiers — donc la
# boutique et l'administration ne peuvent pas diverger par accident.
#
# ⚠️ **Ce fichier a porte la mention : « Les deux etapes nginx qui les
# servaient ont ete retirees : le serveur sera choisi autrement. »** Le serveur
# a ete choisi — c'est nginx, et les deux etapes sont revenues. La phrase est
# reproduite pour qu'on ne les retire pas une seconde fois en croyant nettoyer.
#
# La raison du choix est qu'il n'en demande aucun autre : tout le reste du
# projet est deja conteneurise et deploye par un `docker compose up` sur le
# VPS. Servir le client autrement — un nginx installe sur l'hote, un
# hebergement statique tiers — ajouterait une piece a administrer et un second
# endroit ou se tromper de version.
#
# | Cible | Ce qu'elle sert | Depuis |
# |---|---|---|
# | `construction` | Rien : elle construit | — |
# | **`boutique`** | `dist/` | `vite.config.ts` |
# | **`admin`** | `dist-admin/` | `vite.admin.config.ts` |
#
# ⚠️ **Deux images, et c'est le point de toute la separation.** Le paquet
# d'administration transporte des montants detenus et des files de travail :
# le mettre dans la meme image que la boutique le ferait telecharger par chaque
# acheteur de Lome, et il suffirait d'un nom de fichier pour l'ouvrir.
#
# Pour recuperer les paquets construits sans lancer de serveur :
#
#   docker build --target construction -t groupachat-front:construction .
#   docker create --name extraction groupachat-front:construction
#   docker cp extraction:/app/dist ./dist
#   docker cp extraction:/app/dist-admin ./dist-admin
#   docker rm extraction


# ── Construire les deux paquets ────────────────────────────────────────────
FROM node:22-alpine AS construction

WORKDIR /app

# `package-lock.json` est copie avec `package.json`, et c'est `npm ci` — non
# `npm install` — qui s'en sert : `ci` installe **exactement** les versions du
# verrou et echoue si les deux fichiers ne concordent pas. Une image doit se
# reconstruire a l'identique dans six mois.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# ⚠️⚠️ **`VITE_API_URL` est une variable de CONSTRUCTION, pas d'execution.**
#
# C'est le point le plus facile a manquer de tout ce fichier. Vite **inscrit la
# valeur en clair dans le JavaScript produit** : il n'y a pas de serveur Node
# pour la relire au demarrage, rien que des fichiers deja ecrits. Changer
# l'adresse de l'API demande donc de **reconstruire l'image** ; la passer dans
# `environment:` au lancement n'aurait aucun effet, et c'est un piege d'autant
# plus sournois que rien ne proteste.
#
# ⚠️ **Et c'est une adresse vue depuis le NAVIGATEUR, pas depuis le reseau
# Docker.** `http://api:8000/api` fonctionne entre conteneurs et echoue dans le
# navigateur, qui ne resout pas `api`. Il faut `http://localhost:8000/api` en
# local, ou le vrai nom de domaine public au deploiement.
#
# Le defaut vise le `runserver` local, comme `frontend/.env.exemple`.
ARG VITE_API_URL="http://127.0.0.1:8000/api"
ENV VITE_API_URL=$VITE_API_URL

# `npm run build` enchaine `tsc -b` puis les deux `vite build`. Le typage est
# donc verifie ici : **une erreur de type arrete la construction de l'image**,
# ce qui est exactement ou l'on veut l'apprendre.
RUN npm run build


# ── Servir la boutique ─────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS boutique

# ⚠️ **`/*` et non le dossier.** `COPY dist /usr/share/nginx/html` creerait
# `html/dist/`. Le `/.` copie le **contenu**, qui est ce qu'on veut servir a la
# racine.
COPY --from=construction /app/dist/. /usr/share/nginx/html/

# L'image de base pose une configuration par defaut qui sert `/` sans repli
# SPA : une adresse profonde y repondrait 404. On la remplace.
COPY nginx.boutique.conf /etc/nginx/conf.d/default.conf

# ⚠️ **Un controle a la construction, pas au premier visiteur.** `nginx -t`
# analyse la configuration et echoue si elle est invalide : l'erreur apparait
# ici, pas en production trois minutes apres un deploiement.
RUN nginx -t

EXPOSE 80

# `nginx` s'arrete tout seul si sa configuration est mauvaise ; cette sonde dit
# surtout si le conteneur **sert** encore. `wget` est dans l'image Alpine, pas
# `curl`.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1


# ── Servir l'administration ────────────────────────────────────────────────
FROM nginx:1.27-alpine AS admin

COPY --from=construction /app/dist-admin/. /usr/share/nginx/html/
COPY nginx.admin.conf /etc/nginx/conf.d/default.conf

RUN nginx -t

EXPOSE 80

# ⚠️ **`/admin.html` et non `/`.** Ce paquet n'a pas d'`index.html` : une sonde
# sur `/` passerait par le repli et repondrait quand meme 200, donc elle ne
# verifierait rien. On demande le fichier qui doit exister.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/admin.html || exit 1
