---
type: architecture
statut: à jour
date: 2026-10-28
tags: [architecture]
---

# Architecture

La structure de référence est décrite dans `.claude/conventions/architecture.md`, `CLAUDE.md` et `README.md`. Résumé et points d'entrée pour une évolution.

## Backend — `backend/groupachat/`
| Dossier | Rôle | Points d'entrée |
|---|---|---|
| `catalogue/` | catégories, produits, campagnes, paliers, médias ; tâche de clôture | `models.py` (`Campagne.Statut`, dates de relance `relance_retrait_j3_le` / `relance_retrait_j7_le`, `fin_du_retrait_le`), `vues.py` (`STATUTS_LISTES`, `STATUTS_CONSULTABLES`), `management/commands/cloturer_les_campagnes_echues.py` (quatre étapes, `--a-blanc`), `charger_demo.py` (`VERSION_DEMO` « 7 »), `migrations/0007_relances_de_retrait.py` |
| `commandes/` | participations, code de retrait, avis | `models.py` (`Participation`, `engendrer_code_retrait`, statut `reputee_livree` et `reputee_livree_le`), `vues.py`, `migrations/0004_participation_reputee_livree.py` |
| `comptes/` | utilisateur, code SMS, dossier KYC, réputation | `models.py`, `services.py` (`envoyer_code`), `vues.py`, `pieces_kyc.py` (`PieceKycField` : format lu par Pillow, taille, pixels des pièces KYC), `migrations/0004_noms_aleatoires_des_pieces_kyc.py` |
| `echanges/` | fil de discussion, j'aime, demandes communautaires, notifications | `models.py` (`Notification.Genre`), `vues.py`, `migrations/0004_corriger_liens_des_notifications.py` (migration de données : `/participations/<n>` → `/mes-achats/<n>`), `migrations/0005_alter_notification_genre.py` (genres `livraison_reputee`, `campagne_terminee`) |
| `paiements/` | séquestre, transactions, décaissements ; **le cycle de vie qui écrit** | `services.py` : `encaisser`, `rembourser`, `cloturer`, `maintenir`, `annuler`, `cloturer_les_echus`, `rembourser_les_indecis`, `demander_decaissement`, `executer_decaissement`, `mettre_a_disposition`, `valider_retrait` (verrouillé, garde de statut), `recalculer_reputation`, `_terminer`, `_verrouiller`. `retraits.py` (F-031) : `relancer_retrait` / `relancer_les_retraits` (J+3, J+7), `reputer_livree` / `reputer_livrees_les_echues` (J+14, part `reputee_livree`, campagne `terminee`, réputation créditée une fois), `etape_de_relance`, `situation_a_j_plus_14` ; aucun argent n'y bouge. Ordre des verrous : **campagne → décaissement → séquestre** (`executer_decaissement`, `annuler`, `mettre_a_disposition`, `demander_decaissement`) ; `cloturer` verrouille la campagne en tête (C-052, T5) ; `retraits.py` suit le même ordre. Contrainte en base `sequestre_ne_sort_pas_plus_que_consigne` (`migrations/0002`, C-006). `management/commands/controler_les_sequestres.py` : contrôle en lecture seule des anomalies du séquestre et des décaissements (quatre rubriques). Tests : `tests.py`, et `tests/test_decaissement_double_paiement.py` au niveau transversal |
| `espaces/` | vues de rôle (aucun modèle) | `groupeur.py` (publier, participants, clôturer, maintenir, annuler, demander-retrait, mise-a-disposition, retrait, signature Cloudinary, tableau de bord, état KYC), `administration.py` (dossiers, décaissements, modération, clôture forcée, tableau de bord) |
| `noyau/` | transversal | `permissions.py`, `limitation.py`, `hebergement.py` |
| `tests/` | tests transversaux | `test_administration.py`, `test_cloture.py`, `test_securite.py`, `test_notifications_liens.py` (copie des routes de `App.tsx`, [[2026-10-27-decisions-f008]]), `test_decaissement_double_paiement.py` (courses sous PostgreSQL, [[2026-10-27-decisions-f024]]), `test_retraits_echus.py` (54 tests : relances, livraison réputée, retrait tardif, API, commande, courses ; [[2026-10-27-decisions-f031]]) |
| `api.py` | toutes les routes | routeur DRF + chemins `comptes/…`, `groupeur/…`, `admin/…` |

## Cycle de vie d'une campagne (cahier des charges §9)
```
brouillon → en_cours → (date limite : clôture automatique, cloturer_les_campagnes_echues)
   ├── minimum atteint ─────→ financee → decaissee → approvisionnement → distribution → terminee
   └── minimum non atteint → minimum_non_atteint (argent consigné)
                                ├── maintenir → financee → …
                                ├── renoncer  → annulee (remboursements)
                                └── 7 jours sans décision → annulee (rembourser_les_indecis)
```
`distribution → terminee` : quand tous les codes sont validés (`valider_retrait`), ou à J+14 pour les parts non retirées, qui passent `reputee_livree` (`paiements/retraits.py`, F-031). Relances à J+3 et J+7 : genre `relance_retrait`, par la même commande `cloturer_les_campagnes_echues` (une seule tâche planifiée, toutes les heures). Un colis non retiré ne bloque donc plus la campagne en `distribution`. Au passage, la date de mise à disposition (`Campagne.mise_a_disposition_le`) porte tout le calendrier.

## Frontend — `frontend/`
| Dossier | Rôle | Écrans |
|---|---|---|
| `commun/src/` | socle unique (aucune page) | `api/client.ts`, `api/types.ts`, `contexte/Session.tsx`, `outils/`, `composants/ui.tsx`, `index.css` |
| `boutique/src/` | acheteurs et groupeurs, port 5173 | Accueil, Catalogue, FicheCampagne, Authentification, MesAchats, Notifications, Profil, Communauté ; groupeur : EspaceGroupeur, TableauDeBord, NouvelleCampagne, CampagneGroupeur |
| `admin/src/` | console, port 5174 | TableauAdmin, Dossiers, Décaissements (modération incluse) |

## Vérification
`bash .claude/skills/verify/scripts/check.sh complet` : migrations, pytest (406 tests au 2026-10-28, après F-031 : `406 passed, 9 skipped` sous SQLite (9 ignorés, sans détail au relevé) ; 356 après F-024 (`356 passed, 5 skipped`), 308 après F-011, 255 avant ; la suite complète dure environ 30 à 35 minutes (1818 s et 2072 s au « Vérifier » sur `staging`, 2026-10-28 ; 1355 s au « Vérifier » de F-031, 1243 s pour F-011) ; 7 minutes était la durée de 165 tests), `npm run verifier`. `check.sh rapide` : 338 passed, 9 skipped (F-031). Les courses de F-024 ne tournent réellement que sous PostgreSQL (passe de relecture : 53 passed, 0 skipped).
