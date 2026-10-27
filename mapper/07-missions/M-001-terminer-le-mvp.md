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
| T2 | F-016 Maintenir / renoncer : `CampagneGroupeur.tsx` appelle `/api/api/…` (boucle préparer → fonctionnalite → reviewer-tester → recette) | F-016 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T3 | F-008 Liens des notifications vers `/mes-achats/:id` (même boucle) | F-008 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T4 | F-011 Pièces KYC recto/verso obligatoires, écran et serveur (même boucle ; touche l'authentification/KYC et le contrat d'API : accord utilisateur requis) | F-011 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T5 | F-031 Relances J+3/J+7 par notification, clôture J+14 avec statut « réputée livrée », campagne `terminee`, réputation créditée (archi-backend d'abord, puis même boucle ; migration probable : accord utilisateur requis) | F-031 | GroupAchat1 | archi-backend, puis recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T6 | C-009 Textes de la promesse (`FicheCampagne.tsx`, `CampagneGroupeur.tsx`) (même boucle) | C-009 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T7 | Recette de l'ensemble du MVP | F-001 à F-031 | GroupAchat1 | recette | à faire | |
| T8 | Audit des règles | F-001 à F-031 | GroupAchat1 | regles-auditor | à faire | |
| T9 | F-030 Fuite des pièces KYC : traversée `/medias/x/%2e%2e/kyc/…` et doublon `static()` en DEBUG ; test de régression. **Priorité : traitée en premier, avant T2** (ajoutée le 2026-10-26) | F-030 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette ; branche `fix/F-030-fuite-kyc` depuis `staging` | terminée | reviewer-tester : VALIDÉE, aucun point bloquant ; « Vérifier » `check.sh complet` : CHECK: OK, migrations « No changes detected », **225 tests verts**, typage des deux interfaces OK ; 60 tests `TestPiecesKycPrivees` (`backend/groupachat/tests/test_securite.py`, DEBUG=0 et 1), sans correctif 24 échouent. Recette : **RECETTE OK** le 2026-10-27 (détail : [[F-030-pieces-kyc-privees]], section « Résultat de la recette »). Correctif non commité (voir « À livrer »). |
| T10 | F-024 Double paiement : `mettre_a_disposition` refusé hors `financee` (F-018, C-014) ; décaissement refusé automatiquement à l'annulation ; `executer_decaissement` sous `select_for_update` avec contrôle du statut (C-021) ; annulation interdite si le décaissement est exécuté (D-F024) (ajoutée le 2026-10-26) | F-024, F-018 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette (archi-backend si besoin) | à faire | |
| T11 | F-010 Avis modifiables et supprimables par des tiers : seul l'auteur modifie ou supprime, tout autre (groupeur compris) reçoit 403, le groupeur garde son droit de réponse (D-F010) ; F-021 suit (réputation) (ajoutée le 2026-10-26) | F-010, F-021 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |
| T12 | F-005 : bouton « Participer » recouvert à 390 px (`FicheCampagne.tsx:515`) ; F-009 : réponse à un message d'une autre campagne refusée, commentaire sur le brouillon d'autrui refusé, campagne inexistante sans 500 (ajoutée le 2026-10-26) | F-005, F-009 | GroupAchat1 | recette préparer → fonctionnalite → reviewer-tester → recette | à faire | |

Ordre d'exécution : T9 (priorité), puis T2 à T6, T10, T11, T12, puis T7 et T8.

Avancement : 2 / 12 (tâches restantes : T2 à T8 et T10 à T12, soit 10). Prochaine tâche : T2.

## Hors mission et préalables
- **Hors mission** : C-001 à C-008, F-032 à F-043, et les gênes C-010 à C-013, C-015 à C-020, C-022. C-014 et C-021 sont entrés avec T10 (2026-10-26). Les pannes trouvées par T1 vont au backlog ; elles n'entrent dans la mission qu'avec l'accord de l'utilisateur (tâche « ajoutée le … » dans « Changements de périmètre »).
- **Préalable levé** (2026-10-27) : le réalignement `staging` / `master` (C-001) est fait. `staging`, `master`, `origin/staging` et `origin/master` pointent tous sur `ccd9187` (vérifié par `git rev-parse`). L'ancien `staging` est conservé dans la branche locale `sauvegarde/staging-92bc906` (commit `92bc906`, absent de `master`) ; garder ou supprimer cette branche reste une décision de l'utilisateur. Reste ouvert : l'outillage `.claude/`, `mapper/`, `CLAUDE.md` et `.gitignore` n'est pas commité (voir « À livrer »).

## À livrer
<!-- commits, fusions, push qui attendent la décision de l'utilisateur -->
- **T9 (F-030), à décider par l'utilisateur** : commit du correctif sur la branche `fix/F-030-fuite-kyc` (HEAD `ccd9187`, arbre de travail non commité) : `backend/config/service/fichiers.py`, `backend/config/urls.py`, `backend/groupachat/tests/test_securite.py` (les trois fichiers backend). Puis fusion dans `staging` sur accord, jamais dans `master`.
- **Outillage, à commiter à part, sur accord** : `.claude/`, `mapper/`, `CLAUDE.md` et `.gitignore` (non suivis ou modifiés, hors correctif F-030). Ne pas les mêler au commit F-030.
- **Hors git, décisions de l'utilisateur** : `backend/medias/kyc/` contient sept fichiers `piece_*.png` (dont un daté du 2026-10-27 08:45) ; ils ressemblent à des dépôts de test ou de démonstration. Les pièces déjà exposées en production : rotation ou suppression à décider (D-F030, voir [[2026-10-26-decisions-carte]] et [[2026-10-26-recette-failles]]).
- Rien d'autre à livrer : T1 n'a touché aucun fichier de code ni de git.

## Changements de périmètre
<!-- AAAA-MM-JJ : T5 ajoutée (raison, accord de l'utilisateur) -->
- 2026-10-26 : T9 ajoutée. F-030 (pièces KYC lisibles sans compte, critique, [[2026-10-26-recette-failles]]). Traitée en premier, avant T2 ; branche `fix/F-030-fuite-kyc` depuis `staging`. Accord de l'utilisateur ; décision D-F030 dans [[2026-10-26-decisions-carte]].
- 2026-10-26 : T10 ajoutée. F-024 (double paiement, critique) avec F-018 et C-014 (`mettre_a_disposition` depuis `financee`) et C-021 (verrou dans `executer_decaissement`). Accord de l'utilisateur ; décision D-F024.
- 2026-10-26 : T11 ajoutée. F-010 et F-021 (avis modifiables par tous). Accord de l'utilisateur ; décision D-F010.
- 2026-10-26 : T12 ajoutée. F-005 (bouton « Participer » recouvert à 390 px) et F-009 (fil : réponse à une autre campagne, commentaire sur brouillon d'autrui, 500 sur campagne inexistante). Accord de l'utilisateur.
- 2026-10-26 : C-014 et C-021 retirés de « hors mission », rattachés à T10. Total des tâches 8 → 12, aucune retirée.

## Clôture
<!-- date, preuve du critère de fin, mission suivante proposée -->
