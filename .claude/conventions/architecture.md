# Architecture — Group Achat

Remplace l'architecture en couches `api/services/repositories` du modèle `claude-template`, que ce dépôt ne suit pas. La référence est la structure **réelle**, décrite dans `CLAUDE.md` et `README.md`. Ne pas la réorganiser.

## Backend — `backend/`
```
config/                    réglages (settings.py), routes (urls.py)
  service/                 ce que Django sert : applications compilées, fichiers, pièces KYC
groupachat/
  <sujet>/                 le domaine, un dossier par sujet :
                           catalogue, commandes, comptes, echanges, paiements
    models.py              modèles, TextChoices, contraintes en base
    serialiseurs.py        sérialiseurs DRF (forme et validation)
    vues.py                ViewSets / APIView publiques du sujet
    services.py            la logique métier qui écrit (argent, états, notifications)
    tests.py               les tests de ce seul sujet
    management/commands/   commandes (charger_demo, tâches planifiées)
  espaces/                 administration.py, groupeur.py : des vues, PAS d'application,
                           aucun modèle n'y vit
  noyau/                   ce qui traverse tout : permissions.py, limitation.py,
                           hebergement.py (signature Cloudinary)
  tests/                   les tests qui traversent plusieurs sujets
  api.py                   l'assemblage de toutes les routes (routeur DRF)
conftest.py                fixtures partagées
```

### Où va quoi
- **Une règle qui écrit** — paiement, séquestre, transition d'état d'une campagne, remboursement, retrait, notification — va dans le `services.py` du sujet (modèle : `paiements/services.py`), sous `transaction.atomic`, avec `select_for_update()` quand deux requêtes peuvent se croiser. La vue l'appelle et convertit l'exception métier en réponse.
- **Une lecture ou un CRUD sans règle** peut rester dans la vue (`get_queryset` filtré par propriétaire).
- **Une vue réservée à un rôle** (administration, groupeur) va dans `espaces/`, pas dans le sujet.
- **Le transversal** (permission, limitation de débit, hébergement des médias) va dans `noyau/`.
- **Une tâche planifiée** est une commande de gestion (`cloturer_les_campagnes_echues` en est le modèle), idempotente, qui appelle un service.
- **Un nouveau modèle** va dans le sujet qui le possède ; jamais dans `espaces/` ni `noyau/`.
- Pas de nouvelle application Django ni de nouveau dossier de premier niveau sans décision écrite dans `mapper/02-decisions/`.

### Sens des dépendances
`api.py → vues / espaces → services → models`. Un modèle n'importe pas une vue ; un service n'importe pas une vue ; `noyau/` n'importe aucun sujet.

## Frontend — `frontend/` (espaces de travail npm)
```
commun/src/   le socle, en UN exemplaire : api/ (client.ts, types.ts), composants/ (ui.tsx…),
              contexte/ (Session.tsx), outils/ (formats, requêtes, téléversement), index.css
boutique/src/ acheteurs et groupeurs (port 5173) : pages/, pages/groupeur/, composants/
admin/src/    console d'administration (port 5174) : pages/
```
- **Le socle ne contient aucune page ni route.** Un composant qui ne sert qu'à une interface va dans celle-là (`frontend/commun/README.md`).
- On importe le socle par chemin : `@commun/api/client`, jamais par le dossier.
- **Tout appel réseau passe par `@commun/api/client`** (jeton CSRF, `ErreurApi`) ; jamais de `fetch` direct dans une page.
- Les types de l'API vivent dans `commun/src/api/types.ts`. Une réponse d'API qui change oblige à changer ce fichier dans le même passage.

## Une seule origine
Django sert l'API **et** les deux interfaces compilées ; le domaine demandé décide laquelle s'affiche. Ni CORS, ni cookie tiers, ni serveur web devant. Ne pas proposer une API sur un sous-domaine séparé.

## Simulé, et ce qui ne l'est pas
SMS et paiements sont simulés derrière `_executer_paiement` et la passerelle SMS ; **la comptabilité du séquestre est réelle**. Une fonctionnalité touchant l'argent écrit donc la vraie logique et ne simule que l'exécution.
