#!/usr/bin/env bash
# Contrôles de Group Achat — backend Django et frontend React dans le même dépôt.
#
#   check.sh            = check.sh complet : la commande « Vérifier » de CLAUDE.md
#   check.sh complet    migrations, suite pytest entière (~7 min), typage des deux interfaces
#   check.sh rapide     ce que lance le hook de fin : migrations, typage si le front a changé,
#                       tests des seuls sujets modifiés
#
# Pourquoi deux niveaux : la suite entière dure environ sept minutes ; le hook de fin
# (require-check.sh) ne peut pas la relancer à chaque arrêt. La compétence `verify` et
# `reviewer-tester` exigent le mode complet avant de déclarer une fonctionnalité terminée.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 2
mode="${1:-complet}"
PY="$ROOT/backend/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
failed=0

step() {  # step <libellé> <commande…>
  local label="$1"; shift
  echo "== $label"
  if "$@"; then echo "   ok"; else echo "   ÉCHEC : $label"; failed=1; fi
}
need() {
  "$PY" -c "import django, pytest" 2>/dev/null || {
    echo "CHECK: dépendances Python absentes : $PY -m pip install -r backend/requirements.txt" >&2; exit 2; }
  [ -d frontend/node_modules ] || { echo "CHECK: lancer d'abord : cd frontend && npm ci" >&2; exit 2; }
}
migrations() { (cd backend && "$PY" manage.py makemigrations --check --dry-run); }
pytest_() { (cd backend && "$PY" -m pytest -p no:warnings "$@"); }
# Le client préfixe déjà « /api » : un chemin qui le répète part vers /api/api/…, répond 404
# et s'affiche « Connexion impossible ». Le typage ne le voit pas (c'est une chaîne).
# Le motif accepte un générique TypeScript (api.post<T>(…)) et exige que « /api » soit un segment
# entier, sans quoi « /apiculture » serait signalé à tort.
# Limite connue : grep lit ligne par ligne, donc un appel dont le chemin est sur la ligne suivante
# (api.post(\n '/api/…')) passe. Aucun cas dans le dépôt ; grep -Pzo n'est pas portable (macOS).
prefixe_api() {
  local trouves motif
  motif="api\\.(get|post|patch|put|delete)(<[^(]*>)?\\(\\s*[\`'\"]/api([/\`'\"])"
  trouves="$(grep -rnE "$motif" frontend/*/src 2>/dev/null)"
  if [ -n "$trouves" ]; then
    echo "$trouves"
    echo "Le client @commun/api/client ajoute déjà « /api » : retirer ce préfixe du chemin (ex. « /groupeur/campagnes/1/annuler/ »)."
    return 1
  fi
}
typage() { (cd frontend && npm run --silent verifier); }

need
case "$mode" in
  complet)
    step "Django : aucune migration manquante" migrations
    step "Frontend : aucun chemin d'appel ne répète le préfixe /api" prefixe_api
    step "Backend : suite pytest entière" pytest_
    step "Frontend : typage boutique + admin (npm run verifier)" typage
    ;;
  rapide)
    changed="$( { git diff --name-only HEAD; git ls-files --others --exclude-standard; } 2>/dev/null | sort -u)"
    step "Django : aucune migration manquante" migrations
    step "Frontend : aucun chemin d'appel ne répète le préfixe /api" prefixe_api
    # Tests des sujets touchés : leur tests.py ; transversal (espaces, noyau, config, tests/) : groupachat/tests/.
    cibles=""
    # Un sujet sans tests.py (paiements : ses tests vivent dans groupachat/tests/) retombe sur les
    # tests transversaux ; sinon pytest échoue sur un fichier introuvable et le hook de fin bloque.
    for sujet in catalogue commandes comptes echanges paiements; do
      printf '%s\n' "$changed" | grep -q "^backend/groupachat/$sujet/" || continue
      if [ -f "backend/groupachat/$sujet/tests.py" ]; then cibles="$cibles groupachat/$sujet/tests.py"
      else cibles="$cibles groupachat/tests/"; fi
    done
    printf '%s\n' "$changed" | grep -qE '^backend/(groupachat/(espaces|noyau|tests)/|groupachat/api\.py|config/)' && cibles="$cibles groupachat/tests/"
    for f in $(printf '%s\n' "$changed" | grep -E '^backend/.*/(tests|test_[^/]*|tests_[^/]*)\.py$' | sed 's#^backend/##'); do
      [ -f "backend/$f" ] && cibles="$cibles $f"
    done
    cibles="$(printf '%s\n' $cibles | sort -u | tr '\n' ' ')"
    [ -n "${cibles// /}" ] && step "Tests des sujets touchés :$cibles" pytest_ $cibles
    printf '%s\n' "$changed" | grep -q '^frontend/' && step "Frontend : typage boutique + admin" typage
    ;;
  *) echo "Mode inconnu : $mode (complet | rapide)" >&2; exit 2 ;;
esac

if [ "$failed" -eq 0 ]; then echo "CHECK: OK ($mode)"; else echo "CHECK: ÉCHEC ($mode)"; fi
exit "$failed"
