# Group Achat

Place de marché d'achat groupé pour Lomé, Togo. **Le produit est codé et il tourne** : Django + DRF + PostgreSQL d'un côté, React + Vite + TypeScript de l'autre. Tout — documents, code, commentaires, noms de variables — est rédigé **en français**.

> ⚠️ **Ce paragraphe disait « Projet de conception, pas encore de code : tout le contenu est documentaire ».** C'était vrai au début et ça ne l'est plus depuis longtemps : il y a 70 modules Python, 119 fichiers TypeScript et 293 tests. La phrase est reproduite ici parce qu'un agent qui la lisait en tête de fichier pouvait conclure qu'il n'y avait rien à exécuter.

> Le `AGENTS.md` du dossier parent (`C:\ALLPROJECT\`) décrit un projet React/Vite « figma-make-app » **sans rapport avec celui-ci**. Ne pas l'appliquer ici.

## Les documents et le code

| Fichier | Rôle |
|---|---|
| [PRD.md](PRD.md) | Le PRD d'une page — un paragraphe, puis les détails pour coder |
| [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) | Le document maître : modèle, argent, KYC, admin, livraison, modération, stack |
| [SPEC_ECRANS_FIGMA.md](SPEC_ECRANS_FIGMA.md) | 22 écrans + A1 admin, design system, jeu de données de démonstration |
| [DOCKER.md](DOCKER.md) | Les images, les cibles de construction, et comment lancer la pile en conteneurs |
| [DEPLOIEMENT.md](DEPLOIEMENT.md) | Le déploiement sur un serveur, et ce que la CI fait à chaque poussée |
| `backend/` | Django 5.2 + DRF. `groupachat/` porte le domaine, `config/` les réglages |
| `frontend/` | React 19 + Vite 7 + Tailwind v4. Deux applications, deux ports |
| `docker-compose.yml` | Base et API en conteneurs. ⚠️ Il **ne publie pas** le port de la base — voir ci-dessous |
| `docker-compose.override.yml` | Développement seulement, lu automatiquement : il publie la base sur 5433 |
| `.env` | **Le seul endroit où vit une variable d'environnement.** Jamais commis ; `.env.exemple` le documente |

**Les trois documents produit — PRD, cahier des charges, spec des écrans — se citent entre eux par numéro de section.** Toute insertion ou renumérotation oblige à corriger les renvois dans les deux autres, **et dans le code** : les commentaires y citent des `§` en permanence. Vérifier avec `grep -rno "§[0-9.]*" *.md` et `grep -rn "§" backend/ frontend/src/`.

> ⚠️ Cette phrase parlait de **quatre** documents : le quatrième était `LIVRAISON.md`, le dossier de négociation avec les transporteurs, supprimé depuis. `maquettes/` et `medias/` ont disparu de la même façon.

## Règles produit non négociables

Ce sont des décisions tranchées par l'utilisateur, pas des préférences. Ne pas les rouvrir sans qu'il le demande.

- **Anonymat dans les deux sens.** L'acheteur ne voit qu'un pseudonyme de groupeur ; le groupeur ne voit que des **codes et des quartiers**, jamais un nom, un numéro ou une adresse. C'est ce qui protège le modèle contre la désintermédiation. Seule la page du livreur (écran 22) réunit nom, adresse et téléphone.
- **Le compte acheteur est un vrai compte, et il est demandé avant d'engager quelque chose.** ⚠️ **Cette règle a été réécrite deux fois par l'utilisateur, et l'ancienne version se lisait : « Pas de mur d'authentification. On navigue librement ; le compte est demandé au moment de payer. »** Ce qui vaut aujourd'hui : on **navigue** toujours librement — fil, catalogue, fiches, questions déjà posées — mais **rejoindre un groupage ou poser une question demande un compte**, et un message explique pourquoi avant d'ouvrir le formulaire. L'inscription est **classique** : **prénom, numéro obligatoire, courriel facultatif**, puis vérification du numéro par code SMS. ⚠️ **Le formulaire a porté un mot de passe, et ne le porte plus** — chaque champ posé devant quelqu'un qui s'apprête à payer est un acheteur perdu. Il reste **posable depuis l'écran de profil**, pour se reconnecter sans attendre de SMS. ⚠️ Conséquence assumée : la règle « ne dessine jamais deux boutons *Se connecter* et *Créer un compte* » (§1.5 de la spec) **est volontairement enfreinte** — c'est ce que « classique » veut dire. Ce qu'elle protégeait tient autrement : l'inscription est en bouton plein, la connexion en lien discret.
- **Le numéro de téléphone identifie le compte, et lui seul.** Le courriel est facultatif et ne sert jamais à se connecter : une partie du cœur de cible à Lomé n'a pas d'adresse consultée mais répond au téléphone. ⚠️ **Le code SMS reste la voie de récupération** et lève le verrou des cinq échecs de mot de passe : c'est ce qui dispense d'écrire un parcours « mot de passe oublié », et ce qui garantit qu'un mot de passe perdu ne ferme jamais un compte.
- **Un groupage clôturé quitte le catalogue** : plus sur le fil, plus dans la recherche, plus dans les catégories. Le filtre est **côté serveur**. Sa fiche reste atteignable par son lien, et le groupeur voit toujours les siens.
- **Aucun prix barré, aucun badge de réduction, aucun « au lieu de ».** Nulle part.
- **Des paliers dégressifs, facultatifs, posés par le groupeur.** « 1 part : 5 000 F · à partir de 5 : 3 500 F ». ⚠️ **Ce n'est pas un prix barré et ça ne contredit pas la règle ci-dessus** : aucun prix de référence n'est inventé, il y a **plusieurs prix vrais** et celui qu'on paie dépend de ce qu'on prend. C'est la définition du prix de gros, donc du produit. C'est aussi la réponse à « comment rendre le prix attirant sans prix barré ».
- ⚠️ **Le seuil porte sur la quantité prise par l'acheteur, jamais sur le nombre de participants.** Un seuil collectif serait un **déclencheur**, que la règle de l'objectif interdit — et surtout le prix ne serait **pas connu au moment de payer** : il baisserait après coup, pour des gens dont l'argent est déjà parti au portefeuille du groupeur. Il faudrait rembourser rétroactivement un argent qu'on ne détient pas.
- **Deux verrous sur la grille**, posés par `PalierPrix.clean` : le seuil est d'**au moins 2 parts** — à 1 il remplacerait `prix_part` sans le dire — et chaque palier est **strictement moins cher** que le précédent. Une grille qui monte ferait payer **plus cher en prenant plus**.
- **Le groupeur déclare un objectif de participants**, obligatoire à la création, affiché aux acheteurs en **barre de progression** (§2.5 de la spec). ⚠️ **Ni plafond, ni minimum, ni déclencheur** : dépasser est permis, un groupage sous son objectif peut aboutir, et seule la date clôture. Jamais « places disponibles », « complet », ni « il manque N personnes ».
- **L'argent de l'acheteur va au portefeuille du groupeur**, tenu par la plateforme, dès le paiement. Nous ne détenons plus les fonds pour notre compte : **nous ne versons rien, nous exécutons des retraits.**
- **Le solde du groupeur est retirable à la clôture**, intégralement, avant la livraison. ⚠️ **Et c'est son argent, pas le nôtre : aucun écran acheteur ne doit écrire « vos N F sont détenus par Group Achat ».** Les fonds vont à son portefeuille dès le paiement ; la plateforme tient son compte, elle ne détient pas les fonds pour le sien. La formulation acheteur retenue est « votre paiement va au portefeuille du groupeur, qui ne peut le retirer qu'à la clôture ». Reste interdit : « bloqué jusqu'à la livraison » — le groupeur est payé **avant** qu'on livre. Tableau des formulations interdites au §1.7 de la spec des écrans.
- **Aucun encart bleu sur un écran acheteur.** ⚠️ Le `BandeauConfiance` a été **supprimé**, et les encarts `info` sont passés au neutre : le bleu est le chrome du côté groupeur (§1.2) et s'était réinstallé par petites boîtes un peu partout. Seule exception, la coche « vérifié » de 13 px à côté d'un pseudonyme — c'est une marque, pas une boîte de réassurance. La promesse « livré, ou remboursé » subsiste, en texte.
- **1 500 F par groupage abouti, et c'est le seul revenu.** À la charge du groupeur, **retenus au retrait**. **Ce n'est pas un pourcentage** : un écran qui affiche « 5 % » ou « commission » est un écran à corriger.
- **Le devis fournisseur ne débloque plus l'argent.** Il constate, il ne conditionne pas — §10.2 du cahier des charges, et §9.1 pour ce que ça coûte.
- **Aucun frais de livraison facturé à l'acheteur.** ⚠️ **Cette règle disait : « Frais de livraison calculés selon la position de l'acheteur ; la fonction renvoie 1 000 F pour l'instant. »** L'acheteur ne paie désormais **que sa part** — `FRAIS_LIVRAISON_PROVISOIRES` vaut zéro, côté serveur comme côté client, et les récapitulatifs masquent la ligne tant qu'elle est nulle. La position reste **conservée sur la commande** : c'est elle que suit le livreur, et elle redeviendra la base d'un calcul si les frais reviennent.
- **L'acheteur paie la livraison au livreur, à la remise** — hors plateforme. Group Achat n'encaisse donc rien à ce titre, et son seul revenu reste les 1 500 F par groupage abouti. ⚠️ **Cela oblige à le dire avant** : un total qui n'inclut pas la livraison n'est pas un mensonge, mais ne pas prévenir en est un par omission — l'acheteur découvrirait la dépense à sa porte, livreur devant lui. La phrase vit dans `MENTION_LIVRAISON` (`domaine/livraison.ts`), **à un seul endroit**, et s'affiche sur l'écran de commande, celui du paiement et la confirmation.
- ⚠️ **Le montant de la livraison n'est pas connu**, et aucun écran ne l'annonce. Le tarif de l'agence partenaire n'a jamais été négocié — `LIVRAISON.md`, le dossier qui devait le porter, a été supprimé du dépôt. On écrit qu'on ne le connaît pas plutôt que de l'inventer. Le jour où il existe, il s'écrit dans `MENTION_LIVRAISON`, une fois.
- **Pas de messagerie privée.** Questions publiques uniquement, filtrées avant publication. ⚠️ **La cloche de notifications n'y change rien** : c'est **la plateforme qui rédige**, le groupeur ne fait que déclencher un fait (« le produit est arrivé »), et la réponse ne lui rend qu'un **compte**, jamais une liste de destinataires. Aucun champ de texte ne traverse cette route — §1.10 de la spec des écrans.
- **La clôture par la date passe par une tâche planifiée**, `python manage.py cloturer_les_groupages_echus`. ⚠️ **Cette règle disait « à brancher sur le cron du VPS au déploiement » — et elle ne l'était nulle part** : ni dans Compose, ni dans la CI, ni dans la documentation. Elle tourne maintenant dans le service **`taches`** de `docker-compose.prod.yml`, toutes les dix minutes. Une boucle dans un conteneur plutôt que la crontab de l'hôte : la crontab vit en dehors du dépôt, s'oublie à la réinstallation du serveur, et rien ne dirait qu'elle manque. Sans elle, un groupage échu reste `ouverte`, aucun `Retrait` n'est créé, et **l'argent déjà encaissé ne devient jamais retirable**.
- **Sur téléphone, la recherche est une loupe**, pas un champ permanent. ⚠️ **La spec disait l'inverse** — *« une loupe se remarque moins qu'un champ »* — et l'utilisateur a tranché pour la loupe : le champ occupait une ligne entière sur 390 px. Il **se déplie** au toucher, sur une seconde ligne qui n'existe que pendant la recherche ; c'est le seul champ de recherche de l'application, donc le replier sans le rendre atteignable l'aurait supprimée. Ce que ça coûte : la découvrabilité.
- **Web React d'abord** (mobile d'abord, 390 px), mobile Android/iOS ensuite. Django + DRF + PostgreSQL. **Paiement simulé** jusqu'à l'agrément d'un agrégateur.

## Jeu de données de démonstration

Les additions doivent tomber juste — un jury vérifie.

- Campagne C1 : **Écouteurs filaires avec micro**, **4 000 F** la part, **32 commandes**
- Total payé par l'acheteur : **4 000 F** — la part, et rien d'autre *(c'était 5 000 F quand la livraison était facturée)*
- Collecté **128 000 F** − frais Group Achat **1 500 F** = **126 500 F retirables**
- Second groupage du portefeuille : baskets, 41 × 9 800 = 401 800 F − 1 500 = **400 300 F retirés**
- Code de livraison : `K7M-4PQ` · Acheteuse : Akosua Doe, Tokoin · Groupeuse : Mama Gro

## Chromes

Deux chromes, définis au §1.2 de la spec des écrans. **Ne jamais les inverser.**

- **Acheteur (écrans 1-12) : orange dominant.** `primaire` `#CC4A00` (blanc 4,62:1), `marque` `#FF6A00` **texte sombre uniquement** — blanc sur orange vif = 2,87:1, interdit.
- **Groupeur (écrans 13-21) : bleu dominant.** `confiance` `#1E3A8A` (blanc 10,36:1). L'orange n'y est qu'une alerte.
- **Admin (A1) : chrome neutre**, ni orange ni bleu, et **1 280 × 800** — seul écran destiné à un ordinateur.
- Orange sur aplat bleu = 3,61:1 : gros caractères et pastilles pleines seulement.

**Tout contraste doit être calculé, jamais estimé.**

## Comment lancer le projet

Quatre services, quatre ports. **Les ports sont fixes** (`strictPort`), et ce
n'est pas de la coquetterie : `VITE_API_URL` et `CORS_ORIGINES` les visent déjà,
donc un port qui glisse casse les appels sans rien dire.

| Service | Port | Commande | Depuis |
|---|---|---|---|
| **Boutique** — acheteur, groupeur, livreur | **5173** | `npm run dev` | `frontend/` |
| **Administration** — écran A1 | **5174** | `npm run dev:admin` | `frontend/` |
| **API Django** | **8000** | `python manage.py runserver 8000` | `backend/` |
| **PostgreSQL** | **5433** | `docker compose up -d base` | la racine |

Le site de présentation n'a pas de port à lui : il est servi par la boutique,
sur `http://localhost:5173/presentation/`.

### ⚠️ La base de données, et le piège qui a coûté une demi-journée

**5433 et non 5432, et c'est volontaire** : un PostgreSQL est souvent déjà
installé sur le poste et occupe 5432. Publier la base du projet sur ce port
échouerait, ou pire — ferait croire que tout marche en parlant au mauvais
serveur.

**`docker-compose.yml` ne publie pas le port de la base**, et ce refus est
motivé : en production elle n'a aucune raison d'être joignable depuis la machine
hôte, seule l'API lui parle par le réseau interne. Mais en développement on
lance `migrate`, les tests et `runserver` **depuis la machine**. D'où
`docker-compose.override.yml`, que Compose lit tout seul et qui n'est jamais
déployé : la décision de production reste intacte, le besoin du développement
vit à côté sans la contredire.

**Django ne lit qu'une seule variable pour sa base : `DATABASE_URL`.** Les
`POSTGRES_*` servent au conteneur. Les deux doivent concorder, et `.env.exemple`
le dit : *« Le mot de passe doit être le même que `POSTGRES_PASSWORD` »* — le
premier crée le rôle dans le conteneur, le second s'y connecte depuis la
machine. S'ils divergent, le rôle créé n'est pas celui qu'on présente.

⚠️ **Sans `DATABASE_URL`, Django retombe silencieusement sur SQLite.** C'est
voulu — on peut cloner et lancer les tests sans rien installer — mais il faut le
savoir, sinon on croit travailler sur PostgreSQL alors qu'on écrit dans un
fichier.

⚠️ **Et si la base est injoignable, `runserver` se fige sans un mot.** Il
imprime « System check identified no issues », puis bloque à la vérification des
migrations et **n'ouvre jamais le port 8000**. Aucune erreur, aucune trace. Le
symptôme ressemble à une panne du code ; la cause est toujours la base. Le
réflexe utile :

```
docker compose ps base          # healthy ?
docker compose up -d base       # sinon
```

### Premier démarrage, ou base perdue

```
docker compose up -d base
cd backend && python manage.py migrate
python manage.py charger_demo
```

`charger_demo` reconstruit le jeu de démonstration ci-dessous, aux centimes
près. **La base de développement est donc toujours reconstructible** — c'est ce
qui fait qu'en perdre une n'est pas un drame, à condition qu'elle appartienne au
projet et non à un conteneur venu d'ailleurs.

### Les tests

```
cd backend && python manage.py test groupachat --noinput
```

**330 tests, environ seize minutes** — ce paragraphe annonçait *« 293 tests,
environ huit minutes »*, et les deux chiffres avaient vieilli. `--noinput` évite
la question sur la base de test restée d'une exécution précédente.
⚠️ **Ne jamais tuer une connexion PostgreSQL pour « débloquer » une base de
test occupée** : on tue l'exécution en cours, et on se retrouve avec une base à
moitié créée.

### ⚠️⚠️ Une suite verte en local ne dit rien de la CI, et voici pourquoi

**La CI pose `DJANGO_DEBUG=0` pour tout le job**, parce que c'est le réglage de
production et que c'est tout l'intérêt de la faire tourner. Or `settings.py`
active `SECURE_SSL_REDIRECT` dès que `DEBUG` est faux, et le client de test de
Django parle **en clair** sur `http://testserver` sans envoyer de
`X-Forwarded-Proto`.

Résultat : Django redirige vers `https://testserver` **avant d'atteindre la
moindre vue**, et **toute la suite backend tombe sur des `301`**. Le travail
échouait en quarante-huit secondes — trop vite pour une suite de 330 tests,
c'est le signe qu'on n'a jamais atteint les tests.

Chacun des trois maillons est juste pris isolément ; c'est leur rencontre qui
casse. L'étape des tests pose donc `DJANGO_HTTPS: "0"`, **et elle seule** : le
défaut de production reste `1`, et `check --deploy` garde son propre
environnement pour vérifier la redirection telle qu'elle sera en ligne.

**Le réflexe utile avant de pousser**, qui reproduit la CI :

```
DJANGO_DEBUG=0 DJANGO_HTTPS=0 DJANGO_SECRET_KEY=peu-importe \
  python manage.py test groupachat --noinput
```

Côté client, `npm run typecheck` et `npm run build` — la construction fait les
deux paquets, boutique et administration.

## Le déploiement

**Trois services en conteneur**, décrits par `docker-compose.prod.yml` : `base`,
`api`, `taches`. Le workflow `.github/workflows/deploiement.yml` ne publie plus
qu'une image, celle de l'API.

⚠️⚠️ **Ce paragraphe en annonçait cinq**, dont `boutique` et `admin` — deux
images **nginx** construites depuis `frontend/`. **nginx a été retiré du
dépôt** : `frontend/Dockerfile`, `nginx.boutique.conf`, `nginx.admin.conf` et
`frontend/.dockerignore` ont été supprimés, ainsi que les services, les étapes
de CI et les étapes de publication qui les portaient. Le front est construit et
servi par **Coolify**.

> La bonne manière de lire les trois états successifs de cette section — pas de
> front conteneurisé, puis deux images nginx, puis plus rien — c'est que **le
> serveur du front n'a jamais été une décision de ce dépôt**, et qu'il a fini
> par ne plus y vivre du tout.

### Le front : ce qu'il faut publier, et ce qu'il ne faut surtout pas

```
npm ci && npm run build
```

| | À publier |
|---|---|
| **Boutique** | `frontend/dist/` |
| **Administration** | `frontend/dist-admin/` |

⚠️⚠️ **Publier `frontend/` au lieu de `frontend/dist/` donne une page blanche**,
et c'est arrivé. Le symptôme, dans la console du navigateur :

```
Failed to load module script: Expected a JavaScript-or-Wasm module script
but the server responded with a MIME type of "application/octet-stream".
```

Le diagnostic tient en une ligne : **le navigateur demande `/src/main.tsx`.**
Ce chemin n'existe que dans l'`index.html` **source** ; celui de `dist/` charge
`/assets/index-….js`. Et `application/octet-stream` plutôt qu'une page de repli
prouve que le fichier TypeScript **existe vraiment sur le serveur**. Donc c'est
le dossier source qui est publié, et `npm run build` n'a pas tourné.

⚠️ **`dist-admin/` ne contenait pas d'`index.html`**, seulement `admin.html` —
parce que `rollupOptions.input` vaut `admin.html`. Les deux serveurs que ce
dépôt contrôlait s'en accommodaient, donc le défaut était invisible de
l'intérieur ; tout serveur statique aurait répondu **404** à la racine d'une
page d'administration. `vite.admin.config.ts` écrit maintenant un `index.html`
**à côté** de `admin.html`.

⚠️⚠️ **`VITE_API_URL` est lue à la CONSTRUCTION, pas à l'exécution.** Vite
l'inscrit en clair dans le JavaScript produit ; aucun serveur Node ne la relit
au démarrage. Elle doit être posée **côté construction** chez l'hébergeur. En
variable d'exécution elle n'a **aucun effet** et **rien ne proteste** : le
navigateur de chaque visiteur appelle `127.0.0.1:8000`, c'est-à-dire sa propre
machine. La page s'affiche et rien ne se charge.

### L'administration a un mot de passe

⚠️⚠️ **Ce paragraphe disait : « l'écran A1 s'ouvre sans mot de passe ».**
Il ne s'ouvre plus sans : l'administration se connecte par **identifiant et mot
de passe**, contre un compte Django `is_staff`. Ce qui a remplacé le jeton
unique et partagé :

| | Le jeton partagé | La session |
|---|---|---|
| Distingue deux administrateurs | non | **oui** |
| Se révoque pour une personne | non — il fallait le changer pour tous | **oui**, en décochant `is_staff` |
| Résiste à l'essai systématique | rien ne comptait les échecs | **5 essais, puis 15 minutes** |
| « décidé par » sur une décision KYC | ce qu'on voulait bien saisir | **le compte connecté** |

Le dernier n'est pas cosmétique : le §10.5 confie la validation d'un dossier à
un humain parce que, le jour d'un litige, **ce dossier est notre seul recours
contre le groupeur**. Un journal dont l'auteur est déclaratif ne prouve rien.

**Le premier compte se crée par `python manage.py creer_administrateur`**, qui
lit `ADMIN_IDENTIFIANT` et `ADMIN_MOT_DE_PASSE` dans l'environnement.
⚠️ **Et non `createsuperuser`** : celui-là est interactif et se figerait sur un
serveur sans terminal, tandis que son `--noinput` crée un compte **sans mot de
passe utilisable** — donc une administration dans laquelle personne ne peut
entrer. La commande est idempotente : relancée, elle ne repose pas le mot de
passe d'un compte existant, sinon un `.env` oublié sur le serveur annulerait en
silence tout changement fait depuis l'interface.

⚠️⚠️ **Le `127.0.0.1:5174` de l'administration a disparu avec son service**, et
c'est la perte la plus sérieuse de ce retrait. Le port n'était ouvert que sur
la boucle locale du serveur ; on l'atteignait par
`ssh -L 5174:127.0.0.1:5174 utilisateur@serveur`, et depuis l'extérieur il
n'existait pas.

Cet écran affiche des **noms, des numéros de téléphone et des références de
pièces d'identité**. Le mot de passe est maintenant la première barrière ;
**restreindre l'accès à ce sous-domaine chez l'hébergeur doit rester la
seconde.** Deux barrières valent mieux qu'une devant ces données-là.

⚠️ **Ce qui reste à faire avant une vraie mise en ligne** : le dépôt distant
`origin` pointe sur un autre projet, il n'y a **aucune terminaison HTTPS** dans
ces fichiers, et l'espace groupeur s'identifie encore par `?telephone=` sur
douze routes, dont le retrait d'argent.

## Comment éditer ces fichiers — documents **et** code

**Les heredocs Bash cassent sur les apostrophes françaises** (`l'argent`, `d'achat`) — erreur `unexpected EOF`. Même problème avec `python -c`.

Méthode qui marche : écrire un script de correctifs dans le **scratchpad** avec l'outil `Write`, puis l'exécuter par son chemin.

```python
# -*- coding: utf-8 -*-
import io
p = r'C:\ALLPROJECT\Professionnel\GroupAchat\CAHIER_DES_CHARGES.md'
s = io.open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])   # garde-fou indispensable
    s = s.replace(old, new)

rep("ancien texte", "nouveau texte")
io.open(p, 'w', encoding='utf-8').write(s)
```

L'`assert` sur le nombre d'occurrences évite les remplacements partiels silencieux. **Toujours `grep` la formulation exacte avant d'écrire le
correctif** : ces fichiers ont été réécrits souvent, et la phrase mémorisée
n'est pas toujours celle du fichier.

La même méthode vaut pour le code — `.py`, `.tsx`, `.ts`. Elle a servi à toutes
les modifications de ce dépôt.

### ⚠️ Les deux pièges qui font échouer l'`assert`

**L'espace fine insécable.** Le français typographique met U+202F avant `:` `;`
`?` `!`, et ces fichiers en contiennent. Recopié de mémoire, on écrit une espace
ordinaire ou U+00A0, la chaîne ne correspond plus, et l'`assert` tombe sur
`0 occurrence` — en désignant une phrase qui semble pourtant identique à l'œil.
Ça s'est produit deux fois dans la même session.

**Le remède, quand l'ancrage par chaîne résiste : ancrer par numéro de ligne.**
On repère les bornes du bloc par un préfixe stable en ASCII, on vérifie le
contenu, puis on remplace la tranche :

```python
lignes = io.open(p, encoding='utf-8').read().split('\n')
debut = next(i for i, l in enumerate(lignes) if l.startswith('  if (chargement)'))
fin = next(i for i, l in enumerate(lignes) if i > debut and l == '  }')
assert 'ListeEnChargement' in '\n'.join(lignes[debut:fin + 1])   # on vérifie
lignes[debut:fin + 1] = NOUVEAU.split('\n')
```

⚠️ **Relever tous les index avant la moindre suppression.** Marquer les lignes
au fur et à mesure décale celles qui suivent, et le tour suivant lit la mauvaise.

**Les homoglyphes cyrilliques et grecs.** Un `е` cyrillique (U+0435) au milieu
d'un mot français compile, passe les tests, et casse une recherche de texte des
mois plus tard. Ils se glissent dans du texte généré. À vérifier avant de
conclure :

```python
import unicodedata
mauvais = [c for c in s if ord(c) > 127
           and ('CYRILLIC' in unicodedata.name(c, '')
                or 'GREEK' in unicodedata.name(c, ''))]
```

## Ton de rédaction

Français, phrases pleines, pas de listes à puces télégraphiques. Chaque décision est **justifiée**, et les coûts d'un choix sont dits franchement plutôt que passés sous silence. Quand un chiffre n'est pas connu — les tarifs des transporteurs par exemple — on écrit qu'on ne le connaît pas, **on ne l'invente pas**.

## Git

Branche `master`. **Ne jamais committer sans que l'utilisateur le demande** : il relit avant.
