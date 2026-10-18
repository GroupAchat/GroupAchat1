# Group Achat — fonctionnalités et contenu des écrans pour Figma

> Accompagne le [cahier des charges](CAHIER_DES_CHARGES.md). Version : 3.0 — deux chromes : acheteur orange, groupeur bleu
> Objet : ce qu'il y a **dans** chaque écran — textes réels, données réelles, états réels.

**Comment lire ce document.** Les textes entre guillemets se recopient tels quels. Les chiffres viennent du jeu de données du §3 : n'en invente pas d'autres, la cohérence d'un écran à l'autre est ce qui fait croire à une démonstration.

**Une règle avant tout le reste :** aucun faux texte. Pas de *Lorem ipsum*, pas de « Produit 1 ». Un jury regarde le contenu avant la mise en page.

---

## 1. Fondations

### 1.0 Principes de design

Trois exigences : **fond blanc**, **moderne et épuré**, **expérience simple**. Comme « moderne » et « épuré » ne se vérifient pas, voici les règles concrètes qui les produisent. Ce sont elles qu'on contrôle, pas l'impression générale.

#### Le fond est blanc

**`#FFFFFF` partout.** Il n'y a pas de fond gris dans cette application.

Cela supprime d'un coup le moyen le plus courant de séparer les blocs — une carte blanche sur un fond gris. Il faut donc séparer autrement, et c'est précisément ce qui rend un design épuré :

| Au lieu de | On utilise |
|---|---|
| Un fond gris derrière des cartes blanches | **Le vide** : 24 à 32 px entre deux sections |
| Une bordure complète autour d'un bloc | Un **filet de 1 px** sous l'élément, sur toute la largeur moins les marges |
| Une ombre portée pour détacher une carte | Rien. Un bloc n'a pas besoin de flotter pour exister |
| Un bloc dans un bloc | **Un seul niveau** : on aplatit |

**Une seule exception à l'absence d'ombre :** les éléments qui flottent réellement au-dessus du contenu — le bouton ancré en bas, la feuille de connexion, le bouton flottant du groupeur. Une ombre très légère, et uniquement là.

**Une seule nuance de gris est tolérée**, le jeton `surface-douce` (§1.2), et seulement pour les trois cas listés dans le tableau des couleurs. Si tu te retrouves à en vouloir une quatrième, c'est que la hiérarchie se joue ailleurs.

#### Épuré : sept règles

1. **Un seul bouton primaire par écran.** Tout le reste est secondaire ou textuel. Si deux actions se disputent le bouton primaire, c'est qu'il faut deux écrans.
2. **Une couleur dominante par côté, et elle dépend du rôle** (§1.2) : orange côté acheteur, bleu côté groupeur. Dans les deux cas, une seule couleur porte l'action ; la seconde devient un signal rare. Le vert est réservé à une livraison réussie, le rouge à un problème. Aucun aplat « pour décorer » : une couleur signale une action, un état ou un risque, jamais un ornement.
3. **Pas de dégradé**, sauf le voile sur les médias du fil — où il sert à rendre le texte lisible, pas à faire joli.
4. **Un rayon de coin par famille** : 12 pour les blocs et les médias, 10 pour les boutons et les champs, 999 pour les pastilles. Jamais trois valeurs différentes sur un même écran.
5. **Icônes en traits de 1,5 px**, jamais pleines, jamais multicolores.
6. **Deux niveaux de hiérarchie visibles par bloc**, pas trois. Un titre et un corps ; si un troisième niveau s'impose, le bloc fait trop de choses.
7. **Aucun élément purement décoratif.** Pas d'illustration de remplissage, pas de motif de fond, pas de séparateur ornemental. Dans cette application, tout pixel sert à informer, à rassurer ou à agir.

#### Simple : six règles

1. **Une décision par écran.** L'écran de commande choisit une quantité et une adresse ; il ne vend rien d'autre, ne propose rien d'autre.
2. **Le bouton principal est toujours au même endroit** — ancré en bas, pleine largeur. L'utilisateur ne le cherche jamais.
3. **Il dit ce qu'il fait, avec le montant** : « Payer 4 000 F », pas « Continuer ». Jamais « OK » ni « Valider » seul.
4. **Cinq champs visibles au maximum.** Au-delà, on découpe en étapes (c'est pourquoi l'écran 14 en a trois).
5. **Aucun menu caché.** Tout ce qui compte est dans la barre de navigation à **cinq** onglets. Pas de tiroir latéral, pas de menu à trois points qui cache une action importante.
6. **Le retour est toujours possible et ne détruit rien.** Une seule exception assumée : après un paiement, on ne revient pas.

#### Trois questions auxquelles chaque écran doit répondre

Avant de déclarer un écran fini, vérifie qu'on peut y répondre en une seconde, sans faire défiler :

> **Où suis-je ? Que puis-je faire ici ? Combien ça coûte ?**

Si la troisième question n'a pas de réponse sur un écran qui en implique une, l'écran n'est pas fini.

#### Le fil est l'exception

L'écran 1 est le seul écran sombre de l'application : du média plein cadre, du texte blanc sur un voile. Le contraste avec le reste — blanc, aéré, orange — est volontaire et doit être net. **C'est le seul endroit où l'on sort du fond blanc**, et il est préférable que cette rupture soit franche plutôt qu'adoucie par des demi-teintes.

Attention sur le fil : le texte blanc posé sur un voile sombre est autorisé parce que c'est le **voile** qui porte le contraste, pas l'orange. Un bouton `marque` à texte blanc y reste interdit comme ailleurs — le bouton « Commander » du fil est en `primaire` `#CC4A00`.

#### Mode sombre

Non traité dans le MVP. Les couleurs étant définies en variables Figma (§1.2), la correspondance pourra être ajoutée plus tard sans redessiner. Décision : **À définir**

### 1.1 Cadre et grille

| Élément | Valeur |
|---|---|
| Frame Figma | **390 × 844** |
| Marge latérale | **16 px**, jamais entamée — sauf le fil (§4), qui est à bord perdu |
| Grille d'espacement | multiples de 4 : 4, 8, 12, 16, 24, 32, 48 |
| Entre deux sections | **24 px minimum**, 32 px pour une rupture forte — c'est le vide qui remplace les fonds gris (§1.0) |
| Entre deux éléments d'un même bloc | 12 px |
| Filet de séparation | 1 px `bordure`, sur la largeur moins les marges, **jamais bord à bord** |
| Zone tactile minimale | **48 × 48 px** |
| Barre de navigation | 72 px en bas |
| Bandeau partenaires | **72 px**, en haut du fil, sous l'en-tête (§2.14) |

Prévois aussi une **frame de présentation** : le téléphone centré sur fond neutre, pour la projection devant le jury.

#### Les trois largeurs

Le téléphone reste la référence — on dessine à 390 px et on monte. Mais l'application s'adapte au-delà, et chaque palier change l'**architecture**, pas seulement la mise en page :

| Largeur | Côté acheteur | Côté groupeur |
|---|---|---|
| **< 768 px** | Le fil plein écran, barre de navigation en bas, colonne de 430 px | Colonne de 430 px, barre de navigation en bas |
| **768 à 1023 px** | Le catalogue en grille à 2 colonnes, filtres en puces | Colonne latérale bleue, contenu large |
| **≥ 1024 px** | Catalogue en grille (3 puis 4 puis 5 colonnes), **filtres en tiroir**, fiche sur 2 colonnes, **page bornée à 1 600 px** | Colonne latérale bleue, contenu borné à 1 180 px |

> ⚠️ **Cette ligne annonçait une « colonne de filtres latérale ».** Elle n'existe pas, et elle n'est pas prévue : `TiroirFiltres` glisse par la droite à **toutes** les largeurs. Une colonne permanente demanderait une seconde implémentation du même panneau — ce que la règle juste en dessous interdit — et mangerait, sur une page bornée à 1 600 px, la largeur d'une colonne de résultats. Voir l'écran 2.

⚠️ **Aucun écran n'est dédoublé.** Ce sont les mêmes composants dans les trois cas ; seules la largeur et la navigation changent. Écrire une version bureau séparée doublerait le travail à chaque correction, et les deux divergeraient en quelques semaines.

#### ⚠️ Une seule largeur de page, et elle s'appelle `largeur-page`

Côté acheteur, **l'en-tête, le pied de page et tous les écrans partagent le même plafond et la même gouttière** : la classe `largeur-page` de `index.css`. Plafond **1 600 px**, gouttière qui grandit avec l'écran (16 px, 32 px à partir de 1 024, 48 px à partir de 1 536).

C'est une correction, et le défaut vaut d'être raconté parce qu'il se reproduira sinon. Les largeurs avaient été posées écran par écran : l'en-tête et le pied allaient **d'un bord à l'autre**, le catalogue aussi — on lui avait retiré son plafond exprès — mais la fiche produit, les commandes, les demandes et le profil restaient dans une colonne centrée de **1 280 px**. Sur un écran de 1 920, passer du catalogue à une fiche faisait donc **sauter toute la page** : le contenu rentrait de 320 px de chaque côté pendant que l'en-tête, lui, restait collé aux bords. Les deux ne se sont jamais alignés.

**Pourquoi 1 600 et pas 1 280.** À 1 280, un écran de 1 920 laisse 320 px de vide de chaque côté — c'est exactement ce qui avait fait retirer le plafond du catalogue, et à raison. À 1 600, le même écran laisse 160 px, ce qui se lit comme une marge et non comme un trou. Et un écran de 2 560 cesse d'étaler une barre de recherche sur deux mètres.

**Ce qui doit toucher les bords se pose en dehors du conteneur** et met son propre contenu dedans : la bannière partenaires, un lavis de fond. Une image qui touche les bords est une image ; une image avec 48 px de blanc autour est une vignette.

**À l'intérieur du plafond, trois mesures restent bornées**, parce qu'un conteneur large ne veut pas dire un contenu large :

| Bloc | Mesure | Pourquoi |
|---|---|---|
| Colonnes de texte de la fiche | 672 px | Au-delà d'environ 70 caractères, l'œil ne retrouve plus le début de la ligne suivante |
| Bloc d'achat de la fiche | 576 px | Sans plafond il recevait 880 px, et un bouton « Commander » large comme une table ne se lit plus comme un bouton |
| Formulaires | 672 px | Un champ de 1 000 px ne se remplit pas mieux, il se lit moins bien |

⚠️ **Les paliers de colonnes se calent sur le conteneur, pas sur l'écran.** La grille du catalogue passait à cinq colonnes à 1 800 px alors que le conteneur s'arrête à 1 600 : la cinquième colonne ne gagnait aucune place, elle **rétrécissait les cartes** de 376 à 300 px. Des vignettes qui maigrissent quand l'écran grandit sont l'inverse de ce qu'on attend. Le dernier palier tombe donc là où le conteneur cesse de croître.

Le côté groupeur garde ses propres largeurs — 760 px à une colonne, 1 180 px à deux — parce que ses écrans sont des outils de gestion et non un catalogue.

### 1.2 Couleurs

**L'orange domine. Le bleu reste, mais sur un seul rôle.** Les deux couleurs de marque sont conservées ; ce qui change, c'est leur répartition.

#### Deux chromes, un seul système

L'application sert **deux publics qui ne font pas la même chose** : l'acheteur fait ses courses, le groupeur gère son affaire. Chacun a sa couleur dominante, et le chrome dit immédiatement de quel côté on se trouve.

| | **Côté acheteur** — écrans 1 à 12 | **Côté groupeur** — écrans 13 à 21 |
|---|---|---|
| **Dominante** | **Orange** `#CC4A00` | **Bleu** `#1E3A8A` |
| Aplats, en-tête, cartes de chiffres | Orange | Bleu |
| Rôle de la seconde couleur | Le bleu = **la garantie**, et rien d'autre | L'orange = **le repère et l'urgence** |
| Où la seconde apparaît | Bandeau de confiance, statuts « argent détenu » | Onglet actif, liseré de l'en-tête, compte à rebours, « à faire aujourd'hui », bouton flottant |

**La règle de dominance tient dans les deux cas :** c'est le bleu qui porte les aplats côté groupeur, l'orange qui les ponctue. On sait donc toujours d'un coup d'œil de quel côté on se trouve — et c'est cela, et non la rareté de l'orange, qui distingue les deux chromes.

⚠️ **L'orange côté groupeur ne se limite plus à l'alerte.** Il marque aussi l'onglet actif et souligne l'en-tête : un espace professionnel entièrement bleu est exact mais morne, et la marque doit rester lisible des deux côtés de l'application. Ce qui reste interdit, c'est **l'inversion** — un chrome groupeur à dominante orange le rendrait indiscernable de la boutique.

**Les contrastes, calculés et non estimés :**

| Usage | Rapport | Verdict |
|---|---|---|
| `primaire` `#CC4A00` sur blanc | 4,62:1 | texte autorisé |
| `marque` `#FF6A00` sur `confiance` | 3,61:1 | **aplats pleins seulement** |
| `marque` avec texte blanc | 2,87:1 | **interdit partout** |

D'où le détail du chrome groupeur : le libellé de l'onglet actif est en `primaire` sur blanc, jamais en `marque` ; le liseré de l'en-tête est une **bande pleine**, pas du texte ; et dans la colonne latérale bleue, l'onglet actif est un aplat blanc à texte `primaire` — un libellé orange posé sur le bleu tomberait à 3,61:1, ce qui ne passe pas pour du texte.

#### Pourquoi ce renversement fonctionne

Côté acheteur, le bleu gagne à être rare : une couleur qui ne sert qu'à dire « vous êtes livré ou remboursé » dit cette chose beaucoup plus fort qu'une couleur employée partout.

Côté groupeur, **l'orange change de métier**. Il n'est plus la couleur de l'action — c'est le bleu qui la porte — mais celle du repère et de l'urgence : où je suis dans la navigation, et ce qui presse. Les écrans du groupeur sont pleins de choses qui pressent : « décidez sous 41 h », « déposez le reçu avant le 9 octobre », « 3 questions sans réponse ». Posé sur un fond bleu plutôt que dans un chrome orange, il continue de se voir.

Le bleu a aussi un avantage mesurable comme couleur d'action : **10,36:1** avec du texte blanc, contre 4,62:1 pour l'orange. Les écrans du groupeur, qui portent des chiffres et des décisions sur de l'argent, y gagnent en lisibilité.

#### Le coût de ce choix, dit franchement

Deux chromes, c'est une application qui a deux visages. Il faut l'assumer : la cohérence de marque ne vient plus de la couleur, elle vient du reste — la typographie, le fond blanc, les rayons, le ton des textes, et le logo. **Garde donc tout le reste strictement identique entre les deux côtés.** Si les deux chromes divergent aussi sur les formes et les espacements, ce ne sont plus deux faces d'un produit, ce sont deux produits.

#### Le conflit à résoudre : les statuts côté groupeur

`Statut` utilise le bleu pour « argent détenu ». Sur un écran groupeur au chrome bleu, cette pastille se fond dans le décor et ne signale plus rien.

**Règle :** sur les écrans groupeur, les statuts « argent détenu » passent en **neutre** (`texte-secondaire` sur `surface-douce`). Ce n'est pas une perte : du point de vue du groupeur, ces états ne disent pas « votre argent est protégé » mais simplement « ce participant a payé » — une information factuelle, pas une promesse. Le composant `Statut` porte donc un axe `Rôle`.

#### Comment t'y prendre dans Figma

Deux voies, et la première te fera gagner beaucoup de temps si ton plan le permet :

| Voie | Principe | Condition |
|---|---|---|
| **Deux modes de variables** *(le plus simple)* | La collection `Couleur` reçoit deux modes, `Acheteur` et `Groupeur`. Le jeton `primaire` pointe sur l'orange dans l'un, sur le bleu dans l'autre. **Un écran change de chrome en changeant de mode** — aucun composant à dupliquer | Les modes multiples exigent un plan **Figma Professional** |
| **Un axe `Rôle` sur les composants** | `Bouton`, `BarreNav`, `Statut` et `Encart` reçoivent une variante `Rôle=Acheteur` / `Rôle=Groupeur` | Fonctionne sur le plan gratuit, mais double le nombre de variantes et se maintient à la main |

**Décide-le avant de construire tes composants** : refaire ce choix après coup demande de repasser sur chacun d'eux.

#### Le problème que l'orange pose, et sa solution

`#FF6A00` ne contraste qu'à **2,87:1** avec le blanc, là où il en faut 4,5. Un bouton `#FF6A00` à texte blanc est **illisible**, et il l'est d'autant plus sur l'écran bon marché et en plein soleil de l'utilisateur visé au §5 du cahier des charges.

D'où **deux oranges, deux rôles** — c'est ce que font tous les systèmes construits sur une couleur chaude :

| Jeton | Hex | Rôle | Règle absolue |
|---|---|---|---|
| **`marque`** | **`#FF6A00`** | L'orange qu'on **voit**. Aplats, logo, remplissage des compteurs, bouton flottant, indicateur d'onglet | **Uniquement avec du texte ou une icône sombre** (`#1D1916`, 6,08:1). Jamais de blanc dessus |
| **`primaire`** | **`#CC4A00`** | L'orange qui **se lit**. Boutons pleins, liens, texte orange, états actifs | Texte blanc dessus : **4,62:1** ✅. En texte sur blanc : **4,62:1** ✅ |

Même orange perçu, deux valeurs.

#### La palette complète

| Jeton | Hex | Usage |
|---|---|---|
| `marque` | **`#FF6A00`** | Aplats orange vif — avec du sombre dessus uniquement |
| `primaire` | **`#CC4A00`** | **Tous les boutons pleins**, liens, texte orange, états actifs |
| `primaire-presse` | `#A64200` | État pressé des boutons (6,18:1) |
| `primaire-fond` | `#FFF1E6` | Fonds d'encarts orange : délais, compteurs, avertissements |
| `primaire-texte-sur-fond` | `#B34A00` | Texte sur `primaire-fond` (4,87:1) — `primaire` n'y passe qu'à 4,17:1 |
| **`confiance`** | **`#1E3A8A`** | Le bleu. **Côté acheteur :** la garantie seule — bandeau, bouclier, statuts « argent détenu ». **Côté groupeur :** la couleur dominante — boutons, liens, onglet actif |
| `confiance-presse` | `#152C68` | État pressé des boutons groupeur (13,19:1) |
| `confiance-fond` | `#E8EDF8` | Fond du bandeau de confiance, et fonds d'encarts côté groupeur |
| `succes` | `#0B6B52` | Livrée, paiement confirmé, position enregistrée |
| `succes-fond` | `#E6F4EC` | Fond des confirmations |
| `danger` | `#C0392B` | Erreurs, annulation, litige, refus |
| `danger-fond` | `#FBEAE8` | Fond des erreurs |
| `texte` | `#1D1916` | Texte principal — et texte sur `marque` (17,5:1 sur blanc) |
| `texte-secondaire` | `#5C544D` | Texte courant secondaire (**7,5:1** sur blanc) |
| `texte-mention` | `#7A7066` | Mentions et horodatages (4,9:1 sur blanc) — **jamais un paragraphe** |
| `bordure` | `#EBE8E5` | Filets de séparation, contours de champs |
| **`fond`** | **`#FFFFFF`** | **Fond de tous les écrans** (§1.0) |
| `surface` | `#FFFFFF` | Identique à `fond` : un seul niveau de surface |
| `surface-douce` | `#FAF8F7` | La seule nuance de gris, dans ses trois usages du §1.0 |
| `voile` | `#000000` à 45 % | Dégradé sur les médias du fil |

> **Les neutres sont chauds, et ce n'est pas un détail d'esthète.** Ils étaient
> auparavant bleutés — `#14181F`, `#5A6472`, `#E4E7EC`, `#F7F8FA`, tous entre
> **215° et 220°** de teinte. Or la marque acheteur est à **22-26°**, et ces
> quatre jetons portent **85 % des pixels** d'un écran. L'ensemble lisait donc
> froid, et l'orange y était posé comme un corps étranger.
>
> Les valeurs actuelles tournent la teinte à **28°** à saturation très basse :
> ce sont des gris chauds, pas des beiges. **La clarté n'a pas bougé**, donc
> aucun contraste ne se dégrade — `texte-secondaire` y gagne même, de 6,0:1 à
> 7,5:1. Et le bleu du chrome groupeur s'y pose sans heurt : `confiance` tient
> **9,8:1** sur `surface-douce`.

#### Côté acheteur — où le bleu a le droit d'apparaître

La liste est courte et exhaustive. Partout ailleurs, c'est de l'orange.

| Emplacement | Écrans |
|---|---|
| ~~`BandeauConfiance`~~ | **Supprimé** — voir §1.7 |
| Statuts « Payée — en attente de clôture » et « Campagne clôturée » | 8, 9 |
| `Encart` `info` | information neutre |
| L'icône bouclier | avec le bandeau |

**Sur les écrans acheteur : pas de bouton bleu, pas de lien bleu, pas d'onglet actif bleu.**

#### Côté groupeur — où l'orange a le droit d'apparaître

Symétrique, et tout aussi court.

| Emplacement | Écrans |
|---|---|
| `CompteurTemps` et tout compte à rebours | 15, 16, 17 |
| La section « À faire aujourd'hui » | 13 |
| Le bouton flottant « + Créer une campagne » | 13 |
| `Encart` `attention` — délais, reçu à déposer | 16, 17 |

**Sur les écrans groupeur : pas de bouton orange, pas d'onglet actif orange.** L'orange n'y est jamais une action, toujours une alerte.

Attention à un contraste : **l'orange sur un aplat bleu ne tient qu'à 3,61:1** — acceptable pour un gros caractère ou une pastille pleine, insuffisant pour du texte courant. Un badge orange sur une carte bleue, oui ; du texte orange sur fond bleu, non.

#### Contrastes vérifiés

| Combinaison | Ratio |
|---|---|
| Blanc sur `primaire` `#CC4A00` | **4,62:1** ✅ |
| `primaire` en texte sur blanc | **4,62:1** ✅ |
| Blanc sur `primaire-presse` `#A64200` | 6,18:1 ✅ |
| `#1D1916` sur `marque` `#FF6A00` | 6,08:1 ✅ |
| Blanc sur `marque` `#FF6A00` | **2,87:1** ❌ **interdit** |
| `primaire-texte-sur-fond` sur `primaire-fond` | 4,87:1 ✅ |
| Blanc sur `confiance` `#1E3A8A` | 10,36:1 ✅ |
| `confiance` sur `confiance-fond` | 8,83:1 ✅ |
| `succes` sur `succes-fond` | 5,72:1 ✅ |
| `danger` sur `danger-fond` | 4,67:1 ✅ |
| `texte-secondaire` sur blanc | 6,0:1 ✅ |

Si tu modifies une teinte, **refais ce calcul**. C'est lui qui a dicté la structure de cette palette.

#### Les statuts

La couleur se lit sans lire. C'est le bleu qui dit « Group Achat tient votre argent », et l'orange qui dit « ça avance » :

| Famille | Couleur | Statuts |
|---|---|---|
| **Argent détenu** | `confiance` sur `confiance-fond` | Payée — en attente de clôture · Campagne clôturée |
| **En mouvement** | `primaire-texte-sur-fond` sur `primaire-fond` | Commande en cours chez le groupeur |
| **En cours maintenant** | `marque` plein, texte `#1D1916` | En cours de livraison |
| **Terminé** | `succes` sur `succes-fond` | Livrée |
| **Problème** | `danger` sur `danger-fond` | Litige · Campagne annulée |
| **Clos sans suite** | `texte-secondaire` sur `surface-douce` | Remboursée |

### 1.3 Typographie

**Inter**, ou Roboto pour un rendu plus fidèle sur Android.

| Style | Taille / graisse | Usage |
|---|---|---|
| `Titre-ecran` | 24 / Semibold | Titre en haut d'écran |
| `Titre-fil` | 20 / Bold | Nom du produit dans le fil, en blanc sur média |
| `Titre-section` | 18 / Semibold | Titres de blocs |
| `Prix` | 22 / Bold | Prix et montants |
| `Corps` | 16 / Regular | Texte courant — **plancher absolu** |
| `Corps-fort` | 16 / Semibold | Valeurs importantes |
| `Libelle` | 14 / Medium | Libellés de champs |
| `Petit` | 12 / Regular | Mentions, horodatages |
| `Code` | 32 / Bold, interlettrage +4 | Le code de livraison, uniquement |

Jamais de texte sous 12 px. Sur les médias du fil, tout texte blanc est posé sur un dégradé `voile`, sans quoi il devient illisible sur une photo claire.

### 1.4 Rédaction

- **Vouvoiement** partout.
- **Montants :** `4 000 F` — espace comme séparateur de milliers, `F` et non `FCFA` ni `XOF`.
- **Dates :** `sam. 11 oct.` en liste, `samedi 11 octobre` en détail. Les délais en relatif : « Plus que 2 jours ».
- **Vocabulaire :** une **campagne** (pas un « groupage » ni un « deal »), un **groupeur**, **commander une part**, **livraison**. Jamais *séquestre*, *escrow*, *transaction* à l'écran.
- **Ne jamais nommer le groupeur autrement que par son pseudonyme.**

### 1.5 Règle d'accès : aucun mur à l'entrée

> **À la première ouverture, l'utilisateur arrive directement sur le fil. Le compte n'est demandé qu'au moment où il engage quelque chose.**

Deux choses à ne jamais dessiner : **écran « Connexion / Inscription » au lancement** et **tutoriel bloquant**.

⚠️ **La liste en comptait trois** : s'y ajoutait la **pop-up « créez un compte »**. Il en existe une désormais — le message qui précède l'inscription — et ce qui la sauve de l'interdit tient à trois choses, qui sont des conditions, pas des commentaires. Si l'une saute, elle redevient le mur que ce paragraphe interdit :

- **elle ne vient jamais à l'ouverture**, seulement sur une opération ;
- **elle dit pourquoi**, et la raison change selon l'opération : « votre code de livraison et le suivi de votre colis » pour un groupage, « c'est par là que la réponse du groupeur vous revient » pour une question. « Pour sécuriser nos services » ne répond à rien ;
- **elle se ferme sans rien casser** — croix, Échap, voile — et l'opération reprend après l'inscription.

| Libre, sans compte | Exige un compte |
|---|---|
| Faire défiler le fil, chercher, filtrer | **Rejoindre** un groupage |
| Ouvrir une campagne, voir prix et délai | **Envoyer** une demande de produit |
| Lire les questions et réponses | **Poser** une question |
| Choisir sa quantité, saisir son adresse | Suivre ses commandes et ses demandes |

**Le déclencheur est le bouton « Commander » de l'écran 3**, qui ouvre l'écran 5. Le contrôle au paiement **reste** malgré tout, et pas par prudence décorative : une session expire, et elle peut expirer entre l'écran 5 et le clic sur « Payer ». Sans lui, le paiement partirait sans jeton et échouerait en 401 devant quelqu'un qui n'aurait aucun moyen de comprendre pourquoi.

⚠️ **Ce paragraphe disait : « Le déclencheur est le bouton Payer de l'écran 5, pas avant. Choisir une quantité n'engage rien ; payer engage. »** L'utilisateur a déplacé la porte d'un écran. L'argument n'était pas faux et le coût est réel — voir §10.4 bis du cahier des charges, qui le chiffre.

**La connexion est une feuille remontante, pas une page.** Elle monte par-dessus l'écran en cours, qui reste visible derrière sous un voile sombre. L'utilisateur voit qu'il n'a pas quitté son parcours ; fermer la feuille le ramène à son écran **intact** ; après le code, la feuille redescend et **l'action reprend seule**.

**Ce qui doit survivre à la connexion :** la campagne, la quantité, **l'adresse de livraison saisie**, le contenu du formulaire de demande, la position dans le fil.

**L'inscription est classique, et distincte de la connexion.** Un formulaire — **prénom, numéro obligatoire, courriel facultatif** — puis une vérification du numéro par code SMS. Deux étapes, un indicateur de progression.

⚠️ **Le formulaire a porté un mot de passe et sa confirmation, et ne les porte plus.** Ils ont été retirés du parcours d'achat : chaque champ posé devant quelqu'un qui s'apprête à payer est un acheteur perdu. Le mot de passe reste **posable depuis l'écran de profil**, pour qui veut se reconnecter sans attendre de SMS.

⚠️ **Ce paragraphe disait : « Pas d'inscription distincte. Numéro, puis code SMS. Si le numéro est inconnu, le compte se crée. Ne dessine jamais deux boutons Se connecter et Créer un compte. »** L'utilisateur a tranché pour l'inscription classique, et **les deux boutons sont donc désormais permis** — c'est ce que « classique » veut dire. Ce que la règle protégeait tient autrement, et il faut le tenir : **l'inscription est en bouton plein, la connexion en lien discret.** Quelqu'un qui ne sait pas s'il a déjà un compte suit le bouton plein, et le formulaire le renvoie vers la connexion si son numéro est déjà pris.

**La vérification du numéro par SMS reste**, et ce n'est pas une étape de trop : le numéro *est* l'identifiant du compte, et c'est par lui que partent les notifications de livraison. Sans preuve, n'importe qui s'inscrit sur le numéro d'un voisin et reçoit à sa place l'annonce que son colis est arrivé.

**Les onglets protégés n'affichent pas un mur.** Un visiteur qui touche « Mes commandes » voit :

> 📦 **Vos commandes apparaîtront ici**
> Commandez une part dans une campagne pour suivre votre livraison.
> **[ Voir les campagnes ]** · *J'ai déjà un compte — me connecter*

À décliner pour **Mes commandes**, **Mes demandes** et **Profil**.

⚠️ **L'onglet Profil fait exception depuis l'inscription classique** : son action est « **Créer mon compte** », pas « Voir les campagnes ». L'ancienne formulation — *« votre compte se crée au moment de payer »* — décrivait un parcours qui n'existe plus, et envoyer au catalogue quelqu'un qui vient de demander un compte serait un détour.

### 1.6 Le fil vidéo — contrainte technique à intégrer dès la maquette

Le fil en défilement plein écran est le cœur de l'expérience **et le point de vigilance du projet** : c'est l'écran le plus coûteux en données, destiné au public le plus sensible au coût des données. Un fil qui vide un forfait fait désinstaller l'application, quelle que soit la qualité du reste.

Six règles à matérialiser dans la maquette :

1. **Une image d'abord, toujours.** Chaque campagne a une image de couverture qui s'affiche immédiatement. La vidéo se charge par-dessus une fois prête — jamais d'écran vide pendant le chargement.
2. **Le son coupé par défaut**, avec une icône de son bien visible et touchable. Un son qui démarre seul dans un taxi fait fermer l'application.
3. **Une seule vidéo préchargée à l'avance**, pas trois.
4. **Un mode « économie de données »** dans le profil : images seulement, aucune vidéo automatique. À dessiner, c'est un argument produit sur ce marché.
5. **Les vidéos sont courtes et verticales** : 9:16, 15 secondes maximum, et le prix est lisible sans le son.
6. **Un état de secours** : si le média ne charge pas, la carte reste utilisable avec l'image, le titre, le prix et le bouton.
7. **Le bandeau partenaires se charge en dernier**, après le média de la campagne. Ce sont des **images fixes uniquement, jamais de vidéo publicitaire**, et en mode économie de données les logos cèdent la place à du texte (§2.14). Une publicité ne doit pas retarder l'affichage du contenu que l'utilisateur est venu voir.

À prévoir aussi côté maquette : les campagnes de produits qui se filment mal (un carton, un sachet) auront **une photo, pas une vidéo**. Le fil doit être aussi convaincant avec une photo fixe qu'avec une vidéo — sinon les groupeurs sans moyens de tournage sont désavantagés sans raison.

### 1.7 Anonymat des deux côtés

**L'anonymat va dans les deux sens, et c'est le second sens qui protège le modèle.**

#### Le groupeur, vu de l'acheteur

**Il n'existe aucune page de profil de groupeur, et aucun moyen de le joindre.**

| Visible | Jamais visible |
|---|---|
| Un **pseudonyme** : « Mama Gro » | Nom, photo, quartier, date d'inscription |
| Qu'il répond aux questions | Téléphone, WhatsApp, e-mail, réseaux |
| — | Ses autres campagnes, toute fiche le concernant |

**Le pseudonyme n'est cliquable nulle part.** C'est une étiquette, pas un lien.

#### L'acheteur, vu du groupeur

Symétrique, et tout aussi strict. Le groupeur gère une campagne, pas un carnet d'adresses.

| Visible pour le groupeur | Jamais visible |
|---|---|
| Le **nombre** de parts et de participants | Les noms des acheteurs |
| La **répartition par quartier** (écran 15) | Les téléphones, les adresses précises |
| Les **questions** posées, sous pseudonyme | Qui a commandé quoi, et combien de fois |
| Les **codes de livraison** sur son bordereau de colisage | — |

C'est cette moitié-là qui ferme la fuite réelle. Un groupeur qui connaît les gros acheteurs et leurs numéros peut leur proposer la même marchandise hors plateforme, au même prix, et sans nous. **L'étiquette de colis est le dernier endroit par où cette information pouvait s'échapper** : elle ne porte donc qu'un code, un quartier et un produit. Les identités ne sortent qu'à l'enlèvement, vers le transporteur — voir [LIVRAISON.md §4](LIVRAISON.md) étapes 2 et 3.

Appliqué : l'écran 15 liste les commandes **par code de livraison**, pas par nom. L'écran 22 — la page du livreur — est le seul endroit du produit où nom, adresse et téléphone apparaissent ensemble.

Ce qui porte la confiance à la place, et qui doit être visible sur le fil comme sur le détail, c'est la **promesse de plateforme** :

> 🛡️ **Vous êtes livré, ou remboursé.**

⚠️ **« Groupeurs vérifiés / sélectionnés par Group Achat » a été retiré du produit**, partout. La promesse tient maintenant en une ligne, et c'est un progrès : « vous êtes livré, ou remboursé » est un **engagement vérifiable**, là où « groupeurs sélectionnés » demandait de nous croire sur parole. Le bandeau garde son bouclier, son bleu et sa place.

C'est le seul signal de confiance de l'application : il doit être présent, court, et répété.

**Un point de rédaction qui n'est pas négociable.** Le groupeur peut retirer son argent **dès la clôture du groupage, avant la livraison** (§10.1 du cahier des charges). Il ne faut donc **jamais** écrire « votre argent est bloqué jusqu'à la livraison » ni « le groupeur ne sera payé qu'après votre livraison » : ce serait faux.

Ce qui est vrai, et qui suffit :

| ✅ À écrire | ❌ À ne jamais écrire |
|---|---|
| « Vous êtes livré, ou remboursé » | « Votre argent est bloqué jusqu'à la livraison » |
| « Vous êtes livré, ou remboursé » | « Groupeurs vérifiés / sélectionnés par Group Achat », « Le groupeur n'est payé qu'après votre livraison » |
| « Si le groupage n'aboutit pas, vous êtes remboursé intégralement » | « Votre paiement est protégé jusqu'à la remise » |
| « Votre paiement est détenu **jusqu'à la clôture** » | « …jusqu'à la livraison » |

⚠️ **Deux formulations s'ajoutent depuis le passage au portefeuille du groupeur** (§9 du cahier des charges) :

| ✅ À écrire | ❌ À ne jamais écrire |
|---|---|
| « Group Achat retient **1 500 F par groupage abouti** » | « 5 % de commission », « notre commission » |
| « Votre solde est **détenu jusqu'à la clôture**, puis retirable » | « Nous vous versons votre argent à la clôture » |

Le premier est une question d'exactitude : il n'y a plus de pourcentage, et un écran qui en affiche un est faux. Le second est plus subtil, et c'est pour ça qu'il mérite sa ligne — **nous ne versons plus rien**. L'argent est au groupeur depuis le paiement de ses acheteurs ; nous tenons son compte et nous exécutons ses retraits. Écrire « nous vous versons » laisserait croire que nous pourrions ne pas le faire.

Sur un produit dont l'argument est la sécurité de l'argent, une promesse inexacte sur le circuit de l'argent est la faute la plus coûteuse possible. La garantie réelle est un **engagement de Group Achat** — et c'est déjà un argument fort, qui n'a pas besoin d'être exagéré.

**Filtre anti-contournement :** à la publication d'une question ou d'une réponse, les numéros de téléphone et identifiants de réseaux sociaux sont masqués, avec le message « Les échanges de numéros ne sont pas autorisés. Votre paiement n'est protégé que sur Group Achat. »

### 1.8 Inventaire des médias — ce que tu dois fournir

Tous les emplacements d'image et de vidéo de l'application, avec leur taille. **En attendant tes visuels, chaque emplacement est un bloc `surface-douce` portant sa dimension écrite dessus** — l'échange sera alors immédiat, sans rien redessiner.

#### Les emplacements

| # | Écran | Emplacement | Affiché | À fournir | Format |
|---|---|---|---|---|---|
| M1 | 1 — fil | **Média de campagne** | 390 × 600 | **1080 × 1920** | Photo verticale **ou** vidéo |
| M2 | 3 — détail | Média principal | 390 × 488 | **1170 × 1464** (4:5) | Photo, jusqu'à 3 |
| M3 | 2, 8, 15 | Vignette carrée | 96 × 96 | **288 × 288** | Photo recadrée au carré |
| M4 | 5, 9, 10 | Petite vignette | 64 × 64 et 48 × 48 | Reprise de M3 | — |
| M5 | 1 — bandeau | **Logo d'annonceur** | 40 × 40 | **120 × 120** | PNG à fond transparent |
| M6 | partout | **Logo Group Achat** | 28 de haut en en-tête | Icône **84 × 84**, icône d'application **1024 × 1024**, logotype horizontal | SVG de préférence |
| M7 | 17 | Exemple de reçu fournisseur | pleine largeur | 1 photo, même approximative | Photo de reçu |

#### Ce qui ne demande aucun visuel

- **Les icônes** — jeu en traits de 1,5 px, que je produis dans Figma.
- **Le QR code** de l'écran 9 — généré par le code.
- **Les états vides** — pas d'illustration, c'est la règle 7 du §1.0.
- **Les dépôts de l'utilisateur** — photos de demande (écran 11), photos de produit du groupeur (écran 14), justificatifs (écran 17) : ce sont des zones de dépôt, pas des visuels à fournir.

#### La zone de sécurité du fil — le point à ne pas rater

Sur l'écran 1, le média fait 600 px de haut mais **les 280 px du bas sont recouverts** par le bloc d'information et le bouton, et les 40 px du haut par le dégradé. Il reste donc **280 px réellement dégagés, dans la partie haute**.

```
  ┌──────────────────────┐  ← haut du média
  │ ░░░ dégradé 40 px ░░░│
  │                      │
  │    ZONE DÉGAGÉE      │  ← le produit doit être ICI
  │       280 px         │
  │                      │
  ├──────────────────────┤
  │ compteur, titre,     │
  │ prix, bouton         │  ← 280 px recouverts
  │                      │
  └──────────────────────┘
```

**Conséquence pour tes photos et tes vidéos :** cadre le produit dans le **tiers supérieur**, pas au centre. Une belle photo centrée aura son sujet masqué par le prix et le bouton — c'est l'erreur classique sur ce type de fil, et elle ne se voit qu'au montage.

#### Les vidéos

- **Verticales 9:16**, 1080 × 1920.
- **15 secondes maximum** (§1.6).
- **Compréhensibles sans le son**, qui est coupé par défaut. Si la vidéo a besoin d'une voix pour être comprise, elle ne sert à rien ici.
- MP4, H.264. **Visez moins de 3 Mo** : c'est l'écran le plus coûteux en données de l'application, pour le public le plus sensible à ce coût.
- Filmées au téléphone, c'est très bien. Ce fil n'attend pas des films publicitaires.

#### La liste de courses minimale pour la démonstration

Pour que les cinq campagnes du §3 tiennent à l'écran :

| Besoin | Quantité |
|---|---|
| Photo verticale 1080 × 1920 | **5** — une par campagne (C1 à C5) |
| Photo carrée 288 × 288 | **5** — recadrages des précédentes |
| Vidéo verticale de 15 s | **2** — pour C2 (robe wax) et C4 (baskets), les deux campagnes où le mouvement vend |
| Logo d'annonceur | **2 à 4** |
| Logo Group Achat | **1** jeu |
| Photo de reçu | **1** |

Dépose-les dans [medias/](medias/) en suivant la convention de nommage qui y est décrite.

---

### 1.9 Le lien d'un groupage, et le partage

**Un groupage a une adresse : `?groupage={id}`.** Ouvrir cette adresse affiche la fiche du groupage (écran 3), directement.

⚠️ **Cette adresse est ce qui rend les boutons « Partager » utilisables.** Quatre étaient dessinés — sur le fil, sur la fiche, dans la gestion de campagne — et aucun ne faisait rien. Ce n'était pas une négligence d'implémentation : il n'y avait **rien à partager**, puisque l'application ne savait pas ouvrir une fiche depuis une adresse. Un lien collé dans WhatsApp ramenait sur le catalogue.

⚠️ **Et c'est la moitié manquante d'une règle non négociable.** « Un groupage clôturé quitte le catalogue, mais **sa fiche reste atteignable par son lien** » : le filtre serveur était bien en place — `retrieve` répond encore sur un groupage fermé, `list` seul filtre — mais **personne ne pouvait fabriquer ce lien**. La règle n'existait qu'à moitié, la moitié serveur.

**Ce que fait le bouton, selon l'appareil**

| | |
|---|---|
| Téléphone | La feuille de partage du système, qui ouvre WhatsApp — c'est là que se partage réellement un bon plan à Lomé |
| Ordinateur | Le lien va dans le presse-papier, et **l'écran dit « Lien copié »** |

⚠️ **Le retour à l'écran n'est pas décoratif.** Une copie est invisible : sans message, le bouton se comporte exactement comme les boutons morts qu'on vient de brancher — on clique, rien ne bouge, on reclique. Fermer la feuille de partage, en revanche, **n'est pas un échec** : on ne reproche pas à quelqu'un d'avoir changé d'avis.

**Un lien de fiche saute l'écran de choix de profil.** C'est le cas où le §1.5 est le plus impératif : on arrive d'une conversation, sur un produit précis, souvent pour la première fois. Demander « voulez-vous acheter ou devenir groupeur ? » devant un produit qu'on vient de nous recommander est exactement le mur que ce paragraphe interdit. Le profil **n'est pas retenu** pour autant : personne n'a choisi, donc rien n'a été décidé.

**Le texte partagé dit ce qu'on partage**, pas « regarde ça » : le destinataire reçoit souvent le lien seul. Le prix y figure, parce que c'est lui qui décide d'ouvrir ou non. ⚠️ Pas de prix barré, pas de « au lieu de » — la règle vaut aussi dans un message WhatsApp, qui est pourtant l'endroit où la tentation est la plus forte.

---

### 1.10 La cloche de l'acheteur, et ce qui la remplit

**La cloche était dessinée dans les deux en-têtes acheteur, pastille comprise, et ne faisait rien.** Le compteur était la constante `1` écrite dans le routeur — à sept endroits. Elle annonçait donc en permanence une notification non lue, pour une notification qui n'existait pas. Une pastille qui mentit est pire qu'une cloche absente : on finit par ne plus la regarder.

#### ⚠️ Ce n'est pas une messagerie, et c'est la règle qui tient tout le reste

**C'est la plateforme qui écrit, toujours.** Le groupeur peut *déclencher* une notification ; il n'en rédige jamais le texte. Trois conséquences, dans cet ordre d'importance :

| | |
|---|---|
| **Pas de messagerie privée** | Un champ libre du groupeur vers ses acheteurs serait une messagerie, quel que soit le nom qu'on lui donne |
| **L'anonymat tient** | Le groupeur ne sait pas à qui part la notification. La réponse ne lui rend qu'un **compte** |
| **Rien à modérer** | Il n'y a pas de texte libre, donc pas de filtre du §15 à brancher sur un envoi groupé — ce qui est justement le filtre qu'on oublie |

Il n'y a donc **aucun champ de réponse** dans le panneau : il n'y a personne à qui répondre. Une question se pose sur la fiche du produit, en public (§1.7), et c'est là que mène la notification de réponse.

#### Les quatre natures, et d'où chacune vient

| Nature | Déclenchée par | Mène à |
|---|---|---|
| **Groupage clôturé** | La clôture elle-même — bouton du groupeur **ou** date échue | Sa commande |
| **Votre commande est arrivée** | Le groupeur, écran 15 | Sa commande |
| **Réponse à votre question** | La réponse du groupeur, écran 20 | La fiche du produit |
| **Groupage annulé — vous êtes remboursé** | L'annulation, écran 16 | Sa commande |

**Chacune mène à ce dont elle parle.** Une cloche dont les lignes ne sont pas cliquables est une cloche qu'on lit une fois : on y apprend que le groupage est clôturé, puis on doit retrouver sa commande à la main. La commande d'abord quand la notification en désigne une — c'est là que vivent le suivi et le **code de livraison**, donc ce qu'on cherche après « votre commande est arrivée ».

⚠️ **Elles passent par l'API, pas par le catalogue déjà chargé.** Une notification parle presque toujours d'un groupage **clôturé** — c'est la clôture qui la déclenche — et le catalogue ne sert que de l'ouvert. Le chercher en mémoire échouerait donc dans le cas le plus courant.

#### Ce que le texte ne doit pas dire

⚠️ **Le corps est figé à l'envoi**, côté serveur, et **jamais reformaté à l'affichage**. Une notification décrit un événement daté : « vos 5 000 F vous ont été remboursés » doit continuer à dire 5 000 F si le prix de la part change ensuite. Les formulations vivent toutes dans `notifications_acheteur.py`, pour qu'on puisse les relire d'un coup.

Deux formulations interdites, qui s'ajoutent au tableau du §1.7 :

| On écrit | Jamais |
|---|---|
| « Group Achat garantit votre livraison » *(après la clôture)* | « Votre argent est bloqué jusqu'à la livraison » — à la clôture, le groupeur a déjà été payé |
| « Votre livraison est en préparation » | « Livraison demain », ou toute date : le groupeur sait que le produit est chez lui, pas quand la tournée passera (§6) |

#### Le panneau

Même mécanique que le panneau des questions (écran 10) : **feuille basse sur téléphone, carte de 384 px dans l'angle à partir de `sm`**, pas de voile, Échap ferme. Un panneau de 384 px dans un coin de 390 px n'est pas un coin.

- **Ouvrir vaut lire.** La pastille s'éteint à l'ouverture, sans attendre le serveur — l'attendre la ferait clignoter une demi-seconde après, davantage sur un réseau lent. Les lignes gardent leur point de non-lu **dans ce panneau-ci**, pour qu'on voie d'un coup d'œil ce qu'on n'avait pas vu, et l'auront perdu à la prochaine ouverture.
- **Une seule nature en orange d'alerte** : « groupage annulé », parce que c'est la seule qui annonce quelque chose qui ne s'est pas passé comme prévu. Les quatre en orange feraient de la couleur un ornement, ce que le §1.2 interdit.

⚠️ **Aucune interrogation répétée du serveur.** On relit à l'ouverture de l'application et après un geste qui a pu en produire une. C'est une décision de produit : le §5 pose un forfait de données limité, et une cloche qui interroge toutes les trente secondes consomme toute la journée pour un événement qui arrive deux fois par semaine. Le jour où il faudra du temps réel, ce sera une **poussée du serveur**, pas une boucle dans le navigateur.

---

## 2. Composants à créer avant les écrans

### 2.1 `CarteFil` — la carte plein écran du fil
Le composant le plus important de l'application. Détaillé à l'écran 1.

### 2.2 `BarreNav`
Hauteur 72, fond blanc, **filet de 1 px en haut** et rien d'autre — pas d'ombre. Icône en traits de 1,5 px, 24 px. **Onglet actif : `primaire` côté acheteur, `confiance` côté groupeur** (§1.2). Inactif en `texte-secondaire` dans les deux cas. Variantes : une par onglet actif, par rôle — soit 8.

C'est l'élément où les deux chromes se voient le plus : la barre de navigation est permanente, et c'est elle qui dit en permanence de quel côté du produit on se trouve.
- **Acheteur :** Fil · Rechercher · Demander · Mes commandes
- **Groupeur :** Tableau de bord · Mes campagnes · Demandes · Portefeuille

**Identique, connecté ou non.** Aucun onglet grisé, aucun cadenas.

Sur le fil, la barre est posée sur le média avec un dégradé `voile` derrière elle.

### 2.3 `LigneCampagne` — version liste
Pour la recherche et les listes, à côté du fil plein écran.

**Ce n'est pas une carte.** Sur fond blanc, une carte blanche n'existe pas : c'est une **ligne**, séparée de la suivante par un filet de 1 px et par du vide. Rien ne l'encadre.

```
  [photo 96×96]   Écouteurs filaires avec micro
   coins 12       4 000 F
                  🕐 Plus que 2 jours
                  Mama Gro · 32 commandes
  ────────────────────────────────────────   ← filet 1 px, largeur moins les marges
```

Seule la photo a des coins arrondis — c'est elle qui donne sa structure à la ligne, et c'est suffisant.

Variantes : `ouverte`, `derniers-jours` (le `CompteurTemps` passe en orange, **sans liseré ni cadre**), `cloturee` (photo à 40 % d'opacité, texte en `texte-secondaire`), `annulee`.

Ce choix allège aussi le rendu : une liste de lignes défile mieux qu'une liste de cartes ombrées sur un téléphone d'entrée de gamme.

### 2.4 `CompteurTemps`

**Un badge** : fond teinté, liseré de la même famille, icône horloge, et une phrase — « **Il reste 3 jours** ». **Le temps restant est le principal élément de pression de l'application** — il n'y a ni minimum ni places limitées, donc c'est lui qui crée l'urgence.

⚠️ **C'était une puce nue, et c'est maintenant un badge.** L'état `large` était posé sur fond blanc *sans liseré* : sur une carte blanche, il n'existait pas — un texte gris parmi d'autres textes gris. L'information qui fait commander aujourd'hui plutôt que la semaine prochaine était la moins visible de la carte. Chaque état porte donc un fond et un liseré, ce qui le détache du blanc **sans ombre ni cadre gris** (le §1.0 interdit les deux).

⚠️ **Plus de capitales.** Le libellé était « RESTE 2 JOURS ». Les capitales se justifiaient quand le compteur était posé nu sur une photo ; le badge porte désormais son propre fond, donc la lisibilité vient de son contraste et non de la casse. Les capitales ne faisaient plus que durcir le ton sur un produit qui vend la confiance.

La barre de progression du §2.5 en ajoute un second, plus doux : un groupage proche de son objectif donne envie d'y entrer. ⚠️ Elle ne doit **jamais** être tournée en rareté — ce ne sont pas des places, et le §2.5 dit en entier ce qu'elle n'est pas.
Quatre états, **et les contrastes sont calculés** :

| État | Libellé | Texte sur fond | Rapport |
|---|---|---|---|
| `large` | « Il reste 6 jours » | `texte` sur `surface-douce` | 16,49:1 |
| `proche` | « Il reste 2 jours » | `primaire-texte-sur-fond` sur `primaire-fond` | 4,87:1 |
| `derniere-heure` | « Il reste 4 h » | `danger` sur `danger-fond` | 4,67:1 |
| `terminee` | « Groupage clôturé » | `texte-secondaire` sur `surface-douce` | 7,01:1 |

Le liseré reprend la couleur du texte, très transparent (`primaire/25`, `danger/30`, `bordure` pour les deux états neutres).

⚠️ Les deux plus serrés — `proche` et `derniere-heure` — ont **moins de 0,4 de marge** au-dessus de 4,5:1. Changer l'un de ces jetons oblige à refaire ce calcul, pas à l'estimer.

**Sous un jour, on compte en heures**, jamais en jours : « il reste 0 jour » ne veut rien dire, et « il reste 1 jour » pour cinq heures serait faux dans le sens qui coûte — l'acheteur remettrait sa commande au lendemain.

⚠️ **L'acheteur ne voit jamais l'état `terminee`.** Le catalogue ne sert plus que les groupages ouverts dont la date n'est pas passée (voir l'écran 2). L'état reste décrit ici parce que **le groupeur** voit les siens, clôturés compris, sur ses propres écrans.

Sur le fil, où le badge est posé sur un média sombre, il devient un aplat **`marque` avec texte `#1D1916`** (6,08:1) : c'est son usage le plus visible dans toute l'application, et celui où l'orange de la marque travaille le mieux. Le texte y est sombre, **jamais blanc** — blanc sur `marque` ne tient qu'à 2,87:1.

### 2.5 `JaugeParticipants`

**Une barre de progression vers l'objectif du groupeur**, avec le chiffre écrit à côté : « **32** sur 40 acheteurs ».

Ce composant remplace le `CompteurParticipants`, qui n'affichait qu'un nombre. La raison du changement est que **le groupeur déclare désormais combien de personnes il veut réunir** : le dénominateur existe, donc la barre est honnête. Elle apparaît sur le fil (1), les cartes et les lignes du catalogue (2), le détail (3), et sur ses propres écrans (13, « Mes campagnes »).

#### ⚠️ Les trois choses que cette barre ne dit pas

Elles ne sont pas des précautions de rédaction, ce sont des règles. L'ancienne version de ce paragraphe interdisait toute jauge, et son argument était juste : une jauge laisse croire à une limite.

| Ce n'est pas | Donc on n'écrit jamais |
|---|---|
| **Des places** — dépasser l'objectif est permis et normal | « places disponibles », « complet », « il reste 3 places » |
| **Un minimum** — un groupage à 14 sur 20 peut aboutir : à la clôture c'est le groupeur qui décide (§7 du cahier des charges) | « il manque 6 personnes pour que le groupage parte » |
| **Un déclencheur** — atteindre l'objectif ne clôture rien ; seule la date le fait | « objectif atteint, le groupage se clôture » |

#### Le dépassement

La barre **s'arrête à plein** et le nombre écrit continue de monter : « 24 acheteurs » sur un objectif de 20, avec une pastille « Objectif atteint ». Une barre qui déborderait de sa gouttière serait un défaut d'affichage ; plafonner le nombre en silence ferait disparaître une bonne nouvelle.

Une fois l'objectif passé, le dénominateur cesse d'être écrit : ce qui compte est que le but est franchi, pas de combien.

#### Le chiffre est écrit, toujours

La barre seule ne se lit pas — 60 % de quoi ? Le texte porte le sens, la barre ne fait que le rendre immédiat. C'est aussi ce qui la rend lisible aux lecteurs d'écran : `role="progressbar"`, `aria-valuenow`, `aria-valuemax`, et un `aria-label` qui reprend la phrase affichée.

#### Les couleurs

Remplissage **`marque`** (`#FF6A00`), gouttière `surface-douce`. L'orange vif n'est ici qu'un **aplat plein**, jamais du texte : blanc sur `marque` donne 2,87:1, ce qui est interdit (§1.2). La pastille « Objectif atteint » emploie donc le couple déjà calculé `primaire-texte-sur-fond` sur `primaire-fond`.

**Variante `sombre`**, pour le fil et la carte urgente, où la carte est posée sur un média foncé : texte blanc, gouttière `blanc à 25 %`, remplissage `marque` inchangé.

**Deux tailles :** `compacte` (barre de 6 px, texte `Petit`) pour une ligne de liste, `normale` (8 px) pour une carte ou le détail.

#### Le vocabulaire

« **acheteurs confirmés** », jamais « participants » ni « commandes » (§3). Le champ côté serveur s'appelle `objectif_participants`, mais c'est un nom interne : il ne sort pas à l'écran.

### 2.6 ~~`BandeauConfiance`~~ — **supprimé**, et `MENTION_LIVRAISON`

⚠️⚠️ **Ce composant n'existe plus, et cette section ne subsiste que pour
empêcher qu'on le réinvente.**

Elle le définissait en entier — *« fond `confiance-fond`, texte `confiance`,
icône bouclier, [...] c'est le seul élément bleu de l'application »* — alors
que le §2.0 et la liste de contrôle finale le donnaient déjà pour supprimé.
**Le document se contredisait**, et celui qui ouvrait cette section-ci le
réimplémentait de bonne foi.

**Pourquoi il est parti.** L'argument qui le justifiait — *« c'est précisément
parce que tout le reste est orange que ce bandeau se détache »* — est
exactement ce qui l'a condamné : il a fait école. Le bleu s'est réinstallé par
petites boîtes un peu partout sur les écrans acheteur, alors que le §1.2 le
réserve au côté groupeur. **Aucun encart bleu sur un écran acheteur.** Seule
exception, la coche « vérifié » de 13 px à côté d'un pseudonyme : c'est une
marque, pas une boîte de réassurance.

**La promesse, elle, reste.** « Livré, ou remboursé » n'a pas disparu : elle
est **en texte**, dans le flux de la page, sans boîte colorée autour. Là où un
bloc demeure nécessaire — l'écran 7 — il est **neutre**, bouclier en
`primaire` et non en `confiance`.

#### `MENTION_LIVRAISON` — la phrase qui a pris sa place

Ce n'est pas un composant mais **une constante de texte**, et elle obeit à une
règle stricte : elle vit **à un seul endroit**, `MENTION_LIVRAISON` dans
`domaine/livraison.ts`.

> Les frais de livraison se règlent directement au livreur, au moment de la
> remise.

Elle s'affiche sur les **trois écrans où l'acheteur voit un total** : commande
(écran 4), paiement (écran 5), confirmation (écran 7). En `Petit`
`texte-secondaire`, sans encart.

⚠️ **Pourquoi elle est obligatoire.** L'acheteur ne paie plus aucun frais de
livraison à Group Achat : il règle le livreur à la remise, hors plateforme. Un
total qui n'inclut pas la livraison n'est donc pas un mensonge — mais **ne pas
prévenir en serait un par omission**. Il découvrirait la dépense à sa porte,
livreur devant lui.

⚠️ **Ne recopie jamais cette phrase à la main**, ni dans le code ni dans une
maquette. Le tarif du transporteur n'a jamais été négocié ; le jour où il
existera, la phrase doit changer **une fois et partout**.

**Relis le §1.7 avant d'écrire quoi que ce soit sur l'argent** : la formulation
reste contrainte, puisque le groupeur est payé avant la livraison.

### 2.7 `Bouton`
Hauteur 52, coins 10, pleine largeur moins les marges.
**Deux axes : `Rôle` et `Style`**, parce que la couleur d'action dépend du côté (§1.2).

| Style | Côté acheteur | Côté groupeur |
|---|---|---|
| `primaire` | fond `#CC4A00`, texte blanc (4,62:1), pressé `#A64200` | fond `#1E3A8A`, texte blanc (**10,36:1**), pressé `#152C68` |
| `secondaire` | contour 1,5 px `primaire`, texte `primaire` | contour `confiance`, texte `confiance` |
| `danger-texte` | texte `danger`, sans fond | identique |
| `desactive` | fond `surface-douce`, texte `texte-secondaire` | identique |

Plus un état `chargement` pour chacune.

Le bouton groupeur est nettement plus lisible que le bouton acheteur — 10,36:1 contre 4,62:1. Ce n'est pas un hasard qu'on s'en satisfasse : ses écrans portent des décisions sur des sommes à cinq chiffres.

**Jamais `marque` `#FF6A00` en fond de bouton avec un texte blanc** : 2,87:1, illisible (§1.2). Si tu veux absolument un bouton dans l'orange vif de la marque, son texte doit être `#1D1916` — c'est lisible, mais réserve-le au bouton flottant du groupeur, pour qu'un seul élément de l'application ait ce traitement.
Les boutons principaux sont **ancrés en bas** sur fond blanc, avec une **ombre haute très légère** — le bouton ancré est l'un des trois seuls éléments de l'application autorisés à porter une ombre (§1.0), parce qu'il flotte réellement au-dessus du contenu qui défile dessous.

### 2.8 `Statut`
Hauteur 24, coins complets, texte 12 Medium.

| Statut | Couleur |
|---|---|
| Payée — en attente de clôture | `confiance` sur `confiance-fond` |
| Campagne clôturée | `confiance` sur `confiance-fond` |
| Commande en cours chez le groupeur | `primaire-texte-sur-fond` sur `primaire-fond` |
| **En cours de livraison** | **`marque` plein, texte `#1D1916`** — le seul statut en aplat vif : c'est celui qui demande de l'attention aujourd'hui |
| Livrée | `succes` sur `succes-fond` |
| Litige | `danger` sur `danger-fond` |
| Remboursée | `texte-secondaire` sur `surface-douce` |
| Campagne annulée | `danger` sur `danger-fond` |

Bleu, Group Achat tient l'argent. Orange, ça avance. Vert, c'est fait. Rouge, il y a un problème. Gris, c'est clos (§1.2).

**Axe `Rôle`.** Sur un écran groupeur au chrome bleu, une pastille bleue se fond dans le décor. Les statuts « argent détenu » y passent donc en **neutre** — `texte-secondaire` sur `surface-douce`. Du point de vue du groupeur, ces états ne promettent rien : ils constatent qu'un participant a payé.

### 2.9 `Champ`
Libellé 14 **au-dessus** du champ, jamais un simple placeholder — il disparaît à la saisie et l'utilisateur ne sait plus ce qu'il remplit. Hauteur 52, coins 10, **fond blanc avec un contour de 1 px `bordure`** : sur fond blanc, c'est le contour qui dit « ici on écrit », pas un remplissage gris.
Variantes : `vide`, `rempli`, `focus` (contour `primaire` 2 px), `erreur` (contour `danger` + message 12 dessous), `desactive` (fond `surface-douce`, l'un des trois usages autorisés du gris).

### 2.10 `CodeLivraison`
Bloc centré, fond `surface`, bordure 2 px en tirets `primaire`, coins 16. QR code 160 × 160, le code en style `Code`, et « Montrez ce code au livreur ».

### 2.11 `Encart`
Fond teinté, icône + texte, coins 12, **sans bordure ni ombre**. Sur fond blanc, un aplat de couleur douce se détache seul : y ajouter un liseré alourdit sans rien apporter.

| Variante | Fond | Texte et icône | Pour quoi |
|---|---|---|---|
| `info` | `confiance-fond` | `confiance` | Une information neutre, ou qui rassure |
| `attention` | `primaire-fond` | `primaire-texte-sur-fond` | Un délai, un compte à rebours, un avertissement |
| `succes` | `succes-fond` | `succes` | Une réussite |
| `danger` | `danger-fond` | `danger` | Une erreur, un refus, une annulation |

La répartition suit le §1.2 : le bleu informe et rassure, l'orange presse. Un encart `info` et un encart `attention` ne disent donc pas la même chose, et leur couleur le dit avant le texte.

### 2.12 `EtatVide`
**Icône en traits de 1,5 px, 48 px, en `texte-secondaire`** — pas d'illustration, pas de dessin de remplissage (§1.0, règle 7). Puis titre 18, phrase explicative 16 en `texte-secondaire`, bouton `secondaire`. Centré, avec beaucoup de vide autour : c'est le vide qui rend un état vide élégant, pas l'image qu'on y met.

À décliner : aucune commande, aucune demande, aucune campagne, aucun résultat, non connecté.

### 2.14 `BandeauPartenaires`

L'emplacement publicitaire vendu aux entreprises (§9.3 du cahier des charges). **Hauteur 72 px**, fond blanc, filet de 1 px en dessous, en haut du fil sous l'en-tête.

```
  ┌────────────────────┐ ┌────────────────────┐
  │ [logo]  Nom        │ │ [logo]  Nom        │  ← défilement horizontal
  │         Accroche   │ │         Accroche   │
  └────────────────────┘ └────────────────────┘
  Sponsorisé
```

- **Carrousel horizontal** de vignettes de 280 × 56, coins 12, 12 px entre elles. Deux à quatre annonceurs, défilement au doigt — **pas de rotation automatique** : un contenu qui bouge seul au-dessus d'un fil qu'on fait défiler est désagréable et empêche de toucher ce qu'on visait.
- Chaque vignette : logo 40 × 40 à gauche, nom de l'annonceur en `Corps-fort`, accroche d'une ligne en `Petit` `texte-secondaire`.
- **Mention « Sponsorisé »** en 10 px `texte-secondaire`, alignée à gauche sous le carrousel. Discrète mais présente — c'est une obligation de loyauté, pas une option de mise en page (§9.3).
- **Jamais de prix ni de bouton « Commander »** sur une vignette. Une publicité ne doit à aucun moment ressembler à une campagne.

**Variantes à dessiner**

| Variante | Contenu |
|---|---|
| `deux-annonceurs` | Le cas courant |
| `un-annonceur` | Une vignette pleine largeur |
| `aucun-annonceur` | **Le bandeau disparaît entièrement.** Pas de « Votre publicité ici », pas de place vide : au lancement il n'y aura pas d'annonceur, et un emplacement vide fait plus de mal qu'une absence |
| `economie-donnees` | Les logos sont remplacés par le nom de l'annonceur en texte, sur une seule ligne de 40 px |

**Au toucher**, deux comportements selon ce que l'annonceur a acheté :
- une **page interne** décrivant l'offre, avec un bouton vers l'extérieur ;
- un **lien externe**, et dans ce cas une confirmation obligatoire : « Vous quittez Group Achat » avec les boutons « Continuer » et « Annuler ».

### 2.13 `FriseEtapes`
Frise verticale à 4 ou 5 étapes : un point de 10 px et un trait vertical de 2 px entre les points. Étapes franchies en `primaire`, étape en cours en `primaire` avec un anneau, étapes à venir en `bordure`. Libellé 16 et date 12 à droite de chaque point. Pas d'encadrement autour de la frise.

Sert au suivi de commande (écran 9) et à la confirmation (écran 7).

---

## 3. Jeu de données de démonstration

Un seul jeu, utilisé sur **tous** les écrans.

**Acheteuse :** Akosua Doe — `+228 90 12 34 56` — Tokoin, rue des Cocotiers, près de la pharmacie Sodji

**Groupeurs** — pseudonymes seuls, jamais de nom réel :
**Mama Gro** · **Lomé Deals** · **Chez Sika**

| # | Produit | Prix / part | Commandes | Groupeur | Fin | Média |
|---|---|---|---|---|---|---|
| C1 | Écouteurs filaires avec micro | **4 000 F** | 32 | Mama Gro | Plus que 2 jours | Photo |
| C2 | Robe wax, taille au choix | 7 500 F | 18 | Chez Sika | Plus que 5 jours | **Vidéo** |
| C3 | Huile de palme 20 L | 11 200 F | 24 | Mama Gro | Plus que 6 jours | Photo |
| C4 | Baskets homme, pointures 39-45 | 9 800 F | 41 | Lomé Deals | **Plus que 4 h** | **Vidéo** |
| C5 | Savon de Marseille, carton de 48 | 9 500 F | 12 | Chez Sika | Clôturée | Photo |

> **Pas de colonne « prix détail », et c'est une décision de produit** — voir la règle ci-dessous.

### Le vocabulaire de l'interface — fixé sur la maquette

Les mots visibles à l'écran ne sont pas ceux des documents internes. **Ce tableau fait foi pour toute copie d'interface.**

| À l'écran | Jamais à l'écran | Pourquoi |
|---|---|---|
| **un groupage** | une campagne | C'est le mot que l'utilisateur emploie déjà. « Campagne » reste le terme interne, dans ce document et le cahier des charges |
| **32 acheteurs confirmés** | 32 commandes, 32 participants | « Confirmés » dit que ces gens ont payé. C'est rassurant, et c'est vrai |
| **4 000 F CFA** | 4 000 F | Le prix complet partout où l'utilisateur lit un montant. Le `F` seul reste admis dans les tableaux denses et côté administration |
| **Il reste 2 jours** | Plus que 2 jours, RESTE 2 JOURS | Une phrase, pas un cri. Le badge du §2.4 porte son propre fond, donc la lisibilité ne vient plus des capitales |
| **Par Mama Gro** | Vendu par, Groupeur : | Sobre, et ça ne suggère pas une fiche à ouvrir (§1.7) |
| **Voir le groupage** | Commander — 4 000 F | Sur le fil, on ouvre ; on ne s'engage pas. L'engagement est à l'écran 3 |

### Aucun prix barré, aucun badge de réduction

**Règle absolue dans toute l'application.** Un prix de part s'affiche seul. Jamais de prix de détail barré à côté, jamais de pastille « −19 % », jamais de mention « au lieu de ».

C'est contre-intuitif pour qui vient du e-commerce, et c'est pourtant le bon choix ici, pour trois raisons :

- **Le prix barré est une promesse qu'on ne peut pas tenir.** « 18 000 F au lieu de 4 000 F » suppose qu'on connaisse le prix de détail — or il varie d'un marché à l'autre à Lomé, et il est *déclaré par le groupeur*. Afficher un chiffre que personne ne vérifie dans un produit qui vend la confiance est le pire échange possible.
- **Ça déplace l'argument au mauvais endroit.** Notre promesse n'est pas « c'est soldé », c'est **le prix de gros par le groupage, avec la garantie Group Achat**. Le prix de groupe parle de lui-même : l'acheteur de Lomé sait très bien ce que coûte un écouteur au marché.
- **Ça nous expose.** Des prix barrés gonflés sont la pratique qui a ruiné la crédibilité de bien des plateformes. Ne jamais commencer coûte zéro ; arrêter plus tard coûte la confiance déjà bâtie.

**Donc, à ne dessiner nulle part :** prix barré, pastille de pourcentage, « économisez X F », compte à rebours de promotion, « prix habituel ». Ce qui reste, et qui suffit : le prix de la part, ce que contient une part, le nombre de participants et le temps restant.

**Aucun frais de livraison n'est facturé à l'acheteur.** Il paie **sa part, et rien d'autre**, et il règle la livraison **au livreur, à la remise** — hors plateforme. Group Achat n'encaisse donc rien à ce titre, et son seul revenu reste les 1 500 F par groupage abouti, à la charge du groupeur.

> ⚠️⚠️ **Ce paragraphe disait : « Frais de livraison calculés selon la position de l'acheteur, payés par lui, sur une ligne distincte [...] la fonction renvoie 1 000 F pour toute position. Dans les maquettes, affiche donc 1 000 F. »** `FRAIS_LIVRAISON_PROVISOIRES` vaut maintenant **zéro**, côté serveur comme côté client, et les récapitulatifs masquent la ligne tant qu'elle est nulle.

> ⚠️ **Cela oblige à prévenir.** Un total qui n'inclut pas la livraison n'est pas un mensonge, mais ne rien dire en serait un par omission : l'acheteur découvrirait la dépense à sa porte, livreur devant lui. D'où `MENTION_LIVRAISON` (§2.6), affichée sur les trois écrans où il voit un total.

> ⚠️ **Et le montant n'est pas connu.** Le tarif de l'agence partenaire n'a jamais été négocié — `LIVRAISON.md`, le dossier qui devait le porter, a été supprimé. **Aucun écran ne l'annonce**, pas même sous la forme d'un « à partir de ».

**La commande fil rouge :** C1, 1 part. **`4 000 F` payés — la part, et rien d'autre.** Code de livraison **`K7M-4PQ`**.

> ⚠️ **Cette ligne disait : « 4 000 F de part + 1 000 F de livraison = 5 000 F payés ».** Les frais de livraison facturés à l'acheteur ont été supprimés — le seul revenu de la plateforme est de 1 500 F par groupage abouti, à la charge du groupeur. **Le 5 000 F circule encore dans des captures et des souvenirs** : c'est 4 000 F.

#### ⚠️ Le compte de démonstration n'avait aucune commande

C'était un défaut du jeu de données, et il rendait trois écrans indémontrables. Les commandes étaient réparties sur des acheteurs générés (« Acheteur 54 ») : **le compte avec lequel on se connecte pour montrer le produit n'en possédait pas une seule.** Donc l'**écran 8** était vide, l'**écran 9** — suivi, frise, code de livraison, refus du colis — inatteignable, le code `K7M-4PQ` **n'existait pas en base**, et les notifications de commande n'avaient personne à prévenir.

Akosua Doe porte maintenant **quatre commandes**, une par état à montrer :

| État | Ce que l'écran 9 doit montrer |
|---|---|
| **Payée — en attente de clôture** | Pas de code. C'est la **détention des fonds** qui rassure |
| **En cours de livraison** | Le code `K7M-4PQ`, son QR, et le bouton « Refuser le colis » |
| **Livrée** | Frise complète, code et bouton de refus disparus |
| **Annulée** | Remboursement intégral, livraison comprise |

⚠️ **Deux écarts assumés, à connaître avant de maquetter.**

**Le code `K7M-4PQ` n'est pas sur la commande de C1**, mais sur celle qui est **en cours de livraison**. L'écran 9 n'affiche le code que pendant la livraison : posé sur une commande « payée » de C1 — qui est encore ouverte — il existerait en base et ne s'afficherait **nulle part**. On a préféré la lettre de l'écran à la lettre de ce paragraphe.

**Les commandes sont réassignées, pas ajoutées.** Les additions de cette section doivent tomber juste : un jury vérifie. Ajouter une commande à C1 ferait 33 commandes et 132 000 F au lieu de 128 000 F. On reprend donc des commandes existantes et on change leur propriétaire — les comptes restent exacts, et l'une d'elles devient simplement la sienne.

> **Attention en maquettant :** le montant que l'acheteur paie est **4 000 F** — le prix de la part, partout, du fil jusqu'au détail de la commande.
>
> ⚠️ **Ce paragraphe avertissait de l'inverse** : *« le montant que l'acheteur paie est 5 000 F, pas 4 000 F [...] c'est l'erreur la plus facile à commettre »*. Elle n'existe plus : il n'y a qu'un montant. La livraison se règle au livreur à la remise, et une mention le dit sur les écrans 5, 6 et 7.

**Portefeuille de Mama Gro** — campagne C1, 32 commandes :

| Ligne | Montant | Calcul |
|---|---|---|
| Collecté sur les parts | **128 000 F** | 32 × 4 000 |
| Frais Group Achat | **− 1 500 F** | **un montant fixe par groupage abouti**, pas un pourcentage |
| **Retirable par le groupeur à la clôture** | **126 500 F** | 128 000 − 1 500 |
| Frais de livraison collectés | 32 000 F | 32 × 1 000, **reversés au transporteur, jamais touchés** |
| Disponible sur son portefeuille | **126 500 F** | le groupage des écouteurs est clôturé, il n'a pas encore retiré |

⚠️ **Plus de pourcentage nulle part.** Le frais est de **1 500 F par groupage abouti**, retenus au moment où le groupeur retire son argent (§9.2 du cahier des charges). Un écran qui affiche « 5 % » ou « commission » est un écran à corriger.

**Le second groupage du portefeuille**, celui des baskets, sert à montrer un retrait déjà exécuté : 41 × 9 800 = 401 800 F, moins 1 500 F = **400 300 F retirés le 28 septembre**.

Les additions doivent tomber juste à l'écran : un jury vérifie ce genre de calcul.

**Quartiers :** Agoè, Bè, Tokoin, Adidogomé, Nyékonakpoè, Hédzranawoé.

---

# Lot 1 — commander et payer

## Écran 1 — Accueil, le fil des groupages

**Objectif :** qu'un visiteur comprenne en trois secondes ce qu'il regarde, et qu'il ait envie de faire défiler. C'est l'écran d'ouverture, **sans aucun compte**.

**Structure : un groupage par écran, défilement vertical.** On glisse vers le haut pour le suivant.

**De haut en bas** *(aligné sur ta maquette)*

1. **Le média à bord perdu** : photo ou vidéo 9:16 couvrant tout l'écran. Un dégradé `voile` en haut sur 120 px et en bas sur 280 px, sans quoi aucun texte n'est lisible.
2. **Une loupe**, posée sur le média — **pas un champ de recherche**. À sa
   droite, un bouton `secondaire` compact « **Demander** » → écran 11.

   Au toucher, le champ **se déplie** sur une seconde ligne, qui n'existe que
   pendant la recherche. On le referme avec une croix, et **la fermeture efface
   le filtre** : laisser une recherche active derrière une loupe repliée
   donnerait un fil mystérieusement incomplet.

   ⚠️⚠️ **Ce paragraphe disait exactement l'inverse, et avec un argument :**
   *« La recherche en clair plutôt qu'une icône, c'est un choix fort et c'est
   le bon : sur un fil vertical, rien ne dit à l'utilisateur qu'il peut
   chercher autre chose que ce qui défile. Une loupe se remarque moins qu'un
   champ. »*

   **L'utilisateur a tranché pour la loupe**, et la raison est mesurable : sur
   390 px, le champ occupait une ligne entière, en permanence, par-dessus le
   média qui est le cœur de l'écran.

   ⚠️ **Ce que ça coûte, et il faut le dire : la découvrabilité.** L'argument
   ci-dessus reste vrai — une loupe se remarque moins. C'est un coût accepté,
   pas un coût disparu.

   ⚠️ **Et c'est le seul champ de recherche de l'application** : le replier
   sans le rendre atteignable aurait purement supprimé la recherche. La loupe
   doit donc rester visible à tout moment sur le fil.

   Le code est déjà à jour : voir `acheteur/mise-en-page/EnTeteApplication.tsx`,
   qui porte la même note.

3. **Rail d'actions vertical à droite**, icônes blanches de 28, libellé 12 dessous :
   - 💬 **Questions** — « **7** » → écran 10
   - ↗️ **Partager**
   - 🔇 **Son** — coupé par défaut (§1.6), seulement si le groupage a une vidéo
4. **Bloc d'information en bas à gauche**, au-dessus de la barre de navigation :
   - `CompteurTemps` : badge « **Il reste 2 jours** »
   - **Nom du produit** en `Titre-fil` blanc : « **Écouteurs filaires Pro avec micro** »
   - **Prix** : « **4 000 F CFA** » en `Prix` blanc, **seul** — pas de prix barré, pas de pastille de pourcentage (§3). En dessous, en `Petit` : « la part »
   - « **32 acheteurs confirmés** »
   - « **Par Mama Gro** » en 14 — **non cliquable** (§1.7)
5. **Bouton ancré** au-dessus de la barre de navigation, pleine largeur : « **Voir le groupage** » → écran 3.
6. **`BarreNav`** — **cinq** onglets : **Accueil · Groupage · Demander · Commandes · Profil**. Accueil actif, posée sur un dégradé.

   > ⚠️ **Elle en comptait quatre**, sans « Demander ». Celui-ci était dans l'en-tête, en bouton orange plein — c'est-à-dire du même poids que l'action principale de l'écran. Il est descendu au **centre** de la barre : « Demander » n'est pas une consultation comme ses voisins, c'est ce qu'on fait quand le catalogue n'a pas ce qu'on cherche, et le centre le met sous le pouce juste après « Groupage ». ⚠️ **La barre du groupeur garde ses quatre onglets** — ne pas confondre les deux.
7. **Indice de défilement**, sur la première carte seulement : « **Glisser vers le haut pour le groupage suivant** », qui disparaît au premier geste. Sans lui, un utilisateur qui n'a jamais vu ce type d'interface reste bloqué sur le premier écran.

### Les deux éléments manquants de ta maquette

Ce ne sont pas des oublis de dessin, ce sont **deux décisions antérieures que la maquette abandonne**. Il faut les reprendre sciemment.

**1. Le bandeau publicitaire a disparu.** Tu l'avais demandé en haut de l'accueil. Il n'y est plus — et franchement, **c'est mieux ainsi** : je t'avais signalé qu'il coûtait 9 % de la surface principale en permanence pour l'inventaire le moins performant qui soit. Deux endroits valent mieux :

| Où | Ce que ça donne |
|---|---|
| **En tête de l'onglet Groupage** *(recommandé)* | Une liste supporte un bandeau sans rien sacrifier. L'annonceur garde sa visibilité, l'accueil garde son plein écran |
| **Carte sponsorisée dans le fil** | Plein écran, au format d'un groupage, marquée « Sponsorisé », tous les cinq ou six contenus. C'est l'inventaire qui se vend cher — et c'est plus de travail |

**2. Le bandeau de confiance a disparu aussi**, et celui-là, **il faut le remettre**. « Groupeur sélectionné · Livré ou remboursé » est la seule chose qui distingue ton produit d'un groupage WhatsApp. Sur un écran où un inconnu demande 4 000 F CFA à quelqu'un qui n'a pas de compte, le retirer coûte cher.

**Proposition qui tient dans ta maquette :** une ligne de 20 px, juste au-dessus du bouton « Voir le groupage », texte blanc 12 avec une icône de bouclier — « 🛡️ Groupeur sélectionné · Livré ou remboursé ». Pas un encart bleu, pas un bloc : une ligne. Elle coûte 20 px et elle porte toute la promesse.

### Les onglets, à définir maintenant

| Onglet | Contenu | Écran |
|---|---|---|
| **Accueil** | Le fil vertical plein écran | 1 |
| **Groupage** | La même offre en **vue liste**, avec catégories et filtres. C'est là que vont ceux qui cherchent plutôt que ceux qui flânent | 2 |
| **Commandes** | Mes commandes et leur suivi | 8 |
| **Profil** | Mes informations *(nom, numéro, **courriel**, adresse)*, **mot de passe**, mes demandes, mode économie de données, aide | 12 et réglages |

**Cartes à dessiner** — au moins trois, pour montrer la variété : **C1** (photo, 2 jours), **C2** (vidéo, robe wax), **C4** (vidéo, 4 h restantes — `CompteurTemps` en `danger`, l'urgence maximale).

**États à dessiner**

| État | Contenu |
|---|---|
| Chargement | Fond `surface-douce` avec un dégradé animé discret, sans logo ni texte |
| Image seule | La vidéo n'a pas chargé : image de couverture + toute l'information, pleinement utilisable (§1.6) |
| Mode économie de données | Un bandeau discret en haut : « Mode économie activé — vidéos désactivées » |
| Fin du fil | « Vous avez vu tous les groupages ouverts » + bouton « Demander un produit » |

**Actions :** glisser vers le haut → groupage suivant · toucher le média → pause de la vidéo · « Voir le groupage » → écran 3 · 💬 → écran 10 · recherche → écran 2 · « Demander » → écran 11.

## Écran 2 — Recherche, catégories et résultats

**Objectif :** servir ceux qui cherchent quelque chose de précis — le fil sert la découverte, pas la recherche.

### ⚠️ Le catalogue ne contient que des groupages ouverts

**Un groupage clôturé n'est plus sur la plateforme.** Ni sur le fil, ni dans les résultats, ni dans une catégorie, ni dans le compteur de résultats. La règle vaut pour tout ce qui est clôturé, livré ou annulé, et pour tout groupage dont la date est passée.

On ne peut plus le rejoindre, donc l'afficher ne fait que trois choses, toutes mauvaises : il occupe la place d'un groupage auquel on peut encore participer, il donne l'impression d'un catalogue plus fourni qu'il ne l'est, et il mène à une fiche dont le bouton est mort.

**Le filtre est côté serveur**, et ce n'est pas un détail d'implémentation : un écran qui masquerait les clôturés laisserait l'API les servir, et la recherche comme le compteur de résultats continueraient de les compter.

**Sa fiche reste accessible par son lien** (écran 3). Un acheteur qui a payé garde un chemin vers ce qu'il a acheté — le lui refuser en « page introuvable » lui ferait croire que sa commande a disparu. Il ne le trouve simplement plus en parcourant.

1. En-tête avec champ de recherche actif : « Rechercher un produit… », retour à gauche.
2. **Catégories** en puces défilantes : Alimentaire · Vêtements · Chaussures · Hygiène · Maison · Électronique.
3. **Filtres** en puces : « Se termine bientôt » · « Moins de 10 000 F » · catégorie.
4. **Tri :** fin proche · prix · nombre de commandes.
5. **Résultats** en `LigneCampagne` (§2.3 — des lignes séparées par un filet, pas des cartes), avec le compte : « 7 campagnes ».
6. `BarreNav`, onglet Rechercher actif.

**États :** recherches récentes et suggestions avant toute saisie ; chargement ; **aucun résultat** → `EtatVide` « Aucune campagne pour « lait en poudre » » + bouton « **Demander ce produit** », qui transforme un échec de recherche en demande (écran 11).

### ⚠️ Sur grand écran — une grille, et **pas** de colonne de filtres

**C'est l'écran le plus adapté aux grands formats de toute l'application**, et
cette section manquait.

Les résultats passent en grille de cartes, dont le nombre de colonnes suit le
**conteneur** :

| Largeur | Colonnes |
|---|---|
| téléphone | 2 |
| ≥ 1 024 px | 3 |
| ≥ 1 280 px | 4 |
| ≥ 1 536 px | **5**, et c'est le dernier palier |

⚠️ **Le dernier palier tombe là où le conteneur cesse de croître** (§1). La
grille passait autrefois à cinq colonnes à 1 800 px alors que la page est bornée
à 1 600 : la cinquième colonne ne gagnait aucune place, elle **rétrécissait les
cartes** de 376 à 300 px. Des vignettes qui maigrissent quand l'écran grandit
sont l'inverse de ce qu'on attend.

⚠️⚠️ **Les filtres restent un tiroir, à toutes les largeurs.** Le §1 annonçait
une « colonne de filtres latérale » à partir de 1 024 px : **elle n'existe pas**,
et cette ligne a été corrigée. `TiroirFiltres` glisse par la droite, par-dessus
la page, sur téléphone comme sur ordinateur.

Ce n'est pas un oubli à rattraper. Une colonne latérale permanente coûterait une
**seconde implémentation** du même panneau — exactement ce que le §1 interdit
quand il écrit qu'aucun écran n'est dédoublé — et elle prendrait, sur une page
bornée à 1 600 px, la largeur d'une colonne de résultats entière.

Les **puces de filtres actifs** restent visibles sous la recherche, tiroir
fermé : c'est elles qui disent ce qui est filtré, pas le tiroir.


## Écran 3 — Détail d'une campagne

**Objectif :** donner tout ce qu'il faut pour décider de payer.

### ⚠️ Sur ordinateur : la galerie à gauche, collée ; la lecture à droite

À partir de 1 024 px, la fiche se lit en deux colonnes :

| | Contenu | Comportement |
|---|---|---|
| **Gauche**, 46 % plafonné à 576 px | La galerie | **`sticky`**, à 96 px du haut — sous l'en-tête, qui en fait 80 |
| **Droite**, plafonnée à 672 px | Prix, jauge, contenu d'une part, promesse, boutons, **puis** description, caractéristiques, livraison, règles, questions | Défile |

**C'est tout l'intérêt de la colle** : on lit la description et les caractéristiques **sans perdre la photo de vue**. Le détail était auparavant posé *sous* la fiche, sur deux colonnes ; il fallait remonter pour revoir le produit dont on lisait les dimensions.

**L'ordre du document suit l'ordre visuel** : la galerie d'abord, donc à gauche. Entre 768 et 1 023 px la fiche s'empile, et la photo passe naturellement en tête — comme sur téléphone.

⚠️ Le conteneur de la rangée porte `items-start`. Sans lui, un élément de flex s'étire sur toute la hauteur de la rangée et `sticky` n'a plus de place pour glisser : il ne se passe rien, sans message et sans erreur.

### Après la fiche : « Dans la même catégorie »

Quand la colonne de lecture est finie, la galerie se décolle et une dernière section propose **jusqu'à quatre autres groupages**, en pleine largeur de page et non dans la colonne de lecture — une grille de 672 px au milieu d'une page de 1 600 aurait l'air d'un oubli.

Même catégorie d'abord, complétée par le reste du catalogue si elle n'offre pas assez : **une rangée d'une seule carte ressemble à un défaut d'affichage**. Le catalogue ne contenant que des groupages ouverts (écran 2), on ne propose jamais quelque chose qu'on ne peut plus rejoindre.

### ⚠️ Un groupage clôturé ne se commande pas

Sa fiche reste atteignable par son lien, donc ce cas arrive pour de vrai. Le bouton devient **désactivé et intitulé « Groupage clôturé »**. Il restait actif, et il menait à un paiement que le serveur refuse — l'acheteur remplissait son adresse pour rien.

1. **Galerie** pleine largeur, ratio 4:5, flèche de retour à gauche et **icône de partage à droite**. Jusqu'à **4 photos et 2 vidéos** (écran 14), la couverture en premier.

   **Les vignettes n'apparaissent qu'à partir de deux médias.** Une galerie d'un seul élément est une galerie qui ment sur ce qu'elle contient, et ses commandes ne mènent nulle part.

   **Aucune vidéo ne se charge avant qu'on appuie.** On voit l'affiche et un bouton de lecture ; la vidéo elle-même n'est demandée qu'au toucher, son coupé par défaut. Sur un forfait limité, précharger une vidéo qui ne sera pas regardée est une dépense prise à l'acheteur sans le lui demander — c'est le §1.6 et le §18.1 pris ensemble. La vignette d'une vidéo porte donc un repère de lecture **avant** le clic : on doit savoir ce qu'on déclenche.
2. **Titre :** « Écouteurs filaires avec micro »
3. **Prix :** `4 000 F` en `Prix`, seul. En dessous, en `Corps` `texte-secondaire` : « par part ». **Ni prix barré, ni pastille de réduction.**
4. **`CompteurTemps`** : « 🕐 Plus que 2 jours — se termine le 7 octobre à 23 h 59 ».
5. **`JaugeParticipants`** (§2.5) : « **32** sur 40 acheteurs », barre remplie à 80 %.
6. **Pseudonyme**, non cliquable, sans aucun autre détail : « Proposé par **Mama Gro** ».
7. **La promesse, en texte — pas en bandeau.**

   ⚠️ **Cette étape demandait un `BandeauConfiance` version `complet`, « avant
   le bouton, pas après ».** Le composant a été supprimé (§2.6) : c'était une
   boîte bleue sur un écran acheteur, ce que le §1.2 interdit.

   Rien à dessiner à la place : les règles du point 11 ci-dessous **portent
   déjà la promesse**, en liste à puces — *« Si le groupage n'aboutit pas, vous
   êtes remboursé intégralement »*. Le bandeau répétait, dans une boîte, une
   phrase qui figure dix lignes plus bas.
8. **Ce que contient une part :** « 1 écouteur filaire avec micro, garantie 3 mois », en bloc distinct — c'est la question que tout acheteur se pose en premier.
9. **Description** sur 4 lignes, avec « Voir plus ».
10. **Livraison**, en bloc distinct :
    - « Livraison à domicile par notre partenaire »
    - « Sous 3 à 5 jours après la clôture »
    - `MENTION_LIVRAISON` (§2.6) en `Petit` : « Les frais de livraison se
      règlent directement au livreur, au moment de la remise. »

      ⚠️⚠️ **Cette ligne demandait « Frais de livraison selon votre position »,
      puis « à partir de 1 000 F »**, avec un avertissement sur le danger
      d'annoncer un tarif unique. L'avertissement était juste ; il ne va plus
      assez loin. **Group Achat ne facture aucun frais de livraison**, et le
      tarif de l'agence partenaire **n'a jamais été négocié**.

      ⚠️ **N'écris donc aucun montant ici, pas même un « à partir de ».** On
      écrit qu'on ne connaît pas le prix plutôt que de l'inventer. Le jour où
      il existera, il s'écrira dans `MENTION_LIVRAISON`, **une seule fois**.
11. **Les règles**, en liste à puces :
    - « Paiement à la commande, versé au portefeuille du groupeur et retirable seulement à la clôture »
    - « Le groupeur décide à la clôture si la commande passe »
    - « **Si la campagne n'aboutit pas, vous êtes remboursée intégralement** »
    - « **Vérifiez votre commande devant le livreur** : la contestation n'est plus possible après acceptation »

    La dernière règle est à écrire exactement ainsi. Une fenêtre de contestation fermée à la livraison est acceptable si elle est annoncée ; découverte après coup, elle est vécue comme une arnaque (§12 du cahier des charges).
12. **« Questions sur cette campagne »** : les deux plus récentes avec leur réponse, puis « Voir les 7 questions » (écran 10) et un bouton `secondaire` « Poser une question ».
13. **Bouton ancré :** « Commander — 4 000 F ». **Ne demande aucun compte** : il ouvre l'écran 5.

**Bloc Partage** — à dessiner, c'est un levier de croissance. Deux entrées : l'icône sur le média, et un bouton `secondaire` sous les règles. La feuille propose **WhatsApp en premier**, puis « Copier le lien ». Message pré-rempli :

> *Écouteurs filaires avec micro à **4 000 F** la part — 32 personnes ont déjà commandé*
> *Plus que 2 jours — 32 personnes ont déjà commandé.*
> *Livré à domicile. Paiement gardé par Group Achat jusqu'à la livraison.*
> *👉 [lien]*

Le lien doit ouvrir **directement la campagne, consultable sans rien installer ni créer** (§1.5).

**États :** `cloturee` (bouton désactivé « Campagne clôturée » + « Me prévenir de la prochaine campagne sur ce produit »), `annulee` (`Encart` `danger` : « Campagne annulée — les participants ont été remboursés »).

## Écran 4 — Connexion (feuille remontante)

**Objectif :** déclenchée par le paiement, jamais par l'ouverture. Traversée en moins de 20 secondes.

**À dessiner comme une feuille**, pas comme une page : coins supérieurs arrondis 20, poignée de glissement, croix de fermeture à droite, et l'écran d'origine visible derrière sous un voile à 50 %.

**Étape A — numéro**
1. Poignée et croix — **pas de flèche de retour** : on superpose, on ne navigue pas.
2. Titre : « Votre numéro de téléphone »
3. Sous-titre : « Pour sécuriser votre commande et suivre votre livraison. »
4. Champ : `+228` figé à gauche, puis `90 12 34 56`. Clavier numérique.
5. Mention 12 px : « Nous ne communiquons jamais votre numéro au groupeur. »
6. Bouton « **Continuer** ».
7. **Rappel de contexte** : « Vous rejoignez : Écouteurs filaires avec micro — 4 000 F la part ».

⚠️ **« Continuer » et non « Recevoir mon code ».** À cet instant la feuille **ne sait pas encore** par quelle voie ce numéro entre : le serveur est interrogé d'abord — sans envoyer de SMS — et répond si ce numéro a un mot de passe. Promettre un code à quelqu'un qui verra ensuite un champ de mot de passe le ferait attendre un SMS qui n'arrive pas. C'est aussi ce qui évite un second bouton : un seul chemin, et le serveur choisit.

**Étape A bis — le mot de passe**, si le numéro en a un. Champ masqué, bouton « Se connecter », et en lien discret « **Mot de passe oublié ? Recevoir un code par SMS** ».

⚠️ **Ce lien est tout le parcours « mot de passe oublié », et il tient en une ligne.** Le code SMS ouvre le compte de tout le monde et lève le verrou des cinq échecs : personne ne reste enfermé dehors. Pas de lien à durée de vie à dessiner, pas de courriel à attendre — et le courriel est facultatif sur ce marché.

⚠️ **Ce paragraphe disait : « Aucun second bouton. Pas de Créer un compte à côté de Se connecter (§1.5). »** Voir le §1.5 : la règle a été levée par l'utilisateur, mais la hiérarchie reste — plein pour l'inscription, lien pour la connexion.

**Étape B — code**
1. Titre : « Entrez le code reçu », sous-titre « Code envoyé au +228 90 12 34 56 » + lien « Modifier ».
2. **Quatre cases** de 56 × 56, espacées de 12.
3. « Renvoyer le code dans 00:42 », grisé puis actif.
4. Validation automatique à la quatrième case — pas de bouton.

**Étape C — le nom, facultative**, pour un compte qui n'en a pas encore. Champ « Votre nom », phrase « Le livreur en a besoin pour vous remettre votre commande », bouton « Continuer », lien « Plus tard ».

⚠️ **Cette étape se terminait par : « Rien d'autre : ni e-mail, ni mot de passe. Chaque champ ajouté ici est un acheteur perdu à un écran du paiement. »** L'argument reste vrai et il est respecté — mais autrement, et c'est le point : **aucun champ n'a été ajouté à ce parcours-ci.** Le courriel et le mot de passe vivent dans la **feuille d'inscription** et dans l'**écran 12** (profil), jamais ici. Cette feuille reste celle de quelqu'un qui *a déjà* un compte.

### La feuille d'inscription — à dessiner, deux étapes

C'est l'autre moitié de l'écran 4, et elle est nouvelle. Elle s'ouvre depuis le message du §1.5, ou depuis « Créer mon compte ».

**Indicateur d'étape** en haut : deux barres de 4 px, la seconde en `bordure` tant qu'on est à la première. ⚠️ **Décoratif pour l'œil, annoncé pour un lecteur d'écran** — deux barres colorées ne disent rien à qui ne les voit pas : « Étape 1 sur 2 » en texte masqué.

**Étape 1 — le formulaire.** Médaillon rond de 56 px en `primaire-fond` avec l'icône de profil en `primaire-texte-sur-fond` (**4,87:1**, calculé), titre « Créer votre compte », sous-titre « Une minute, et c'est fait pour toutes vos commandes ». Puis cinq champs : **nom**, **numéro** (`+228` figé), **courriel (facultatif)**, **mot de passe**, **confirmation**. Bouton « Continuer », puis en lien « Vous avez déjà un compte ? Se connecter ».

⚠️ **Le médaillon n'est pas en `marque` plein** : un disque orange vif de 56 px sous un en-tête déjà orange ferait un second aplat de marque à trois centimètres du premier.

**Si le numéro est déjà pris**, un encart `primaire-fond` sous le champ : « Vous avez déjà un compte avec ce numéro » et un bouton « Se connecter plutôt ». ⚠️ **Pas un simple message d'erreur** : le champ est juste, c'est le parcours qui est le mauvais, et laisser l'erreur seule enverrait l'acheteur modifier un numéro qui est bien le sien.

**Étape 2 — la vérification.** Titre « Vérifions votre numéro », les mêmes quatre cases que l'étape B, le même compte à rebours de renvoi.

**Mention sous le mot de passe** : « Au moins 8 caractères. Votre numéro ne peut pas servir de mot de passe. »

**Après validation :** la feuille redescend, **le paiement reprend seul** (écran 6). **Si l'utilisateur ferme :** retour à l'écran 5 intact, quantité et adresse conservées.

**États :** code erroné (cases en `danger` + « Code incorrect. Il vous reste 2 essais. »), code expiré, vérification en cours.

## Écran 5 — Commander : quantité et adresse

**Objectif :** choisir une quantité, saisir une adresse, voir le total. **Aucun compte encore demandé.**

1. En-tête « Commander », retour.
2. **Rappel compact :** vignette 64, « Écouteurs filaires avec micro », « 4 000 F la part ».
3. **Sélecteur de quantité :** `−` | `1` | `+`, boutons 48 × 48, valeur en 24 Semibold.
   **Pas de plafond** : il n'y a ni places limitées ni minimum (§7 du cahier des charges). Ne dessine donc **aucune** mention « places disponibles ».
4. **Variantes du produit** si la campagne en a — pour C2, « Taille » ; pour C4, « Pointure ». En puces sélectionnables, obligatoire avant de continuer.
5. **Où livrer**, en bloc. Ce bloc vient **avant le récapitulatif**, parce que c'est lui qui détermine les frais (§11.1 du cahier des charges).

   **Deux façons d'indiquer où on est, et l'acheteur choisit.** À dessiner comme deux options côte à côte, pas comme un formulaire à remplir entièrement :

   | Option | Ce que l'acheteur voit | Pourquoi la proposer |
   |---|---|---|
   | **Partager ma position** *(mise en avant)* | Un bouton `secondaire` pleine largeur avec une icône de repère. Un appui, l'autorisation du téléphone, et c'est fait | Le plus précis, le plus rapide, et c'est ce qui aide le plus le livreur |
   | **Indiquer le nom du lieu** | Un champ de recherche : « Tokoin, Agoè, Adidogomé… », avec suggestions pendant la frappe | Pour qui refuse le GPS, n'a pas de réseau, ou commande pour quelqu'un d'autre |

   **Les deux mènent au même résultat** : une position, que la fonction de frais consomme. Ne fais pas de la seconde un rattrapage honteux — beaucoup de gens refusent le GPS, et ce doit rester un chemin normal.

   Puis, dans les deux cas :
   - « **Repère** » — texte libre, avec l'exemple « rue des Cocotiers, près de la pharmacie Sodji ». **Obligatoire même avec le GPS** : à Lomé le repère vaut plus que la coordonnée, et un livreur avec un point sur une carte mais sans repère tourne quand même.
   - « Numéro à joindre à la livraison » — pré-rempli après connexion

   **Les états à maquetter pour ce bloc**, dans cet ordre d'importance :

   | État | Affichage |
   |---|---|
   | **Rien de donné** — l'état d'arrivée | Les deux options, et le récapitulatif sans total |
   | **Position partagée** | « Position enregistrée » avec une coche `succes`, le nom du lieu reconnu, et un lien « Modifier » |
   | **Autorisation refusée** | `Encart` `info`, **jamais** `danger` — « Pas de problème : indiquez le nom du lieu ci-dessous. » Un refus de permission n'est pas une erreur |
   | **Position imprécise ou introuvable** | On garde ce que le téléphone a donné et on demande un repère plus précis. On ne bloque pas |

   > **Une règle d'anonymat à ne pas perdre ici** (§1.7) : la position précise est une donnée personnelle, et elle **ne remonte jamais au groupeur** — lui ne voit que des codes et des quartiers (écran 15). Elle ne sort qu'une fois, vers le livreur, le jour de la tournée (écran 22).
6. **Récapitulatif** — **deux lignes**, et le total est la seule valeur en
   style `Prix` :
   - 1 part × 4 000 F → `4 000 F`
   - **Total à payer** → **`4 000 F`**

   Sous le total, en `Petit` `texte-secondaire`, `MENTION_LIVRAISON` (§2.6) :

   > Les frais de livraison se règlent directement au livreur, au moment de la
   > remise.

   ⚠️⚠️ **Il n'y a plus de ligne « Livraison », et ce passage en décrivait une
   longuement.** Il demandait trois lignes, dont « Livraison à Tokoin →
   `1 000 F` », puis **deux états à maquetter** selon que la position était
   connue ou non, puis une zone non desservie. Tout cela reposait sur des
   frais facturés par Group Achat. **Il n'y en a plus** :
   `FRAIS_LIVRAISON_PROVISOIRES` vaut zéro, côté serveur comme côté client, et
   les récapitulatifs **masquent la ligne tant qu'elle est nulle**.

   Le document se contredisait d'ailleurs à trois lignes d'intervalle : il
   additionnait `4 000 F` et `1 000 F` pour un total de `4 000 F`.

   **Ce qui disparaît avec la ligne**, et c'est autant de moins à dessiner :
   l'état « total en attente de la position », le bouton désactivé tant que le
   montant est inconnu, et l'`Encart` « zone non desservie ». Le total est
   **connu dès l'ouverture de l'écran**.

   ⚠️ **Ce qui ne disparaît pas : la position est toujours demandée.** Elle ne
   sert plus à calculer un prix, elle sert au **livreur** — c'est elle qu'il
   suit le jour de la tournée (écran 22). Elle reste conservée sur la
   commande, et elle redeviendrait la base d'un calcul si les frais revenaient.

   ⚠️ **Et la règle d'anonymat tient toujours** : la position précise ne
   remonte **jamais** au groupeur, qui ne voit que des codes et des quartiers.


   **Supprimé : la variante « tarif calculé plus tard ».** Elle existait quand les frais hors de Lomé étaient à définir. Désormais le prix est **toujours connu avant le paiement** — soit la fonction renvoie un montant pour cette position, soit elle répond que la zone n'est pas desservie. Il n'y a pas de troisième cas, et c'est un progrès : **on ne demande jamais à quelqu'un de payer un total qu'on complétera plus tard.**
7. **`MENTION_LIVRAISON`**, en `Petit` `texte-secondaire`, juste sous le total.

   ⚠️ **Cette étape demandait un `BandeauConfiance` version courte** — supprimé
   (§2.6). Ce qui prend sa place n'est pas une réassurance mais un
   **avertissement**, et il est plus utile :

   > Les frais de livraison se règlent directement au livreur, au moment de la
   > remise.

   La phrase vit **à un seul endroit** dans le code — `MENTION_LIVRAISON`, dans
   `domaine/livraison.ts` — et s'affiche sur les trois écrans où l'acheteur voit
   un total : commande, paiement, confirmation. ⚠️ **Ne la recopie jamais à la
   main** : le jour où le tarif du transporteur sera connu, elle doit changer
   une fois et partout.
8. Case à cocher « J'accepte les conditions de vente » (lien). Non cochée par défaut, bouton désactivé tant qu'elle ne l'est pas.
9. **Bouton ancré : « Payer 4 000 F ».** Le montant du bouton est le total, qui est le prix de la part — la livraison n'y est pas, elle se règle au livreur.

**C'est ce bouton qui déclenche la connexion** (écran 4), et seulement si l'utilisateur n'a pas de compte. S'il en a un, il va droit à l'écran 6. **Deux variantes à prototyper depuis ce bouton.**

## Écran 6 — Paiement Mobile Money (simulé)

**Objectif :** reproduire un paiement Mobile Money avec assez de fidélité pour qu'il soit crédible, tout en disant honnêtement qu'il est simulé.

1. En-tête « Paiement », retour.
2. **Bandeau de démonstration**, `Encart` `info`, **tout en haut et à dessiner** : « **Démonstration** — aucun paiement réel n'est effectué. »

   Ne le cache pas. Notre argument est la sécurité de l'argent : nous nous jugeons d'abord sur notre franchise. Un jury qui découvre seul que le paiement est faux le prend bien plus mal que s'il l'a lu. Il disparaîtra au branchement de l'agrégateur agréé (§18.2 du cahier des charges).
3. **Montant** au centre : `4 000 F` en 32 Bold, puis « Écouteurs filaires avec micro — 1 part ». **Plus de ligne dépliable « Détail »** : il n'y a plus rien à détailler.
4. **Moyen de paiement** : deux cartes sélectionnables 100 × 80, **T-Money** et **Flooz**.
5. **Champ numéro**, pré-rempli, modifiable — le numéro de paiement peut différer du numéro du compte.
6. **Rappel :** « Votre paiement va au portefeuille du groupeur, qui ne peut le retirer qu'à la clôture du groupage. » — formulation contrainte, voir §1.7.
7. **Mention livraison :** « Les frais de livraison se règlent directement au livreur, au moment de la remise. »
7. Bouton ancré : « Confirmer le paiement ».

**États à dessiner — ce sont eux qui font la différence**

- **En attente de confirmation sur le téléphone :** superposition sombre, indicateur circulaire, « **Validez le paiement sur votre téléphone** », « Saisissez votre code Mobile Money quand il s'affiche », « Ne fermez pas cette page ». C'est l'étape réelle d'un paiement Mobile Money, et l'oublier dans la maquette la rend fausse.
- **Réussi :** passage automatique à l'écran 7.
- **Échec :** `Encart` `danger`, « Le paiement n'a pas abouti. **Aucun montant n'a été débité.** » + « Réessayer » / « Changer de moyen de paiement ». La phrase sur l'absence de débit est celle qui évite la panique.
- **Expiré :** « Vous n'avez pas validé le paiement à temps. Aucun montant n'a été débité. »
- **Campagne clôturée entre-temps :** « Cette campagne vient de se clôturer. Aucun montant n'a été débité. »

**L'écran est identique en paiement réel**, au bandeau près. L'étape « validez sur votre téléphone » n'est pas une fiction destinée à la démo : c'est le déroulement réel d'un paiement Mobile Money, et la maquette doit la montrer, sans quoi le branchement de l'agrégateur obligerait à redessiner le parcours.

## Écran 7 — Confirmation de commande

**Objectif :** l'écran qui transforme un paiement en confiance.

1. Pas de retour — on ne revient pas sur un paiement. Croix de fermeture à droite.
2. **Pastille de succès :** rond `succes-fond` 72, coche `succes` 40.
3. **Titre :** « Commande confirmée »
4. **Sous-titre :** « Vous êtes la 33ᵉ personne à commander cette campagne. »
5. **Un bloc neutre**, icône bouclier en `primaire` à gauche, texte à droite.
   **Pas de fond coloré, pas de bleu.**

   ⚠️ **Cette étape demandait un `BandeauConfiance` « en version développée, le
   plus grand de l'application »** — supprimé (§2.6). Le bloc reste, parce
   qu'ici il est justifié : c'est le moment où l'acheteur range son téléphone.
   Mais il est **neutre**, et le bouclier est orange, pas bleu.

   > **Vos 4 000 F vont au portefeuille du groupeur**
   > Il ne peut les retirer qu'à la clôture du groupage, pour commander chez le
   > fournisseur. Si celui-ci n'aboutit pas, vous êtes remboursé intégralement.
   >
   > Les frais de livraison se règlent directement au livreur, au moment de la
   > remise.

   La dernière ligne est `MENTION_LIVRAISON` (§2.6). ⚠️ **Elle est ici plus
   qu'ailleurs indispensable** : c'est le dernier écran avant qu'il repose son
   téléphone, et il doit savoir qu'une somme reste à prévoir le jour de la
   remise. Ne pas le dire serait un mensonge par omission — il découvrirait la
   dépense à sa porte, livreur devant lui.

   ⚠️ **Ne pas écrire à l'acheteur que l'argent est « versé au groupeur à la clôture ».** C'est désormais inexact — la somme est inscrite à son portefeuille dès le paiement (§9 du cahier des charges) — et surtout cette phrase ne lui dit pas ce qu'il veut savoir. Ce qui le rassure, c'est que **rien n'est retirable avant la clôture** et que l'annulation le rembourse.

   Exact et suffisant. Ne va pas au-delà : le groupeur est payé à la clôture, donc rien n'est « bloqué jusqu'à la livraison » (§1.7).
6. **`FriseEtapes`**, première étape active :
   - ✅ **Paiement reçu** — 4 000 F au portefeuille du groupeur
   - ⏳ **Clôture de la campagne** — 7 octobre
   - 📦 **Commande chez le fournisseur** — par le groupeur
   - 🛵 **Livraison à domicile** — sous 3 à 5 jours
7. **`Encart` `attention`**, à ne pas omettre : « **Vérifiez votre commande devant le livreur.** Vous pourrez refuser le colis s'il ne correspond pas, mais plus après l'avoir accepté. »
8. **Rappel de l'adresse** saisie, avec un lien « Modifier » actif tant que la campagne n'est pas clôturée.
9. Deux boutons : « Suivre ma commande » (primaire), « Voir d'autres campagnes » (secondaire).

## Écran 8 — Mes commandes

1. En-tête « Mes commandes ».
2. **Onglets :** « En cours (3) » / « Terminées (2) ».
3. **Liste**, pastille `Statut` en évidence :

| Produit | Montant | Statut |
|---|---|---|
| Écouteurs filaires avec micro — Mama Gro | 4 000 F | **En cours de livraison** — arrive demain |
| Robe wax — Chez Sika | 8 500 F | **Commande en cours chez le groupeur** |
| Huile de palme 20 L — Mama Gro | 12 200 F | **Payée — en attente de clôture** — 6 jours |
| Baskets homme — Lomé Deals | 10 800 F | **Livrée** — 28 septembre |
| Savon de Marseille — Chez Sika | 10 500 F | **Remboursée** — campagne annulée |

Les montants de cette liste sont des **totaux payés**, et chacun est **exactement le prix de la part** du §3.

> ⚠️ **Cette phrase disait : « totaux payés, livraison comprise : chacun est le prix de la part plus 1 000 F ».** L'acheteur ne paie plus aucun frais de livraison à Group Achat. Si des captures anciennes montrent des totaux supérieurs au prix de la part, elles sont périmées.

La ligne « Remboursée » est à garder : elle montre que la promesse de remboursement n'est pas qu'une phrase dans les conditions.

4. Sur la ligne « En cours de livraison », le code est accessible sans ouvrir le détail : « Votre code : **K7M-4PQ** ». C'est le geste fait debout devant le livreur.

**Deux états vides à distinguer :** non connecté → l'état pédagogique du §1.5 ; connecté sans commande → « Vous n'avez pas encore commandé » + « Voir les campagnes ».

## Écran 9 — Détail d'une commande et suivi

**Objectif :** porter le suivi et le code de livraison.

1. En-tête « Ma commande », retour.
2. **Pastille `Statut`** large.
3. **`CodeLivraison`** quand la livraison est en cours — le bloc dominant :
   - QR code 160 × 160, `K7M-4PQ` en style `Code`
   - « Montrez ce code au livreur »
   - Lien « Augmenter la luminosité » — en plein soleil, un écran sombre ne se scanne pas
4. **`FriseEtapes`** avec l'étape atteinte et les dates.
5. **Récapitulatif :** vignette, produit, 1 part, **total `4 000 F`**, et « Payée le 5 octobre ». Aucune ligne de livraison chiffrée.
6. **Adresse de livraison** et numéro joignable. **Aucun contact du groupeur** (§1.7) — ni numéro, ni bouton d'appel. À la place : « Une question ? » vers l'écran 10.
7. **`Encart` `attention`**, tant que la livraison n'est pas faite : « **Vérifiez votre commande devant le livreur.** Vous pouvez refuser le colis s'il ne correspond pas à votre commande. »
8. **Bouton « Refuser le colis »** en `danger-texte`, visible **uniquement** pendant la livraison.

**Les six états à dessiner — ils racontent tout le circuit**

| État | Ce qui change |
|---|---|
| **Payée — en attente de clôture** | Pas de code. « Votre code apparaîtra ici quand la livraison sera lancée. » Compteur : « Clôture dans 2 jours ». Mention : « Vos 4 000 F sont au portefeuille du groupeur, qui ne peut les retirer qu'à la clôture. » |
| **Campagne clôturée** | « Le groupeur confirme la commande sous 48 h. » Si la campagne est maintenue : « Le groupeur a reçu les fonds et prépare votre commande. **Group Achat garantit votre livraison.** » — exact, et c'est la garantie qui porte, pas la détention des fonds (§1.7) |
| **Commande en cours chez le groupeur** | « Le groupeur a passé commande chez son fournisseur. » |
| **En cours de livraison** | Le code est affiché. État principal ci-dessus. Bouton « Refuser le colis » actif |
| **Livrée** | Coche `succes`, « Livrée le 11 octobre ». Le code et le bouton de refus disparaissent |
| **Campagne annulée** | `Encart` `danger` : « Cette campagne n'a pas abouti. **Vos 4 000 F vous ont été remboursés le 8 octobre**, livraison comprise. » |

**Feuille « Refuser le colis »** : motif (ce n'est pas le produit commandé · produit visiblement abîmé · autre), description, photos, bouton « Refuser et signaler ». Puis : « Votre signalement est enregistré. Group Achat examine votre dossier sous 48 h et vous rembourse si le refus est justifié. »

⚠️ **Branchée sur `POST /api/commandes/{id}/refuser/`.** Le bouton était dessiné et ne faisait rien — c'est le pire endroit du produit pour un bouton mort, puisque c'est là que « vous êtes livré, ou remboursé » est mise à l'épreuve pour de vrai. Trois choses à ne pas récrire :

- **le refus ouvre un litige, il ne rembourse pas.** La commande passe à `litige` et un humain examine. Rembourser sur déclaration se paierait sur notre trésorerie à chaque refus, vrai ou non : le groupeur a déjà retiré son argent à la clôture (§10.2 du cahier des charges) ;
- **refusable pendant la livraison seulement.** Avant, il n'y a rien à refuser ; après, le code a été donné au livreur, donc c'est une réclamation après réception et non un refus de colis. Le serveur refuse les deux cas ;
- **le dépôt de photo n'est pas dessiné.** Le stockage de fichiers est reporté au déploiement sur le VPS. Un champ de dépôt qui perd les photos serait **pire que son absence** : l'acheteur croirait avoir fourni sa preuve. Le motif et la description partent ; la photo suivra avec le stockage.

Ne promets pas ici que l'argent « reste détenu » : à ce stade, le groupeur a déjà été payé. Le remboursement est un **engagement de Group Achat**, et c'est ce qu'il faut écrire.

## Écran 10 — Questions sur une campagne

**Objectif :** obtenir une information manquante sans jamais sortir de la plateforme. C'est ce qui rend l'anonymat du groupeur supportable.

### ⚠️ Sur ordinateur, c'est un panneau posé sur la page, pas un écran

Un **bouton flottant** se tient dans l'angle bas-droit de la fiche produit et suit le défilement. Un clic ouvre un panneau de 384 px **dans le même angle**, par-dessus la page.

**Pourquoi pas un écran plein.** On pose une question **parce qu'on hésite à commander**. Un écran plein remplace le produit par un formulaire, et il faut revenir en arrière pour retrouver le prix ou la photo dont on voulait parler. Le panneau laisse la fiche derrière lui.

| | Règle |
|---|---|
| **Pas de voile, `aria-modal="false"`** | Le panneau ne bloque pas la page : on doit pouvoir relire la fiche pendant qu'on écrit |
| **Échap ferme** | C'est le geste attendu de tout ce qui se pose par-dessus ; son absence se remarque surtout au clavier |
| **Le focus entre dans le panneau** | Sinon il reste sur le bouton flottant, derrière, et la première tabulation repart dans la page |
| **Le bouton disparaît** quand le panneau est ouvert | Les deux occupent le même angle |
| **Le corps défile dans le panneau** | Pas la page derrière |

⚠️ **Le panneau ne réécrit pas le formulaire** : c'est le même composant, en variante. Tout ce qui est délicat — le filtre de modération du §15, la connexion demandée au bouton et non à l'ouverture (§1.5), le refus du serveur affiché sous le champ — n'existe qu'une fois. Un panneau qui dupliquerait ce formulaire finirait par laisser passer un numéro de téléphone que l'écran, lui, bloque encore.

**Sur téléphone, l'écran plein reste.** Un panneau de 384 px dans un coin de 390 px n'est pas un coin : il couvrirait la fiche sans rien laisser voir, pour un résultat moins lisible que l'écran qui existe déjà.

1. En-tête « Questions », retour, rappel de la campagne : vignette 48 + « Écouteurs filaires avec micro ».
2. **Questions courantes d'abord**, pas le champ libre. Une rangée de pastilles tactiles à 36 px, défilables horizontalement : « Quelle marque ? » · « Quelle origine ? » · « Quand la livraison ? » · « Quelles variantes ? » · « Autre question ». Un appui envoie directement.

   **C'est une mesure de sécurité autant qu'un confort** (§14.2 du cahier des charges) : la plupart des questions légitimes n'ont alors aucun texte libre, et le texte libre redevient l'exception.

3. **Champ de question libre**, sous les pastilles : « Posez votre question sur ce produit… », 2 lignes, bouton « Envoyer ».
4. **Mention sous le champ**, 12 px : « Votre question et la réponse seront visibles par tout le monde. » À lire avant d'écrire.
5. **Liste des questions**, la plus récente en haut :
   - question en `Corps`, auteur « Akosua D. » et date en `Petit`
   - réponse en retrait de 16 px, fond `surface-douce`, coins 12, sans bordure, avec « **Mama Gro** » et la date. C'est l'un des trois seuls usages autorisés du gris (§1.2) : ici il sépare deux voix, donc il informe
   - une question sans réponse porte une pastille `En attente de réponse`

**Contenu à écrire dans la maquette** — du vrai contenu, c'est ce qui rend l'écran crédible :

| Question | Réponse |
|---|---|
| « C'est quelle marque d'écouteurs ? » — Akosua D. | « Jack 3,5 mm, micro intégré, câble de 1,2 m. Garantie 3 mois. » — Mama Gro |
| « La livraison va jusqu'à Adidogomé ? » — Yawa T. | « Oui, tout Lomé est couvert. Comptez un jour de plus pour Adidogomé. » — Mama Gro |
| « On peut prendre 2 sacs ? » — Kossi A. | « Oui, mettez 2 dans la quantité. » — Mama Gro |
| « Est-ce qu'on peut payer à la livraison ? » — Dodzi M. | *En attente de réponse* |

6. **`Encart` `attention` en bas de liste** : « N'échangez jamais de numéro de téléphone. Votre paiement n'est protégé que sur Group Achat. » À dessiner, pas à sous-entendre (§1.7).

**La connexion est demandée au bouton « Envoyer »**, pas à l'ouverture : la lecture est libre.

### Les états de modération — à dessiner

Le filtre du §14.2 du cahier des charges a besoin de ses écrans, sinon il n'existe pas. **Trois états à maquetter**, et le premier est le plus important.

**a) Message refusé — le cas courant, et le plus important à bien écrire.**

Deux choses se produisent **en même temps** : le message **n'est pas publié**, et son auteur en est averti immédiatement avec la raison. Jamais l'un sans l'autre — pas de blocage silencieux, pas de message qui part et disparaît ensuite.

Le message reste dans le champ, modifiable. Sous le champ, un `Encart` `danger` :

> **Ce message ne sera pas publié.**
> Il contient des informations qui permettraient de vous identifier. Pour votre sécurité, les échanges restent anonymes sur Group Achat.
>
> Posez votre question sur le produit — le groupeur répond ici même.

**Chaque mot de ce texte est choisi**, et c'est la copie la plus sensible du produit :

| Formulation | Pourquoi |
|---|---|
| « ne **sera** pas publié » | Au futur, parce que rien n'est encore parti. C'est un avertissement avant l'envoi, pas le constat d'un échec |
| « permettraient de **vous** identifier » | On parle de **sa** protection, pas de notre règlement. C'est la seule formulation qu'il acceptera sans se sentir soupçonné |
| « les échanges **restent anonymes** » | On rappelle une protection, on n'énonce pas une interdiction |
| **Jamais** « tentative de contournement », « interdit », « violation » | La plupart des gens qui écrivent leur numéro le font **de bonne foi**, pour être joints à la livraison. Les traiter en fraudeurs est faux et les fait fuir |

Le passage en cause est **surligné en `danger-fond`** dans le champ, pour qu'il voie exactement quoi corriger. Deux boutons : « Modifier » (primaire) et « Annuler ».

**Le signal arrive avant l'appui sur Envoyer.** Dès que la saisie déclenche la détection, le bouton « Envoyer » passe en `desactive` et l'encart apparaît. L'utilisateur n'a donc pas à échouer pour apprendre — **il voit tout de suite que ça ne passera pas**, ce qui est exactement ce qu'on veut. (Au niveau 2, le classifieur IA ne pouvant pas tourner à chaque frappe, son refus arrive à l'envoi, avec le même encart.)

**Une variante à ne pas oublier : le cas de bonne foi.** Si l'acheteur écrit son numéro parce qu'il veut être joignable, la bonne réponse n'est pas de le bloquer et de s'arrêter là — c'est de lui dire où ça va. Une ligne supplémentaire dans l'encart, affichée quand un numéro est détecté :

> *Votre numéro est déjà enregistré pour la livraison. Le livreur l'aura le jour de sa tournée.*

**À ne pas faire :** afficher le message publié avec le numéro masqué en ●●●●. Ça apprend à contourner, et ça laisse l'intention lisible de tous.

**b) En vérification** — phase 2, quand le classifieur hésite. La question apparaît dans le fil, **visible de son seul auteur**, avec une pastille `Statut` neutre « En vérification » et la mention « Votre question sera publiée après vérification. »

**c) Signalement** — une icône de drapeau discrète, en `texte-secondaire`, sur chaque message. Un appui ouvre une feuille : « Signaler ce message » avec trois motifs — *coordonnées personnelles*, *proposition de vente hors plateforme*, *contenu inapproprié*. **Pas de champ libre**, pour que la file de modération reste exploitable.

⚠️ **Branché sur `POST /api/questions/{id}/signaler/`.** L'icône n'allait nulle part, et c'est le **niveau 3 du §15** — l'humain, après publication — qui n'avait donc aucun moyen d'être saisi : un message qui passe les deux filtres automatiques et qu'un lecteur voit pourtant comme un numéro déguisé restait en ligne sans recours. La file se tient dans l'admin Django, comme le prévoit le §15.

⚠️ **Le message signalé reste publié**, et la feuille le dit : « Group Achat examine ce message. Il reste visible le temps de cet examen. » Dépublier sur signalement donnerait à n'importe qui le pouvoir de faire taire n'importe qui — il suffirait de signaler la question gênante pour l'effacer du seul canal public du produit. Ne jamais écrire « ce message a été retiré ».

⚠️ **Un signalement par personne et par question**, garanti en base. Sans cette contrainte, un seul lecteur contrarié gonfle le compteur autant qu'il veut et décide seul de ce qu'un humain regarde en premier. Un second envoi du même lecteur répond `200` et non une erreur : de son point de vue, le geste avait réussi.

**État vide :** « Aucune question pour le moment » + « Soyez le premier à poser une question ».

---

# Lot 2 — la demande crée l'offre

## Écran 11 — Demander un produit

**Objectif :** un formulaire si court qu'on le remplit en marchant. Cinq champs.

1. En-tête « Demander un produit », retour.
2. Accroche : « Dites ce que vous cherchez. Nos groupeurs le verront et pourront lancer une campagne. »
3. **Les champs :**
   - « Quel produit ? » — texte, avec suggestions à la saisie
   - « Quelle quantité ? » — texte court (« 20 litres », « 2 paires »)
   - « Votre quartier » — liste déroulante
   - « Budget maximum (facultatif) » — montant
   - « Photo ou précisions (facultatif) » — dépôt + texte
4. **`Encart` `info`** : « 32 personnes ont déjà demandé de l'huile de palme à Bè cette semaine. Votre demande rejoindra la leur. » Dynamique selon la saisie — c'est ce qui donne l'impression d'un marché vivant.
5. Bouton ancré « Envoyer ma demande ».

**La connexion n'est demandée qu'à l'envoi.** Les cinq champs se remplissent sans compte, et **tout ce qui a été saisi, photo comprise, est conservé** pendant la connexion, puis l'envoi reprend seul.

**Après envoi :** « Demande envoyée », « Nous vous prévenons dès qu'un groupeur lance une campagne », boutons « Voir mes demandes » / « Retour au fil ».

## Écran 12 — Mes demandes

1. En-tête « Mes demandes ».
2. Liste avec pastille `Statut` :

| Demande | Statut |
|---|---|
| Huile de palme, 20 L — Bè | **Campagne lancée !** — « Mama Gro a lancé une campagne » + bouton « Commander » |
| Lait en poudre, 2 kg — Tokoin | **Prise en charge** — « Un groupeur prépare une campagne » |
| Charbon, 1 sac — Tokoin | **En attente** — « 8 personnes ont demandé la même chose » |
| Ventilateur — Agoè | **Non aboutie** — « Aucun groupeur n'a pu trouver ce produit » |

La première ligne ferme la boucle du produit : une demande devient une campagne qu'on peut commander. C'est la ligne à montrer au jury. La dernière est honnête et doit exister : une demande peut ne rien donner, et l'acheteur doit l'apprendre (§8 du cahier des charges).

3. **États vides :** connecté sans demande, et non connecté (§1.5).

---

# Lot 3 — côté groupeur

## Écran 12 bis — Profil de l'acheteur

⚠️⚠️ **Cet écran existe dans le produit et n'avait aucune section ici.** Il
était cité quatre fois en passant — l'onglet de la `BarreNav`, le mot de passe
« posable depuis l'écran de profil », le mode économie de données — sans jamais
être décrit. C'est pourtant **la mise en page bureau la plus élaborée du côté
acheteur**.

**Objectif :** tout ce qui concerne le compte, sans quitter la boutique. Ce
n'est pas un écran de réglages système : on y vient surtout pour **vérifier son
numéro** avant une livraison, ou pour poser un mot de passe.

### Sur téléphone — une colonne

1. **Carte d'identité** : médaillon sur fond `primaire-fond`, texte
   `primaire-texte-sur-fond` (4,87:1), prénom, numéro, et le mois d'inscription
   — « membre depuis mars 2026 », jamais une date précise.
2. **Mes commandes**, **Mes demandes** — des entrées, pas des listes.
3. **Mot de passe** : « définir » ou « modifier » selon qu'il en a un.
4. **Mes appareils** : les sessions ouvertes, avec un moyen de les fermer.
5. **Aide** — sept questions, en accordéon.
6. **Supprimer mon compte**, en bas, en `danger-texte`.

### ⚠️ Sur ordinateur — deux colonnes à partir de 1 280 px

**Pas avant.** La bascule est à `xl`, et non à `lg` comme le catalogue : les
blocs de ce profil sont étroits, et les passer en deux colonnes dès 1 024 px
donnerait deux colonnes maigres au lieu d'une colonne lisible.

| | Largeur |
|---|---|
| Colonne de gauche | le reste |
| Colonne de droite | **22 rem**, fixe |

La page est bornée à `max-w-2xl` en dessous, **`max-w-6xl`** à partir de `xl` —
elle ne suit donc pas le plafond de 1 600 px du catalogue, parce qu'un formulaire
de compte étalé sur 1 600 px ne se lit plus.

**La colonne de droite est `sticky`**, callée à `top-24`. Elle porte les blocs
courts — identité, activité — et reste visible pendant qu'on fait défiler les
réglages à gauche.

⚠️ **`items-start` sur la grille, et ce n'est pas décoratif.** Sans lui, un
enfant de grille s'étire à la hauteur de la rangée, et **un élément étiré ne
colle plus** : `sticky` n'a plus de course où glisser. Le symptôme est une
colonne qui ne colle pas, sans aucune erreur — on cherche alors dans `top`, dans
`overflow`, partout sauf au bon endroit.

### La suppression du compte

Confirmation **par saisie** : il faut taper `SUPPRIMER`. Pas une case à cocher,
pas un second bouton — on ne supprime pas un compte qui porte un historique de
commandes par inadvertance.

⚠️ **Le compte est anonymisé, pas effacé.** Ses commandes portent une relation
`PROTECT` : les détruire effacerait des lignes comptables et fausserait le solde
d'un groupeur. L'écran ne doit donc pas promettre un effacement total.


## Écran 13 — Tableau de bord groupeur

**Chrome bleu** (§1.2) : l'en-tête, les boutons, l'onglet actif et les tuiles de chiffres sont en `confiance`. L'orange n'apparaît que dans « À faire aujourd'hui » et sur le bouton flottant — c'est son seul métier de ce côté-ci : l'alerte.

1. **En-tête :** « Bonjour Mama Gro », pseudonyme et non nom réel, même sur son propre écran. Fond `confiance`, texte blanc (10,36:1).
2. **Quatre tuiles**, grille 2 × 2. **Toutes cliquables vers l'écran 21** — un chiffre affiché sans moyen d'aller voir ce qu'il contient est une frustration :
   - **3** campagnes ouvertes
   - **74** commandes
   - **128 000 F** collectés
   - **126 500 F** disponibles

   Sous la grille, un lien discret : « **Voir toutes mes statistiques** » → écran 21.
3. **« À faire aujourd'hui »** — la section qui donne une raison d'ouvrir l'application, et **le seul bloc orange de l'écran**. C'est ce qui la fait ressortir sur le bleu :
   - 🔴 « **Écouteurs filaires — campagne clôturée, décidez sous 41 h** » → écran 16
   - 🟠 « **Déposez le reçu d'achat — Robe wax** » → écran 17
   - 🟣 « **3 questions sans réponse** » → écran 20
   - 🔵 « 4 nouvelles demandes dans votre quartier » → écran 19
4. **« Mes campagnes »** : liste compacte avec compteur de commandes, temps restant et statut.
5. **Bouton flottant** « + Créer une campagne », 56 × 56, en bas à droite, fond `marque` `#FF6A00` avec icône `#1D1916` (6,08:1). Sur un écran bleu, c'est l'élément le plus repérable de toute l'interface groupeur — et c'est voulu : créer une campagne est l'action qui fait vivre la plateforme.
6. `BarreNav` version groupeur — quatre onglets : **Tableau de bord · Mes campagnes · Statistiques · Portefeuille**. C'est l'arrivée de l'écran 21 qui fixe ce quatrième onglet ; sans lui, les statistiques resteraient un écran qu'on ne retrouve pas.

## Écran 14 — Créer une campagne

**Trois étapes** avec indicateur de progression : un formulaire de douze champs sur un seul écran mobile ne se remplit pas.

**Étape 1 — le produit, en détail**

C'est l'étape qui décide si une campagne se vend. Un acheteur qui ne trouve pas une information ne pose pas de question : il passe à la campagne suivante. Le formulaire doit donc **réclamer les détails**, pas les rendre optionnels.

| Champ | Obligatoire | Remarque |
|---|---|---|
| **Nom du produit** | Oui | Avec la marque si elle existe |
| **Catégorie** | Oui | Pilote les filtres de l'écran 2 |
| **Médias** | Oui | Jusqu'à **4 photos et 2 vidéos** — au moins une photo |
| **Ce que contient une part** | Oui | La question que tout acheteur se pose en premier |
| **Description** | Oui, 200 caractères minimum | Voir ci-dessous |
| **Caractéristiques** | Recommandé | Liste de paires *libellé / valeur* — voir ci-dessous |
| **État** | Oui | Neuf / reconditionné / occasion. **Un choix, pas un texte libre** |
| **Garantie** | Oui | Durée, ou « aucune ». Ne pas laisser le champ vide par défaut |
| **Origine** | Recommandé | Import, local, marque officielle |

**Les caractéristiques, en paires libellé / valeur.** C'est ce qui remplace une description fourre-tout, et c'est ce qui se maquette bien : un tableau sur deux colonnes à l'écran 3. Le groupeur ajoute ses lignes, et le formulaire **en propose selon la catégorie** — pour de l'électronique : connectique, longueur de câble, compatibilité, couleur.

> Exemple à utiliser dans les maquettes :
> *Connectique : jack 3,5 mm · Longueur : 1,2 m · Micro : intégré · Couleur : noir · Garantie : 3 mois*

**Une liste de contrôle avant publication**, à dessiner comme un bloc à cocher plutôt qu'une suite d'erreurs : « Photo nette ✓ · Contenu d'une part ✓ · Garantie ✓ · Caractéristiques — *3 recommandées, 0 remplie* ». Un formulaire qui guide obtient de meilleures fiches qu'un formulaire qui refuse.

Sur le média, une consigne à afficher dans le formulaire : « Une vidéo verticale filmée au téléphone marche très bien. Une photo nette suffit aussi. » Les groupeurs sans moyens de tournage ne doivent pas se sentir exclus du fil (§1.6).

**Quatre photos et deux vidéos, et les deux nombres ne protègent pas la même chose.** Quatre photos est une limite de confort, large exprès : les faces, l'échelle, ce que contient réellement une part. Un acheteur qui ne trouve pas une information ne demande pas la photo suivante, il passe au groupage suivant. Deux vidéos est une limite de coût : l'acheteur est sur un forfait de données limité (§18.1), une vidéo pèse cent fois une photo, et la troisième ne convainc plus personne — elle ne fait que coûter de l'argent à celui qui la regarde.

**Au moins une photo, même quand il y a une vidéo.** C'est le §1.6 appliqué au formulaire : les cartes, les lignes de liste et le fil affichent une image, et une fiche qui n'en porte aucune reste vide le temps que la vidéo charge — c'est-à-dire pendant la seconde où l'acheteur décide de s'arrêter ou de faire défiler. L'affiche d'une vidéo est acceptée à la place : c'en est une.

**La première photo est la couverture**, celle qui part dans les listes. À dire dans le formulaire, sinon le groupeur ne sait pas que l'ordre compte.

**Les adresses, pas les fichiers — pour l'instant.** Le stockage des médias reste à définir (§18 du cahier des charges). Tant qu'il n'existe pas, le formulaire demande une adresse et le dit franchement : un bouton « Choisir un fichier » qui ne mène nulle part est pire qu'un champ honnête. Le jour où le stockage existe, seul ce formulaire change — ni le modèle, ni l'API.

**Étape 2 — le prix, les paliers et la durée**

**Le prix se saisit à la pièce, puis les autres quantités se déduisent.** C'est l'ordre naturel pour un commerçant : il connaît son prix unitaire, pas son prix par lot.

1. **« Prix pour 1 pièce »** — le champ principal, et le seul obligatoire. C'est ce prix qui s'affiche partout dans l'application.
2. **« Ce que contient une part »** — 1 pièce par défaut. Un groupeur peut vendre par lot de 2 ou de 10.
3. **Les autres quantités, avec leur prix** — une liste que le groupeur allonge lui-même, un bouton « + Ajouter une quantité » :

   | Quantité | Prix total | Prix à la pièce |
   |---|---|---|
   | 1 pièce | **4 000 F** | 4 000 F |
   | 3 pièces | 11 000 F | *3 667 F* |
   | 5 pièces | 17 500 F | *3 500 F* |

   **La troisième colonne est calculée, pas saisie**, et affichée en `texte-secondaire`. Elle sert à deux choses : le groupeur voit tout de suite si son palier a du sens, et l'acheteur comprend l'intérêt de prendre plus.

   **Deux garde-fous à dessiner :** un palier dont le prix à la pièce *monte* au lieu de descendre déclenche un `Encart` `attention` — « À 3 pièces, le prix unitaire est plus élevé qu'à 1 pièce. C'est voulu ? » On avertit, **on ne bloque pas** : il peut avoir une raison. Et les paliers sont **facultatifs** : une campagne sans palier reste parfaitement valable.

4. **Sa marge, affichée pour lui seul.** Un champ optionnel « Ce que ça vous coûte à la pièce », qui ne sort jamais de son interface et n'est **jamais visible de l'acheteur**. En échange, il obtient le calcul qu'il refait aujourd'hui de tête :

   > Prix de vente 4 000 F · votre coût 2 800 F
   > **Votre marge : 1 200 F par pièce, soit 38 400 F sur 32 commandes**
   > Moins 1 500 F de frais Group Achat au retrait : **36 900 F**

   **La marge est désormais entière à la pièce**, parce que le frais ne se calcule plus par part : il se retient une seule fois, sur le groupage. C'est plus simple à comprendre pour lui, et c'est une des raisons du changement.

   C'est l'écran qui transforme le formulaire en outil de gestion. Et c'est ce qui alimente les statistiques de l'écran 21 — sans ce champ, aucune marge ne peut y être calculée.

5. **Combien de personnes voulez-vous réunir ?** — un entier, **obligatoire**. C'est le dénominateur de la barre de progression que ses acheteurs verront (§2.5).

   ⚠️ **Dire tout de suite ce que ce nombre ne fait pas**, sous le champ et dès qu'il est saisi : « Ce nombre n'est ni une limite ni un minimum. Vous pouvez dépasser 20 personnes, et à la clôture c'est vous qui décidez de maintenir le groupage ou non, même s'il n'est pas atteint. »

   Sans cette phrase, deux erreurs se produisent, et elles sont opposées. Le groupeur qui le prend pour une limite de places le met trop haut « pour avoir de la marge », et sa barre reste au quart pendant toute la campagne. Celui qui le prend pour un minimum le met trop bas, par peur d'une annulation automatique qui n'existe pas.

6. **Durée de la campagne** — 3, 7, 14 jours, ou une date.
6. **Variantes éventuelles** — tailles, pointures, coloris.

**Pas de champ « prix au détail ».** Il a été retiré : aucun prix barré dans l'application (§3). Un groupeur qui le réclame s'entend répondre que son prix de groupe est l'argument.

**Un aperçu en direct de la `CarteFil`** telle que les acheteurs la verront, mis à jour à la saisie. Il évite les erreurs de prix et rend le formulaire moins aride.

Sous le prix, le calcul affiché : « Sur 4 000 F, **vous recevez 4 000 F par part**. Group Achat retient **1 500 F une seule fois**, au retrait, si le groupage aboutit. » Le frais se dit au moment de fixer le prix, pas au moment de retirer.

**Étape 3 — la livraison**
Délai de livraison annoncé · zones couvertes · et un choix en deux cartes :
- « **J'utilise le service partenaire de Group Achat** » — l'option par défaut
- « **J'ai mon propre livreur** » — il gère alors ses livraisons lui-même

Sous ce choix, une mention qui évite un malentendu : « Les frais de livraison sont payés par l'acheteur **au livreur, à la remise**. Ils ne passent jamais par Group Achat et n'entrent jamais dans votre solde. »

> ⚠️ **Cette mention annonçait « 1 000 F dans Lomé ».** Le tarif de l'agence partenaire **n'a jamais été négocié** — `LIVRAISON.md`, le dossier qui devait le porter, a été supprimé du dépôt. On écrit qu'on ne le connaît pas plutôt que de l'inventer, et **aucun écran ne l'annonce**.

**Écran de fin :** récapitulatif + « Publier la campagne ». Puis une confirmation avec **« Partager sur WhatsApp »** bien visible : c'est par là que les groupeurs amènent leurs contacts existants, et l'ignorer serait ignorer comment ce marché fonctionne.

**Variante pré-remplie** (arrivée depuis l'écran 19) : `Encart` `info` en haut, « Créée à partir de 32 demandes pour « Huile de palme » à Agoè », champs déjà remplis.

## Écran 15 — Gérer une campagne

1. En-tête « Écouteurs filaires avec micro », retour, icône « modifier ».
2. **Bandeau de synthèse :** « 32 commandes » · « 128 000 F collectés » · `CompteurTemps` « Plus que 2 jours ».
3. **Actions :** « Partager la campagne » · « Clôturer maintenant » · « Prévenir que le produit est arrivé ».

⚠️ **« Prévenir les participants » est devenu « Prévenir que le produit est arrivé », et ce n'est pas qu'une question de mots.** L'ancien libellé promettait un canal du groupeur vers ses acheteurs, c'est-à-dire une messagerie privée — ce que le produit refuse, et ce que son anonymat interdit. Le nouveau annonce **un fait précis** : `POST /api/espace-groupeur/{id}/annoncer-l-arrivee/`, **sans aucun champ de texte**. La plateforme rédige le message ; le groupeur ne fait que dire que la marchandise est là. Voir §1.10.

Trois bornes à ne pas retirer :

- **il ne rédige rien.** Aucun texte ne traverse cette route, donc rien n'échappe au filtre du §15 — un message libre partant à trente personnes d'un coup est exactement le genre d'envoi sur lequel on oublie de brancher la modération ;
- **il n'apprend rien sur qui reçoit.** La réponse ne renvoie **qu'un compte** — « 32 personnes prévenues » — jamais une liste. Un nom, un numéro ou un quartier ici lui donnerait le fichier de clients que l'anonymat lui refuse partout ailleurs ;
- **une seule fois, et après la clôture seulement.** L'arrivée est un fait unique : une cloche qui répète le même message perd en une semaine le droit d'être regardée. Le bouton devient « Arrivée annoncée », désactivé. Avant la clôture il n'apparaît pas — « le produit est arrivé » sur un groupage encore ouvert ferait croire à une livraison imminente à des gens qui viennent de payer.

**« Partager la campagne »** partage **la fiche acheteur**, pas cet écran : recruter des participants, c'est envoyer quelqu'un sur la page où il peut commander. Lien `?groupage={id}` — voir §1.9.
4. **Liste des commandes**, 32 lignes : **code de livraison** en `Code` (« K7M-4PQ »), quantité, variante choisie, montant, quartier de livraison. **Pas de nom** — le code identifie la commande, et c'est tout ce dont le groupeur a besoin pour emballer et compter.
5. **Répartition par quartier**, en petit tableau — utile au groupeur pour organiser les tournées, et c'est une information qu'il n'a nulle part ailleurs.

**Point de conception — et c'est le plus important de l'écran.** Ni nom, ni numéro, ni adresse : le groupeur voit des codes et des quartiers (§1.7). L'écran 4 promet à l'acheteur que ses coordonnées ne sont pas communiquées au groupeur, et cet écran-ci doit tenir cette promesse — c'est aussi ce qui empêche un groupeur de se constituer un fichier de clients et de les servir hors plateforme. Les identités ne sortent qu'une fois, vers le livreur, le jour de la livraison (écran 22).

## Écran 16 — Clôturer et décider

**Objectif :** le point de bascule de la campagne. **C'est l'écran le plus important côté groupeur**, et il n'a pas d'équivalent dans une application de vente classique.

1. En-tête « Décision », retour désactivé — on ne quitte pas cet écran sans décider ou sans le refermer explicitement.
**Chrome bleu**, à une exception près : le bandeau de décision est orange. C'est le seul écran où l'orange occupe autant de place côté groupeur, parce que c'est le seul où quelque chose presse vraiment.

2. **`Encart` `attention` avec compte à rebours** — orange sur fond bleu clair :
   > ⏳ **La campagne est clôturée**
   > 32 commandes · **128 000 F collectés** · il vous reste **41 h** pour décider.
   > Sans décision, les acheteurs seront remboursés automatiquement.
3. **Récapitulatif de la décision :**
   - Collecté sur les parts : `128 000 F`
   - Frais Group Achat : `− 1 500 F`
   - **Retirable maintenant : `126 500 F`** — en style `Prix`, c'est le chiffre qui décide
   - *Frais de livraison collectés : 32 000 F — gérés par Group Achat avec son transporteur*

   La dernière ligne est en retrait et en `texte-secondaire` : ce n'est pas son argent, et il doit comprendre pourquoi elle n'entre pas dans son solde.
4. **`Encart` `info`** : « Ce montant devient retirable dès maintenant, pour que vous puissiez acheter la marchandise. Déposez ensuite le devis de votre fournisseur, puis votre reçu de paiement. » Le groupeur doit savoir, à l'instant où il décide, ce qu'on attendra de lui juste après.
5. **Deux boutons :**
   - « **Je passe la commande** » (primaire) → confirmation : « Vous pourrez retirer 126 500 F et vous vous engagez à livrer les 32 commandes. Déposez le devis de votre fournisseur. » → écran 17
   - « J'annule la campagne » (`danger-texte`) → confirmation : « Les 32 acheteurs seront remboursés intégralement. Aucun frais ne vous sera prélevé. »

**Le compte à rebours n'est pas décoratif** : passé 48 h, la plateforme annule et rembourse (§8.2 du cahier des charges). L'afficher en heures, pas en date.

## Écran 17 — Déposer un justificatif d'achat

**Objectif :** la pièce maîtresse du dispositif de sécurisation (§10 du cahier des charges). À traiter avec autant de soin que le paiement.

**Deux dépôts successifs, dans cet ordre.**

**A — Le devis, avant de retirer**
1. Titre : « Devis de votre fournisseur »
2. Phrase : « Déposez le devis ou la facture de votre fournisseur. »

   ⚠️ **Ne pas écrire que le devis débloque l'argent.** Il ne le débloque plus : le solde est retirable dès la clôture, et le devis constate au lieu de conditionner (§10.2 du cahier des charges). La phrase d'origine — « Vos 121 600 F sont versés après vérification » — promettait un contrôle qui n'existe plus, et il vaut mieux un écran moins rassurant qu'un écran faux.
3. Champs : montant du devis · nom du fournisseur · **photo ou PDF du document** (zone de dépôt).
4. Bouton « Envoyer pour vérification ».
5. **État d'attente :** « En cours de vérification — réponse sous 4 h ouvrées » avec `FriseEtapes`.

**B — Le reçu, après l'achat**
1. Titre : « Reçu de paiement »
2. **`Encart` `attention` avec délai** : « Déposez votre reçu **avant le 9 octobre à 14 h**. Sans reçu, la campagne est annulée et les acheteurs remboursés. » Le délai doit être une date et une heure, pas « sous 72 h ».
3. Champs : montant payé · date · photo du reçu.
4. Bouton « Envoyer ».

**États à dessiner :** à déposer · en vérification · **refusé** (`Encart` `danger` : « Document illisible. Déposez une photo plus nette. » + bouton « Déposer à nouveau ») · validé (coche `succes` + « **Devis vérifié le 7 octobre** »).

**Variante mise de côté — le paiement direct au fournisseur.** Le portefeuille du groupeur la rend inapplicable dans le cas général : l'argent est sur son compte avant que l'achat ne se décide. Elle reste écrite au §10.3 du cahier des charges, comme recours au-dessus d'un seuil de montant si le taux de non-livraison l'impose. **Il n'y a donc rien à dessiner pour l'instant.**

L'état *refusé* est celui qu'on oublie et celui qui arrivera le plus souvent : une photo de reçu prise à la va-vite dans un marché est rarement nette du premier coup.

## Écran 18 — Portefeuille groupeur

**Objectif :** montrer où est l'argent et à quel titre. C'est l'écran qui explique le modèle économique sans un mot de pitch.

1. En-tête « Portefeuille ».
2. **Carte principale**, fond `confiance` (`#1E3A8A`), texte blanc (10,36:1) : « Disponible » / **`126 500 F`** / bouton blanc « Retirer mes fonds ».

   ⚠️ **Ce bouton agit réellement, et c'est nouveau.** C'est le geste qui déclenche la retenue des 1 500 F par groupage abouti : la confirmation doit donc l'annoncer — « Vous retirez **126 500 F**. Group Achat retient 1 500 F pour 1 groupage abouti. » Un retrait qui solde trois groupages annonce 4 500 F.
3. **Trois tuiles :**
   - **135 000 F** — « En cours de collecte » — « Campagnes pas encore clôturées » — icône horloge
   - **400 300 F** — « Retiré » — « Baskets homme, le 28 septembre » — icône flèche entrante
   - **3 000 F** — « Frais Group Achat » — « 1 500 F par groupage abouti · 2 groupages » — icône reçu, **plus l'icône pourcentage** : il n'y a plus de pourcentage
4. **`Encart` explicatif**, à ne pas omettre : « L'argent de vos acheteurs est à vous dès leur paiement. Il est détenu jusqu'à la clôture du groupage, puis vous pouvez le retirer en entier. Group Achat retient 1 500 F par groupage abouti, au moment du retrait. Aucun frais sur un groupage annulé. Les frais de livraison payés par vos acheteurs ne vous reviennent pas : ils vont au transporteur. »

   Un groupeur qui découvre la retenue au moment de retirer se sent trompé. Elle est dite ici, à l'écran 14 au moment de fixer le prix, et à l'écran 16 au moment de décider : trois fois, et c'est volontaire.
5. **Historique**, lignes datées :

| Date | Libellé | Montant |
|---|---|---|
| 7 oct. | **Groupage clôturé — Écouteurs filaires** (32 commandes) | **+128 000 F** |
| 7 oct. | Frais Group Achat — à retenir au retrait | −1 500 F |
| 7 oct. | Devis fournisseur reçu | — |
| 28 sept. | **Retrait — Baskets homme** (41 commandes) | **+400 300 F** |
| 28 sept. | Frais Group Achat — retenus | −1 500 F |
| 20 sept. | Groupage annulé — Savon de Marseille | **Aucun frais** |

Les chiffres des baskets doivent tomber juste aussi : 41 × 9 800 = 401 800 F, moins 1 500 F = **400 300 F**.

**Deux libellés différents, et la différence compte** : « groupage clôturé » pour un solde devenu retirable mais pas encore retiré, « retrait » pour de l'argent réellement parti. Le groupeur doit pouvoir distinguer les deux d'un coup d'œil, sinon il croit avoir été payé deux fois.

La dernière ligne vaut d'être montrée : elle prouve qu'aucun frais n'est prélevé sur un groupage annulé, comme l'annonce le §7 du cahier des charges.

6. **Lien** « Voir mes statistiques » → écran 21. Le portefeuille dit *combien*, les statistiques disent *pourquoi*.
7. **Bandeau de démonstration** en bas : « Démonstration — aucun mouvement de fonds réel. »

## Écran 19 — Fil des demandes (groupeur)

**Objectif :** transformer une masse de demandes en décision commerciale. **Agrégé, jamais une liste brute.**

1. En-tête « Demandes », icône de filtre.
2. **Filtres :** « Mon quartier » · « Toutes » · « Cette semaine ».
3. **Cartes de demande agrégée :**

```
┌──────────────────────────────────────┐
│ Huile de palme                       │
│ 🔥 32 personnes · Agoè · 7 jours     │
│ Budget moyen indiqué : 11 500 F      │
│ Volume estimé : 640 L                │
│         [ Lancer une campagne ]      │
└──────────────────────────────────────┘
```

Trois autres : Lait en poudre (18, Tokoin) · Charbon (14, Bè) · Couches bébé (9, Adidogomé).

4. ⚠️ **« Voir les 32 demandes » a été retiré, et ne doit pas revenir.** Le lien ne faisait rien, et le brancher aurait été une faute : il promettait les demandes une par une, alors qu'une demande individuelle porte le numéro de celui qui l'a déposée. La servir au groupeur lui donnerait exactement le fichier de clients que l'anonymat lui refuse partout ailleurs. L'API s'y refuse d'ailleurs explicitement — la route `demandes` **n'agrège que par produit et quartier**. « 14 personnes à Agoè veulent du riz » est tout ce qu'il faut pour décider de lancer un groupage, et c'est déjà sur la carte.
5. **`Encart` `info`** : « Les produits les plus demandés sont ceux où vous avez le moins de concurrence. »

**« Lancer une campagne » ouvre l'écran 14 pré-rempli** : produit, quantité estimée, quartier, prix suggéré. C'est tout l'intérêt de l'écran — à matérialiser dans le prototypage.

## Écran 20 — Questions reçues (groupeur)

1. En-tête « Questions », compteur « 3 sans réponse ».
2. **Filtres :** « Sans réponse (3) » · « Toutes ».
3. **Liste groupée par campagne** : vignette, nom, puis les questions avec auteur, date, texte, et un champ de réponse dépliable + bouton « Répondre ».
4. **`Encart` `info`** : « Une réponse publique profite à tous vos participants et rassure les visiteurs. »

Une question sans réponse est une vente qui n'a pas lieu : c'est pourquoi elle figure dans « À faire aujourd'hui » de l'écran 13.

### Le filtre s'applique ici aussi — et plus fermement

**C'est le côté risqué du fil** (§14.2 du cahier des charges). L'acheteur n'a rien à gagner à sortir de la plateforme ; le groupeur, si. Les états de modération de l'écran 10 s'appliquent donc **à l'identique sur ses réponses**, et deux éléments s'ajoutent.

**a) L'avertissement de première réponse.** Une feuille, affichée **une seule fois**, à sa toute première réponse. Fond blanc, icône bouclier en `confiance` :

> **Vos réponses sont publiques.**
> Ne communiquez jamais votre numéro, votre adresse ou un lien vers un autre service. Les acheteurs paient sur Group Achat, et c'est ce qui vous garantit d'être payé à la clôture.
>
> *Un seul bouton : « J'ai compris ».*

Le second paragraphe est à soigner : il ne menace pas, **il explique son intérêt**. C'est plus efficace qu'un règlement.

**b) L'état « réponse refusée », en plus ferme que côté acheteur.** Même `Encart` `danger`, même mécanique — non publié et averti en même temps — mais la copie change, parce que la bonne foi est moins probable ici :

> **Cette réponse ne sera pas publiée.**
> Elle contient des informations permettant de vous identifier ou de vous contacter hors de Group Achat.
>
> Cette tentative est enregistrée. Les échanges de coordonnées peuvent entraîner la suspension de votre compte.

La dernière ligne est la seule menace du produit, et elle n'apparaît que de ce côté. Elle doit être vraie : le compteur de tentatives alimente les signaux de surveillance du §10.5.

Elle doit y être, et elle doit être vraie : le compteur de tentatives alimente les signaux de surveillance du §10.5.

**Ce qui n'apparaît nulle part dans l'application :** le compteur lui-même, l'historique des messages refusés, le palier de suspension. Ça vit dans **l'admin Django**, pas dans une maquette — un groupeur qui voit son compteur apprend à rester juste en dessous.

---

## Écran 21 — Statistiques du groupeur

**Objectif :** qu'un groupeur sache, en dix secondes, **si son activité marche et ce qu'il doit changer**. C'est l'écran qui fait passer Group Achat d'une place de marché à un outil de gestion — et c'est celui qui le retient, parce qu'il ne le retrouvera nulle part ailleurs.

**Chrome bleu**, comme tout le côté groupeur (§1.2). L'orange n'y apparaît que sur une alerte.

### Le principe à tenir : un chiffre, puis sa variation, puis sa cause

Un tableau de bord qui donne un chiffre sans point de comparaison ne sert à rien : « 128 000 F collectés » ne dit pas si c'est bien. **Chaque chiffre porte donc sa variation**, et un appui dessus ouvre ce qui l'explique.

**Période, en haut** — segment à trois positions : « 30 jours » · « 3 mois » · « Tout ». 30 jours par défaut. Toutes les variations se lisent par rapport à la période précédente de même durée.

### De haut en bas

1. **En-tête** « Mes statistiques », fond `confiance`, texte blanc (10,36:1). À droite, une icône d'export.

2. **La carte maîtresse** — fond `confiance`, texte blanc, coins 16. Une seule chose dedans, et c'est **ce qu'il a gagné**, pas ce qu'il a encaissé :

   > **Vos revenus — 30 jours**
   > **668 100 F** nets
   > *+ 18 % par rapport aux 30 jours précédents* — flèche montante

   **Pourquoi « net » et pas « collecté » :** le collecté inclut l'argent qui n'est pas encore retirable, et il inclut les frais de plateforme. Un tableau de bord qui met en avant un chiffre plus flatteur que la réalité détruit sa propre crédibilité au premier retrait. **Le chiffre de la carte est la somme des barres de l'histogramme** — 126 500 + 400 300 + 141 300 : un total qu'on ne peut pas recalculer depuis l'écran est un total qu'on ne croit pas.

3. **Quatre tuiles**, en grille 2 × 2, fond blanc, filet 1 px `bordure`, coins 12. Chacune : un libellé en `Libelle`, le chiffre en `Prix`, la variation en `Petit`.

   | Tuile | Valeur de démonstration | Variation |
   |---|---|---|
   | **Campagnes abouties** | **4 sur 5** | `succes` |
   | **Participants** | **127** | + 31 % |
   | **Panier moyen** | **4 150 F** | − 4 % en `danger` |
   | **Taux de réussite** | **80 %** | stable |

   Le **taux de réussite** — campagnes allées jusqu'à la livraison sur campagnes lancées — est le chiffre qui compte le plus pour nous comme pour lui : c'est le même que celui qui conditionne ses plafonds d'exposition (§10.4 du cahier des charges). **Le lui montrer est un acte de loyauté** : il doit savoir ce sur quoi il est jugé.

4. **Graphique : revenus par campagne** — un **histogramme horizontal**, une barre par campagne, en `confiance`. Horizontal et non vertical, pour que les noms de campagne restent lisibles sur 390 px de large. Au bout de chaque barre, le montant.

   ```
   Écouteurs filaires     ████████████████████  126 500 F
   Baskets homme          ██████████████████████████  400 300 F
   Huile de palme         ███████████  141 300 F
   Savon de Marseille     ▏ annulée
   ```

   La campagne annulée **reste visible**, en `texte-secondaire`, sans barre. Un tableau de bord qui cache les échecs ne sert pas à décider.

5. **Graphique : ce qui se vend, par catégorie** — barres empilées ou anneau, maximum **quatre catégories plus un « autres »**. Au-delà, c'est illisible sur mobile et personne ne lit la légende.

6. **Carte des quartiers** — *pas une carte géographique*, un tableau classé : les cinq quartiers d'où viennent ses commandes, avec leur part.

   | Quartier | Commandes | Part |
   |---|---|---|
   | Agoè | 38 | 30 % |
   | Tokoin | 29 | 23 % |
   | Bè | 24 | 19 % |

   **C'est la donnée la plus actionnable de l'écran**, et il ne l'a nulle part ailleurs : elle lui dit où concentrer ses tournées et quels quartiers annoncer. Et elle respecte l'anonymat (§1.7) — un quartier n'identifie personne.

7. **Section « Ce que ça vous dit »** — deux ou trois constats en phrases, calculés, dans des `Encart` :

   > `info` — « Vos campagnes d'électronique aboutissent plus souvent que vos campagnes alimentaires. »
   > `attention` — « Votre panier moyen baisse depuis deux mois. »
   > `succes` — « 3 acheteurs sur 10 vous ont recommandé une campagne. »

   **À dessiner avec soin, et à écrire avec prudence.** C'est ce qui distingue un vrai outil d'un empilement de chiffres. Mais la règle est stricte : **un constat, jamais un conseil**. « Votre panier moyen baisse » est un fait ; « augmentez vos prix » est un conseil commercial dont nous ne sommes pas responsables, et qui nous rendrait comptables de ses pertes.

8. **Lien bas de page** : « Voir mon portefeuille » → écran 18. Les statistiques expliquent, le portefeuille paie. **Deux écrans distincts, volontairement** : on ne mélange pas l'analyse et le mouvement d'argent.

### Les états à maquetter

| État | Affichage |
|---|---|
| **Aucune campagne** — le plus important, c'est le premier écran d'un nouveau groupeur | `EtatVide` — « Vos statistiques apparaîtront ici après votre première campagne » + bouton « Créer une campagne ». **Ne dessine jamais un tableau de bord rempli de zéros** : c'est décourageant et ça n'informe de rien |
| **Une seule campagne** | Les chiffres s'affichent, **sans variation** — il n'y a pas de période précédente. Masque les flèches, ne mets pas « + 0 % » |
| **Chargement** | Squelettes gris aux emplacements des tuiles et des graphiques, pas de roue qui tourne |

### Ce qui ne doit surtout pas y figurer

- **Aucun nom, aucun numéro, aucune adresse d'acheteur.** Des quartiers, des nombres, des montants. C'est la même règle qu'à l'écran 15, et c'est elle qui protège le modèle (§1.7).
- **Aucune comparaison avec les autres groupeurs.** Pas de classement, pas de « vous êtes dans les 20 % les meilleurs ». Les groupeurs ne se voient pas entre eux, et nous ne les mettons pas en concurrence — ce serait les pousser à baisser leurs prix jusqu'à ne plus pouvoir livrer.
- **Aucune projection.** « Vous gagnerez X le mois prochain » est une promesse. On montre le passé.

---

# Lot 4 — la livraison

## Écran 22 — Tournée du livreur (page web)

**Ce n'est pas un écran de l'application mobile.** C'est une **page web** que le livreur ouvre depuis un lien reçu, sans rien installer et sans compte — le livreur est un prestataire partenaire, pas un utilisateur de Group Achat (§6 du cahier des charges). À dessiner quand même : c'est là que se fabrique la **preuve de livraison**. Elle ne conditionne aucun retrait — le solde du groupeur est retirable depuis la clôture (§10.1 du cahier des charges) — mais elle construit **son historique de fiabilité**, qui détermine son plafond d'exposition. C'est le seul levier qui nous reste sur lui, donc il vaut cet écran.

**À dessiner en 390 × 844 comme les autres**, puisqu'elle sera ouverte sur un téléphone, mais sans `BarreNav` : c'est une page isolée.

**De haut en bas**

1. **En-tête simple :** « Group Achat — Livraisons » et la date du jour. Pas de navigation, pas de menu.
2. **Progression :** « **3 livrées sur 12** » avec une barre fine remplie en `marque`.
3. **Liste des livraisons**, une carte par acheteur :
   - **Nom** : « Akosua D. » en `Corps-fort`
   - **Adresse et repère** : « Tokoin, rue des Cocotiers, près de la pharmacie Sodji »
   - **Téléphone** avec un bouton d'appel — c'est **le seul endroit de tout le produit** où le numéro d'un acheteur est visible, et uniquement le jour de sa livraison
   - **Contenu** : « Écouteurs filaires avec micro — 1 part »
   - **Jamais le montant payé** : le livreur n'a pas à le connaître, et l'afficher créerait une tentation inutile
   - **Champ de saisie du code** : six cases, deux groupes de trois, clavier en majuscules
   - Deux boutons : « **Valider la livraison** » (primaire) et « Colis refusé » (`danger-texte`)
4. **Les cartes validées** passent en haut repliées, avec une coche `succes` et l'heure : « Livrée à 10 h 32 ».

**Les états et cas particuliers à dessiner**

| Cas | Écran |
|---|---|
| **Succès** | La carte se replie, coche `succes`, « Livrée à 10 h 32 », la progression avance |
| **Code incorrect** | Cases en `danger` + « Code incorrect. Vérifiez auprès du client. » |
| **Code déjà validé** | « Cette livraison a déjà été validée à 10 h 32. » |
| **Code non présenté** | Lien discret « Le client n'a pas son code » → confirmation avec le **nom et le numéro**, coché « code non présenté ». La livraison est marquée **confirmée sans code** et signalée pour contrôle, sans bloquer le groupeur (§11.1) |
| **Colis refusé** | Feuille : motif (ce n'est pas le produit commandé · colis abîmé · client absent · adresse introuvable), champ de description, photo, bouton « Enregistrer le refus ». Sans ce bouton, un refus ressemble à une livraison non faite et le litige devient impossible à instruire |
| **Hors réseau** | Bandeau `attention` : « Pas de connexion — vos validations seront envoyées dès le retour du réseau. » La saisie reste possible |
| **Lien expiré** | Page simple : « Ce lien a expiré. Demandez un nouveau lien à Group Achat. » |

**Sécurité à matérialiser dans la maquette :** le lien ne couvre **que la tournée du jour**, il expire le soir, et il n'affiche aucun montant. Une page qui liste des noms, des adresses et des numéros de téléphone est une page sensible — c'est à ce titre qu'elle se dessine, et pas comme un simple formulaire.

---

# Lot 5 — l'administration

## Écran A1 — Tableau de bord administrateur

**C'est la seule maquette côté administrateur.** Tout le reste — fiches, recherche, édition, actions — vit dans l'admin Django et ne se dessine pas (§13.6 du cahier des charges). Cette page-ci existe parce que c'est précisément ce que l'admin Django ne sait pas faire : donner une vue d'ensemble en un écran.

**À dessiner en 1280 × 800**, et non en 390 : c'est le seul écran du produit destiné à un ordinateur. L'administrateur travaille assis, avec un clavier, pas dans un taxi.

**Chrome neutre**, ni orange ni bleu. Fond `surface-douce`, cartes blanches. Les deux chromes de marque appartiennent aux deux publics ; l'outil interne n'en porte aucun, et cette neutralité est utile : elle évite de confondre une capture d'écran interne avec le produit.

### A1.0 — La feuille de connexion, avant tout le reste

⚠️⚠️ **Cette section est nouvelle, et son absence était le plus gros trou du
document.** L'écran A1 **s'ouvrait sans mot de passe** — il était gardé par un
**jeton unique et partagé**, posé dans le `.env` du serveur et recopié à la
main par chaque administrateur. Le code qui le portait l'admettait : *« ce
n'est pas de l'authentification, et il ne faut pas le prendre pour telle »*.

Il y a maintenant **de vrais comptes**. Ce que ça change :

| | Le jeton partagé | La session |
|---|---|---|
| Distingue deux administrateurs | non | **oui** |
| Se révoque pour une personne | non — il fallait le changer pour tous | **oui** |
| Résiste à l'essai systématique | rien ne comptait les échecs | **5 essais, puis 15 minutes** |
| « décidé par » sur une décision KYC | ce qu'on voulait bien saisir | **le compte connecté** |

Le dernier n'est pas cosmétique. Le §10.5 du cahier des charges confie la
validation d'un dossier à un humain parce que, le jour d'un litige, **ce
dossier est notre seul recours contre le groupeur**. Un journal dont l'auteur
est un champ de texte libre ne prouve rien.

**À dessiner : une carte centrée, 1 280 × 800, chrome neutre.**

1. Titre — « **Administration Group Achat** »
2. Une phrase qui dit pourquoi c'est fermé : « Ces écrans affichent des noms,
   des numéros de téléphone et des références de pièces d'identité. »
3. Champ « **Identifiant** »
4. Champ « **Mot de passe** », masqué
5. Bouton plein « **Ouvrir l'administration** », désactivé tant qu'un des deux
   champs est vide, en état `chargement` pendant l'envoi

⚠️ **Pas de code SMS ici, et pas de « mot de passe oublié ».** L'acheteur a le
code SMS comme voie de récupération ; l'administrateur n'en a aucune. Un
administrateur qui a perdu son mot de passe le fait réinitialiser par un autre,
dans l'admin Django. C'est assumé : ce sont quelques personnes, pas un public.

#### ⚠️⚠️ Un seul message d'erreur pour trois causes

Identifiant inconnu, mot de passe faux, compte sans droits : **la même phrase**,
mot pour mot.

> Identifiant ou mot de passe incorrect.

Distinguer « cet identifiant n'existe pas » de « mauvais mot de passe » dirait
à qui essaie **quels identifiants existent**, et lui permettrait de n'attaquer
que ceux-là. C'est la différence entre deviner deux secrets et n'en deviner
qu'un. **Ne dessine jamais deux messages distincts ici**, même si l'un semblerait
plus serviable.

#### Le verrou

Au **cinquième** échec, la connexion se ferme **quinze minutes**, et le message
change pour annoncer le délai restant :

> Trop de tentatives. Réessayez dans 14 minute(s).

⚠️ **Le verrou s'annonce à l'instant où il est posé**, pas à la tentative
suivante. Sinon la personne passerait le quart d'heure à chercher un mot de
passe qui, de toute façon, ne serait pas accepté.

⚠️ **Quinze minutes et pas davantage**, parce qu'**il n'y a pas d'autre porte**.
Côté acheteur, le code SMS reste ouvert pendant le verrou, donc personne n'est
fermé dehors. Ici, un administrateur verrouillé attend, ou un collègue lui lève
le verrou depuis l'admin Django.

#### La session, et où elle se voit

**Douze heures, et elle ne glisse pas** : l'échéance est posée à l'ouverture et
ne bouge plus. ⚠️ C'est volontairement différent de la session acheteur, qui
dure trente jours **glissants** : là-bas refaire un code SMS à chaque visite
ferait perdre des acheteurs, ici l'écran montre des pièces d'identité. Douze
heures couvrent une journée de travail.

**Le pied de la barre latérale** porte l'identité, et c'est la seule chose qui
change dans le chrome de A1 :

> Connecté en tant que
> **Ama Koffi**
> Les décisions KYC porteront ce nom.
> *Fermer la session*

⚠️ **Ce pied de page portait un aveu** : *« Jeton partagé — il n'identifie
personne. Les décisions portent le nom qu'on veut bien y mettre. »* Il n'a plus
lieu d'être. La place sert désormais à dire **qui** signe — ce qu'il faut savoir
avant de trancher un dossier, et surtout avant de le trancher depuis le poste
d'un collègue resté connecté.

#### Ce qui ne se dessine pas

**La création d'un compte** : elle se fait par
`python manage.py creer_administrateur`, en ligne de commande, et les comptes
suivants dans l'admin Django en cochant `is_staff`.

**La révocation** : on décoche `is_staff`, et **les sessions en cours tombent à
la requête suivante** — pas au bout de douze heures. Il n'y a donc aucun écran
« gérer les administrateurs » à maquetter, et il ne faut pas en inventer un :
l'admin Django le fait déjà, mieux et avec un journal.

⚠️ **La déconnexion ferme la session côté serveur**, elle ne se contente pas
d'oublier le jeton dans le navigateur. C'est tout l'écart avec le jeton
partagé : l'oublier ne le rendait pas invalide, il restait bon pour qui l'avait
noté. Les **autres** sessions du même compte survivent — fermer l'onglet d'un
poste partagé ne doit pas déconnecter la même personne de son téléphone.

### L'ordre vertical, qui est tout le propos

**1. Les alertes**, pleine largeur, en haut. Une ligne par alerte, la plus grave en premier. `Encart` `danger` pour un changement de compte Mobile Money, `attention` pour un plafond approché. **Rien quand il n'y a rien** — pas de bloc vide « aucune alerte », qui prend de la place et apprend à ignorer la zone.

**2. Les six files de travail**, en grille de 3 × 2. Une carte par file :

- le **nombre** en `Prix`, c'est ce qu'on lit de loin
- le libellé en `Corps-fort`
- **le plus ancien en attente** en `Petit` — « le plus ancien : 3 jours ». C'est cette ligne qui fait agir, pas le compteur
- la carte entière est cliquable vers la vue filtrée de l'admin Django

| File | Démonstration |
|---|---|
| Dossiers KYC à valider | **4** · le plus ancien : 2 jours |
| Justificatifs d'achat à contrôler | **2** · le plus ancien : 1 jour |
| Contestations à arbitrer | **1** · le plus ancien : 4 jours |
| **Livraisons non confirmées (7 j)** | **3** · le plus ancien : 9 jours |
| Messages signalés | **6** · le plus ancien : 1 jour |
| Retours de colis | **0** |

**La carte « Livraisons non confirmées » se distingue des cinq autres** : filet `danger` et non `bordure`. C'est la seule file où **notre propre argent** est exposé, puisque le groupeur a déjà été payé. Les autres coûtent de la confiance ; celle-ci coûte du cash — et un écran qui les traite à égalité ment sur les priorités.

**Une file à zéro reste affichée**, en `texte-secondaire`, sans mise en avant. Faire disparaître une file vide déplace les cartes d'un jour à l'autre, et on ne retrouve plus rien.

**3. Les quatre indicateurs**, en ligne, sous les files. Libellé, valeur, variation sur 30 jours :

| Indicateur | Démonstration |
|---|---|
| **Argent détenu pour les groupeurs** | **1 284 000 F** |
| Campagnes en cours | **11** · dont 3 à échéance sous 48 h |
| Taux de livraison (30 j) | **94 %** |
| Frais encaissés (30 j) | **18 000 F** · 12 groupages aboutis |

Sous le premier, une ligne qui n'est pas décorative : « **Rapprochement : écart de 0 F** » en `succes`, ou l'écart en `danger` s'il y en a un. **C'est la ligne la plus sérieuse de l'écran** — le jour où l'argent détenu calculé et le solde réel divergent, quelque chose ne va pas, et il faut le voir tout de suite.

**4. Activité récente**, en bas : dix lignes datées — groupage clôturé, retrait exécuté, dossier validé, litige tranché. C'est le seul bloc du tableau de bord qui regarde le passé, et c'est pour ça qu'il est en dernier.

### Ce qui ne doit pas y figurer

- **Le nombre d'inscrits en grand.** C'est la mesure qui flatte et n'engage à rien. Ce qui compte, c'est le nombre de campagnes allées jusqu'à la livraison.
- **Aucun bouton qui déplace de l'argent.** Depuis le tableau de bord on *va vers* un dossier ; on ne rembourse pas en un clic depuis une vue d'ensemble, sans avoir ouvert le dossier. Toute action sur l'argent est tracée et motivée (§18.3 du cahier des charges).
- **Aucune donnée personnelle.** Des compteurs et des montants. Un nom n'apparaît qu'une fois le dossier ouvert, et cet accès est journalisé (§13.5).

### Les états à maquetter

| État | Affichage |
|---|---|
| **Journée calme** — l'état le plus fréquent, et celui qu'on oublie | Pas d'alertes, files à zéro ou à un, indicateurs normaux. Il doit être agréable à regarder : un administrateur qui ouvre son écran tous les matins pour voir un mur rouge finit par ne plus l'ouvrir |
| **Alerte sérieuse** | Un changement de compte Mobile Money en haut, en `danger`, avec le nom du groupeur et un lien vers son dossier |
| **Écart de rapprochement** | La ligne sous l'argent détenu passe en `danger` : « Écart de 12 500 F — à instruire » |

---

# Textes d'écran, prêts à coller

Le contenu littéral de chaque écran, dans le format de ta maquette d'accueil. **À donner tel quel à Stitch, ou à recopier dans Figma.** Le vocabulaire suit le tableau du §3 : *groupage*, *acheteurs confirmés*, *F CFA*.

---

### 1 — Accueil

```
Rechercher un produit...          Demander
                                        7
                                  Partager
Il reste 2 jours
Écouteurs filaires Pro avec micro
4 000 F CFA
la part
32 acheteurs confirmés
Par Mama Gro
Groupeur sélectionné · Livré ou remboursé
Voir le groupage
Glisser vers le haut pour le groupage suivant
Accueil  Groupage  Demander  Commandes  Profil
```

### 2 — Groupage (vue liste)

```
Rechercher un produit...
Tous   Alimentaire   Électronique   Mode   Maison
Écouteurs filaires Pro avec micro
4 000 F CFA · 32 acheteurs confirmés · Il reste 2 jours
Robe wax, taille au choix
7 500 F CFA · 18 acheteurs confirmés · Il reste 5 jours
Baskets homme, pointures 39-45
9 800 F CFA · 41 acheteurs confirmés · Il reste 4 h
Vide : Aucun groupage ne correspond. Demander ce produit
```

### 3 — Détail du groupage

```
Écouteurs filaires Pro avec micro
4 000 F CFA  par part
Il reste 2 jours · 32 acheteurs confirmés
Par Mama Gro
Ce que contient une part
1 écouteur filaire avec micro, garantie 3 mois
Caractéristiques
Connectique  jack 3,5 mm
Longueur     1,2 m
Micro        intégré
Garantie     3 mois
État         Neuf
Livraison
À domicile par notre partenaire
Sous 3 à 5 jours après la clôture
Les frais de livraison se règlent directement au livreur, à la remise.
Les règles
Paiement à la commande, versé au groupeur, retirable à la clôture
Le groupeur décide à la clôture si la commande passe
Si le groupage n'aboutit pas, vous êtes remboursé intégralement
Questions (7)          Voir les questions
Partager
Commander — 4 000 F CFA
```

### 4 — Connexion *(feuille remontante, déclenchée par « Payer »)*

```
Encore une étape
Votre numéro sert à vous joindre pour la livraison. Rien de plus.
+228  Numéro de téléphone
Recevoir le code
--- puis ---
Code reçu par SMS
[  ][  ][  ][  ]
Renvoyer le code (0:42)
Valider
```

### 5 — Commander

```
Écouteurs filaires Pro avec micro
Quantité
−   1   +
Où livrer
Partager ma position
ou
Indiquer le nom du lieu
Repère : rue des Cocotiers, près de la pharmacie Sodji
Numéro à joindre à la livraison
Récapitulatif
1 part × 4 000 F CFA            4 000 F CFA
Total à payer                   4 000 F CFA
Les frais de livraison se règlent directement au livreur, à la remise.
Groupeur sélectionné · Livré ou remboursé
J'accepte les conditions de vente
Payer 4 000 F CFA
```

### 6 — Paiement Mobile Money *(simulé)*

```
Paiement
4 000 F CFA
Choisissez votre opérateur
T-Money        Flooz
Confirmez sur votre téléphone
Composez #145# et validez
En attente de confirmation...
Démonstration — aucun argent réel ne circule
```

### 7 — Confirmation

```
C'est confirmé
4 000 F CFA payés
Écouteurs filaires Pro avec micro — 1 part
Votre code de livraison
K7M-4PQ
À donner au livreur, et à lui seul.
Livraison prévue sous 3 à 5 jours après la clôture du groupage
Voir ma commande          Retour à l'accueil
```

### 8 — Mes commandes

```
Mes commandes
En cours   Terminées
Écouteurs filaires Pro avec micro
4 000 F CFA · Payée — en attente de clôture
Robe wax, taille M
8 500 F CFA · En cours de livraison
Savon de Marseille, carton de 48
10 500 F CFA · Remboursée
Vide : Aucune commande pour le moment. Voir les groupages ouverts
```

### 9 — Détail d'une commande

```
Écouteurs filaires Pro avec micro
Payée — en attente de clôture
Commandé    Clôturé    Commande passée    En livraison    Livré
Votre code de livraison
K7M-4PQ
Récapitulatif
Part        4 000 F CFA
Total       4 000 F CFA
Payée le 5 octobre
Livrer à : Tokoin, rue des Cocotiers, près de la pharmacie Sodji
Votre paiement va au portefeuille du groupeur, retirable à la clôture.
Une question ?          Signaler un problème
```

### 10 — Questions

```
Questions
Écouteurs filaires Pro avec micro
Quelle marque ?   Quelle origine ?   Quand la livraison ?   Autre question
Posez votre question sur ce produit...
Votre question et la réponse seront visibles par tout le monde.
Envoyer
---
C'est quelle marque d'écouteurs ?  — Akosua D.
  Jack 3,5 mm, micro intégré, câble de 1,2 m. Garantie 3 mois.  — Mama Gro
La livraison va jusqu'à Adidogomé ?  — Yawa T.
  Oui, tout Lomé est couvert.  — Mama Gro
Est-ce qu'on peut payer à la livraison ?  — Dodzi M.
  En attente de réponse
---
N'échangez jamais de numéro de téléphone. Votre paiement n'est protégé que sur Group Achat.
Message refusé :
Ce message ne sera pas publié.
Il contient des informations qui permettraient de vous identifier.
Pour votre sécurité, les échanges restent anonymes sur Group Achat.
Votre numéro est déjà enregistré pour la livraison. Le livreur l'aura le jour de sa tournée.
Modifier          Annuler
```

### 11 — Demander un produit

```
Demander un produit
Dites ce que vous cherchez. Si assez de personnes le demandent, un groupeur lance le groupage.
Quel produit ?
Quantité souhaitée
Votre quartier
Prix que vous accepteriez (facultatif)
Envoyer ma demande
```

### 12 — Mes demandes

```
Mes demandes
Huile de palme 20 L
32 personnes le demandent · Groupage lancé
Sucre en poudre, sac de 50 kg
7 personnes le demandent · En attente
Vide : Vous n'avez encore rien demandé.
```

---

## Côté groupeur — chrome bleu

### 13 — Tableau de bord

```
Bonjour Mama Gro
3 groupages ouverts    74 commandes
128 000 F CFA collectés    126 500 F CFA disponibles
Voir toutes mes statistiques
À faire aujourd'hui
Écouteurs filaires — groupage clôturé, décidez sous 41 h
Déposez le reçu d'achat — Robe wax
3 questions sans réponse
4 nouvelles demandes dans votre quartier
Mes groupages
+ Créer un groupage
Tableau de bord   Mes groupages   Statistiques   Portefeuille
```

### 14 — Créer un groupage

```
Étape 1 — Le produit
Nom du produit · Catégorie · Photos ou vidéo
Ce que contient une part
Description
Caractéristiques : Connectique / Longueur / Micro / Couleur
État : Neuf — Reconditionné — Occasion
Garantie
Avant publication : Photo nette ✓ · Contenu d'une part ✓ · Garantie ✓

Étape 2 — Le prix
Prix pour 1 pièce        4 000 F CFA
Ce que contient une part : 1 pièce
+ Ajouter une quantité
   3 pièces   11 000 F CFA   (3 667 F CFA la pièce)
   5 pièces   17 500 F CFA   (3 500 F CFA la pièce)
Ce que ça vous coûte à la pièce (visible de vous seul)
   Prix de vente 4 000 · votre coût 2 800
   Votre marge : 1 200 F CFA par pièce, soit 38 400 F CFA sur 32 commandes
   Moins 1 500 F CFA de frais Group Achat au retrait : 36 900 F CFA
Sur 4 000 F CFA, vous recevez 4 000 F CFA par part. Group Achat retient 1 500 F CFA une seule fois, au retrait, si le groupage aboutit.
Durée : 3 jours — 7 jours — 14 jours — une date
Variantes (tailles, pointures, coloris)

Étape 3 — La livraison
Délai annoncé · Zones couvertes
J'utilise le service partenaire de Group Achat
J'ai mon propre livreur
Les frais de livraison sont payés par l'acheteur et vont au transporteur. Ils n'entrent jamais dans votre solde.
Publier le groupage
Partager sur WhatsApp
```

### 15 — Gérer un groupage

```
Écouteurs filaires Pro avec micro
32 commandes · 128 000 F CFA collectés · Il reste 2 jours
Partager   Clôturer maintenant   Prévenir les participants
Commandes
K7M-4PQ   1 part · noir · 4 000 F CFA · Tokoin
P3R-9XA   2 parts · noir · 8 000 F CFA · Agoè
...
Répartition par quartier
Agoè 38 %   Tokoin 23 %   Bè 19 %
```

### 16 — Clôturer et décider

```
Le groupage est clôturé
Décidez sous 41 h
32 commandes · 128 000 F CFA collectés
Vous pourrez retirer 126 500 F CFA (frais Group Achat : 1 500 F CFA)
Je maintiens le groupage
J'annule — tous les acheteurs sont remboursés
Sans décision sous 48 h, le groupage est annulé et les acheteurs remboursés.
```

### 17 — Déposer un justificatif

```
Déposer votre reçu d'achat
Photographiez le reçu du fournisseur.
Prendre une photo        Choisir un fichier
Montant   Fournisseur   Date
Envoyer
Sans reçu avant le 9 octobre, le groupage est annulé et les acheteurs remboursés.
```

### 18 — Portefeuille

```
Portefeuille
Disponible
126 500 F CFA
Retirer mes fonds
135 000 F CFA  En cours de collecte — détenu jusqu'à la clôture
400 300 F CFA  Retiré — Baskets homme, le 28 septembre
3 000 F CFA    Frais Group Achat — 1 500 F CFA par groupage abouti · 2 groupages
L'argent de vos acheteurs est à vous dès leur paiement. Il est détenu jusqu'à la clôture du groupage, puis vous pouvez le retirer en entier.
Group Achat retient 1 500 F CFA par groupage abouti, au moment du retrait. Aucun frais sur un groupage annulé. Les frais de livraison vont au transporteur.
Historique
7 oct.   Groupage clôturé — Écouteurs filaires (32 commandes)   +128 000 F CFA
7 oct.   Frais Group Achat — à retenir au retrait                −1 500 F CFA
28 sept. Retrait — Baskets homme (41 commandes)                 +400 300 F CFA
28 sept. Frais Group Achat — retenus                             −1 500 F CFA
20 sept. Groupage annulé — Savon de Marseille                   Aucun frais
Voir mes statistiques
Démonstration — aucun mouvement de fonds réel.
```

### 19 — Fil des demandes

```
Demandes des acheteurs
Mon quartier   Toutes   Cette semaine
Huile de palme 20 L
32 personnes · Agoè · prix souhaité ~11 000 F CFA
Lancer un groupage
```

### 20 — Questions reçues

```
Questions          3 sans réponse
Sans réponse (3)   Toutes
Écouteurs filaires Pro avec micro
  Est-ce qu'on peut payer à la livraison ? — Dodzi M.
  Répondre
Une réponse publique profite à tous vos participants et rassure les visiteurs.
Avertissement, première réponse :
Vos réponses sont publiques.
Ne communiquez jamais votre numéro, votre adresse ou un lien vers un autre service.
Les acheteurs paient sur Group Achat, et c'est ce qui vous garantit d'être payé à la clôture.
J'ai compris
```

### 21 — Statistiques

```
Mes statistiques
30 jours   3 mois   Tout
Vos revenus — 30 jours
668 100 F CFA nets
+ 18 % par rapport aux 30 jours précédents
Groupages aboutis   4 sur 5
Participants        127        + 31 %
Panier moyen        4 150 F CFA   − 4 %
Taux de réussite    80 %
Revenus par groupage
Baskets homme        400 300 F CFA
Huile de palme       141 300 F CFA
Écouteurs filaires   126 500 F CFA
Savon de Marseille   annulé
D'où viennent vos commandes
Agoè 38 (30 %)   Tokoin 29 (23 %)   Bè 24 (19 %)
Ce que ça vous dit
Vos groupages d'électronique aboutissent plus souvent que vos groupages alimentaires.
Votre panier moyen baisse depuis deux mois.
Voir mon portefeuille
Vide : Vos statistiques apparaîtront ici après votre premier groupage.
```

---

## Hors application

### 22 — Tournée du livreur *(page web)*

```
Group Achat — Livraisons        7 octobre
3 livrées sur 12
Akosua D.
Tokoin, rue des Cocotiers, près de la pharmacie Sodji
+228 90 12 34 56        Appeler
Écouteurs filaires Pro avec micro — 1 part
Code de livraison
[  ][  ][  ] - [  ][  ][  ]
Valider la livraison        Colis refusé
Livrée à 10 h 32
Code incorrect — vérifiez auprès de l'acheteur
```

### A1 — Tableau de bord administrateur *(1 280 × 800)*

```
Changement de compte Mobile Money — Mama Gro        Voir le dossier
Dossiers KYC à valider              4   le plus ancien : 2 jours
Justificatifs d'achat à contrôler   2   le plus ancien : 1 jour
Contestations à arbitrer            1   le plus ancien : 4 jours
Livraisons non confirmées (7 j)     3   le plus ancien : 9 jours
Messages signalés                   6   le plus ancien : 1 jour
Retours de colis                    0
Argent détenu pour les groupeurs  1 284 000 F CFA
   Rapprochement : écart de 0 F
Groupages en cours             11   dont 3 à échéance sous 48 h
Taux de livraison (30 j)       94 %
Frais encaissés (30 j)         18 000 F CFA   12 groupages aboutis
Activité récente
```

---

## 4. Ce qu'il faut prototyper dans Figma

Un enchaînement cliquable vaut dix écrans statiques. Quatre parcours :

1. **Commander :** 1 *(glisser 2 ou 3 cartes)* → 3 → 5 → **[feuille 4A → 4B]** → 6 → *(attente de validation)* → 7 → 8 → 9
2. **Livraison :** 9 en état *en cours de livraison* → code affiché → 9 en état *livrée*
3. **Groupeur :** 13 → 16 → *(je passe la commande)* → 17A → *(validé)* → 18
4. **Demande :** 11 → *(confirmation)* → 12, puis 19 → 14
5. **Livraison :** 21 → *(code saisi)* → succès → retour à la liste avec la progression qui avance, puis l'écran 9 de l'acheteur passé en *livrée*

Six détails qui font la différence devant un jury :

- le **défilement du fil** sur au moins trois cartes, dont une vidéo ;
- le **parcours libre jusqu'au paiement**, sans jamais demander de compte ;
- la **reprise de l'action après connexion** : la feuille redescend, le paiement continue ;
- l'**attente de validation Mobile Money**, qui est l'étape réelle du paiement ;
- l'**écran de décision du groupeur** (16), avec son compte à rebours et le montant qu'il pourra retirer ;
- la **validation d'un code par le livreur** (écran 22), qui est la preuve de livraison et ce qui alimente l'historique de fiabilité du groupeur ;
- au moins un **cas d'erreur** cliquable — le reçu refusé à l'écran 17 est le plus parlant.

## 5. À vérifier avant de présenter

- [ ] Aucun *Lorem ipsum*, aucun « Produit 1 » sur aucun écran.
- [ ] Les montants concordent : **4 000 F la part = 4 000 F payés** *(aucun frais de livraison)*, 128 000 F collectés, 1 500 F de frais Group Achat, **126 500 F retirables par le groupeur**.
- [ ] **Aucun écran n'affiche une ligne « Livraison » chiffrée** tant que les frais sont nuls — ni « 0 F », qui se lit comme un oubli.
- [ ] **La mention « frais de livraison réglés au livreur à la remise » figure sur l'écran 5, l'écran 6 et l'écran 7.** Sans elle, l'acheteur découvre la dépense à sa porte.
- [ ] Le montant est **4 000 F partout** : le total payé est le prix de la part, du fil jusqu'au détail de la commande.
- [ ] **La grille dégressive, là où il y en a une**, est un tableau de prix — **jamais** un prix barré ni une pastille de pourcentage (§3). Elle s'affiche sur la fiche (écran 3) et le prix suit la quantité à l'écran 5.
- [ ] Sous le sélecteur de quantité, la phrase dit **ce qu'il reste à faire** — « à partir de 5 parts, la part passe à 3 500 F » — et **jamais ce qu'on « rate »**.
- [ ] La ligne de frais de livraison est **distincte**, jamais fondue dans le prix de la part.
- [ ] **Aucun écran ne promet que l'argent est bloqué jusqu'à la livraison** (§1.7) — le groupeur est payé à la clôture.
- [ ] **Aucun encart bleu sur un écran acheteur** : le `BandeauConfiance` a été supprimé et les encarts `info` sont neutres. Seule la coche « vérifié » du pseudonyme reste bleue.
- [ ] **Aucun écran n'écrit que Group Achat détient l'argent.** La formulation est « votre paiement va au portefeuille du groupeur, qui ne peut le retirer qu'à la clôture ».
- [ ] L'avertissement « vérifiez votre commande devant le livreur » figure sur les écrans 3, 7 et 9.
- [ ] **Aucun contact de groupeur sur un écran acheteur**, et **aucun numéro d'acheteur sur un écran groupeur**.
- [ ] **Le pseudonyme du groupeur n'est cliquable nulle part**, et aucune page de profil n'existe.
- [ ] Le message « créez un compte » **ne s'affiche jamais à l'ouverture** : seulement sur « Rejoindre » et sur « Poser une question », et il dit **pourquoi**, avec une raison propre à chacune (§1.5).
- [ ] L'inscription est en **bouton plein**, la connexion en **lien discret** — jamais deux boutons pleins côte à côte (§1.5).
- [ ] La feuille d'inscription a son **indicateur de deux étapes**, et l'étape est aussi annoncée **en texte masqué** pour un lecteur d'écran.
- [ ] Un **numéro déjà inscrit** ouvre un encart « Se connecter plutôt », et pas un simple message d'erreur sous le champ.
- [ ] L'étape du mot de passe porte le lien « **Mot de passe oublié ? Recevoir un code par SMS** » — c'est tout le parcours de récupération.
- [ ] Le **courriel est marqué « (facultatif) »** partout où il apparaît, et il ne sert jamais à se connecter.
- [ ] L'onglet Profil sans compte propose « **Créer mon compte** », pas « Voir les campagnes ».
- [ ] **Aucun groupage clôturé, livré ou annulé dans le catalogue** : ni sur le fil, ni dans la recherche, ni dans une catégorie, ni dans le compteur de résultats (écran 2).
- [ ] Le temps restant est un **badge** — fond teinté, liseré, icône horloge — et son libellé est une phrase : « Il reste 3 jours », **jamais en capitales**.
- [ ] Sous un jour, le badge compte en **heures** : « Il reste 4 h », jamais « il reste 0 jour ».
- [ ] Sur écran large, **l'en-tête, le pied de page et le contenu s'alignent sur les mêmes bords** : un seul plafond `largeur-page`, et la page ne saute pas d'un écran à l'autre.
- [ ] Aucune ligne de texte ne dépasse ~672 px, et aucun bouton ne s'étire sur toute la largeur du conteneur.
- [ ] La barre de progression du §2.5 est présente sur le fil, les cartes, les lignes et le détail, et elle porte **le chiffre écrit à côté**, jamais la barre seule.
- [ ] Aucune mention de « places disponibles », de « complet », ni de « il manque N personnes » : l'objectif n'est ni un plafond ni un minimum.
- [ ] Un groupage qui dépasse son objectif montre une barre **pleine** et le nombre réel — « 24 acheteurs », pas « 24 sur 20 » tronqué à 20.
- [ ] Le fil a son **état image seule** et son **mode économie de données** dessinés.
- [ ] Le son des vidéos est **coupé par défaut**, avec son icône visible.
- [ ] Chaque liste a son état vide, et les onglets protégés leur variante « non connecté ».
- [ ] L'écran 17 a son état **refusé**.
- [ ] Le **bandeau de démonstration** est présent sur les écrans 6 et 18.
- [ ] L'écran 22 existe, avec ses états **code refusé**, **code non présenté** et **colis refusé**.
- [ ] L'écran 22 n'affiche **aucun montant**, et le numéro de l'acheteur n'apparaît nulle part ailleurs.
- [ ] **Nulle part de texte blanc sur `marque` `#FF6A00`** (2,87:1). Les boutons pleins sont en `primaire` `#CC4A00`.
- [ ] `marque` n'apparaît qu'avec du texte ou une icône sombre : compteur du fil, statut « en cours de livraison », bouton flottant, barre de progression.
- [ ] **Écrans acheteur (1 à 12) : chrome orange, et **aucun** élément bleu.** ⚠️ Cette ligne en tolérait un par écran — *« le bandeau de confiance ou un statut argent détenu »*. Le `BandeauConfiance` a été supprimé (§2.6) et les encarts `info` sont passés au neutre. **Seule exception : la coche « vérifié » de 13 px** à côté d'un pseudonyme — c'est une marque, pas une boîte de réassurance.
- [ ] **Écrans groupeur (13 à 20) : chrome bleu.** Au plus un bloc orange par écran, et c'est une urgence. Aucun bouton ni onglet actif orange.
- [ ] Les statuts « argent détenu » passent en **neutre** sur les écrans groupeur.
- [ ] **Nulle part de texte orange sur un aplat bleu** (3,61:1) — une pastille pleine, oui ; du texte courant, non.
- [ ] Typographie, fond blanc, rayons, espacements et ton des textes **strictement identiques** des deux côtés : c'est tout ce qui reste pour tenir la cohérence de marque.
- [ ] **Le fond est blanc sur tous les écrans**, le fil excepté (§1.0).
- [ ] **Aucune ombre**, sauf sur le bouton ancré, la feuille de connexion et le bouton flottant.
- [ ] Les listes sont des **lignes séparées par un filet**, pas des cartes encadrées.
- [ ] Le gris `surface-douce` n'apparaît que dans ses trois usages autorisés.
- [ ] **Un seul bouton primaire par écran.**
- [ ] Aucun élément purement décoratif, aucune illustration de remplissage.
- [ ] Le **bandeau partenaires** porte la mention « Sponsorisé », n'affiche **ni prix ni bouton « Commander »**, et sa variante **sans annonceur** fait disparaître le bandeau.
- [ ] Un lien publicitaire externe passe par la confirmation « Vous quittez Group Achat ».
- [ ] Le média du fil est bien calculé à **600 px**, bandeau compris.
- [ ] Chaque écran répond en une seconde à : où suis-je, que puis-je faire, combien ça coûte.
- [ ] Tous les textes de bouton sont des verbes d'action, pas « OK » ni « Valider » seul.
- [ ] **Aucun prix barré, aucune pastille de pourcentage, aucun « au lieu de »** nulle part (§3).
- [ ] L'article de démonstration est l'**écouteur filaire à 4 000 F**, et les additions tombent juste : 32 × 4 000 = 128 000 F, moins 1 500 F de frais = **126 500 F retirables**.
- [ ] L'écran 21 a son **état vide dessiné**, et il ne montre **ni nom d'acheteur, ni classement entre groupeurs**.
- [ ] L'écran 14 saisit le **prix pour 1 pièce**, et les paliers de quantité affichent leur prix unitaire calculé.
- [ ] **Aucune ligne « Livraison » dans un récapitulatif acheteur**, et **aucun montant de livraison nulle part** — pas même un « à partir de ». Le total est **exactement le prix de la part**, connu dès l'ouverture de l'écran (§3).
- [ ] `MENTION_LIVRAISON` apparaît sur les **trois** écrans où l'acheteur voit un total — commande, paiement, confirmation — et **nulle part elle n'est recopiée à la main** (§2.6).
- [ ] **Sur téléphone, la recherche est une loupe**, pas un champ permanent. Elle se déplie au toucher et la fermeture efface le filtre (écran 1).
- [ ] **L'écran A1 ne s'ouvre pas sans mot de passe** : feuille de connexion identifiant + mot de passe, **un seul message d'erreur pour les trois causes de refus**, verrou de 15 minutes au cinquième échec, et le pied de la barre latérale dit **qui signera les décisions KYC** (§A1.0).
