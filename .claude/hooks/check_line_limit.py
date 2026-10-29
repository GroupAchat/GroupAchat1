#!/usr/bin/env python3
"""PostToolUse (Edit, Write) : limite de 200 lignes par fichier de code.

- Fichier au-delà de 200 lignes → code 2, Claude reçoit l'ordre de découper.
- Fichier qui dépassait déjà la limite dans le dernier commit : seulement interdit de grossir.
PostToolUse arrive après l'écriture : le hook ne l'annule pas, il renvoie la consigne à Claude.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

MAX_LINES = int(os.environ.get("MAX_LINES", "200"))
PROJECT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
CODE = re.compile(r"\.(py|js|jsx|ts|tsx|mjs|cjs|vue|svelte|dart)$")
EXCLUDED = re.compile(
    r"(^|/)(migrations|node_modules|\.venv|venv|dist|build|\.next|generated|__pycache__|coverage|fixtures)/"
    r"|\.config\.(js|ts|mjs|cjs)$|\.d\.ts$|(^|/)settings(\.py|/)"
    r"|(^|/)\.dart_tool/|\.(g|freezed|gr|mocks|config)\.dart$|(^|/)firebase_options\.dart$|(^|/)l10n/generated/"
)


def lines_in_head(rel: str) -> int | None:
    try:
        out = subprocess.run(
            ["git", "show", f"HEAD:{rel}"], capture_output=True, text=True, cwd=PROJECT, timeout=5
        )
    except Exception:
        return None
    return out.stdout.count("\n") if out.returncode == 0 else None


def main() -> None:
    try:
        path = (json.load(sys.stdin).get("tool_input") or {}).get("file_path", "")
    except Exception:
        sys.exit(0)
    if not path or not CODE.search(path) or EXCLUDED.search(path) or not os.path.isfile(path):
        sys.exit(0)
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = sum(1 for _ in f)
    if lines <= MAX_LINES:
        sys.exit(0)
    rel = os.path.relpath(os.path.realpath(path), os.path.realpath(PROJECT))
    before = lines_in_head(rel)
    if before is not None and before > MAX_LINES:
        if lines <= before:
            sys.exit(0)
        print(
            f"{rel} dépassait déjà {MAX_LINES} lignes ({before}) et passe à {lines}. "
            "Ne le fais pas grossir : déplace le code ajouté dans un nouveau module.",
            file=sys.stderr,
        )
        sys.exit(2)
    print(
        f"{rel} fait {lines} lignes (max {MAX_LINES}). Découpe-le par responsabilité "
        "avant de continuer ; ne compacte pas le code pour passer sous la limite.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
