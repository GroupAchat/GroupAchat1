# La boutique : construite, puis servie. Rien a regler ailleurs.
#
# ## Pourquoi ce fichier existe
#
# Le deploiement par site statique demandait quatre reglages dans l'interface
# de l'hebergeur, dont le **dossier publie**. Celui-la est reste sur le dossier
# source, et le resultat etait une page blanche avec, dans la console :
#
#   Failed to load module script: Expected a JavaScript-or-Wasm module script
#   but the server responded with a MIME type of "application/octet-stream".
#
# Le serveur rendait l'`index.html` **source**, qui demande `/src/main.tsx` —
# un fichier TypeScript qu'aucun navigateur n'execute. Mesure sur le domaine :
# `/package.json` repondait 200, `/assets/` repondait 404.
#
# Ce `Dockerfile` enleve le reglage au lieu de le documenter. Il construit et
# il sert ; il n'y a plus de dossier a designer, donc plus de dossier a se
# tromper.
#
# ## ⚠️ Caddy, et pas nginx
#
# nginx a ete retire de ce depot a la demande de l'utilisateur. Ce qui le
# remplace n'est pas un autre serveur a configurer : `caddy file-server`
# **n'a aucun fichier de configuration**, juste la commande en bas de ce
# fichier. Et sa table de types MIME est interne, donc le defaut qui a cause la
# page blanche ne peut pas se reproduire : un `.js` sort en `text/javascript`
# sans qu'on ait rien a declarer.
#
# ## ⚠️⚠️ `VITE_API_URL` est lue ICI, a la construction
#
# Vite l'inscrit **en clair dans le JavaScript produit** ; aucun serveur ne la
# relit au demarrage. La passer en variable d'execution n'a **aucun effet** et
# **rien ne proteste** : le site s'affiche, et le navigateur de chaque visiteur
# appelle `127.0.0.1:8000`, c'est-a-dire sa propre machine. Changer l'adresse
# de l'API demande donc de **reconstruire l'image**, jamais de la redemarrer.
#
# ## L'administration
#
# Elle a son propre fichier, `Dockerfile.admin`. Deux fichiers plutot qu'une
# cible a choisir : une cible se designe dans un champ de l'interface, et c'est
# exactement le genre de champ qui est reste vide et a produit la page blanche.
# Un fichier se designe par son chemin, ce qui est plus dur a oublier.


# ── Construire ──────────────────────────────────────────────────────────────

FROM node:22-alpine AS construction

WORKDIR /app

# Les manifestes d'abord, et seuls : tant qu'ils ne changent pas, Docker
# reutilise la couche de `npm ci`. Copier tout le dossier avant reinstallerait
# les dependances a chaque modification d'un composant.
COPY package.json package-lock.json ./

# `npm ci` et non `npm install` : il respecte `package-lock.json` a la lettre
# et echoue si les deux fichiers divergent. `install` resoudrait les versions a
# neuf, et on deploierait des dependances que personne n'a jamais essayees.
RUN npm ci

COPY . .

# La valeur par defaut vise la machine locale : elle sert au developpement, et
# elle est **fausse en production**. Voir l'avertissement en tete de fichier.
ARG VITE_API_URL="http://127.0.0.1:8000/api"
ENV VITE_API_URL=$VITE_API_URL

# `npm run build` enchaine `tsc -b`, puis les deux `vite build`. Il produit
# donc `dist/` **et** `dist-admin/` ; on n'en garde qu'un ici.
RUN npm run build


# ── Servir ──────────────────────────────────────────────────────────────────

FROM caddy:2-alpine AS boutique

# ⚠️ `/app/dist/.` et non `/app/dist` : avec le `/.` on copie le **contenu**
# du dossier. Sans lui, selon que la destination existe deja, on obtiendrait
# un `/srv/dist/` imbrique — et le serveur rendrait un 404 sur tout.
COPY --from=construction /app/dist/. /srv/

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q --spider http://127.0.0.1/ || exit 1

# ⚠️ **Aucun `Caddyfile`, et c'est le but.** `caddy file-server` sert un
# dossier et rien d'autre : pas de configuration a relire, pas de type MIME a
# declarer, pas de directive a oublier.
#
# ⚠️ **Et aucun repli vers `index.html` non plus.** C'est le reglage que
# reclament la plupart des applications React, et **celle-ci n'en a pas
# besoin** : elle n'utilise aucune route par chemin. Tout passe par des
# parametres — `?role=groupeur`, `?groupage=c1` — donc chaque adresse est `/`
# suivi d'une chaine de requete, qu'un serveur de fichiers resout sans rien
# savoir. Le seul vrai sous-dossier, `/presentation/`, existe comme de vrais
# fichiers avec son propre `index.html`.
#
# Si un jour un routeur par chemin arrive, il faudra un `Caddyfile` avec
# `try_files {path} /index.html`. Pas avant.
CMD ["caddy", "file-server", "--root", "/srv", "--listen", ":80"]
