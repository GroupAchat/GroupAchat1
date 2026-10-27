# Group Achat — Cahier des charges

Plateforme web **mobile-first** d'intermédiation et de gestion d'achats groupés au Togo.

## 1. Problématique

Au Togo, les achats groupés se font de manière informelle, principalement sur WhatsApp :

- **Côté acheteur** : forte méfiance — peur de perdre son argent, sans garantie ni recours.
- **Côté Organisateur d'Achat (OA)** : gestion chaotique — suivi manuel des listes, vérification fastidieuse des captures d'écran Mobile Money, risques d'impayés et de litiges à la livraison.

## 2. Solution

| | Garantie apportée |
|---|---|
| **Acheteur** | « Livré ou remboursé » : paiement sous **séquestre** et validation de livraison par **QR code unique**, généré après le paiement de la participation. |
| **Organisateur d'Achat (OA)** | Outil de gestion automatisée : suivi des participations, gestion d'un article par groupage, preuve de livraison opposable et visibilité au-delà de ses cercles habituels. |

### Ce que la plateforme garantit — et ce qu'elle ne garantit pas

Group Achat **met en relation, elle n'arbitre pas**. Elle garantit l'argent de la collecte : les fonds restent sous séquestre, et un groupage annulé rembourse.
Elle ne se prononce pas sur la marchandise — ni sur sa qualité, ni sur sa conformité, ni sur ce qui s'est dit au point de retrait.

L'acheteur et l'OA ne se connaissent pas directement. Les échanges passent exclusivement par la plateforme au moyen du **chat privé payant**. Il n'existe plus de fil de discussion public sur la plateforme.

Une plainte ou une question sur un produit passe donc par le chat privé avec l'OA. La plateforme n'arbitre pas le différend ; elle conserve les échanges et peut les modérer selon ses règles.

## 3. Les trois acteurs

### 🛒 L'acheteur

1. **Accès** — explore le catalogue **librement, sans inscription**. Il crée son compte au moment de commander : **nom, prénom, numéro de téléphone, mot de passe** et **adresse e-mail facultative**. Un **code reçu par SMS** vérifie ensuite le numéro.
2. **Découverte** — parcourt les groupages disponibles ou soumet une demande de produit dans l'espace communautaire. L'identité et les coordonnées de l'OA ne sont pas visibles.
3. **Participation** — rejoint un groupage portant sur **un seul article** et règle sa part en ligne. L'argent part en séquestre et n'est jamais versé directement à l'OA.
4. **Communication** — peut acheter l'abonnement **Contact Privé** pour communiquer avec l'OA dans un chat interne. L'acheteur doit avoir au moins **50 points** et payer **2 000 FCFA par mois**. Le nombre de messages n'est pas limité pendant la période active.
5. **Choix de réception** — choisit la livraison à domicile ou le retrait dans une agence partenaire, selon les options proposées pour le groupage. La remise en main propre par l'OA est réservée aux groupages organisés par un OA de grade **Or**.
6. **Réception** — après le paiement de sa part, reçoit un **QR code unique** lié à sa participation. Il le présente lors de la remise du colis ; le scan prouve la livraison et clôture sa commande.

### 🛍️ L'Organisateur d'Achat (OA)

L'OA porte un ou plusieurs groupages. Chaque groupage concerne **un seul article**. Cet article peut comporter jusqu'à **trois images et une vidéo**.

À l'inscription, l'OA choisit l'un des profils suivants :

- **Commerçant** : boutique ou vendeur professionnel ;
- **Organisateur individuel** : particulier ou initiateur de groupages.

Par principe de confidentialité, **l'OA ne connaît pas l'identité ni les coordonnées personnelles de l'acheteur**, et l'acheteur ne connaît pas non plus l'identité ni les coordonnées directes de l'OA. Les échanges se font uniquement dans le chat privé de la plateforme.

1. **Inscription et confiance** — s'inscrit, choisit son profil et soumet son dossier KYC : pièce d'identité, justificatifs liés à son profil, numéro Mobile Money et informations concernant ses livreurs ou responsables de remise lorsque cela est nécessaire.
2. **Validation** — tant que l'administrateur n'a pas validé son dossier, l'OA n'accède pas à l'espace de création et de gestion des groupages.
3. **Publication** — après validation, il achète un ticket de publication à **100 FCFA**, permettant de publier jusqu'à **10 groupages**. Chaque groupage présente un seul article, avec ses images, sa vidéo éventuelle, son prix, son minimum de pièces, sa date limite et ses options de réception.
4. **Collecte** — suit la jauge et les participations au moyen d'identifiants internes. Il ne voit pas les coordonnées personnelles des acheteurs.
5. **Communication** — répond aux acheteurs dans le chat privé, uniquement lorsque ceux-ci ont activé leur abonnement Contact Privé. Les messages sont illimités pendant la durée de l'abonnement.
6. **Approvisionnement et livraison** — après la clôture du groupage, prépare l'article et le remet aux agences partenaires. Un OA de grade **Or** peut, en plus, remettre lui-même les colis et connaître l'acheteur au moment de la remise.
7. **Réception des fonds** — les fonds sont libérés conformément aux règles du séquestre, après validation des conditions de livraison et déduction de la commission correspondant au grade de l'OA.

### 🛡️ L'administrateur

1. Vérifie le dossier KYC de l'OA, son profil et les justificatifs associés.
2. Vérifie les informations déclarées sur les livreurs ou responsables de remise des OA individuels.
3. Valide ou refuse l'accès de l'OA à son espace de gestion.
4. Supervise et modère la plateforme ainsi que les chats privés.
5. Consigne les fonds sur le compte séquestre, contrôle les remboursements et libère les montants selon les règles prévues.
6. Contrôle les commissions, les tickets de publication, les points et les grades.
7. Supervise les agences partenaires et les opérations de livraison.
8. Clôture les participations lorsque le QR code est scanné ou lorsque les règles de livraison réputée acquise s'appliquent.

## 4. Article et groupage

- **Un groupage correspond à un seul article.**
- Un article peut avoir au maximum **trois images et une vidéo**.
- La vidéo est facultative et doit disposer d'une image d'aperçu si le format technique l'exige.
- La vignette du catalogue utilise une image de l'article.
- Le prix, le minimum de pièces, la date limite et les modalités de réception sont définis au niveau du groupage.
- Un acheteur peut participer à plusieurs groupages, mais une participation concerne un article et un groupage déterminés.
- **Une participation payée ne peut pas être annulée par l'acheteur.** Elle ne peut prendre fin que par la livraison, le remboursement d'un groupage annulé ou l'application d'une règle de clôture prévue par le présent cahier des charges.

## 5. Profils des Organisateurs d'Achat

| Profil | Description | Justificatifs indicatifs |
|---|---|---|
| **Commerçant** | Boutique ou vendeur professionnel proposant des articles dans le cadre de son activité. | Pièce d'identité, justificatif de l'activité ou de la boutique, numéro Mobile Money vérifié. |
| **Organisateur individuel** | Particulier ou initiateur de groupages organisant des achats ponctuels ou communautaires. | Pièce d'identité, numéro Mobile Money vérifié et informations sur le ou les livreurs/responsables de remise. |

## 6. Modèle économique et monétisation

- **Ticket de publication** : **100 FCFA** pour publier jusqu'à **10 groupages**. Le paiement d'un ticket rapporte **2 points** à son acheteur.
- **Commission sur les ventes** : la plateforme prélève une commission sur chaque groupage abouti selon le grade de l'OA :
  - **Bronze : 4 %** ;
  - **Argent : 3 %** ;
  - **Or : 2 %**.
- **Chat privé — Contact Privé** : l'acheteur doit avoir au moins **50 points** et payer **2 000 FCFA par mois** pour débloquer le chat privé avec un OA.
- **Durée de l'accès** : l'abonnement est mensuel. Pendant sa période de validité, l'acheteur peut échanger avec l'OA dans le cadre prévu par la plateforme, sans limite de messages.
- **Portée du chat** : l'abonnement donne accès au chat privé avec l'OA concerné et à ses groupages accessibles dans la plateforme, sans révéler les coordonnées directes de l'une ou l'autre partie.
- **Aucun chat public** : la plateforme ne comporte plus de fil de discussion public sous les groupages. Toute communication avec l'OA passe par le chat privé payant.
- **Acheteur** : aucun frais obligatoire ne lui est facturé pour participer à un groupage, hors abonnement Contact Privé et frais de livraison éventuellement affichés.
- **Transparence** : le prix de l'abonnement, le taux de commission, les frais de livraison et le montant net revenant à l'OA sont présentés avant validation.

## 7. Parrainage, sponsoring, points et grades

### Système de points

Les règles de points sont configurables par l'administrateur. La règle déjà définie est la suivante :

- **Paiement d'un ticket de publication** : **2 points**.

Les points peuvent également être attribués pour d'autres actions — achats, parrainages, création de groupages ou utilisation du chat — mais les montants correspondants restent à définir avant leur implémentation.

### Grades et commissions

| Grade | Seuil de points | Commission sur les groupages aboutis |
|---|---:|---:|
| **Bronze** | **250 points** | **4 %** |
| **Argent** | **400 points** | **3 %** |
| **Or** | **600 points** | **2 %** |

Les conditions de perte ou de rétrogradation d'un grade ne sont pas encore définies. Tant qu'elles ne sont pas validées, un grade obtenu est conservé.

### Sponsoring des OA individuels

Le sponsoring concerne les **OA individuels qui n'ont pas encore atteint le grade Bronze**. Il vise à éviter qu'un OA débutant parte directement avec l'argent des acheteurs sans dispositif de confiance suffisant.

Avant qu'un OA individuel atteigne Bronze :

- l'administrateur demande les informations sur le ou les livreurs ou responsables de remise de l'OA ;
- ces personnes sont vérifiées et enregistrées dans le dossier de l'OA ;
- la commande et la remise peuvent être suivies par la plateforme et les agences partenaires ;
- les conditions de paiement ou de libération des fonds sont contrôlées par l'administrateur jusqu'à l'obtention du grade Bronze.

Le fonctionnement détaillé du sponsoring, les personnes éligibles et les éventuels bonus associés devront être précisés dans les règles administratives avant la mise en production.

## 8. Règles métier

- **Confidentialité par défaut** : l'OA et l'acheteur ne voient pas les coordonnées directes l'un de l'autre.
- **Intermédiation obligatoire** : les échanges passent par le chat privé de la plateforme. Aucun chat public n'est disponible.
- **Participation irrévocable** : une participation payée ne peut pas être annulée par l'acheteur.
- **QR code de livraison** : le QR code est généré **après confirmation du paiement de la participation**. Il est unique pour le couple groupage/article et acheteur. Le scan lors de la remise valide la réception et constitue la preuve de livraison.
- **Séquestre** : les fonds restent consignés jusqu'à la clôture prévue et ne sont libérés ou remboursés que selon les règles du groupage.
- **Clôture** : à la date limite, la collecte se ferme automatiquement et le groupage quitte le catalogue.
- **Minimum non atteint** : le groupage n'est pas annulé automatiquement. L'argent reste consigné pendant le délai de décision de sept jours. Sans réponse de l'OA, les participants sont intégralement remboursés.
- **Historique** : un groupage sorti du catalogue reste consultable par les participants concernés.
- **Inscription** : le numéro de téléphone est l'identifiant et doit être vérifié par SMS. Aucun compte n'est nécessaire pour consulter le catalogue.
- **Distribution** : les OA de grade Bronze et Argent remettent les colis aux agences partenaires. Seul un OA de grade **Or** peut remettre lui-même les colis et connaître l'acheteur au moment de la livraison.
- **Colis non récupéré** : relances à J+3 et J+7 ; au bout de 14 jours après la mise à disposition, la livraison est réputée acquise et le dossier se clôt.
- **Frais de remboursement** : en cas de groupage annulé, les frais d'opérateur du remboursement sont à la charge de la plateforme.
- **Demandes communautaires** : un acheteur peut publier une demande de produit et les autres peuvent marquer leur intérêt. Les OA voient les demandes classées par intérêt, sans obtenir les coordonnées personnelles des intéressés.

## 9. Options de livraison et de réception

Les acheteurs disposent des options suivantes selon le groupage :

1. **Livraison à domicile** via les partenaires logistiques autorisés, notamment Gozem ou La Poste ;
2. **Retrait en agence ou point relais partenaire** ;
3. **Remise en main propre par l'OA**, uniquement lorsque l'OA est de grade **Or**.

Pour les OA Bronze et Argent, les agences partenaires reçoivent les colis et assurent la remise aux acheteurs. L'OA ne connaît pas l'identité de l'acheteur.

Pour un OA Or, la remise en main propre est autorisée. L'OA Or peut connaître l'acheteur uniquement au moment de la livraison, afin de vérifier la remise du colis avec le QR code. Cette exception ne donne pas accès aux coordonnées permanentes de l'acheteur dans le tableau de bord.

Le scan du QR code est obligatoire pour valider la livraison. Les frais, délais et zones couvertes sont affichés avant le paiement.

## 10. Sécurité et garanties

- **Paiements sécurisés** : les transactions sont protégées et les fonds restent sous séquestre.
- **Preuve de livraison par QR code** : le QR code est généré après le paiement. Il est scanné à la remise du colis pour prouver que l'acheteur a bien été livré.
- **Garantie acheteur** : l'acheteur bénéficie de la promesse « livré ou remboursé », dans les limites des règles de séquestre et d'annulation.
- **Logistique partenaire** : les agences partenaires sont sélectionnées et encadrées par contrat afin de réduire les risques de retard, de perte ou de mauvaise remise.
- **Confidentialité** : les coordonnées des acheteurs et des OA ne sont pas affichées aux autres parties. Les données de livraison sont limitées aux acteurs autorisés.
- **Modération du chat** : le chat privé peut être signalé, modéré et conservé pour des raisons de sécurité et de conformité.

## 11. Encadrement juridique et administratif

- Rédaction des CGU, CGV, politique de confidentialité et contrats avec les OA, les agences partenaires et les livreurs.
- Définition des critères d'approbation, de validation, de suspension et de retrait applicables aux OA et aux groupages.
- Conservation sécurisée des pièces KYC et traçabilité des décisions administratives.
- Encadrement du sponsoring des OA individuels n'ayant pas atteint Bronze.
- Formalisation des obligations de livraison, de preuve de remise, de traitement des incidents et de protection des données.
- Présentation claire des prix, commissions, abonnement Contact Privé, frais, délais, garanties et limites de responsabilité.

## 12. Comptes et rôles

| Rôle | Accès |
|---|---|
| **Acheteur** | Dès le numéro vérifié : commander, choisir une option de livraison, suivre ses participations, gagner des points et souscrire au chat privé s'il possède au moins 50 points. |
| **Organisateur d'Achat (OA)** | Après validation KYC : créer des groupages, suivre les participations, gérer l'approvisionnement et la remise selon son grade, consulter ses points et sa commission. |
| **Administrateur** | Console séparée : validation KYC, gestion du sponsoring, supervision des fonds, commissions, points, grades, chats et agences partenaires. |

Un acheteur peut demander à devenir OA à tout moment. Il choisit son profil, dépose son dossier KYC et attend la validation sans perdre son historique d'acheteur.

## 13. Mode prototype

Cette première version est une **maquette fonctionnelle**. Aucun flux d'argent, d'envoi SMS ou de livraison réelle n'est branché. Les services tiers sont simulés derrière des interfaces remplaçables :

| Service | Simulation |
|---|---|
| **SMS** | Le code de vérification s'affiche à l'écran au lieu d'être envoyé. |
| **Paiement Mobile Money** | Un bouton TMoney ou Flooz marque instantanément le paiement comme réussi. |
| **Séquestre** | La consignation, la libération et le remboursement sont pilotés par la console d'administration. |
| **Ticket de publication** | Un paiement simulé de 100 FCFA crédite un quota de 10 groupages et 2 points. |
| **Commission** | Le taux de 4 %, 3 % ou 2 % est calculé selon le grade de l'OA, sans prélèvement réel. |
| **Chat privé** | Un paiement simulé de 2 000 FCFA active l'abonnement mensuel, sous réserve d'un solde minimum de 50 points. Les messages sont illimités. |
| **QR de livraison** | Le QR code est généré après le paiement simulé et son scan valide la livraison. |
| **Livraison** | Les agences partenaires sont simulées ; la remise directe est autorisée uniquement pour un OA Or. |
| **Décaissement OA** | Action administrateur enregistrée sans ordre de virement réel. |

Le code métier — séquestre, remboursements, commissions, points, grades, sponsoring, QR de livraison, confidentialité, chat payant et règles de livraison — est écrit pour de vrai ; seule l'exécution des services tiers est factice.

## 14. Chat privé payant

La plateforme ne comporte **aucun chat public**.

- L'acheteur doit avoir au moins **50 points**.
- Il paie **2 000 FCFA** pour activer un abonnement mensuel.
- L'abonnement permet de discuter avec l'OA concerné pendant un mois.
- Le nombre de messages est **illimité** pendant la période active.
- Les échanges se font dans la plateforme, sans partage automatique des numéros, adresses e-mail ou coordonnées directes.
- L'accès au chat est lié à l'OA et à ses groupages accessibles, selon les règles de la plateforme.
- Les messages peuvent être signalés, modérés et conservés par l'administrateur.
- À l'expiration de l'abonnement, le chat passe à l'état expiré et l'acheteur doit renouveler son abonnement pour poursuivre les échanges.

Cycle du chat :

```
non_achete → paiement_confirme → chat_actif → chat_expire ou chat_ferme
```

## 15. Notifications

Les participants sont notifiés lors du paiement enregistré, de la génération du QR code, du financement du groupage, de la mise à disposition de l'article, de la confirmation de l'option de livraison, du suivi logistique, du scan du QR code, de la livraison confirmée, de l'annulation et du remboursement, ainsi que des nouveaux messages privés.

L'OA est notifié de chaque participation, de l'atteinte du minimum, de la décision KYC, de son ticket de publication, de ses points, de son grade, de sa commission, de la livraison et des nouveaux messages du chat privé.

## 16. Cycle de vie d'un groupage et d'une participation

```
brouillon → en_cours → date_limite : clôture_automatique
   │
   ├── minimum atteint ───────→ financee → approvisionnement → livraison → terminee
   │
   └── minimum non atteint ──→ minimum_non_atteint
                                  │
                                  ├── l'OA maintient → financee → …
                                  ├── l'OA renonce → annulee → remboursements
                                  └── silence 7 jours → annulee → remboursements
```

Une participation suit le cycle suivant :

```
en_attente → payee → qr_genere → preparee →
   ├── agence_partenaire
   ├── livraison_domicile
   └── remise_oa_or
        → qr_scane → livree → terminee
```

Une participation payée ne possède aucun état d'annulation à la demande de l'acheteur.

## 17. Pile technique

| Couche | Choix |
|---|---|
| API | Django 5.2 + Django REST Framework |
| Base | PostgreSQL 17 (SQLite en secours hors déploiement) |
| Front | React 19 + Vite + Tailwind CSS — deux applications : boutique et console d'administration |
| Exécution | Docker Compose (`base`, `api`, `boutique`, `admin`) |
| Configuration | un seul `.env` à la racine, lu par Django, Vite et Compose |
| Médias | Cloudinary : maximum 3 images et 1 vidéo par article |
| Authentification | Numéro de téléphone vérifié par SMS ; les services SMS et Mobile Money sont simulés en prototype |

Le français est la langue du code : noms de modèles, de champs, de routes et de variables. Le terme métier à utiliser est **Organisateur d'Achat (OA)** ; l'ancien terme « groupeur » ne doit plus être utilisé, sauf dans un contexte historique ou de migration.
