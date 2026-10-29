---
name: design
description: Direction visuelle et contrôle anti « look IA » pour les interfaces, pages, visuels et prompts d'images. À utiliser avant de créer ou modifier une interface, de choisir couleurs et polices, d'écrire un prompt d'image, ou pour juger si un écran fait générique.
---

# Design sans « look IA »

## Fichiers
- `anti-ai.md` — signes d'une interface générée et ce que font les vraies marques à la place (chiffres sur 69 marques).
- `images.md` — photos, illustrations, prompts d'images et de vidéo qui ne font pas « IA ».
- `brands-index.md` — une ligne par marque de la bibliothèque : thème, polices, titre display, couleurs, rayons.
- `DESIGN.template.md` — modèle de `design/DESIGN.md` du projet.
- `scripts/design-lint.py` — détecte dans le code les signes d'interface générée.
- `scripts/build-index.py` — régénère `brands-index.md` quand la bibliothèque change.

## Bibliothèque de références
Chemin indiqué dans `CLAUDE.md` (ligne « Références design »), par défaut `~/Boulot/opensource/brands-design-md`.
Pour une marque : `brands/<dossier>/DESIGN.md` (règles), `tokens.json` (valeurs), `preview.html` (aperçu),
`cover_*.webp` (capture du vrai site — à regarder avec Read).
Qualité inégale : seuls les DESIGN.md marqués « Riche » dans l'index contiennent de vraies règles ; ailleurs,
les « Do / Don't » sont génériques et certaines valeurs sont fausses. Croiser avec la capture et les tokens.

## Règles
1. **Pas d'interface sans `design/DESIGN.md`.** S'il n'existe pas, le faire créer par l'agent `directeur-artistique`.
2. **Jamais une seule marque copiée.** On emprunte des principes à 2 ou 3 références, jamais logo, nom, police propriétaire,
   illustration ou mascotte. Le résultat ne doit être confondu avec aucune d'elles.
3. **Tout passe par les tokens** (`design/tokens.css`) : aucune couleur, taille ou rayon en dur dans les composants.
   App Flutter : les tokens sont traduits dans `lib/core/theme/` (`app_tokens.dart`, `app_theme.dart`), seul endroit où une valeur `Color(0x…)` est écrite.
4. **Contenu réel** : textes, noms, prix (FCFA), lieux du projet. Pas de lorem ipsum, pas de chiffres inventés.
5. **Contrôler** avant de livrer :
   ```bash
   python3 .claude/skills/design/scripts/design-lint.py src
   ```
   (app Flutter : `design-lint.py lib`). Zéro alerte BLOQUANT ; chaque alerte « à revoir » est soit corrigée, soit justifiée par une règle de `design/DESIGN.md`.
6. **Regarder le résultat** : capture d'écran (Playwright) en 1440px et 390px de large, puis le test final de `anti-ai.md`.
   App Flutter : build web + Playwright en 360px et 390px, ou `flutter screenshot` sur émulateur (voir `integrateur-ui`).

## Rapport
Terminer par `DESIGN: PASS` ou `DESIGN: FAIL`, avec les alertes restantes et ce qu'il faut corriger.
