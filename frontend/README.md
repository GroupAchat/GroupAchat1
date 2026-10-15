# Front React — Group Achat

Le parcours d'achat du PRD, codé : **voir les groupages, payer sa part,
recevoir son code de livraison**. Le reste du dépôt reste documentaire ; les
quatre documents de la racine font foi, et ce dossier les applique.

```bash
npm install

npm run dev          # La boutique       — http://localhost:5173
npm run dev:admin    # L'administration  — http://localhost:5174

npm run typecheck
npm run build        # Construit les deux : dist/ et dist-admin/
```

Le **site de présentation** est servi par la boutique, sur
<http://localhost:5173/presentation/> — il n'a ni port ni service à lui. Il vit dans
`public/presentation/`, écrit en HTML et CSS simples, sans construction ni dépendance : Vite le
recopie tel quel dans `dist/`. Voir [PRESENTATION.md](PRESENTATION.md).

⚠️ **`public/` appartient à la boutique seule.** `vite.admin.config.ts` déclare son propre
`publicDir` (`public-admin/`, qui ne contient que le favicon) : sans cela, l'administration
embarquerait le site de présentation en entier, et `localhost:5174/presentation/` l'aurait servi
depuis le port de l'outil interne.

**Ce sont deux applications et deux ports**, a lancer dans deux terminaux. La
boutique porte l'acheteur, le groupeur et le livreur ; l'administration porte
le seul ecran A1. Les deux partagent le design system, les jetons de couleur et
le dossier `domaine/`, mais **pas le meme paquet** : `vite.config.ts` et
`vite.admin.config.ts` nomment chacun leur entree, de sorte que le code
d'administration — montants detenus, files de travail, libelles d'alertes — ne
part pas dans la construction telechargee par un acheteur de Lome.

| | Boutique | Administration |
|---|---|---|
| Commande | `npm run dev` | `npm run dev:admin` |
| Port | **5173** | **5174** |
| Page | `index.html` | `admin.html` |
| Configuration | `vite.config.ts` | `vite.admin.config.ts` |
| Entree React | `src/main.tsx` | `src/admin/main.tsx` |
| Construction | `dist/` | `dist-admin/` |

Les frontieres sont tenues en developpement : `/admin.html` repond **404** sur
le port 5173, et la racine du port 5174 sert l'administration et non la
boutique. ⚠️ **Ce n'est pas une mesure de securite** — l'administration s'ouvre
encore sans mot de passe sur son propre port, et le fera jusqu'au branchement
de l'authentification. Le vrai controle d'acces est celui de l'admin Django
(§13.6), qui demande un compte.

## Trois architectures, pas une feuille de style

La bascule est dans `src/hooks/useEstBureau.ts`, à **768 px**.

| | < 768 px | 768 à 1023 px | ≥ 1024 px |
|---|---|---|---|
| Ouverture | Page de démarrage, puis **le fil** | **Le catalogue** | **Le catalogue** |
| Navigation | `BarreNav` en bas | En-tête de site, pied de page | En-tête de site, pied de page |
| Résultats | Des **lignes** (§2.3) | Grille de **2 cartes** | Grille de **3 cartes** |
| Filtres | Puces défilantes | Puces défilantes | Colonne latérale |
| Fiche produit | Une colonne, bouton ancré | Une colonne | **Deux colonnes**, bloc d'achat collé |
| Tunnel d'achat | Pleine largeur, bouton ancré | Colonne centrée | Colonne centrée |

**Le fil n'existe pas au-delà du téléphone**, et ce n'est pas qu'une question
de goût. Le défilement vertical carte par carte est un geste de pouce : à la
molette, chaque cran saute un produit entier. Surtout, quelqu'un qui arrive sur
un site marchand depuis un ordinateur vient chercher, comparer et acheter — il
attend un catalogue, des filtres et une fiche produit.

Le composant `Fil` n'est donc **pas monté** au-delà de 768 px, pas seulement
caché : un fil masqué en CSS télécharge quand même ses dix photos et garde ses
écouteurs de défilement. Même raison pour la `BarreNav` et la page de
démarrage — un site ne s'ouvre pas sur un logo plein écran.

Le §2.3 impose une ligne plutôt qu'une carte, pour deux raisons explicites :
sur fond blanc une carte blanche n'existe pas, et une liste de lignes défile
mieux sur un Android d'entrée de gamme. **Les deux arguments tombent sur une
grille de bureau**, où il faut bien délimiter des colonnes voisines. La ligne
reste donc la forme mobile et la carte la forme bureau ; le §2.3 gagnerait à
distinguer les deux cas.

## La page d'accueil du site (≥ 768 px)

De haut en bas :

1. **En-tête** — logo, barre de recherche, bouton « Demander », bouton de
   notifications. Rien d'autre ;
2. **Section publicité** — le `BandeauPartenaires` du §2.14 : trois bannières
   illustrées qui **défilent toutes seules** toutes les 5 s, avec des
   annonceurs et des visuels **fictifs** (`donnees/annonceurs.ts`) ;
3. **« Se termine bientôt »** — les groupages à moins de 48 h de la clôture,
   en carrousel ;
4. **« Les autres groupages »** — le reste, en carrousel ;
5. **« Tous les groupages ouverts »** — la grille complète, avec la colonne de
   filtres ;
6. **Pied de page**.

Le partage entre les deux carrousels se fait sur le **même seuil de 48 h** que
la puce « Se termine bientôt » du filtre : deux seuils différents pour la même
idée seraient un piège à incohérence.

**Dès qu'une recherche ou un filtre est actif, la publicité et les deux
carrousels disparaissent** et la grille prend toute la place. Quelqu'un qui a
tapé « riz » veut ses résultats, pas deux carrousels à faire défiler avant de
les atteindre.

**Les deux carrousels de produits ne tournent pas tout seuls** — seules les
bannières publicitaires le font. Les flèches disparaissent en bout de course
plutôt que de rester grisées : une flèche grisée est un bouton qui ment.

### La rotation automatique des bannières

C'est un **écart assumé avec le §2.14**, qui écrit « pas de rotation
automatique : un contenu qui bouge seul au-dessus d'un fil qu'on fait défiler
est désagréable et empêche de toucher ce qu'on visait ». La demande est
explicite et postérieure, donc elle s'applique — mais la gêne décrite est
réelle, et quatre garde-fous la ramènent à peu de chose :

- la rotation **s'arrête au survol et au focus clavier**, donc elle ne dérobe
  jamais la cible d'un clic en cours ;
- elle **s'arrête définitivement dès qu'on fait défiler ou qu'on clique une
  pastille** : un geste de l'utilisateur l'emporte sur l'automatisme ;
- elle **ne démarre pas** si le système demande à réduire les animations ;
- elle **se met en pause quand l'onglet est en arrière-plan**, pour ne pas
  faire tourner une minuterie dans le vide sur un forfait limité.

Le §2.14 est à corriger, sans quoi il contredit l'écran construit.

Deux règles du §2.14 que la section publicité tient quand même : la mention
« Sponsorisé » est affichée (obligation de loyauté, pas option de mise en
page), une vignette ne porte **ni prix ni bouton « Commander »** — le type
`Annonceur` n'a aucun champ pour en mettre — et s'il n'y a aucun annonceur, le
bandeau **disparaît entièrement** plutôt que d'afficher « Votre publicité ici ».

## L'architecture

Le code est rangé selon **deux axes**, décrits dans
**[ARCHITECTURE.md](ARCHITECTURE.md)**.

**Par rôle d'abord** : `acheteur/`, `groupeur/`, `admin/` et `livreur/`
contiennent chacun tout ce qui n'intéresse que ce public — son routeur, ses
pages, ses composants, son chrome. **Par couche ensuite**, à l'intérieur de
chaque rôle et à la racine pour ce qui est partagé : `domaine/` (les règles,
sans React), `donnees/` (les jeux de démonstration), `ui/` (le design system du
§2), `composants/`, `mise-en-page/` et `pages/`.

Les deux règles tiennent en deux lignes : **un rôle n'importe jamais un autre
rôle**, et **une couche ne connaît que celles qui sont en dessous d'elle**.

Les écarts assumés avec la spec sont signalés par `⚠️` dans le code :

```bash
grep -rn "⚠️" src/
```

## Les écrans

| Écran | Fichier | Spec |
|---|---|---|
| 0 — Page de démarrage *(téléphone seulement)* | `pages/PageDemarrage.tsx` | — |
| 1 — Le fil, un groupage par écran *(téléphone seulement)* | `acheteur/pages/Fil.tsx` | écran 1 |
| 2 — Groupages ouverts (liste, recherche, filtres, tri) | `acheteur/pages/GroupagesOuverts.tsx` | écran 2 |
| 3 — Détail d'un groupage | `acheteur/pages/DetailGroupage.tsx` | écran 3 |
| 4 — Connexion (feuille remontante) | `acheteur/composants/FeuilleConnexion.tsx` | écran 4 |
| 5 — Commander : quantité, position, récapitulatif | `acheteur/pages/Commander.tsx` | écran 5 |
| 6 — Paiement Mobile Money simulé | `acheteur/pages/Paiement.tsx` | écran 6 |
| 7 — Confirmation et code de livraison | `acheteur/pages/Confirmation.tsx` | écran 7 |
| 8 — Mes commandes | `acheteur/pages/MesCommandes.tsx` | écran 8 |
| 9 — Détail d'une commande et suivi | `acheteur/pages/DetailCommande.tsx` | écran 9 |
| 10 — Questions publiques et modération | `acheteur/pages/Questions.tsx` | écran 10 |
| 11 — Demander un produit | `acheteur/pages/DemanderProduit.tsx` | écran 11 |
| 12 — Mes demandes | `acheteur/pages/MesDemandes.tsx` | écran 12 |
| **Profil** *(4e onglet : mes informations, mes demandes, économie de données, aide)* | `acheteur/pages/Profil.tsx` | écran 1, « les onglets » — « 12 et réglages » |

### Côté groupeur — chrome **bleu** (§1.2)

| Écran | Fichier | Spec |
|---|---|---|
| 13 — Tableau de bord | `groupeur/pages/TableauDeBord.tsx` | écran 13 |
| 14 — Créer une campagne (3 étapes) | `groupeur/pages/CreerCampagne.tsx` | écran 14 |
| 15 — Gérer une campagne | `groupeur/pages/GererCampagne.tsx` | écran 15 |
| 16 — Clôturer et décider | `groupeur/pages/Decision.tsx` | écran 16 |
| 17 — Déposer un justificatif | `groupeur/pages/Justificatif.tsx` | écran 17 |
| 18 — Portefeuille | `groupeur/pages/Portefeuille.tsx` | écran 18 |
| 19 — Fil des demandes | `groupeur/pages/FilDemandes.tsx` | écran 19 |
| 20 — Questions reçues | `groupeur/pages/QuestionsRecues.tsx` | écran 20 |
| 21 — Statistiques | `groupeur/pages/Statistiques.tsx` | écran 21 |

### Les deux autres publics

| Écran | Fichier | Spec |
|---|---|---|
| 22 — Tournée du livreur *(page web isolée)* | `livreur/pages/TourneeLivreur.tsx` | écran 22 |
| A1 — Administration *(1 280 × 800, chrome neutre)* | `admin/pages/TableauDeBordAdmin.tsx` | écran A1 |

**Les 23 écrans de la spec sont construits.**

## Le parcours d'ouverture

```
Page de démarrage  →  Choix du profil  →  « Je veux acheter »        → le fil
   (téléphone)         (téléphone)         « Je veux être groupeur »  → inscription → tableau de bord
```

**Sur grand écran, ni démarrage ni choix de profil** : un site marchand ne
s'ouvre ni sur un logo plein écran ni sur une question, il s'ouvre sur son
catalogue. Les deux sont des usages d'application mobile.

### Le choix du profil est en tension avec le §1.5

Le §1.5 demande qu'on arrive **directement** sur le fil à la première
ouverture, et range « un écran Connexion / Inscription au lancement » parmi les
trois choses à ne jamais dessiner. La demande est explicite et postérieure,
donc elle s'applique — mais la raison du §1.5 reste vraie, et trois conditions
empêchent cet écran de devenir le mur qu'il interdit :

- **le chemin acheteur ne demande rien** : un appui, et on est sur le fil. Pas
  de compte, pas de numéro, pas de mot de passe. Ce n'est pas un mur
  d'authentification, c'est un aiguillage ;
- **il est proposé en premier et en bouton plein**, l'autre en contour ;
- **il n'apparaît qu'une fois.**

Si l'un des trois saute, l'écran redevient le mur du §1.5. Le §1.5 est à
corriger pour acter l'aiguillage.

### L'inscription d'un groupeur

Quatre étapes, et **seulement le niveau « Entrée » du KYC** (§10.5 du cahier
des charges) : pièce d'identité avec selfie, concordance du compte Mobile
Money, téléphone vérifié. Plafond 150 000 F par campagne. Les références, le
lieu d'activité et le contrat viennent au niveau Confirmé, après trois
campagnes livrées — demander tout dès la première minute ferait fuir les
commerçants de l'informel, qui sont le cœur de cible.

**Le contrôle n° 2 arrête la procédure** : si le nom du titulaire du compte
Mobile Money ne correspond pas à la pièce d'identité, on ne continue pas. La
comparaison tolère l'ordre des mots, la casse et les accents, et le refus est
signalé **à la saisie** plutôt que quatre heures plus tard.

## Les quatre publics, et comment passer de l'un à l'autre

Group Achat n'est pas une application mais **quatre**, qui partagent un design
system et une base de données — mais **pas le même port** :

| Rôle | Écrans | Chrome | Port | Comment on y entre, en vrai |
|---|---|---|---|---|
| **Acheteur** | 0 à 12 | Orange | 5173 | On ouvre le site, on répond à l'écran de profil |
| **Groupeur** | 13 à 21 | **Bleu** | 5173 | Même porte, puis inscription et dossier KYC |
| **Livreur** | 22 | Neutre, page isolée | 5173 | On ouvre un lien reçu le matin |
| **Administration** | A1 | **Neutre**, 1 280 × 800 | **5174** | On passe par l'admin Django |

**L'acheteur et le groupeur sont sur le même port, et c'est voulu** : c'est le
même public, et le passage de l'un à l'autre est le mouvement que le produit
cherche — un acheteur satisfait devient groupeur. L'écran de choix de profil
(`pages/ChoixProfil.tsx`) les départage à la première visite, et **ne revient
pas** : `domaine/profil.ts` retient le choix dans `localStorage`.

**L'administration est à part, et c'est voulu aussi** : personne ne passe
d'acheteur à administrateur. Elle n'est plus un rôle du sélecteur de
démonstration, qui n'en donne que l'adresse. Les trois raisons de cette
séparation sont détaillées dans l'en-tête de `src/admin/main.tsx`.

Le **sélecteur en bas à gauche** existe pour la démonstration, et uniquement
pour elle : il permet de sauter d'un rôle à l'autre et de **rejouer l'écran de
choix de profil**, sans quoi le revoir demanderait de vider les données de site
du navigateur à la main. Il est à retirer au branchement de
l'authentification.

⚠️ **Le choix de profil est désormais demandé sur ordinateur aussi**, alors
qu'il était sauté au-delà de 768 px. Ce changement répare un trou réel — sur
grand écran il n'existait aucun chemin vers le côté groupeur hors du sélecteur
de démonstration — mais il étend au bureau la tension avec le §1.5, qui
demande qu'on arrive **directement** sur le catalogue. Voir l'en-tête de
`src/App.tsx` pour les trois conditions qui bornent cet écart.

Les composants du design system portent un axe `role` (`ui/chrome.ts`) pour
que le chrome soit un paramètre et non une relecture. **Ne jamais les
inverser** : un écran groupeur avec un bouton orange, ou un écran acheteur avec
un onglet actif bleu, casse le seul repère permanent qu'ont les deux publics.

`acheteur/ApplicationAcheteur.tsx` et `groupeur/ApplicationGroupeur.tsx`
enchaînent leurs écrans sans bibliothèque de routage : quatre écrans
n'ont pas besoin d'un routeur, et chaque kilo-octet compte sur l'Android
d'entrée de gamme du §5 du cahier des charges. L'écran 5 reste monté pendant la
connexion, ce qui est la seule façon de tenir la promesse du §1.5 — fermer la
feuille ramène à l'écran **intact**.

## Le reste du dossier

| Chemin | Rôle |
|---|---|
| `src/index.css` | Les jetons de couleur du §1.2, en variables Tailwind v4. Aucune couleur n'est écrite en dur ailleurs |
| `src/domaine/format.ts` | Montants (« 4 000 F CFA »), dates, et temps restant (« Il reste 2 jours ») avec les seuils d'urgence du §2.4 |
| `src/domaine/livraison.ts` | Frais de livraison et code de livraison. La fonction de frais **renvoie 1 000 F pour toute position** — c'est écrit tel quel dans la spec, et c'est la seule constante à changer le jour du vrai calcul |
| `src/donnees/groupages.ts` | Les **seize** groupages fictifs. C1 à C4 sont ceux du jeu canonique du §3, chiffres compris ; C6 à C17 sont des ajouts |
| `src/ui/` | Le design system, qui ne connaît aucune notion métier : `Bouton` (§2.7), `Champ` (§2.9), `Encart` (§2.11), `Statut` (§2.8), `FriseEtapes` (§2.13), `EtatVide` (§2.12), `Carrousel`, `FeuilleRemontante`, `Icones`, `Logo`, `chrome.ts` |
| `src/acheteur/composants/` | `LigneGroupage` (§2.3), `CompteurTemps` (§2.4), `CompteurParticipants` (§2.5), `BandeauConfiance` (§2.6), `CodeLivraison` (§2.10), `BandeauPartenaires` (§2.14), `CarteGroupage`, `RechercheEtFiltres` (écran 2), `PanneauFiltres`, `FeuilleConnexion` |
| `src/acheteur/mise-en-page/` | `BarreNav` (§2.2), `EnTeteApplication`, `EnTeteEcran`, `EnTeteBureau`, `PiedPage` |
| `src/composants/` | Les composants métier partagés par plusieurs rôles. Il n'y en a qu'un : `Vignette` |

## Charte

Polices **Jost** pour les titres et les montants, **Poppins** pour le texte
courant, chargées depuis Google Fonts avec les seules graisses utilisées et
`display=swap`. Roboto reste en secours : il est déjà sur tout Android, donc la
page est lisible avant que les polices n'arrivent.

Le logo existe en quatre déclinaisons, dans `src/assets/` :

| | `cote` (158 × 35) | `haut` (307 × 177) |
|---|---|---|
| `couleur` | en-têtes sur fond blanc | page de démarrage claire |
| `blanc` | sur un média sombre | page de démarrage sur aplat orange |

`ui/Logo.tsx` les expose sous un seul composant. La version `blanc` est
monochrome : elle veut un fond foncé ou un aplat de couleur, jamais du blanc.
Les fichiers gardent leurs propres teintes (`#FE6C00`, `#1F3B8D`), très
légèrement différentes des jetons `marque` et `confiance` — un logo n'est pas un
composant d'interface, on ne le repeint pas pour le faire entrer dans une
palette.

Les quatre SVG sont **intégrés au paquet sous forme de données**
(`assetsInlineLimit` dans `vite.config.ts`) : le logo s'affiche avec la page,
sans requête. C'est ce qui permet à la page de démarrage de ne jamais
apparaître vide. Coût mesuré : environ 9 ko gzip pour les quatre.

## La page de démarrage

Fond `primaire` `#CC4A00`, logo blanc en disposition `haut`, accroche, puis le
fil. **Le fond n'est pas `marque` `#FF6A00`** : le logo blanc n'y contrasterait
qu'à 2,87:1, et le §1.2 l'interdit sans exception — le nom de la marque reste
du texte. Sur `primaire`, le blanc tient à 4,62:1. Les deux oranges se
ressemblent à l'œil ; un seul se lit au soleil de Lomé.

Elle **ne bloque personne** : elle disparaît seule après 1,4 s et un appui la
passe. C'est à cette condition qu'elle ne tombe pas sous l'interdiction du §1.5
(ni écran de connexion, ni tutoriel bloquant à l'ouverture). Elle ne doit jamais
devenir l'endroit où l'on explique le produit — le fil s'en charge en trois
secondes. L'animation se désactive si le système demande à réduire les
animations.

## Les photos produit

Ce sont des photos de banque d'images (Pexels), servies depuis leur CDN. Les
dix URL ont été vérifiées une à une, et le chargement des dix est vérifié dans
le navigateur.

**Elles sont approchantes, pas exactes** : le bidon d'huile de palme est une
huile de cuisine, le carton de lait est un verre de lait. Elles tiennent pour
une démonstration, pas pour une mise en ligne — un acheteur qui reçoit autre
chose que la photo a raison de se plaindre. À remplacer par les photos réelles
des groupeurs (§1.8).

## Ce qui est simulé, et dit comme tel

Le paiement et le SMS. Les deux écrans le **disent à l'écran** plutôt que de le
laisser découvrir : bandeau « Démonstration — aucun paiement réel n'est
effectué » en haut de l'écran 6, et le code de démonstration affiché sous les
quatre cases de l'écran 4. Notre argument est la sécurité de l'argent ; nous
nous jugeons d'abord sur notre franchise.

En revanche l'étape « Validez le paiement sur votre téléphone » n'est pas une
fiction : c'est le déroulement réel d'un paiement Mobile Money, et l'omettre
obligerait à redessiner le parcours le jour du branchement de l'agrégateur.

## Ce qui n'y est pas encore

Pas d'appel réseau : les données sont une constante, que remplacera
`GET /api/campagnes/?statut=ouverte` servie par Django/DRF. Les champs de
`Groupage` et de `Commande` sont nommés comme ceux du §6 du PRD pour que la
bascule soit un `fetch`.

Pas de géocodage inverse : aucune fonction ne sait traduire des coordonnées en
quartier de Lomé. L'écran 5 renvoie donc Tokoin après un partage de position,
et l'acheteur peut corriger. C'est documenté dans le fichier, parce que mentir
sur ce point se verrait au premier essai depuis un autre quartier.

Les photos produit manquent (`medias/` n'existe pas encore, §1.8). `Vignette`
tient la place exacte de la photo et affichera l'image dès que le champ `photo`
sera renseigné dans les données.
