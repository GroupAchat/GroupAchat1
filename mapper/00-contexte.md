---
type: contexte
statut: validé
date: 2026-10-26
tags: [contexte]
---

# Group Achat — contexte

## Objectif
Plateforme web **mobile d'abord** d'intermédiation et de gestion d'achats groupés au Togo, avec une promesse : **« livré ou remboursé »**. L'argent de l'acheteur part sous **séquestre par campagne** ; la livraison se prouve par un **code unique / QR par participation**. Group Achat **met en relation, elle n'arbitre pas** : une plainte sur un produit va au groupeur, publiquement, et se traduit dans sa note. Source : `CAHIER_DES_CHARGES.md` §1–2.

## Utilisateurs
- **Acheteur** : explore sans compte, crée son compte au moment de commander (numéro vérifié par SMS), paie sa part, retire son colis contre son code, note le groupeur.
- **Groupeur** : même compte + dossier KYC validé par l'administrateur ; crée ses campagnes, suit les paiements nominatifs, décide si le minimum n'est pas atteint, demande le retrait des fonds (− 1 500 FCFA), distribue et valide les codes.
- **Administrateur** : console séparée ; valide les dossiers KYC, modère le fil, exécute les décaissements, supervise le séquestre.

## Périmètre du MVP
Les 31 fonctionnalités marquées `MVP` dans `03-fonctionnalites/backlog.md`. Carte validée le 2026-10-26 ([[carte]]) : **27 sont constatées** dans le code (route et écran présents), **4 sont partielles** (F-008 notifications, F-011 pièces KYC, F-016 maintien / renoncer, F-031 relances et clôture J+14), et **aucune n'est recettée**. Aucune fonctionnalité n'est `terminée`.

**Critère de fin du MVP** (critère de la mission qui le termine) : les 31 fonctionnalités MVP en `terminée` dans le backlog, la commande « Vérifier » de `CLAUDE.md` verte, `regles-auditor` sans point critique.

## Hors périmètre (pour l'instant)
- **Abonnements des groupeurs** (gestion CRUD côté administration, visible des seuls groupeurs) : demandés le 2026-10-26 puis **mis de côté par l'utilisateur**. Ils contredisent le cahier des charges (§2 « outil gratuit », §4 « aucun abonnement ») ; trois questions restent à trancher avant toute ligne de code — voir `02-decisions/2026-10-26-questions-ouvertes.md`.
- Les fonctionnalités `hors MVP` du backlog : utiles, prévues par le cahier des charges, pas nécessaires pour démontrer la promesse.

## Contraintes
- Pile imposée : Django 5.2 + DRF, PostgreSQL 17 (SQLite en secours), React 19 + Vite + Tailwind v4 ; une seule origine ; déploiement Coolify sur `achatgr.com` (`COOLIFY.md`).
- **Prototype** : SMS et paiements simulés ; la comptabilité du séquestre est réelle (`CAHIER_DES_CHARGES.md` §6).
- Tout en français, code compris. Montants en entiers FCFA. Téléphone à huit chiffres.

## Données
Utilisateur (rôle acheteur / groupeur), DossierKYC, Réputation ; Catégorie, Produit, Campagne (cycle de vie §9), PalierPrix, médias ; Participation (code de retrait), Avis ; Séquestre, Transaction, Décaissement ; Commentaire, J'aime, DemandeProduit, Intérêt, Notification. Sensibles : téléphones, pièces d'identité (jamais publiques, jamais chez Cloudinary).

## Risques
- La suite de tests dure environ sept minutes : chaque boucle de vérification est lente.
- La branche `staging` a **15 commits de retard sur `master`** et **1 commit propre** (`92bc906 save before merge with master`), vérifié par `git rev-list` le 2026-10-26 : à remettre d'accord, par l'utilisateur, avant d'y fusionner du travail (C-001).
- Les contradictions du cahier des charges sont tranchées le 2026-10-26 (livraison, qui décaisse, abonnements, « livré ou remboursé », KYC, annulation, rôle, J+14…) : [[2026-10-26-decisions-carte]]. Le cahier des charges n'est pas encore réécrit (C-003) : le code et le texte divergent d'ici là.
- « Livré ou remboursé » est tenu ainsi : les fonds sont libérés avant la distribution. Un groupeur qui ne livre pas ne rembourse donc pas l'acheteur tout seul. Les textes d'écran qui disent le contraire doivent être corrigés (C-009).
- F-031 n'est pas faite : un colis non retiré bloque la campagne en `distribution` tant qu'elle ne l'est pas.
