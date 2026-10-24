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
commun/      socle partagé par les deux interfaces — il n'existe qu'en un exemplaire
frontend/    la boutique : acheteurs et groupeurs          → port 5173
admin/       la console d'administration                    → port 5174
backend/     l'API Django et le modèle de données           → port 8000
```

| Document | Ce qu'il contient |
|---|---|
| [README.md](README.md) | l'architecture, comment démarrer, les comptes de démonstration |
| [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) | les règles métier : séquestre, KYC, frais, codes de retrait |
| [COOLIFY.md](COOLIFY.md) | le déploiement sur `achatgr.com`, les variables, la sécurité |
| [commun/README.md](commun/README.md) | ce que le socle contient **et ne doit pas contenir** |

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

**Le prix est figé à la commande.** Un palier franchi plus tard ne réécrit
pas ce qui a déjà été payé.

**Le séquestre est par campagne**, avec des contraintes en base qui
interdisent de libérer ou rembourser plus que le consigné.

**Les pièces d'identité ne sont jamais servies publiquement** : `/medias/`
refuse le dossier `kyc/`, et une vue séparée vérifie qui demande.

## Lancer et vérifier

```bash
npm install                        # une fois, à la racine
npm run dev                        # boutique
npm run dev:admin                  # console

cd backend
python manage.py migrate
python manage.py charger_demo      # jeu de démonstration, tous états couverts
python manage.py runserver
python -m pytest                   # 110 tests
```

⚠️ **La configuration vient d'un seul `.env`, à la racine** — celui que
lisent Django, Vite et Docker Compose. Pas de second fichier par dossier.

⚠️ **`VITE_API_URL` doit rester vide.** Le client retombe alors sur `/api`,
relayé depuis la même origine. Une adresse absolue rouvre le CORS.

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
