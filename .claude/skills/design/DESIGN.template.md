# <Nom du projet> — Direction visuelle

> <Une phrase : l'impression qu'on veut laisser, pour qui. Ex. « Un carnet de quartier : chaleureux, direct, fait à Lomé ».>

**Thème :** clair | sombre
**Trois mots :** <ex. chaleureux, dense, honnête>
**Ce que ce n'est pas :** <ex. pas une startup de la Silicon Valley, pas un site de luxe>

## Décisions fortes
Les 2 ou 3 choix qui rendent le projet reconnaissable sans son logo. Tout le reste en découle.
1. <ex. Fond papier `#f5f1ec`, aucune ombre sur les cartes : la profondeur vient des filets.>
2. <ex. Titres en serif Instrument Serif 400 à grande taille, interligne 1.0.>
3. <ex. Une seule couleur d'action, orange piment `#e8590c`, jamais en fond de section.>

## Références
Ce qu'on prend à chaque référence de `brands-design-md` — jamais tout d'une seule marque.
| Marque | Ce qu'on prend | Ce qu'on laisse |
|---|---|---|
| <dossier> | <ex. rythme des sections, filets> | <ex. sa palette> |

## Couleurs
| Nom | Valeur | Token | Rôle |
|---|---|---|---|
| canvas | `#` | `--color-canvas` | fond de page |
| surface | `#` | `--color-surface` | cartes, panneaux |
| ink | `#` | `--color-ink` | texte principal |
| ink-mute | `#` | `--color-ink-mute` | texte secondaire |
| hairline | `#` | `--color-hairline` | filets, bordures |
| action | `#` | `--color-action` | action principale, une par écran |
| on-action | `#` | `--color-on-action` | texte sur l'action |
| danger / success | `#` | `--color-danger` … | états |

## Typographie
- Titres : <police libre>, graisses <…> ; texte : <police> ; mono : <police ou aucune>.
| Rôle | Taille | Interligne | Approche | Graisse | Token |
|---|---|---|---|---|---|
| display | <56–96px> | <0.95–1.1> | <−2 % à −4 %> | | `--text-display` |
| h1 | | | | | `--text-h1` |
| h2 | | | | | `--text-h2` |
| body | 16px | 1.5 | 0 | 400 | `--text-body` |
| small | 14px | 1.45 | 0 | 400 | `--text-small` |
| label | 12px | 1.2 | +4 % | 500, capitales | `--text-label` |

## Espacements et formes
- Échelle : 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96.
- Largeur max : <…>px. Écart entre sections : <…>px.
- Rayons : boutons <…>, champs <…>, cartes <…>, pastilles 9999px.
- Profondeur : <filets / surfaces / ombre réservée à …>.

## Composants
Pour chacun : fond, texte, rayon, marge interne, états (survol, focus, désactivé, chargement).
- Bouton principal :
- Bouton secondaire :
- Champ de saisie :
- Carte :
- Navigation :

## Imagerie
- Photos : <vraies photos de … ; style ; lumière>.
- Illustrations : <style unique ou aucune>.
- Icônes : <famille, épaisseur> ou aucune.

## Voix
- Tutoiement ou vouvoiement ; ton ; longueur des titres.
- Exemples de titres validés : <…>.

## À faire
- <règles précises, chiffrées>

## Interdits
- <règles précises — en plus de `.claude/skills/design/anti-ai.md`>

## Guide pour les agents
Trois prompts de composants prêts à l'emploi, avec valeurs exactes :
1. <ex. Hero : fond `--color-canvas`, titre display 80px …>
2.
3.
