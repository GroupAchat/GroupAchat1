# Ne pas ressembler à de l'IA — interfaces

Ce qui trahit une interface générée, et ce que font les vraies marques à la place.
Les chiffres viennent des tokens des 69 marques de `brands-design-md` (voir `brands-index.md`).

## Le principe
Une interface « IA » est la **moyenne** de toutes les interfaces : rien n'y est faux, rien n'y est choisi.
Une vraie marque prend **2 ou 3 décisions fortes** et s'y tient partout (Slack : boutons à 4px, cartes à 16px,
dégradé sur un seul mot ; Notion : fond papier, aucune ombre sur les cartes, une seule couleur d'action).
Avant d'écrire une ligne, nommer ces décisions dans `design/DESIGN.md`. Si on ne peut pas les nommer, le résultat sera générique.

## Typographie — le signal le plus visible
| Signe IA | Ce que font les marques |
|---|---|
| Inter partout, une seule famille | 18 marques sur 69 utilisent Inter, et presque toujours avec une police de titre à côté. Médiane : 2 familles (titre + texte, parfois une mono). |
| Titres en gras 700, interligne 1.2–1.5 | Titre display médian : 64px (56–81px), interligne médian **1.05** (51 marques ≤ 1.1). Graisse 400–500 dans 32 marques sur 69 : la taille fait la hiérarchie, pas le gras. |
| Approche par défaut (0) | 41 marques sur 69 resserrent les titres : −1 % à −3 % de la taille (Vercel −5 %, Notion −4,8 %). Les petites capitales et étiquettes, elles, s'écartent (+2 à +6 %). |
| 5 graisses mélangées | 2 ou 3 graisses dans 41 marques. |
| Paragraphes en police de titre | Police de titre réservée aux titres et chiffres clés. |

Polices libres qui ont du caractère (à préférer à Inter seul) : titres — Instrument Serif, Fraunces, Bricolage Grotesque,
Space Grotesk, Syne, DM Serif Display, Archivo (variantes étroites), Familjen Grotesk ; texte — Geist, IBM Plex Sans,
Manrope, Public Sans, Figtree ; mono — JetBrains Mono, Geist Mono, IBM Plex Mono. Ne jamais reprendre une police propriétaire
d'une marque (Söhne, Cal Sans UI, SF Pro…) : prendre le substitut libre indiqué dans son DESIGN.md.

## Couleur
| Signe IA | Ce que font les marques |
|---|---|
| Dégradé violet → bleu (ou rose) sur le hero, les boutons, le texte | Les dégradés existent (24 marques) mais à **un seul endroit** : Stripe, une trame dans le tiers haut ; Slack, un mot du titre. Jamais sur les boutons ni les cartes. |
| Blanc pur `#ffffff` + noir pur `#000000` | Fond souvent légèrement teinté : `#faf9f5`, `#f7f7f4`, `#f6f5f4`, `#fffaf0`, `#eeefe9`, `#f5f1ec`. Texte presque noir et teinté : `#1d1d1f`, `#141413`, `#26251e`, `#201515`. |
| Une couleur d'accent sur tout (liens, badges, icônes, boutons) | Une seule couleur pour l'action principale par écran ; le reste en neutres. Beaucoup de marques ont un accent… noir. |
| Palette « tailwind par défaut » (indigo-500, slate) | Des couleurs nommées et situées : orange `#f54e00`, vert `#9fe870`, jaune `#faff69`, rouge `#ea2804`. Une couleur inattendue mais assumée vaut mieux qu'un indigo sûr. |

## Formes, profondeur, mise en page
| Signe IA | Ce que font les marques |
|---|---|
| `rounded-2xl` + `shadow-lg` sur chaque carte | Médiane des ombres déclarées : **0**. Profondeur par filets 1px (`rgba(0,0,0,.08)`) et changement de surface. L'ombre est réservée à ce qui flotte (menu, modale, capture produit). |
| Même rayon pour tout | Rayons choisis par rôle et contrastés : Slack 4px boutons / 16px cartes ; Notion 8px / 12px ; Caldera 40px partout ; Wired et Bugatti 0. Répartition du rayon max : 0–4px (6), 5–12px (21), 13–24px (26), >24px (16) : il n'y a pas de bon rayon, il y a un rayon assumé. |
| Verre dépoli, halos flous, blobs | Aplats. Le flou n'apparaît que sur une barre de navigation au-dessus de contenu. |
| Hero centré : pastille « ✨ Nouveau », titre, sous-titre, 2 boutons, 3 cartes à icône | Hero avec un vrai objet : une capture du produit, un fragment d'interface réel (Cal.com montre un calendrier de réservation), une photo, une donnée. Grilles asymétriques, alternance pleine largeur / colonne. |
| Sections toutes de même hauteur et même rythme | Rythme varié : une bande sombre isolée, une section très dense, une très aérée. |
| Icônes en emoji ou icône dans un carré coloré arrondi | Une seule famille d'icônes au trait (Lucide, Phosphor, Tabler), même épaisseur, ou pas d'icône du tout. |

## Contenu et texte
- Jamais de lorem ipsum ni de « John Doe » : contenu réel du projet (noms togolais, prix en FCFA, quartiers de Lomé, vrais horaires).
- Interdits dans les titres : « Révolutionnez », « Boostez », « Libérez le potentiel », « en quelques clics », « sans effort »,
  « tout-en-un », « nouvelle génération », et en anglais « Unlock », « Supercharge », « Seamless », « Elevate », « Effortless ».
- Un titre dit **ce que fait le produit pour qui**, avec un verbe concret : « Réservez une table à Lomé sans appeler » plutôt que « La restauration réinventée ».
- Les chiffres sont vrais ou absents : pas de « 10 000+ utilisateurs satisfaits » inventés, pas de faux témoignages.

## Mouvement
- Une seule animation d'entrée calme (≤ 300 ms), pas de fondu sur chaque section au défilement.
- Survol : changement de couleur ou de fond en 150–200 ms, pas de `scale-105` partout.
- `prefers-reduced-motion` respecté.

## Test final (à passer avant de livrer)
1. Masquer le logo : reconnaît-on quand même le produit ? Sinon, les 2–3 décisions fortes manquent.
2. Compter les couleurs vives visibles à l'écran : plus de 2 → trop.
3. Compter les ombres : chaque ombre doit correspondre à un élément qui flotte.
4. Lire les titres à voix haute : s'ils pourraient être sur le site d'un concurrent, les réécrire.
5. Lancer `python3 .claude/skills/design/scripts/design-lint.py` : zéro alerte bloquante.
