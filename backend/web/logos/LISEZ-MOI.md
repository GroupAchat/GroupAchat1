# Déposez vos logos ici

Ce dossier est servi **tel quel** par Vite. Un fichier déposé à
`public/logos/marque.svg` est accessible à `/logos/marque.svg`.

**Remplacez un fichier par le vôtre en gardant exactement le même nom, et le
logo change partout dans l'application** — aucune ligne de code à toucher,
aucune reconstruction. Rafraîchissez la page, au besoin en forçant le vidage
du cache (Ctrl+Maj+R).

## Les fichiers attendus

| Fichier | Obligatoire | Où il s'affiche |
|---|---|---|
| `logo-horizontal.svg` | **oui** | Barre du haut sur écran large, écrans d'inscription et de connexion |
| `marque.svg` | **oui** | Barre du haut sur téléphone, favicon de l'onglet, pastilles |
| `logo-horizontal-blanc.svg` | non | Mêmes usages que l'horizontal, mais sur fond coloré ou sombre |
| `logo-complet.svg` | non | Réservé à une page de présentation |

Les deux variantes facultatives peuvent manquer : le code retombe alors sur
la version en couleur plutôt que d'afficher une image cassée.

## Ce que chaque fichier doit respecter

**Le format.** Le SVG est préférable : il reste net sur tous les écrans et
pèse quelques kilo-octets. Si vous n'avez qu'un PNG, déposez-le en haute
résolution (au moins 1 000 px de large, fond transparent) et **corrigez
l'extension dans [`src/composants/logos.ts`](../../src/composants/logos.ts)** —
c'est le seul fichier du code à modifier, les chemins y sont tous rassemblés.

**Les proportions.** L'horizontal s'affiche à une hauteur de 30 à 34 pixels ;
sa largeur suit. La marque seule s'affiche dans un carré : son dessin doit
donc tenir dans un carré, sans marge blanche superflue autour — une marge
intégrée au fichier le ferait paraître plus petit que prévu.

**Le fond.** Transparent, dans tous les cas. Un fond blanc intégré au fichier
se verrait comme un rectangle sur les bannières colorées et en thème sombre.

**Les métadonnées.** Les SVG exportés par certains outils embarquent un bloc
de signature (C2PA) qui pèse souvent plus lourd que le dessin lui-même. Ce
n'est pas bloquant, mais le retirer allège la page.

## Les couleurs de la marque

Elles sont reprises dans tout le système de design
([`src/index.css`](../../src/index.css)) :

| | Code | Usage |
|---|---|---|
| Bleu marine | `#1E3A8A` | Espace groupeur, administration |
| Orange mangue | `#FF6A00` | Espace acheteur, visiteurs |

Si vos fichiers utilisent des teintes légèrement différentes, dites-le :
c'est `--color-marine-800` et `--color-mangue-500` qu'il faut aligner, et
toute l'interface suit.
