#!/usr/bin/env python3
"""PreToolUse (Bash, Edit, Write) : bloque les actions dangereuses.

Code de sortie 2 = action bloquée ; le message (stderr) est renvoyé à Claude, qui
sait alors quoi faire à la place. Bibliothèque standard uniquement.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.dont_write_bytecode = True  # pas de __pycache__ dans .claude/hooks/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import branch_policy  # noqa: E402
import git_policy  # noqa: E402

PROJECT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
ENV_ALLOWED = (".env.exemple", ".env.example", ".env.sample", ".env.template")  # Group Achat : .env.exemple
ENV_FILES = (".env", ".env.local")  # les deux seuls fichiers d'environnement autorisés


def block(reason: str) -> None:
    print(f"Bloqué par .claude/hooks/guard.py : {reason}", file=sys.stderr)
    sys.exit(2)


# ── Bash ──────────────────────────────────────────────────────


def is_env_name(token: str) -> bool:
    name = os.path.basename(token.strip("'\""))
    return bool(re.fullmatch(r"\.env(\.[\w.-]+)?", name)) and name not in ENV_ALLOWED


def check_env_writes(seg: str) -> None:
    """Seuls .env et .env.local existent, et Claude ne les crée qu'en copiant .env.exemple."""
    words = seg.split()
    targets = re.findall(r">>?\s*(\S+)", seg)
    if words and words[0] in ("cp", "mv", "ln", "install") and len(words) >= 3:
        targets.append(words[-1])
    if words and words[0] == "tee":
        targets += [w for w in words[1:] if not w.startswith("-")]
    for target in targets:
        if not is_env_name(target):
            continue
        name = os.path.basename(target.strip("'\""))
        if name not in ENV_FILES:
            block(f"{name} : seuls .env et .env.local sont autorisés (pas de .env.production, .env.bak…).")
        sources = [os.path.basename(w) for w in words[1:-1] if not w.startswith("-")]
        if not (words[0] == "cp" and sources == [".env.exemple"]):
            block(f"{name} n'est jamais écrit par Claude. Seule la copie depuis .env.exemple est permise ; l'utilisateur remplit les valeurs.")


def check_git(seg: str, branches: branch_policy.Branches) -> None:
    """Contrôle une commande git, options globales retirées (git -C <chemin>, -c k=v…)."""
    cmd = branch_policy.parse(seg, PROJECT)
    if cmd.sub in ("commit", "push", "merge", "rebase") and "--no-verify" in cmd.args:
        block("--no-verify interdit : corrige ce que les vérifications signalent.")
    branch = branches.get(cmd)
    reason = branch_policy.check(cmd, branch)
    if reason:
        pass
    elif cmd.sub == "push":
        reason = git_policy.check_push(cmd.cwd)
    elif cmd.sub == "add":
        reason = git_policy.check_add(cmd.seg, cmd.cwd)
    elif cmd.sub == "commit":
        reason = git_policy.check_commit(cmd.seg, cmd.cwd)
    if reason:
        block(reason)
    branches.update(cmd, branch)


def check_bash(cmd: str) -> None:
    if re.search(r"sk_live_[0-9A-Za-z]{8,}|\bsk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY", cmd):
        block("clé secrète en clair dans la commande. Passe par une variable d'environnement.")
    branches = branch_policy.Branches()  # lues à la première commande git, suivies à travers git switch
    for raw in re.split(r"&&|\|\||;|\||\n", cmd):
        seg = " ".join(raw.split())
        if not seg:
            continue
        check_env_writes(seg)
        if re.match(r"(sudo )?git \S", seg):
            check_git(seg, branches)
        if re.match(r"(sudo )?rm (-\w*r\w*f\w*|-\w*f\w*r\w*|-r -f|-f -r)( |$)", seg):
            targets = seg.split()[2:]
            if any(t in ("/", "/*", "~", "~/", "~/*", "*", ".", "./", "..", "$HOME") for t in targets):
                block("suppression récursive d'un dossier racine refusée. Supprime des chemins précis.")
        destructive = (
            r"prisma migrate reset",
            r"prisma db push\b.*(--force-reset|--accept-data-loss)",
            r"manage\.py (flush|reset_db)\b",
            r"manage\.py migrate \S+ zero\b",
            r"\b(drop (table|database|schema)|truncate( table)?) ",
            r"docker( |-)compose down\b.*(-v\b|--volumes)",
        )
        if any(re.search(p, seg, re.IGNORECASE) for p in destructive):
            block("commande qui efface des données. Elle ne se lance que sur demande explicite, par l'utilisateur lui-même.")
        if re.match(r"(cat|less|more|head|tail|bat|nl|strings|grep|source|\.|cp|scp) ", seg):
            tokens = seg.split()[1:]
            if seg.split()[0] in ("cp", "scp"):
                tokens = tokens[:-1]  # la destination n'est pas lue
            for token in tokens:
                if is_env_name(token):
                    block(f"lecture de {token} refusée : il contient des secrets. Utilise .env.exemple.")


# ── Fichiers ──────────────────────────────────────────────────


def check_file(path: str, tool: str) -> None:
    if not path:
        return
    name = os.path.basename(path)
    if re.fullmatch(r"\.env(\.[\w.-]+)?", name) and name not in ENV_ALLOWED:
        if name not in ENV_FILES:
            block(f"{name} : seuls .env et .env.local sont autorisés (pas de .env.production, .env.bak…).")
        block(f"{name} est protégé. Ajoute la variable dans .env.exemple et dans la config du projet ; l'utilisateur remplit la valeur.")
    absolute = path if os.path.isabs(path) else os.path.join(PROJECT, path)
    is_migration = re.search(r"prisma/migrations/[^/]+/migration\.sql$", path) or re.search(
        r"/migrations/\d{4}_[^/]+\.py$", path
    )
    if is_migration and os.path.exists(absolute):
        block(f"{path} est une migration existante : ne jamais la modifier. Crée une nouvelle migration.")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool == "Bash":
        check_bash(tool_input.get("command", ""))
    elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        check_file(tool_input.get("file_path") or tool_input.get("notebook_path", ""), tool)
    sys.exit(0)


if __name__ == "__main__":
    main()
