# Group Achat — Cahier des charges

Plateforme web **mobile-first** d'intermédiation et de gestion d'achats groupés au Togo.

## 1. Vision et objectifs

Group Achat permet à des acheteurs de rejoindre des achats groupés organisés par des **Organisateurs d'Achat (OA)**. La plateforme sécurise le parcours de participation, conserve les paiements dans un portefeuille interne, organise la livraison et fournit une preuve de remise grâce à un QR code unique.

Les objectifs sont de :

- rendre les achats groupés accessibles au-delà des réseaux privés comme WhatsApp ;
- rassurer les acheteurs grâce à la traçabilité des paiements et des livraisons ;
- donner aux OA un outil de publication, de suivi et de gestion ;
- protéger les coordonnées personnelles des acheteurs et des OA ;
- favoriser l'activité grâce aux points, au parrainage et aux grades ;
- proposer une première version fonctionnelle avec des services tiers simulés.

## 2. Principes de fonctionnement

- Un groupage correspond à **un seul article**.
- Un article peut contenir au maximum **trois images et une vidéo**.
- Le catalogue est consultable sans inscription.
- L'inscription est demandée uniquement pour participer, parrainer, souscrire au chat ou accéder à un espace personnel.
- Le paiement de l'acheteur est crédité dans le portefeuille interne de l'OA, mais le solde reste bloqué ou retirable selon les règles de la plateforme.
- Le retrait n'est pas automatiquement déclenché par le paiement ni par la livraison.
- Une participation payée ne peut pas être annulée par l'acheteur.
- Un QR code unique est généré après confirmation du paiement et doit être scanné lors de la remise.
- Il n'existe aucun chat public.
- Le chat privé est accessible à l'acheteur grâce à un abonnement mensuel donnant accès à tous les OA de la plateforme.

## 3. Ce que la plateforme garantit

Group Achat garantit :

- l'enregistrement du paiement ;
- la traçabilité du montant dans le portefeuille interne de l'OA ;
- l'application des règles de remboursement ;
- la génération et la validation du QR code ;
- l'enregistrement de la preuve de livraison ;
- la protection des coordonnées personnelles ;
- la conservation et la modération des conversations privées signalées.

Group Achat ne garantit pas :

- la qualité de l'article ;
- la conformité de l'article à la présentation de l'OA ;
- la disponibilité du fournisseur ;
- les engagements commerciaux non enregistrés dans la plateforme.

La plateforme met en relation et trace les opérations, mais n'arbitre pas la qualité de la marchandise. Les conditions de remboursement concernent les cas prévus par le cycle du groupage et non les désaccords commerciaux ordinaires sur la qualité du produit.

## 4. Profils et rôles

La plateforme utilise un compte utilisateur unique. Un compte peut avoir le rôle d'acheteur, demander le rôle d'OA ou être un compte administrateur créé en interne.

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
- discuter avec tous les OA pendant la durée de son abonnement ;
- publier une demande de produit ;
- consulter son historique.

### 4.2 Organisateur d'Achat (OA)

L'OA peut être :

- **Commerçant** : boutique ou vendeur professionnel ;
- **Organisateur individuel** : particulier ou initiateur de groupages.

L'OA doit fournir les justificatifs correspondant à son profil et attendre la validation de l'administrateur avant d'accéder aux fonctionnalités de publication.

L'OA peut :

- acheter un ticket de publication ;
- créer jusqu'à 10 groupages avec un ticket ;
- publier un article par groupage ;
- suivre les participations et les montants collectés ;
- consulter son portefeuille interne ;
- suivre son bénéfice estimé et son solde retirable ;
- répondre aux acheteurs dans le chat privé ;
- déclarer un fournisseur lorsqu'une procédure interne est nécessaire ;
- gérer la livraison selon son grade ;
- gagner des points et progresser dans les grades Bronze, Argent et Or.

### 4.3 Administrateur

L'administrateur dispose d'une console séparée pour :

- valider les comptes et les dossiers KYC ;
- gérer les OA, les groupages, les paiements et les portefeuilles ;
- contrôler les retraits et les remboursements ;
- gérer les points, les grades et les commissions ;
- gérer les partenaires logistiques et les agences ;
- enregistrer les fournisseurs et gérer en interne les opérations des OA individuels sous Bronze ;
- valider les livreurs déclarés par les OA Or ;
- modérer les chats privés signalés ;
- consulter les journaux d'activité.

## 5. Parcours de l'acheteur

1. L'acheteur consulte le catalogue sans compte.
2. Il ouvre la fiche d'un groupage.
3. Il crée son compte avec son nom, son prénom, son numéro de téléphone, son mot de passe et, facultativement, son adresse e-mail.
4. Il vérifie son numéro par SMS.
5. Il choisit la quantité et l'option de livraison.
6. Il paie sa participation par Mobile Money.
7. La plateforme confirme le paiement et crédite le portefeuille interne de l'OA.
8. La plateforme génère le QR code unique de la participation.
9. L'acheteur suit la préparation et la livraison.
10. Il présente son QR code à l'agence, au livreur ou au livreur de l'OA Or.
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
- l'OA responsable ;
- l'historique des paiements et des décisions.

## 7. Modèle économique

### 7.1 Ticket de publication OA

- Prix : **100 FCFA**.
- Utilisation : jusqu'à **10 créations de groupages**.
- Récompense : **2 points au total par ticket payé**.
- Les 2 points sont attribués une seule fois au paiement du ticket.
- Les points ne sont pas répétés pour chacune des 10 créations.
- Un ticket utilisé partiellement conserve le nombre de créations restantes selon les règles de la plateforme.

### 7.2 Commission sur les groupages aboutis

| Grade de l'OA | Commission de la plateforme |
|---|---:|
| Bronze | 4 % |
| Argent | 3 % |
| Or | 2 % |

Le taux applicable est affiché dans l'espace OA et enregistré au moment du calcul de la commission.

### 7.3 Abonnement Contact Privé

- L'abonnement est payé par l'acheteur.
- L'acheteur doit posséder au moins **50 points**.
- Les 50 points sont une condition d'accès et ne sont pas consommés.
- Prix : **2 000 FCFA par mois**.
- Récompense : **10 points** pour chaque abonnement mensuel payé.
- Les messages sont illimités pendant la période active.
- L'abonnement donne accès au chat privé avec **tous les OA de la plateforme**.
- L'acheteur peut demander des informations sur un OA, y compris lui demander directement s'il accepte de révéler certaines informations.
- Aucune identité, aucun numéro ou aucune adresse ne sont révélés automatiquement.

### 7.4 Réduction de livraison

Lorsqu'un acheteur atteint **100 points**, il bénéficie d'une réduction de **50 % sur une livraison éligible**. Cette réduction est consommée lors de son utilisation et ne réduit pas le prix de l'article.

## 8. Points, parrainage et grades

### 8.1 Attribution des points

| Action | Bénéficiaire | Points |
|---|---|---:|
| Paiement d'un ticket de publication à 100 FCFA | OA | 2 points au total par ticket |
| Achat et paiement d'un article | Acheteur | 5 points |
| Parrainage validé par lien | Acheteur parrain | 2 points |
| Paiement d'un abonnement Contact Privé | Acheteur | 10 points |

Une même opération ne peut pas attribuer plusieurs fois les mêmes points.

### 8.2 Parrainage acheteur

L'acheteur peut partager un lien vers un article ou un groupage. Le parrainage est validé lorsque la personne invitée :

1. ouvre le lien de parrainage ;
2. rejoint effectivement le groupage ;
3. paie sa participation ;
4. n'est pas identifiée comme une opération frauduleuse ou artificielle.

Le parrain reçoit alors 2 points. Un clic, une inscription sans paiement ou un paiement annulé ne donne aucun point.

### 8.3 Grades OA

| Grade | Seuil de points | Commission |
|---|---:|---:|
| Bronze | 250 points | 4 % |
| Argent | 400 points | 3 % |
| Or | 600 points | 2 % |

Les règles de perte ou de rétrogradation d'un grade ne sont pas encore définies. Tant qu'elles ne sont pas validées, un grade obtenu est conservé.

## 9. Paiements et portefeuille interne de l'OA

### 9.1 Paiement de l'acheteur

Après confirmation du paiement :

- la participation passe à l'état `paiement_confirme` ;
- le montant est crédité dans le portefeuille interne de l'OA ;
- le montant est affecté au groupage concerné ;
- le QR code de l'acheteur est généré ;
- le paiement est enregistré dans l'historique.

### 9.2 États du portefeuille OA

Le portefeuille doit distinguer :

- **solde total** : total des montants crédités ;
- **solde bloqué** : montant non retirable ;
- **solde retirable** : montant autorisé par la plateforme ;
- **bénéfice estimé** : montant revenant à l'OA après les règles applicables ;
- **commissions** ;
- **transactions** ;
- **retraits demandés, autorisés ou refusés**.

Le paiement n'est pas libéré automatiquement à la livraison. Le scan du QR code constitue une preuve de remise, mais ne rend pas automatiquement le solde retirable.

### 9.3 Règles de retrait

Le retrait dépend notamment :

- du profil de l'OA ;
- de son grade ;
- du statut du groupage ;
- du fournisseur déclaré ;
- des contrôles administratifs ;
- des éventuelles garanties demandées.

L'OA voit clairement, dans son portefeuille, pourquoi un montant est bloqué ou retirable.

### 9.4 OA individuel sous Bronze : procédure interne

Pour un OA individuel n'ayant pas encore atteint Bronze, la gestion du fournisseur et le paiement de la marchandise sont réalisés **en interne** par la plateforme et ne constituent pas une fonctionnalité publique de l'espace OA.

La procédure interne peut comprendre :

1. déclaration du fournisseur par l'OA ;
2. vérification du fournisseur par l'administrateur ;
3. vérification de la commande et du montant nécessaire ;
4. paiement direct du fournisseur par la plateforme ou mise en place d'une garantie ;
5. affichage dans l'espace OA du bénéfice estimé et du montant retirable autorisé ;
6. décision administrative concernant le retrait.

Le fournisseur, la garantie éventuelle et le paiement interne sont gérés par l'administrateur. L'OA ne peut pas retirer librement l'argent collecté avant l'autorisation prévue.

### 9.5 OA Bronze et Argent

Les OA Bronze et Argent utilisent les procédures de paiement, de retrait et de livraison contrôlées par la plateforme. Ils ne gèrent pas librement une livraison avec leurs propres livreurs.

### 9.6 OA Or

L'OA Or bénéficie d'une autonomie logistique plus importante :

- il peut organiser la livraison avec ses propres livreurs ;
- ses livreurs doivent être déclarés et validés ;
- le QR code doit être scanné lors de la remise ;
- le paiement n'est pas automatiquement libéré au scan ;
- les règles de retrait restent contrôlées par la plateforme.

## 10. Livraison et preuve de remise

### 10.1 Options de livraison

L'acheteur peut choisir, selon les options du groupage :

1. livraison à domicile par un partenaire autorisé, notamment Gozem ou La Poste ;
2. retrait en agence ou point relais partenaire ;
3. remise organisée par un OA Or avec un livreur enregistré.

### 10.2 QR code

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

Le scan confirme la remise et clôture la participation sur le plan opérationnel. Il ne déclenche pas automatiquement le retrait de l'OA.

### 10.3 Confidentialité lors de la livraison

- L'agence ou le partenaire logistique reçoit uniquement les informations nécessaires à la remise.
- L'adresse de livraison n'est pas visible par l'OA lorsqu'elle est traitée par un partenaire.
- L'OA Or peut connaître l'acheteur uniquement au moment de la remise lorsque cela est nécessaire.
- L'OA ne reçoit pas automatiquement les coordonnées permanentes de l'acheteur.

## 11. Chat privé et confidentialité

La plateforme ne comporte **aucun chat public**.

Le Contact Privé permet à un acheteur abonné de discuter avec tous les OA de la plateforme pendant un mois.

Fonctionnalités du chat :

- liste des conversations ;
- recherche d'un OA ;
- création d'une conversation ;
- messages illimités pendant l'abonnement ;
- identifiants internes ou pseudonymes ;
- demande volontaire d'informations sur l'OA ;
- signalement d'un message ;
- modération administrative ;
- historique des messages.

Les coordonnées personnelles ne sont pas révélées automatiquement. Chaque partie choisit les informations qu'elle accepte de communiquer, sous réserve des règles de la plateforme.

Cycle du chat :

```
non_achete → paiement_confirme → chat_actif → chat_expire ou chat_ferme
```

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
- la progression vers 50 et 100 points ;
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
- les informations publiques sur l'OA : grade, note et volume d'activité ;
- les conditions de participation ;
- les boutons Participer et Partager.

### 12.2 Interface OA

Avant validation KYC, l'OA voit un espace d'attente contenant :

- le statut du dossier ;
- les documents manquants ;
- les demandes de correction ;
- les messages de l'administrateur.

Après validation, l'espace OA comprend :

- Tableau de bord ;
- Mes groupages ;
- Créer un groupage ;
- Mes tickets ;
- Mon portefeuille ;
- Mes points et mon grade ;
- Mes livraisons ;
- Mes conversations ;
- Mon dossier KYC ;
- Mes livreurs, uniquement pour l'OA Or ;
- Notifications.

Le tableau de bord OA affiche :

- le grade et la commission ;
- les points et la progression ;
- les tickets et quotas disponibles ;
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

L'OA consulte les participations sous forme de références internes. Il ne voit pas automatiquement les numéros, adresses ou e-mails des acheteurs.

### 12.3 Fonctionnalités par grade OA

| Fonctionnalité | Bronze | Argent | Or |
|---|:---:|:---:|:---:|
| Créer des groupages | Oui | Oui | Oui |
| Consulter le portefeuille | Oui | Oui | Oui |
| Commission | 4 % | 3 % | 2 % |
| Utiliser les agences partenaires | Oui | Oui | Oui |
| Déclarer un fournisseur | Selon procédure interne | Selon règles | Selon règles |
| Gérer ses propres livreurs | Non | Non | Oui |
| Organiser une remise directe | Non | Non | Oui |
| Connaître l'acheteur à la remise | Non | Non | Oui, uniquement si nécessaire |

### 12.4 Interface administrateur

La console administrateur comprend :

- Tableau de bord ;
- Utilisateurs ;
- Dossiers KYC ;
- OA ;
- Groupages ;
- Articles ;
- Paiements ;
- Portefeuilles ;
- Retraits ;
- Remboursements ;
- Points et grades ;
- Chats privés ;
- Fournisseurs ;
- Agences et partenaires ;
- Livreurs OA Or ;
- Notifications ;
- Journal d'activité ;
- Paramètres.

L'administrateur peut :

- valider, refuser ou suspendre un OA ;
- consulter les pièces KYC ;
- modifier les règles de points ;
- contrôler les commissions ;
- autoriser ou refuser les retraits ;
- gérer les remboursements ;
- vérifier les fournisseurs des OA individuels sous Bronze ;
- gérer les livreurs des OA Or ;
- consulter les scans QR ;
- modérer les chats signalés ;
- consulter toutes les actions sensibles dans le journal.

### 12.5 Matrice des permissions

| Fonctionnalité | Acheteur | OA | Administrateur |
|---|:---:|:---:|:---:|
| Consulter le catalogue | Oui | Oui | Oui |
| Participer à un groupage | Oui | Oui | Oui |
| Créer un groupage | Non | Oui, avec ticket | Oui |
| Acheter un ticket | Non | Oui | Oui |
| Consulter son portefeuille OA | Non | Oui | Oui |
| Autoriser un retrait | Non | Non | Oui |
| Souscrire au Contact Privé | Oui, dès 50 points | Non requis | Gestion |
| Utiliser le chat privé | Oui, avec abonnement | Répondre | Modérer |
| Gérer les livreurs | Non | OA Or uniquement | Oui |
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

L'OA reçoit des notifications pour :

- validation ou refus KYC ;
- achat et consommation d'un ticket ;
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

### 14.1 Dossier OA

```
brouillon → soumis → en_verification → valide
                             ├── documents_a_corriger
                             ├── refuse
                             └── suspendu
```

### 14.2 Groupage

```
brouillon → en_cours → cloture_automatique
   │
   ├── minimum_atteint → finance → approvisionnement → livraison → termine
   │
   └── minimum_non_atteint
          ├── OA_maintient → finance → approvisionnement
          ├── OA_renonce → annule → remboursements
          └── silence_7_jours → annule → remboursements
```

### 14.3 Participation

```
en_attente → paiement_confirme → qr_genere → preparee
   ├── livraison_domicile
   ├── agence_partenaire
   └── remise_oa_or
        → qr_scane → livree → terminee
```

Une participation payée ne possède aucun état d'annulation à la demande de l'acheteur.

### 14.4 Portefeuille et retrait

```
paiement_confirme → solde_oa_bloque →
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
| Portefeuille OA | Le paiement est crédité dans le portefeuille interne et le retrait est contrôlé par l'administrateur. |
| Ticket OA | Le paiement simulé de 100 FCFA donne 10 créations et 2 points au total. |
| Chat privé | Le paiement simulé de 2 000 FCFA active l'abonnement mensuel avec 50 points minimum et donne 10 points. |
| Points | Les achats donnent 5 points et les parrainages validés donnent 2 points. |
| QR livraison | Le QR est généré après paiement et son scan confirme la remise sans déclencher automatiquement le retrait. |
| Fournisseur sous Bronze | La vérification et le paiement sont simulés dans la console administrateur. |
| Partenaires logistiques | Les agences et livraisons sont simulées. |
| Livraison OA Or | Le livreur enregistré et le scan QR sont simulés. |

Le code métier — paiements, portefeuille, remboursements, commissions, points, grades, QR code, chat, confidentialité et règles de livraison — doit être écrit de manière réelle. Seuls les appels aux services externes sont simulés.

## 16. Pile technique

| Couche | Choix |
|---|---|
| API | Django 5.2 + Django REST Framework |
| Base | PostgreSQL 17, SQLite en secours hors déploiement |
| Front | React 19 + Vite + Tailwind CSS |
| Applications front | Boutique acheteur et console OA/administrateur selon les permissions |
| Exécution | Docker Compose (`base`, `api`, `boutique`, `admin`) |
| Configuration | Un seul `.env` à la racine, lu par Django, Vite et Compose |
| Médias | Cloudinary : maximum 3 images et 1 vidéo par article |
| Authentification | Numéro de téléphone vérifié par SMS ; SMS et Mobile Money simulés dans le prototype |

Le français est la langue du code : noms de modèles, champs, routes et variables. Le terme métier à utiliser est **Organisateur d'Achat (OA)**.
