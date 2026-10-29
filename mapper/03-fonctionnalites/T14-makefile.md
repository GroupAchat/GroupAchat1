---
type: fonctionnalite
id: T14
statut: terminée
mission: M-001 (T14)
commit: fafebab
date: 2026-10-28
tags: [fonctionnalite, T14, M-001, outillage]
---

# T14 — Makefile de présentation

Rôle : exploitant / présentateur · Couches : serveur non · web non · mobile non (outillage) · Source : mission M-001

## Recette — 2026-10-28

**RECETTE OK** — base `staging` f32b69c + Makefile, README et .gitignore de `chore/T14-makefile` (non committé). Rejouée sur une copie neuve (sans venv, node_modules, .env, backend/web, base), Django sur les ports 8123 puis 8124, Chrome headless à 390 px (console à 1280 px).

| # | Scénario | Résultat |
|---|---|---|
| M1 | `make` liste les cibles avec leur phrase | OK : 12 cibles dont `servir`, `PORT` affiché |
| M2 | `preparer-presentation` sur copie neuve, puis relancé | OK : 2 min 27 s la première fois (venv, pip, `npm ci`, migrations, démo, compilation). Message « .env créé depuis .env.exemple… ». Conseille `make servir PORT=<p>`. Second passage 53 s : installation sautée, « No migrations to apply », « Jeu de démonstration déjà en version 7 », `.env` inchangé (taille et date identiques ; contenu non lu, le hook l'interdit) |
| M3 | `make servir` | OK : sans recompiler, `http://localhost:8123/` 200 (boutique), `http://admin.localhost:8123/` 200 (console) |
| M4 | Parcours de démo | OK (détails ci-dessous) |
| M5 | `lancer` et refus de `WEB=frontend` | OK : `lancer` recompile (index.html renouvelé) puis sert, les deux adresses répondent. `WEB=frontend`, `WEB=backend/web/..` et `WEB=` refusés, `frontend/` et `backend/web/` intacts |

### M4 en détail
- Acheteur 91002233 : connexion par l'écran, accueil, catalogue (7 campagnes), fiche campagne 1, « Participer » puis « Payer 18 000 FCFA » (T-Money / Flooz) : feuille « Paiement confirmé », « Votre part est consignée », code de retrait affiché ; compteur 11/20 → 12/20. « Mes achats » : liste, détail avec code et QR lisibles. Captures : `img/02` à `img/09`.
- Groupeur 90001122 : tableau de bord, tuile « Consigné en séquestre 2 250 000 FCFA » lisible (blanc sur bleu), 12 campagnes. « Prévenir les participants » : feuille « Prévenir 4 participants… » avec Prévenir / Annuler, annulée sans confirmer. Captures `img/10`, `11`, `27`, `28`.
- Administrateur 99000011 (`admin.localhost`, 1280 px) : « Détenu en séquestre 2 460 000 FCFA » lisible, dossiers KYC (3 à examiner), décaissements (1 à libérer). Feuille « Libérer les fonds ? » / « Libérer 473 500 FCFA » visible, annulée. Captures `img/21` à `24`.
- Acheteur sur la console : « Ce compte n'appartient pas à l'équipe. » (`img/25`).
- Aucune erreur de page ; aucun 4xx hormis `GET /api/comptes/moi/` 403 avant connexion (normal, visible seulement dans la console du navigateur).

### À savoir pour demain
- Mot de passe commun `demo2026Groupe`. Admin `99000011`, groupeur `90001122` (ou `96004477`), acheteurs `91002233`, `92003344`… Tous les numéros sont en `README.md`.
- Adresses : `http://localhost:<PORT>/` et `http://admin.localhost:<PORT>/`. Le port par défaut est 8000, déjà pris sur cette machine : `PORT=8100`. Le même `PORT` doit être donné à `preparer-presentation` et à `servir`.
- **« Prévenir les participants » n'apparaît dans aucune campagne de la démo** : il n'existe que pour une campagne en « approvisionnement ». Pour le montrer : console admin, Décaissements, « Libérer 473 500 FCFA » (campagne Smartphone Itel, id 7), puis groupeur, campagne 7. Cette libération est irréversible : à faire sur le serveur de démonstration, pas avant de vouloir la montrer. Sur un jeu déjà consommé, `charger_demo` remet à plat si `VERSION_DEMO` change.
- Un paiement joué en répétition reste en base : l'acheteur 91002233 a une part de plus. Pour repartir de zéro, supprimer la base SQLite locale avant `preparer-presentation` (ne pas toucher au `.env`).
- Aucune campagne n'a de photo (pas de Cloudinary) : fond dégradé coloré avec icône de colis et initiale du produit (un grand « S » à moitié masqué par les boutons sur l'accueil mobile). Acceptable, à annoncer. Les titres sont tronqués (« Ventilateurs… ») dans la liste groupeur à 390 px.
- Le paiement prend environ 1 s à l'écran, rien de lent. Compter 2,5 min pour la première préparation (réseau pour `npm ci` et pip), à faire avec Internet.
- Le chiffre « Détenu en séquestre » diffère entre groupeur (2 250 000) et admin (2 460 000) : pas vérifié si c'est attendu (l'admin compte tous les groupeurs, et les deux lectures ne sont pas au même instant). À garder en tête si on compare les deux écrans devant le public.
- `make verifier` annonce 25 à 35 minutes : ne pas le lancer demain.
- Nettoyage : copie temporaire de 292 Mo supprimée, serveurs et Chrome headless arrêtés (les Chrome encore ouverts sur la machine sont ceux de l'utilisateur).

## Clôture — 2026-10-28

**Terminée.** Relecture VALIDÉE, recette « RECETTE OK » (section « Recette — 2026-10-28 », ci-dessus).

- **Passes.** 1re passe : `fonctionnalite`. Relecture : VALIDÉE (parcours réel : connexion acheteur `91002233` et admin `99000011`, CSRF 403 sans jeton, 204 avec). Quatre finitions retenues par le chef de projet : `make servir`, factorisation de `RUNSERVER`, garde avant `rm -rf`, aide de `verifier`. Relecture des finitions : **À CORRIGER**, ordre de `lancer` sous `make -j`. Reprise : `lancer` = `$(MAKE) construire && $(MAKE) servir` ; garde : `WEB` doit être un dossier `web*` directement sous `backend/`. Relecture : VALIDÉE.
- **Preuves.** Commit `fafebab` (« Ajoute un Makefile pour installer et lancer la démo en local » : `Makefile`, `README.md`, `.gitignore`), fusionné dans `staging` par avance rapide (accord de l'utilisateur). « Vérifier » rapide sur `staging` : en cours, à compléter par le chef de projet (non relu par l'archiviste).
- **Décisions** : [[2026-10-28-decisions-t14-t17]] (D4 à D7).
- **Démo** : [[presentation-2026-10-29]]. **Mission** : [[M-001-terminer-le-mvp]] (T14 `terminée`).
- **Hors dépôt** : worktree `.claude/worktrees/t14-makefile` (branche `chore/T14-makefile`, à `fafebab`) : rangement à décider.
