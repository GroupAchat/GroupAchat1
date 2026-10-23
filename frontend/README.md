# Front-end Group Achat

Deux applications React, une par public, servies sur deux ports.

| | Boutique | Administration |
|---|---|---|
| Page | `index.html` | `admin.html` |
| Entrée | `src/main.tsx` | `src/main-admin.tsx` |
| Configuration | `vite.config.ts` | `vite.admin.config.ts` |
| Port | **5173** | **5174** |
| Construction | `dist/` | `dist-admin/` |

Deux configurations parce que Vite n'ouvre qu'un port par serveur. Le port de
la boutique **refuse `/admin.html`** : sans ce garde, la séparation n'aurait
rien séparé, il aurait suffi de connaître le nom du fichier. Ce n'est pas une
mesure de sécurité — c'est l'API qui garde ses routes.

## Démarrer

```bash
# L'API, depuis backend/
python manage.py migrate
python manage.py charger_demo      # jeu de démonstration
python manage.py runserver

# La boutique, depuis frontend/
npm install
npm run dev                        # http://localhost:5173

# La console d'administration
npm run dev:admin                  # http://localhost:5174/admin.html
```

Les appels `/api` sont relayés vers Django par le serveur de développement :
les deux partagent alors la même origine, et le cookie de session suit sans
réglage CORS particulier.

La configuration vient d'**un seul `.env`**, à la racine du dépôt — le même
que lisent Django et Docker Compose (`envDir: ".."`).

## Comptes de démonstration

Mot de passe commun : `demo2026Groupe`

| Rôle | Numéro |
|---|---|
| Administrateur | `99000011` |
| Groupeur validé | `90001122` |
| Groupeur en attente de KYC | `90009988` |
| Acheteurs | `91002233`, `92003344`, `93004455`, `94005566`, `95006677` |

## Les choix d'interface

**Le fil vertical.** Sur téléphone, l'accueil est un fil aimanté : une
campagne par écran, qu'on parcourt au pouce. Sur ordinateur il cède la place
à une bannière et une grille — le geste du fil n'a pas de sens à la souris.
Voir `src/composants/FilCampagnes.tsx`.

**La couleur suit le profil.** L'acheteur vit dans l'orange, le groupeur et
l'administration dans le bleu. Un seul attribut sur `<html>`
(`data-profil`) redéfinit `--teinte-accent` ; aucun composant n'a donc à
savoir qui le regarde. Voir le bloc « L'accent change avec le profil » dans
`src/index.css`.

**Pas de photos ?** Le catalogue reste lisible : `Visuel` fabrique un dégradé
déterminé par le nom du produit, toujours le même pour un produit donné.

## Arborescence

```
src/
  api/          client HTTP (jeton CSRF, erreurs) et types de l'API
  composants/   trousse partagée, fil vertical, feuille, discussion
  contexte/     session et teinte du profil
  outils/       formats (FCFA, dates, numéros) et crochets de requête
  pages/        écrans de la boutique
  pages/groupeur/ espace groupeur
  pages/admin/  console d'administration
```
