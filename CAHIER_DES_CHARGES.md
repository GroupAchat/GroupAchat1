# Group Achat — Cahier des charges

Plateforme web **mobile-first** d'intermédiation et de gestion d'achats groupés au Togo.

## 1. Problématique

Au Togo, les achats groupés se font de manière informelle, principalement sur WhatsApp :

- **Côté acheteur** : forte méfiance — peur de perdre son argent, sans garantie ni recours.
- **Côté groupeur** : gestion chaotique — suivi manuel des listes, vérification fastidieuse
  des captures d'écran Mobile Money, risques d'impayés et de litiges à la livraison.

## 2. Solution

| | Garantie apportée |
|---|---|
| **Acheteur** | « Livré ou remboursé » : paiement sous **séquestre** (escrow) et validation de livraison par **code unique / QR code**. |
| **Groupeur** | Outil **gratuit** de gestion automatisée : suivi nominatif des paiements en temps réel, protection contre les litiges, visibilité au-delà de ses cercles habituels. |

## 3. Les trois acteurs

### 🛒 L'acheteur

1. **Accès** — explore le catalogue **librement, sans inscription**. Il ne crée son
   compte qu'au moment de commander : **nom, prénom, numéro de téléphone, mot de passe**,
   et **adresse e-mail facultative**. Un **code reçu par SMS** vérifie ensuite le numéro ;
  
2. **Découverte** — parcourt les campagnes ou **soumet une demande de produit** sur
   l'espace communautaire.
3. **Participation** — rejoint une campagne et règle sa part en ligne (Mobile Money).
   L'argent part en séquestre, il n'est jamais versé directement au groupeur.
4. **Clôture** — reçoit la confirmation de clôture de la campagne.
5. **Réception** — notifié que le produit est prêt, il présente son **code unique / QR code**
   au livreur pour récupérer son colis.

### 🛍️ Le groupeur (premier client)

1. **Confiance** — s'inscrit avec les mêmes informations que l'acheteur, puis soumet ses
   pièces (CNI / passeport + numéro Mobile Money) pour obtenir son **badge de confiance**.
   **Tant que l'administrateur n'a pas validé son dossier, il n'accède pas à l'espace
   groupeur** : il ne voit qu'un écran d'attente rappelant où en est son dossier.
2. **Lancement** — crée librement sa campagne (photos, prix, minimum de pièces, date limite)
   en **autonomie totale** : sourcing libre, aucun fournisseur imposé.
3. **Collecte** — suit la jauge et les **paiements nominatifs** (« Abalo a payé ») en temps
   réel sur son tableau de bord.
4. **Décaissement** — retire **100 % des fonds en une fois**, moins **1 500 FCFA de frais
   fixes**, et va s'approvisionner chez son fournisseur.
5. **Distribution** — notifie sur la plateforme que la marchandise est à disposition.
   **Tous les participants reçoivent aussitôt une notification** soit le partcipant decide d'etre livrer ou bien lui meme peux venir recuperer 

### 🛡️ L'administrateur

1. Vérifie le **dossier KYC** du groupeur et valide son compte.
2. Supervise et modère la plateforme.
3. **Consigne les fonds** sur le compte séquestre.
4. **Libère** le montant total vers le compte Mobile Money du groupeur.
5. **Clôture le dossier** dès que le code de retrait est validé, et alimente la **note de
   réputation** du groupeur.

## 4. Règles métier

- **Frais de plateforme** : 1 500 FCFA fixes, prélevés une seule fois au décaissement.
  Aucun frais pour l'acheteur, aucun abonnement pour le groupeur.
- **Séquestre** : les fonds d'une campagne restent consignés jusqu'à sa clôture.
- **Clôture** : à la date limite, la collecte se ferme **automatiquement** et la
  campagne quitte le catalogue — on ne peut plus la rejoindre.
- **Minimum non atteint** : la campagne n'est pas annulée pour autant, et
  **l'argent ne repart pas tout seul**. Le groupeur peut décider de maintenir la
  commande malgré le nombre — il a parfois déjà négocié avec son fournisseur, ou
  complète de sa poche. Rembourser d'office ferait échouer des groupages qui
  auraient abouti. Les participants sont prévenus que le groupage n'a pas abouti
  et que leur part reste consignée en attendant la décision.
- **Délai de décision** : sept jours. Passé ce délai sans réponse du groupeur,
  chaque participant est **intégralement remboursé** sans avoir à réclamer. Ce
  délai borne l'attente sans contredire la règle précédente : sans lui, un
  groupeur qui disparaît laisserait l'argent bloqué indéfiniment.
- **Historique** : une campagne qui a quitté le catalogue reste **consultable par
  ceux qui y ont participé** — fiche produit complète, point de remise et fil de
  discussion. Leur commande ne disparaît pas avec l'annonce.
- **Inscription** : nom, prénom, numéro de téléphone, mot de passe ; e-mail facultatif.
  Le **numéro fait office d'identifiant** et doit être **vérifié par SMS**. Aucun compte
  n'est demandé pour consulter le catalogue.
- **Retrait** : un **code unique et son QR code par participation**, c'est-à-dire propre
  au couple **produit + participant**. Le QR porte l'identifiant de la campagne en plus du
  code, pour qu'un code valide d'une autre campagne soit refusé au scan. Le colis n'est
  remis que contre ce code ; sa validation vaut preuve de livraison et ferme tout litige.
- **Médias d'un produit** : jusqu'à **trois photos et deux vidéos**. Les groupeurs
  photographient au téléphone, sur une connexion mesurée ; au-delà, la fiche devient
  lente à charger pour l'acheteur sans rien lui apprendre de plus. Une vidéo exige une
  image d'aperçu, faute de quoi elle apparaîtrait comme un rectangle noir dans la
  galerie. La vignette du catalogue reste **toujours une photo**.
- **Réputation** : alimentée par les campagnes menées à terme et les litiges constatés.
- **Distribution** : pas de flotte de livreurs. Le groupeur, ou la personne qu'il désigne,
  remet les colis au point de retrait et valide le code de chaque participant. Le modèle
  enregistre qui a effectué la remise, pour pouvoir ouvrir ce rôle plus tard.
- **Colis non récupéré** : relances à J+3 et J+7 ; au bout de **14 jours** après la mise à
  disposition, la livraison est réputée acquise et le dossier se clôt.
- **Frais de remboursement** : en cas de campagne annulée, les frais d'opérateur du
  remboursement sont à la charge de la plateforme — c'est le prix de la promesse
  « risque zéro ». Ils sont tracés pour être mesurés.
- **Demandes communautaires** : un acheteur publie une demande de produit, les autres
  marquent leur intérêt (« moi aussi »). Les groupeurs voient ces demandes classées par
  intérêt et peuvent en convertir une en campagne.

## 5. Comptes et rôles

Un **seul type de compte**, distingué par un rôle demandé à l'inscription :

| Rôle | Accès |
|---|---|
| **Acheteur** | Dès le numéro vérifié : commander, suivre ses participations, poster une demande produit. |
| **Groupeur** | Après validation du dossier KYC par l'administrateur. Avant, l'espace groupeur est inaccessible. |
| **Administrateur** | Console séparée, compte créé en interne. |

Un acheteur peut **demander à devenir groupeur** à tout moment : il dépose son dossier KYC
et attend la validation, sans perdre son historique d'acheteur.

## 6. Mode prototype

Cette première version est une **maquette fonctionnelle destinée à présenter la solution**.
Aucun flux d'argent ni d'envoi SMS réel n'est branché. Tout ce qui dépend d'un tiers est
**simulé**, derrière des interfaces qui permettront de brancher le vrai service plus tard
sans toucher au reste du code :

| Service | Simulation |
|---|---|
| **SMS** | Le code de vérification s'affiche à l'écran au lieu d'être envoyé. |
| **Paiement Mobile Money** | Un bouton « Payer avec TMoney / Flooz » marque la part payée instantanément. |
| **Séquestre** | Tenu en base : la consignation et la libération sont des actions de la console d'administration. |
| **Décaissement groupeur** | Action administrateur, qui enregistre le retrait sans ordre de virement réel. |

Le code métier (séquestre, frais, remboursements, codes de retrait) est en revanche
**écrit pour de vrai** : seule la couche d'exécution est factice.

## 7. Fil de discussion sous chaque campagne

La fiche produit porte un **fil de messages publics**, dans l'esprit des commentaires
d'un réseau social : on y pose ses questions, on répond, on marque son accord.

- **Lecture ouverte à tous, sans compte** : c'est ce fil qui rassure l'acheteur hésitant.
  Le cacher derrière une inscription le priverait de sa raison d'être.
- **Écriture réservée aux numéros vérifiés**, sinon le fil se remplit de faux avis.
- **Un seul niveau de réponse**, lisible sur un écran de téléphone.
- **Les messages du groupeur sont distingués** du reste du fil.
- **« J'aime »** une seule fois par personne et par message ; le fil peut se trier par
  popularité.
- **Modération** : un message contraire aux règles est **masqué, jamais supprimé** — la
  trace doit rester en cas de contestation.

## 8. Notifications

Les participants sont notifiés à chaque étape qui les concerne : paiement enregistré,
campagne financée, **marchandise à disposition** (avec le point de remise et le rappel du
code de retrait), retrait confirmé, campagne annulée et remboursement, et **réponse à
leur message**. Le groupeur est notifié de chaque paiement reçu, de l'atteinte du minimum,
de la décision KYC et de **chaque nouveau message sous ses campagnes**.

## 9. Cycle de vie d'une campagne

```
brouillon → en_cours → (date limite : clôture automatique)
   │
   ├── minimum atteint ──────────→ financee → decaissee → approvisionnement
   │                                                    → distribution → terminee
   │
   └── minimum non atteint ──→ minimum_non_atteint   (l'argent reste consigné)
                                    │
                                    ├── le groupeur maintient ──→ financee → …
                                    ├── le groupeur renonce ────→ annulee (remboursements)
                                    └── silence pendant 7 jours → annulee (remboursements)
```

## 10. Pile technique

| Couche | Choix |
|---|---|
| API | Django 5.2 + Django REST Framework |
| Base | PostgreSQL 17 (SQLite en secours hors déploiement) |
| Front | React 19 + Vite + Tailwind CSS — deux applications : boutique et console d'administration |
| Exécution | Docker Compose (`base`, `api`, `boutique`, `admin`) |
| Configuration | un seul `.env` à la racine, lu par Django, Vite et Compose |

Le français est la langue du code : noms de modèles, de champs, de routes et de variables.
