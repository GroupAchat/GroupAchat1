#!/usr/bin/env python3
"""Repère dans le frontend les signes d'une interface « générée par IA ».

Usage : python3 design-lint.py [dossier ...]   (défaut : le projet courant)
Sortie : une alerte par ligne « niveau  fichier:ligne  règle — extrait ».
Code de sortie : 1 s'il reste une alerte BLOQUANT, 0 sinon. Les alertes « à revoir » demandent un jugement.
Les couleurs en dur sont tolérées dans les définitions de tokens (`--nom: #...`), la config Tailwind
et, en Flutter, dans `lib/core/theme/` (fichiers de tokens et de thème).
"""
from __future__ import annotations

import colorsys
import re
import sys
from pathlib import Path

EXTENSIONS = {".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".astro", ".html", ".css", ".scss", ".dart"}
SKIP_DIRS = {"node_modules", ".next", "dist", "build", "out", ".git", "coverage", "venv", ".venv",
             "__pycache__", "staticfiles", "vendor", ".claude", "migrations"}
SKIP_FILES = re.compile(r"(tailwind\.config|\.test\.|\.spec\.|\.stories\.|\.d\.ts$|preview\.html$|\.(g|freezed)\.dart$|_test\.dart$)")
BLOQUANT, REVOIR = "BLOQUANT", "à revoir"

CLICHES = re.compile(
    r"\b(r[ée]volutionn\w*|boostez|lib[ée]rez (le|votre) potentiel|en quelques clics|sans effort|tout-en-un|"
    r"nouvelle g[ée]n[ée]ration|unlock|supercharge|seamless(ly)?|elevate|effortless(ly)?|game[- ]changer|"
    r"next[- ]gen(eration)?|cutting[- ]edge|empower)\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF✨⭐⚡✅❌❤]")
HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
TOKEN_DEF = re.compile(r"--[\w-]+\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))")
TW_GRADIENT = re.compile(r"\bfrom-(purple|violet|indigo|fuchsia|pink)-\d+\b.*\bto-(blue|indigo|purple|violet|pink|cyan)-\d+")
GRADIENT_TEXT = re.compile(r"bg-clip-text[^\"'`]*text-transparent|text-transparent[^\"'`]*bg-clip-text|background-clip:\s*text")
TW_DEFAULT_PALETTE = re.compile(r"\b(bg|text|border|ring|from|to|via)-(indigo|violet|purple|fuchsia|slate)-\d00\b")
CHECKS_REVOIR = [
    (re.compile(r"\bshadow-(lg|xl|2xl)\b|box-shadow:\s*0 (10|20|25)px"), "ombre forte : réservée à ce qui flotte"),
    (re.compile(r"\bbackdrop-blur|backdrop-filter:\s*blur"), "verre dépoli : seulement sur une barre au-dessus de contenu"),
    (re.compile(r"\bhover:(scale|-translate-y)-"), "survol qui grossit ou soulève : préférer un changement de couleur"),
    (re.compile(r"\banimate-(bounce|pulse|ping)\b"), "animation décorative (hors indicateur de chargement)"),
    (re.compile(r"\brounded-(2xl|3xl)\b"), "grand rayon : vérifier qu'il correspond au rayon choisi dans DESIGN.md"),
]
# ── Flutter ──────
DART_COLOR = re.compile(r"\bColor\(\s*0x[0-9a-fA-F]{2}([0-9a-fA-F]{6})\s*\)|\bColor\.from(ARGB|RGBO)\(")
DART_MATERIAL = re.compile(r"\bColors\.(?!white\b|black\b|transparent\b)(\w+)")
DART_PURPLE = re.compile(r"\bColors\.(purple|deepPurple|indigo|purpleAccent|deepPurpleAccent|indigoAccent)\b")
CHECKS_REVOIR_DART = [
    (re.compile(r"\bBackdropFilter\b|ImageFilter\.blur"), "verre dépoli : seulement sur une barre au-dessus de contenu"),
    (re.compile(r"blurRadius:\s*([2-9]\d|\d{3})"), "ombre forte : réservée à ce qui flotte"),
    (re.compile(r"BorderRadius\.circular\(\s*(2[4-9]|[3-9]\d)"), "grand rayon : vérifier qu'il correspond au rayon choisi dans DESIGN.md"),
    (re.compile(r"\bfontSize:\s*\d"), "taille de police en dur : passer par Theme.of(context).textTheme"),
]


def is_theme_file(path: Path) -> bool:
    return path.suffix == ".dart" and ("theme" in path.parts or re.search(r"(tokens|theme)\w*\.dart$", path.name) is not None)


LOREM = re.compile(r"lorem ipsum|\b(john|jane) doe\b", re.I)


def files(roots: list[Path]):
    for root in roots:
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            if path.suffix in EXTENSIONS and not SKIP_DIRS.intersection(path.parts) and not SKIP_FILES.search(path.name):
                yield path


def is_purple_blue(hex_color: str) -> bool:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    r, g, b = (int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    return sat > 0.35 and 0.2 < light < 0.8 and 200 <= hue * 360 <= 320


def check_line(line: str, path: Path) -> list[tuple[str, str]]:
    alerts: list[tuple[str, str]] = []
    markup = path.suffix not in {".css", ".scss"}
    if LOREM.search(line):
        alerts.append((BLOQUANT, "texte factice : mettre le vrai contenu du projet"))
    if CLICHES.search(line) and markup:
        alerts.append((BLOQUANT, f"formule marketing creuse « {CLICHES.search(line).group(0)} »"))
    if EMOJI.search(line) and markup:
        alerts.append((BLOQUANT, "emoji dans l'interface : utiliser la famille d'icônes du projet ou rien"))
    if TW_GRADIENT.search(line):
        alerts.append((BLOQUANT, "dégradé violet → bleu/rose"))
    if "linear-gradient" in line or "radial-gradient" in line:
        stops = HEX.findall(line)
        if len(stops) >= 2 and sum(is_purple_blue(c) for c in stops) >= 2:
            alerts.append((BLOQUANT, "dégradé violet → bleu en CSS"))
    if GRADIENT_TEXT.search(line):
        alerts.append((BLOQUANT, "texte en dégradé : au plus un mot, validé dans DESIGN.md"))
    hard = HEX.search(TOKEN_DEF.sub("", line))
    if hard and not ("gradient" in line and alerts):
        alerts.append((BLOQUANT, f"couleur en dur {hard.group(0)} : passer par un token"))
    if path.suffix == ".dart":
        alerts += check_dart(line, path)
    if TW_DEFAULT_PALETTE.search(line):
        alerts.append((REVOIR, f"palette Tailwind par défaut « {TW_DEFAULT_PALETTE.search(line).group(0)} » au lieu des tokens"))
    for pattern, message in CHECKS_REVOIR:
        if pattern.search(line):
            alerts.append((REVOIR, message))
    return alerts


def check_dart(line: str, path: Path) -> list[tuple[str, str]]:
    alerts: list[tuple[str, str]] = []
    if "Gradient" in line:
        stops = ["#" + m.group(1) for m in DART_COLOR.finditer(line) if m.group(1)]
        if DART_PURPLE.search(line) or sum(is_purple_blue(c) for c in stops) >= 2:
            alerts.append((BLOQUANT, "dégradé violet → bleu en Flutter"))
    if is_theme_file(path):
        return alerts
    color = DART_COLOR.search(line)
    if color and not alerts:
        alerts.append((BLOQUANT, f"couleur en dur {color.group(0)} : passer par AppTokens ou colorScheme"))
    material = DART_MATERIAL.search(line)
    if material:
        alerts.append((REVOIR, f"couleur Material par défaut « Colors.{material.group(1)} » au lieu des tokens"))
    for pattern, message in CHECKS_REVOIR_DART:
        if pattern.search(line):
            alerts.append((REVOIR, message))
    return alerts


def check_fonts(paths: list[Path]) -> list[str]:
    """Une seule famille, Inter : signe typique d'une interface par défaut."""
    families: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r"font-family:\s*['\"]?([A-Za-z][\w ]*)", text):
            families.add(match.group(1).strip())
        for match in re.finditer(r"\bimport\s*\{([^}]+)\}\s*from\s*['\"]next/font/google", text):
            families.update(name.strip() for name in match.group(1).split(","))
        for match in re.finditer(r"GoogleFonts\.(\w+?)(TextTheme)?\(|fontFamily:\s*['\"]([^'\"]+)", text):
            families.add(match.group(1) or match.group(3))
    real = {f for f in families if f.lower() not in {"inherit", "var", "system", "ui", "sans", "serif", "monospace"}}
    if real and all(f.lower().startswith("inter") for f in real):
        return ["une seule famille de police (Inter) : ajouter une police de titre choisie dans DESIGN.md"]
    return []


def main() -> int:
    roots = [Path(a) for a in sys.argv[1:]] or [Path.cwd()]
    paths = sorted(set(files(roots)))
    counts = {BLOQUANT: 0, REVOIR: 0}
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for level, message in check_line(line, path):
                counts[level] += 1
                print(f"{level:9} {path}:{number}  {message} — {line.strip()[:90]}")
    for message in check_fonts(paths):
        counts[REVOIR] += 1
        print(f"{REVOIR:9} (projet)  {message}")
    print(f"\nDESIGN-LINT : {len(paths)} fichier(s), {counts[BLOQUANT]} bloquant(s), {counts[REVOIR]} à revoir.")
    return 1 if counts[BLOQUANT] else 0


if __name__ == "__main__":
    sys.exit(main())
