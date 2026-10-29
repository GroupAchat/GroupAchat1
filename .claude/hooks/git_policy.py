"""Politique « ce qui entre dans git », appliquée par guard.py sur git add / commit / push.

La liste positive est dans `.claude/conventions/workflow.md` ; ici, ce qui est refusé et pourquoi.
"""

from __future__ import annotations

import os
import re
import subprocess

MAX_BYTES = 5 * 1024 * 1024
COMMIT_TYPES = "feat|fix|refactor|test|docs|chore|perf|ci|build|style|revert"
SAMPLE_DIRS = r"(^|/)(tests?|fixtures|seeds?|__fixtures__|testdata)/"

# (motif sur le chemin, raison) — le premier qui correspond l'emporte
FORBIDDEN: list[tuple[str, str]] = [
    (r"(^|/)\.env(\.(?!exemple$|example$|sample$|template$)[\w.-]+)?$", "fichier d'environnement (secrets)"),
    (r"\.(pem|key|p12|pfx|jks|keystore|crt)$|(^|/)id_(rsa|ed25519|ecdsa)(\.pub)?$", "clé ou certificat"),
    (r"(^|/)(credentials|service[-_]account[\w-]*|secrets?)\.(json|ya?ml|txt)$", "fichier d'identifiants"),
    (r"(^|/)key\.properties$", "identifiants de signature Android"),
    (r"(^|/)(node_modules|\.venv|venv|__pycache__|\.pnpm-store|vendor/bundle|\.pub-cache|Pods|\.symlinks)/", "dépendances installées"),
    (r"\.py[co]$|(^|/)(\.(ruff|pytest|mypy)_cache|\.turbo|\.parcel-cache|\.cache|\.dart_tool|\.gradle)/"
     r"|(^|/)\.flutter-plugins(-dependencies)?$", "cache"),
    (r"(^|/)(dist|build|\.next|out|\.nuxt|\.svelte-kit|staticfiles|generated|\.prisma)/", "fichier généré par un build"),
    (r"(^|/)(coverage|htmlcov|playwright-report|test-results|\.nyc_output)/|(^|/)\.coverage$", "rapport de tests"),
    (r"\.(log|sqlite3?|db|dump|bak|swp|swo|tmp|orig|rej)$|\.sql\.gz$|~$", "journal, base locale ou fichier temporaire"),
    (r"(^|/)(media|uploads|user[-_]?files)/", "fichiers envoyés par les utilisateurs"),
    (r"(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini)$|(^|/)\.idea/", "fichier du système ou de l'éditeur"),
    (r"(^|/)\.vscode/(?!extensions\.json$|settings\.json$)", "réglage personnel de l'éditeur"),
    (r"(^|/)local\.properties$", "chemins de la machine (Android)"),
    (r"(^|/)CLAUDE\.local\.md$|(^|/)\.claude/settings\.local\.json$|(^|/)CLAUDE\.template\.md$", "fichier Claude personnel"),
]
# Données : autorisées seulement comme jeux d'essai fictifs dans tests/, fixtures/, seeds/
DATA_FILE = r"\.(csv|xlsx?|parquet|jsonl|ndjson)$"


def git(*args: str, cwd: str) -> str:
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd, timeout=10)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""


def refusal(path: str) -> str | None:
    for pattern, reason in FORBIDDEN:
        if re.search(pattern, path, re.IGNORECASE):
            return reason
    if re.search(DATA_FILE, path, re.IGNORECASE) and not re.search(SAMPLE_DIRS, path):
        return "données réelles (seuls les jeux d'essai fictifs vont dans tests/, fixtures/ ou seeds/)"
    return None


def problems(paths: list[str], cwd: str, size_ref: str | None) -> list[str]:
    """size_ref : ':' pour l'index, un commit pour HEAD, None pour le disque."""
    found = []
    for path in paths:
        reason = refusal(path)
        if reason:
            found.append(f"{path} — {reason}")
            continue
        if size_ref is None:
            full = os.path.join(cwd, path)
            size = os.path.getsize(full) if os.path.isfile(full) else 0
        else:
            raw = git("cat-file", "-s", f"{size_ref}{path}", cwd=cwd).strip()
            size = int(raw) if raw.isdigit() else 0
        if size > MAX_BYTES:
            found.append(f"{path} — {size // 1024 // 1024} Mo (> 5 Mo : stockage externe ou Git LFS)")
    return found


def message(found: list[str], action: str) -> str:
    lines = "\n  - ".join(found[:15])
    more = f"\n  … et {len(found) - 15} autre(s)" if len(found) > 15 else ""
    return (f"{action} refusé, ces fichiers n'entrent pas dans git :\n  - {lines}{more}\n"
            + ("Retire-les des commits (git rm --cached <fichier>, nouveau commit ; si l'historique doit être nettoyé, demande à l'utilisateur) "
               if action == "push" else "Retire-les (git restore --staged <fichier>) ")
            + "et ajoute leur motif au .gitignore. "
            "Voir « Ce qui entre dans git » dans .claude/conventions/workflow.md.")


def check_add(seg: str, cwd: str) -> str | None:
    args = seg.split()[2:]
    if any(a in ("-f", "--force") for a in args):
        return "git add --force interdit : un fichier ignoré l'est pour une raison."
    if any(a in ("-A", "--all", ".", "*", ":/") or a.startswith("-A") for a in args):
        return ("git add global interdit pour Claude : regarde git status, puis ajoute les fichiers par leur nom "
                "(git add src/x.py tests/test_x.py).")
    paths = [a.strip("'\"") for a in args if not a.startswith("-")]
    found = problems(paths, cwd, size_ref=None)
    return message(found, "git add") if found else None


def check_commit(seg: str, cwd: str) -> str | None:
    paths = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", cwd=cwd).split()
    if re.search(r"\s(-a|--all|-\w*a\w*)\b", seg):
        paths += git("diff", "--name-only", "--diff-filter=ACMR", cwd=cwd).split()
    found = problems(sorted(set(paths)), cwd, size_ref=":")
    if found:
        return message(found, "commit")
    subject = re.search(r"-m\s+(['\"])(.+?)\1", seg)
    if subject:
        first = subject.group(2).splitlines()[0]
        # Group Achat : le style du dépôt est une phrase française, verbe en tête,
        # sans préfixe de type (« Permet au groupeur de photographier le lot… »).
        vague = {"update", "fix", "wip", "test", "commit", "maj", "modif", "correction"}
        if len(first) > 72 or len(first) < 12 or first.lower().strip(" .") in vague or not first[0].isupper():
            return (f"message de commit « {first} » hors format. Attendu : une phrase française qui dit "
                    "ce que le commit change, verbe au présent en tête, 12 à 72 caractères "
                    "(ex. « Relance les participants qui n'ont pas retiré leur colis »).")
    return None


def check_push(cwd: str) -> str | None:
    """Vérifie les commits qui partiraient, même faits à la main."""
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", cwd=cwd).strip()
    candidates = ("origin/staging", "origin/main", "origin/master")  # sans amont : la base d'intégration
    base = upstream or next((r for r in candidates if git("rev-parse", "--verify", r, cwd=cwd)), "")
    if base:
        paths = git("diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD", cwd=cwd).split()
    else:  # premier push : tout ce que contient HEAD part
        paths = git("ls-tree", "-r", "--name-only", "HEAD", cwd=cwd).split()
    found = problems(paths, cwd, size_ref="HEAD:")
    return message(found, "push") if found else None
