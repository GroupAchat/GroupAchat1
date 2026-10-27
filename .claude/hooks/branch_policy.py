"""Politique de branche, appliquée par guard.py à chaque commande git.

Toute branche de travail part de staging et y revient par fusion. main n'avance que jusqu'à
staging, par l'utilisateur : Claude ne la fait jamais avancer, ne la déplace ni ne la supprime,
quelle que soit la forme de la commande (git -C <chemin>, -c k=v, --git-dir=…).
"""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass

import git_policy

MAIN_BRANCHES = {"main", "master"}
MERGE_ONLY = {"staging"}  # on n'y entre que par fusion d'une branche feat/…, fix/…, refactor/…
MAIN_LOCKED = "main n'avance que jusqu'à staging, par l'utilisateur. Propose-lui la fusion ; il la fait lui-même."
UNKNOWN = ("dossier de git -C (ou --git-dir, --work-tree) introuvable : branche inconnue, opération refusée "
           "par prudence. Lance-la depuis le dépôt lui-même, une fois qu'il existe.")
ON_MAIN = ("merge", "rebase", "reset", "cherry-pick", "revert", "am", "pull")  # font avancer la branche courante
WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}  # options globales à valeur
TOKEN = re.compile(r"""(?:[^\s'"]+|'[^']*'|"[^"]*"|['"])+""")  # mots, guillemets compris


@dataclass
class Git:
    """Commande git dont les options globales sont retirées."""

    seg: str  # la commande sans options globales, telle que git_policy la lit
    sub: str
    args: list[str]
    cwd: str  # dossier où git s'exécute (git -C)
    repo: tuple[str, ...]  # --git-dir=…, --work-tree=… à repasser à git
    found: bool  # False : dossier ou dépôt introuvable, branche inconnue


def parse(seg: str, project: str) -> Git:
    """Retrouve la sous-commande derrière -C <chemin>, -c k=v, --git-dir=…, --no-pager, -P…"""
    raw = TOKEN.findall(seg.removeprefix("sudo "))[1:]  # sans « git »
    words = [re.sub(r"['\"]", "", w) for w in raw]
    cwd, repo, i = project, [], 0
    while i < len(words) and words[i].startswith("-"):
        name, eq, value = words[i].partition("=")
        if name in WITH_VALUE and not eq:
            i += 1
            value = words[i] if i < len(words) else ""
        if name == "-C":  # plusieurs -C s'enchaînent, chacun relatif au précédent
            cwd = os.path.join(cwd, os.path.expanduser(value))
        elif name in ("--git-dir", "--work-tree"):
            repo.append(f"{name}={os.path.expanduser(value)}")
        i += 1
    found = os.path.isdir(cwd) and all(os.path.exists(os.path.join(cwd, r.partition("=")[2])) for r in repo)
    seg = seg if i == 0 else " ".join(["git", *raw[i:]])
    sub = words[i] if i < len(words) else ""
    return Git(seg, sub, words[i + 1:], os.path.normpath(cwd), tuple(repo), found)


class Branches:
    """Branche courante de chaque dépôt visé : lue une fois, puis suivie à travers git switch / checkout."""

    def __init__(self) -> None:
        self.dirs: dict[tuple[str, tuple[str, ...]], str] = {}  # (cwd, repo) → dossier .git
        self.known: dict[str, str] = {}  # dossier .git → branche

    def _key(self, cmd: Git) -> str:
        where = (cmd.cwd, cmd.repo)
        if where not in self.dirs:  # git -C src et la racine désignent le même dépôt
            gitdir = git_policy.git(*cmd.repo, "rev-parse", "--absolute-git-dir", cwd=cmd.cwd).strip()
            self.dirs[where] = gitdir or cmd.cwd
        return self.dirs[where]

    def get(self, cmd: Git) -> str | None:
        """None : dépôt introuvable."""
        if not cmd.found:
            return None
        key = self._key(cmd)
        if key not in self.known:
            self.known[key] = git_policy.git(*cmd.repo, "branch", "--show-current", cwd=cmd.cwd).strip()
        return self.known[key]

    def update(self, cmd: Git, branch: str | None) -> None:
        if cmd.found and cmd.sub in ("switch", "checkout"):
            self.known[self._key(cmd)] = switched_to(cmd.args) or branch or ""


def switched_to(args: list[str]) -> str | None:
    """Branche où mène git switch / git checkout (None : checkout de fichiers)."""
    if "--" in args:
        return None
    for flag, name in zip(args, args[1:]):
        if flag in ("-c", "-C", "-b", "-B", "--create", "--force-create"):
            return name
    names = [a for a in args if not a.startswith("-")]
    return names[0] if names else None


def to_main(refspec: str) -> bool:
    """Refspec de fetch ou de pull qui écrit main en local : src:main, +src:refs/heads/main, *:*…"""
    if ":" not in refspec:
        return False
    dst = refspec.rsplit(":", 1)[1]
    dst = dst if dst.startswith("refs/") else f"refs/{dst}" if dst.startswith("heads/") else f"refs/heads/{dst}"
    return any(fnmatch.fnmatchcase(f"refs/heads/{m}", dst) for m in MAIN_BRANCHES)


def check_main(sub: str, args: list[str], branch: str | None) -> str | None:
    """Claude ne fait jamais avancer main : l'utilisateur seul l'amène jusqu'à staging."""
    names = [a for a in args if not a.startswith("-")]
    if branch in MAIN_BRANCHES and sub in ON_MAIN:
        return MAIN_LOCKED
    if sub == "rebase":  # git rebase <amont> main : rebase main elle-même
        rest = [a for a, prev in zip(args, [""] + args) if not a.startswith("-") and prev != "--onto"]
        if len(rest) >= 2 and rest[-1] in MAIN_BRANCHES:
            return MAIN_LOCKED
    if sub in ("fetch", "pull") and any(to_main(n) for n in names):
        return MAIN_LOCKED
    moves = ("--force", "--move", "--copy", "--delete")  # et -f, -m, -M, -c, -C, -d, -D, seuls ou groupés
    if sub == "branch" and set(names) & MAIN_BRANCHES and any(
        a in moves or re.fullmatch(r"-[a-zA-Z]*[fmMcCdD][a-zA-Z]*", a) for a in args
    ):
        return MAIN_LOCKED
    if sub == "update-ref" and names and names[0].removeprefix("refs/heads/") in MAIN_BRANCHES:
        return MAIN_LOCKED
    if sub in ("switch", "checkout", "worktree"):  # -C / -B main : remet main de force sur un autre commit
        pairs = list(zip(args, args[1:])) + [tuple(a.split("=", 1)) for a in args if a.startswith("--force-create=")]
        if any(flag in ("-C", "-B", "--force-create") and name in MAIN_BRANCHES for flag, name in pairs):
            return MAIN_LOCKED
    return None


def check_push(args: list[str], branch: str | None) -> str | None:
    if any(a.startswith(("--force", "+")) or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) for a in args):
        return "push forcé interdit. Pousse normalement ou crée une nouvelle branche."
    refs = [a for a in args if not a.startswith("-")][1:]  # le premier est le remote
    targets = {r.split(":")[-1].removeprefix("refs/heads/") for r in refs}
    if branch is None and (not refs or "HEAD" in targets):
        return UNKNOWN
    targets = {branch if t == "HEAD" else t for t in targets}
    if targets & MAIN_BRANCHES or (not refs and branch in MAIN_BRANCHES) or {"--all", "--mirror"} & set(args):
        return f"push vers main interdit : {MAIN_LOCKED}"
    return None


def check_commit_branch(cmd: Git, branch: str | None) -> str | None:
    if branch in MAIN_BRANCHES:
        return "commit direct sur main interdit. Crée une branche depuis staging : git switch -c feat/<nom> staging."
    # un git merge arrêté sur un conflit se conclut par git commit : c'est encore une fusion
    if branch in MERGE_ONLY and not git_policy.git(*cmd.repo, "rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=cmd.cwd):
        return (f"commit direct sur {branch} interdit : on n'y entre que par fusion (git merge [--ff-only] <branche>) "
                f"d'une branche feat/…, fix/… ou refactor/…. Crée-en une : git switch -c fix/<nom> {branch}.")
    return None


def check(cmd: Git, branch: str | None) -> str | None:
    """Raison du refus, ou None si la commande respecte la politique de branche."""
    if branch is None and cmd.sub in (*ON_MAIN, "commit"):
        return UNKNOWN
    reason = check_main(cmd.sub, cmd.args, branch)
    if not reason and cmd.sub == "push":
        reason = check_push(cmd.args, branch)
    if not reason and cmd.sub == "commit":
        reason = check_commit_branch(cmd, branch)
    return reason
