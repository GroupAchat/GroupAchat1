# Ne pas ressembler à de l'IA — images

Claude ne génère pas d'images matricielles lui-même. Il écrit les **prompts** pour un générateur
(Midjourney, Flux, Ideogram, Seedance pour la vidéo…), produit des **illustrations SVG** quand le vectoriel convient,
et décide **quand une vraie photo vaut mieux qu'une image générée**.

## D'abord : faut-il générer ?
- Produit, plat, lieu, personne réelle de l'entreprise : **vraie photo** (même au téléphone, bien cadrée). Une image générée d'un plat qu'on vend est un mensonge visible.
- Fond, ambiance, illustration de concept, visuel de campagne : génération possible.
- Pictogramme, schéma, motif, illustration à plat : **SVG** écrit à la main, aux couleurs des tokens.

## Ce qui trahit une image générée
| Signe | Correction dans le prompt |
|---|---|
| Peau lisse, plastique, pores absents | « visible skin texture, pores, natural imperfections, unretouched » |
| Lumière parfaite de studio partout, contre-jour doré | lumière précise et située : « harsh midday sun in Lomé, hard shadows », « fluorescent kitchen light », « overcast » |
| Composition centrée et symétrique, sujet face caméra | « off-center subject, candid, caught mid-action, partially cropped » |
| Étalonnage orange / bleu, saturation forte | « muted natural colors », ou une pellicule précise : « Kodak Portra 400 », « Fujifilm Superia » |
| Flou d'arrière-plan extrême (bokeh) systématique | profondeur de champ réaliste : « f/5.6, background slightly soft but readable » |
| Décor générique « appartement scandinave », personnes génériques | lieu précis et local : « small maquis in Bè, Lomé, plastic chairs, hand-painted menu board » |
| Mains, texte, logos déformés | éviter les mains en gros plan et tout texte dans l'image ; le texte s'ajoute ensuite en HTML |
| Rendu 3D brillant, blobs, verre, néon violet | si 3D : « matte clay render, soft studio light, limited palette of #xxxxxx and #yyyyyy » |
| Tout est propre et neuf | « slightly worn, lived-in, everyday clutter » |

## Construire un prompt photo
Ordre : **sujet et action → lieu précis → moment et lumière → cadrage et optique → support → couleurs de la marque → exclusions**.
```
Woman in her 40s arranging attiéké and grilled fish on a plate, small family restaurant in Tokoin, Lomé,
late afternoon light through a side window, hard shadows, shot from slightly above at 35mm, f/4,
candid, partially cropped, Kodak Portra 400, muted natural colors with warm orange accents (#f54e00),
visible skin texture, unretouched
--no studio lighting, bokeh, symmetry, text, logo, 3D render
```
- Mentionner les couleurs de `design/DESIGN.md` (accent, fond) pour que l'image appartienne au site.
- Toujours écrire le prompt en anglais (meilleurs résultats), le commentaire pour David en français.
- Donner 3 variantes : même scène, cadrages différents (large, moyen, détail).
- Prévoir le format final : 16:9 hero, 4:5 réseaux sociaux, 1:1 carte.

## Illustrations et SVG
- Un seul style d'illustration par projet, décrit dans `design/DESIGN.md` (trait, épaisseur, couleurs, remplissage).
- Couleurs uniquement issues des tokens ; 2 ou 3 au maximum par illustration.
- Formes un peu irrégulières plutôt que des cercles parfaits ; pas de dégradés.
- Jamais de personnage connu, de mascotte d'une marque ni de logo existant.

## Vidéo (Seedance et autres)
- Un seul mouvement de caméra par plan (« slow push-in », « static tripod »), durée courte.
- Mêmes règles de lumière, de lieu et de texture que pour la photo.
- Pas de texte dans la vidéo générée : titres ajoutés au montage.
