# Group Achat

Plateforme d'achats groupés au Togo — « livré ou remboursé ».

## Architecture

```
GroupAchat/
├── backend/              l'API Django et le modèle de données
│   ├── config/           réglages, routes, et ce que Django sert
│   │   └── service/      interfaces compilées, fichiers téléversés
│   └── groupachat/
│       ├── catalogue/    ─┐
│       ├── commandes/     │  le domaine : un dossier par sujet,
│       ├── comptes/       │  modèles, sérialiseurs, vues, tests
│       ├── echanges/      │
│       ├── paiements/    ─┘
│       ├── espaces/      administration et groupeur : des vues,
│       │                 pas des applications — aucun modèle
│       ├── noyau/        ce qui traverse tout : accès, limitation
│       ├── tests/        les tests qui traversent plusieurs sujets
│       └── api.py        l'assemblage des routes
└── frontend/             les interfaces web
    ├── commun/           le socle partagé — écrit une seule fois
    ├── boutique/         acheteurs et groupeurs      → port 5173
    └── admin/            console d'administration     → port 5174
```

**Pourquoi un socle séparé.** La boutique et la console ont besoin du même
client HTTP, des mêmes types, de la même gestion de session et de la même
trousse d'interface. Les dupliquer garantirait qu'ils divergent — et une
divergence sur l'authentification ne se voit qu'en production. Le socle les
tient donc en **un seul exemplaire**, que les deux importent par `@commun/…`.

Les trois dossiers de `frontend/` sont des **espaces de travail npm** : un
seul `npm install` dans `frontend/`, un seul `node_modules`, aucune
dépendance installée deux fois.

| Dossier | Ce qu'il contient | Ce qu'il ne contient pas |
|---|---|---|
| `frontend/commun/` | client API, types, session, boutons et champs, logos, feuille de style | aucune page, aucune route |
| `frontend/boutique/` | fil vertical, catalogue, fiche campagne, espace groupeur | rien de l'administration |
| `frontend/admin/` | KYC, séquestre, décaissements, modération | rien de la boutique |

## Démarrer

```bash
# L'API, depuis backend/
python manage.py migrate
python manage.py charger_demo      # jeu de démonstration
python manage.py runserver

# Les interfaces, depuis frontend/
cd frontend
npm install
npm run dev                        # boutique       → http://localhost:5173
npm run dev:admin                  # administration → http://localhost:5174
```

Les appels `/api` sont relayés vers Django par le serveur de développement :
les deux partagent alors la même origine, et le cookie de session suit sans
réglage CORS particulier.

La configuration vient d'**un seul `.env`**, à la racine — le même que lisent
Django et Docker Compose.

## Démarrer avec make

Un `Makefile` à la racine enchaîne les commandes ci-dessous. `make` seul liste les cibles.

```bash
make preparer-presentation   # installe, migre, charge la démo, compile les deux interfaces
make lancer                  # compile puis sert Django seul sur le port 8000 (PORT=8100 pour un autre)
make servir                  # le jour J : sert les builds existants, sans recompiler
```

`make lancer` sert la boutique sur `http://localhost:8000/` et la console sur
`http://admin.localhost:8000/` : comme en production, le domaine décide de
l'interface. Il utilise SQLite et `DJANGO_DEBUG=1` sans toucher au `.env`
(`SQLITE=0` pour suivre la `DATABASE_URL` du `.env`). `make dev` lance Django et
les deux serveurs Vite (port 8000 obligatoire) ; `make tests`, `make verifier-rapide`
et `make verifier` complètent le tout.

## Comptes de démonstration

Mot de passe commun : `demo2026Groupe`

| Rôle | Numéro |
|---|---|
| Administrateur | `99000011` |
| Groupeur validé | `90001122`, `96004477` |
| Groupeur en attente de KYC | `90009988` |
| Acheteurs | `91002233`, `92003344`, `93004455`, `94005566`, `95006677` |

## Tests

```bash
cd backend && python -m pytest        # 110 tests
```

## En production

Un seul conteneur sert tout : Django rend l'API, et **WhiteNoise sert les
deux interfaces compilées**. Le domaine demandé décide de ce qui s'affiche —
`admin.achatgr.com` montre la console, le reste la boutique. Ni serveur web
devant, ni CORS, ni cookie tiers.

Voir [COOLIFY.md](COOLIFY.md) pour le déploiement et
[CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) pour les règles métier.

> **Cette version est une démonstration.** Aucun SMS n'est envoyé, aucun
> paiement n'est encaissé, aucun versement n'est effectué. La comptabilité du
> séquestre, elle, est tenue pour de vrai.
