#!/usr/bin/env bash
# SessionStart (matcher "compact") : réinjecte l'état du travail après un compactage.
# Le texte écrit sur stdout est ajouté au contexte de Claude.
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0
echo "## Contexte réinjecté après compactage"
if [ -f mapper/00-contexte.md ]; then
  echo "### Projet (mapper/00-contexte.md)"; head -25 mapper/00-contexte.md
fi
if [ -f mapper/03-fonctionnalites/backlog.md ]; then
  echo "### Fonctionnalités en cours"; grep -iE "en cours|à vérifier" mapper/03-fonctionnalites/backlog.md | head -10
fi
mission="$(grep -lE '^statut: *en cours' mapper/07-missions/M-*.md 2>/dev/null | head -1)"
if [ -n "$mission" ]; then
  echo "### Mission en cours ($mission)"; grep -m1 '^# ' "$mission"
  awk '/^## (Critère de fin|Tâches)/{p=1} /^## (À livrer|Changements|Clôture)/{p=0} p' "$mission" | head -40
fi
# Kit de vérification : mission en cours dans audit/missions/ (agent verificateur)
verif="$(grep -lE '^statut: *en cours' audit/missions/M-*.md 2>/dev/null | head -1)"
if [ -n "$verif" ]; then
  echo "### Mission de vérification en cours ($verif)"; grep -m1 '^# ' "$verif"
  awk '/^## (Critère de fin|Tâches)/{p=1} /^## (Journal|Clôture)/{p=0} p' "$verif" | head -40
  [ -f audit/defauts.md ] && { echo "Défauts ouverts ou retenus :"; grep -E '^\|' audit/defauts.md | grep -iE 'ouvert|retenu|en correction' | head -15; }
fi
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "### Git"; echo "Branche : $(git branch --show-current)"
  echo "Fichiers modifiés :"; git status --short | head -30
  echo "Derniers commits :"; git log --oneline -5
fi
[ -f CLAUDE.local.md ] && { echo "### Notes de la branche (CLAUDE.local.md)"; head -20 CLAUDE.local.md; }
exit 0
