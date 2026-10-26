# Group Achat — Cahier des charges

Plateforme web **mobile-first** d'intermédiation et de gestion d'achats groupés au Togo.

## 1. Problématique

Au Togo, les achats groupés se font de manière informelle, principalement sur WhatsApp :

- **Côté acheteur** : forte méfiance — peur de perdre son argent, sans garantie ni recours.
- **Côté Organisateur d'Achat (OA)** : gestion chaotique — suivi manuel des listes, vérification fastidieuse des captures d'écran Mobile Money, risques d'impayés et de litiges à la livraison.

## 2. Solution

| | Garantie apportée |
|---|---|
| **Acheteur** | « Livré ou remboursé » : paiement sous **séquestre** (escrow), options de livraison encadrées et validation de livraison par **code unique / QR code**. |
| **Organisateur d'Achat (OA)** | Outil de gestion automatisée : suivi nominatif des paiements en temps réel, preuve de livraison opposable, visibilité au-delà de ses cercles habituels et accompagnement selon son profil. |

### Ce que la plateforme garantit — et ce qu'elle ne garantit pas

Group Achat **met en relation, elle n'arbitre pas**. Elle garantit l'argent de la collecte : les fonds restent sous séquestre, et une campagne annulée rembourse.
Elle ne se prononce pas sur la marchandise — ni sur sa qualité, ni sur sa conformité, ni sur ce qui s'est dit au point de retrait.

Une plainte sur un produit **va donc directement à l'OA** : l'acheteur en discute avec lui sous la campagne, publiquement, et le **note**. Il n'y a pas de dossier de litige à instruire, pas d'arbitre à saisir. La sanction d'un mauvais OA, c'est sa réputation qui baisse et les acheteurs suivants qui la voient.

C'est un choix de produit, pas une facilité : arbitrer supposerait de juger sur pièces des marchandises qu'on n'a jamais vues, à Lomé, sans levier réel sur le vendeur. La transparence publique en dit davantage, et plus vite.

## 3. Les trois acteurs

### 🛒 L'acheteur

1. **Accès** — explore le catalogue **librement, sans inscription**. Il ne crée son compte qu'au moment de commander : **nom, prénom, numéro de téléphone, mot de passe**, et **adresse e-mail facultative**. Un **code reçu par SMS** vérifie ensuite le numéro.
2. **Découverte** — parcourt les campagnes ou **soumet une demande de produit** sur l'espace communautaire.
3. **Participation** — rejoint une campagne et règle sa part en ligne (Mobile Money). L'argent part en séquestre, il n'est jamais versé directement à l'OA.
4. **Choix de réception** — sélectionne, selon les options proposées pour le groupage, la livraison à domicile, le retrait en point relais ou le retrait en main propre auprès de l'OA.
5. **Clôture** — reçoit la confirmation de clôture de la campagne.
6. **Réception** — présente son **code unique / QR code** au livreur, au point relais ou à l'OA pour récupérer son colis.

### 🛍️ L'Organisateur d'Achat (OA)

L'OA est le porteur d'un ou plusieurs groupages. À l'inscription, il choisit l'un des profils suivants et fournit les justificatifs correspondants :

- **Commerçant** : boutique ou vendeur professionnel ;
- **Organisateur individuel** : particulier ou initiateur de groupages.

1. **Inscription et confiance** — s'inscrit avec les mêmes informations que l'acheteur, choisit son profil, puis soumet son dossier KYC (pièce d'identité, justificatifs liés à son profil et numéro Mobile Money). **Tant que l'administrateur n'a pas validé son dossier, il n'accède pas à l'espace OA** : il ne voit qu'un écran d'attente rappelant où en est son dossier.
2. **Publication** — après validation, il achète un ticket de publication à **100 FCFA**, qui lui permet de publier jusqu'à **10 groupages**. Il crée ses groupages (photos, prix, minimum de pièces, date limite et options de livraison) en autonomie, avec un sourcing libre.
3. **Collecte** — suit la jauge et les **paiements nominatifs** (« Abalo a payé ») en temps réel sur son tableau de bord.
4. **Décaissement** — après aboutissement du groupage, retire les fonds selon les règles de séquestre, déduction faite de la commission applicable à son grade et des éventuels frais explicitement prévus.
5. **Approvisionnement et distribution** — signale que la marchandise est disponible, prépare les colis et remet ceux-ci à l'acheteur, au partenaire logistique ou au point relais choisi.
6. **Réputation et progression** — reçoit des points pour ses activités, peut progresser dans les grades **Bronze → Argent → Or** et bénéficier d'une commission réduite ainsi que de bonus selon les règles du programme.

### 🛡️ L'administrateur

1. Vérifie le **dossier KYC** de l'OA, son profil et les justificatifs associés, puis valide ou refuse son compte.
2. Supervise et modère la plateforme.
3. **Consigne les fonds** sur le compte séquestre.
4. Contrôle les commissions, les remboursements et les décaissements.
5. Valide les règles d'approbation applicables aux clubs et aux groupages d'achat.
6. Supervise les partenaires logistiques et les opérations de livraison.
7. **Clôture le dossier** lorsque la réception est validée ou réputée acquise, et alimente la **note de réputation** de l'OA.

## 4. Profils des Organisateurs d'Achat (OA)

À l'inscription, l'OA choisit son profil et fournit les documents justificatifs correspondants :

| Profil | Description | Justificatifs indicatifs |
|---|---|---|
| **Commerçant** | Boutique ou vendeur professionnel qui propose des produits dans le cadre de son activité. | Pièce d'identité, justificatif de l'activité ou de la boutique, numéro Mobile Money professionnel ou personnel vérifié. |
| **Organisateur individuel** | Particulier ou initiateur de groupages organisant des achats ponctuels ou communautaires. | Pièce d'identité et numéro Mobile Money vérifié. |

L'administrateur peut demander des justificatifs complémentaires et définir des critères différents selon le profil, le volume d'activité ou le niveau de risque.

## 5. Modèle économique et monétisation

- **Ticket de publication** : **100 FCFA** pour publier jusqu'à **10 groupages**. Le ticket est consommé selon les règles définies par la plateforme et ne remplace pas les éventuelles commissions sur les ventes.
- **Commission sur les ventes** : la plateforme prélève **1 %, 2,5 % ou 5 %** sur chaque groupage abouti. Le taux dépend du grade de l'OA et est affiché avant la validation du groupage.
- **Grades** : les grades **Bronze, Argent et Or** peuvent réduire la commission de plateforme et débloquer des bonus additionnels, selon l'activité, le sponsoring, la réputation et les critères validés par l'administrateur.
- **Option « Contact Privé »** : un acheteur peut payer pour échanger en privé avec un OA ou obtenir ses coordonnées directes, lorsque cette option est activée et autorisée par la plateforme. Les conditions, le prix et les limites d'utilisation sont présentés avant paiement.
- **Acheteur** : aucun frais obligatoire ne lui est facturé pour participer à un groupage, hors options choisies comme le Contact Privé ou les frais de livraison éventuellement affichés.
- **Transparence** : le montant du ticket, le taux de commission, les frais de livraison et le montant net revenant à l'OA sont visibles avant la confirmation de l'opération.

## 6. Règles métier

- **Séquestre** : les fonds d'une campagne restent consignés jusqu'à sa clôture et ne peuvent être libérés ou remboursés au-delà des montants effectivement consignés.
- **Clôture** : à la date limite, la collecte se ferme **automatiquement** et le groupage quitte le catalogue — on ne peut plus le rejoindre.
- **Minimum non atteint** : le groupage n'est pas annulé automatiquement et **l'argent ne repart pas tout seul**. L'OA peut décider de maintenir la commande malgré le nombre atteint. Les participants sont prévenus que le groupage n'a pas abouti et que leur part reste consignée en attendant la décision.
- **Délai de décision** : sept jours. Passé ce délai sans réponse de l'OA, chaque participant est **intégralement remboursé** sans avoir à réclamer.
- **Historique** : un groupage qui a quitté le catalogue reste **consultable par ceux qui y ont participé** — fiche produit complète, mode de réception et fil de discussion. Leur commande ne disparaît pas avec l'annonce.
- **Inscription** : nom, prénom, numéro de téléphone, mot de passe ; e-mail facultatif. Le **numéro fait office d'identifiant** et doit être **vérifié par SMS**. Aucun compte n'est demandé pour consulter le catalogue.
- **Retrait** : un **code unique et son QR code par participation et par article**. Le QR porte l'identifiant du groupage en plus du code, pour qu'un code valide d'un autre groupage soit refusé au scan. Le colis n'est remis que contre ce code ; sa validation vaut **preuve de livraison**.
- **Prix** : le prix est figé au moment de la participation. Un palier franchi plus tard ne réécrit pas ce qui a déjà été payé.
- **Médias d'un produit** : jusqu'à **trois photos et deux vidéos**, hébergés chez Cloudinary et recompressés à la livraison selon le navigateur. Une vidéo exige une image d'aperçu. La vignette du catalogue reste **toujours une photo**.
- **Réputation** : la note est la **moyenne des avis laissés par les acheteurs**, et rien d'autre. À côté s'affichent les compteurs de volume — groupages menés à terme, participants servis — afin de distinguer « 5/5 sur un avis » de « 4,2/5 sur quarante ».
- **Distribution** : l'OA peut remettre les colis lui-même ou utiliser les partenaires logistiques et points relais proposés. Le modèle enregistre qui a effectué la remise.
- **Colis non récupéré** : relances à J+3 et J+7 ; au bout de **14 jours** après la mise à disposition, la livraison est réputée acquise et le dossier se clôt, sous réserve des règles applicables au mode de livraison choisi.
- **Frais de remboursement** : en cas de groupage annulé, les frais d'opérateur du remboursement sont à la charge de la plateforme. Ils sont tracés pour être mesurés.
- **Demandes communautaires** : un acheteur publie une demande de produit, les autres marquent leur intérêt (« moi aussi »). Les OA voient ces demandes classées par intérêt et peuvent en convertir une en groupage.

## 7. Options de livraison et de réception

Les acheteurs bénéficient de trois options pour réceptionner leurs colis, selon la disponibilité du groupage et de la zone desservie :

1. **Livraison à domicile** via des partenaires logistiques, notamment **Gozem** ou **La Poste** ;
2. **Retrait en point relais** dans les agences partenaires, notamment **Gozem** ou **La Poste** ;
3. **Retrait en main propre auprès de l'OA** ou de la personne qu'il a désignée.

Les frais, délais, zones couvertes et responsabilités sont affichés avant le paiement. Le choix de l'option de livraison peut être effectué lors de la participation ou avant la mise à disposition, selon les règles du groupage.

## 8. Sécurité et garanties

- **Paiements sécurisés** : les transactions sont protégées et les fonds restent sous séquestre jusqu'à la clôture prévue.
- **Preuve de livraison par QR code** : un QR code unique est généré pour chaque acheteur et chaque article. Le scan lors de la remise valide la réception et clôture la commande correspondante.
- **Garantie acheteur** : l'acheteur bénéficie de la promesse « livré ou remboursé », dans les limites des règles de séquestre et d'annulation prévues au présent cahier des charges.
- **Logistique certifiée** : les partenaires logistiques sont sélectionnés et encadrés par contrat afin de réduire les risques de retard, de perte ou de mauvaise remise.
- **Données sensibles** : les pièces d'identité ne sont jamais servies publiquement et ne sont transmises qu'aux personnes autorisées dans le cadre de la vérification KYC.

## 9. Gamification, sponsoring et programme de fidélité

### Système de points

- **Acheteur** : accumulation de points lors des achats, publications de demandes, parrainages et échanges sur le chat, selon les actions retenues par la plateforme.
- **OA** : gain de points à chaque création de groupage et lors des actions éligibles, afin de débloquer des compétences, fonctionnalités et avantages.

### Parrainage et niveaux (grades)

- Évolution par paliers : **Bronze → Argent → Or**.
- Les critères de passage de grade peuvent inclure l'activité, le volume de groupages aboutis, la satisfaction des acheteurs, le sponsoring et le respect des règles.
- Le grade détermine notamment le niveau de commission applicable — **1 %, 2,5 % ou 5 %** — ainsi que les bonus additionnels disponibles.
- La plateforme affiche les règles de calcul, les conditions de perte de grade et les avantages associés de manière compréhensible.

## 10. Encadrement juridique et administratif

- **Contrats officiels** : rédaction et validation des CGU, CGV, politiques de confidentialité et contrats liant la plateforme, les OA et les livreurs ou partenaires logistiques.
- **Règles de gestion** : définition des critères d'approbation, de validation, de suspension et de retrait applicables à la création des clubs et des groupages d'achat.
- **KYC et conformité** : conservation sécurisée des justificatifs, traçabilité des décisions administratives et limitation de l'accès aux données sensibles.
- **Partenaires** : formalisation des obligations de livraison, de preuve de remise, de traitement des incidents et de protection des données.
- **Information des utilisateurs** : présentation claire des prix, commissions, frais, délais, garanties et limites de responsabilité avant toute validation.

## 11. Comptes et rôles

Un **seul type de compte**, distingué par un rôle et, pour l'OA, par un profil demandé à l'inscription :

| Rôle | Accès |
|---|---|
| **Acheteur** | Dès le numéro vérifié : commander, choisir une option de livraison, suivre ses participations, poster une demande produit et accéder aux fonctionnalités autorisées. |
| **Organisateur d'Achat (OA)** | Après validation du dossier KYC : créer des groupages, suivre les paiements, gérer la distribution, consulter ses points et son grade. |
| **Administrateur** | Console séparée, compte créé en interne : validation KYC, supervision, modération, gestion du séquestre, des commissions et des partenaires. |

Un acheteur peut **demander à devenir OA** à tout moment : il choisit son profil, dépose son dossier KYC et attend la validation, sans perdre son historique d'acheteur.

## 12. Mode prototype

Cette première version est une **maquette fonctionnelle destinée à présenter la solution**. Aucun flux d'argent, d'envoi SMS ou de livraison réelle n'est branché. Tout ce qui dépend d'un tiers est **simulé**, derrière des interfaces qui permettront de brancher le vrai service plus tard sans toucher au reste du code :

| Service | Simulation |
|---|---|
| **SMS** | Le code de vérification s'affiche à l'écran au lieu d'être envoyé. |
| **Paiement Mobile Money** | Un bouton « Payer avec TMoney / Flooz » marque la part payée instantanément. |
| **Séquestre** | Tenu en base : la consignation, la libération et le remboursement sont des actions de la console d'administration. |
| **Ticket de publication** | Un paiement simulé de 100 FCFA crédite un quota de 10 groupages publiables. |
| **Commissions** | Le taux de 1 %, 2,5 % ou 5 % est calculé et enregistré selon le grade de l'OA, sans prélèvement réel. |
| **Contact Privé** | Le paiement est simulé et l'accès privé est accordé selon les règles configurées. |
| **Livraison** | Les options domicile, point relais et remise en main propre sont enregistrées sans appel réel à Gozem ou La Poste. |
| **Décaissement OA** | Action administrateur, qui enregistre le retrait sans ordre de virement réel. |

Le code métier (séquestre, commissions, remboursements, points, grades, codes de retrait et règles de livraison) est en revanche **écrit pour de vrai** : seule la couche d'exécution est factice.

## 13. Fil de discussion sous chaque groupage

La fiche produit porte un **fil de messages publics**, dans l'esprit des commentaires d'un réseau social : on y pose ses questions, on répond, on marque son accord.

- **Lecture ouverte à tous, sans compte** : c'est ce fil qui rassure l'acheteur hésitant.
- **Écriture réservée aux numéros vérifiés**, sinon le fil se remplit de faux avis.
- **Un seul niveau de réponse**, lisible sur un écran de téléphone.
- **Les messages de l'OA sont distingués** du reste du fil.
- **« J'aime »** une seule fois par personne et par message ; le fil peut se trier par popularité.
- **Contact Privé** : lorsqu'il est activé et payé, l'échange privé se fait dans l'espace prévu à cet effet, sans exposer publiquement les coordonnées personnelles de l'OA.
- **Modération** : un message contraire aux règles est **masqué, jamais supprimé** — la trace doit rester en cas de contestation.

## 14. Notifications

Les participants sont notifiés à chaque étape qui les concerne : paiement enregistré, groupage financé, **marchandise à disposition**, option de livraison confirmée, point de remise ou suivi logistique, rappel du code de retrait, retrait confirmé, groupage annulé et remboursement, et **réponse à leur message**.

L'OA est notifié de chaque paiement reçu, de l'atteinte du minimum, de la décision KYC, de son ticket de publication, de l'utilisation de ses quotas, de la commission applicable, du choix de livraison et de **chaque nouveau message sous ses groupages**.

## 15. Cycle de vie d'un groupage

```
brouillon → en_cours → (date limite : clôture automatique)
   │
   ├── minimum atteint ──────────→ financee → decaissee → approvisionnement
   │                                                    → livraison/distribution → terminee
   │
   └── minimum non atteint ──→ minimum_non_atteint   (l'argent reste consigné)
                                    │
                                    ├── l'OA maintient ──────→ financee → …
                                    ├── l'OA renonce ────────→ annulee (remboursements)
                                    └── silence pendant 7 jours → annulee (remboursements)
```

Une participation suit également son propre cycle :

```
en_attente → payee → preparee →
   ├── remise_oa
   ├── point_relais
   └── livraison_domicile
        → livree (QR code validé) → terminee
```

## 16. Pile technique

| Couche | Choix |
|---|---|
| API | Django 5.2 + Django REST Framework |
| Base | PostgreSQL 17 (SQLite en secours hors déploiement) |
| Front | React 19 + Vite + Tailwind CSS — deux applications : boutique et console d'administration |
| Exécution | Docker Compose (`base`, `api`, `boutique`, `admin`) |
| Configuration | un seul `.env` à la racine, lu par Django, Vite et Compose |

Le français est la langue du code : noms de modèles, de champs, de routes et de variables. Le terme métier à utiliser dans les documents, interfaces et commentaires est **Organisateur d'Achat (OA)** ; l'ancien terme « groupeur » ne doit plus être utilisé, sauf dans un contexte historique ou de migration.
