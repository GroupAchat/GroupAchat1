# Workflow (git, dépendances, mémoire)

## Branches
- `master` = production (déployée sur Coolify, voir `COOLIFY.md`) : jamais de commit direct, jamais de `push --force`. `staging` = intégration, le rempart avant `master`.
- Une branche par fonctionnalité du backlog, créée depuis `staging` : `feat/F-012-relances-retrait`, `fix/double-paiement`, `chore/`, `docs/`, `test/`.
- Une branche = une fonctionnalité. Elle est fusionnée dans `staging` (PR ou `git merge`, sur accord de l'utilisateur) après un verdict `VALIDÉE` de `reviewer-tester` et « Vérifier » vert ; jamais directement dans `master`. Conflit : la fusion est annulée et le conflit se règle sur la branche de travail.
- Tout est fusionné dans `staging`, sans conflit, et « Vérifier » y est vert : le chef de projet crée `test_<nom_du_projet>.json` à la racine (collection Postman de toutes les routes de l'API ; un seul fichier, remplacé à chaque fois, ignoré par git) pour tester `staging`.
- `master` n'avance que jusqu'à `staging`, une fois `staging` testée, par l'utilisateur seul. Le hook (`branch_policy.py`) refuse tout commit direct sur `master` ou `staging` et toute avancée de `master` par Claude.

## Commits
- **Le style du dépôt, en français** : une phrase qui dit ce que le commit change, verbe au présent en tête, 72 caractères max, sans préfixe de type.
  `Permet au groupeur de photographier le lot qu'il a en main`, `La clôture ne rembourse plus : c'est le groupeur qui tranche`, `Ferme trois failles de sécurité`.
- Un commit = un changement cohérent qui passe la commande « Vérifier ». Jamais de message vague (`update`, `fix bug 1`, `test`, `design 2`).
- Corps (facultatif) : le pourquoi, et la référence : `Réf. : F-012`, `Bug : [[Bugs-Detectes]] 2026-08-14`.
- Une migration est commitée avec le changement de modèle qui la produit.
- Claude ne commit et ne pousse que sur demande ; jamais `--no-verify`, jamais de réécriture d'un commit déjà poussé.

## Ce qui entre dans git
Principe : git contient **tout ce qu'il faut pour reconstruire, comprendre et lancer le projet** sur une machine neuve,
et **rien de ce qui se régénère, se télécharge, est personnel ou contient des données réelles**.

**Toujours versionné**
- Le code source et ses tests (y compris tests de caractérisation et de régression).
- Les manifestes et fichiers de verrouillage : `package.json` + `package-lock.json` (ou `pnpm-lock.yaml`), `pyproject.toml` + `poetry.lock` / `uv.lock`, `requirements*.txt`, `pubspec.yaml` + `pubspec.lock` (app Flutter).
- Le schéma et les migrations : `prisma/schema.prisma`, `prisma/migrations/`, `*/migrations/*.py` (Django).
- La configuration sans secret : `tsconfig.json`, `ruff.toml`, `eslint.config.*`, `Dockerfile`, `docker-compose.yml`, `nest-cli.json`, `analysis_options.yaml`, dossiers `android/` et `ios/` de Flutter, `.vscode/extensions.json` et `settings.json` partagés.
- `.env.exemple`, complet et commenté : toute variable lue par le code y figure, avec une valeur factice.
- La CI et l'outillage : `.github/workflows/`, scripts du projet (`scripts/`), `Makefile`.
- La configuration Claude partagée : `CLAUDE.md`, `.claude/` (sauf `settings.local.json`).
- La mémoire et la conception : `mapper/`, `design/` (DESIGN.md, tokens, prompts d'images), `README.md`, `docs/`.
- Les ressources utilisées par l'application : images, polices, icônes de `public/` ou `static/`, chacune de moins de 5 Mo.
- Les jeux d'essai **fictifs** : `tests/fixtures/`, `seeds/` (noms, numéros et montants inventés).

**Jamais versionné**
- Secrets : `.env`, `.env.local`, clés et certificats (`*.pem`, `*.key`, `*.p12`), fichiers d'identifiants (`credentials.json`, comptes de service), signature Android (`key.properties`, `*.jks`, `*.keystore`).
- Ce qui se télécharge : `node_modules/`, `.venv/`, `ios/Pods/`, `.pub-cache/`.
- Ce qui se régénère : `dist/`, `build/`, `.next/`, `staticfiles/`, client Prisma, caches (`__pycache__`, `.ruff_cache`, `.pytest_cache`, `.dart_tool/`), rapports (`coverage/`, `playwright-report/`, `test-results/`), fichier de test `test_<nom_du_projet>.json`.
- Données réelles : exports CSV ou Excel de clients, dumps de base (`*.dump`, `*.sql.gz`), bases locales (`*.sqlite3`, `*.db`), fichiers envoyés par les utilisateurs (`media/`, `uploads/`), photos et vocaux de clients.
- Journaux et temporaires : `*.log`, `*.bak`, `*.tmp`, `*.swp`.
- Personnel : `CLAUDE.local.md`, `CLAUDE.template.md`, `.claude/settings.local.json`, `.idea/`, réglages personnels de l'éditeur, `.DS_Store`.
- Tout fichier de plus de 5 Mo : stockage externe (S3, Drive) ou Git LFS, décidé dans `mapper/02-decisions/`.
- Les fichiers CSV, Excel ou JSONL hors de `tests/`, `fixtures/` ou `seeds/`.

**Comment Claude ajoute des fichiers**
- `git status`, puis `git add` **fichier par fichier** : jamais `git add .`, `-A`, `--all` ni `--force`.
- `git diff --cached` relu avant chaque commit : uniquement les fichiers de la fonctionnalité en cours.
- Un nouveau type de fichier à ignorer → son motif est ajouté au `.gitignore` dans le même commit.
- Un fichier interdit déjà suivi → `git rm --cached <fichier>` + `.gitignore`, dans un commit `chore(git): …` ; si c'est un secret, la clé est considérée comme compromise et doit être changée.

Le hook `guard.py` (module `git_policy.py`) applique ces règles sur `git add`, `git commit` (fichiers indexés, taille, longueur du message) et `git push` (tous les commits qui partiraient).
Le `.gitignore` de base est dans `.claude/git/gitignore` ; `init.sh` le fusionne dans celui du projet.

## Pull requests
- Titre au format des commits ; description : quoi, pourquoi, comment tester, référence `F-XXX` ; captures d'écran si l'interface change.
- Petite : environ 400 lignes de diff max hors tests et migrations ; au-delà, découper la fonctionnalité.

## Dépendances
- Avant d'ajouter une dépendance : vérifier qu'une dépendance existante ou la bibliothèque standard ne suffit pas.
- Toute nouvelle dépendance est justifiée dans `mapper/02-decisions/YYYY-MM-DD-<nom>.md` (besoin, alternatives, maintenance, licence).
- Le fichier de verrouillage (`package-lock.json`, `poetry.lock`, `requirements.txt` épinglé) est commité avec le changement.

## Mémoire du projet
- Fonctionnalité fusionnée → `obsidian-mapper` met à jour `mapper/` (journal du jour, statut dans `backlog.md`).
- Choix d'architecture ou de dépendance → une note de décision dans `mapper/02-decisions/`.
- Bug de production corrigé → une entrée dans `mapper/` (`[[Bugs-Detectes]]`) et un test de régression (voir `testing.md`).
