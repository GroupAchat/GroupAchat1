#!/usr/bin/env python3
"""Génère brands-index.md : une ligne par marque de la bibliothèque brands-design-md.

Usage : python3 build-index.py <dossier brands-design-md> > brands-index.md
Les valeurs aberrantes de la bibliothèque (taille 0.14px, noms de tokens qui sont des phrases)
sont signalées par « ? » au lieu d'être recopiées.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RICH_SECTIONS = ("## Imagery", "## Surfaces", "## Agent Prompt Guide", "## Usage guidance", "## Rules")


def px(value) -> float | None:
    match = re.match(r"(-?[\d.]+)(px|rem|em)?", str(value).strip())
    if not match:
        return None
    number = float(match.group(1))
    return number * 16 if match.group(2) == "rem" else number


def values(group: dict) -> dict:
    return {k: v["$value"] for k, v in group.items() if isinstance(v, dict) and "$value" in v}


def family(style: dict) -> str:
    fam = style.get("fontFamily", "")
    fam = fam[0] if isinstance(fam, list) else fam
    name = str(fam).split(",")[0].strip(" '\"")
    # Certains tokens ont une phrase à la place d'un nom de police
    noise = re.search(r"[{}()/—]|\b(buttons?|cards?|badges?|elements?|frames?|default)\b", name, re.I)
    return name if name and len(name) < 40 and not noise else ""


def display_style(typo: dict) -> tuple[float, dict] | None:
    best = None
    for style in typo.values():
        if not isinstance(style, dict):
            continue
        size = px(style.get("fontSize"))
        if size and 24 <= size <= 200 and (best is None or size > best[0]):
            best = (size, style)
    return best


def tracking_percent(size: float, style: dict) -> str:
    raw = style.get("letterSpacing")
    if raw in (None, "", "normal", 0, "0"):
        return "0"
    if str(raw).endswith("em") and not str(raw).endswith("rem"):
        value = float(str(raw)[:-2]) * size
    else:
        value = px(raw) or 0.0
    percent = value / size * 100
    return f"{percent:+.1f}%" if abs(percent) < 15 else "?"


def line_height(size: float, style: dict) -> str:
    raw = style.get("lineHeight")
    if raw is None:
        return "?"
    if "px" in str(raw):
        return f"{px(raw) / size:.2f}"
    try:
        return f"{float(raw):.2f}"
    except ValueError:
        return "?"


def pick_color(colors: dict, pattern: str) -> str:
    for name, value in colors.items():
        if len(name) < 40 and re.search(pattern, name) and isinstance(value, str) and value.startswith("#"):
            return value.lower()
    return "?"


def radius_summary(radii: dict) -> str:
    sizes = sorted({px(v) for v in radii.values() if px(v) is not None and px(v) < 999})
    pill = any((px(v) or 0) >= 999 for v in radii.values())
    text = "/".join(str(int(s)) for s in sizes[:5]) or "0"
    return text + (" + pill" if pill else "")


def row(root: Path, entry: dict) -> str:
    folder = root / "brands" / entry["folder"]
    tokens = json.loads((folder / "tokens.json").read_text(encoding="utf-8"))
    design = (folder / "DESIGN.md").read_text(encoding="utf-8")
    typo = values(tokens.get("typography", {}))
    colors = values(tokens.get("color", {}))
    fonts = sorted({family(s) for s in typo.values() if isinstance(s, dict)} - {""})
    weights = sorted({s.get("fontWeight") for s in typo.values()
                      if isinstance(s, dict) and isinstance(s.get("fontWeight"), (int, float))})
    disp = display_style(typo)
    if disp:
        size, style = disp
        display = f"{int(size)}px/{style.get('fontWeight', '?')} lh {line_height(size, style)} tr {tracking_percent(size, style)}"
    else:
        display = "?"
    theme = tokens.get("meta", {}).get("theme") or ("dark" if "Dark UI" in entry["tags"] else "light")
    canvas = pick_color(colors, r"^(canvas|paper|page|background|bg)|canvas")
    ink = pick_color(colors, r"^(ink|text|foreground)$|^ink|text-primary")
    accent = pick_color(colors, r"^(primary|brand|accent)")
    rich = "oui" if any(s in design for s in RICH_SECTIONS) else ""
    tags = ", ".join(t for t in entry["tags"] if t not in ("Design System", "Light UI"))
    return (f"| {entry['folder']} | {entry['category']} | {theme} | {tags} | {', '.join(fonts[:3]) or '?'} "
            f"| {display} | {'/'.join(str(w) for w in weights)} | {canvas} | {ink} | {accent} "
            f"| {radius_summary(values(tokens.get('radius', {})))} | {rich} |")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser()
    registry = json.loads((root / "registry.json").read_text(encoding="utf-8"))
    print("# Index des références design\n")
    print(f"Généré par `scripts/build-index.py` depuis `{sys.argv[1]}` ({len(registry)} marques).")
    print("Display = plus grand style de titre : taille/graisse, interligne, approche (% de la taille).")
    print("« ? » = valeur absente ou aberrante dans la bibliothèque : lire le DESIGN.md.")
    print("Riche = le DESIGN.md contient de vraies règles (imagerie, surfaces, à faire / à éviter).\n")
    print("| Dossier | Catégorie | Thème | Tags | Polices | Display | Graisses | Fond | Texte | Accent | Rayons | Riche |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for entry in sorted(registry, key=lambda e: e["folder"]):
        try:
            print(row(root, entry))
        except (OSError, json.JSONDecodeError) as error:
            print(f"| {entry['folder']} | lecture impossible : {error} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
