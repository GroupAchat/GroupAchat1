# Group Achat — Cahier des charges

Plateforme web **mobile-first** d'intermédiation et de gestion d'achats groupés au Togo.

## 1. Vision et objectifs

Group Achat permet à des acheteurs de rejoindre des achats groupés organisés par des **Organisateurs d'Achat (OAG)**. La plateforme sécurise le parcours de participation, conserve les paiements dans un portefeuille interne, organise la livraison et fournit une preuve de remise grâce à un QR code unique.

Les objectifs sont de :

- rendre les achats groupés accessibles au-delà des réseaux privés comme WhatsApp ;
- rassurer les acheteurs grâce à la traçabilité des paiements et des livraisons ;
- donner aux OAG un outil de publication, de suivi et de gestion ;
- tenir l'acheteur et l'OAG **mutuellement anonymes** : chacun n'est désigné
  que par son nom d'utilisateur, et seul l'abonnement Contact Privé ouvre le
  pont entre les deux ;
- favoriser l'activité grâce aux points, au parrainage et aux grades ;
- proposer une première version fonctionnelle avec des services tiers simulés.

## 2. Principes de fonctionnement

- Un groupage correspond à **un seul article**.
- Un article peut contenir au maximum **trois images et une vidéo**.
- Le catalogue est consultable sans inscription.
- L'inscription est demandée uniquement pour participer, parrainer, souscrire au chat ou accéder à un espace personnel.
- Le paiement de l'acheteur est crédité dans le portefeuille interne de l'OAG, mais le solde reste bloqué ou retirable selon les règles de la plateforme.
- Le retrait n'est pas automatiquement déclenché par le paiement ni par la livraison.
- Une participation payée ne peut pas être annulée par l'acheteur.
- Un QR code unique est généré après confirmation du paiement et doit être scanné lors de la remise.
- Sur la plateforme, l'acheteur et l'OAG **ne se connaissent pas** : ils
  n'apparaissent que sous un nom d'utilisateur.
- Il n'existe **aucune discussion publique**, ni chat, ni fil de
  commentaires sous une campagne.
- Le chat privé est accessible à l'acheteur grâce à un abonnement mensuel donnant accès à tous les OAG de la plateforme.

## 3. Ce que la plateforme garantit

Group Achat garantit :

- l'enregistrement du paiement ;
- la traçabilité du montant dans le portefeuille interne de l'OAG ;
- l'application des règles de remboursement ;
- la génération et la validation du QR code ;
- l'enregistrement de la preuve de livraison ;
- la protection des coordonnées personnelles ;
- la conservation et la modération des conversations privées signalées ;
- la **couverture assurantielle** de chaque groupage lancé sur la plateforme,
  dans les termes de la police souscrite auprès de l'assureur partenaire ;
- le **cadre contractuel** établi par l'institution notariale partenaire.

Group Achat ne garantit pas :

- la qualité de l'article ;
- la conformité de l'article à la présentation de l'OAG ;
- la disponibilité du fournisseur ;
- les engagements commerciaux non enregistrés dans la plateforme ;
- **toute transaction conclue hors de la plateforme** : ni le séquestre, ni
  l'assurance, ni le contrat ne jouent. Voir la section 11.5.

La plateforme met en relation et trace les opérations, mais n'arbitre pas la qualité de la marchandise. Les conditions de remboursement concernent les cas prévus par le cycle du groupage et non les désaccords commerciaux ordinaires sur la qualité du produit.

## 4. Profils et rôles

La plateforme utilise un compte utilisateur unique. Un compte peut avoir le rôle d'acheteur, demander le rôle d'OAG ou être un compte administrateur créé en interne.

### 4.1 Acheteur

L'acheteur peut :

- consulter le catalogue sans inscription ;
- créer et vérifier son compte ;
- participer à un groupage ;
- payer par Mobile Money ;
- recevoir et présenter son QR code ;
- suivre ses participations et ses livraisons ;
- gagner des points ;
- parrainer des acheteurs par lien ;
- souscrire au Contact Privé ;
- discuter avec tous les OAG pendant la durée de son abonnement ;
- publier une demande de produit ;
- consulter son historique.

### 4.2 Organisateur d'Achat Groupé (OAG)

L'OAG peut être :

- **Grossiste** : commerçant déclaré, disposant d'un local et d'un stock ;
- **Organisateur individuel** : particulier qui monte des groupages.

L'OAG doit fournir les justificatifs correspondant à son profil, passer l'entretien de vérification, signer le contrat-cadre et attendre la validation de l'administrateur avant d'accéder aux fonctionnalités de publication. Voir le [manuel d'exploitation](MANUEL_EXPLOITATION.md).

L'OAG peut :

- acheter un pack de publication ;
- créer et publier des groupages dans la limite de son pack ;
- dépenser une mise en avant sur un de ses groupages ;
- publier un article par groupage ;
- suivre les participations et les montants collectés ;
- consulter son portefeuille interne ;
- suivre son bénéfice estimé et son solde retirable ;
- répondre aux acheteurs dans le chat privé ;
- déclarer un fournisseur lorsqu'une procédure interne est nécessaire ;
- gérer la livraison selon son grade ;
- gagner des points et progresser du grade Bronze vers Argent puis Or ;
- n'apparaître sur la plateforme que sous son **nom d'utilisateur**.

### 4.3 Administrateur

L'administrateur dispose d'une console séparée pour :

- valider les comptes, les dossiers KYC et les **noms d'utilisateur** des OAG ;
- gérer les OAG, les groupages, les paiements et les portefeuilles ;
- contrôler les retraits et les remboursements ;
- gérer les points, les grades et les commissions ;
- gérer les partenaires logistiques et les agences ;
- enregistrer les fournisseurs et gérer en interne les opérations des organisateurs individuels au grade Bronze ;
- valider les livreurs déclarés par les OAG Or ;
- modérer les chats privés signalés ;
- consulter les journaux d'activité.

## 5. Parcours de l'acheteur

1. L'acheteur consulte le catalogue sans compte.
2. Il ouvre la fiche d'un groupage.
3. Il crée son compte avec son nom, son prénom, son numéro de téléphone, son mot de passe et, facultativement, son adresse e-mail et un **nom d'utilisateur** (section 11.1).
4. Il vérifie son numéro par SMS.
5. Il choisit la quantité et l'option de livraison.
6. Il paie sa participation par Mobile Money.
7. La plateforme confirme le paiement et crédite le portefeuille interne de l'OAG.
8. La plateforme génère le QR code unique de la participation.
9. L'acheteur suit la préparation et la livraison.
10. Il présente son QR code à l'agence, au livreur ou au livreur de l'OAG Or.
11. Le scan confirme la livraison et clôture la participation.

Une participation payée ne peut pas être annulée par l'acheteur.

## 6. Article et groupage

### 6.1 Données d'un article

Un article comporte :

- un titre ;
- une description ;
- une catégorie ;
- un prix unitaire ;
- jusqu'à trois images ;
- une vidéo facultative ;
- une image d'aperçu si nécessaire ;
- les informations utiles à la livraison.

### 6.2 Données d'un groupage

Un groupage comporte :

- un article unique ;
- un prix de participation ;
- une quantité minimale ;
- une date limite ;
- une zone de livraison ;
- les options de livraison disponibles ;
- le statut du groupage ;
- l'OAG responsable ;
- l'historique des paiements et des décisions.

## 7. Modèle économique

### 7.1 Droit de publier : abonnement ou pack

Publier un groupage se paie. L'OAG choisit entre deux formules.

| Formule | Prix | Publications | Points |
|---|---:|---|---:|
| **Abonnement publication** | 2 000 FCFA par mois | illimitées | 10 points par mois payé |
| **Pack** | 500 FCFA | 5 | 2 points, une seule fois |

L'abonnement s'adresse à celui qui publie régulièrement, le pack à celui qui
essaie ou qui lance un groupage de loin en loin. Les deux compteurs sont
**indépendants** : un OAG dont l'abonnement expire garde les publications de
ses packs.

**Mise en avant.** Pousser un groupage devant les acheteurs — tête de
catalogue, accueil, notification — est un service distinct du droit de
publier : un OAG qui lance dix petits groupages n'a pas le même besoin que
celui qui en lance un seul et veut qu'on le voie. Une mise en avant se dépense
sur un groupage **déjà publié**. Son tarif et son mode d'obtention — achetée,
incluse dans l'abonnement, ou payée en points — restent **à trancher**.

Une mise en avant est **signalée comme telle** sur la fiche. L'acheteur ne
connaît pas son vendeur ; sans cette mention, il lirait « premier du
catalogue » comme « le plus fiable ».

Règles communes :

- Les points sont attribués **au paiement**, et non à chaque publication :
  une seule fois pour un pack, chaque mois pour l'abonnement.
- Une publication est consommée **à la mise en ligne**, pas à la création du
  brouillon : un groupage abandonné avant publication ne coûte rien.
- Les packs **se cumulent** : les compteurs s'additionnent.
- Un pack **n'expire pas**. Ce qui reste reste.
- Une publication consommée n'est pas rendue si le groupage échoue : elle paie
  la mise en ligne, pas la réussite.

### 7.2 Commission sur les groupages aboutis

| Grade de l'OAG | Commission de la plateforme |
|---|---:|
| Bronze | **3,5 %** |
| Argent | **2,5 %** |
| Or | **1,3 %** |

Le taux applicable est affiché dans l'espace OAG et enregistré au moment du calcul de la commission.

### 7.3 Abonnement Contact Privé

L'acheteur et l'OAG ne se connaissent pas (section 11). **Le Contact Privé est
le seul pont entre les deux** : c'est ce qu'il vend, et ce n'est pas seulement
une messagerie.

- Payé par l'acheteur. Prix : **1 000 FCFA par mois**, 30 jours.
- Récompense : **5 points** par mois payé.
- **Aucune condition de points.** L'abonnement n'en coûte pas, il en
  rapporte. Les points récompensent ; en faire un péage fermerait la porte à
  celui qui n'a encore rien acheté — c'est-à-dire exactement celui qu'on
  cherche à rassurer.
- Il ouvre le **chat privé avec tous les OAG** de la plateforme, messages
  illimités pendant la période active.
- Il donne accès à l'**identité de l'OAG** : son nom et son numéro de contact.
- Renouveler avant l'échéance **ajoute** trente jours à ceux qui restent.
  Sinon renouveler tôt coûterait plus cher que renouveler tard, et personne
  ne renouvellerait tôt.

Hors abonnement, aucune identité, aucun numéro et aucune adresse ne sont
révélés — ni à l'acheteur, ni à l'OAG.

La levée de l'anonymat de l'OAG au profit d'un abonné n'est pas une
transmission de données à son insu : elle fait partie des engagements du
**contrat-cadre** qu'il signe avant sa validation, et l'écran d'inscription le
lui dit.

### 7.4 Réduction de livraison

Lorsqu'un acheteur atteint **150 points**, il bénéficie d'une réduction de **50 % sur une livraison éligible**. Cette réduction est consommée lors de son utilisation et ne réduit pas le prix de l'article.

⚠️ **Le mécanisme reste à définir.** La plateforme n'encaissant pas les frais de livraison (section 10.1), elle ne peut pas en retrancher la moitié. Il faut donc soit un **bon** que l'acheteur présente à l'agence et que la plateforme lui rembourse, soit une **remise accordée par l'agence** dans le cadre du partenariat. Le premier coûte de l'argent réel, le second se négocie. Tant que ce n'est pas tranché, la réduction n'est pas développée.

## 8. Points, parrainage et grades

### 8.1 Attribution des points

| Action | Bénéficiaire | Points |
|---|---|---:|
| Paiement d'un pack de publication | OAG | 2 points, une seule fois |
| Paiement d'un mois d'abonnement publication | OAG | 10 points |
| **Groupage mené à son terme** | OAG | **10 points** |
| Achat et paiement d'un article | Acheteur | **10 points** |
| Parrainage validé par lien | Acheteur parrain | 2 points |
| Paiement d'un mois de Contact Privé | Acheteur | 5 points |

Aucune de ces lignes ne **coûte** de points : le barème n'attribue jamais
un solde négatif. Les dépenses sont une autre affaire, et elles ne
touchent que le solde.

Une même opération ne peut pas attribuer plusieurs fois les mêmes points.

**Deux compteurs, et non un seul.** Les points servent à deux choses qui ne
peuvent pas partager le même solde : ils **mesurent** le parcours — c'est le
grade — et ils **s'échangent** contre des avantages. Si dépenser ses points
faisait perdre son grade, personne ne les dépenserait. La plateforme tient donc
pour chaque compte :

- les **points cumulés**, qui ne baissent jamais et décident du grade ;
- le **solde de points**, qui monte aux mêmes occasions et baisse à chaque
  dépense.

Ce que l'OAG peut acheter avec son solde reste **à trancher**.

### 8.2 Parrainage acheteur

L'acheteur peut partager un lien vers un article ou un groupage. Le parrainage est validé lorsque la personne invitée :

1. ouvre le lien de parrainage ;
2. rejoint effectivement le groupage ;
3. paie sa participation ;
4. n'est pas identifiée comme une opération frauduleuse ou artificielle.

Le parrain reçoit alors 2 points. Un clic, une inscription sans paiement ou un paiement annulé ne donne aucun point.

**Un filleul n'a qu'un parrain, et pour toujours** : le premier qui l'amène.
Sans cette unicité, le même compte servirait de filleul à tout un réseau, et
deux personnes se disputeraient le même mérite. Le parrainage paie donc
l'arrivée d'une personne, **une fois** — pas chacun de ses achats.

**Le lien porte un code court**, et non l'identifiant du parrain : un `?p=42`
se devine, se change, et dit combien de comptes existent. Le code naît au
premier partage et non à l'inscription — la plupart des comptes ne
parraineront jamais.

**Le code est rangé dans le navigateur de l'invité, puis envoyé avec la
commande** : c'est le dernier moment où l'on sait encore d'où vient la
personne. Il est retiré de l'adresse dès l'arrivée, sinon l'invité
réexpédierait le lien de son parrain et se ferait voler ses propres filleuls.

**Le parrain voit le nombre, jamais les noms.** Qui a accepté l'invitation ne
regarde que l'invité.

⚠️ **La détection des opérations artificielles (point 4) n'est pas
développée.** Ce qui est en place est structurel : on ne se parraine pas
soi-même — la contrainte est en base —, un filleul ne compte qu'une fois, et
seul un paiement confirmé déclenche les points. Détecter un réseau de comptes
créés pour s'auto-parrainer demande d'autres signaux (numéros, appareils,
rythme des paiements) qui restent à définir.

### 8.3 Grades OAG

| Grade | Points cumulés | Commission |
|---|---:|---:|
| Bronze | niveau de départ | 3,5 % |
| Argent | 500 points | 2,5 % |
| Or | 700 points | 1,3 % |

**Bronze n'est pas un palier à atteindre : c'est le niveau de tout OAG dès la validation de son dossier.** Un OAG qui débute publie, encaisse et livre comme les autres ; ce sont la commission et l'autonomie logistique qui s'améliorent avec les points, pas le droit d'exercer.

Les règles de perte ou de rétrogradation d'un grade ne sont pas encore définies. Tant qu'elles ne sont pas validées, un grade obtenu est conservé.

## 9. Paiements et portefeuille interne de l'OAG

### 9.1 Paiement de l'acheteur

Après confirmation du paiement :

- la participation passe à l'état `paiement_confirme` ;
- le montant est crédité dans le portefeuille interne de l'OAG ;
- le montant est affecté au groupage concerné ;
- le QR code de l'acheteur est généré ;
- le paiement est enregistré dans l'historique.

### 9.2 États du portefeuille OAG

Le portefeuille doit distinguer :

- **solde total** : total des montants crédités ;
- **solde bloqué** : montant non retirable ;
- **solde retirable** : montant autorisé par la plateforme ;
- **bénéfice estimé** : montant revenant à l'OAG après les règles applicables ;
- **commissions** ;
- **transactions** ;
- **retraits demandés, autorisés ou refusés**.

Le paiement n'est pas libéré automatiquement à la livraison. Le scan du QR code constitue une preuve de remise, mais ne rend pas automatiquement le solde retirable.

### 9.3 Règles de retrait

Le retrait dépend notamment :

- du profil de l'OAG ;
- de son grade ;
- du statut du groupage ;
- du fournisseur déclaré ;
- des contrôles administratifs ;
- des éventuelles garanties demandées.

L'OAG voit clairement, dans son portefeuille, pourquoi un montant est bloqué ou retirable.

### 9.4 OAG individuel au grade Bronze : procédure interne

Pour un **organisateur individuel** encore au grade Bronze, la gestion du fournisseur et le paiement de la marchandise sont réalisés **en interne** par la plateforme et ne constituent pas une fonctionnalité publique de l'espace OAG.

Cette procédure vise le **profil** autant que le grade : un commerçant déclaré a une existence vérifiable et un fournisseur habituel, un particulier qui lance son premier groupage n'a ni l'un ni l'autre. Elle s'arrête dès le passage à Argent.

La procédure interne peut comprendre :

1. déclaration du fournisseur par l'OAG ;
2. vérification du fournisseur par l'administrateur ;
3. vérification de la commande et du montant nécessaire ;
4. paiement direct du fournisseur par la plateforme ou mise en place d'une garantie ;
5. affichage dans l'espace OAG du bénéfice estimé et du montant retirable autorisé ;
6. décision administrative concernant le retrait.

Le fournisseur, la garantie éventuelle et le paiement interne sont gérés par l'administrateur. L'OAG ne peut pas retirer librement l'argent collecté avant l'autorisation prévue.

### 9.5 OAG Bronze et Argent

Les OAG Bronze et Argent utilisent les procédures de paiement, de retrait et de livraison contrôlées par la plateforme. Ils ne gèrent pas librement une livraison avec leurs propres livreurs.

### 9.6 OAG Or

L'OAG Or bénéficie d'une autonomie logistique plus importante :

- il peut organiser la livraison avec ses propres livreurs ;
- ses livreurs doivent être déclarés et validés ;
- le QR code doit être scanné lors de la remise ;
- le paiement n'est pas automatiquement libéré au scan ;
- les règles de retrait restent contrôlées par la plateforme.

## 10. Livraison et preuve de remise

### 10.1 Options de livraison

**Il n'y a pas de point de remise fixé par l'OAG.** Un lieu unique —
« Dépôt Agoè-Nyivé », « Boutique Abalo, Bè-Kpota » — obligeait la moitié de la
ville à traverser Lomé pour un sac de riz, et ne disait rien à qui voulait
être livré. L'OAG groupe et remet le lot à l'agence ; il n'a pas à savoir où
va chaque colis.

**C'est l'acheteur qui choisit, part par part**, au moment où il commande :

1. **retrait au bureau de poste** le plus proche de chez lui — il nomme
   lui-même le bureau qui l'arrange ;
2. **livraison à son adresse**, dont les frais sont fixés par l'agence et
   réglés **à la remise**.

Le choix est demandé à la commande et non à l'arrivée : c'est lui qui décide
si l'agence dépose au bureau ou passe à la porte, et elle prépare sa tournée
avant que le lot arrive. La base refuse une part dont la destination est
vide — le colis est déjà parti quand on s'aperçoit qu'on ne sait pas où.

**L'adresse de livraison ne sort jamais vers l'OAG.** Un bureau de poste est
un lieu public : le nommer ne dit rien de personne. Une adresse désigne un
domicile, et l'OAG ne connaît pas ses acheteurs (section 11) — la lui servir
contournerait la règle par la logistique. Il voit « Livraison par l'agence »,
rien de plus ; l'adresse ne va qu'à celui qui livre.

**La plateforme n'encaisse pas les frais de livraison.** Le tarif est fixé par
l'agence, et l'acheteur la paie **directement, à la livraison**. Ce que
l'acheteur règle sur Group Achat est le prix de la marchandise, rien d'autre.

Trois conséquences à tenir dans le code :

- le montant d'une participation **ne contient jamais de frais de livraison** ;
- le séquestre ne consigne que la marchandise, et un remboursement ne porte
  que sur elle ;
- le choix du mode de remise est enregistré **sur la participation** —
  `mode_retrait`, et le bureau ou l'adresse — pour que le partenaire sache
  quoi faire, mais il **n'a aucun effet sur le paiement**.

Le tarif de l'agence n'est pas de la responsabilité de la plateforme et ne
figure pas dans ses revenus.

### 10.2 QR code

**C'est le livreur partenaire qui scanne — La Poste, Gozem — et lui seul.**
L'OAG confie le lot en bloc à l'agence et ne rencontre jamais ses acheteurs ;
s'il validait lui-même les retraits, celui qui doit livrer signerait sa propre
livraison, et le code ne prouverait plus rien. Chaque scan prévient
**l'acheteur** que son colis est remis, et **l'OAG** que telle personne l'a
reçu : c'est ainsi qu'il suit sa distribution sans appeler l'agence.

Le code est cherché **sur toute la plateforme**, pas dans une campagne : un
livreur porte dans la même tournée les colis de plusieurs groupages, et il a
un paquet et un code, pas le nom du groupage.

**Le livreur est le seul à voir l'adresse et le numéro de l'acheteur** — on ne
livre pas un pseudonyme, il faut sonner et appeler. En revanche il ne sait
rien de l'OAG ni des montants : porter un colis n'a pas besoin de savoir qui
l'a groupé, ni ce qu'il a coûté.

Le QR code est généré uniquement après confirmation du paiement. Il est lié à :

- l'acheteur ;
- la participation ;
- l'article ;
- le groupage.

Le QR code doit être à usage unique. Un QR invalide, déjà utilisé, expiré ou appartenant à un autre groupage doit être refusé.

Le scan enregistre :

- la date et l'heure ;
- le groupage ;
- la participation ;
- le responsable de remise ;
- le mode de livraison ;
- le statut de la livraison.

Le scan confirme la remise et clôture la participation sur le plan opérationnel. Il ne déclenche pas automatiquement le retrait de l'OAG.

### 10.3 Confidentialité lors de la livraison

- L'agence ou le partenaire logistique reçoit uniquement les informations nécessaires à la remise.
- L'adresse de livraison n'est pas visible par l'OAG lorsqu'elle est traitée par un partenaire.
- L'OAG Or peut connaître l'acheteur uniquement au moment de la remise lorsque cela est nécessaire.
- L'OAG ne reçoit pas automatiquement les coordonnées permanentes de l'acheteur.

## 11. Anonymat, nom d'utilisateur et couverture

L'acheteur n'achète pas la parole d'un inconnu : il achète un dispositif. Le
séquestre tient l'argent, l'assurance couvre le groupage, le contrat notarié
encadre l'OAG. **C'est le dispositif qui est digne de confiance, pas la
personne** — et c'est pourquoi la personne peut rester anonyme.

### 11.1 Le nom d'utilisateur

Chaque OAG **choisit son nom d'utilisateur** à l'inscription. C'est sous ce
nom, et sous lui seul, qu'il existe sur la plateforme : sur ses groupages, dans
les avis, dans le chat. Son nom civil, son numéro et ses pièces restent dans
son dossier, invisibles.

L'acheteur **peut** également en choisir un. À défaut, il apparaît sous son
prénom suivi de l'initiale de son nom. Dans les avis et les listes de
participants, c'est ce nom qui s'affiche — jamais son nom complet, jamais son
numéro.

**Le nom d'utilisateur de l'OAG est validé avec son dossier**, par la personne
qui mène l'entretien. Un nom librement choisi peut défaire l'anonymat à lui
seul :

| Nom demandé | Motif de refus |
|---|---|
| `Boutique Ramatou – Grand Marché` | désigne son commerce : l'acheteur le retrouve sans payer |
| `Faya 90112233` | contient un numéro de téléphone |
| `Group Achat Officiel` | se fait passer pour la plateforme |
| `OAG Certifié Or` | s'attribue un signal de confiance |
| `Faya02` alors que `Faya-02` existe | prête à confusion avec un autre OAG |

Les règles de validation sont donc :

- **unique**, en ignorant la casse, les accents, les espaces et les tirets ;
- **aucune coordonnée** : ni suite de chiffres évoquant un numéro, ni
  identifiant de messagerie ;
- **aucun mot réservé** : *officiel, certifié, vérifié, garanti, admin,
  Group Achat* ;
- **aucune raison sociale ni enseigne** lui appartenant.

La dernière règle est la plus contraignante, et elle a un coût au recrutement :
un grossiste installé voudra naturellement mettre l'enseigne qu'il a mis des
années à faire connaître. Elle est maintenue parce que c'est exactement ce qui
fait tomber le modèle — l'acheteur note le nom, se rend à la boutique, et la
fois suivante la plateforme ne sert plus à rien. L'entretien de recrutement le
dit franchement : sur Group Achat, l'OAG construit une réputation **de
plateforme**, qui le suit même lorsqu'il change de fournisseur.

**Le nom d'utilisateur ne change plus** une fois validé : la note, les avis et
le nombre de groupages aboutis y sont attachés, et le laisser changer
permettrait d'effacer un mauvais historique. Une modification reste possible
par un administrateur, à titre exceptionnel, avec conservation de l'ancien nom.

### 11.2 Ce que l'acheteur voit à la place du vendeur

Puisque l'acheteur ne connaît pas l'OAG, le bloc qui le désigne est **tout ce
dont il dispose pour décider**. Il figure sur chaque fiche de groupage :

```
Faya-02 · Argent · 4,6 / 5 (38 avis) · 47 groupages aboutis
```

Aucun de ces éléments — nom d'utilisateur, grade, note, volume, mention de
vérification — **ne peut s'acheter**, ni en argent ni en points. Le jour où un
OAG peut acheter un signal de confiance, la promesse entière s'effondre, et
personne ne le voit venir.

### 11.3 Chat privé

La plateforme ne comporte **aucune discussion publique**. Le fil de
commentaires sous les campagnes a été retiré : il laissait convenir d'un
arrangement direct à la vue de tous, et hors de la plateforme ni le séquestre
ni l'assurance ne jouent. Ce qui faisait vendre dans ce fil — les questions
déjà posées, les réponses de l'OAG — est repris autrement : par la fiche
produit, les photos du lot et les avis.

Le Contact Privé permet à un acheteur abonné d'écrire à tous les OAG pendant
trente jours (section 7.3).

**Un seul fil par paire**, quelle que soit la campagne : l'acheteur parle à
quelqu'un, pas à une annonce. Rattacher le fil à une campagne éparpillerait la
même conversation en autant de fils que de groupages, et l'historique — qui
est précisément ce qui protège les deux parties — deviendrait illisible.

**L'OAG répond sans abonnement.** Il ne paie pas pour parler à ses propres
acheteurs, et un fil où seul l'un des deux peut écrire ne vaut rien.

**L'historique reste lisible quand l'abonnement s'achève.** Ce sont les
échanges de l'acheteur ; les lui retirer parce qu'il n'a pas renouvelé
effacerait la preuve de ce qui a été convenu. Ce qu'il perd, c'est le droit
d'écrire et la vue sur l'identité de l'OAG.

**La messagerie est une page, pas un tiroir.** Elle occupe l'écran : la
liste des fils d'un côté, l'échange de l'autre, comme toutes les messageries
de places de marché. On passe du temps ici — on relit ce qui a été promis, on
revient voir la réponse ; une feuille flottante au-dessus du catalogue perdait
le fil à chaque fermeture. Sur téléphone, il n'y a de place que pour l'un des
deux : la liste, puis l'échange en plein écran. Écrire à un OAG depuis la
fiche d'un groupage **y conduit** au lieu d'ouvrir un panneau par-dessus.

Fonctionnalités du chat :

- liste des conversations ;
- ouverture d'une conversation depuis la fiche d'un groupage ;
- messages illimités pendant l'abonnement ;
- affichage des deux parties sous leur nom d'utilisateur ;
- accès à l'identité de l'OAG, ouvert par l'abonnement ;
- signalement d'un message par son destinataire ;
- modération administrative **des seuls messages signalés** — les
  conversations sont privées, les parcourir sans motif reviendrait à lire le
  courrier de tout le monde ;
- masquage sans suppression : un message effacé sans trace empêcherait
  d'instruire le signalement suivant venant du même compte ;
- historique des messages, consultable même hors abonnement.

Cycle du chat :

```
non_achete → paiement_confirme → chat_actif → chat_expire ou chat_ferme
```

### 11.4 Couverture : assurance et contrat

Chaque groupage lancé sur la plateforme est **couvert par une police
d'assurance** souscrite auprès d'un assureur partenaire, et l'OAG est engagé
par un **contrat établi par une institution notariale partenaire**.

C'est le cœur de ce que la plateforme offre et que le groupe WhatsApp ne peut
pas offrir. Ces deux éléments doivent donc être **visibles dans le produit** —
sur la fiche du groupage, à côté du séquestre, et au moment du paiement — et
non enfouis dans les conditions générales.

⚠️ **Avant d'écrire quoi que ce soit à ce sujet dans l'interface** : au Togo
l'assurance relève du **code CIMA**, et ce qui peut être affiché dépend de qui
est l'assuré. Si la police couvre **la plateforme** — sa responsabilité, son
risque de défaillance d'un OAG —, l'affichage est libre. Si elle couvre
**directement les acheteurs**, la plateforme distribue de l'assurance et le
statut d'intermédiaire est requis. À confirmer avec le courtier.

### 11.5 Hors de la plateforme, rien n'est couvert

Toute transaction conclue directement entre un acheteur et un OAG, en dehors de
la plateforme, échappe au séquestre, à l'assurance et au contrat. Les deux
parties en sont seules responsables.

Cette règle figure aux conditions générales, mais une clause ne retient
personne. **Elle est affichée là où naît la tentation** :

| Emplacement | Pourquoi là |
|---|---|
| Bandeau permanent dans le fil de discussion | seul endroit où un arrangement direct peut se convenir |
| Une ligne au moment du paiement | le moment où l'acheteur compare avec « payer en direct » |
| Mention sur la fiche du groupage | avant même que la question se pose |

La formulation désigne une **perte réelle**, et non une interdiction : « hors
de la plateforme, ni le séquestre ni l'assurance ne jouent — vous êtes seuls ».
Un interdit se contourne ; une perte se calcule.

### 11.6 Ce que l'anonymat ne couvre pas

L'anonymat porte sur les **coordonnées**, pas sur le visage. Au point de
remise, l'acheteur et l'OAG se voient. Si le retrait se fait dans le commerce
de l'OAG, l'acheteur connaît dès lors son adresse et peut y revenir
directement.

Le fermer complètement supposerait des **points de retrait neutres**, ce qui
est une décision distincte, avec un coût logistique. Elle n'est pas prise
ici.

## 12. Fonctionnalités et interfaces par profil

### 12.1 Interface publique et acheteur

L'interface acheteur est une boutique mobile-first avec les rubriques suivantes :

- Accueil ;
- Catalogue ;
- Recherche et filtres ;
- Détail d'un groupage ;
- Mes participations ;
- Mes livraisons ;
- Mon QR code ;
- Mes points ;
- Parrainage ;
- Contact Privé ;
- Notifications ;
- Mon profil.

Le tableau de bord affiche :

- le solde de points ;
- la progression vers 150 points (réduction de livraison) ;
- l'accès à l'abonnement ;
- la réduction de livraison disponible ;
- les participations actives ;
- les livraisons en attente ;
- les derniers messages.

La fiche d'un groupage affiche :

- les images et la vidéo ;
- le prix ;
- le minimum de pièces ;
- la date limite ;
- la progression du groupage ;
- les options et frais de livraison ;
- les informations publiques sur l'OAG : grade, note et volume d'activité ;
- les conditions de participation ;
- les boutons Participer et Partager.

### 12.2 Interface OAG

Avant validation KYC, l'OAG voit un espace d'attente contenant :

- le statut du dossier ;
- les documents manquants ;
- les demandes de correction ;
- les messages de l'administrateur.

Après validation, l'espace OAG comprend :

- Tableau de bord ;
- Mes groupages ;
- Créer un groupage ;
- Mon pack ;
- Mon portefeuille ;
- Mes points et mon grade ;
- Mes livraisons ;
- Mes conversations ;
- Mon dossier KYC ;
- Mes livreurs, uniquement pour l'OAG Or ;
- Notifications.

Le tableau de bord OAG affiche :

- le grade et la commission ;
- les points et la progression ;
- les publications et les mises en avant qui restent ;
- les groupages actifs et terminés ;
- le montant total du portefeuille ;
- le montant bloqué ;
- le montant retirable ;
- le bénéfice estimé ;
- les livraisons à préparer ;
- les nouveaux messages.

Le formulaire de création contient :

- article ;
- description ;
- catégorie ;
- prix ;
- minimum de pièces ;
- date limite ;
- trois images maximum ;
- une vidéo facultative ;
- options de livraison ;
- aperçu et validation de publication.

L'OAG consulte les participations sous forme de références internes. Il ne voit pas automatiquement les numéros, adresses ou e-mails des acheteurs.

### 12.3 Fonctionnalités par grade OAG

| Fonctionnalité | Bronze | Argent | Or |
|---|:---:|:---:|:---:|
| Créer des groupages | Oui | Oui | Oui |
| Vérification avant mise en ligne | Systématique | Par sondage | A posteriori |
| Consulter le portefeuille | Oui | Oui | Oui |
| Commission | 3,5 % | 2,5 % | 1,3 % |
| Utiliser les agences partenaires | Oui | Oui | Oui |
| Déclarer un fournisseur | Procédure interne si organisateur individuel | Selon règles | Selon règles |

**La vérification est le seul filtre entre un OAG tout neuf et la vitrine.**
Le dossier de confiance dit qui il est ; il ne dit rien de ce qu'il publie.
Un prix absurde, une photo volée ou un produit interdit coûtent plus cher à
réparer qu'à relire, et c'est l'acheteur qui paie la différence — puisque
c'est la plateforme qu'il croit.

Une campagne en attente de relecture porte l'état `en_verification` : elle
n'apparaît pas au catalogue, sa fiche n'est pas ouvrable, et **aucun séquestre
n'est ouvert** tant que personne ne peut payer.

**Le sondage de l'Argent est déterministe** : une mise en ligne sur quatre,
comptée sur celles qu'il a déjà demandées. Un tirage au sort aurait le même
effet moyen, mais ni l'OAG ni l'équipe ne pourraient vérifier après coup que
la règle a été suivie — et un contrôle qu'on ne peut pas auditer finit par
être soupçonné.

**Un refus rend la publication consommée** et exige un motif. Elle paie la
mise en ligne ; si la plateforme la refuse, la mise en ligne n'a pas eu lieu,
et la facturer serait indéfendable. Ce n'est pas le cas d'un groupage qui
échoue après coup : celui-là est bien allé en vitrine (§7.1).
| Gérer ses propres livreurs | Non | Non | Oui |
| Organiser une remise directe | Non | Non | Oui |
| Connaître l'acheteur à la remise | Non | Non | Oui, uniquement si nécessaire |

Le grade n'allège pas seulement la commission : **il allège la surveillance**.
C'est ce qui en fait un objectif, et pas une simple remise.

### 12.4 Interface administrateur

La console administrateur comprend :

- Tableau de bord ;
- Utilisateurs ;
- Dossiers KYC ;
- Entretiens de vérification ;
- Contrats signés ;
- OAG ;
- Surveillance des OAG ;
- Groupages ;
- Groupages à approuver avant mise en ligne ;
- Articles ;
- Paiements ;
- Portefeuilles ;
- Retraits ;
- Remboursements ;
- Packs de publication ;
- Points et grades ;
- Chats privés ;
- Fournisseurs ;
- Agences et partenaires ;
- Livreurs OAG Or ;
- Notifications ;
- Journal d'activité ;
- Paramètres.

L'administrateur peut :

- valider, refuser ou suspendre un OAG ;
- consulter les pièces KYC ;
- modifier les règles de points ;
- contrôler les commissions ;
- autoriser ou refuser les retraits ;
- gérer les remboursements ;
- vérifier les fournisseurs des organisateurs individuels au grade Bronze ;
- gérer les livreurs des OAG Or ;
- approuver la mise en ligne des groupages des OAG Bronze ;
- enregistrer les comptes rendus d'entretien et les contrats signés ;
- traiter les demandes d'accès, de rectification et d'effacement des données ;
- consulter les scans QR ;
- modérer les chats signalés ;
- consulter toutes les actions sensibles dans le journal.

### 12.5 Matrice des permissions

| Fonctionnalité | Acheteur | OAG | Administrateur |
|---|:---:|:---:|:---:|
| Consulter le catalogue | Oui | Oui | Oui |
| Participer à un groupage | Oui | Oui | Oui |
| Créer un groupage | Non | Oui, dans la limite de son pack | Oui |
| Acheter un pack | Non | Oui | Oui |
| Consulter son portefeuille OAG | Non | Oui | Oui |
| Autoriser un retrait | Non | Non | Oui |
| Souscrire au Contact Privé | Oui, sans condition | Non requis | Gestion |
| Utiliser le chat privé | Oui, avec abonnement | Répondre | Modérer |
| Gérer les livreurs | Non | OAG Or uniquement | Oui |
| Gérer les fournisseurs | Non | Déclarer | Oui |
| Scanner un QR de livraison | Non | Responsable autorisé | Oui |
| Modifier les points et grades | Non | Non | Oui |

## 13. Notifications

L'acheteur reçoit des notifications pour :

- confirmation du paiement ;
- génération du QR code ;
- changement d'état du groupage ;
- disponibilité de l'article ;
- choix et suivi de livraison ;
- scan du QR code ;
- remboursement ;
- nouveau message privé ;
- expiration de l'abonnement.

L'OAG reçoit des notifications pour :

- validation ou refus KYC ;
- achat d'un pack, publication consommée, pack épuisé ;
- participation payée ;
- atteinte du minimum ;
- changement d'état du groupage ;
- nouveau message privé ;
- décision concernant un fournisseur ;
- évolution des points et du grade ;
- demande ou décision de retrait ;
- livraison confirmée.

L'administrateur reçoit des notifications pour :

- nouveaux dossiers KYC ;
- paiements et remboursements ;
- demandes de retrait ;
- signalements ;
- erreurs de scan QR ;
- fournisseurs ou livreurs à vérifier ;
- échéances de groupages.

## 14. Cycles de vie

### 14.1 Dossier OAG

```
brouillon → soumis → en_verification → entretien_terrain → contrat_a_signer → valide
                             ├── documents_a_corriger
                             ├── refuse
                             └── suspendu
```

`entretien_terrain` et `contrat_a_signer` correspondent à des actes qui se
déroulent **hors de la plateforme** — un appel ou une visite, une signature chez
le notaire. Ce sont malgré tout des états du dossier : sans eux, personne ne sait
à quelle étape en est un candidat, et deux personnes peuvent appeler le même OAG
en croyant être les premières. Voir la section 16.

### 14.2 Groupage

```
brouillon → en_cours → cloture_automatique
   │
   ├── minimum_atteint → finance → approvisionnement → livraison → termine
   │
   └── minimum_non_atteint
          ├── OAG_maintient → finance → approvisionnement
          ├── OAG_renonce → annule → remboursements
          └── silence_7_jours → annule → remboursements
```

### 14.3 Participation

```
en_attente → paiement_confirme → qr_genere → preparee
   ├── livraison_domicile
   ├── agence_partenaire
   └── remise_oag_or
        → qr_scane → livree → terminee
```

Une participation payée ne possède aucun état d'annulation à la demande de l'acheteur.

### 14.4 Portefeuille et retrait

```
paiement_confirme → solde_oag_bloque →
   ├── retrait_en_attente → autorise → retire
   └── remboursement → rembourse
```

Le scan du QR code clôture la livraison, mais ne rend pas automatiquement le solde retirable.

## 15. Mode prototype

Cette version est une maquette fonctionnelle. Les services tiers sont simulés derrière des interfaces remplaçables :

| Service | Simulation |
|---|---|
| SMS | Le code de vérification s'affiche à l'écran. |
| Mobile Money | Un bouton confirme immédiatement le paiement. |
| Portefeuille OAG | Le paiement est crédité dans le portefeuille interne et le retrait est contrôlé par l'administrateur. |
| Droit de publier | Le paiement simulé de 500 FCFA crédite 5 publications et 2 points ; celui de 2 000 FCFA ouvre un mois de publications illimitées et 10 points. |
| Mise en avant | ⚠️ **Pas encore développée** : son tarif et son mode d'obtention restent à trancher (§7.1). Le droit de publier, lui, l'est. |
| Contrat OAG | Le document du cabinet notarial est joint au dossier ; l'acceptation et sa date sont réelles. |
| Contact Privé | Le paiement simulé de 1 000 FCFA ouvre trente jours, donne 5 points et dévoile l'identité des OAG. |
| Points | Les achats donnent 10 points, les groupages aboutis 10 points à l'OAG, et les parrainages validés 2 points. |
| QR livraison | Le QR est généré après paiement et son scan confirme la remise sans déclencher automatiquement le retrait. |
| Fournisseur en procédure interne | La vérification et le paiement sont simulés dans la console administrateur. |
| Partenaires logistiques | Les agences et livraisons sont simulées. |
| Livraison OAG Or | Le livreur enregistré et le scan QR sont simulés. |

Le code métier — paiements, portefeuille, remboursements, commissions, points, grades, QR code, chat, confidentialité et règles de livraison — doit être écrit de manière réelle. Seuls les appels aux services externes sont simulés.

## 16. Hors plateforme : le cadre d'exploitation

Le recrutement des OAG, les entretiens de vérification, les contrats, la
conformité IPDCP, les rôles à pourvoir et le modèle économique détaillé vivent
dans le **[manuel d'exploitation](MANUEL_EXPLOITATION.md)**. Ce ne sont pas des
règles de logiciel : ce sont des actes humains, et les mélanger ici
obligerait à relire un cahier des charges pour savoir qui appelle un candidat.

Ce cahier n'en retient que ce qui se code. Trois points y renvoient :

- le cycle du dossier OAG passe par `entretien_terrain` et `contrat_a_signer`
  (§14.1) — deux états d'actes qui se déroulent dehors ;
- la vérification avant mise en ligne dépend du grade (§12.3) ;
- l'acceptation d'un contrat est enregistrée avec sa version, sa date et son
  signataire.

## 17. Pile technique

| Couche | Choix |
|---|---|
| API | Django 5.2 + Django REST Framework |
| Base | PostgreSQL 17, SQLite en secours hors déploiement |
| Front | React 19 + Vite + Tailwind CSS |
| Applications front | Boutique acheteur et console OAG/administrateur selon les permissions |
| Exécution | Docker Compose (`base`, `api`, `boutique`, `admin`) |
| Configuration | Un seul `.env` à la racine, lu par Django, Vite et Compose |
| Médias | Cloudinary : maximum 3 images et 1 vidéo par article |
| Authentification | Numéro de téléphone vérifié par SMS ; SMS et Mobile Money simulés dans le prototype |

Le français est la langue du code : noms de modèles, champs, routes et variables. Le terme métier à utiliser est **Organisateur d'Achat Groupé (OAG)**.
