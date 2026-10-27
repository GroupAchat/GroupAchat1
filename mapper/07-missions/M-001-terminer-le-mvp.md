---
type: mission
id: M-001
statut: en cours
genre: MVP
ouverte: 2026-10-26
fermee:
date: 2026-10-27
tags: [mission]
---

# M-001  Terminer le MVP

## Objectif
Terminer le MVP : les 31 fonctionnalités F-001 à F-031 vérifiées de bout en bout (aujourd'hui 27 constatées, 4 partielles, aucune recettée). Périmètre : [[carte]], [[backlog]].

## Critère de fin
- [ ] F-001 à F-031 en `terminée` dans [[backlog]]
- [ ] `bash .claude/skills/verify/scripts/check.sh complet` vert
- [ ] `regles-auditor` sans point bloquant

## Tâches
| # | Tâche | F-XXX | Dépôt | Agent | Statut | Preuve |
|---|---|---|---|---|---|---|
| T1 | État des lieux du MVP : recette des 27 fonctionnalités constatées (mode état des lieux ; lecture seule) | F-001 à F-031 | GroupAchat1 | recette | terminée | 165 tests verts ; rapport [[recette-etat-des-lieux-2026-10-26]] (2026-10-26) |
| T2 | F-016 Maintenir / renoncer : `CampagneGroupeur.tsx` appelle `/api/api/…` (boucle préparer → fonctionnalite → reviewer-tester → recette) | F-016 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | terminée | reviewer-tester : VALIDÉE sur le code et VALIDÉE sur la reprise de `check.sh` ; « Vérifier » `check.sh complet` : CHECK: OK (complet), migrations « No changes detected », **244 tests passés**, typage des deux interfaces OK ; `check.sh rapide` : 132 tests passés, CHECK: OK (rapide) ; `test_cloture.py` : 40 tests collectés (268 lignes ajoutées, aucune supprimée). Recette : **RECETTE OK** le 2026-10-27 (serveur OK, web OK à 390 px, mobile —) : [[F-016-decision-minimum-non-atteint]], section « Recette (2026-10-27…) ». Commitée `f8b78f9` (« Rend au groupeur les boutons maintenir et renoncer »), fusionnée dans `staging`, poussée sur `origin/staging`. Décisions D1 à D4 : [[2026-10-27-decisions-f016]]. |
| T3 | F-008 Liens des notifications vers `/mes-achats/:id` (même boucle) | F-008 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | terminée | reviewer-tester : VALIDÉE en deux passes (première : `check.sh complet` OK, 255 tests passés, `test-diff.sh` SIGNAUX 0, migration aller / retour / aller sur base jetable, point relevé : l'inverse écrasait des liens corrects ; reprise : retour neutre et migration autonome, `check.sh complet` : 255 passed, `CHECK: OK (complet)`, SIGNAUX 0, seule suppression de test demandée et remplacée par un test du retour neutre) ; « Vérifier » : 255 tests passés ; recette : **RECETTE OK** le 2026-10-27 (serveur OK, web OK à 390 px, mobile —) : [[F-008-liens-des-notifications]], section « Recette (recetter, 2026-10-27) ». Décisions D1 à D3 : [[2026-10-27-decisions-f008]]. Commitée `769ec1a` (« Répare les liens des notifications qui menaient à une page introuvable »), dans `staging`, poussée sur `origin/staging`. |
| T4 | F-011 Pièces KYC recto/verso obligatoires, écran et serveur (même boucle ; touche l'authentification/KYC et le contrat d'API : accord utilisateur requis) | F-011 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | terminée | reviewer-tester, première relecture : **À CORRIGER** (bloquant : une vraie image au nom à extension hors liste ou sans extension recevait le message anglais de Django, `invalid_extension` ; non bloquants : bombe de 100 Mpx acceptée, limite comptant les échecs, pas de verrou dans `post`, `_effacer` de la démo effaçant les fichiers de tous les dossiers, taille contrôlée seulement après réception). Reprise par `fonctionnalite`, puis reviewer-tester, seconde relecture : **VALIDÉE** ; `check.sh complet` : CHECK: OK (complet), **308 tests passés**, migrations « No changes detected », `npm run verifier` OK ; `test-diff.sh` SIGNAUX 0 (une seule assertion supprimée, remplacée par un test plus strict). Recette : **RECETTE OK** le 2026-10-27 (serveur ✅, web ✅ boutique et console admin à 390 px, mobile —) : [[F-011-depot-dossier-kyc]], section « Recette — 2026-10-27 ». Décisions D1 à D12 : [[2026-10-27-decisions-f011]]. Non commitée au 2026-10-27 (voir « À livrer ») |
| T5 | F-031 Relances J+3/J+7 par notification, clôture J+14 avec statut « réputée livrée », campagne `terminee`, réputation créditée (archi-backend d'abord, puis même boucle ; migration probable : accord utilisateur requis) | F-031 | GroupAchat1 | archi-backend, puis recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T6 | C-009 Textes de la promesse (`FicheCampagne.tsx`, `CampagneGroupeur.tsx`) (même boucle) | C-009 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T7 | Recette de l'ensemble du MVP | F-001 à F-031 | GroupAchat1 | recette | à faire | |
| T8 | Audit des règles | F-001 à F-031 | GroupAchat1 | regles-auditor | à faire | |
| T9 | F-030 Fuite des pièces KYC : traversée `/medias/x/%2e%2e/kyc/…` et doublon `static()` en DEBUG ; test de régression. **Priorité : traitée en premier, avant T2** (ajoutée le 2026-10-26) | F-030 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette ; branche `fix/F-030-fuite-kyc` depuis `staging` | terminée | reviewer-tester : VALIDÉE, aucun point bloquant ; « Vérifier » `check.sh complet` : CHECK: OK, migrations « No changes detected », **225 tests verts**, typage des deux interfaces OK ; 60 tests `TestPiecesKycPrivees` (`backend/groupachat/tests/test_securite.py`, DEBUG=0 et 1), sans correctif 24 échouent. Recette : **RECETTE OK** le 2026-10-27 (détail : [[F-030-pieces-kyc-privees]], section « Résultat de la recette »). Commitée `fb4963c` (« Ferme la traversée qui exposait les pièces d'identité »), fusionnée dans `staging` le 2026-10-27, poussée sur `origin/staging`. |
| T10 | F-024 Double paiement : `mettre_a_disposition` refusé hors `financee` (F-018, C-014) ; décaissement refusé automatiquement à l'annulation ; `executer_decaissement` sous `select_for_update` avec contrôle du statut (C-021) ; annulation interdite si le décaissement est exécuté (D-F024) (ajoutée le 2026-10-26) | F-024, F-018 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette (archi-backend si besoin) | à faire | |
| T11 | F-010 Avis modifiables et supprimables par des tiers : seul l'auteur modifie ou supprime, tout autre (groupeur compris) reçoit 403, le groupeur garde son droit de réponse (D-F010) ; F-021 suit (réputation) (ajoutée le 2026-10-26) | F-010, F-021 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T12 | F-005 : bouton « Participer » recouvert à 390 px (`FicheCampagne.tsx:515`) ; F-009 : réponse à un message d'une autre campagne refusée, commentaire sur le brouillon d'autrui refusé, campagne inexistante sans 500 (ajoutée le 2026-10-26) | F-005, F-009 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |

Ordre d'exécution : T9 (priorité), puis T2 à T6, T10, T11, T12, puis T7 et T8.

Avancement : 5 / 12 (tâches restantes : T5 à T8 et T10 à T12, soit 7). Prochaine tâche : T5 (F-031) ; `archi-backend` d'abord, puis migration probable (accord de l'utilisateur requis).

## Hors mission et préalables
- **Hors mission** : C-001 à C-008, F-032 à F-043, et les gênes C-010 à C-013, C-015 à C-020, C-022. C-014 et C-021 sont entrés avec T10 (2026-10-26). Les pannes trouvées par T1 vont au backlog ; elles n'entrent dans la mission qu'avec l'accord de l'utilisateur (tâche « ajoutée le … » dans « Changements de périmètre »).
- **Préalable levé** (2026-10-27) : le réalignement `staging` / `master` (C-001) est fait. `staging`, `master`, `origin/staging` et `origin/master` pointent tous sur `ccd9187` (vérifié par `git rev-parse`). L'ancien `staging` est conservé dans la branche locale `sauvegarde/staging-92bc906` (commit `92bc906`, absent de `master`) ; garder ou supprimer cette branche reste une décision de l'utilisateur. L'outillage (`.claude/`, `mapper/`, `CLAUDE.md`, `.gitignore`) est commité dans `474656a`, sur `staging`, non poussé (voir « À livrer »).

## À livrer
<!-- commits, fusions, push qui attendent la décision de l'utilisateur -->
- **État du dépôt au 2026-10-27** : `staging` et `origin/staging` sont à `769ec1a`. Poussés ensemble (`ccd9187..769ec1a`) après un « Vérifier » complet vert (255 tests), sur accord de l'utilisateur. Commits de la mission sur `staging` : `fb4963c` (T9), `474656a` (outillage), `f8b78f9` (T2), `769ec1a` (T3).
- **(a) F-011, commit puis fusion dans `staging`, sur accord** : arbre de travail non commité au 2026-10-27, branche `fix/F-011-depot-dossier-kyc` (partie de `staging` `769ec1a`). Modifiés (14) : `.env.exemple`, `backend/config/settings.py`, `backend/groupachat/catalogue/management/commands/charger_demo.py`, `backend/groupachat/comptes/models.py`, `backend/groupachat/comptes/serialiseurs.py`, `backend/groupachat/comptes/tests.py`, `backend/groupachat/comptes/vues.py`, `backend/groupachat/espaces/administration.py`, `backend/groupachat/noyau/limitation.py`, `backend/groupachat/tests/test_administration.py`, `backend/groupachat/tests/test_notifications_liens.py`, `frontend/admin/src/pages/Dossiers.tsx`, `frontend/boutique/src/pages/Profil.tsx`, `frontend/commun/src/api/types.ts`. Nouveaux (3) : `backend/groupachat/comptes/pieces_kyc.py`, `backend/groupachat/comptes/migrations/0004_noms_aleatoires_des_pieces_kyc.py`, `frontend/boutique/src/composants/ChampPiece.tsx`. Fiche [[F-011-depot-dossier-kyc]] et décisions [[2026-10-27-decisions-f011]] : dans `mapper/`, à commiter avec le changement.
- **(b) Push de `staging` après (a), sur accord** : une fois F-011 fusionnée dans `staging`. Le push de `ccd9187..769ec1a` est déjà fait.
- **(c) Avance de `master`, par l'utilisateur seul** : `master` reste à `ccd9187` tant que `staging` n'est pas testée. **Notes à signaler avant l'avance** :
  - la migration `echanges/0004` (F-008, D1) réécrira en production les anciens liens `/participations/<n>` en `/mes-achats/<n>` ([[2026-10-27-decisions-f008]]) ;
  - la migration `comptes/0004` (F-011, D8) ne touche pas aux données ;
  - `VERSION_DEMO` "6" est sans effet en production : l'utilisateur confirme `CHARGER_DEMO=0` sur achatgr.com (D10, [[2026-10-27-decisions-f011]]).
- **Hors git, décisions de l'utilisateur** : `backend/medias/kyc/` contient sept fichiers `piece_*.png` (dont un daté du 2026-10-27 08:45) ; ils ressemblent à des dépôts de test ou de démonstration. Les pièces déjà exposées en production : rotation ou suppression à décider (D-F030, C-025, voir [[2026-10-26-decisions-carte]] et [[2026-10-26-recette-failles]]). Dossiers validés sans pièce en production : C-048.
- T2 (F-016), T3 (F-008) et T9 (F-030) sont livrées dans `staging` (voir leurs lignes) ; elles ne sont plus à livrer.

## En attente
- **Carte** : `mapper/carte.md` affiche encore F-016 et F-008 comme partielles, F-030 comme constatée et F-011 comme partielle (état du 2026-10-26). Une mise à jour par le cartographe est nécessaire ; l'archiviste n'y touche pas.
- **Android réel** (C-049) : appareil photo et galerie à vérifier par l'utilisateur sur un vrai téléphone ; hors recette web.

## Changements de périmètre
<!-- AAAA-MM-JJ : T5 ajoutée (raison, accord de l'utilisateur) -->
- 2026-10-26 : T9 ajoutée. F-030 (pièces KYC lisibles sans compte, critique, [[2026-10-26-recette-failles]]). Traitée en premier, avant T2 ; branche `fix/F-030-fuite-kyc` depuis `staging`. Accord de l'utilisateur ; décision D-F030 dans [[2026-10-26-decisions-carte]].
- 2026-10-26 : T10 ajoutée. F-024 (double paiement, critique) avec F-018 et C-014 (`mettre_a_disposition` depuis `financee`) et C-021 (verrou dans `executer_decaissement`). Accord de l'utilisateur ; décision D-F024.
- 2026-10-26 : T11 ajoutée. F-010 et F-021 (avis modifiables par tous). Accord de l'utilisateur ; décision D-F010.
- 2026-10-26 : T12 ajoutée. F-005 (bouton « Participer » recouvert à 390 px) et F-009 (fil : réponse à une autre campagne, commentaire sur brouillon d'autrui, 500 sur campagne inexistante). Accord de l'utilisateur.
- 2026-10-26 : C-014 et C-021 retirés de « hors mission », rattachés à T10. Total des tâches 8 → 12, aucune retirée.
- 2026-10-27 : aucune tâche ajoutée ni retirée. Suivis de la recette T2 ajoutés au backlog, **hors mission** : C-026 à C-037 (décisions D1 à D4 : [[2026-10-27-decisions-f016]]).
- 2026-10-27 : aucune tâche ajoutée ni retirée (T3). Suivis de la recette T3 ajoutés au backlog, **hors mission** : C-038 à C-041 (décisions D1 à D3 : [[2026-10-27-decisions-f008]]). C-017 complété. Décision D1 (migration de données plutôt que redirection) : relecture de la migration demandée et acceptée par le chef de projet, retour neutre ; sans effet sur le périmètre des tâches.
- 2026-10-27 : aucune tâche ajoutée ni retirée (T4). Suivis de la recette F-011 ajoutés au backlog, **hors mission** : C-042 à C-050 (décisions D1 à D12 : [[2026-10-27-decisions-f011]]). C-031 complété (verrou de `DossierKYCVue.post`). C-038 terminé avec F-011.

## Clôture
<!-- date, preuve du critère de fin, mission suivante proposée -->
