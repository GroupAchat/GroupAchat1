#!/usr/bin/env bash
# Kit de vérification : garde les sept agents du kit d'accord entre ce projet et le template.
#
#   kit-sync.sh apres-edition   PostToolUse (Edit|Write) : un agent du kit vient d'être modifié
#                               → il remonte dans le template, puis sync.sh le propage aux stacks.
#   kit-sync.sh demarrage       SessionStart (startup) : le template a-t-il des versions plus
#                               récentes ? → le signale (ne remplace rien : le projet peut avoir
#                               des modifications locales).
#
# Template : $CLAUDE_TEMPLATE_DIR, sinon ~/Boulot/claude-template. Absent → ne fait rien.
# Ne bloque jamais l'outil, sauf pour un agent qui contient un terme propre au projet :
# Claude reçoit alors le refus et doit déplacer ce terme dans .claude/verification.md.
set -uo pipefail
PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TEMPLATE="${CLAUDE_TEMPLATE_DIR:-$HOME/Boulot/claude-template}"
SCRIPT="$TEMPLATE/kit-verification.sh"
KIT="verificateur testeur-fonctionnel auditeur-securite gardien-regles analyste-logique correcteur relecteur-correction"
[ -f "$SCRIPT" ] || exit 0
[ "$(cd "$PROJECT" && pwd)" = "$(cd "$TEMPLATE" && pwd)" ] && exit 0  # pas dans le template lui-même

contexte() {  # texte ajouté au contexte de Claude
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": sys.argv[1], "additionalContext": sys.argv[2]}}))' "$1" "$2"
}

case "${1:-}" in
  apres-edition)
    path="$(python3 -c 'import json,sys; print((json.load(sys.stdin).get("tool_input") or {}).get("file_path",""))' 2>/dev/null)"
    agent="$(basename "$path" .md)"
    case "$path" in */.claude/agents/*.md) ;; *) exit 0 ;; esac
    case " $KIT " in *" $agent "*) ;; *) exit 0 ;; esac
    if out="$(bash "$SCRIPT" remonter "$PROJECT" "$agent" 2>&1)"; then
      [ -n "$out" ] && contexte PostToolUse "Kit de vérification — $out"
      exit 0
    fi
    printf 'Kit de vérification : %s\n' "$out" >&2
    exit 2
    ;;
  demarrage)
    plus_recents="$(bash "$SCRIPT" etat "$PROJECT" 2>/dev/null | awk '$2=="template-plus-recent"||$2=="absent-projet"{print $1}' | tr '\n' ' ')"
    [ -z "$plus_recents" ] && exit 0
    contexte SessionStart "Kit de vérification : le template a une version plus récente ou absente d'ici pour : $plus_recents. Propose à l'utilisateur : bash $SCRIPT descendre \"$PROJECT\" (les versions locales sont sauvegardées avant)."
    ;;
esac
exit 0
