---
type: presentation
statut: prête
date: 2026-10-29
tags: [presentation, demo, M-001, T14]
---

# Fiche de démo — 2026-10-29

Pour présenter Group Achat en local, depuis la machine de démonstration. Sources : recette T14 ([[T14-makefile]]), `README.md` (« Démarrer avec make », « Comptes de démonstration »), `CAHIER_DES_CHARGES.md`, [[carte]]. Outillage : commit `fafebab` sur `staging`.

## 1. Avant

**La veille**, avec Internet (environ 2 min 30 s la première fois, 53 s ensuite) :

```bash
make preparer-presentation PORT=8100
```

Installe ce qui manque (venv Python, `npm ci`), crée `.env` depuis `.env.exemple` **seulement s'il manque**, migre, charge la démo, compile les deux interfaces. On peut le relancer sans risque.

**Le jour J**, sans rien recompiler :

```bash
make servir PORT=8100
```

Le même `PORT` doit servir aux deux commandes. Adresses :
- boutique : `http://localhost:8100/`
- console : `http://admin.localhost:8100/`

Les ports 8000 et 5173 sont pris sur cette machine : ne pas lancer `make dev` (il exige `PORT=8000`).

**Repartir de zéro** (pour effacer les paiements joués en répétition) :
1. Arrêter le serveur (`Ctrl+C`).
2. Supprimer `backend/base-de-secours.sqlite3`. C'est la base SQLite que `settings.py` crée quand `DJANGO_FORCER_SQLITE=1`, réglage que le Makefile pose par défaut (`SQLITE=1`).
3. Relancer `make preparer-presentation PORT=8100`.

Ne jamais toucher au `.env`, ni le supprimer.

## 2. Comptes

Mot de passe commun : `demo2026Groupe`

| Rôle | Numéro | Usage dans le déroulé |
|---|---|---|
| Administrateur | `99000011` | console seulement (`admin.localhost`) |
| Groupeur | `90001122` | espace groupeur (12 campagnes en démo, dont la 7) |
| Groupeur | `96004477` | en réserve |
| Acheteur | `91002233` | participe et paie |
| Acheteurs | `92003344`, `93004455`, `94005566`, `95006677` | en réserve |
| Groupeur en attente de KYC | `90009988` | facultatif : l'écran d'attente (non joué en recette) |

## 3. Déroulé conseillé (10 à 15 min)

Une seule histoire : une campagne, de la vitrine à la remise. Pour chaque étape, la phrase du cahier qu'elle illustre.

| # | Où et qui | Ce qu'on montre | Phrase-clé |
|---|---|---|---|
| 1 | Boutique, sans compte | Accueil, catalogue, fiche d'une campagne : jauge, paliers, réputation du groupeur, fil | « explore le catalogue librement, sans inscription » (`CAHIER_DES_CHARGES.md` §3, acheteur 1) |
| 2 | Boutique, `91002233` | « Participer » puis « Payer 18 000 FCFA » (T-Money ou Flooz, simulé). Feuille « Paiement confirmé », « Votre part est consignée », code de retrait. « Mes achats » : code et QR. Campagne 1 : compteur 11/20 à 12/20 à la recette | « L'argent part en séquestre, il n'est jamais versé directement au groupeur » (§3, acheteur 3). Prix figé : « Le prix est figé à la commande » (`CLAUDE.md`, pas une règle du cahier) |
| 3 | Boutique, `90001122` | Tableau de bord : tuile « Consigné en séquestre », liste des campagnes, « Qui a payé » sur la campagne, fil et réponse sous un avis | « suit la jauge et les **paiements nominatifs** en temps réel » (§3, groupeur 3) |
| 4 | Console, `99000011` | Tableau : « Détenu en séquestre ». Dossiers KYC (pièces recto et verso, à examiner). Décaissements | « Vérifie le dossier KYC du groupeur » (§3, administrateur 1) ; « Les pièces d'identité ne sont jamais servies publiquement » (`CLAUDE.md`) |
| 5 | Console, Décaissements | « Libérer 473 500 FCFA » pour la campagne 7 (Smartphone Itel). **Irréversible**, voir section 4 | « Retire 100 % des fonds en une fois, moins 1 500 FCFA de frais fixes » (§3, groupeur 4) ; frais « prélevés une seule fois au décaissement » (§4) |
| 6 | Boutique, `90001122`, campagne 7 | « Prévenir les participants » (ce bouton n'existe que pour une campagne en approvisionnement, donc après l'étape 5). Ouvrir la feuille, puis annuler ou confirmer | « Tous les participants reçoivent aussitôt une notification » (§3, groupeur 5) |
| 7 | Boutique, `90001122`, campagne 7 | Valider le code de retrait d'un participant (saisi ou collé depuis le QR). Un code d'une autre campagne est refusé | « Le colis n'est remis que contre ce code ; sa validation vaut preuve de livraison » (§4, retrait) |

**À dire en parole, sans écran** (aucune campagne de la démo ne le montre) :
- Minimum non atteint : la campagne n'est pas annulée ; le groupeur maintient ou renonce. Sans réponse pendant **7 jours**, chaque participant est **intégralement remboursé** sans rien réclamer (§4, délai de décision).

## 4. Pièges

- **La libération (étape 5) est irréversible.** À faire une seule fois, au moment voulu, pas avant. La feuille « Libérer les fonds ? » peut encore être annulée ; une fois confirmée, rien ne revient en arrière, sauf en repartant de zéro (section 1), ce qui efface toute la base locale.
- **Un paiement rejoué ajoute une part.** Après la répétition, l'acheteur `91002233` a une part de plus. Repartir de zéro (section 1) si besoin.
- **Le code de retrait de la campagne 7 n'a pas été relevé à la recette.** Le repérer avant la démo (console ou fiche groupeur), pour ne pas chercher devant le public.
- **Pas de photos.** Sans Cloudinary, chaque produit a un fond dégradé et une initiale. Sur l'accueil mobile, l'initiale est à moitié masquée par les boutons. Dans la liste groupeur à 390 px, les titres sont tronqués (« Ventilateurs… »). **À annoncer** avant de les voir.
- **« Détenu en séquestre » diffère** entre l'écran groupeur (ses campagnes) et la console (toute la plateforme, tous les groupeurs). C'est normal : à dire si on compare les deux écrans.
- **Le code SMS s'affiche encore à l'écran** à l'inscription. La tâche T15 le retirera après la présentation.
- **Les citations du cahier viennent de `staging`.** `origin/master` porte six commits de cahier plus récents (rôle OA, abonnements, points, groupage) absents de `staging`. Ne pas citer une règle de ces commits sans l'avoir relue.
- **SMS et paiement sont simulés.** La comptabilité du séquestre est réelle. À dire dès l'ouverture.
- **Ne pas lancer `make verifier`** : 25 à 35 minutes.

## 5. Si ça casse

| Symptôme | Action |
|---|---|
| Le serveur ne répond plus | `Ctrl+C`, puis `make servir PORT=8100` |
| Page blanche | `make construire`, puis `make servir PORT=8100` (la compilation prend du temps) |
| « Aucun build dans backend/web » | `make construire`, puis `make servir PORT=8100` |
| Connexion refusée sur la console | Vérifier l'adresse : `http://admin.localhost:8100/` (pas `localhost`), même port que `servir` |
| Données de répétition gênantes | Repartir de zéro (section 1) |
