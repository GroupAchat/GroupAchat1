---
type: architecture
statut: à jour
date: 2026-10-27
tags: [architecture]
---

# Architecture

La structure de référence est décrite dans `.claude/conventions/architecture.md`, `CLAUDE.md` et `README.md`. Résumé et points d'entrée pour une évolution.

## Backend — `backend/groupachat/`
| Dossier | Rôle | Points d'entrée |
|---|---|---|
| `catalogue/` | catégories, produits, campagnes, paliers, médias ; tâche de clôture | `models.py` (`Campagne.Statut`), `vues.py` (`STATUTS_LISTES`, `STATUTS_CONSULTABLES`), `management/commands/cloturer_les_campagnes_echues.py`, `charger_demo.py` (`VERSION_DEMO`) |
| `commandes/` | participations, code de retrait, avis | `models.py` (`Participation`, `engendrer_code_retrait`), `vues.py` |
| `comptes/` | utilisateur, code SMS, dossier KYC, réputation | `models.py`, `services.py` (`envoyer_code`), `vues.py`, `pieces_kyc.py` (`PieceKycField` : format lu par Pillow, taille, pixels des pièces KYC), `migrations/0004_noms_aleatoires_des_pieces_kyc.py` |
| `echanges/` | fil de discussion, j'aime, demandes communautaires, notifications | `models.py` (`Notification.Genre`), `vues.py`, `migrations/0004_corriger_liens_des_notifications.py` (migration de données : `/participations/<n>` → `/mes-achats/<n>`) |
| `paiements/` | séquestre, transactions, décaissements ; **le cycle de vie qui écrit** | `services.py` : `encaisser`, `rembourser`, `cloturer`, `maintenir`, `annuler`, `cloturer_les_echus`, `rembourser_les_indecis`, `demander_decaissement`, `executer_decaissement`, `mettre_a_disposition`, `valider_retrait`, `recalculer_reputation`. Ordre des verrous : **campagne → décaissement → séquestre** (`executer_decaissement`, `annuler`, `mettre_a_disposition`, `demander_decaissement`) ; `cloturer` ne le respecte pas encore (C-052). Contrainte en base `sequestre_ne_sort_pas_plus_que_consigne` (`migrations/0002`, C-006). `management/commands/controler_les_sequestres.py` : contrôle en lecture seule des anomalies du séquestre et des décaissements (quatre rubriques). Tests : `tests.py`, et `tests/test_decaissement_double_paiement.py` au niveau transversal |
| `espaces/` | vues de rôle (aucun modèle) | `groupeur.py` (publier, participants, clôturer, maintenir, annuler, demander-retrait, mise-a-disposition, retrait, signature Cloudinary, tableau de bord, état KYC), `administration.py` (dossiers, décaissements, modération, clôture forcée, tableau de bord) |
| `noyau/` | transversal | `permissions.py`, `limitation.py`, `hebergement.py` |
| `tests/` | tests transversaux | `test_administration.py`, `test_cloture.py`, `test_securite.py`, `test_notifications_liens.py` (copie des routes de `App.tsx`, [[2026-10-27-decisions-f008]]), `test_decaissement_double_paiement.py` (courses sous PostgreSQL, [[2026-10-27-decisions-f024]]) |
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
`distribution → terminee` : quand tous les codes sont validés (`valider_retrait`). **Manque** : la clôture réputée acquise à J+14 et les relances J+3 / J+7 (`Campagne.mise_a_disposition_le` est posé, le genre `Notification.RELANCE_RETRAIT` existe, aucune tâche ne les exploite).

## Frontend — `frontend/`
| Dossier | Rôle | Écrans |
|---|---|---|
| `commun/src/` | socle unique (aucune page) | `api/client.ts`, `api/types.ts`, `contexte/Session.tsx`, `outils/`, `composants/ui.tsx`, `index.css` |
| `boutique/src/` | acheteurs et groupeurs, port 5173 | Accueil, Catalogue, FicheCampagne, Authentification, MesAchats, Notifications, Profil, Communauté ; groupeur : EspaceGroupeur, TableauDeBord, NouvelleCampagne, CampagneGroupeur |
| `admin/src/` | console, port 5174 | TableauAdmin, Dossiers, Décaissements (modération incluse) |

## Vérification
`bash .claude/skills/verify/scripts/check.sh complet` : migrations, pytest (356 tests au 2026-10-27, après F-024 : `356 passed, 5 skipped` sous SQLite, les 5 propres à PostgreSQL ; 308 après F-011, 255 avant ; la suite complète dure environ 20 minutes (1243 s au « Vérifier » de F-011) ; 7 minutes était la durée de 165 tests), `npm run verifier`. Les courses de F-024 ne tournent réellement que sous PostgreSQL (passe de relecture : 53 passed, 0 skipped).
