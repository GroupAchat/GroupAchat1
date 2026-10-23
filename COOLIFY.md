# Déploiement sur Coolify — achatgr.com

Quatre conteneurs, deux domaines, aucun certificat à gérer : Coolify termine
le TLS et route vers les conteneurs.

```
                    ┌──────────────────────────────────────┐
  achatgr.com ─────▶│                                      │
                    │  api  (Django + Gunicorn)            │
admin.achatgr.com ─▶│  · l'API sous /api                   │
                    │  · la boutique et la console,        │──▶ base
                    │    servies par WhiteNoise            │   (PostgreSQL)
                    └──────────────────────────────────────┘
```

**Deux conteneurs, pas cinq, et aucun nginx.** Coolify termine déjà le TLS et
route par domaine : un serveur web de plus n'apporterait qu'une image à
construire et à tenir à jour. WhiteNoise, livré avec Django, sert les fichiers
compilés par Vite ; une vue rend la page d'entrée qui convient.

**Le domaine demandé décide de ce qui s'affiche** : `admin.achatgr.com` rend
la console, tout le reste rend la boutique. Les deux gardent leurs routes à
la racine, et parlent à l'API depuis leur propre origine.

**L'API n'a pas de domaine public, et c'est voulu.** Chaque nginx relaie
`/api` vers Django depuis sa propre origine. Le navigateur ne voit donc
qu'un seul domaine par application : le cookie de session suit naturellement,
et il n'y a **ni CORS ni cookie tiers** à régler. Exposer l'API sur
`api.achatgr.com` aurait imposé `SameSite=None`, des en-têtes CORS avec
identifiants, et une liste d'origines à tenir à jour — pour aucun gain.

## 1. Les domaines, dans Coolify

Dans la ressource Docker Compose, onglet **Domains**, service par service :

| Service | Domaines |
|---|---|
| `api` | `https://achatgr.com` **et** `https://admin.achatgr.com` |
| `base` | **aucun** |

Les deux domaines pointent sur **le même service**. Coolify détecte le port
8000. Si l'interface en réclame un, indiquez `8000`.

> **Le bloc `ports:` du fichier Compose** publie 8000 sur l'hôte. Pratique en
> local, inutile sur le serveur — ça laisse une porte ouverte à côté du
> proxy. Dans Coolify, videz les **Port Mappings** de la ressource, ou
> supprimez le bloc.

## 2. Les variables d'environnement

Onglet **Environment Variables**. Celles marquées **obligatoire** font échouer
le démarrage si elles manquent — à dessein : mieux vaut un conteneur qui
refuse de partir qu'un site en ligne avec une clé publique.

| Variable | Valeur pour achatgr.com | |
|---|---|---|
| `POSTGRES_PASSWORD` | un mot de passe long et aléatoire | **obligatoire** |
| `DJANGO_SECRET_KEY` | 50 caractères aléatoires | **obligatoire** |
| `DJANGO_ALLOWED_HOSTS` | `achatgr.com,www.achatgr.com,admin.achatgr.com` | **obligatoire** |
| `DJANGO_DEBUG` | `0` | |
| `CHARGER_DEMO` | `1` pour la démonstration, `0` ensuite | |
| `POSTGRES_DB` / `POSTGRES_USER` | `groupachat` | par défaut |
| `SMS_FOURNISSEUR` | `demonstration` tant qu'aucune passerelle n'est branchée | |
| `HOTES_ADMINISTRATION` | `admin` — le sous-domaine qui montre la console | par défaut |
| `DJANGO_SUPERUSER_USERNAME` | un numéro à 8 chiffres | facultatif |
| `DJANGO_SUPERUSER_PASSWORD` | un mot de passe solide | facultatif |

Pour engendrer la clé :

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**`CSRF_TRUSTED_ORIGINS` n'est pas à renseigner** : Django la dérive de
`DJANGO_ALLOWED_HOSTS` en préfixant `https://`. C'est l'oubli classique qui
donne une panne déroutante — le site s'affiche, mais tous les formulaires
échouent en 403. `DJANGO_ORIGINES_SURES` reste disponible pour un cas
particulier.

**`CORS_ORIGINES` ne sert qu'en développement**, où Vite tourne sur un autre
port. En production tout vient de la même origine : laissez la valeur par
défaut.

## 3. Ce qui est figé à la construction

⚠️ **Vite inscrit les variables `VITE_*` dans le code compilé.** Les changer
dans Coolify après coup n'a aucun effet : il faut **reconstruire** l'image.

C'est pourquoi `VITE_API_URL` est volontairement vide dans le Compose — le
client retombe alors sur `/api`, relayé par nginx. Rien à régler, et rien à
reconstruire si le domaine change.

## 4. Les volumes

| Volume | Contenu | Conséquence d'une perte |
|---|---|---|
| `donnees-postgres` | toute la base | tout est perdu |
| `medias` | pièces KYC, photos de produits | images manquantes |

Les fichiers compilés du front, eux, **vivent dans l'image** : ils sont
reconstruits à chaque déploiement, il n'y a rien à conserver.

Les deux sont déclarés dans le Compose, donc Coolify les crée et les
conserve entre les déploiements. Pensez à les inclure dans vos sauvegardes.

## 5. Le premier déploiement

1. Renseignez les variables ci-dessus.
2. Déployez. Le conteneur `api` attend PostgreSQL, applique les migrations,
   collecte les fichiers statiques, puis charge la démonstration si
   `CHARGER_DEMO=1`.
3. Vérifiez les journaux de `api` : vous devez y lire `→ Gunicorn sur le
   port 8000.`
4. Ouvrez `https://achatgr.com`, puis `https://admin.achatgr.com`.

**Comptes de démonstration** — mot de passe commun `demo2026Groupe` :

| Rôle | Numéro |
|---|---|
| Administrateur | `99000011` |
| Groupeur validé | `90001122` |
| Groupeur en attente de KYC | `90009988` |
| Acheteurs | `91002233`, `92003344`, `93004455`, `94005566`, `95006677` |

> **Mettez `CHARGER_DEMO=0` dès que le site est public.** Ces comptes ont des
> mots de passe connus, et l'un d'eux est administrateur.

## 6. Mettre à jour

Coolify reconstruit à chaque envoi sur la branche suivie. Les migrations
s'appliquent au démarrage, `charger_demo` ne fait rien si des campagnes
existent déjà : un redéploiement ne duplique pas les données.

## 7. Essayer la pile en local

```bash
docker compose up --build
```

Tout sort sur <http://localhost:8000> : la boutique à la racine, l'API sous
`/api`. Pour voir la console en local, où il n'y a pas de sous-domaine,
ajoutez `HOTES_ADMINISTRATION=admin,console.localhost` et ouvrez
<http://console.localhost:8000>.

Pour développer, ne passez pas par Docker : `npm run dev` côté `frontend/` et
`manage.py runserver` côté `backend/` donnent le rechargement à chaud.

⚠️ **Gardez `DJANGO_DEBUG=1` dans le `.env` local.** À `0`, Django ne pose
ses cookies de session qu'en HTTPS : en local, où il n'y a pas de TLS, la
connexion échouerait sans message clair. Sur Coolify, qui sert en HTTPS,
c'est bien `0` qu'il faut.

## 8. Ce qui reste simulé

Le site déployé est une **démonstration fonctionnelle**, pas une plateforme
en exploitation :

- **aucun SMS n'est envoyé** — le code de vérification s'affiche à l'écran ;
- **aucun paiement réel** — « Payer avec T-Money / Flooz » consigne la part
  dans le séquestre tenu en base, sans contacter l'opérateur ;
- **aucun versement réel** — le décaissement est une action de la console.

La comptabilité du séquestre, elle, est tenue pour de vrai. Brancher un
agrégateur revient à réécrire `_executer_paiement` dans
[`backend/groupachat/paiements/services.py`](backend/groupachat/paiements/services.py)
et une passerelle dans
[`backend/groupachat/comptes/services.py`](backend/groupachat/comptes/services.py).
