# Group Achat en conteneurs

**Trois services** : la base, l'API, et la tâche de clôture.

> ⚠️⚠️ **Ce document en annonçait cinq**, dont `boutique` et `admin`, deux
> images nginx construites depuis `frontend/`. **Elles ont été retirées du
> dépôt avec nginx lui-même.** Le front est maintenant construit et servi par
> **Coolify**, qui n'a besoin ni d'image ni de serveur web ici.
>
> Avant cela, le document disait encore autre chose : *« Deux services : la
> base et l'API. Le front n'est pas conteneurisé. »* La bonne manière de lire
> ces trois états successifs, c'est que **le serveur du front n'a jamais été
> une décision de ce dépôt**, et qu'il a fini par ne plus y vivre du tout.

| Service | Image | Port publié |
|---|---|---|
| `base` | `postgres:17-alpine` | aucun |
| `api` | construite depuis `backend/` | `8000` |
| `taches` | l'image de l'API, sans son point d'entrée | aucun |

## Le front, et ses deux images sans nginx

Deux images, **un fichier chacune**, qui construisent **et** servent :

| Fichier | Sert | Image |
|---|---|---|
| `frontend/Dockerfile` | la boutique, depuis `dist/` | `caddy:2-alpine` |
| `frontend/Dockerfile.admin` | l'administration, depuis `dist-admin/` | `caddy:2-alpine` |

```
docker build -t boutique --build-arg VITE_API_URL=https://api.exemple.tg/api ./frontend
docker build -t admin -f frontend/Dockerfile.admin --build-arg VITE_API_URL=https://api.exemple.tg/api ./frontend
```

### ⚠️ Caddy, et pas nginx

nginx a été retiré du dépôt. Ce qui le remplace n'est pas un autre serveur à
configurer : `caddy file-server` **n'a aucun fichier de configuration**, juste
une commande. Sa table de types MIME est interne, donc **le défaut qui a causé
la page blanche ne peut pas se reproduire** — un `.js` sort en
`text/javascript` sans qu'on ait rien à déclarer.

### ⚠️⚠️ Ce que ces images réparent

Le déploiement passait par un « site statique » où le **dossier publié** se
règle dans l'interface de l'hébergeur. Il est resté sur le dossier source, et
`achatgr.com` servait l'`index.html` **source** — celui qui demande
`/src/main.tsx`, un fichier TypeScript qu'aucun navigateur n'exécute. Mesuré
sur le domaine : `/package.json` répondait **200**, `/assets/` répondait
**404**.

Ces images **suppriment le réglage au lieu de le documenter**. Il n'y a plus de
dossier à désigner, donc plus de dossier à se tromper. Vérifié en les faisant
tourner : `/src/main.tsx` et `/package.json` répondent **404**, et le module
sort en `text/javascript`.

### ⚠️ Deux fichiers plutôt qu'une cible à choisir

Un seul `Dockerfile` à deux cibles marcherait, et c'était la forme précédente.
La cible se désigne alors dans un champ de l'interface — exactement le genre de
champ qui est resté vide. Pire, `docker build` sans `--target` construit la
**dernière** étape du fichier : avec l'administration en dernier, un hébergeur
qui ne précise rien déploierait l'écran interne à la place du site public.

Le coût assumé : les étapes de construction sont identiques dans les deux
fichiers. Quinze lignes recopiées, contre un champ qui peut rester vide.

⚠️⚠️ **`VITE_API_URL` est une variable de CONSTRUCTION.** Vite l'inscrit en
clair dans le JavaScript produit ; il n'existe aucun serveur Node pour la
relire au démarrage. La poser comme variable d'exécution n'a **aucun effet** et
ne provoque **aucune erreur** : le navigateur de chaque visiteur appelle alors
`127.0.0.1:8000`, c'est-à-dire sa propre machine. La page s'affiche, et rien
ne se charge. C'est le piège le plus coûteux de toute cette chaîne.

⚠️ **L'administration affiche des noms, des numéros et des références de
pièces d'identité.** Elle était publiée sur `127.0.0.1:` et atteinte par un
tunnel SSH. Ce prefixe n'existe plus : **c'est à l'hébergeur de restreindre
l'accès** à ce sous-domaine. Elle est désormais protégée par un mot de passe
— une session contre un compte `is_staff`, cinq essais avant un verrou de
quinze minutes — mais une page d'administration ouverte sur Internet reste une
page d'administration ouverte sur Internet.


Le **site de présentation** vit dans `frontend/public/presentation/`, donc Vite
le recopie dans le paquet de la boutique et il part avec lui, quel que soit le
serveur retenu. Voir [frontend/PRESENTATION.md](frontend/PRESENTATION.md).

```bash
cp .env.exemple .env      # puis renseigner les deux secrets
docker compose up --build
```

| Service | Adresse | Ce que c'est |
|---|---|---|
| `api` | <http://localhost:8000> | Django + DRF. L'admin Django est sur `/admin/` |
| `base` | *(interne)* | PostgreSQL 17 — aucun port publié |

Le front, lui, tourne à côté et hors Docker :

```bash
cd frontend
npm run dev          # la boutique, sur 5173
npm run dev:admin    # l'administration, sur 5174
```

**Les ports sont ceux du développement local**, et ce n'est pas un hasard : les
valeurs par défaut de `CORS_ORIGINES` et de `VITE_API_URL` les visent déjà.
Lancer l'API en conteneur ne demande donc de reconfigurer ni le navigateur ni
les origines autorisées.

## Les deux secrets

Compose **s'arrête avec un message en français** si l'un des deux manque. Ce
n'est pas une commodité : une base au mot de passe vide et une clé de signature
par défaut sont deux façons de mettre un service en ligne ouvert.

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"   # DJANGO_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(24))"   # POSTGRES_PASSWORD
```

`.env` est ignoré par git ; le dépôt ne contient que `.env.exemple`, sans aucun
secret.

> ⚠️ **Ils étaient trois, et le troisième était `JETON_ADMIN`** — un jeton
> unique et partagé qui ouvrait l'écran d'administration. Il n'est plus lu par
> personne : l'administration se connecte avec un **compte**, créé une fois par
> `python manage.py creer_administrateur` depuis `ADMIN_IDENTIFIANT` et
> `ADMIN_MOT_DE_PASSE`. Ces deux variables ne sont **pas** passées aux services :
> les laisser dans l'environnement du conteneur les rendrait lisibles par
> `docker inspect` en permanence, pour un usage unique.

## Le piège à connaître avant de déployer

`VITE_API_URL` est **une variable de construction, pas d'exécution**, et c'est
l'erreur la plus facile à commettre ici. Vite inscrit la valeur **en clair dans
le JavaScript produit** : il n'y a pas de serveur Node pour la relire au
démarrage, seulement des fichiers déjà écrits.

```bash
# Changer l'adresse de l'API :
cd frontend && VITE_API_URL=https://api.exemple.tg/api npm run build
#                                                      ↑ reconstruire le paquet
```

La mettre dans `environment:` n'aurait **aucun effet, et aucun message
d'erreur**. Second piège de la même variable : c'est une adresse vue **depuis
le navigateur**, pas depuis le réseau Docker. `http://api:8000/api` fonctionne
entre conteneurs et échoue dans le navigateur, qui ne résout pas `api`.

Et `VITE_API_URL` va **toujours par paire avec `CORS_ORIGINES`** : si le front
change d'adresse, il faut l'ajouter aux origines autorisées côté backend, sinon
le navigateur bloque les appels.

## Les commandes utiles

```bash
docker compose logs -f api              # suivre l'API
docker compose exec api python manage.py createsuperuser
docker compose exec api python manage.py test groupachat
docker compose exec base psql -U groupachat -d groupachat

docker compose down                     # arrêter, en gardant la base
docker compose down -v                  # ⚠️ supprime aussi le volume
```

`docker compose down -v` détruit `donnees-postgres`, donc toute la base. Sans
le `-v`, les données survivent aux arrêts.

## Ce que fait l'API au démarrage

`backend/entrypoint.sh`, dans cet ordre : il **attend PostgreSQL** en ouvrant
une vraie connexion Django (le `depends_on` de Compose ne suffit pas — un
conteneur déclaré sain peut encore être en train d'initialiser son répertoire
de données), applique les **migrations**, puis charge le jeu du §3 si
`CHARGER_DEMO=1` et crée un superutilisateur si les variables sont fournies.

`CHARGER_DEMO=1` est pratique au premier lancement et **à passer à `0`
ensuite** : la commande réécrit les données de démonstration à chaque
démarrage.

## Les décisions, et ce qu'elles coûtent

**Node reste hors des images servies.** Le front est construit par Node, puis
ses fichiers statiques sont servis par autre chose : embarquer le constructeur
dans l'image servie multiplierait sa taille par dix et exposerait un
interpréteur qui n'a plus rien à y faire. Cette règle survit au retrait du
serveur web, et c'est elle qu'il faudra respecter en en choisissant un autre.
Le backend, lui, compile ses dépendances dans une première étape dont l'image
finale ne reçoit que le résultat.

**Une seule construction pour les deux fronts.** `npm run build` produit
`dist/` et `dist-admin/` d'un coup. Les dépendances ne s'installent qu'une
fois, et les deux paquets sortent du même arbre de fichiers — donc ils ne
peuvent pas diverger par accident.

**`gunicorn` et `whitenoise` ont été ajoutés à `requirements.txt`**, et deux
réglages à `config/settings.py` (`STATIC_ROOT` et le stockage compressé). Ce
n'était pas optionnel : `runserver` est un serveur de développement qui, hors
`DEBUG`, **renvoie 404 sur tous les fichiers statiques** — l'admin Django, qui
est *l'*outil d'administration du §13.6, s'afficherait sans feuille de style ni
script. Et `collectstatic` échouait faute de `STATIC_ROOT`, ce qui ne se voyait
pas tant qu'on ne travaillait qu'en `DEBUG=1`.

**Les images tournent sous un utilisateur non privilégié** (`groupachat`, uid
10001) pour le backend. Par défaut un conteneur tourne en `root`, et une faille
d'exécution de code y devient une faille `root`.

**`requirements.txt` installe aussi `pytest` et ses dépendances** dans l'image
de production. C'est assumé pour l'instant — ça permet
`docker compose exec api python manage.py test groupachat` sans seconde image —
au prix d'une dizaine de méga-octets. Séparer en `requirements.txt` et
`requirements-dev.txt` serait plus propre si la taille devient un sujet.

## ⚠️ Ce que cette configuration ne fait pas

**Il n'y a pas de HTTPS.** Aucun certificat, aucune terminaison TLS, aucune
redirection. `manage.py check --deploy` le signale en cinq avertissements
(`SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`) et ils sont **tous justes**. Ils se règlent à la couche
qui termine le TLS — un reverse-proxy devant ces conteneurs, Caddy ou
Traefik — pas dans ce fichier. Tel quel, l'ensemble convient à une machine de
développement et à une démonstration locale, **pas à un VPS exposé**.

**L'administration ne demande aucun mot de passe.** L'écran A1 n'affiche que
des compteurs et des montants, mais **l'écran A2 affiche des noms, des numéros
et des références de pièces d'identité**. Ce qui protège ces données
aujourd'hui, c'est le jeton `X-Jeton-Admin` exigé par `/api/dossiers/` côté
backend : la page s'ouvre, les données ne viennent pas sans le jeton, et c'est
la seule chose qui les protège. **Le serveur web qui servira
`dist-admin/` devra donc poser quelque chose de plus** : un réseau privé, un
VPN, ou à défaut une authentification HTTP. Tant que ce choix n'est pas fait,
l'administration ne s'ouvre qu'en local, par `npm run dev:admin`.

**Le paiement reste simulé** (§18.2) : c'est un manque du produit, pas du
conteneur, et il dure jusqu'à l'agrément d'un agrégateur. Voir
`backend/README.md`.

**Une seule réplique d'API.** Les migrations tournent au démarrage de chaque
conteneur ; avec plusieurs répliques démarrant ensemble, deux `migrate`
concurrents se marcheraient dessus. Il faudrait alors une tâche de migration
distincte, exécutée une fois avant la mise en service.
