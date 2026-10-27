---
type: architecture
statut: à jour
date: 2026-10-26
tags: [architecture]
---

# Architecture

La structure de référence est décrite dans `.claude/conventions/architecture.md`, `CLAUDE.md` et `README.md`. Résumé et points d'entrée pour une évolution.

## Backend — `backend/groupachat/`
| Dossier | Rôle | Points d'entrée |
|---|---|---|
| `catalogue/` | catégories, produits, campagnes, paliers, médias ; tâche de clôture | `models.py` (`Campagne.Statut`), `vues.py` (`STATUTS_LISTES`, `STATUTS_CONSULTABLES`), `management/commands/cloturer_les_campagnes_echues.py`, `charger_demo.py` (`VERSION_DEMO`) |
| `commandes/` | participations, code de retrait, avis | `models.py` (`Participation`, `engendrer_code_retrait`), `vues.py` |
| `comptes/` | utilisateur, code SMS, dossier KYC, réputation | `models.py`, `services.py` (`envoyer_code`), `vues.py` |
| `echanges/` | fil de discussion, j'aime, demandes communautaires, notifications | `models.py` (`Notification.Genre`), `vues.py` |
| `paiements/` | séquestre, transactions, décaissements ; **le cycle de vie qui écrit** | `services.py` : `encaisser`, `rembourser`, `cloturer`, `maintenir`, `annuler`, `cloturer_les_echus`, `rembourser_les_indecis`, `demander_decaissement`, `executer_decaissement`, `mettre_a_disposition`, `valider_retrait`, `recalculer_reputation` |
| `espaces/` | vues de rôle (aucun modèle) | `groupeur.py` (publier, participants, clôturer, maintenir, annuler, demander-retrait, mise-a-disposition, retrait, signature Cloudinary, tableau de bord, état KYC), `administration.py` (dossiers, décaissements, modération, clôture forcée, tableau de bord) |
| `noyau/` | transversal | `permissions.py`, `limitation.py`, `hebergement.py` |
| `tests/` | tests transversaux | `test_administration.py`, `test_cloture.py`, `test_securite.py` |
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
`bash .claude/skills/verify/scripts/check.sh complet` : migrations, pytest (244 tests au 2026-10-27 ; la durée d'environ 7 min était celle de 165 tests), `npm run verifier`.
