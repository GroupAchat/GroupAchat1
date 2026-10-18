# Déploiement

Deux workflows GitHub Actions, dans `.github/workflows/` :

| Fichier | Quand | Ce qu'il fait |
|---|---|---|
| `ci.yml` | chaque poussé et chaque *pull request* | 160 tests sur PostgreSQL, typage et construction du front, construction des trois images, validation des deux fichiers Compose |
| `deploiement.yml` | une étiquette `v*`, ou à la main | publie les images sur GHCR, puis `pull` + `up -d` sur le serveur par SSH |

## ⚠️ À régler avant tout : le dépôt distant est le mauvais

```
$ git remote -v
origin  https://github.com/kephira-07/SosCaniveaux.git
```

**`SosCaniveaux` est un autre projet.** En l'état, un `git push` enverrait Group Achat dans le
dépôt d'un projet sans rapport, et les workflows s'exécuteraient là-bas — avec ses secrets, ses
images et son historique. Rien de ce qui suit ne fonctionnera avant de corriger :

```bash
git remote set-url origin https://github.com/<proprietaire>/<depot-group-achat>.git
```

Je ne l'ai pas fait moi-même : changer le dépôt distant d'un projet est une décision qui
t'appartient, et je ne sais pas quel dépôt tu veux utiliser.

## Ce qui ne construit rien sur le serveur

```
étiquette v1.0.0
      │
      ├─ GitHub Actions construit 3 images ──→ GHCR
      │                                         │
      └─ SSH ──→ serveur : docker compose pull ─┘ puis up -d
```

Le serveur n'a besoin **que de Docker**. Ni Node, ni Python, ni le code source. Deux raisons, et la
seconde compte plus que la première :

- un `vite build` demande Node, 300 Mo de `node_modules` et plus de mémoire qu'un petit VPS à un
  cœur ;
- **on déploie l'image que l'intégration continue a validée**, pas une reconstruction du même
  code. Construire deux fois, c'est se donner deux occasions d'obtenir deux résultats différents.

## 1. Configurer le dépôt

*Settings → Secrets and variables → Actions*

**Variables** (onglet *Variables*) :

| Nom | Contenu |
|---|---|
| `VITE_API_URL` | `https://api.votredomaine.tg/api` — l'adresse **publique** de l'API |

C'est une variable et non un secret, délibérément : elle est inscrite en clair dans le JavaScript
servi à tous les visiteurs, donc la cacher ne protégerait rien — et un secret serait masqué dans
les journaux, où l'on veut justement pouvoir relire quelle adresse a servi.

**Secrets** (onglet *Secrets*) :

| Nom | Contenu |
|---|---|
| `SSH_HOTE` | le nom de domaine ou l'IP du serveur |
| `SSH_UTILISATEUR` | le compte de déploiement |
| `SSH_CLE_PRIVEE` | la clé privée SSH, en entier, en-têtes comprises |
| `SSH_PORT` | *(facultatif)* 22 par défaut |

```bash
# Sur votre machine : une paire de clés dédiée au déploiement, sans phrase de passe
ssh-keygen -t ed25519 -f ~/.ssh/groupachat_deploiement -C "deploiement group achat" -N ""

# La publique va sur le serveur, la privée dans le secret SSH_CLE_PRIVEE
ssh-copy-id -i ~/.ssh/groupachat_deploiement.pub utilisateur@serveur
cat ~/.ssh/groupachat_deploiement        # → à coller dans SSH_CLE_PRIVEE
```

Une clé **dédiée**, et non votre clé personnelle : elle vit dans les secrets de GitHub, et on doit
pouvoir la révoquer sans perdre son propre accès au serveur.

## 2. Préparer le serveur

```bash
# Docker et le greffon Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"   # puis se reconnecter

mkdir -p ~/groupachat && cd ~/groupachat
```

Le `.env` du serveur s'écrit **une fois, à la main**, et le déploiement ne l'envoie jamais : il
contient les secrets de production, qui n'ont pas à passer par GitHub Actions. Reprendre
`.env.exemple` du dépôt et renseigner :

```bash
# Les secrets, générés sur le serveur
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # DJANGO_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(24))"   # POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(18))"   # ADMIN_MOT_DE_PASSE
```

⚠️ **`JETON_ADMIN` a disparu de cette liste.** L'administration était ouverte
par un **jeton unique et partagé** que chaque administrateur recopiait à la
main ; elle exige maintenant une **session ouverte contre un mot de passe**,
adossée aux comptes Django filtrés sur `is_staff`.

**Le premier compte se crée une fois, après les migrations :**

```bash
docker compose -f docker-compose.prod.yml run --rm \
  -e ADMIN_IDENTIFIANT -e ADMIN_MOT_DE_PASSE -e ADMIN_NOM \
  api python manage.py creer_administrateur
```

⚠️ **Et non `createsuperuser`** : celui-là est interactif et attendrait une
saisie qui ne viendra jamais sur un serveur, tandis que son `--noinput` crée un
compte **sans mot de passe utilisable** — donc une administration dans laquelle
personne ne peut entrer. `creer_administrateur` lit l'environnement, ne demande
rien, et est idémpotente : relancée, elle ne repose pas le mot de passe d'un
compte existant.

⚠️ **Changez ce mot de passe depuis l'admin Django une fois entré.** Un mot de
passe passé par l'environnement traîne dans la configuration de la plateforme,
dans l'historique du shell, parfois dans les journaux de démarrage. Il sert à
entrer la première fois. Les comptes suivants se créent dans l'admin Django en
cochant `is_staff`, et se révoquent en le décochant — ce qui **ferme leurs
sessions en cours** dès la requête suivante, sans attendre les douze heures.

Les valeurs qui **doivent** changer par rapport au développement :

| Variable | Valeur serveur |
|---|---|
| `DJANGO_DEBUG` | `0` — sinon la trace et les réglages, donc les identifiants, s'affichent sur toute erreur 500 |
| `DJANGO_ALLOWED_HOSTS` | votre nom de domaine |
| `CORS_ORIGINES` | l'origine publique de la boutique, `https://votredomaine.tg` |
| `CHARGER_DEMO` | `0` — sinon le jeu de démonstration réécrit les données à chaque redémarrage |
| `IMAGE_PREFIXE` | `ghcr.io/<proprietaire>/<depot>`, **en minuscules** |

`CORS_ORIGINES` et `VITE_API_URL` vont **toujours par paire** : si le front change d'adresse, il
faut l'ajouter aux origines autorisées, sinon le navigateur bloque tous les appels sans que le
serveur voie quoi que ce soit.

Si les images du dépôt sont privées, le serveur doit aussi pouvoir les tirer :

```bash
echo "<jeton-personnel-avec-read:packages>" | docker login ghcr.io -u <proprietaire> --password-stdin
```

## 3. Déployer

```bash
git tag v1.0.0
git push origin v1.0.0
```

Ou, depuis l'onglet *Actions*, lancer « Déploiement » à la main — en donnant une étiquette plus
ancienne pour **revenir en arrière** :

```
Actions → Déploiement → Run workflow → etiquette : v0.9.3
```

Le retour arrière est immédiat, parce que l'ancienne image est toujours dans le registre. C'est le
principal bénéfice de ne rien construire sur le serveur.

### Le premier déploiement

L'admin Django (§13.6) est inutilisable sans compte, et le créer demande un terminal :

```bash
ssh utilisateur@serveur
cd ~/groupachat
docker compose -f docker-compose.prod.yml exec api python manage.py createsuperuser
```

Cette commande demande le mot de passe sans l'écrire nulle part — contrairement aux variables
`DJANGO_SUPERUSER_*`, qui le laisseraient dans `docker inspect`. Les laisser vides en production.

## 4. Vérifier

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
curl -fsS https://api.votredomaine.tg/api/campagnes/ | head -c 200
```

Le déploiement attend déjà que l'API réponde avant de se déclarer réussi : si elle ne répond pas
en 30 secondes, il affiche les 50 dernières lignes du journal et échoue, au lieu de signaler un
succès trompeur.

## ⚠️ Ce qui n'est pas couvert

**Il n'y a pas de HTTPS dans ces fichiers.** Aucun certificat, aucune terminaison TLS, aucune
redirection. `manage.py check --deploy` le signale en plusieurs avertissements — tous justes. Il
faut un reverse-proxy devant ces conteneurs : Caddy obtient et renouvelle les certificats tout
seul, Traefik aussi, nginx demande certbot. **Tant que ce n'est pas fait, ne pas mettre le service
devant de vrais acheteurs** : les numéros de téléphone et les adresses de livraison passeraient en
clair.

**Le front a ses deux images, et elles ne contiennent pas nginx.**
⚠️⚠️ Ce paragraphe a dit trois choses successives — *« les images nginx ont été retirées, c'est la
pièce qui manque »*, puis *« le workflow publie `boutique` et `admin` »*, puis *« le front est
construit et servi par l'hébergeur »*. **C'est ce dernier état qui a mis le site en page blanche**,
et la raison vaut d'être retenue : il déplaçait la décision du dépôt vers un champ de formulaire
— le *dossier publié* — et ce champ est resté sur le dossier source.

| Fichier | Sert | Image |
|---|---|---|
| `frontend/Dockerfile` | la boutique, depuis `dist/` | `caddy:2-alpine` |
| `frontend/Dockerfile.admin` | l'administration, depuis `dist-admin/` | `caddy:2-alpine` |

Ils construisent **et** servent : il n'y a plus de dossier à désigner, donc plus de dossier à se
tromper. `caddy file-server` **n'a aucun fichier de configuration**, et sa table de types MIME est
interne — un `.js` sort en `text/javascript` sans qu'on déclare quoi que ce soit.

Mesuré sur `achatgr.com` avant la correction : `/package.json` répondait **200**, `/src/main.tsx`
répondait **200 `application/octet-stream`**, et `/assets/` répondait **404**. Avec ces images, les
deux premiers répondent **404** et le module sort en `text/javascript`.

⚠️⚠️ **`VITE_API_URL` est lue à la CONSTRUCTION et inscrite en clair dans le JavaScript.** Elle
doit donc être posée côté **construction** chez l'hébergeur. En variable d'exécution elle n'a
**aucun effet** et rien ne proteste : le navigateur de chaque visiteur appelle `127.0.0.1:8000`,
c'est-à-dire sa propre machine. La page s'affiche et rien ne se charge. Changer l'adresse de l'API
demande toujours de **reconstruire le paquet**.

⚠️ **L'administration n'est plus derrière un tunnel SSH.** Elle était publiée sur `127.0.0.1:5174`
et atteinte par `ssh -L`. Ce préfixe est parti avec le service. Elle exige maintenant un mot de
passe — une session contre un compte `is_staff` — mais elle affiche des noms, des numéros et des
références de pièces d'identité : **restreindre l'accès à ce sous-domaine chez l'hébergeur reste
la seconde barrière**, et deux barrières valent mieux qu'une devant ces données-là.

**La clôture par la date tourne dans le service `taches`.** ⚠️ Elle n'était planifiée nulle part —
ni ici, ni dans Compose, ni dans la CI. Sans elle, un groupage échu reste `ouverte`, aucun
`Retrait` n'est créé, et **l'argent déjà encaissé ne devient jamais retirable**. Une boucle dans un
conteneur plutôt que la crontab de l'hôte : la crontab vit en dehors du dépôt, s'oublie à la
réinstallation du serveur, et rien ne dirait qu'elle manque.

**L'administration n'a aucun mot de passe.** L'écran A1 n'affiche que des compteurs, mais l'écran
A2 affiche des noms, des numéros et des références de pièces d'identité. Ce qui protège ces
données, c'est le jeton `X-Jeton-Admin` exigé par `/api/dossiers/` : la page s'ouvre, les données
ne viennent pas sans le jeton, et c'est la seule chose qui les protège. **Le serveur web retenu
devra donc poser quelque chose de plus** — un réseau privé, un VPN, ou à défaut une
authentification HTTP — et surtout ne pas publier `dist-admin/` sur une interface ouverte.

**Aucune sauvegarde de la base n'est configurée.** Le volume `donnees-postgres` survit aux
redémarrages et aux `down`, mais pas à une panne de disque ni à un `down -v`. À mettre en place
avant d'avoir des données réelles :

```bash
docker compose -f docker-compose.prod.yml exec -T base \
  pg_dump -U groupachat groupachat | gzip > sauvegarde-$(date +%F).sql.gz
```

**Une seule réplique d'API.** Les migrations tournent au démarrage de chaque conteneur ; avec
plusieurs répliques démarrant ensemble, deux `migrate` concurrents se marcheraient dessus. Il
faudrait alors une tâche de migration distincte, exécutée une fois avant la mise en service.

**Le paiement reste simulé** (§18.2) et **l'authentification des acheteurs repose sur un code SMS
de démonstration** (`SMS_FOURNISSEUR=demonstration`, le code vaut 1234). Ce sont des manques du
produit, pas du déploiement — voir `backend/README.md`.

**Ces workflows n'ont jamais été exécutés.** Leur YAML est validé et les deux fichiers Compose se
résolvent avec `.env.exemple` seul, mais aucune de leurs étapes n'a tourné : il n'y a pas de dépôt
GitHub en face, et le démon Docker n'est pas disponible sur la machine de développement. Attendez
le premier passage pour les croire.
