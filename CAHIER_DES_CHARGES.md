# Group Achat — Cahier des charges

Plateforme web **mobile-first** d'intermédiation et de gestion d'achats groupés au Togo.

## 1. Problématique

Au Togo, les achats groupés se font de manière informelle, principalement sur WhatsApp :

- **Côté acheteur** : forte méfiance — peur de perdre son argent, sans garantie ni recours.
- **Côté Organisateur d'Achat (OA)** : gestion chaotique — suivi manuel des listes, vérification fastidieuse des paiements Mobile Money, risques d'impayés et de litiges à la livraison.

## 2. Solution

| Acteur | Garantie apportée |
|---|---|
| **Acheteur** | Promesse « livré ou remboursé » : paiement sous **séquestre** et validation de livraison par un **QR code unique**, généré après le paiement de sa participation. |
| **OA** | Outil de gestion des groupages : suivi des participations, gestion d'un article par groupage, accès à un système de points et preuve de livraison. |

### Ce que la plateforme garantit — et ce qu'elle ne garantit pas

Group Achat **met en relation, elle n'arbitre pas**. Elle garantit l'argent de la collecte : les fonds restent sous séquestre et un groupage annulé est remboursé selon les règles prévues.

Elle ne se prononce pas sur la qualité, la conformité ou la valeur de la marchandise. Les échanges entre l'acheteur et l'OA se font exclusivement dans le **chat privé payant**. Aucun chat public n'est disponible.

L'acheteur et l'OA ne connaissent pas les coordonnées directes l'un de l'autre. L'exception concerne l'OA de grade **Or**, qui peut connaître l'acheteur uniquement au moment de la remise en main propre afin de confirmer la livraison.

## 3. Les acteurs

### 🛒 L'acheteur

1. Explore le catalogue librement, sans inscription.
2. Crée un compte au moment de commander : nom, prénom, numéro de téléphone, mot de passe et e-mail facultatif.
3. Vérifie son numéro par code SMS.
4. Rejoint un groupage portant sur **un seul article** et paie sa participation par Mobile Money.
5. Reçoit un **QR code unique après confirmation du paiement**.
6. Choisit une livraison à domicile, un retrait en agence partenaire ou, uniquement pour un OA Or, une remise en main propre.
7. Peut souscrire à l'abonnement **Contact Privé** pour connaître l'OA et discuter avec lui.
8. Présente son QR code lors de la remise. Le scan confirme la livraison et clôture sa commande.

### 🛍️ L'Organisateur d'Achat (OA)

L'OA peut être :

- **Commerçant** : boutique ou vendeur professionnel ;
- **Organisateur individuel** : particulier ou initiateur de groupages.

L'OA ne voit pas l'identité ni les coordonnées personnelles des acheteurs. Il utilise les références générées par la plateforme et communique avec les acheteurs via le chat privé lorsque ceux-ci disposent d'un abonnement actif.

1. S'inscrit, choisit son profil et dépose son dossier KYC.
2. Attend la validation de l'administrateur avant d'accéder à l'espace OA.
3. Paie un ticket de publication de **100 FCFA**, donnant droit à la création de **10 groupages**.
4. Reçoit **2 points** au moment du paiement de ce ticket.
5. Crée des groupages portant chacun sur un seul article, avec au maximum trois images et une vidéo.
6. Suit les participations et la jauge sans accéder aux coordonnées personnelles des acheteurs.
7. Prépare les colis et les remet à une agence partenaire, sauf s'il est OA Or.
8. L'OA Or peut organiser lui-même la livraison avec ses propres livreurs enregistrés et connaître l'acheteur au moment de la remise.

### 🛡️ L'administrateur

L'administrateur :

- vérifie les dossiers KYC des OA ;
- valide, refuse ou suspend un compte OA ;
- contrôle les tickets, points, grades et commissions ;
- supervise le séquestre, les remboursements et les décaissements ;
- enregistre les fournisseurs déclarés par les OA individuels débutants lorsque le dispositif de sponsoring s'applique ;
- vérifie les livreurs déclarés par les OA Or ;
- supervise les agences partenaires ;
- modère les chats privés ;
- vérifie que chaque livraison est confirmée par le scan du QR code.

## 4. Article et groupage

- **Un groupage correspond à un seul article.**
- Un article peut contenir au maximum **trois images et une vidéo**.
- La vidéo est facultative.
- La fiche du groupage indique le prix, le minimum de pièces, la date limite et les modalités de livraison.
- Le QR code de livraison est généré uniquement après confirmation du paiement de la participation.
- Une participation payée ne peut pas être annulée par l'acheteur.

## 5. Modèle économique

### Ticket de publication OA

- Le ticket coûte **100 FCFA**.
- Un ticket permet de créer **10 groupages**.
- Le paiement du ticket rapporte **2 points à l'OA**.
- Le ticket et le quota de créations sont enregistrés dans le compte de l'OA.

### Commission sur les groupages aboutis

| Grade de l'OA | Commission plateforme |
|---|---:|
| **Bronze** | **4 %** |
| **Argent** | **3 %** |
| **Or** | **2 %** |

### Abonnement Contact Privé de l'acheteur

- L'abonnement est payé par **l'acheteur**, et non par l'OA.
- L'acheteur doit avoir au moins **50 points** pour souscrire.
- Le prix est de **2 000 FCFA par mois**.
- L'abonnement permet de connaître l'OA concerné et de discuter avec lui dans le chat privé de la plateforme.
- Le nombre de messages est **illimité** pendant la période d'abonnement.
- Les coordonnées directes, notamment le numéro de téléphone et l'adresse e-mail, ne sont pas automatiquement révélées.
- L'accès au chat est lié aux OA et aux groupages autorisés par la plateforme.

### Réduction de livraison

- Lorsqu'un acheteur atteint **100 points**, il bénéficie d'une **réduction de 50 % sur ses frais de livraison**.
- La réduction est appliquée selon les conditions affichées au moment du choix de la livraison.
- Elle ne s'applique pas au prix de l'article et ne transforme pas la livraison en service gratuit si des frais minimums sont prévus.

## 6. Système de points, parrainage et grades

### Attribution des points

| Action | Bénéficiaire | Points |
|---|---|---:|
| Paiement d'un ticket de publication de 100 FCFA | OA | **2 points** |
| Achat et paiement d'un article | Acheteur | **5 points** |
| Parrainage réussi | Acheteur parrain | **2 points** |
| Souscription à un abonnement Contact Privé | Acheteur | **Points attribués selon la règle configurée par l'administrateur** |
| Création d'un groupage au moyen d'un ticket payé | OA | **2 points**, inclus dans la règle du ticket |

Le système doit empêcher qu'une même action soit comptée plusieurs fois pour la même opération.

### Parrainage acheteur

Un acheteur peut publier ou partager le lien d'un article ou d'un groupage. Lorsque de nouveaux acheteurs rejoignent le groupage grâce à ce lien et paient leur participation, le parrain reçoit **2 points par parrainage validé**, selon les règles anti-fraude de la plateforme.

Un parrainage n'est validé qu'après une participation réellement payée. Les clics, inscriptions seules ou paiements annulés ne donnent pas droit aux points.

### Grades OA

| Grade | Seuil de points | Commission |
|---|---:|---:|
| **Bronze** | **250 points** | **4 %** |
| **Argent** | **400 points** | **3 %** |
| **Or** | **600 points** | **2 %** |

Les conditions de perte ou de rétrogradation d'un grade ne sont pas encore définies. Tant qu'elles ne sont pas validées, un grade obtenu est conservé.

Les principaux avantages de l'OA Or sont :

- commission réduite à 2 % ;
- possibilité de gérer directement la livraison avec ses livreurs enregistrés ;
- possibilité de remettre lui-même les colis ;
- possibilité de connaître l'acheteur uniquement lors de la remise ;
- suivi de la livraison par QR code obligatoire.

## 7. Dispositif de sponsoring des OA individuels débutants

Le **sponsoring** est un dispositif de sécurité distinct du fonctionnement de l'OA Or.

Il concerne les **OA individuels qui n'ont pas encore atteint le grade Bronze**, afin d'éviter qu'un nouvel OA puisse recevoir et utiliser librement l'argent des acheteurs sans contrôle suffisant.

Dans ce dispositif :

1. l'OA individuel débutant déclare le fournisseur auprès duquel il compte acheter la marchandise ;
2. l'administrateur vérifie le fournisseur et les informations nécessaires à la commande ;
3. la plateforme peut contrôler ou effectuer le paiement de la marchandise auprès du fournisseur déclaré ;
4. les fonds des acheteurs restent sous le contrôle de la plateforme jusqu'à la confirmation des étapes prévues ;
5. la livraison est effectuée par une agence partenaire ou par un livreur enregistré, selon la décision de la plateforme ;
6. le paiement ou le décaissement est libéré selon la confirmation de la commande et de la livraison par QR code.

Le sponsoring est applicable aux OA individuels débutants tant qu'ils n'ont pas atteint le grade Bronze. Les modalités précises de paiement du fournisseur, les justificatifs exigés et les contrôles administratifs sont définis par la plateforme avant la mise en production.

Un OA Or n'est pas soumis au passage par l'agence partenaire : il peut gérer la livraison avec ses propres livreurs, à condition que ces livreurs soient déclarés et vérifiés par l'administrateur. La plateforme doit seulement enregistrer le scan du QR code afin de confirmer que le colis a été remis.

## 8. Règles métier

- **Séquestre** : les fonds d'une participation restent consignés selon le cycle du groupage et les règles de sponsoring applicables.
- **Participation irrévocable** : une participation payée ne peut pas être annulée par l'acheteur.
- **QR code** : le QR code est généré après le paiement confirmé de la participation. Il est lié à l'acheteur, au groupage et à l'article.
- **Validation de livraison** : le QR code est scanné lors de la remise. Un QR déjà utilisé, invalide ou appartenant à un autre groupage doit être refusé.
- **Preuve de livraison** : le scan enregistre la date, l'heure, le lieu ou le responsable de remise, puis marque la participation comme livrée.
- **Anonymat** : l'OA et l'acheteur ne voient pas les coordonnées directes l'un de l'autre. L'OA Or ne peut connaître l'acheteur qu'au moment de la remise.
- **Clôture** : à la date limite, la collecte se ferme automatiquement et le groupage quitte le catalogue.
- **Minimum non atteint** : le groupage n'est pas annulé automatiquement. L'argent reste consigné pendant sept jours, le temps que l'OA décide de maintenir ou d'abandonner la commande.
- **Absence de décision** : après sept jours sans réponse de l'OA, le groupage est annulé et les acheteurs sont intégralement remboursés.
- **Historique** : les participants conservent l'accès à l'historique du groupage, de leur participation, du chat et de la livraison.
- **Colis non récupéré** : relances à J+3 et J+7 ; après 14 jours suivant la mise à disposition, la livraison est réputée acquise selon les règles applicables.
- **Frais de remboursement** : les frais opérateur d'un remboursement sont pris en charge par la plateforme.
- **Aucun chat public** : toutes les communications avec l'OA passent par le chat privé payant.

## 9. Options de livraison

1. **Livraison à domicile** par un partenaire logistique autorisé, notamment Gozem ou La Poste ;
2. **Retrait dans une agence ou un point relais partenaire** ;
3. **Remise directe par un OA Or** ou par un livreur enregistré par cet OA.

Pour un OA Bronze, Argent ou un OA individuel sous le dispositif de sponsoring, les colis sont remis à une agence partenaire ou à un livreur autorisé par la plateforme.

Pour un OA Or :

- l'OA peut organiser lui-même la livraison ;
- ses livreurs doivent être déclarés et vérifiés ;
- la plateforme enregistre l'identité du livreur responsable de la remise ;
- le QR code doit obligatoirement être scanné ;
- l'OA peut connaître l'acheteur au moment de la remise uniquement ;
- l'OA ne reçoit pas les coordonnées permanentes de l'acheteur dans son tableau de bord.

Pour la livraison à domicile, l'adresse et le numéro nécessaires sont transmis uniquement au partenaire logistique autorisé.

## 10. Sécurité et garanties

- Paiements protégés et fonds sous séquestre.
- QR code unique généré après paiement.
- QR code à usage unique et refus des scans invalides ou déjà utilisés.
- Promesse « livré ou remboursé » dans les limites des règles du groupage.
- Vérification des OA, fournisseurs, agences partenaires et livreurs déclarés.
- Conservation de la preuve de scan avec date, heure et responsable de remise.
- Protection des données KYC, des coordonnées et des conversations privées.
- Modération et conservation des chats privés en cas de signalement ou de contrôle.

## 11. Encadrement juridique et administratif

- Rédaction des CGU, CGV et politique de confidentialité.
- Contrats avec les OA, fournisseurs, agences partenaires et livreurs.
- Définition des règles de validation, suspension et retrait des OA.
- Encadrement du sponsoring des OA individuels sous Bronze.
- Définition des conditions de paiement des fournisseurs déclarés.
- Traçabilité des paiements, remboursements, scans QR et décisions administratives.
- Information claire sur les prix, commissions, abonnement, points, réductions et frais de livraison.

## 12. Comptes et rôles

| Rôle | Accès |
|---|---|
| **Acheteur** | Consulter le catalogue, participer à un groupage, recevoir un QR code, gagner des points, parrainer et souscrire au chat privé à partir de 50 points. |
| **Organisateur d'Achat (OA)** | Après validation KYC : créer des groupages, suivre les participations, déclarer un fournisseur, gérer la préparation et organiser la livraison selon son grade. |
| **Administrateur** | Valider les OA, fournisseurs et livreurs, gérer le sponsoring, les fonds, les remboursements, les points, les grades, les chats et les partenaires. |

Un acheteur peut demander à devenir OA sans perdre son historique d'acheteur.

## 13. Mode prototype

Cette première version est une maquette fonctionnelle. Les services tiers sont simulés :

| Service | Simulation |
|---|---|
| **SMS** | Le code de vérification s'affiche à l'écran. |
| **Paiement Mobile Money** | Un bouton marque le paiement comme réussi. |
| **Séquestre** | La consignation, le contrôle, la libération et le remboursement sont pilotés par la console d'administration. |
| **Ticket OA** | Un paiement simulé de 100 FCFA donne 10 créations de groupages et 2 points. |
| **Chat privé** | Un paiement simulé de 2 000 FCFA active l'abonnement mensuel de l'acheteur si celui-ci possède au moins 50 points. |
| **Points** | Les points d'achat, de parrainage, d'abonnement et de ticket sont calculés dans la base. |
| **QR livraison** | Le QR est généré après paiement et son scan confirme la remise. |
| **Agence partenaire** | L'agence et la remise sont simulées. |
| **Sponsoring** | Le fournisseur déclaré, le contrôle de la commande et la libération sont simulés par l'administrateur. |
| **Livraison OA Or** | Le livreur enregistré et le scan QR sont simulés sans service logistique réel. |

Le code métier — séquestre, remboursements, commissions, points, grades, sponsoring, QR de livraison, confidentialité, chat payant et réduction de livraison — est écrit pour de vrai ; seule l'exécution des services tiers est factice.

## 14. Chat privé payant

La plateforme ne comporte **aucun chat public**.

- L'acheteur doit avoir au moins **50 points**.
- Il paie **2 000 FCFA** pour activer un abonnement mensuel.
- L'abonnement est payé par l'acheteur pour discuter avec l'OA et obtenir les informations autorisées sur celui-ci.
- Les messages sont illimités pendant le mois actif.
- Le chat est hébergé et modéré par la plateforme.
- Les coordonnées personnelles ne sont pas automatiquement communiquées.
- À l'expiration, le chat passe à l'état `chat_expire` et l'acheteur doit renouveler son abonnement.

Cycle du chat :

```
non_achete → paiement_confirme → chat_actif → chat_expire ou chat_ferme
```

## 15. Notifications

Les acheteurs sont notifiés lors du paiement, de la génération du QR code, du financement du groupage, de la disponibilité de l'article, du choix de livraison, du suivi logistique, du scan QR, de la livraison confirmée, du remboursement et des nouveaux messages privés.

Les OA sont notifiés des paiements reçus, de l'atteinte du minimum, de la validation KYC, du ticket, des points, du grade, de la commission, de la commande fournisseur, de la livraison et des nouveaux messages privés.

## 16. Cycles de vie

### Groupage

```
brouillon → en_cours → date_limite : cloture_automatique
   │
   ├── minimum atteint ───────→ finance → approvisionnement → livraison → termine
   │
   └── minimum non atteint ──→ minimum_non_atteint
                                  │
                                  ├── OA maintient → finance → …
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

Une participation payée ne possède aucun état d'annulation à la demande de l'acheteur.

## 17. Pile technique

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
