#!/usr/bin/env bash
# Stop et SubagentStop : pas de « terminé » tant que la commande « Vérifier » échoue.
# - Rien à vérifier si aucun fichier de code n'a changé (question, relecture, doc).
# - Résultat mis en cache : l'état du dépôt déjà vérifié avec succès n'est pas relancé.
# - Garde-fou anti-boucle : après 3 refus consécutifs, Claude peut s'arrêter et doit
#   alors signaler l'échec à l'utilisateur.
set -uo pipefail
input="$(cat)"
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

field() { printf '%s' "$input" | python3 -c "import json,sys;print(json.load(sys.stdin).get('$1',''))" 2>/dev/null; }
# On ne s'appuie pas sur stop_hook_active : il laisserait finir dès la 2e tentative.
# Le compteur ci-dessous accorde 3 tentatives de correction.

changed="$(git status --porcelain --untracked-files=all | awk '{print $NF}' \
  | grep -E '(\.(py|js|jsx|ts|tsx|mjs|cjs|vue|svelte|prisma|sql|dart)|(^|/)pubspec\.yaml)$' | grep -vE '(^|/)(mapper|docs)/')"
[ -z "$changed" ] && exit 0

gitdir="$(git rev-parse --git-dir)"
state="$( { git diff HEAD; git ls-files --others --exclude-standard | xargs -r cat 2>/dev/null; } | md5sum | cut -d' ' -f1)"
[ "$(cat "$gitdir/claude-last-check" 2>/dev/null)" = "$state" ] && exit 0

counter="$gitdir/claude-stop-blocks-$(field session_id)"
blocks="$(cat "$counter" 2>/dev/null || echo 0)"
if [ "$blocks" -ge 3 ]; then
  rm -f "$counter"
  echo "La vérification échoue toujours après 3 tentatives : arrête-toi et signale l'échec à l'utilisateur." >&2
  exit 0
fi

# Group Achat : mode rapide (la suite entière dure ~7 min, la compétence verify l'exige à part).
out="$(bash .claude/skills/verify/scripts/check.sh rapide 2>&1)"
if [ $? -eq 0 ]; then
  echo "$state" > "$gitdir/claude-last-check"
  rm -f "$counter"
  exit 0
fi
echo $((blocks + 1)) > "$counter"
{
  echo "Pas terminé : la commande « Vérifier » échoue. Corrige avant de finir (tentative $((blocks + 1))/3)."
  printf '%s\n' "$out" | tail -30
} >&2
exit 2
