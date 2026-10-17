# Group Achat — cahier des charges

> Version : 1.7 — l'administrateur, troisième rôle
> Lomé, Togo · interface en français · **web aujourd'hui, mobile pour le grand public**
> Légende : **À définir** = volontairement vide. *(proposition)* = à valider par toi.
> Documents liés : [contenu des écrans pour Figma](SPEC_ECRANS_FIGMA.md) — [le partenariat de livraison](LIVRAISON.md)

---

## 1. Contexte et problème

Au Togo, les achats groupés existent déjà, mais ils vivent dans des **groupes WhatsApp** qui posent deux problèmes distincts :

**Pour l'acheteur, un problème de fiabilité.** Il verse de l'argent à quelqu'un qu'il ne connaît pas, sans garantie, sans recours, et sans moyen de savoir si cette personne a déjà livré ou disparu avec une caisse.

**Pour l'acheteur, un problème de choix.** Un groupe WhatsApp ne montre que ce que son animateur publie. L'offre est limitée à un organisateur, un cercle, un moment. Rien ne permet de voir tout ce qui est en groupage à un instant donné.

**Pour le groupeur, un problème de visibilité.** Il ne vend qu'à son carnet d'adresses. Son marché s'arrête aux membres de son groupe, alors que sa capacité à négocier, elle, ne s'arrête pas là.

## 2. Solution

**Group Achat réunit au même endroit les campagnes de groupage et les groupeurs que nous avons nous-mêmes sélectionnés.**

- L'acheteur **gagne en fiabilité** : il ne traite plus avec un inconnu, il commande sur une plateforme qui a choisi ses groupeurs et qui détient l'argent.
- Le groupeur **gagne un marché** : il n'est plus limité à son groupe WhatsApp, il est exposé à toute la demande de Lomé.
- La plateforme **retient 1 500 F sur chaque groupage abouti**, au moment où le groupeur retire son argent.

La plateforme n'achète pas, ne stocke pas et ne négocie pas. Elle **rassemble l'offre, encaisse, sécurise et organise la livraison**.

## 3. Ce qui nous distingue

| L'existant | Ce qu'il fait | Ce qui manque |
|---|---|---|
| Groupes WhatsApp | Groupages informels | Offre limitée à un animateur, aucune fiabilité, aucun recours |
| Pages et comptes de vente sur les réseaux | Vente au détail | Pas de groupage, pas de prix de gros |
| Sites de e-commerce | Catalogue et livraison | Prix au détail, pas de mécanique de groupage |

**Notre force, c'est la sécurité.** Pas un algorithme, pas un catalogue : la certitude, pour l'acheteur, qu'il sera livré ou remboursé. Cette certitude repose sur deux choses indissociables :

1. **Des groupeurs vérifiés un par un** — nous ne laissons personne ouvrir une campagne (section 10.5) ;
2. **Un circuit de l'argent conçu pour qu'un groupeur ne puisse pas partir avec la caisse** (sections 10.1 à 10.4).

L'acheteur ne juge donc pas un groupeur : il fait confiance à Group Achat. C'est un engagement lourd — un seul groupeur défaillant abîme notre réputation, pas la sienne — et toute la section 10 existe pour le rendre tenable.

## 4. Objectifs

- Rassembler en un lieu toutes les campagnes de groupage ouvertes à Lomé.
- Permettre à un groupeur sélectionné de lancer une campagne en quelques minutes.
- Garantir à l'acheteur qu'il est livré ou remboursé.
- Faire naître l'offre à partir de la demande des acheteurs.
- Objectifs chiffrés (groupeurs, campagnes, volume) : **À définir**

## 5. Public cible

**Acheteurs :** toute personne à Lomé qui veut acheter au prix de gros sans gros budget — particuliers, ménages, petits commerçants, revendeuses. Pas de restriction de segment.

**Profil type retenu pour concevoir le MVP :** un adulte de Lomé, smartphone Android d'entrée de gamme, forfait data limité, habitué aux achats groupés WhatsApp et aux applications où l'on fait défiler des vidéos. Ce profil tranche les choix concrets, il n'exclut personne.

**Groupeurs :** personnes qui savent déjà sourcer et négocier — organisateurs de groupages, commerçants, importateurs à petite échelle. **Ils ne s'inscrivent pas librement : nous les recrutons.**

**Catégories de produits :** sans restriction — alimentaire, vêtements, chaussures, maison, hygiène, électronique.

## 6. Acteurs et rôles

| Acteur | Ce qu'il fait | Ce qu'il y gagne |
|---|---|---|
| **Visiteur** | Fait défiler les campagnes, cherche, consulte, pose des questions — sans compte | — |
| **Acheteur** | Commande une part dans une campagne, paie, suit, reçoit, peut contester à la livraison | La fiabilité : il est livré ou remboursé |
| **Groupeur** | Lance les campagnes, fixe le produit, le prix et le délai, décide si la commande passe, commande chez son fournisseur, répond aux questions | Un marché bien plus large que son carnet d'adresses |
| **Service de livraison partenaire** | Livre les acheteurs pour les groupeurs qui n'ont pas de livreur | Son tarif de livraison |
| **Annonceur** | Achète un emplacement dans le bandeau partenaires de l'accueil. **Pas un utilisateur de l'application** : son emplacement est saisi par l'administrateur | De la visibilité auprès des acheteurs |
| **Administrateur (nous)** | Recrute et vérifie les groupeurs, contrôle les justificatifs d'achat, arbitre les litiges, modère, **gère les emplacements publicitaires**. Ce n'est pas un spectateur : c'est l'opérateur dont dépend tout le circuit de l'argent — **§13** | Les frais de retrait et les emplacements |

**Sur le livreur.** Nous ne gérons pas de flotte et n'employons personne. Nous **passons un partenariat avec un service de livraison** et lui confions les livraisons des groupeurs qui n'ont pas leur propre livreur. Un groupeur qui a déjà son livreur peut l'utiliser. Le livreur n'est donc **pas un profil utilisateur de l'application** dans le MVP — c'est un prestataire, avec une conséquence importante traitée en section 11 : il faut quand même un moyen de prouver qu'il a livré.

## 7. Règles générales

1. **Aucune authentification au premier contact.** À la première ouverture, l'utilisateur arrive directement sur le fil des campagnes. Pas d'écran de connexion, pas de tutoriel bloquant.

   ⚠️ **Cette règle disait aussi « pas d'invitation à créer un compte ».** Il en existe une désormais, mais elle ne se déclenche **jamais à l'ouverture** : seulement quand l'utilisateur engage quelque chose, et elle explique pourquoi avant d'ouvrir le formulaire. La distinction est tout ce qui sépare une porte d'un péage.

2. **La connexion est déclenchée par l'opération, jamais par l'ouverture.** Elle n'est demandée qu'au moment où l'utilisateur engage quelque chose.

   | Reste libre, sans compte | Exige un compte |
   |---|---|
   | Faire défiler le fil, chercher, filtrer | **Rejoindre** un groupage |
   | Consulter une campagne, son prix, son délai | **Envoyer** une demande de produit |
   | Lire les questions et les réponses | **Poser** une question |
   | Choisir sa quantité et voir son total | Suivre ses commandes et ses demandes |

   ⚠️ **« Rejoindre » signifie l'ouverture de l'écran de commande, pas le bouton « Payer ».** Le compte est demandé un écran plus tôt qu'avant. Ce que ça coûte, franchement : quelqu'un venu d'un lien WhatsApp qui voudrait seulement *voir* les variantes et les frais de livraison vers son quartier doit maintenant se connecter d'abord. Ce que ça rend : l'écran de commande affiche des frais et pré-remplit une adresse, deux choses qui appartiennent à un compte — les demander à un inconnu, puis lui réclamer un code à l'écran suivant, faisait saisir son adresse avant de savoir qu'un compte serait nécessaire.

   **L'inscription est classique** : **prénom, numéro obligatoire, courriel facultatif**, puis vérification du numéro par code SMS. ⚠️ **Pas de mot de passe à l'inscription** — il se pose plus tard, depuis l'écran de profil, et sert alors à se reconnecter sans attendre de SMS. Un acheteur qui en a posé un entre par lui, ou par un code SMS s'il l'a oublié.

   ⚠️ **Ce paragraphe disait : « Le compte se crée par numéro de téléphone + code SMS. Pas de mot de passe, pas d'e-mail, pas d'inscription distincte de la connexion. »** C'est faux depuis que l'utilisateur a tranché pour l'inscription classique. La phrase est reproduite pour que personne ne la restaure en croyant réparer une régression — elle se trouve encore, sous d'autres formes, dans des commentaires du code.

   **La vérification du numéro par SMS reste, et il ne faut pas la retirer pour « faire plus classique ».** Le numéro *est* l'identifiant du compte, et c'est par lui que partent les notifications de livraison : sans preuve, n'importe qui s'inscrit sur le numéro d'un voisin, choisit le mot de passe, et reçoit à sa place l'annonce que son colis est arrivé.

3. **Rien de ce qui a été saisi n'est perdu.** Après connexion, l'action interrompue reprend d'elle-même, avec la quantité, l'adresse et le contenu des formulaires conservés. Une connexion abandonnée ramène à l'écran d'origine intact.

4. **Les groupeurs sont anonymes.** L'acheteur ne voit qu'un **pseudonyme**. Ni nom, ni photo, ni quartier, ni coordonnées, et aucune page de profil. Le pseudonyme n'est cliquable nulle part.

   La raison est économique : un acheteur qui peut identifier et joindre le groupeur traite directement avec lui la fois suivante, sans la plateforme, sans garantie et sans un franc pour nous. L'anonymat protège le modèle autant que l'acheteur.

5. **Les échanges passent par la plateforme.** L'acheteur pose ses questions **publiquement** sous une campagne, le groupeur répond, et la réponse est visible de tous. **Il n'existe aucun canal privé.** Tout message est filtré avant publication pour en retirer les coordonnées et les tentatives de prise de contact direct — voir §14.2.

6. **Le groupeur est maître de sa campagne.** Il choisit le produit, le prix, la quantité par part, la durée, et c'est lui qui décide, à la clôture, si la commande passe ou non. La plateforme n'impose **aucun minimum de participants**.

7. **Un acheteur peut être servi seul**, si le groupeur l'autorise. Il n'y a pas de seuil imposé par la plateforme.

7 bis. **Le groupeur déclare combien de personnes il veut réunir**, et ce nombre s'affiche aux acheteurs sous forme de barre de progression (§2.5 de la spec des écrans). ⚠️ **Ce n'est ni un plafond ni un minimum** : dépasser est permis, un groupage au-dessous de son objectif peut parfaitement aboutir, et atteindre l'objectif ne déclenche rien. C'est une information, pas une règle — la décision reste celle du point 6.

8. **L'argent passe par la plateforme, mais il appartient au groupeur.** L'acheteur paie dans l'application, jamais le groupeur de la main à la main. La somme s'inscrit aussitôt au **portefeuille du groupeur**, où elle est **détenue jusqu'à la clôture** (§9).

9. **1 500 F par groupage abouti**, retenus au moment du retrait. **Aucun frais sur un groupage annulé** : les acheteurs sont remboursés intégralement.

10. **La plateforme n'est ni vendeuse ni productrice.** Elle encaisse, sécurise, fait livrer et arbitre.

## 8. Le cycle d'une campagne

Le mot **campagne** désigne une opération de groupage sur un produit, ouverte pendant une durée fixée par le groupeur.

### 8.1 Statuts

**ouverte** → **clôturée** → *(décision du groupeur)* → **commande passée** → **en cours de livraison** → **terminée**

À la clôture, le groupeur tranche :
- **il maintient** : la campagne passe à *commande passée* et suit son cours ;
- **il annule** : tous les acheteurs sont **remboursés intégralement**, sans aucun frais, et reçoivent une notification expliquant que la campagne n'a pas abouti.

**État alternatif :** *annulée*.

⚠️ **Dès la clôture, le groupage quitte le catalogue.** Il n'apparaît plus ni sur le fil, ni dans la recherche, ni dans les catégories : on ne peut plus le rejoindre, donc l'y laisser occuperait la place d'un groupage auquel on peut encore participer. Sa fiche reste atteignable par son lien, pour que l'acheteur qui a payé garde un chemin vers ce qu'il a acheté. Côté groupeur, rien ne change : il voit tous les siens, clôturés compris.

### 8.2 Ce qui déclenche chaque étape

| Étape | Déclencheur |
|---|---|
| Clôture | La date fixée par le groupeur est atteinte, ou il clôture à la main |
| Décision | Le groupeur, dans un délai de **48 h** *(proposition)* après la clôture |
| Annulation automatique | Aucune décision du groupeur passé ce délai — sinon l'argent des acheteurs resterait bloqué indéfiniment |
| Commande passée | Le groupeur a retiré son solde et déposé son justificatif d'achat (section 10) |
| Livraison | Le groupeur déclare la marchandise reçue et prête |
| Terminée | Toutes les livraisons sont confirmées |

### 8.3 Statuts d'une commande d'acheteur

**payée** → **campagne clôturée** → **commande en cours chez le groupeur** → **en cours de livraison** → **livrée**

**États alternatifs :** *litige*, *remboursée*.

## 9. Circuit de l'argent

```
   Acheteur            Group Achat            Portefeuille         Fournisseur
      │              (tient le compte)       du groupeur               │
      │                      │                     │                   │
      │  paie sa part        │                     │                   │
      ├─────────────────────▶│  inscrit au crédit  │                   │
      │                      ├────────────────────▶│                   │
      │                      │              détenu jusqu'à la clôture  │
      │                      │                     │                   │
      │              ── clôture du groupage ──     │                   │
      │                      │                     │                   │
      │                      │   le solde devient  │                   │
      │                      │     retirable       │                   │
      │                      │                     │                   │
      │                      │  retrait : 1 500 F  │   achat           │
      │                      │  retenus par part   ├──────────────────▶│
      │                      │◀── de groupage ─────┤                   │
      │                      │                     │                   │
      │     livraison par le partenaire            │                   │
      │◀─────────────────────┴─────────────────────┘                   │
```

1. L'acheteur paie sa part **à la commande**, par Mobile Money. Il ne paie rien d'autre : pas de frais de service, pas d'abonnement.
2. **La somme s'inscrit immédiatement au portefeuille du groupeur**, tenu par la plateforme. Ce n'est plus l'argent de Group Achat : c'est le sien, et son portefeuille le lui montre dès la première commande.
3. **Mais elle n'est pas retirable tant que le groupage est ouvert** : elle est **détenue jusqu'à la clôture**. C'est ce qui rend le remboursement possible si le groupage n'aboutit pas.
4. À la clôture, si le groupeur maintient le groupage, **son solde devient retirable**.
5. **Au retrait, la plateforme retient 1 500 F par groupage abouti** (§9.2). Le groupeur reçoit le reste et achète sa marchandise.
6. Il dépose le **justificatif de son achat**, la marchandise arrive, le partenaire de livraison livre les acheteurs.
7. Si le groupage est annulé, **remboursement intégral** et **aucun frais** — ni pour l'acheteur, ni pour le groupeur.

**Ce que ce circuit change par rapport au précédent.** La version antérieure de ce document faisait de Group Achat le détenteur des fonds : l'acheteur payait la plateforme, qui versait au groupeur à la clôture. L'argent appartient désormais au groupeur dès le premier paiement, et la plateforme n'est plus qu'un teneur de compte. La conséquence pratique est qu'il n'y a plus de « versement » à décider ni à libérer : il y a un **solde** et un **retrait**.

### 9.1 Le point faible de ce circuit, énoncé clairement

**L'argent part avant que quoi que ce soit ne soit livré.** Entre le retrait et la livraison, les acheteurs ont payé, la plateforme s'est dessaisie, et rien n'a encore été reçu. Un groupeur qui retire et ne livre pas laisse la plateforme face à des acheteurs qu'elle doit rembourser sur sa propre trésorerie — ou décevoir, ce qui est pire, puisque notre promesse unique est la fiabilité.

Ce n'est pas une critique du modèle : le groupeur a réellement besoin de cet argent pour acheter, et lui demander d'avancer sa trésorerie reviendrait à écarter la majorité des groupeurs. **C'est l'exécution qu'il faut armer**, et c'est l'objet du §10.

Deux choses se sont aggravées en passant au portefeuille, et il faut les dire :

- **Le retrait n'est plus conditionné au devis fournisseur.** Dans le circuit précédent, un administrateur libérait l'argent et pouvait refuser tant que le devis manquait. Un portefeuille dont le titulaire ne peut pas retirer son propre argent sans l'accord d'un tiers n'est pas un portefeuille, et prétendre le contraire serait malhonnête. Le devis reste demandé, mais il **constate** au lieu de **conditionner**.
- **Le paiement direct au fournisseur devient impossible** dans le cas général : l'argent est déjà sur le compte du groupeur quand l'achat se décide. C'était la mesure la plus protectrice du dispositif précédent (§10.3).

Ce qui reste pour tenir le risque : la **vérification des groupeurs à l'entrée** (§10.5), le **plafond de collecte par groupage** (§10.4), et le **délai de dépôt du reçu** sous peine d'annulation (§10.2). Ces trois mesures jouent toutes **en amont**, et aucune n'est optionnelle.

### 9.2 Le frais de plateforme — tranché

| Décision | Valeur |
|---|---|
| **Montant** | **1 500 F par groupage abouti**. Un montant fixe, pas un pourcentage |
| **Assiette** | Aucune : le montant ne dépend ni de la collecte, ni du nombre de parts, ni du prix du produit |
| **Qui le supporte** | **Le groupeur** |
| **Quand il est retenu** | **Au retrait**, déduit de la somme qu'il reçoit. Un retrait qui solde trois groupages aboutis porte 4 500 F de frais |
| **Groupage annulé** | **Aucun frais** |
| **Frais de livraison** | Jamais touchés. Ils sont encaissés pour le compte du transporteur et lui sont reversés |

**Pourquoi un montant fixe plutôt qu'un pourcentage.** Un pourcentage se discute à chaque groupage ; un chiffre fixe s'annonce une fois et ne se renégocie pas. Surtout, un pourcentage pèse très différemment selon la marge du produit : 5 % sur un sac de riz acheté 12 000 F et revendu 14 500 F absorbaient 29 % de la marge du groupeur, contre trois fois moins sur une robe. Les produits alimentaires de base — ceux qui servent le mieux notre public — étaient les plus pénalisés. 1 500 F fixes effacent cette distorsion.

**Ce que ce choix nous coûte, dit franchement.** Sur le groupage témoin — 32 écouteurs à 4 000 F, 128 000 F collectés — l'ancienne commission de 5 % rapportait 6 400 F. Le frais fixe rapporte 1 500 F, soit **un quart**. Le modèle ne tient donc plus par le montant d'un groupage mais par **leur nombre** : il faut un peu plus de quatre groupages aboutis pour faire ce qu'un seul faisait avant. C'est un pari assumé sur le volume, et sur le fait qu'un frais faible et lisible attire plus de groupeurs qu'un pourcentage n'en rapporte.

**Le plancher de rentabilité.** 1 500 F doivent couvrir la vérification du groupeur, le contrôle des justificatifs et les frais de l'agrégateur de paiement sur l'encaissement **et** sur le reversement. Ces tarifs ne sont pas connus : **ils seront déterminants**, et le jour où ils le seront, c'est ce calcul qui dira si 1 500 F tiennent. Le levier, le cas échéant, est le montant — pas le retour à un pourcentage.

**Le petit groupage est le cas limite.** Sur un groupage à 10 000 F de collecte, 1 500 F représentent 15 %. C'est beaucoup, et c'est voulu : un groupage minuscule coûte en vérification exactement ce qu'un gros coûte. Si la collecte est inférieure au frais, le frais est ramené à la collecte — **on ne laisse jamais un retrait négatif**.

### 9.3 Deuxième source de revenus : les emplacements publicitaires

Un **bandeau partenaires** en haut de l'écran d'accueil est vendu à des entreprises. C'est une recette indépendante des frais de retrait, et qui a l'avantage d'arriver **avant** le volume : un annonceur paie son emplacement même les semaines où peu de campagnes aboutissent.

**Modèle de vente proposé : un emplacement au forfait, à la semaine ou au mois.** Pas d'enchère, pas de coût pour mille impressions, pas de régie. À l'échelle de Lomé et au démarrage, un forfait se vend en une conversation, se facture sans outil, et s'administre depuis l'admin Django. Construire une machinerie publicitaire pour quatre annonceurs serait du travail perdu. Tarifs : **À définir**

#### Les règles, qui ne sont pas négociables

Une plateforme dont l'argument est la sécurité ne peut pas se permettre une publicité ambiguë. Quatre règles :

1. **Tout emplacement est identifié comme tel**, par la mention « Sponsorisé » ou « Publicité », lisible et non décorative.
2. **Une publicité ne doit jamais pouvoir être prise pour une campagne.** Format distinct, pas de prix de groupage affiché, pas de bouton « Commander ». Un acheteur qui croit rejoindre un groupage garanti et se retrouve sur une offre commerciale extérieure perd confiance dans tout le reste — y compris dans ce qui marche.
3. **Ce qui est hors de la plateforme est annoncé comme tel.** Si l'emplacement mène à un site extérieur ou à un numéro, l'utilisateur doit le savoir avant de toucher : « Vous quittez Group Achat ».
4. **Une ligne éditoriale écrite**, et un refus possible. Sont à exclure : les offres concurrentes de groupage, les produits vendus au prix de détail à côté de nos campagnes — qui nous feraient de la contre-publicité —, les placements financiers, et tout ce qui ne survivrait pas à une vérification sommaire. Un annonceur douteux dans un produit qui vend la confiance coûte plus que ce qu'il rapporte. Liste précise : **À définir**

#### Le coût technique, à ne pas sous-estimer

Le bandeau ajoute des images à charger **sur l'écran le plus coûteux en données de l'application** (§18.1). D'où trois contraintes : **images fixes uniquement, pas de vidéo publicitaire**, chargement différé après le contenu de la campagne, et désactivation en mode économie de données — où l'emplacement devient un simple texte avec le nom de l'annonceur. Ce point doit figurer dans le contrat de l'annonceur, pour qu'il ne découvre pas la règle après coup.

## 10. Sécurisation du circuit — comment tenir la promesse de fiabilité

Le portefeuille du groupeur (§9) déplace tout le dispositif **en amont du retrait** : une fois l'argent parti, il n'existe plus aucun levier. Les mesures ci-dessous sont classées de la plus efficace à la plus accessoire, et les trois premières me paraissent nécessaires avant d'encaisser le premier franc réel.

### 10.1 Le solde : détenu jusqu'à la clôture, retirable ensuite

**Décision retenue :** l'argent de l'acheteur est inscrit au portefeuille du groupeur dès le paiement, mais **il n'est retirable qu'à la clôture d'un groupage maintenu**. Le retrait n'est pas lié à la livraison.

| Moment | Le solde du groupeur |
|---|---|
| Pendant le groupage | Inscrit à son crédit, **détenu jusqu'à la clôture** — visible, pas retirable |
| Clôture, groupage maintenu | **Retirable intégralement**, moins 1 500 F au retrait |
| Clôture, groupage annulé | Retiré de son solde et **remboursé aux acheteurs**, sans frais |
| Ensuite | Il achète, dépose son reçu, et la marchandise est livrée |

⚠️ **« Détenu jusqu'à la clôture », jamais « bloqué jusqu'à la livraison ».** La seconde formulation est fausse — rien ne dépend de la livraison — et elle ferait croire à une retenue de garantie qui n'existe pas. Le tableau des formulations interdites est au §1.7 de la spec des écrans.

**Pourquoi ne pas ouvrir le retrait dès le paiement.** Parce que c'est la détention jusqu'à la clôture qui rend le remboursement possible. Un groupage annulé rend son argent aux acheteurs depuis le solde du groupeur ; si celui-ci avait déjà pu retirer, il n'y aurait rien à leur rendre et la promesse « livré ou remboursé » deviendrait un engagement de notre trésorerie sur chaque groupage ouvert, et non seulement sur ceux qui ont abouti.

### 10.2 Déposer le devis avant, le reçu après

La séquence reste la bonne, même si le devis ne commande plus le retrait :

1. Le groupeur dépose le **devis ou la facture du fournisseur** → la plateforme sait ce qui va être acheté, à quel prix, chez qui.
2. Il **retire son solde**, 1 500 F retenus par groupage abouti (§9.2).
3. Il dépose le **reçu de paiement** → la plateforme constate l'achat effectif.
4. Sans reçu dans un délai donné *(proposition : 72 h)*, le groupage est annulé et les acheteurs remboursés — pendant que l'argent est encore récupérable.

⚠️ **Le devis constate, il ne conditionne plus.** C'est la contrepartie du portefeuille, et elle a un prix : le seul contrôle qui s'exerçait encore au moment où l'argent sortait a disparu. Le devis n'empêchait pas une fraude déterminée, mais il rendait le mensonge documenté, donc attaquable, et il écartait l'erreur de bonne foi. Il garde ce rôle — il ne garde plus le levier.

**Ce qui le remplace partiellement :** le délai du point 4. Un groupeur qui a retiré et ne produit pas de reçu voit son groupage annulé, et c'est cette annulation, inscrite à son historique, qui plafonne son groupage suivant (§10.4). La sanction est différée au lieu d'être préventive.

### 10.3 Payer le fournisseur directement — mesure mise de côté

**Cette mesure était la plus protectrice du dispositif précédent, et le portefeuille la rend inapplicable.** Elle consistait à ce que la plateforme règle elle-même le fournisseur sur la base du devis, de sorte que l'argent des acheteurs ne transite jamais par le groupeur. Elle supposait que la plateforme détienne les fonds au moment de l'achat : ce n'est plus le cas, ils sont sur le compte du groupeur depuis la première commande.

Elle est conservée ici, et non supprimée, pour deux raisons. D'abord parce qu'elle reste **le seul dispositif connu qui supprime le risque au lieu de le borner** : si l'exécution montre un taux de non-livraison que les mesures en amont ne tiennent pas, c'est vers elle qu'il faudra revenir, et il faudra alors rouvrir le choix du portefeuille. Ensuite parce qu'elle redevient envisageable **au-dessus d'un seuil de montant** : un gros groupage pourrait n'être retirable qu'après règlement direct du fournisseur, le portefeuille restant la règle en dessous. Seuil : **À définir**, et la question ne se tranche pas avant d'avoir observé de vrais groupages.

### 10.4 Plafonner l'exposition d'un groupeur

Puisque nous recrutons les groupeurs nous-mêmes, nous disposons d'une information que personne d'autre n'a : leur historique chez nous. Autant l'utiliser pour borner le risque maximal.

| Niveau | Condition | Plafond de collecte par campagne *(proposition)* |
|---|---|---|
| Nouveau | 0 campagne livrée | 150 000 F |
| Confirmé | 3 campagnes livrées sans litige | 600 000 F |
| Établi | 10 campagnes livrées sans litige | Sans plafond, au cas par cas |

⚠️ **Le plafond se contrôle au paiement, pas à la création du groupage.** Le contrôler à la création reviendrait à ne rien contrôler — la collecte y vaut zéro. C'est donc un paiement qui ferait dépasser le plafond qui est refusé, et l'acheteur lit « ce groupage est complet » : il n'a rien fait de mal, et nos règles internes ne le regardent pas.

Un plafond n'empêche pas la fraude, il **borne le montant maximal d'un sinistre** — ce qui, pour une jeune structure, est la différence entre un incident et une fermeture. Il ne coûte rien à mettre en place et remplace utilement la certification abandonnée : la fiabilité se construit en livrant, pas en déposant des pièces.

### 10.4 bis Le compte acheteur — inscription classique, demandée à l'engagement

**On navigue sans compte.** Le §1.5 l'interdit à l'entrée, et pour une raison économique : tout écran placé entre quelqu'un et le produit fait perdre des visiteurs. Le fil, le catalogue, les fiches produit et les questions déjà posées se lisent librement.

Le compte est demandé **à l'ouverture de l'écran de commande**, et pour **poser une question**. Un message explique alors pourquoi, puis le formulaire d'inscription s'ouvre.

⚠️ **Ce paragraphe disait que le compte était demandé « au bouton Payer — et pas avant », et l'argumentait ainsi : « À Commander, l'acheteur n'a encore rien choisi : abandonner ne lui coûte rien. À Payer, il a choisi sa quantité, sa variante et son adresse : il va au bout. Déplacer la demande plus tôt coûterait des commandes sans rien protéger. »** L'utilisateur a tranché dans l'autre sens. L'argument n'était pas faux, et le coût est réel : quelqu'un venu d'un lien WhatsApp qui voudrait seulement voir les variantes et les frais vers son quartier doit désormais se connecter d'abord. Ce qu'on gagne en échange : l'écran de commande calcule des frais de livraison et pré-remplit une adresse — deux choses qui appartiennent à un compte. Les demander à un inconnu, puis lui réclamer un code à l'écran suivant, faisait saisir son adresse avant de savoir qu'un compte serait nécessaire.

#### Ce qu'on lui demande, et ce qu'on ne lui demande pas

| Demandé | Facultatif | Jamais demandé |
|---|---|---|
| Son **nom** — le livreur en a besoin | Un **courriel** | Une date de naissance, un genre |
| Son **numéro**, vérifié par code SMS | | Une adresse postale à l'inscription |
| Un **mot de passe**, 8 caractères au moins | | Quoi que ce soit d'autre |

⚠️ **Ce tableau rangeait « un mot de passe » et « une adresse de messagerie » dans la colonne *Pas demandé*.** Les deux existent désormais : le mot de passe est obligatoire, le courriel reste facultatif et il le restera. Une partie du cœur de cible à Lomé n'a pas d'adresse consultée mais répond au téléphone — c'est le même raisonnement qu'au §10.5 pour les groupeurs. **Le courriel ne sert jamais à se connecter** : le numéro identifie le compte, et lui seul.

**Le mot de passe en détail.** Huit caractères au minimum — c'est `AUTH_PASSWORD_VALIDATORS` qui le dit, pas une règle écrite à la main — et le numéro de téléphone est refusé, puisque c'est la valeur que l'attaquant possède déjà. ⚠️ **Un mot de passe entièrement numérique reste accepté**, et c'est un arbitrage assumé : sur un clavier de téléphone d'entrée de gamme (§5 de la spec des écrans), exiger des lettres pousse à l'écrire sur un papier. Huit chiffres valent dix millions de combinaisons, et la voie se **verrouille quinze minutes au bout de cinq échecs** — l'énumération ne passe pas.

⚠️ **Le code SMS lève ce verrou, et c'est structurant.** Prouver qu'on a le téléphone vaut mieux que connaître le mot de passe. Deux conséquences : un mot de passe oublié ou verrouillé **ne ferme jamais un compte**, donc il n'y a **aucun parcours « mot de passe oublié » à écrire** — ni lien à durée de vie, ni courriel à attendre, ce qui tombe bien puisqu'il est facultatif. Et le verrou peut être sévère sans offrir à un tiers le moyen d'enfermer dehors l'acheteur de son choix en se trompant exprès cinq fois sur un numéro qui n'est pas le sien.

**En changer exige l'ancien.** La session seule suffirait techniquement, mais le jeton survit à la fermeture de l'onglet : sans l'ancien mot de passe, un téléphone prêté cinq minutes suffirait à verrouiller son propriétaire dehors pour de bon.

**Son adresse est enregistrée sans être demandée.** Au moment où la feuille de connexion s'ouvre, il vient de saisir son quartier et son repère à l'écran précédent : ils partent avec le code et deviennent son adresse par défaut. Ses commandes suivantes arrivent pré-remplies, modifiables — on se fait livrer ailleurs un jour sur dix.

⚠️ **L'adresse du compte ne remplace jamais celle de la commande.** Chaque commande garde sa propre copie de la position (§6 du PRD) : le livreur doit voir l'adresse qui valait au moment de la commande, pas celle du compte si l'acheteur déménage entre-temps.

#### Le formulaire vient avant le code, et il est contrôlé avant l'envoi

⚠️ **Ce paragraphe disait l'inverse : « Le nom vient après le code, et c'est délibéré. »** C'était la conséquence de l'inscription implicite, qui n'existe plus. Dans un parcours classique, on remplit un formulaire puis on vérifie son numéro.

**Le formulaire est validé avant que le code parte.** Sans ce contrôle, un mot de passe trop court ne serait refusé qu'à la dernière requête : l'acheteur a reçu son SMS, il est devant les quatre cases, et il doit revenir corriger un champ. C'est la façon sûre de faire abandonner une inscription — et, le jour où un fournisseur sera branché (§18.2), de payer un SMS pour rien. Le même contrôle refuse un numéro **déjà inscrit** et renvoie vers la connexion, plutôt que de laisser corriger un champ qui est juste.

⚠️ **Le mot de passe n'est posé qu'à la création du compte.** L'accepter sur un compte existant ferait du code SMS une remise à zéro silencieuse — alors qu'en changer exige l'ancien. Ce serait annuler cette protection par un autre chemin.

#### La session — pourquoi un jeton et pas le numéro

L'acheteur est reconnu à sa visite suivante sans refaire de code. Ce qui le reconnaît est **un jeton délivré par le serveur**, et non son numéro de téléphone. La différence n'est pas technique :

| | Le numéro | Le jeton |
|---|---|---|
| Se devine | **oui**, huit chiffres | non, 256 bits |
| Expire | jamais | 30 jours glissants |
| Se révoque | impossible sans changer de numéro | oui |

Identifier quelqu'un par son numéro — ce que faisait l'API jusqu'ici — revenait à donner ses commandes à qui connaît ce numéro : un reçu, un répertoire, ou simplement huit chiffres essayés au hasard. C'est le minimum qu'on doive à quelqu'un dont on garde l'adresse et l'historique d'achats.

⚠️ **Le jeton n'est pas le mot de passe, même depuis qu'un mot de passe existe.** Il vit dans le navigateur et survit à la fermeture de l'onglet : qui a l'appareil déverrouillé a le compte. Le mot de passe sert à **entrer depuis un appareil neuf**, pas à garder la porte fermée sur celui-ci — on ne peut pas à la fois laisser naviguer librement et exiger un secret à chaque visite.

La seule conséquence pratique est celle déjà dite plus haut : **changer de mot de passe exige l'ancien**, justement parce que la session seule ne prouve pas qu'on est le titulaire.

#### Le code SMS

Quatre chiffres, valables **dix minutes**, **trois essais**, et il ne sert qu'une fois. Le code est généré et contrôlé pour de bon ; ce qui manque est **son envoi** — Group Achat n'a pas de fournisseur SMS (§18.2).

⚠️ **Le serveur refuse de servir un code fixe hors développement.** Sans fournisseur configuré, la demande de code répond 503 plutôt que d'ouvrir un compte à qui connaît le code de démonstration. Un réglage de développement ne doit pas pouvoir partir en production par simple oubli : il faut que quelque chose l'arrête.

Sur le hachage du code, il faut être franc : quatre chiffres, c'est dix mille possibilités qu'un attaquant ayant la base épuise instantanément. Le hachage évite seulement que des codes en vol traînent en clair dans des sauvegardes. **La vraie protection est le compteur d'essais.**

### 10.5 Vérifier les groupeurs — la procédure KYC

**KYC**, pour *Know Your Customer*, désigne l'ensemble des contrôles qui permettent d'établir qu'une personne est bien celle qu'elle prétend être, et qu'on sait où la retrouver. Deux KYC différents interviennent dans ce projet, et il faut les distinguer :

| Qui vérifie qui | Nature | Qui le subit |
|---|---|---|
| **L'agrégateur de paiement vérifie Group Achat** | Obligation réglementaire. Sans ce dossier, pas de compte marchand, donc pas d'encaissement | Nous, en tant que structure |
| **Group Achat vérifie ses groupeurs** | Pas une obligation qui pèse sur nous aujourd'hui, mais **c'est notre produit** | Chaque groupeur, avant sa première campagne |

Le second n'est pas une formalité administrative : c'est la matérialisation de la promesse de sécurité. « Nous sélectionnons nos groupeurs » ne vaut rien comme phrase marketing — cela vaut comme **dossier constitué, par groupeur, opposable le jour d'un litige**.

#### Les sept contrôles

| # | Contrôle | Comment | Ce qu'il empêche |
|---|---|---|---|
| 1 | **Pièce d'identité** | CNI, passeport ou carte consulaire, recto et verso, plus un **selfie tenant la pièce près du visage** | Qu'on se présente avec la pièce d'un tiers. Sans le selfie, une pièce volée suffit |
| 2 | **Concordance du compte Mobile Money** | Le **nom du titulaire** du compte qui recevra les retraits doit correspondre à la pièce d'identité | Le prête-nom. C'est le contrôle le plus rentable du lot : gratuit, immédiat, et c'est sur ce compte que partira l'argent |
| 3 | **Téléphone vérifié** | Code SMS, numéro conservé au dossier | Un numéro jetable |
| 4 | **Lieu d'activité** | Photo de l'étal ou de la boutique, localisation, et **visite physique pour les premiers groupeurs** | Le groupeur sans existence réelle. Rien ne remplace d'avoir vu la personne à son poste |
| 5 | **Justificatif d'activité** | Registre de commerce, NIF, ou tout document d'activité | L'improvisation. **Non bloquant** : la plupart des bons groupeurs sont dans l'informel, l'exiger écarterait notre cœur de cible |
| 6 | **Deux références joignables** | Un fournisseur, un autre groupeur, une association de commerçants — **appelées, pas seulement collectées** | L'inconnu complet. Une référence qu'on n'appelle pas ne sert à rien |
| 7 | **Contrat signé** | Engagement de livraison, obligation de dépôt des justificatifs, sanctions, copie de la pièce en annexe | L'absence de recours. C'est ce qui transforme un manquement en faute contractuelle |

Le contrôle n° 2 mérite d'être souligné : **si le nom du compte Mobile Money ne correspond pas à la pièce d'identité, la procédure s'arrête.** Il n'y a pas de bonne raison de recevoir l'argent des acheteurs sur le compte de quelqu'un d'autre.

#### Trois niveaux, selon l'exposition

Appliquer les sept contrôles à tout le monde coûterait trop cher en temps et ralentirait le recrutement, qui est notre goulot d'étranglement au lancement. La profondeur de la vérification suit donc le montant que le groupeur peut collecter (§10.4) :

| Niveau | Contrôles exigés | Plafond de collecte par campagne *(proposition)* |
|---|---|---|
| **Entrée** | 1, 2, 3 | 150 000 F |
| **Confirmé** | + 4, 6, 7 — après 3 campagnes livrées sans litige | 600 000 F |
| **Établi** | + 5, visite renouvelée, garant — après 10 campagnes livrées | Au cas par cas |

#### Le KYC n'est pas un acte unique

Un dossier validé une fois ne protège de rien si rien n'est surveillé ensuite. À suivre en continu, dans l'admin :

- **changement du compte Mobile Money de retrait** — le signal d'alerte le plus important : il suspend les retraits et déclenche une re-vérification, parce que c'est exactement le geste d'un compte repris par un tiers ;
- retards répétés de dépôt du reçu d'achat ;
- taux de livraison, délais, litiges ;
- montants inhabituels au regard de l'historique du groupeur.

Signalement automatique, **décision humaine**.

#### Outils et conservation

**Dans le MVP, tout se fait à la main** : dépôt des pièces par le groupeur, examen par un administrateur, validation, attribution du niveau et du plafond. À ce volume, c'est le bon choix — et c'est aussi ce qui nous apprend à qui nous avons affaire.

Deux outils le permettent, et ils font le même travail. L'**admin Django** reste disponible et donne accès aux références des pièces déposées, avec un accès journalisé. L'**écran A2** du produit a été construit parce que l'admin Django ne sait pas faire trois choses dont dépend ce parcours : trier la file par ancienneté d'attente plutôt que par date de création, montrer d'un coup d'œil si les noms concordent sans ouvrir chaque fiche, et **afficher le texte que le groupeur recevra avant qu'on tranche**.

#### Quand l'argent part réellement

**C'est le groupeur qui le décide, et c'est nous qui l'exécutons.** Trois états, et un seul appelle une action de notre part :

| État | Ce que ça veut dire | Qui agit |
|---|---|---|
| **Retirable** | Le groupage est clôturé et maintenu, le solde est à lui | Lui, quand il veut |
| **Retrait demandé** | Il a appuyé sur « Retirer mes fonds » | **Nous** : exécuter le transfert Mobile Money |
| **Effectué** | L'argent est parti, 1 500 F retenus | Personne |

Tant que le paiement est simulé (§18.2), « exécuter » veut dire faire le transfert à la main depuis l'écran A3 et marquer la ligne. Le jour de l'agrégateur, cette même ligne déclenchera l'appel au prestataire, et rien d'autre ne changera.

⚠️ **Nous ne pouvons pas refuser un retrait.** C'est la conséquence directe du portefeuille (§9.1) : le solde appartient au groupeur depuis le premier paiement de ses acheteurs. Le devis fournisseur est demandé avant, il est lu, il est archivé — mais son absence ne bloque plus rien. L'écran A1 garde donc deux files, et seule la première est un ordre à exécuter :

| File | Ce que c'est | Ce qu'on peut faire |
|---|---|---|
| **Retraits à exécuter** | Un groupeur attend son argent | Faire le transfert |
| **Devis manquants** | Un groupeur a retiré sans rien déposer | Le relancer, et compter les récidives |

⚠️ **L'ancienneté est le chiffre qui doit faire agir, pas le montant.** Un groupeur qui attend depuis cinq jours ne peut pas acheter la marchandise qu'il a vendue, et ce sont ses acheteurs qui attendront ensuite. Les deux files sont donc triées du plus ancien au plus récent.

#### Annoncer la décision — par écrit ou de vive voix

Un dossier tranché dont l'intéressé ne sait rien ne vaut pas mieux qu'un dossier non tranché : il a quitté la file d'attente, donc plus personne ne le reprend, et le groupeur attend une réponse qui ne viendra jamais. **C'est la panne silencieuse de ce parcours**, et l'écran A2 lui réserve une section en tête de file.

La décision part donc par l'un des deux canaux, qui sont **de rang égal** :

| Canal | Quand | Ce que fait la plateforme |
|---|---|---|
| **Courriel** | Le groupeur en a déposé un | Il part dans la seconde, et la décision est marquée annoncée |
| **Appel téléphonique** | Sinon, ou si on préfère | La plateforme fournit **un script à lire**, et la décision reste *à annoncer* jusqu'à ce qu'un administrateur ait confirmé avoir appelé |

L'appel n'est pas un pis-aller. Une partie du cœur de cible — des commerçants de Lomé, souvent dans l'informel — n'a pas d'adresse de messagerie consultée mais répond au téléphone. **Le courriel est donc facultatif à l'inscription, le téléphone obligatoire** : ainsi aucun groupeur n'est injoignable, et il n'existe aucune décision impossible à annoncer.

Le script d'appel n'est pas une formalité bureaucratique : sans lui, deux administrateurs annoncent le même refus de deux manières différentes, et l'un des deux le dit mal un jour de fatigue.

**Trois issues, et non deux.** Un dossier peut être validé, refusé, ou **renvoyé à compléter**. La troisième est la plus utile : la plupart des dossiers qui échouent le font sur une photo floue ou une pièce prise de travers, et les refuser définitivement pour cela ferait perdre des groupeurs recrutables — alors que le recrutement est le goulot d'étranglement du lancement. Un dossier renvoyé conserve tout le reste de ce qui a été déposé.

**Un motif est obligatoire dès que la décision n'est pas une validation**, et il se choisit dans une liste fermée. Un champ libre contiendrait au bout de six mois quarante formulations du même refus : on ne pourrait plus compter *pourquoi* les dossiers échouent, donc plus corriger le formulaire d'inscription qui les fait échouer. Le motif a deux rédactions — celle que l'administrateur lit, et celle que le groupeur reçoit. Elles diffèrent : « doute sérieux sur l'identité » est une note interne, et la dire à l'intéressé lui apprendrait quoi corriger pour recommencer.

**Tant que le dossier n'est pas validé, le groupeur ne peut pas lancer de groupage.** Le verrou est dans le modèle, pas dans l'interface : un bouton masqué ne protège de rien, il suffit d'une requête directe pour le contourner. Son tableau de bord s'ouvre quand même, en lecture, pour qu'il découvre l'outil pendant l'attente — mais il n'y engage l'argent de personne.

**Plus tard**, des services de vérification d'identité automatisée couvrent l'Afrique de l'Ouest (Smile ID, Youverify, Dojah et d'autres). Leur couverture réelle pour les pièces togolaises, leur tarif et leur fiabilité sont **à vérifier directement auprès d'eux** : je ne peux pas te les garantir.

**Protection des données — à traiter sérieusement.** Les pièces d'identité et les selfies sont des données personnelles sensibles. Elles ne doivent pas se trouver dans le même stockage que les photos de produits, l'accès doit être restreint à l'administrateur, et une durée de conservation doit être fixée. Détail : **À définir**

#### Retirer un groupeur

Procédure à écrire : motifs de retrait, préavis, et surtout **le sort des campagnes en cours** — les acheteurs ne doivent jamais être les victimes d'une sanction. Si un groupeur est retiré alors qu'une campagne est en cours, soit un autre groupeur la reprend, soit les acheteurs sont remboursés. Règle précise : **À définir**

### 10.6 Faut-il demander une caution aux groupeurs ?

Ta question, et ma réponse est : **pas comme protection principale.**

Le raisonnement. Pour couvrir réellement une campagne de 464 000 F, il faudrait une caution du même ordre. Or les groupeurs que nous voulons — les bons commerçants de marché, ceux qui savent sourcer — ne disposent pas de cette somme immobilisée ; s'ils l'avaient, ils n'auraient pas besoin de l'argent des acheteurs pour acheter. Une caution suffisante **écarte exactement les groupeurs que nous cherchons**, et une caution abordable (25 000 F) ne couvre rien. Elle ralentirait le recrutement, qui est notre vrai goulot d'étranglement, sans réduire le risque de façon sérieuse. S'y ajoute un détail juridique : détenir une caution est encore de la détention de fonds de tiers.

**Ce qui joue le rôle d'une caution, sans en avoir les inconvénients :**

1. **Le paiement direct au fournisseur (§10.3).** Là, il n'y a plus rien à cautionner : l'argent ne passe pas par le groupeur. C'est la seule mesure qui supprime le risque au lieu de l'encadrer, et c'est pourquoi elle passe devant toutes les autres.
2. **Le plafond d'exposition (§10.4).** Il ne protège pas d'une fraude, il en **borne le montant maximal** — pour une jeune structure, c'est la différence entre un incident et une fermeture.
3. **Le garant.** Une personne identifiée qui co-signe le contrat. Coût nul pour le groupeur, pression sociale réelle, et c'est un mécanisme que notre marché comprend bien mieux qu'un dépôt bancaire.
4. **L'historique du groupeur**, qui conditionne son plafond : ce qu'il a à perdre, ce n'est pas un dépôt, c'est son accès aux campagnes importantes.

Le retrait du groupeur étant intégral et antérieur à la livraison (§10.1), **il n'y a aucune retenue en aval** : ces quatre leviers sont tout ce dont nous disposons.

**Où une caution garde du sens :** en **option, à l'initiative du groupeur, pour débloquer un plafond supérieur.** Un groupeur établi qui veut mener des campagnes à 1 500 000 F peut déposer une garantie pour y accéder. C'est volontaire, cela ne freine personne à l'entrée, et le montant suit le risque. Barème : **À définir**

### 10.6 Ce que cela donne, assemblé

> L'acheteur paie sa part et ses frais de livraison dans l'application. La part s'inscrit au **portefeuille du groupeur**, détenue jusqu'à la clôture. À la clôture, s'il maintient le groupage, **son solde devient retirable** : il dépose son devis fournisseur, retire son argent — **1 500 F retenus par groupage abouti** —, achète. Il dépose ensuite son reçu de paiement, sous peine d'annulation du groupage. La marchandise arrive, les livraisons sont confirmées par code, et son taux de livraison détermine le plafond de sa prochaine campagne.

Le groupeur n'avance jamais sa trésorerie. Tout le contrôle se joue **avant** que l'argent ne sorte : qui il est (§10.5), combien il peut collecter (§10.4), ce qu'il va acheter et à qui (§10.2), et si possible sans jamais toucher les fonds (§10.3).

## 11. Livraison

- **Dans le MVP, tout est livré.** Il n'y a pas de retrait sur un point de rendez-vous.
- La livraison est assurée par un **service partenaire**, ou par le livreur du groupeur s'il en a un.
- L'acheteur saisit son **adresse de livraison** au moment de la commande (quartier, repères, numéro joignable).
- **Plus tard**, quand la structure aura un local, l'acheteur pourra venir récupérer sur place.

### 11.1 Frais de livraison — tranchés

| Décision | Valeur |
|---|---|
| **Qui paie** | **L'acheteur** |
| **Principe** | **Les frais dépendent de l'endroit où se trouve l'acheteur.** C'est une fonction de sa position, pas un tarif annoncé |
| **Comment l'acheteur l'indique** | **Deux voies, à son choix** : il **partage sa position exacte**, ou il **donne le nom du lieu** (§écran 5 de la spec) |
| **Valeur retournée aujourd'hui** | **1 000 F**, quelle que soit la position — en attendant les éléments nécessaires au vrai calcul |
| **Calcul réel** | **À venir**, quand les tarifs des transporteurs seront connus |
| **Affichage** | **Une ligne distincte** du prix de la part, dans le récapitulatif et dans le total |
| **Commission** | **Aucune** : les frais sont encaissés pour le compte du transporteur et lui sont reversés intégralement (§9.2) |

#### Une seule fonction, et elle renvoie 1 000 F pour l'instant

Tout tient dans une décision de construction :

```
frais_livraison(position) -> montant

  aujourd'hui :  return 1 000
  demain      :  calcul réel selon la distance et le barème du transporteur
```

**Un seul endroit à modifier**, le jour où tu auras les chiffres. Aucun écran à reprendre, aucune migration, aucune décision reprise. C'est le seul objectif de ce paragraphe : que le provisoire ne coûte rien à remplacer.

**Quatre règles à tenir dès maintenant pour que ce soit vrai :**

- **La position est stockée, pas seulement le prix.** Coordonnées si l'acheteur les a partagées, nom du lieu sinon. Sans elle, le jour du vrai calcul, **aucune commande passée ne pourra servir à étalonner le barème** — et tu perdrais des mois de données utiles. C'est la règle la plus importante de ce paragraphe.
- **Les frais sont figés à la commande**, jamais recalculés. Qui a payé 1 000 F paie 1 000 F, même si le barème change le lendemain. Sinon le montant d'une commande cesse d'être stable et plus rien ne se réconcilie.
- **Les frais s'affichent après que la position est donnée**, jamais avant. Tant qu'elle manque, l'écran dit « Frais de livraison : selon votre position » — pas « 1 000 F ».
- **Aucun écran n'écrit « 1 000 F » en dur** dans un texte fixe. Les maquettes affichent la valeur que la fonction renvoie, pas une constante — sinon le jour du vrai calcul, les écrans mentent.

> **Une zone non desservie reste possible.** La fonction doit pouvoir répondre « nous ne livrons pas là-bas », pas seulement un montant. Sans ce cas, tu n'as aucun moyen de refuser une commande à 300 km.

**Pourquoi une ligne distincte et non un prix tout compris.** Parce que le prix de la part est le même pour tous et que les frais, eux, varient selon l'endroit où se trouve l'acheteur : les mélanger rendrait deux commandes de la même campagne incomparables, et l'acheteur ne pourrait plus vérifier qu'on ne lui a rien glissé dans le total.

> **À ne pas confondre avec un affichage promotionnel.** L'application **n'affiche aucun prix barré et aucun badge de réduction** : notre argument est le prix de gros obtenu par le groupage, pas une remise sur un prix de détail que nous ne contrôlons pas. La règle complète est au §3 du document des écrans.

**Conséquence sur les montants affichés :** le total payé par l'acheteur **est** le prix de la part — 4 000 F sur la campagne de référence.

> ⚠️ **Ce paragraphe disait l'inverse** : *« le total payé n'est plus le prix de la part [...] 4 000 F de part + 1 000 F de livraison = 5 000 F à payer »*. Les frais de livraison facturés à l'acheteur ont été supprimés — il règle la livraison directement au livreur, à la remise. Tous les écrans affichent donc 4 000 F, et **aucun n'affiche de ligne « Livraison » chiffrée**.

> **Le dossier complet du partenariat — économie, circuit physique, cas d'échec, questions à poser à une agence — est dans [LIVRAISON.md](LIVRAISON.md).**

### 11.2 Qui organise la livraison

- **Par défaut, Group Achat**, avec **l'un de ses transporteurs partenaires** — il y en a plusieurs, et aucun n'est exclusif (§7 de [LIVRAISON.md](LIVRAISON.md)). Le groupeur achète la marchandise, et nous organisons l'acheminement jusqu'aux acheteurs.
- **Si le groupeur a son propre livreur**, il gère lui-même ses livraisons. Il l'indique à la création de la campagne.

Dans les deux cas, **la preuve de livraison est la même** : le code saisi par celui qui remet (§11.3).

### 11.3 La preuve de livraison — tranchée

**Le livreur saisit le code que l'acheteur lui montre.** C'est la preuve de livraison, et elle est unique.

| Élément | Décision |
|---|---|
| **Le code** | 6 caractères, alphabet sans ambiguïté (ni 0/O, ni 1/I/L), affichés par groupes de trois : `K7M-4PQ`. Plus un QR code pour aller vite |
| **Où il apparaît** | Dans la commande de l'acheteur, **dès que la livraison est lancée** — pas avant |
| **Qui le saisit** | Le livreur, sur une **page web ouverte depuis un lien de tournée**. Aucune installation, aucun compte |
| **Ce que ça déclenche** | La commande passe à *livrée*, et la campagne se termine quand toutes le sont. Le retrait du groupeur, lui, a déjà pu avoir lieu dès la clôture (§10.1) : la preuve sert ici à **clore le dossier, instruire une contestation et alimenter l'historique de fiabilité du groupeur** (§10.4) |

**Pourquoi cette voie plutôt que la confirmation par l'acheteur.** Le code conserve une preuve **unique, horodatée et détenue par la plateforme**, indépendante de la bonne volonté des deux parties. Un acheteur qui oublie de confirmer laisserait un dossier ouvert sans fin ; un groupeur qui déclare avoir livré ne prouve rien.

C'est aussi cette preuve qui fait tourner le dispositif de sécurité : **le taux de livraisons confirmées d'un groupeur détermine son plafond d'exposition** (§10.4). Comme il n'y a plus de solde retenu pour le tenir, son historique est devenu le seul levier dont nous disposons sur lui — et il n'existe que si les livraisons sont réellement validées.

**Le lien de tournée.** Le livreur reçoit un lien unique et expirant qui ouvre la liste de ses livraisons du jour : pour chacune, le nom, l'adresse, le repère, le numéro à joindre, et un champ de saisie du code. Il valide au fur et à mesure. Chaque validation est horodatée.

C'est aussi là qu'il déclare un **colis refusé** (§12), avec un motif. Sans ce bouton, une livraison refusée ressemble à une livraison non faite, et le dossier devient impossible à instruire.

**Deux replis, nécessaires parce que le terrain n'est pas idéal**

| Situation | Repli |
|---|---|
| L'acheteur n'a pas son téléphone, écran cassé, batterie vide | Le livreur ouvre la livraison dans sa tournée et confirme **avec le nom et le numéro** de l'acheteur, en cochant « code non présenté ». La livraison est marquée comme **confirmée sans code** et signalée pour contrôle |
| Pas de réseau sur le lieu de livraison | La saisie se fait plus tard dans la journée, depuis la même page. L'heure enregistrée est celle de la saisie, et l'écart est visible à l'administration |

**Sécurité du lien.** Un lien de tournée donne accès à des noms, adresses et numéros d'acheteurs : il expire à la fin de la journée, ne couvre que les livraisons de cette tournée, et n'affiche jamais le montant payé.

**Livraison non confirmée.** Si une livraison n'est ni confirmée ni refusée **7 jours** après le lancement de la livraison *(proposition)*, elle remonte à l'administration pour instruction. C'est un cas plus grave qu'il n'y paraît : le groupeur a déjà été payé, donc **c'est la trésorerie de Group Achat qui est exposée** si l'acheteur doit être remboursé. Ces dossiers sont à traiter en priorité, pas à laisser vieillir.

**Plus tard**, si le service de livraison partenaire dispose d'une API, une intégration remplacera le lien de tournée. Cela ne change pas le modèle : la preuve reste la validation horodatée d'une livraison.

## 12. Contestation et litiges

- L'acheteur peut contester **au moment de la livraison**, pas après. Le motif est le non-respect flagrant de la commande : il a commandé une robe, on lui présente une chaussure.
- Une fois la livraison acceptée, la contestation n'est plus possible.
- En cas de contestation, le colis n'est pas accepté et le dossier remonte à l'administrateur.
- L'administrateur examine et tranche : remboursement de l'acheteur, ou commande tenue pour livrée. ⚠️ **Le groupeur a pu retirer entre-temps** (§9.1) : un remboursement décidé ici se prend sur notre trésorerie, pas sur son solde.

**Ce que cette règle implique, et qu'il faut regarder en face.** Une fenêtre fermée à la livraison protège le groupeur contre les réclamations tardives de mauvaise foi, ce qui est légitime. Mais elle ne couvre pas ce qu'on ne voit pas sur le pas de la porte : un carton scellé, une quantité manquante au fond du sac, un produit défectueux à l'usage.

Je ne propose pas de rouvrir la fenêtre — ton choix se défend. Je propose de la **borner explicitement dans les conditions d'utilisation** et de l'**afficher sur l'écran de suivi** avant la livraison : « vérifiez votre commande devant le livreur, la contestation n'est plus possible ensuite ». Un acheteur prévenu accepte une règle stricte ; un acheteur surpris la vit comme une arnaque, et c'est la réputation de la plateforme qui paie.

Délais de réponse du groupeur, durée maximale d'un litige : **À définir**

## 13. L'administrateur — le troisième rôle

L'administrateur était jusqu'ici une ligne dans le tableau des acteurs. Il mérite mieux, parce qu'il **n'est pas un spectateur : il est l'opérateur dont dépend tout le circuit de l'argent.**

### 13.1 Pourquoi ce rôle porte le produit

Relis le §10 : la promesse de fiabilité ne tient pas par la technique, elle tient par **des décisions humaines prises à temps**. Valider un dossier KYC. Contrôler un justificatif d'achat. Arbitrer une contestation. Décider si on rembourse ou si on libère.

Chacune de ces décisions a de l'argent derrière elle, et chacune a un **délai** au-delà duquel on perd — soit la confiance d'un acheteur, soit la trésorerie de Group Achat. **Un administrateur qui prend trois jours de retard coûte plus cher qu'un bug.**

D'où le principe qui gouverne tout son écran :

> **Son tableau de bord n'est pas un rapport, c'est une liste de travail.** Ce qui attend une décision passe avant ce qui s'est passé.

C'est la même règle que le « À faire aujourd'hui » du groupeur, et pour la même raison : un écran qui ouvre sur des totaux flatteurs laisse pourrir ce qui est urgent.

### 13.2 Ce qu'il voit — les files d'attente d'abord

Six files, et chacune porte un compteur et un délai. Ce sont elles qui occupent le haut de l'écran.

| File | Ce qui s'y décide | Ce qu'on perd en tardant |
|---|---|---|
| **Dossiers KYC à valider** | Un groupeur peut-il lancer des campagnes, et jusqu'à quel plafond (§10.5) | Du recrutement — notre vrai goulot d'étranglement |
| **Justificatifs d'achat à contrôler** | La marchandise a-t-elle été commandée (§10.3) | Le seul point où l'on vérifie que l'argent versé est allé au produit |
| **Contestations à arbitrer** | Rembourser l'acheteur ou tenir la commande pour livrée (§12) | La confiance de l'acheteur, et vite |
| **Livraisons non confirmées à 7 jours** | Instruction d'un dossier où le groupeur est déjà payé (§12) | **De la trésorerie** — c'est la file la plus coûteuse |
| **Messages signalés** | Modération, et comptage des tentatives (§14.2) | L'anonymat, donc le modèle |
| **Retours de colis** | Qui reprend, qui stocke, qui paie ([LIVRAISON.md](LIVRAISON.md) §4) | De l'argent, et la patience d'un acheteur |

**La quatrième file mérite d'être mise en avant visuellement**, et pas par goût de la couleur : c'est la seule où **notre propre argent** est exposé, puisque le groupeur a déjà été payé. Les autres coûtent de la confiance ; celle-ci coûte du cash.

### 13.3 Ce qu'il voit ensuite — les indicateurs

En dessous des files, et seulement en dessous. Quatre chiffres suffisent, chacun avec sa variation :

- **Argent détenu en ce moment** — la somme des parts collectées sur des campagnes non clôturées. **C'est le chiffre le plus important du produit** : c'est l'argent des autres que nous détenons, et il doit toujours être rapproché du solde bancaire réel.
- **Campagnes en cours**, et combien arrivent à échéance dans 48 h.
- **Taux de livraison** sur 30 jours, et taux de contestation.
- **Commission encaissée** sur la période.

**Un indicateur à ne surtout pas afficher en grand : le nombre d'inscrits.** C'est la mesure qui flatte et qui n'engage à rien. Ce qui compte au démarrage, c'est le nombre de campagnes allées **jusqu'à la livraison**.

### 13.4 Les alertes — ce qui remonte tout seul

Le §10.5 définit une surveillance continue, mais une surveillance que personne ne regarde n'existe pas. Elle se matérialise ici, en haut de l'écran, et par ordre de gravité :

1. **Changement de compte Mobile Money d'un groupeur** — le signal numéro un du §10.5
2. **Groupeur approchant son plafond d'exposition**
3. **Compteur de messages bloqués** au-delà du seuil (§14.2)
4. **Campagne clôturée sans décision** à l'approche des 48 h
5. **Écart de rapprochement** entre l'argent détenu calculé et le solde réel

La cinquième n'a l'air de rien et c'est la plus sérieuse : **le jour où les deux chiffres divergent, quelque chose ne va pas**, et le découvrir tôt change tout.

### 13.5 L'administrateur est le point faible de l'anonymat

Toute l'architecture du §14 repose sur le fait que personne ne voit les deux côtés. **L'administrateur, lui, voit tout** : les noms des acheteurs, les pièces d'identité des groupeurs, les numéros, les adresses, les montants. C'est nécessaire — on ne peut pas arbitrer un litige à l'aveugle — mais c'est une concentration de risque qu'il faut traiter comme telle.

**Quatre mesures, et elles ne coûtent presque rien si elles sont prises au début :**

- **Deux profils, pas un.** Un profil *support* qui voit les commandes, les campagnes et les messages, sans accéder aux pièces d'identité ni exécuter un retrait ; un profil *direction* qui a tout. Au démarrage une seule personne porte les deux — mais la séparation doit exister avant la première embauche, pas après.
- **Un journal d'accès aux données sensibles.** Qui a ouvert quelle pièce d'identité, et quand. C'est ce qui transforme une promesse de confidentialité en engagement vérifiable.
- **Toute action sur l'argent est tracée et motivée.** Un remboursement, l'exécution d'un retrait, un déblocage de plafond : qui, quand, pourquoi. Jamais de bouton qui déplace de l'argent sans laisser de trace (§18.3).
- **Aucune suppression, jamais.** On annule, on rembourse, on suspend — on n'efface pas. Un enregistrement effacé est une preuve perdue le jour du litige.

### 13.6 Django admin ou écran sur mesure — tranché

**Les deux, et la répartition est nette.**

| Quoi | Où | Pourquoi |
|---|---|---|
| Les six files de travail, la recherche, les fiches, les actions | **Admin Django** | C'est gratuit, immédiat, déjà sécurisé et déjà journalisé. Reconstruire un outil d'édition de données est le travail le plus inutile qu'on puisse s'infliger |
| **Un seul écran de synthèse** : alertes, compteurs des six files, quatre indicateurs | **Page sur mesure** | C'est ce qui manque vraiment à l'admin Django, et c'est l'écran qu'on montre à un jury |

Ce découpage donne le maximum d'effet pour le minimum de travail : **une page à écrire**, le reste étant de la configuration. Les files d'attente sont des vues filtrées de l'admin, et les actions sont des actions d'admin.

### 13.7 Hors périmètre pour l'administrateur

- Statistiques avancées, cohortes, entonnoirs de conversion
- Export comptable automatisé
- Notifications par SMS ou e-mail vers l'administrateur *(il ouvre son écran ; les alertes y sont)*
- Gestion de plusieurs villes ou de plusieurs devises

## 14. Confiance et anonymat

### 14.1 Ce qui remplace la réputation individuelle

Tu as retiré la certification : **tous les groupeurs présents sont sélectionnés par nous**, c'est la garantie. L'acheteur ne compare donc pas les groupeurs entre eux, et ne voit d'eux qu'un pseudonyme.

Cela a une conséquence qu'il faut assumer : **toute la confiance repose sur la marque Group Achat**, et plus du tout sur le groupeur. Un seul groupeur défaillant n'abîme pas sa propre réputation — il abîme la nôtre. C'est exactement pourquoi la section 10 n'est pas un luxe.

Ce qui remplace la réputation individuelle, côté acheteur :

- une **promesse de plateforme** affichée clairement : « vous êtes livré, ou remboursé », et l'argent détenu par Group Achat jusqu'à la clôture. ⚠️ **« Groupeurs sélectionnés par Group Achat » a été retiré de l'interface** — tableau des formulations interdites au §1.7 de la spec des écrans. La vérification des groupeurs reste entière (section 10.5), mais elle n'est plus ce qu'on affiche : « vous êtes livré, ou remboursé » est un engagement que l'acheteur peut nous opposer, là où « groupeurs sélectionnés » lui demandait de nous croire sur parole ;
- les **questions publiques** sous chaque campagne, qui montrent un groupeur qui répond — et depuis la cloche, l'acheteur **sait** qu'on lui a répondu, au lieu de devoir revenir vérifier de lui-même sur la fiche ;
- une **cloche de notifications** qui dit où en est chaque groupage rejoint : clôturé, produit arrivé, annulé et remboursé. ⚠️ **C'est la plateforme qui rédige, toujours.** Le groupeur déclenche un fait, il ne rédige pas de message : un champ libre vers ses acheteurs serait une messagerie privée, et un texte partant à trente personnes d'un coup échapperait au filtre de la section 15. La réponse ne lui rend qu'un compte, jamais une liste — §1.10 de la spec des écrans ;
- la **mécanique de recours** : contestation à la livraison, arbitrage, remboursement. Elle existe désormais pour de vrai côté produit — `POST /api/commandes/{id}/refuser/`, trois motifs et une description, refusable **pendant la livraison seulement**. ⚠️ **Le refus ouvre un litige, il ne rembourse pas** : la commande passe à `litige` et un humain examine sous 48 h. Rembourser sur déclaration se paierait sur notre trésorerie à chaque refus, vrai ou non, puisque le groupeur a déjà retiré son argent à la clôture (section 10.2). Le dépôt de photo attend le stockage de fichiers du VPS : un champ qui perd les photos serait pire que son absence, parce que l'acheteur croirait avoir fourni sa preuve.

**Avis et notes :** retirés de l'interface acheteur, puisqu'il n'y a pas de profil à noter. Mais il serait dommage de ne pas mesurer la fiabilité **en interne** : taux de campagnes livrées, délais, litiges, c'est ce qui alimente les plafonds de 10.4. Affichage public d'un indicateur agrégé : **À définir**

### 14.2 La modération des échanges publics

C'est le dernier endroit par où l'anonymat peut fuir. Les deux côtés sont anonymes (§13, §1.7 de la spec écrans), les identités ne circulent plus sur les colis — **il ne reste que le fil de questions**. Il doit être traité comme un point de sécurité, pas comme un espace de discussion.

#### Ce que la conception règle avant tout filtre

Le filtre technique est la **dernière** ligne, pas la première. Trois choix de conception font déjà l'essentiel du travail, et ils ne coûtent rien :

- **Aucune messagerie privée.** Il n'y a pas de boîte de réception, pas de fil à deux. Un message destiné à fuir doit être écrit **devant tout le monde**, administrateurs compris. Rien ne dissuade autant.
- **Pas de champ libre par défaut.** La question commence par un **choix parmi des questions courantes** — marque, origine, date de livraison, variante, état de la marchandise. La majorité des questions légitimes n'ont alors **aucun texte libre**, et le texte libre redevient l'exception, qu'on peut examiner de près.
- **Un fil par campagne, pas par personne.** Le fil meurt avec la campagne. Pas d'historique de relation à construire.

#### Les trois niveaux de filtrage

| Niveau | Quoi | Quand | Coût |
|---|---|---|---|
| **1 — Règles déterministes** | Suites de 8 chiffres (format togolais), chiffres espacés ou ponctués, `+228`, e-mails, URL, `@identifiants`, mots-clés : *whatsapp, telegram, appelle, mon numéro, contacte-moi, en privé* | **Instantané**, avant publication | Nul. Fonctionne hors ligne |
| **2 — Classifieur IA** | Ce que les règles ne voient pas : numéros **écrits en lettres** (« zéro neuf, un deux, trente-quatre »), descriptions permettant de se reconnaître (« la dame en face de la pharmacie Sodji »), propositions de rendez-vous, langage détourné, mélange français-éwé | Avant publication, sur ce qui a passé le niveau 1 | Faible : quelques questions par campagne, un petit modèle suffit |
| **3 — Humain** | Bouton « Signaler » + file de modération dans l'admin Django | Après publication | Du temps, et il en faudra |

**Le niveau 3 est en place** : `POST /api/questions/{id}/signaler/`, trois motifs fermés, et la file dans l'admin Django. Il l'a été tard, et c'est instructif — l'icône de drapeau était dessinée sur chaque message depuis le début et **n'allait nulle part**. Le niveau 3 n'avait donc aucun moyen d'être saisi : ce que les deux filtres automatiques laissent passer restait en ligne sans recours, alors que c'est précisément ce que ce niveau existe pour attraper.

Deux règles de ce niveau, qui ne se discutent pas :

- **un signalement ne dépublie rien.** Dépublier sur signalement donnerait à n'importe qui le pouvoir de faire taire n'importe qui : il suffirait de signaler la question gênante — « ce produit est-il garanti ? » — pour l'effacer du seul canal public du produit. Le signalement remplit une file ; un humain tranche ;
- **un signalement par personne et par question**, garanti par une contrainte en base. Sans elle, un seul lecteur contrarié gonfle le compteur autant qu'il veut et décide seul de ce qu'un humain regarde en premier.

**L'IA a sa place au niveau 2, et nulle part ailleurs.** La mettre en première ligne coûterait plus cher, serait plus lent, et échouerait sur ce qu'une expression régulière attrape en une microseconde. L'inverse est aussi vrai : des règles seules ne verront jamais « appelle le neuf zero douze trente-quatre cinquante-six ». **Les deux, dans cet ordre.**

#### Deux pièges à éviter

**Les faux positifs coûtent cher.** « câble de 1,2 m pour 4 000 F », « il reste 90 parts » : une règle qui bloque tous les chiffres rend le fil inutilisable. D'où la précision du niveau 1 : on cible **le format d'un numéro togolais** — huit chiffres commençant par 7 ou 9, avec ou sans séparateurs, précédés ou non de `+228` — pas les chiffres en général.

**Ne masque pas, bloque — et avertis dans le même mouvement.** Afficher « appelle-moi au ●●●●●●●● » apprend à l'utilisateur qu'il faut contourner, et laisse l'intention visible de tous.

**La règle, en une phrase :** *un message qui contient une information sensible ne part pas, et son auteur l'apprend au même instant, avec la raison.*

Jamais l'un sans l'autre. **Pas de blocage silencieux** — un message qui disparaît sans explication fait croire à une panne et pousse à réessayer ailleurs. Le message reste dans le champ, modifiable, le passage en cause surligné, avec :

> **Ce message ne sera pas publié.**
> Il contient des informations qui permettraient de vous identifier. Pour votre sécurité, les échanges restent anonymes sur Group Achat.

Et mieux encore : **l'avertissement arrive avant l'envoi.** Dès que la saisie déclenche le niveau 1, le bouton « Envoyer » se désactive et l'explication apparaît. L'utilisateur n'a pas besoin d'échouer pour comprendre.

**Le ton compte autant que la règle.** La plupart des gens qui écrivent leur numéro le font **de bonne foi** — ils veulent être joignables à la livraison. Les traiter en fraudeurs est factuellement faux et les fait fuir. Donc : on parle de **leur** protection, pas de notre règlement ; on écrit « les échanges restent anonymes », jamais « tentative de contournement » ; et quand un numéro est détecté, on ajoute où il va vraiment : *« votre numéro est déjà enregistré pour la livraison, le livreur l'aura le jour de sa tournée »*. Le ton ferme est réservé au groupeur, qui lui a un intérêt à fuir.

#### L'asymétrie à assumer

**C'est le groupeur qu'il faut surveiller, pas l'acheteur.** L'acheteur n'a rien à gagner à contourner : sans la plateforme il perd la garantie et le prix de groupe. Le groupeur, lui, a un intérêt direct : **un client gardé pour la suite**. Le frais de 1 500 F pèse peu dans ce calcul — ce qu'il vise, c'est le répertoire.

Donc : **les réponses du groupeur passent le filtre au même titre que les questions**, et un avertissement écrit lui est présenté une fois, à sa première réponse.

#### Le compteur de tentatives — la mesure la plus utile

Chaque message bloqué est **conservé et attribué**. Le texte refusé n'est pas jeté : c'est une preuve.

Un groupeur qui s'y reprend à trois fois ne s'est pas trompé — il essaie. **Ce compteur rejoint les signaux de surveillance du §10.5**, au même rang que le changement de compte Mobile Money. Palier proposé : avertissement à la première tentative, revue manuelle à la troisième, suspension au-delà.

#### La limite, dite franchement

**Aucun filtre ne tiendra contre deux personnes déterminées.** « On se voit là où tu sais » passera toujours. Il ne faut donc pas sur-investir dans la détection, mais **rendre la fuite peu rentable** :

- le groupeur perd son compte, et avec lui l'accès à toutes ses campagnes futures ;
- l'acheteur qui sort de la plateforme perd la garantie « livré ou remboursé », et c'est lui qui prend le risque sur un paiement d'avance.

**Le vrai rempart est économique, pas technique.** Le filtre sert à ce que la fuite ne soit pas *facile* et ne soit jamais *ouverte* ; la sanction sert à ce qu'elle ne soit pas *intéressante*.

#### Ce qu'on construit, et quand

| Phase | Contenu |
|---|---|
| **MVP / compétition** | Niveau 1 + bouton Signaler + file de modération admin + compteur de tentatives. **Aucune dépendance réseau** — la démonstration fonctionne hors ligne |
| **Phase 2** | Niveau 2, le classifieur IA, avec un état « en vérification » pour les cas incertains et une revue humaine derrière |

## 15. Périmètre du MVP

- **Produit, v1 :** **application web** (React), ouvrable depuis un lien, sans installation. C'est ce qui sert la compétition **et** les premiers vrais utilisateurs.
- **Produit, ensuite :** **application mobile Android et iOS** — c'est la version destinée au grand public, parce que c'est là que vit notre utilisateur type (§5). Le web n'est pas un brouillon du mobile : il reste l'outil d'administration et le point d'entrée sans installation.
- **Conséquence à tenir dès maintenant :** le web est conçu **mobile d'abord**, à 390 px de large, exactement comme les maquettes. Un web pensé pour un écran d'ordinateur ne se transforme pas en application mobile — il se refait.
- **Paiement simulé dans un premier temps.** Le parcours de paiement est complet et crédible, mais aucun argent réel ne circule : l'agrégateur agréé n'est pas encore en place (§18.2). Le branchement du paiement réel ne change ni les écrans, ni les statuts, ni la logique métier — seul le connecteur diffère.
- Ville : Lomé. Langue : français.

### 15.1 Ordre de priorité

1. **Commander une part dans une campagne et payer.** Le fil, la campagne, la quantité, l'adresse, le paiement, le suivi. Sans cela, il n'y a pas de produit.
2. **Lancer et gérer une campagne, côté groupeur.** Créer, suivre les participants, clôturer, décider, déposer les justificatifs, être payé.
3. **La demande de produit par l'acheteur.** Elle fait naître l'offre et rend le catalogue illimité sans gérer de stock.
4. **Le contrôle administrateur.** Recrutement des groupeurs, vérification des justificatifs, déblocage des fonds, litiges.

### 15.2 Hors périmètre, assumé

- Retrait sur place : attend le local.
- Compte et application pour le livreur : le partenaire est un prestataire, pas un utilisateur.
- Avis et notes publics.
- Langues locales et recherche vocale.
- Abonnements et visibilité payante.

## 16. Parcours

### 16.1 Acheteur

Il ouvre l'application et **fait défiler** les campagnes en plein écran, photo ou vidéo, comme un fil de réseau social. Une campagne l'intéresse : il ouvre le détail, lit le prix, la quantité par part, le délai restant, les questions déjà posées. **Il peut en poser une — et c'est là qu'un compte lui est demandé pour la première fois**, avec un message qui dit pourquoi : c'est par le compte que la réponse du groupeur lui reviendra.

**C'est en rejoignant le groupage que son compte lui est demandé**, à l'ouverture de l'écran de commande : prénom, numéro, courriel facultatif, puis un code SMS pour vérifier le numéro. L'action reprend seule ensuite — il choisit sa quantité, voit son total, saisit son adresse de livraison, et paie.

⚠️ **Cette phrase disait : « C'est en payant que son compte lui est demandé — numéro, code SMS. »** Le compte est désormais demandé un écran plus tôt, et l'inscription est classique (§10.4 bis).

Il suit sa commande : *payée*, puis *campagne clôturée*, puis *commande en cours chez le groupeur*, puis *en cours de livraison*. Le livreur se présente, **il vérifie sa commande devant lui** et accepte, ou refuse si ce n'est pas du tout ce qu'il a commandé.

Si la campagne est annulée, il est notifié et **remboursé intégralement**.

### 16.2 Groupeur

Nous le recrutons, vérifions son identité, lui faisons signer un contrat et lui créons son accès. Il choisit un **pseudonyme**.

Il consulte le **fil des demandes** des acheteurs, agrégé par produit et quartier — c'est ce qui lui dit où est la demande réelle. Il peut aussi lancer une campagne de sa propre initiative.

Il crée la campagne : produit détaillé — caractéristiques, état, garantie —, photos ou vidéo, description, **prix pour une pièce** et paliers de quantité facultatifs, durée. Il suit les participants et le montant collecté, répond aux questions publiques, et peut partager sa campagne sur WhatsApp pour amener ses contacts.

**Et il dispose d'un outil de gestion, pas seulement d'un formulaire.** Un écran de statistiques lui montre ses revenus versés, son taux de réussite, son panier moyen, ses revenus par campagne et la répartition de ses commandes par quartier. C'est ce qui le retient : il ne trouve ces chiffres nulle part ailleurs, et la répartition par quartier lui dit concrètement où concentrer ses tournées. Trois interdits y sont stricts : **aucune identité d'acheteur, aucun classement entre groupeurs, aucune projection de revenus** — détail à l'écran 21 du document des écrans.

À la clôture, **il décide** : la commande passe, ou pas. S'il maintient, son solde devient retirable : il dépose son devis fournisseur, **retire l'intégralité du montant collecté moins 1 500 F** (§10.1), achète, dépose son reçu. La marchandise arrive, le partenaire livre.

**Il n'y a pas de solde retenu après la livraison** : tout devient retirable à la clôture. C'est ce qui rend le contrôle *avant* le retrait — KYC et plafond de collecte — indispensable plutôt que confortable, d'autant que le devis ne commande plus rien (§10.2).

### 16.3 Administrateur

**Il ouvre son tableau de bord et regarde ce qui attend une décision**, pas ce qui s'est passé. Six files : dossiers KYC, justificatifs d'achat, contestations, livraisons non confirmées à 7 jours, messages signalés, retours de colis. Il traite en priorité la quatrième, la seule où notre propre trésorerie est exposée.

Au-dessus des files, les alertes remontées toutes seules — changement de compte Mobile Money, plafond approché, écart de rapprochement. En dessous, quatre indicateurs, dont **l'argent détenu en ce moment**, qu'il rapproche du solde bancaire réel.

Il recrute et vérifie les groupeurs, fixe leur plafond, contrôle les reçus, exécute les retraits, arbitre les contestations, modère, et gère les emplacements publicitaires. Détail complet au §13.

## 17. Écrans

**Acheteur**
1. Fil des campagnes (défilement vertical plein écran)
2. Recherche, catégories et résultats
3. Détail d'une campagne
4. Connexion (feuille remontante)
5. Commander : quantité et adresse de livraison
6. Paiement Mobile Money
7. Confirmation de commande
8. Mes commandes
9. Détail d'une commande et suivi de livraison
10. Questions sur une campagne
11. Demander un produit
12. Mes demandes

**Groupeur**
13. Tableau de bord
14. Créer une campagne
15. Gérer une campagne
16. Clôturer et décider
17. Déposer un justificatif d'achat
18. Portefeuille
19. Fil des demandes
20. Questions reçues
21. Statistiques

**Livreur** — page web, sans compte ni installation
22. Tournée du livreur

**Administrateur** — quatre écrans derrière une barre latérale, le reste en admin Django (§13.6)
- **A1. Tableau de bord** : alertes, files de travail, courbe de collecte, répartition des groupages, quatre indicateurs
- **A2. Recrutement — dossiers KYC** : la file d'attente, l'examen d'un dossier, la décision et son annonce
- **A3. Retraits des groupeurs** : le devis fournisseur, et l'exécution des transferts
- **A4. Groupages** : tous états — ouverts, clôturés, livrés, annulés
- A3. Justificatifs d'achat et déblocage des fonds — admin Django
- A4. Contestations et livraisons non confirmées — admin Django
- A5. Modération et messages signalés — admin Django
- A6. Emplacements publicitaires : annonceur, visuel, période, lien, activation — admin Django

## 18. Contraintes non fonctionnelles

### 18.1 Interface et réseau

- Application légère, pensée pour une connexion lente et un forfait data limité.
- **Le fil en défilement vidéo est le point de vigilance du projet** : c'est l'écran le plus coûteux en données, sur le public le plus sensible au coût des données. Les mesures à prendre sont détaillées au §1.6 du document Figma.
- Gros boutons, textes lisibles, contraste élevé.
- Aucune action engageant de l'argent ne doit pouvoir être exécutée deux fois à cause d'une coupure réseau : chaque requête de paiement porte une **clé d'idempotence**.

### 18.2 Conformité et paiement

**Phase 1 — paiement simulé.** Le parcours est complet de bout en bout, mais aucun argent réel ne circule. Le prototype l'**affiche honnêtement** : un bandeau « Démonstration — aucun paiement réel n'est effectué » sur l'écran de paiement et sur le portefeuille du groupeur. Une plateforme dont l'argument est la sécurité de l'argent se juge d'abord sur sa franchise : un jury qui découvre seul que le paiement est faux le prend bien plus mal que s'il l'a lu.

**Phase 2 — paiement réel**, dès que l'agrégateur est en place. Les prérequis ne sont pas techniques, et c'est pourquoi ils doivent être lancés en parallèle du développement, pas après :

- **Détenir l'argent de tiers est une activité réglementée.** L'encaissement doit passer par un **agrégateur de paiement agréé** connecté à T-Money et Flooz. Group Achat ne détient jamais l'argent sur un compte personnel.
- Cela suppose un **compte marchand**, donc une **structure juridique constituée** et un dossier KYC sur la société et ses dirigeants (§10.5). **C'est le délai le plus long du projet.**
- Un **avis juridique** est nécessaire sur la détention de fonds et sur l'engagement « livré ou remboursé », qui nous engage financièrement.
- Choix de l'agrégateur, **ses tarifs d'encaissement et de reversement** — qui déterminent si le frais de 1 500 F tient (§9.2) —, délais de reversement : **À définir**

Architecturalement, le passage de la phase 1 à la phase 2 ne touche qu'une seule couche : le connecteur de paiement. Statuts, écrans, calculs de solde et de frais, journal des opérations sont identiques dans les deux cas. C'est à cette condition que le travail de la phase 1 n'est pas perdu.

### 18.3 Traçabilité

Journal horodaté de **tous** les mouvements d'argent et de **tous** les changements de statut : paiements, retraits des groupeurs, dépôts de justificatifs, livraisons confirmées, remboursements, décisions d'arbitrage. C'est à la fois l'exigence comptable, la preuve en cas de litige, et la matière des plafonds de 10.4.

## 19. Stack technique

**Architecture.** API séparée de l'interface. Le back-end expose une API indépendante que le prototype web consomme aujourd'hui et que l'application mobile consommera. **Toute la logique métier — détention des fonds, calcul des frais, retraits, statuts — vit côté serveur, jamais dans l'application.** Une application installée ne se corrige pas par un déploiement : ce qui est côté serveur se corrige le jour même.

**Back-end :** Django + Django REST Framework, PostgreSQL. L'admin Django sert de back-office pour le recrutement, le contrôle des justificatifs, le déblocage des fonds et les litiges — **plus une seule page sur mesure**, le tableau de bord de synthèse (§13.6).

**Front, v1 :** **React**, application web responsive conçue **mobile d'abord** (390 px). C'est le choix de la vitesse : on livre quelque chose d'utilisable sans passer par les magasins d'applications, et on corrige en déployant.

**Front, ensuite :** une **application mobile Android et iOS** pour le grand public. Le travail n'est pas perdu : toute la logique métier vit côté serveur (voir ci-dessus), et l'application mobile consommera **la même API** que le web. Ce qui se refait, c'est l'interface — pas le produit.

> **La décision à ne pas prendre trop vite :** React Native permettrait de partager du code entre le web et le mobile, Flutter donnerait une meilleure application mais aucun partage avec React. Ce choix ne se tranche pas maintenant — il se tranche quand le web aura des utilisateurs et qu'on saura ce qu'ils font. Choisir aujourd'hui, c'est choisir sans information.

**Intégrité.** Toute opération touchant à l'argent passe par une transaction avec verrouillage de ligne (`SELECT FOR UPDATE`) : pas de double retrait au groupeur, pas de double validation de livraison, pas de double paiement.

**Tâches planifiées.** Trois règles ne se déclenchent sur aucune action utilisateur, et chacune est une **porte de sortie de l'argent détenu** :
1. clôture d'une campagne à sa date d'échéance ;
2. annulation et remboursement si le groupeur ne décide pas dans les 48 h ;
3. annulation et remboursement si le reçu d'achat n'est pas déposé dans le délai.

MVP : commande de gestion Django appelée par un cron horaire. Plus tard : Celery et Redis.

**Hébergement :** VPS avec Gunicorn derrière Nginx en production ; Render ou équivalent en phase de test.

**Stockage des médias.** Les vidéos du fil changent la nature du problème : il faut un stockage objet et une diffusion adaptée, pas des fichiers servis par le serveur applicatif. Solution retenue : **À définir**

## 20. Évolutions

- Retrait sur place dès l'ouverture d'un local.
- Intégration technique avec le service de livraison partenaire.
- Indicateur de fiabilité des groupeurs, interne puis peut-être public.
- Extension à d'autres villes, puis à d'autres pays.
- Création de campagne par dictée vocale, et interface en éwé, mina ou kabiyè. La traduction est faisable aujourd'hui ; la reconnaissance vocale dans ces langues reste faible, donc la dictée commencera en français.
- Agrégation de la demande par produit, quartier et période, pour orienter les groupeurs.
- **Emplacements sponsorisés dans le fil** lui-même, au format d'une campagne et marqués comme tels. C'est l'inventaire qui se vend le mieux dans un fil, mais il demande un ciblage et une mesure que le forfait du §9.3 n'exige pas : à garder pour après le pilote.
- Détection automatique des groupeurs à risque — signalement automatique, décision humaine.

**Prérequis à mettre en place dès le MVP :** ces derniers usages supposent un historique qui n'existera pas au départ. Enregistrer proprement, dès maintenant, chaque changement de statut avec sa date, chaque justificatif avec son montant, chaque livraison avec son heure et chaque demande avec son quartier. C'est gratuit aujourd'hui et irrécupérable plus tard.

## 21. État des décisions

### 21.1 Tranché

| Sujet | Décision | Où |
|---|---|---|
| Frais de plateforme | **1 500 F par groupage abouti**, à la charge du groupeur, retenus au retrait | §9.2 |
| Frais de livraison | **1 000 F dans tout Lomé, payés par l'acheteur**, ligne distincte, jamais touchés par le frais de plateforme | §11.1 |
| Retrait du groupeur | **Intégral, ouvert dès la clôture**, avant la livraison | §10.1 |
| Organisation de la livraison | **Group Achat et son partenaire** par défaut ; le groupeur s'il a son livreur | §11.2 |
| Preuve de livraison | **Le livreur saisit le code de l'acheteur**, via un lien de tournée | §11.3 |
| Paiement | **Simulé** en phase 1, réel dès l'agrégateur agréé | §18.2 |
| Vérification des groupeurs | **Sept contrôles, trois niveaux** selon l'exposition | §10.5 |
| Caution | **Pas de caution obligatoire.** Paiement direct au fournisseur, plafond, garant et historique en tiennent le rôle | §10.6 |
| Anonymat des groupeurs | Pseudonyme seul, aucune page de profil, aucun contact | §7 règle 4 |

### 21.2 Rien ne bloque plus la maquette

Les écrans peuvent être dessinés en entier. Les deux points ouverts qui restent — le barème hors Lomé et le seuil de paiement direct au fournisseur — n'empêchent aucun écran : le premier est une ligne de tarif, le second une règle interne invisible de l'acheteur.

### 21.3 Bloquant avant d'encaisser réellement

- Agrégateur de paiement, compte marchand, structure juridique constituée.
- Avis juridique sur la détention de fonds et sur la promesse « livré ou remboursé ».
- **Tarifs de l'agrégateur** — ils déterminent si 1 500 F par groupage laissent une marge nette viable.
- **Seuil de paiement direct au fournisseur** (§10.3). C'est désormais la seule mesure qui supprime le risque plutôt que de le borner : je recommande de le fixer bas.

### 21.4 À traiter pendant la construction

- Plafonds d'exposition par niveau *(propositions en §10.4 et §10.5)*.
- **Barème des frais de livraison hors de Lomé.**
- **Tarifs des emplacements publicitaires et ligne éditoriale** (§9.3).
- Modalités de reversement des frais de livraison au transporteur partenaire.
- Contrat groupeur, rôle du garant, barème de la caution optionnelle, procédure de retrait.
- Délais : décision du groupeur, dépôt du reçu, livraison non confirmée, durée d'un litige.
- Notifications : quels événements, par quel canal.
- Protection des données : pièces d'identité et selfies des groupeurs, adresses de livraison, durée de conservation.
- Stockage et diffusion des vidéos du fil.
- Planning, équipe, budget, date de la compétition.
