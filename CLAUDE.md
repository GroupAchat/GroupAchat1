# Group Achat — repères pour travailler sur ce dépôt

Place de marché d'achat groupé pour Lomé, Togo. Django + DRF + PostgreSQL
d'un côté, React + Vite + TypeScript de l'autre.

**Tout est rédigé en français** : documents, code, commentaires, noms de
variables, de modèles, de routes. Un fichier qui mélange `Participation` et
`Order` coûte une traduction mentale à chaque lecture.

> Le `AGENTS.md` du dossier parent (`C:\ALLPROJECT\`) décrit un projet
> React/Vite « figma-make-app » **sans rapport avec celui-ci**. Ne pas
> l'appliquer ici.

## Où se trouve quoi

```
backend/              l'API Django                               → port 8000
  config/             réglages, routes, service des fichiers
  groupachat/
    <sujet>/          le domaine : catalogue, commandes, comptes,
                      echanges, paiements — modèles et vues ensemble
    espaces/          administration et groupeur : des vues, pas
                      des applications ; aucun modèle n'y vit
    noyau/            ce qui traverse tout : accès, limitation
    tests/            les tests qui traversent plusieurs sujets
frontend/             les interfaces web
  commun/             le socle — il n'existe qu'en un exemplaire
  boutique/           acheteurs et groupeurs                   → port 5173
  admin/              console d'administration                  → port 5174
```

| Document | Ce qu'il contient |
|---|---|
| [README.md](README.md) | l'architecture, comment démarrer, les comptes de démonstration |
| [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) | les règles métier : séquestre, KYC, frais, codes de retrait |
| [MANUEL_EXPLOITATION.md](MANUEL_EXPLOITATION.md) | l'exploitation : recrutement des OAG, contrats, conformité, rôles, modèle économique |
| [COOLIFY.md](COOLIFY.md) | le déploiement sur `achatgr.com`, les variables, la sécurité |
| [frontend/commun/README.md](frontend/commun/README.md) | ce que le socle contient **et ne doit pas contenir** |

## Les décisions à ne pas défaire sans raison

**Le socle partagé.** Le client API, les types, la session et la trousse
d'interface vivent dans `commun/`, importés par `@commun/…`. Les dupliquer
garantirait qu'ils divergent, et une divergence sur l'authentification ne se
voit qu'en production. Dès qu'un composant ne sert qu'à une seule interface,
sa place est dans celle-là.

**Une seule origine.** Django sert l'API **et** les deux interfaces
compilées ; c'est le domaine demandé qui décide laquelle s'affiche. Il n'y a
donc ni CORS, ni cookie tiers, ni serveur web devant. Une API sur un
sous-domaine séparé rouvrirait les trois sujets d'un coup.

**Les montants sont des entiers de FCFA.** Le franc n'a pas de centime ; un
décimal n'apporterait que des arrondis.

**Le téléphone est l'identifiant**, normalisé à huit chiffres. Sans ça,
`+22890001122` et `90001122` créeraient deux comptes pour la même personne.

**Le barème a deux axes.** La **tranche** dépend de ce que prend un seul
acheteur — « à partir de 12 pièces, 22 000 » — et reste **figée à la
commande** : elle ne peut jamais remonter. La **chute** dépend du nombre de
participants et s'applique **rétroactivement**, à ceux qui ont déjà payé
comme aux derniers venus ; la différence leur est rendue à la clôture. Une
chute réservée aux derniers arrivés punirait celui qui a fait venir du
monde, et c'est précisément lui qu'on veut récompenser.

Les deux vivent dans **une seule table** : le barème est une grille, et une
grille se range dans une table à deux clés. `PalierPrix.prix_pour()` retient
toujours **le meilleur prix auquel l'acheteur a droit**, jamais le dernier
palier franchi — un barème saisi de travers ne doit pas faire payer plus
cher celui qui prend plus.

**Le séquestre est par campagne**, avec des contraintes en base qui
interdisent de libérer ou rembourser plus que le consigné.

**Publier se paie, et la publication se consomme à la mise en ligne.**
Abonnement au mois (illimité) ou pack de cinq, les deux compteurs
indépendants : un abonnement qui s'achève ne prend pas les publications déjà
payées. Un brouillon ne coûte rien ; un groupage qui échoue ne rend rien —
elle paie la mise en ligne, pas la réussite. Un **refus de l'équipe**, lui,
la rend : la mise en ligne n'a pas eu lieu.

**La relecture avant vitrine dépend du grade** — systématique en Bronze, une
sur quatre en Argent, jamais en Or. Le sondage est déterministe et compté sur
les mises en ligne demandées : un tirage au sort ne s'audite pas. Une
campagne `en_verification` n'est ni listée ni ouvrable, et n'ouvre pas de
séquestre.

**Le retrait du colis appartient à l'acheteur, pas à l'OAG** : bureau de
poste de son choix ou livraison à son adresse, part par part. Il n'y a aucun
point de remise sur la campagne. **L'adresse de livraison ne sort jamais vers
l'OAG** — un bureau de poste est un lieu public, une adresse désigne un
domicile.

**C'est le livreur partenaire qui scanne le code de retrait**, jamais l'OAG :
celui-ci confie le lot à l'agence et ne rencontre pas ses acheteurs. S'il
validait lui-même, celui qui doit livrer signerait sa propre livraison. Le
livreur est aussi le seul à voir l'adresse et le numéro de l'acheteur.

**Le parrainage ne se valide qu'au paiement du filleul.** Un clic ou une
inscription ne valent rien, un filleul n'a qu'un parrain — le premier qui
l'amène —, et le parrain voit le nombre, jamais les noms.

**Les pièces d'identité ne sont jamais servies publiquement** : `/medias/`
refuse le dossier `kyc/`, et une vue séparée vérifie qui demande. Elles ne
partent pas non plus chez Cloudinary — **seuls les médias de catalogue y
vont**. Une adresse de CDN reste publique même quand elle est illisible.

**Les images sont téléversées du navigateur vers Cloudinary**, Django se
contentant de signer l'autorisation (`groupachat/noyau/hebergement.py`).
Faire transiter trois mégaoctets par l'API doublerait l'attente sur une
connexion mesurée. Sans les variables `CLOUDINARY_*`, tout retombe sur le
disque local : les tests et la démonstration n'ont pas besoin d'un compte.

## Lancer et vérifier

```bash
cd frontend && npm install         # une fois
npm run dev                        # boutique
npm run dev:admin                  # console

cd backend
python manage.py migrate
python manage.py charger_demo      # jeu de démonstration, tous états couverts
python manage.py runserver
python -m pytest                   # la suite complète
```

⚠️ **La configuration vient d'un seul `.env`, à la racine** — celui que
lisent Django, Vite et Docker Compose. Pas de second fichier par dossier.

⚠️ **`VITE_API_URL` doit rester vide.** Le client retombe alors sur `/api`,
relayé depuis la même origine. Une adresse absolue rouvre le CORS.

**Le jeu de démonstration suit un numéro de version.** `VERSION_DEMO` dans
`charger_demo.py` décide si un redéploiement remet les données à plat.
**À incrémenter dès qu'on touche au jeu** — sinon les ajouts n'apparaissent
jamais sur un serveur déjà démarré une fois.

## Ce qui est simulé

Aucun SMS n'est envoyé — le code s'affiche à l'écran. Aucun paiement n'est
encaissé, aucun versement effectué. La **comptabilité du séquestre est
tenue pour de vrai** : seule la couche d'exécution est factice, derrière
`_executer_paiement` et la passerelle SMS.

## Écrire du code ici

Les commentaires expliquent **pourquoi**, pas quoi. Un commentaire qui
paraphrase la ligne suivante est du bruit ; un commentaire qui dit « sans
ça, deux acheteurs payaient la dernière place en même temps » sauve une
heure à la relecture.

Les tests décrivent un comportement attendu, pas une implémentation. Et ils
doivent **réellement tourner** : `pytest.ini` collecte `tests.py`,
`test_*.py` et `tests_*.py` — vingt-huit tests avaient dormi sans être
exécutés parce que le troisième motif manquait.

Un test qui ne porte que sur un sujet reste dans son dossier ; ceux qui en
traversent plusieurs vont dans `groupachat/tests/`.
