# Backend — Group Achat

Django 5.2 + DRF. Il porte les règles que le cahier des charges verrouille :
l'argent, l'anonymat, l'idempotence du paiement et le filtre des messages.

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt

.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py charger_demo    # le jeu du §3
.venv/Scripts/python manage.py runserver       # http://127.0.0.1:8000

.venv/Scripts/python manage.py test groupachat # 252 tests
```

## ⚠️ Une tâche planifiée est obligatoire en production

```bash
.venv/Scripts/python manage.py cloturer_les_groupages_echus
.venv/Scripts/python manage.py cloturer_les_groupages_echus --a-blanc  # pour regarder d'abord
```

**« Seule la date clôture »** est une règle produit non négociable, et elle ne
l'était pas dans le code : `cloturer_campagne` n'avait que deux appelants, le
bouton « Clôturer maintenant » du groupeur et les chargeurs de démonstration.
Rien ne s'exécute quand une date passe — il faut donc quelque chose qui
regarde l'heure.

Sans cette tâche branchée sur le cron du VPS, un groupage dont la date tombe :

- **disparaît du catalogue** — l'écran 2 écarte les `date_fin` passées — donc
  plus personne ne le voit, pas même nous ;
- **ne crée aucun `Retrait`**, donc l'argent déjà encaissé auprès des acheteurs
  **ne devient jamais retirable**. Le portefeuille du groupeur affiche zéro sur
  une collecte réelle ;
- laisse ses commandes en `payee` au lieu de `cloturee`, donc l'écran 9
  continue de promettre « détenu jusqu'à la clôture » sur un groupage échu ;
- **n'envoie pas la notification de clôture**, puisque c'est
  `cloturer_campagne` qui l'envoie.

Autrement dit, un groupeur qui oublie un bouton bloque l'argent de ses
acheteurs sans que personne ne soit averti. Un passage par quart d'heure
suffit : la clôture n'a pas besoin d'être à la seconde, et l'écran acheteur
n'affiche « il reste N heures » qu'à l'heure près.

Elle **n'annule rien** : un groupage sous son objectif de participants se
clôture comme les autres et peut aboutir. L'annulation reste une décision,
prise à l'écran 16.

## La base de données

**PostgreSQL dès que `DATABASE_URL` est renseignée, y compris pour les tests.**
Le moteur de test doit être celui de la production : SQLite et PostgreSQL
diffèrent sur les transactions, les contraintes et les types, et une suite
verte sur l'un peut échouer sur l'autre.

SQLite reste le **secours** quand aucune `DATABASE_URL` n'existe, pour qu'on
puisse cloner le dépôt et lancer les tests sans rien installer. Mais un secours
silencieux est un piège — on pourrait valider pendant des semaines en croyant
tester PostgreSQL. D'où :

```bash
.venv/Scripts/python manage.py verifier_base
```

Elle affiche le moteur, la base, le serveur et la version, et **avertit
explicitement** quand on est sur SQLite.

### L'instance de développement, port 5433

La machine porte déjà PostgreSQL 17, mais son serveur exige un mot de passe et
tourne sous un compte de service : sans droits administrateur, on ne peut ni y
créer un rôle, ni recharger sa configuration. Plutôt que de modifier un serveur
auquel on n'a pas droit, l'outillage en monte un second :

```bash
python outils/instance_postgres.py
```

- **les mêmes binaires PostgreSQL 17**, donc c'est le vrai moteur de production
  qui exécute les tests, pas une approximation ;
- données dans `backend/.pgdata`, ignoré par git ;
- écoute sur **127.0.0.1:5433** : ne touche ni au port ni aux données du
  serveur installé, qui continue de tourner sans rien savoir de lui ;
- rôle avec **mot de passe généré**, pas `trust` — une instance de
  développement sans authentification est une mauvaise habitude qui finit par
  se retrouver ailleurs ;
- met à jour la ligne `DATABASE_URL` du `.env` **de la racine**, ignoré par
  git, et ne touche à rien d'autre dedans.

Pour travailler sur le serveur installé (port 5432), il suffit de remplacer
`DATABASE_URL` dans `.env` : rien d'autre dans le code ne dépend du port.

⚠️ **Piège Windows, déjà payé une fois.** Un serveur démarré par `pg_ctl` hérite
des descripteurs du parent. Avec `subprocess.run(capture_output=True)`, le
script attend une fin de flux qui n'arrive jamais et se bloque indéfiniment,
alors que le serveur tourne très bien. Toutes les commandes `pg_ctl` de
l'outillage utilisent donc `DEVNULL`.

## Vérifier l'API de bout en bout

```bash
python outils/verifier_api.py
```

Il remet la base à neuf, recharge le jeu de démonstration, démarre un serveur
**sur un port libre** — pour ne pas interroger par mégarde un serveur resté en
route sur une autre base, ce qui est exactement l'erreur commise en écrivant
cet outil — puis vérifie douze points : catalogue public, montants du fil
rouge, absence d'identité côté groupeur, idempotence du paiement, zone non
desservie, modération.

## L'architecture

```
backend/
├── config/              Réglages, routes
├── groupachat/
│   ├── domaine.py         L'argent, le code de livraison, le KYC — zéro Django
│   ├── moderation.py      Le filtre des messages publics (§14.2)
│   ├── api.py             Sérialiseurs et vues DRF
│   ├── comptes/           Acheteur, Groupeur, dossier KYC
│   ├── catalogue/         Campagne (« groupage » à l'écran)
│   ├── commandes/         Commande, Versement, paiement, clôture
│   ├── echanges/          Question, Demande
│   └── tests/             63 tests, nommés d'après la règle qu'ils protègent
```

`domaine.py` et `moderation.py` **ne connaissent ni Django ni la base**. Ce
sont les règles que le cahier des charges verrouille, et elles doivent pouvoir
se lire et se tester sans monter une application.

Ils ont un **pendant côté React**, dans `frontend/src/domaine/`. Les deux
implémentations sont volontairement redondantes : le client calcule pour
afficher, le serveur calcule pour encaisser, et **c'est le serveur qui fait
foi**. Quand une règle change d'un côté, elle change de l'autre.

## Ce que les tests protègent

Les tests portent le nom de **la règle**, pas celui de la fonction : quand l'un
casse, on doit savoir ce qui ne tient plus.

### L'argent

- 128 000 − 1 500 = **126 500** et 401 800 − 1 500 = **400 300** — un jury
  refait ces calculs ;
- **les frais sont un montant fixe**, 1 500 F par groupage abouti, et jamais un
  pourcentage. Un test les compare sur trois collectes très différentes : c'est
  la règle qui se perd le plus vite, parce qu'un pourcentage remis « comme
  avant » passerait inaperçu sur un seul groupage ;
- **les frais ne portent jamais sur les frais de livraison.** Avec un montant
  fixe, l'assiette ne change plus le prélèvement : le test vérifie donc ce qui
  reste faux dans ce cas, le **net**, qui porterait 32 000 F qui ne sont pas au
  groupeur ;
- **jamais de net négatif** : sur un groupage plus petit que les frais, les
  frais sont ramenés à la collecte ;
- 4 000 + 1 000 = **5 000 F payés** — l'erreur la plus facile de ce produit
  est d'afficher 4 000 là où l'acheteur paie 5 000 ;
- les frais de livraison **ne se multiplient pas** par la quantité : un colis,
  des frais ;
- **aucun frais sur un groupage annulé** : la fonction ne crée aucun `Retrait`,
  pas même une ligne à zéro ;
- **le devis fournisseur ne bloque plus le retrait**, et un test le dit
  explicitement. C'est une perte de levier assumée (§9.1) : s'il casse un jour,
  c'est que le verrou a été rétabli, ce qui demande de rouvrir le cahier des
  charges et pas seulement le test.

### L'anonymat (§1.7)

Les tests sont volontairement **méfiants** : ils ne vérifient pas que l'API
renvoie les bons champs, ils vérifient qu'elle ne renvoie **aucun** champ
interdit — nom, numéro, repère, référence à l'acheteur. Un
`fields = "__all__"` ajouté par distraction les fait tomber, ce qui est le but.

- ce que le groupeur voit d'une commande : **un code et un quartier** ;
- ce que l'acheteur voit du groupeur : **un pseudonyme** ;
- on ne voit pas les commandes d'un autre.

### Le paiement

- **deux appels avec la même clé d'idempotence ne créent qu'une commande**, et
  le code de livraison ne change pas au rejeu. L'API répond 201 puis 200 ;
- un total fabriqué par le client est refusé : le serveur recalcule ;
- on ne commande pas dans une campagne fermée, ni dans une zone non desservie.

### La modération (§14.2)

- « 20 litres » et « 2 paires » passent ; un numéro de téléphone non ;
- le **passage en cause** est renvoyé, et c'est le numéro qui est signalé, pas
  le « Appelez-moi » qui le précède — c'est le numéro qu'il faut effacer ;
- la copie de refus ne contient ni « interdit », ni « violation », ni
  « contournement » côté acheteur ; côté groupeur elle est plus ferme et parle
  de suspension ;
- **le serveur refait le contrôle que le client a déjà fait.** Un appel direct
  à l'API est bloqué comme le reste.

### La photo d'une demande (écran 11)

- une demande **sans** photo passe : le §1.0 plafonne le formulaire à cinq
  champs, la photo est un bonus et pas une condition ;
- les **octets ne partent jamais dans la liste** des demandes. Le sérialiseur
  ne rend qu'une `photo_url` ; cent demandes sérialisées avec leurs octets
  feraient trente mégaoctets de réponse pour des images que l'écran
  n'affichera peut-être pas (§18.1) ;
- un fichier qui **se déclare** image sans en être une est refusé. C'est le
  contrôle qui compte : le `Content-Type` du formulaire vient du client, seuls
  les premiers octets ne mentent pas ;
- une photo trop lourde est **refusée, pas ignorée**. L'acheteur a attendu son
  téléversement sur un forfait compté : le laisser croire sa demande partie
  avec la photo serait un mensonge que rien à l'écran ne corrigerait ;
- la photo d'un autre acheteur répond **404, et non 403** — « interdit »
  confirmerait que la demande existe.

⚠️ **Les octets sont en base, et c'est provisoire.** Le §18 du cahier des
charges laisse le stockage des médias « à définir » et le §10.5 explique
pourquoi `MEDIA_ROOT` serait le mauvais endroit : poser un `ImageField`
aurait tranché à la place de l'utilisateur. Le plafond de 300 ko
(`domaine.PHOTO_DEMANDE_MAX_OCTETS`) est ce qui rend l'attente tenable — mille
demandes pèsent alors 300 Mo, ce qui se sauvegarde encore. Le jour où le
stockage objet existe, `photo` et `photo_type` deviennent une référence et le
reste de la chaîne ne change pas.

### Le KYC (§10.5)

- le **contrôle n° 2** bloque le prête-nom à l'enregistrement, et tolère
  « MENSAH Akossiwa » pour « Akossiwa Mensah » ;
- un groupeur sans dossier validé ne lance aucune campagne ;
- les plafonds suivent les niveaux, et celui du niveau Établi reste `None` —
  au cas par cas, et on n'invente pas de valeur.

## Ce qui n'est pas encore là

- **Le paiement réel.** `enregistrer_paiement` enregistre la commande comme si
  l'encaissement avait réussi. L'appel à l'agrégateur viendra entre la
  vérification de la clé d'idempotence et la création de la commande (§18.2).
- **L'authentification.** L'acheteur est identifié par son numéro, comme dans
  la feuille de connexion de l'écran 4. Il n'y a ni jeton ni session : à
  brancher avant toute mise en ligne.
- **Les écrans groupeur et admin côté serveur.** Les modèles sont là ; les
  points d'entrée du portefeuille, des statistiques et des files
  d'administration restent à écrire. L'essentiel du travail d'administration
  vit de toute façon dans l'admin Django (§13.6).
- **Le front ne parle pas encore à cette API** : il lit ses propres constantes.
  Les champs portent les mêmes noms des deux côtés pour que la bascule soit un
  `fetch`.
