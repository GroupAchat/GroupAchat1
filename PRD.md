# Group Achat — PRD d'une page

> Avant tout prompt · 7 octobre 2026

## 1. Problème

À Lomé, un particulier paie le prix de détail faute de pouvoir acheter en gros seul ou de faire confiance à un inconnu qui propose de grouper.

## 2. Utilisateurs

- **Acheteur** — sur Mobile Money, veut le prix de gros sans risque.
- **Groupeur** — commerçant sélectionné, lance les campagnes.

## 3. Fonctionnalités

**Acheteur**
- Parcourir les campagnes sans compte
- Rejoindre une campagne et payer sa part — **rejoindre demande un compte**, demandé dès l'ouverture de l'écran de commande
- Suivre sa livraison, validée par un code
- Poser une question publique au groupeur, qui reste anonyme — **demande un compte**

**Groupeur**
- Créer une campagne
- Décider à la clôture si la commande passe
- Retirer l'argent collecté dès la clôture, moins **1 500 F par groupage abouti**

**Récit de la fonctionnalité n°1** — *en tant qu'acheteur à Lomé avec un smartphone, je veux rejoindre une campagne et payer ma part en Mobile Money, afin d'obtenir le prix de gros sans avancer l'argent à un inconnu.*

## 4. C'est fini quand

- Je vois les campagnes sans créer de compte
- Je vois mon total, livraison comprise, avant de payer
- Je crée mon compte par un formulaire classique — prénom, numéro, courriel facultatif — puis je vérifie mon numéro par un code SMS
- On me le demande **quand j'engage quelque chose** : rejoindre un groupage, poser une question. Jamais à l'ouverture
- Je reçois une confirmation avec mon code de livraison
- Si la campagne n'aboutit pas, je suis remboursé intégralement

## 5. Écrans

1. **Détail de la campagne** — prix de la part, contenu, participants, temps restant
2. **Commander** — quantité, position, récapitulatif, connexion
3. **Confirmation** — montant payé, code de livraison

## 6. Données

| Table | Champs |
|---|---|
| **groupeur** | id · téléphone · pseudonyme · statut KYC · plafond |
| **acheteur** | id · téléphone · nom · créé_le |
| **campagne** | id · groupeur_id · titre · description · prix_part · contenu_part · média · date_fin · statut |
| **commande** | id · campagne_id · acheteur_id · quantité · montant_part · **frais_livraison** · total · **position** · repère · téléphone · code_livraison · **clé_idempotence** · statut |

Trois champs à ne pas oublier : **frais de livraison séparés de la part** *(à zéro aujourd'hui — l'acheteur ne paie que sa part — mais le champ reste, séparé)*, **position conservée** sur la commande, **clé d'idempotence** sur le paiement.

## 7. Hors périmètre

Filtrage des messages par IA · paiement réel · application mobile

---

**Stack :** React · Django · PostgreSQL
