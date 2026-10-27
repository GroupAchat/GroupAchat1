# Group Achat — Cahier des charges

Plateforme web **mobile-first** d'intermédiation et de gestion d'achats groupés au Togo.

## 1. Problématique

Au Togo, les achats groupés se font principalement de manière informelle, notamment sur WhatsApp. L'acheteur craint de perdre son argent et l'Organisateur d'Achat (OA) gère difficilement les participants, les paiements et les livraisons.

## 2. Solution

Group Achat met en relation les acheteurs et les OA tout en protégeant les paiements. L'acheteur paie sa participation sur la plateforme ; le montant est placé dans le portefeuille interne de l'OA, mais il reste **bloqué et non retirable** selon les règles de la plateforme.

La plateforme ne garantit pas la qualité de la marchandise. Elle garantit la traçabilité du paiement, le traitement des remboursements prévus et la preuve de livraison par QR code.

L'acheteur et l'OA ne connaissent pas automatiquement leurs coordonnées personnelles. L'acheteur peut demander les informations de l'OA dans le chat privé, mais l'OA ne les voit pas automatiquement non plus.

## 3. Acteurs

### Acheteur

- Consulte le catalogue sans inscription.
- Crée un compte au moment de participer : nom, prénom, téléphone, mot de passe et e-mail facultatif.
- Vérifie son numéro par SMS.
- Rejoint un groupage portant sur un seul article et paie sa participation par Mobile Money.
- Reçoit un QR code unique **après confirmation du paiement**.
- Choisit une livraison à domicile, un retrait en agence partenaire ou, lorsque cela est autorisé, une remise organisée par un OA Or.
- Peut souscrire à l'abonnement Contact Privé pour demander des informations à l'OA et discuter avec lui.
- Présente son QR code lors de la remise ; le scan confirme la livraison.

### Organisateur d'Achat (OA)

L'OA peut être :

- **Commerçant** : boutique ou vendeur professionnel ;
- **Organisateur individuel** : particulier ou initiateur de groupages.

L'OA doit être validé par l'administrateur avant d'accéder à son espace de gestion. Il crée des groupages, suit les participations sans voir automatiquement les coordonnées des acheteurs, prépare la commande et organise la livraison selon son grade.

Chaque groupage porte sur **un seul article**, avec au maximum **trois images et une vidéo**.

### Administrateur

L'administrateur valide les OA, supervise les paiements et les portefeuilles, gère les remboursements, les points, les grades, les agences partenaires, les chats signalés et les règles de retrait.

## 4. Article, groupage et participation

- Un groupage correspond à un seul article.
- Un article contient au maximum trois images et une vidéo.
- La vidéo est facultative.
- Le groupage définit le prix, le minimum de pièces, la date limite et les modalités de livraison.
- Le QR code est généré après le paiement confirmé de la participation.
- Le QR code est unique pour la participation, l'article et le groupage.
- Le QR code est scanné lors de la remise pour prouver la livraison.
- Une participation payée ne peut pas être annulée par l'acheteur.

## 5. Modèle économique

### Ticket de publication OA

- Le ticket coûte **100 FCFA**.
- Un ticket permet de créer jusqu'à **10 groupages**.
- Le paiement du ticket donne **2 points au total à l'OA**.
- Ces 2 points sont attribués une seule fois au paiement du ticket et ne sont pas répétés pour chacune des 10 créations.

### Commissions

| Grade de l'OA | Commission plateforme |
|---|---:|
| Bronze | 4 % |
| Argent | 3 % |
| Or | 2 % |

### Abonnement Contact Privé

- L'abonnement est payé par l'acheteur.
- L'acheteur doit posséder au moins **50 points** pour souscrire.
- Les 50 points sont seulement une condition d'accès et ne sont pas consommés.
- L'abonnement coûte **2 000 FCFA par mois**.
- Il donne accès au chat privé avec l'OA concerné.
- Les messages sont illimités pendant le mois actif.
- L'acheteur peut demander à connaître l'OA ou lui demander des informations, mais ces informations ne sont pas révélées automatiquement.
- Le chat ne donne pas automatiquement accès au numéro de téléphone, à l'adresse e-mail ou aux autres coordonnées directes.

### Réduction de livraison

Lorsqu'un acheteur atteint **100 points**, il bénéficie d'une réduction de **50 % sur une livraison**. La réduction est appliquée une seule fois à une livraison éligible et ne réduit pas le prix de l'article.

## 6. Points, parrainage et grades

| Action | Bénéficiaire | Points |
|---|---|---:|
| Paiement d'un ticket de publication à 100 FCFA | OA | 2 points au total par ticket |
| Achat et paiement d'un article | Acheteur | 5 points |
| Parrainage réussi par lien | Acheteur parrain | 2 points |
| Paiement d'un abonnement Contact Privé | Acheteur | 10 points |

Le système ne doit jamais compter deux fois la même action.

### Parrainage acheteur

L'acheteur partage le lien d'un article ou d'un groupage. Lorsque de nouveaux acheteurs rejoignent le groupage grâce à ce lien et paient leur participation, le parrain reçoit **2 points** par parrainage validé. Un simple clic, une inscription ou un paiement annulé ne donne pas de point.

### Grades OA

| Grade | Seuil de points | Commission |
|---|---:|---:|
| Bronze | 250 points | 4 % |
| Argent | 400 points | 3 % |
| Or | 600 points | 2 % |

Les conditions de perte ou de rétrogradation d'un grade ne sont pas encore définies. Tant qu'elles ne sont pas validées, un grade obtenu est conservé.

## 7. Paiements, portefeuille OA et retrait

- Le paiement de l'acheteur est confirmé par la plateforme.
- Le montant payé est automatiquement crédité dans le **portefeuille interne de l'OA**.
- Le montant affiché dans le portefeuille ne devient pas automatiquement retirable.
- La plateforme bloque le retrait selon le statut de l'OA, le grade, le groupage, le fournisseur et les règles administratives.
- Le solde retirable et le bénéfice estimé sont affichés séparément du solde bloqué.
- Le QR code de livraison confirme la remise du colis, mais **le paiement n'est pas libéré à la livraison**. Le scan sert de preuve de livraison et de clôture opérationnelle de la participation.
- Les règles de retrait sont contrôlées par l'administrateur et peuvent dépendre du profil de l'OA et de son grade.

### OA individuel sous Bronze

Pour un OA individuel n'ayant pas encore atteint Bronze, la plateforme peut gérer en interne le paiement du fournisseur. Cette opération n'est pas réalisée directement dans l'interface publique de la plateforme.

- L'OA déclare son fournisseur à l'administrateur.
- L'administrateur vérifie le fournisseur et la commande.
- La plateforme peut payer le fournisseur directement ou demander une garantie selon le dossier de l'OA.
- L'OA voit dans son compte le montant correspondant à son bénéfice et le montant retirable selon la décision interne.
- Le fournisseur, le paiement interne, la garantie éventuelle et la décision de retrait sont gérés hors de la plateforme publique.

## 8. Livraison

Les options sont :

1. livraison à domicile par un partenaire logistique autorisé, notamment Gozem ou La Poste ;
2. retrait dans une agence ou un point relais partenaire ;
3. livraison organisée par un OA Or avec ses livreurs enregistrés.

### OA Bronze et Argent

Les OA Bronze et Argent remettent les colis aux agences partenaires ou utilisent les partenaires logistiques autorisés. Ils ne connaissent pas automatiquement l'identité ni les coordonnées de l'acheteur.

### OA Or

L'OA Or peut gérer ses livraisons avec ses propres livreurs enregistrés. La plateforme doit connaître et enregistrer les livreurs responsables de la remise. L'OA Or peut connaître l'acheteur uniquement au moment de la remise si cela est nécessaire, mais il ne reçoit pas automatiquement ses coordonnées permanentes.

Dans tous les cas, le QR code doit être scanné pour confirmer la remise. Le scan enregistre la date, l'heure, le responsable de remise et le statut de livraison.

## 9. Confidentialité et chat privé

- Il n'existe aucun chat public.
- Les échanges passent par le chat privé payant.
- L'acheteur doit avoir au moins 50 points et payer l'abonnement mensuel de 2 000 FCFA.
- Les messages sont illimités pendant l'abonnement.
- L'acheteur peut demander à connaître l'OA, mais l'OA ne lui est pas automatiquement révélé par défaut.
- L'acheteur et l'OA peuvent échanger sans voir automatiquement leurs numéros, adresses e-mail ou coordonnées directes.
- Les messages peuvent être signalés, modérés et conservés par l'administrateur.

Cycle du chat :

```
non_achete → paiement_confirme → chat_actif → chat_expire ou chat_ferme
```

## 10. Règles métier

- Les participations payées ne peuvent pas être annulées par l'acheteur.
- À la date limite, la collecte se ferme automatiquement.
- Si le minimum n'est pas atteint, l'argent reste consigné pendant sept jours afin que l'OA décide de maintenir ou d'abandonner le groupage.
- Après sept jours sans décision, le groupage est annulé et les acheteurs sont remboursés.
- Les frais opérateur des remboursements sont pris en charge par la plateforme.
- Un QR code déjà utilisé, invalide ou appartenant à un autre groupage doit être refusé.
- Les participants conservent l'historique de leur participation, du chat et de la livraison.
- Relances pour colis non récupéré à J+3 et J+7 ; après 14 jours, la livraison est réputée acquise selon les règles applicables.

## 11. Encadrement administratif et juridique

- CGU, CGV et politique de confidentialité.
- Contrats avec les OA, fournisseurs, agences partenaires et livreurs.
- Procédure de validation, suspension et retrait des OA.
- Procédure interne de gestion des fournisseurs des OA individuels sous Bronze.
- Traçabilité des paiements, remboursements, portefeuilles, retraits et scans QR.
- Information claire sur les commissions, abonnements, points, réductions et frais de livraison.

## 12. Comptes et rôles

| Rôle | Accès |
|---|---|
| Acheteur | Consulter le catalogue, participer, recevoir un QR code, gagner des points, parrainer et souscrire au chat privé à partir de 50 points. |
| Organisateur d'Achat (OA) | Après validation KYC : créer des groupages, consulter son portefeuille, suivre les participations et organiser la livraison selon son grade. |
| Administrateur | Valider les OA, contrôler les fournisseurs, gérer les portefeuilles, retraits, remboursements, points, grades, chats et partenaires. |

## 13. Mode prototype

| Service | Simulation |
|---|---|
| SMS | Le code de vérification s'affiche à l'écran. |
| Paiement Mobile Money | Un bouton confirme immédiatement le paiement. |
| Portefeuille OA | Le paiement est crédité dans le portefeuille interne ; le retrait reste bloqué ou autorisé par l'administrateur. |
| Ticket OA | Le paiement simulé de 100 FCFA donne 10 créations et 2 points au total. |
| Chat privé | Le paiement simulé de 2 000 FCFA active l'abonnement mensuel si l'acheteur possède au moins 50 points. Il donne 10 points. |
| Points | Les achats donnent 5 points, les parrainages validés 2 points et le ticket OA 2 points au total. |
| QR livraison | Le QR est généré après paiement et son scan confirme la livraison, sans déclencher automatiquement le retrait. |
| Fournisseur sous Bronze | La vérification et le paiement du fournisseur sont simulés par l'administrateur dans le cadre d'une procédure interne. |
| Livraison OA Or | Le livreur enregistré et le scan QR sont simulés sans service logistique réel. |

## 14. Cycles de vie

### Groupage

```
brouillon → en_cours → date_limite : cloture_automatique
   │
   ├── minimum atteint → finance → approvisionnement → livraison → termine
   │
   └── minimum non atteint → minimum_non_atteint
                                ├── OA maintient → finance
                                ├── OA renonce → annule → remboursements
                                └── silence 7 jours → annule → remboursements
```

### Participation et QR code

```
en_attente → paiement_confirme → qr_genere → preparee
   ├── agence_partenaire
   ├── livraison_domicile
   └── remise_oa_or
        → qr_scane → livree → terminee
```

Le scan du QR code clôture la livraison, mais ne rend pas automatiquement le solde de l'OA retirable.

## 15. Pile technique

| Couche | Choix |
|---|---|
| API | Django 5.2 + Django REST Framework |
| Base | PostgreSQL 17 (SQLite en secours hors déploiement) |
| Front | React 19 + Vite + Tailwind CSS — boutique et console d'administration |
| Exécution | Docker Compose (`base`, `api`, `boutique`, `admin`) |
| Configuration | Un seul `.env` à la racine, lu par Django, Vite et Compose |
| Médias | Cloudinary : maximum 3 images et 1 vidéo par article |
| Authentification | Numéro de téléphone vérifié par SMS ; SMS et Mobile Money simulés dans le prototype |

Le français est la langue du code : noms de modèles, champs, routes et variables. Le terme métier à utiliser est **Organisateur d'Achat (OA)** ; l'ancien terme « groupeur » ne doit plus être utilisé, sauf dans un contexte historique ou de migration.
