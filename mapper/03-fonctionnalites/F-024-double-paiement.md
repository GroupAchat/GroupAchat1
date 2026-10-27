---
type: fonctionnalite
id: F-024
statut: terminée
date: 2026-10-27
tags: [fonctionnalite, F-024, F-018, C-014, C-021, decaissement, sequestre, argent, mvp]
---

# F-024 — Décaissement : plus de double paiement (avec F-018, C-014, C-021)

Statut : **terminée** (2026-10-27) : RECETTE OK après reprise, relecture `reviewer-tester` VALIDÉE. **Non commitée** : la base est `abaa622`, l'arbre de travail porte le correctif (commit et fusion attendent la décision de l'utilisateur). Tâche T10 de [[M-001-terminer-le-mvp]] ; décision D-F024 ([[2026-10-26-decisions-carte]], section « Décisions après l'état des lieux »). Panne d'origine : [[2026-10-26-recette-failles]] n°3 et [[recette-etat-des-lieux-2026-10-26]].

Rôles : **Administrateur** (exécute), **Groupeur** (demande, annule, met à disposition), **Acheteur** (remboursé), **Système**. Couches : serveur oui · web admin oui · web boutique oui · mobile non (pas d'application dans ce dépôt). Source : `CAHIER_DES_CHARGES.md` §6 (« Décaissement », 100 % moins 1 500 FCFA), §9 (cycle de vie) ; Q4, Q6, Q9, Q14 de [[2026-10-26-decisions-carte]].
Hors périmètre : refuser un décaissement avec motif, par l'administrateur (F-042) ; relances de retrait (F-031, voir « Cohérence »).

**Code écrit et recetté.** Les questions Q1 à Q7 ont été tranchées par l'utilisateur le 2026-10-27 (section « Décisions » ci-dessous, détail dans [[2026-10-27-decisions-f024]]), et la conception est faite (section « Conception (archi-backend, 2026-10-27) »). Le point N1 (déploiement) est traité par la ligne de contrôle de `COOLIFY.md` §8. N2 et N3 sont des ajouts facultatifs de la conception ; leur statut n'a pas été relevé au 2026-10-27.

## Vérification (2026-10-27)

- Relecture `reviewer-tester`, première passe **À CORRIGER** : deux tests faux sous PostgreSQL (R33 : verrou pris dans un point de sauvegarde annulé ; rubrique 1 : `pending trigger events`). Le code de production était jugé bon. Corrigés.
- Relecture, seconde passe **VALIDÉE** : `53 passed in 251.47s` sur PostgreSQL 17, aucun test ignoré, courses R31 à R33 comprises. Avant correction, R2 échouait sur l'ancien code, avec ou sans la contrainte.
- « Vérifier » `check.sh complet` : **356 passed, 5 skipped**, `CHECK: OK (complet)`. Les 5 ignorés sous SQLite sont les tests propres à PostgreSQL, couverts par la passe PostgreSQL ci-dessus.
- `check.sh rapide` : `CHECK: OK`. `test-diff.sh` : 0 signal.
- Recette : voir « Recette — 2026-10-27 » et « Reprise R11/R12 — 2026-10-27 » ci-dessous.

## Décisions

Réponses de l'utilisateur du 2026-10-27 aux questions de la fiche (le détail des options reste dans « Questions ouvertes », en fin de fiche).

| Q | Décision |
|---|---|
| Q1 | `mettre_a_disposition` n'est permis que depuis `approvisionnement`. `decaissee` est exclu, après avoir vérifié qu'aucune campagne n'y est. Aucun code n'affecte ce statut et la base locale ne contient aucune campagne. Pour la production, c'est la commande Q6 qui le vérifie (voir N1). |
| Q2 | Exécution avec un solde inférieur au brut : **refus 400**, le décaissement reste `demande`. **Oui à la contrainte en base** `montant_libere + montant_rembourse <= montant_consigne` (C-006, migration `paiements`). |
| Q3 | Les cinq messages de la fiche sont validés tels quels. Le dernier (« Les fonds ont déjà été versés au groupeur : cette campagne ne peut plus être annulée. ») ne remplace « Cette campagne ne peut plus être annulée. » que si un décaissement exécuté existe. |
| Q4 | À l'annulation, un décaissement `demande` passe `refuse`, avec `motif_refus = "Campagne annulée le <date> : <motif>"`. Le groupeur est prévenu par le genre existant `campagne_annulee`. Pas de nouveau genre, pas de migration `echanges`. |
| Q5 | Aucun changement d'écran pour le bouton d'annulation en `financee`, qui part au backlog. Restent à faire : l'affichage de `motif_refus` dans `Decaissements.tsx` et le retrait de `decaissee` de la condition de `CampagneGroupeur.tsx`. |
| Q6 | Une **commande de gestion en lecture seule** qui liste les anomalies : séquestres dont libéré + remboursé dépasse le consigné, décaissements `demande` sur une campagne qui n'est pas `financee`, campagnes en `decaissee`. |
| Q7 | Le refus écrit puis annulé quand l'opérateur échoue part **au backlog** (avec F-043), hors T10. |

## La règle

Enchaînement réel des statuts de `Campagne` (`catalogue/models.py` l. 271-285) : `brouillon → en_cours → financee | minimum_non_atteint → … → approvisionnement → distribution → terminee`, plus `annulee`. Le statut `decaissee` existe dans l'énumération mais **aucun code ne l'affecte jamais** : `executer_decaissement` fait passer `financee` directement à `approvisionnement` (`services.py` l. 508-510). Q14 le retire du modèle (C-005).

Ce que change « décaissement exécuté » : le `Decaissement` passe `execute` ; le séquestre gagne `montant_libere += montant_brut` et passe `libere` ; la campagne passe `approvisionnement`. C'est le seul endroit où l'argent quitte le séquestre vers le groupeur.

| Action | Statut de campagne permis | Autre condition | Statut de campagne après |
|---|---|---|---|
| Demander le retrait (`demander_decaissement`, inchangé) | `financee` | aucun décaissement existant pour la campagne | `financee` |
| **Exécuter le décaissement** | `financee` | décaissement `demande` (ni `execute`, ni `refuse`) ; solde du séquestre ≥ `montant_brut` (voir Q2) ; tout relu sous verrou | `approvisionnement` |
| **Mettre à disposition** | `approvisionnement` seulement | campagne relue sous verrou | `distribution` |
| **Annuler** | `en_cours`, `minimum_non_atteint`, `financee` (Q6, inchangé) | aucun décaissement `execute` ; si un décaissement `demande` existe il est refusé automatiquement dans la même transaction | `annulee` |

Conséquence pour `mettre_a_disposition` : `financee` est **retirée** de la liste des statuts permis. `decaissee` y est aussi retirée (jamais atteint ; Q14), voir Q1.

Verrous : ordre unique **campagne, puis décaissement, puis séquestre**, dans `executer_decaissement`, `annuler` et `mettre_a_disposition`, pour qu'une annulation et une exécution qui se croisent ne s'interbloquent pas et que la seconde voie l'état de la première.

## État constaté du code (2026-10-27, `abaa622`)

| Élément | Constat |
|---|---|
| `executer_decaissement` (`paiements/services.py` l. 473-522) | Seule garde : `decaissement.statut == EXECUTE` (l. 476), sur un objet lu **avant** la transaction par `self.get_object()` (`administration.py` l. 135). Ni `select_for_update`, ni contrôle du statut de la campagne, ni du solde. Un décaissement `refuse` serait exécuté. Montant versé = `montant_brut` figé à la demande, jamais comparé au solde. |
| Repasse à `approvisionnement` | l. 508-510 : `campagne.statut = APPROVISIONNEMENT` sans condition, donc une campagne `annulee` redevient vivante. |
| `annuler` (l. 325-375) | Verrouille la campagne (`_verrouiller`), rembourse les parts, passe le séquestre à `rembourse`. **Ne regarde pas** le `Decaissement` : un décaissement `demande` reste en attente et exécutable. Refuse déjà `approvisionnement` et au-delà (« Cette campagne ne peut plus être annulée. », l. 336-342), donc l'annulation après exécution est **déjà interdite par le statut**, mais sans test ni garde sur le décaissement. |
| `mettre_a_disposition` (l. 525-566) | Accepte `approvisionnement`, `decaissee`, **`financee`** (l. 531-535), sans verrou. Depuis `financee`, le décaissement est sauté : participations `prete`, codes actifs, mais séquestre jamais libéré (C-014). |
| `demander_decaissement` (l. 450-470) | Refuse hors `financee` et si un décaissement existe (`OneToOne`). Non verrouillé : deux clics simultanés, l'un échoue sur l'unicité en base (500 possible). Hors périmètre, à noter. |
| Contraintes du séquestre (`paiements/models.py` l. 56-71) | `libere ≤ consigné` et `rembourse ≤ consigné`, **chacune isolément**. Rien n'interdit `libere + rembourse > consigné` : c'est ce qui laisse passer 475 000 remboursés + 473 500 versés (C-006). |
| Échec opérateur (l. 485-492) | Le statut `refuse` est enregistré puis `ErreurPaiement` levée **dans** un `@transaction.atomic` : l'écriture est annulée avec la transaction. Défaut latent, hors périmètre (passerelle simulée, Q10/F-043), à noter. |
| `Decaissement.Statut` | `demande`, `approuve` (jamais utilisé), `execute`, `refuse` (n'est posé que par l'échec opérateur). Champ `motif_refus` existe. |
| Vue admin (`administration.py` l. 133-141) | `POST /api/admin/decaissements/<id>/executer/` ; `ErreurPaiement` devient 400 `{"detail": …}`. Permission `EstAdministrateur`. Le sérialiseur renvoie déjà `statut` et `motif_refus`. |
| Vue groupeur (`groupeur.py` l. 171-186, 204-216) | `annuler` et `mise-a-disposition` convertissent `ErreurPaiement` en 400 `{"detail": …}`. |
| Console admin (`Decaissements.tsx`) | « À libérer » = `statut === "demande"` (bouton « Libérer … FCFA ») ; le reste en « Historique » avec l'étiquette « Versé » ou « **Refusé** » (tout statut non `execute`). `motif_refus` n'est pas affiché. L'erreur du serveur s'affiche via `<Alerte>` (l. 47). |
| Boutique (`CampagneGroupeur.tsx`) | `financee` : bouton « Demander le retrait » (l. 206-213) **sans** bouton d'annulation (le seul « Renoncer et rembourser » est en `minimum_non_atteint`, l. 196) ; `decaissee` / `approvisionnement` : formulaire de mise à disposition (l. 215-228) ; aucun bouton de mise à disposition en `financee`. Le bouton « Demander le retrait » reste affiché après la demande (relevé F-017 de la T1). |
| Jeu de démonstration (`charger_demo.py` l. 624-662) | Passe toujours par `executer_decaissement` avant `mettre_a_disposition` : pas affecté par le correctif. |
| Tests existants | `commandes/tests.py` l. 236-305 (demande, unicité, exécution), `test_notifications_liens.py` l. 252-270 (parcours complet). Aucun ne met à disposition depuis `financee`, aucun n'annule avec un décaissement, aucun test de verrou. |

L'API d'annulation d'une campagne `financee` par le groupeur existe côté serveur (`POST /api/groupeur/campagnes/<id>/annuler/`, Q6 « gardée »), mais **aucun écran ne la propose** depuis `financee` : la T1 l'a reproduite par requête directe. Le double paiement est donc atteignable par API ; la fiche exige qu'il soit fermé à ce niveau (Q5 pour l'écran).

## Recette
Rôle : administrateur, groupeur, acheteur, système · Couches : serveur oui · web admin oui · web boutique oui · mobile non · Source : CDC §6 et §9 ; Q4, Q6, Q14 ; D-F024.

Données communes : groupeur validé G, acheteurs A1 et A2, campagne C de 10 pièces minimum à 18 000 FCFA l'unité, A1 paie 6 pièces et A2 4 pièces : consigné **180 000**. Frais **1 500**, net **178 500**. Messages en français à confirmer (Q3). « Séquestre avant / après » se lit par `Sequestre.objects.get(campagne=C)` (champs `montant_consigne`, `montant_libere`, `montant_rembourse`, `statut`) ; solde = consigné − libéré − remboursé.

### Scénarios — Administrateur

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | C `financee`, G a demandé le retrait (décaissement `demande`, brut 180 000, net 178 500) | l'administrateur `POST /api/admin/decaissements/<id>/executer/` | 200 ; `statut="execute"`, `execute_par` = l'admin, `reference` non vide ; séquestre : libéré 0 → 180 000, rembourse 0, statut `libere`, solde 0 ; C `approvisionnement` ; une notification « Fonds versés » pour G (lien `/groupeur/campagnes/<id>`) | serveur |
| R2 | C `financee`, décaissement `demande` ; **reproduction T1** : G annule C (`POST /api/groupeur/campagnes/<id>/annuler/`) : A1 et A2 remboursés (180 000), séquestre `rembourse` | l'administrateur exécute le décaissement resté en attente | **400** `{"detail": …}` (message : Q3) ; le décaissement est `refuse` (voir R10) ; séquestre inchangé (libéré 0, remboursé 180 000) ; C reste `annulee` ; aucune notification « Fonds versés » ; aucun `Transaction` ni versement ; le total sorti (remboursé + libéré) vaut 180 000 et non 358 500 | serveur |
| R3 | décaissement `refuse` (par R2) | l'administrateur l'exécute de nouveau | 400 ; statut inchangé ; séquestre inchangé | serveur |
| R4 | décaissement déjà `execute` (R1) | l'administrateur l'exécute de nouveau | 400 « Ce décaissement a déjà été exécuté. » ; `montant_libere` reste 180 000 (pas 360 000) ; une seule notification « Fonds versés » ; `execute_le` et `reference` inchangés | serveur |
| R5 | C `financee`, décaissement `demande` mais le solde du séquestre est inférieur au brut (état forcé par le test : `montant_rembourse` > 0, une part remboursée hors annulation) | l'administrateur l'exécute | 400 (message : Q3) ; rien d'écrit ; décaissement toujours `demande` (Q2 : refus pur, ou aussi `refuse`) | serveur |
| R6 | C dans un statut autre que `financee` (`en_cours`, `minimum_non_atteint`, `approvisionnement`, `distribution`, `terminee`) avec un décaissement `demande` (forcé par le test) | l'administrateur l'exécute | 400 pour chacun ; rien d'écrit, séquestre et statut de C inchangés | serveur |
| R7 | un acheteur, un groupeur, un anonyme | chacun `POST …/executer/` | 403 (anonyme : 401 ou 403 selon la session) ; rien d'écrit ; séquestre inchangé | serveur |
| R8 | décaissement inexistant (`id` inconnu) | l'administrateur exécute | 404 | serveur |
| R9 | console admin, `/decaissements`, ligne « À libérer » pour C `financee` | l'administrateur clique « Libérer 178 500 FCFA » | bouton en chargement pendant l'appel (pas de double clic), puis la ligne passe dans « Historique » avec « Versé » et la date de versement | web admin |
| R10 | R2 jouée, console admin rechargée | l'administrateur ouvre `/decaissements` | la ligne du décaissement refusé **n'est plus** dans « À libérer » : aucun bouton « Libérer » ; elle est dans « Historique » avec l'étiquette « Refusé » **et** le motif (« Campagne annulée… », Q4) ; `motif_refus` non vide dans `GET /api/admin/decaissements/` | serveur + web admin |
| R11 | console admin ouverte avant l'annulation (ligne « À libérer » périmée), puis G annule | l'administrateur clique « Libérer » | le message du serveur s'affiche lisiblement dans l'`Alerte` en haut de page ; la liste se recharge (la ligne passe en « Historique ») ; pas de page vide ni d'erreur générique « Connexion impossible » | web admin |
| R12 | `/decaissements`, 390 px | l'administrateur ouvre la page : chargement, aucune demande, erreur réseau | squelette pendant le chargement ; « Aucune demande » si vide ; l'erreur s'affiche et n'est pas prise pour un état vide | web admin |

### Scénarios — Groupeur

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R13 | C `financee`, **sans** décaissement exécuté (cas C-014) | G `POST /api/groupeur/campagnes/<id>/mise-a-disposition/` `{"point_remise": "Boutique Abalo"}` | **400** (message : Q3) ; C reste `financee` ; aucune participation `prete` ; **0** notification `marchandise_disponible` ; séquestre inchangé (solde 180 000) | serveur |
| R14 | C `financee` avec décaissement `demande` | G met à disposition | 400 ; mêmes constats que R13 ; décaissement toujours `demande` | serveur |
| R15 | C `approvisionnement` (décaissement R1 exécuté) | G met à disposition avec un point de remise | 200 `{"participants_notifies": 2, "point_remise": …}` ; C `distribution`, `mise_a_disposition_le` posée ; A1 et A2 `prete` ; 2 notifications « Votre produit est arrivé » avec le code de retrait ; séquestre inchangé (libéré 180 000, solde 0) | serveur |
| R16 | C `distribution`, ou `terminee`, ou `annulee`, ou `en_cours` | G met à disposition | 400 ; aucun changement ; aucune notification | serveur |
| R17 | un autre groupeur G2 (campagne d'autrui) | G2 met à disposition la campagne de G | 404 (queryset filtré par propriétaire) ; rien d'écrit | serveur |
| R18 | C `financee`, décaissement `demande` | G annule (`POST …/annuler/` `{"motif": "Fournisseur défaillant"}`) | 200 ; C `annulee`, `motif_annulation` posé ; A1 et A2 `remboursee`, 2 transactions de remboursement ; séquestre : consigné 180 000, remboursé 180 000, libéré 0, statut `rembourse`, solde 0 ; **le décaissement passe `refuse`** avec `motif_refus` non vide ; une notification à G (Q4) ; `Reputation.campagnes_annulees` +1 | serveur |
| R19 | C `financee`, **sans** décaissement | G annule | 200, comme R18, sans décaissement à refuser ; aucune erreur sur l'absence de décaissement | serveur |
| R20 | C `approvisionnement`, décaissement `execute` (R1) | G annule | 400 « Cette campagne ne peut plus être annulée. » (ou message dédié, Q3) ; C reste `approvisionnement` ; A1 et A2 toujours `payee` ; aucun remboursement ; séquestre inchangé (libéré 180 000) | serveur |
| R21 | état forcé par le test : C `financee` mais décaissement `execute` (incohérence) | G annule | 400 ; rien d'écrit. Garde de défense sur le décaissement, indépendante du statut de campagne (D-F024, 4e point) | serveur |
| R22 | C `distribution` / `terminee` / `annulee` | G annule | 400 ; rien d'écrit (non-régression) | serveur |
| R23 | un autre groupeur, un acheteur, un anonyme | chacun annule la campagne de G | 404 / 403 ; rien d'écrit | serveur |
| R24 | boutique, `/groupeur/campagnes/<id>`, 390 px, C `financee` | G ouvre la page | « Demander le retrait » visible ; **aucun** bouton « Annoncer l'arrivée » ; bouton d'annulation : voir Q5 | web boutique |
| R25 | idem, C `approvisionnement` | G ouvre la page | le formulaire « Annoncez l'arrivée de la marchandise » est visible ; après envoi, la page passe à « Distribution en cours » ; une erreur serveur (campagne annulée entre-temps) s'affiche lisiblement dans l'alerte en haut de page | web boutique |
| R26 | idem, C `annulee` (par R18) | G ouvre la page | « Campagne annulée » + motif ; aucun bouton de retrait ni de mise à disposition | web boutique |

### Scénarios — Acheteur

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R27 | R18 jouée | A1 ouvre `GET /api/mes-participations/` (ou « Mes achats ») et ses notifications | sa part est `remboursee` ; une notification « Remboursement effectué » (montant exact) et « Groupage annulé » ; **une seule** fois chacune, même après la tentative R2 | serveur + web boutique |
| R28 | R2 jouée | A1 consulte ses notifications | aucune notification de versement ni de mise à disposition ; code de retrait non actif | serveur |
| R29 | C `financee` sans décaissement exécuté, R13 jouée | A1 ouvre sa participation | statut inchangé (`payee`), **pas** « à retirer » ; aucune notification « Votre produit est arrivé » | serveur + web boutique |
| R30 | R15 jouée | A1 ouvre sa participation | `prete`, code de retrait affiché, point de remise visible | serveur + web boutique |

### Scénarios — Système (concurrence, tâches)

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R31 | C `financee`, décaissement `demande` ; deux requêtes administrateur simultanées | `executer` lancé deux fois en parallèle (deux fils, deux connexions) | une seule réussit (200), l'autre 400 « déjà exécuté » ; `montant_libere` = 180 000 exactement ; une seule notification « Fonds versés » ; une seule `reference` | serveur (PostgreSQL) |
| R32 | idem | `executer` et `annuler` lancés en parallèle | exactement l'un des deux issues cohérentes : (a) exécution d'abord : décaissement `execute`, C `approvisionnement`, l'annulation est refusée (400), aucun remboursement ; (b) annulation d'abord : C `annulee`, remboursements, décaissement `refuse`, l'exécution est refusée (400). Jamais les deux : `libere + rembourse ≤ consigné` dans tous les cas | serveur (PostgreSQL) |
| R33 | idem | `executer` et `mise-a-disposition` en parallèle | la mise à disposition ne réussit que si l'exécution a réussi avant ; sinon 400. Aucune participation `prete` avec un séquestre non libéré | serveur (PostgreSQL) |
| R34 | une instance `Decaissement` chargée avant l'annulation (objet périmé, comme dans la vue entre `get_object()` et le service) | l'annulation est faite, puis `executer_decaissement(instance_perimee, admin)` est appelé | `ErreurPaiement` ; aucune écriture. Prouve que le service relit sous verrou et ne croit pas l'objet reçu. **Test déterministe qui tourne aussi sur SQLite** | serveur |
| R35 | `python manage.py charger_demo` sur une base neuve | le jeu se charge | pas d'erreur : ventilateurs en `distribution`, blenders `terminee`, smartphones `financee` avec décaissement `demande` ; les séquestres sont cohérents (`libere + rembourse ≤ consigné`) | serveur |
| R36 | C `minimum_non_atteint` sans décaissement, délai écoulé | la tâche `rembourser_les_indecis` annule | non-régression : annulation et remboursements identiques à avant, sans erreur due à l'absence de décaissement | serveur |

### Tests automatiques attendus

Tous sont à écrire ; les « de régression » doivent **échouer sur `abaa622`** et passer avec le correctif. Collectés par pytest : `paiements/tests.py` correspond au motif `tests.py` ; un fichier transversal `groupachat/tests/test_decaissement_double_paiement.py` correspond à `test_*.py`. Vérifier avec `python -m pytest --collect-only -q <fichier>`.

| Scénario | Fichier :: test | Régression ? |
|---|---|---|
| R1 | `commandes/tests.py::TestDecaissement::test_l_administrateur_libere_les_fonds` (existe : y ajouter la notification « Fonds versés » et le statut `libere`) | non |
| R2 | `tests/test_decaissement_double_paiement.py::test_un_decaissement_en_attente_n_est_pas_execute_apres_l_annulation` : reproduit la T1, vérifie 400, séquestre, statut `annulee`, 0 notification, total sorti = 180 000 | **oui** |
| R3 | `::test_un_decaissement_refuse_ne_peut_pas_etre_execute` | **oui** |
| R4 | `::test_un_decaissement_deja_execute_ne_verse_pas_deux_fois` (`montant_libere` 180 000) | non (la garde existe) |
| R5 | `::test_le_decaissement_est_refuse_quand_le_solde_ne_suffit_pas` | **oui** |
| R6 | `::test_le_decaissement_n_est_execute_que_sur_une_campagne_financee` (paramétré sur 5 statuts) | **oui** |
| R7, R8 | `::test_seul_l_administrateur_execute_un_decaissement` ; `::test_un_decaissement_inconnu_est_introuvable` | non |
| R10 | `::test_l_annulation_refuse_le_decaissement_avec_un_motif` (API admin renvoie `refuse` + `motif_refus`) | **oui** |
| R13, R14 | `::test_on_ne_met_pas_a_disposition_une_campagne_financee` : 400, statut, participations, 0 notification, solde intact | **oui** |
| R15 | `commandes/tests.py::TestDistributionEtRetrait::test_la_mise_a_disposition_notifie_tous_les_participants` (existe) | non |
| R16 | `::test_la_mise_a_disposition_est_refusee_hors_approvisionnement` (paramétré) | partiel |
| R17 | `::test_un_groupeur_ne_met_pas_a_disposition_la_campagne_d_un_autre` | non |
| R18 | `paiements/tests.py::test_l_annulation_d_une_campagne_financee_refuse_le_decaissement_en_attente` | **oui** |
| R19, R36 | `::test_l_annulation_sans_decaissement_reste_possible` ; test de la tâche existant dans `tests/test_cloture.py` à relire | non |
| R20 | `::test_on_n_annule_pas_une_campagne_dont_les_fonds_sont_verses` (séquestre et parts inchangés) | non (le statut la refuse déjà) : verrouille le comportement |
| R21 | `::test_l_annulation_est_refusee_si_un_decaissement_est_execute_meme_si_la_campagne_est_financee` | **oui** |
| R23 | `::test_l_annulation_est_reservee_au_groupeur_de_la_campagne` | non |
| R27 à R30 | `::test_l_acheteur_n_est_prevenu_qu_une_fois_du_remboursement` ; `::test_aucune_notification_de_retrait_sans_fonds_liberes` | R29 : oui |
| R31 | `::test_deux_executions_simultanees_ne_paient_qu_une_fois` : fils, `@pytest.mark.django_db(transaction=True)`, **ignoré si le moteur n'est pas PostgreSQL** (`pytest.mark.skipif` sur `connection.vendor`), motif écrit : SQLite ignore `select_for_update` | **oui** |
| R32, R33 | `::test_l_execution_et_l_annulation_simultanees_ne_paient_pas_deux_fois` ; `::test_l_execution_et_la_mise_a_disposition_simultanees_restent_coherentes` (mêmes conditions) | **oui** |
| R34 | `::test_le_service_relit_le_decaissement_sous_verrou` (objet périmé) | **oui**, tourne partout |
| R35 | `::test_le_jeu_de_demonstration_se_charge_avec_un_sequestre_coherent` (appel de `charger_demo`, `libere + rembourse ≤ consigné`) | non |

Les tests concurrents ne doivent pas être mocks : deux vraies connexions. Si la base de la CI est SQLite, R31 à R33 sont **non vérifiables** et R34 porte la preuve du relire-sous-verrou ; à écrire dans le rapport de recette.

### Vérification d'interface
- **Console admin, `/decaissements`** (390 px et 1280 px) : états chargement (squelettes), vide (« Aucune demande »), erreur (alerte avec le message du serveur, pas un état vide). Un décaissement `demande` d'une campagne `financee` : bouton « Libérer … FCFA » ; un décaissement `refuse` : jamais de bouton, étiquette « Refusé » + motif (R10) ; un `execute` : « Versé » + date.
- **Boutique, `/groupeur/campagnes/<id>`**, 390 px : le bouton « Annoncez l'arrivée » n'apparaît qu'en `approvisionnement` (`decaissee` à retirer de la condition `CampagneGroupeur.tsx` l. 215 en même temps que le statut, C-005) ; en `financee` seule la demande de retrait est proposée ; en `annulee` aucune action. Une erreur 400 d'une action est lue dans l'alerte (`erreurAction`, l. 99-104).
- Types : `Decaissement` dans `commun/src/api/types.ts` porte déjà `statut` et `motif_refus`, à vérifier avant d'afficher le motif ; si un statut ou un champ est ajouté, ce fichier change dans le même passage.
- Pas de changement de route ni de méthode : `POST /api/admin/decaissements/<id>/executer/`, `POST /api/groupeur/campagnes/<id>/{annuler,mise-a-disposition,demander-retrait}/`.

## Fichiers que le correctif touchera probablement
- `backend/groupachat/paiements/services.py` : `executer_decaissement` (relecture sous verrou, gardes), `mettre_a_disposition` (verrou, statut), `annuler` (refus du décaissement, garde sur décaissement exécuté), nouvelle fonction du service pour refuser automatiquement ; si le volume dépasse une centaine de lignes, un module voisin du sujet `paiements`.
- `backend/groupachat/paiements/tests.py` et nouveau `backend/groupachat/tests/test_decaissement_double_paiement.py`.
- `backend/groupachat/commandes/tests.py` (compléments sur les tests existants).
- `backend/groupachat/espaces/administration.py` (vue `executer` : relire / ne pas servir un objet périmé ; réponse inchangée).
- `frontend/admin/src/pages/Decaissements.tsx` (motif du refus), `frontend/boutique/src/pages/groupeur/CampagneGroupeur.tsx` (selon Q5, et condition `decaissee`).
- Si Q4 retient un nouveau genre de notification : `echanges/models.py` + migration `echanges/00NN`, `commun/src/api/types.ts`, et `VERSION_DEMO` non touché (le jeu ne change pas).
- Si Q2 retient une contrainte en base : migration `paiements` (C-006), à revoir par `archi-backend`.
- `CAHIER_DES_CHARGES.md` §6 / §9 (précision sur le refus automatique), par l'archiviste, hors fiche.

La liste qui fait foi est désormais celle du §5 de la conception, ci-dessous.

## Conception (archi-backend, 2026-10-27)

Base : `abaa622`. Aucun nouveau modèle, aucun nouveau genre de notification, aucune nouvelle route. Tout reste dans le sujet `paiements` (séquestre, décaissement, cycle de vie qui écrit). Seules les deux vues existantes s'adaptent.

### 1. La contrainte C-006

**Dans `paiements/models.py`**, `Sequestre.Meta.constraints`, en troisième position. On garde les deux contraintes existantes : la nouvelle les implique, mais les retirer serait un changement de schéma que personne n'a demandé.

```python
models.CheckConstraint(
    condition=models.Q(
        montant_consigne__gte=models.F("montant_libere") + models.F("montant_rembourse"),
    ),
    name="sequestre_ne_sort_pas_plus_que_consigne",
),
```

Le nom suit le format `sequestre_ne_<verbe>_pas_plus_que_consigne`, comme les deux contraintes existantes. Il faut ajouter au-dessus un commentaire qui donne le pourquoi : chacune des deux contraintes isolées laissait passer 475 000 remboursés plus 473 500 versés sur 475 000 consignés (T1).

**Migration** : `backend/groupachat/paiements/migrations/0002_sequestre_ne_sort_pas_plus_que_consigne.py`, une seule opération `AddConstraint`, dépendant de `0001_initial`. Elle se produit avec `python manage.py makemigrations paiements --name sequestre_ne_sort_pas_plus_que_consigne`, puis se relit. Il n'y a ni valeur par défaut ni migration de données : on ne corrige pas automatiquement de l'argent déjà bougé (Q6).

**Effet sur une base remplie.** PostgreSQL vérifie toutes les lignes existantes à l'`ALTER TABLE … ADD CONSTRAINT … CHECK`. SQLite le fait aussi, en recopiant la table. Si une ligne viole la règle, **la migration échoue** avec une `IntegrityError` (`CheckViolation`). Sur PostgreSQL, la migration est transactionnelle, donc le schéma reste intact. Mais `backend/entrypoint.sh` lance `migrate` sous `set -e` : le nouveau conteneur ne démarre pas, et le déploiement échoue.

**Le savoir avant de déployer.** La commande Q6 (§2) arrive dans la même image que la migration, et l'`entrypoint` migre avant toute autre chose. L'ordre « commande d'abord, migration ensuite » est donc **impossible dans un seul déploiement**. Le contrôle se fait sur la production, avec le code actuel, avant de fusionner dans `master` (terminal Coolify du conteneur de l'API) :

```bash
python manage.py shell -c "from django.db.models import F; from groupachat.paiements.models import Sequestre, Decaissement; from groupachat.catalogue.models import Campagne; print('C-006', list(Sequestre.objects.filter(montant_consigne__lt=F('montant_libere')+F('montant_rembourse')).values_list('campagne_id', flat=True))); print('demande hors financee', list(Decaissement.objects.filter(statut='demande').exclude(campagne__statut='financee').values_list('id', 'campagne__statut'))); print('decaissee', Campagne.objects.filter(statut='decaissee').count())"
```

- Si la ligne `C-006` est vide, on peut déployer.
- Si elle ne l'est pas, on s'arrête et l'utilisateur décide (N1).

Par la suite, `controler_les_sequestres` fera ce contrôle. Oui, il faut ajouter un paragraphe à `COOLIFY.md`, « Avant un déploiement qui ajoute une contrainte sur l'argent ». Il donne la ligne ci-dessus pour ce déploiement-ci, puis la commande pour les suivants. C'est le travail de l'archiviste, pas du codeur.

**Chemins qui écrivent `montant_libere` ou `montant_rembourse`** (relevé exhaustif par `grep`, hors migrations) :

| Chemin | Écrit | Respecte C-006 ? |
|---|---|---|
| `encaisser` (`services.py` l. 97-99) | `montant_consigne +=` seulement | oui : le consigné ne fait que croître |
| `rembourser` (l. 177-179), appelé seulement par `annuler` | `montant_rembourse += part` | oui tant qu'aucun versement n'a eu lieu. **Viole** si `annuler` passe sur une campagne dont le décaissement est `execute` (cas R21, état forcé), d'où la garde du §3 |
| `executer_decaissement` (l. 498-504) | `montant_libere += montant_brut` | **Viole** dans le chemin T1 : le brut est figé à la demande, puis l'annulation rembourse, puis l'exécution libère (R2). **Viole aussi** si une part est remboursée après la demande (R5) ou si `executer` et `annuler` se croisent (R32). D'où les gardes et les verrous du §3 |
| `charger_demo.py` (l. 624-662) | seulement par les services, toujours `cloturer → demander → executer → mettre_a_disposition` | oui. Aucune ligne n'est écrite à la main, `VERSION_DEMO` reste inchangé |
| Tests existants (`commandes/tests.py`, `tests/test_cloture.py`, `tests/test_administration.py`) | seulement par l'API ou les services, aucune écriture directe des montants | oui (libéré 180 000 / remboursé 0, ou libéré 0 / remboursé 90 000) |
| `espaces/administration.py` l. 205-208, `espaces/groupeur.py` l. 398 | lecture (agrégats) | sans objet |

Les tests à écrire qui forcent un état doivent le faire **sans violer C-006**, sinon c'est la base qui répond à la place de la garde :
- R5 : un `rembourser(part)` après la demande ;
- R21 : `Decaissement.objects.filter(...).update(statut="execute")` sans toucher au séquestre, ou bien exécution puis `Campagne.objects.filter(...).update(statut="financee")`. Dans ce second cas, c'est la garde de l'annulation qui doit répondre 400 avant toute `IntegrityError` ;
- R6 : décaissement `demande` créé par `Decaissement.objects.create(...)` sur une campagne dans un autre statut.

Le test propre à la contrainte (`paiements/tests.py::test_la_base_refuse_un_sequestre_qui_rend_plus_que_le_consigne`) fait `Sequestre.objects.filter(pk=…).update(montant_libere=…, montant_rembourse=…)` dans un `transaction.atomic()` et attend une `IntegrityError`. Il tourne sur les deux moteurs, car SQLite applique les `CHECK`.

**Limite connue** (sans effet pratique) : sur PostgreSQL, la somme de deux `integer` déborde au-delà de 2 147 483 647 FCFA. L'écriture est alors refusée par une erreur de dépassement plutôt que par la contrainte. Elle est refusée dans les deux cas.

### 2. La commande Q6 : `controler_les_sequestres`

**Emplacement** : `backend/groupachat/paiements/management/commands/controler_les_sequestres.py`. Il faut créer aussi `paiements/management/__init__.py` et `paiements/management/commands/__init__.py`. Elle va dans `paiements`, qui possède le séquestre et le décaissement, et non dans `catalogue` comme `cloturer_les_campagnes_echues`. Le modèle suivi est celui de cette dernière : docstring, `help` et sortie texte en français.

**Comportement** : lecture seule, sans transaction ni option. Idempotente par construction. Elle se lance à la main avant un déploiement ou sur demande, et ne se planifie pas.

**Sortie** : trois rubriques, toujours affichées, chacune avec son compte puis une ligne par anomalie.

```
Séquestres qui rendent plus que le consigné : 1
  campagne 12 · Smartphones Itel… — consigné 475000, libéré 475000, remboursé 475000
Décaissements en attente sur une campagne non financée : 1
  décaissement 7 · campagne 12 (annulee) — brut 475000, net 473500
Campagnes au statut « decaissee » : 0
```

**Code de retour** :
- aucune anomalie : `self.style.SUCCESS("Aucune anomalie.")`, code **0** ;
- au moins une : `raise CommandError(f"{n} anomalie(s) : à trancher par l'administrateur, rien n'a été corrigé.")`, code **1**. Dans un test, `call_command` lève alors `CommandError`, et c'est ce qu'on attend.

**Requêtes** :
1. `Sequestre.objects.filter(montant_consigne__lt=F("montant_libere") + F("montant_rembourse")).select_related("campagne")` ;
2. `Decaissement.objects.filter(statut="demande").exclude(campagne__statut="financee").select_related("campagne")` ;
3. `Campagne.objects.filter(statut="decaissee")`.

Une fois C-006 en base, la rubrique 1 ne peut plus rien trouver. On la garde pour une sauvegarde restaurée sans migration, ou si la contrainte venait à disparaître.

**Tests** (dans `paiements/tests.py`) :
- base saine : code 0 et « Aucune anomalie. » ;
- rubriques 2 et 3, forcées par `.update()` : `CommandError`, et la sortie nomme l'identifiant ;
- rubrique 1 : il faut retirer la contrainte le temps du test (`connection.schema_editor().remove_constraint(...)` dans la transaction du test). Ce test est **ignoré hors PostgreSQL**, parce que l'éditeur de schéma de SQLite refuse de tourner dans un bloc atomique ;
- vérifier qu'aucune ligne n'est modifiée par la commande (comptes et montants identiques avant et après).

### 3. Les services (`paiements/services.py`)

**Ordre unique des verrous : campagne, puis décaissement, puis séquestre.** Toute fonction qui en prend plusieurs les prend dans cet ordre, et chacune prend d'abord celui de la campagne. Deux transactions qui se croisent attendent donc sur la même ligne sans s'interbloquer, et la seconde relit l'état laissé par la première.

On ajoute deux aides privées, à côté de `_verrouiller` (qui reste inchangée) :

```python
def _verrouiller_decaissement(campagne: Campagne) -> Decaissement | None:
    """Le décaissement de la campagne, verrouillé, ou None. Après _verrouiller(campagne)."""
    return Decaissement.objects.select_for_update().filter(campagne=campagne).first()

def _verrouiller_sequestre(campagne: Campagne) -> Sequestre:
    """Le séquestre, créé s'il manque, verrouillé. Après les deux autres verrous."""
    return Sequestre.objects.select_for_update().get_or_create(campagne=campagne)[0]
```

Il ne faut **pas** de `select_related` sur une requête `select_for_update` : PostgreSQL verrouillerait aussi les lignes jointes, hors de l'ordre prévu.

**`executer_decaissement(decaissement: Decaissement, administrateur) -> Decaissement`** : la signature ne change pas, donc `charger_demo` reste intact. Elle reste `@transaction.atomic`. **L'objet reçu ne sert qu'à connaître deux clés** (`campagne_id`, `pk`), et la fonction **rend l'objet relu**. Dans l'ordre :

1. `campagne = Campagne.objects.select_for_update().get(pk=decaissement.campagne_id)` ;
2. `decaissement = Decaissement.objects.select_for_update().get(pk=decaissement.pk)` : c'est **la relecture sous verrou**, qui rend R34 vrai ;
3. `sequestre = _verrouiller_sequestre(campagne)` ;
4. les gardes, dans cet ordre, chacune levant `ErreurPaiement` avec le message validé (Q3) :
   - `statut == EXECUTE` : « Ce décaissement a déjà été exécuté. » (inchangé) ;
   - `statut == REFUSE` : « Ce décaissement a été refusé : la campagne a été annulée. » ;
   - `campagne.statut != FINANCEE` : « Ce décaissement ne peut plus être exécuté : la campagne n'est plus financée. » ;
   - `sequestre.solde < decaissement.montant_brut` : « Le séquestre ne contient pas assez de fonds pour ce versement. » Le décaissement reste `demande` et rien n'est écrit (Q2) ;
5. seulement ensuite `_executer_paiement(...)`. **Les gardes passent avant l'appel à l'opérateur.** Avec un vrai agrégateur, une `IntegrityError` levée après l'appel laisserait de l'argent parti sans écriture comptable. C-006 n'est que le dernier filet ;
6. les écritures actuelles : décaissement `execute`, séquestre `montant_libere += montant_brut` sur l'objet **verrouillé**, campagne `approvisionnement`, notification « Fonds versés ». Elles sont inchangées.

Hypothèse retenue : le statut `approuve`, qu'aucun code ne pose, reste exécutable. La règle de la fiche dit « ni `execute`, ni `refuse` ». L'échec de l'opérateur (l. 484-488) n'est pas touché (Q7).

**`annuler(campagne: Campagne, motif: str = "") -> Campagne`** : la signature ne change pas, et la fonction reste `@transaction.atomic`. Dans l'ordre :

1. `campagne = _verrouiller(campagne)` (existe déjà) ;
2. `decaissement = _verrouiller_decaissement(campagne)` ;
3. **avant** le contrôle du statut, si `decaissement` est `execute`, lever `ErreurPaiement("Les fonds ont déjà été versés au groupeur : cette campagne ne peut plus être annulée.")`. Cela couvre R20 avec le message dédié, et R21 (garde de défense, indépendante du statut) ;
4. le contrôle de statut existant, avec son message inchangé « Cette campagne ne peut plus être annulée. » ;
5. `sequestre = _verrouiller_sequestre(campagne)`, pris **avant** les remboursements. `rembourser` relit le séquestre par `sequestre_de` dans la même transaction et écrit sur une autre instance : il faut donc garder le `refresh_from_db()` avant de poser `rembourse` ;
6. l'annulation de la campagne, puis les notifications et les remboursements existants ;
7. si `decaissement` est `demande` (ou `approuve`), le passer à `refuse` avec `motif_refus = f"Campagne annulée le {timezone.localdate():%d/%m/%Y} : {campagne.motif_annulation}"`. La date est donnée dans le fuseau `Africa/Lome`, et le motif est celui qui est enregistré, avec la valeur par défaut « Groupage non abouti. ». Puis une notification `Notification.Genre.CAMPAGNE_ANNULEE` au groupeur :
   - titre « Demande de retrait annulée » (hypothèse, titre non validé) ;
   - message « Votre demande de retrait de {montant_net} FCFA est annulée avec la campagne. » (proposition de Q4) ;
   - lien `/groupeur/campagnes/<id>`.
   
   Il n'y a rien à faire sans décaissement (R19, R36).

`rembourser_les_indecis` n'est pas modifié : il prend déjà le verrou de la campagne avant `annuler`, ce qui reste dans l'ordre, et une campagne en `minimum_non_atteint` n'a jamais de décaissement.

**`mettre_a_disposition(campagne: Campagne, point_remise: str = "") -> int`** : la signature ne change pas. Dans l'ordre :

1. `campagne = _verrouiller(campagne)`. C'est le seul verrou nécessaire, puisque `approvisionnement` n'est atteint que par `executer_decaissement`, sous le même verrou ;
2. si `campagne.statut == FINANCEE` : « Les fonds n'ont pas encore été versés : la marchandise ne peut pas être mise à disposition. » ;
3. sinon, si `campagne.statut != APPROVISIONNEMENT` : « Cette campagne n'en est pas à la distribution. » (inchangé). `DECAISSEE` et `FINANCEE` sortent de la liste (Q1) ;
4. le reste est inchangé.

**Exception et conversion en 400** : `ErreurPaiement`, qui existe déjà. Les vues la convertissent déjà en `400 {"detail": str(erreur)}`. Pas de nouvelle exception, pas de nouveau format de réponse.

**Les vues** :
- `espaces/administration.py`, `DecaissementAdminVueEnsemble.executer` : `self.get_object()` ne sert plus qu'au 404 et à la permission. La vue écrit `decaissement = executer_decaissement(self.get_object(), requete.user)` et **sérialise l'objet rendu par le service**, pas celui qu'elle a lu. Sans cela, la réponse 200 montrerait l'état d'avant l'exécution, puisque le service n'écrit plus sur l'instance reçue. La permission (`EstAdministrateur`), la route et la forme de la réponse ne changent pas. Il n'y a pas de limitation de débit à ajouter : la route est réservée à l'administrateur, et le double clic est désormais absorbé par le verrou ;
- `espaces/groupeur.py`, `mise_a_disposition` : le service écrit maintenant `point_remise` sur l'instance verrouillée. La vue fait `campagne.refresh_from_db(fields=["point_remise"])` avant de répondre `{"participants_notifies", "point_remise"}`. La réponse est inchangée.

**À valider (N2)** : ajouter `_verrouiller(campagne)` en tête de `demander_decaissement`, soit deux lignes, et relire le statut sur l'objet verrouillé. Sans ce verrou, une demande qui croise une annulation crée un décaissement `demande` sur une campagne `annulee`, que l'annulation n'a pas pu refuser. L'argent est sauf (l'exécution le refuse, la commande Q6 le liste), mais la ligne reste « À libérer » pour toujours. Le double clic donne aussi un 500 sur l'unicité au lieu d'un 400. La fiche classait ce point hors périmètre.

### 4. Les tests de course

**La base réelle des tests.** `pytest.ini` charge `config.settings`. `settings.py` (l. 106-118) choisit PostgreSQL dès que `DATABASE_URL` est renseignée, et SQLite sinon ou si `DJANGO_FORCER_SQLITE=1`. `conftest.py` ne change rien au moteur. Dans les faits :
- **la CI (`.github/workflows/ci.yml`) tourne sur PostgreSQL 17** (service `postgres:17-alpine`, `DATABASE_URL` posée) ;
- **sur ce poste, le moteur résolu est SQLite** (`connection.vendor == "sqlite"`, vérifié le 2026-10-27) ;
- `check.sh` utilise le moteur que donne le `.env`.

La question ne tombe donc qu'à moitié. R31 à R33 tournent en CI et sont ignorés en local. R34 porte la preuve partout.

**R31 à R33**, dans `tests/test_decaissement_double_paiement.py` :
- marqués `@pytest.mark.django_db(transaction=True)` et `@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite ignore select_for_update : la course n'y est pas reproductible")`. `connection.vendor` se lit à la collecte sans ouvrir de connexion ;
- **un verrou tenu par le test plutôt qu'une course au hasard**, pour que le résultat soit déterministe :
  1. le fil principal ouvre `transaction.atomic()` et y joue la première action (par exemple `annuler(campagne)` ou `executer_decaissement(...)`). Les `atomic` imbriqués deviennent des points de sauvegarde, donc les verrous restent tenus jusqu'à la sortie du bloc ;
  2. il lance un `threading.Thread` qui joue la seconde action et range le résultat ou l'exception dans une liste ;
  3. `fil.join(timeout=0.5)` doit trouver le fil **encore vivant**, ce qui prouve qu'il attend le verrou ;
  4. on sort du bloc (validation de la transaction), puis `fil.join(timeout=10)` ;
  5. on vérifie l'issue attendue : 400 « déjà exécuté » ou « refusé », `montant_libere` exact, une seule notification, et `libere + rembourse <= consigne`.
- chaque fil ferme sa connexion (`connection.close()` dans un `finally`) : sinon le nettoyage de la base de test bloque sur une connexion ouverte ;
- R32 se joue dans les deux ordres, ce qui donne deux tests paramétrés : annulation d'abord, puis exécution d'abord ;
- R33 se joue dans un seul ordre : la mise à disposition tient le verrou d'abord et échoue, puis l'exécution passe.

**R34** (tous moteurs) :
1. charger `Decaissement` ;
2. appeler `annuler(campagne)` ;
3. appeler `executer_decaissement(instance_perimee, admin)`. On attend `ErreurPaiement` (« refusé »), un séquestre inchangé et aucune notification « Fonds versés ».

Il faut aussi faire l'inverse : une instance périmée dans l'état `demande`, alors qu'en base le décaissement est déjà `execute`. On attend « déjà exécuté » et `montant_libere` inchangé.

### 5. Ordre de création et fichiers touchés

1. **La contrainte** : `paiements/models.py`, migration `paiements/migrations/0002_sequestre_ne_sort_pas_plus_que_consigne.py`, et `paiements/tests.py` (**nouveau fichier**, collecté par le motif `tests.py`, avec `pytestmark = pytest.mark.django_db`). On vérifie avec `makemigrations --check`.
2. **Les tests de régression d'abord** : `groupachat/tests/test_decaissement_double_paiement.py` (nouveau), compléments dans `paiements/tests.py` et `commandes/tests.py` (R1 : statut `libere` et notification). Sur `abaa622` plus la contrainte, ils doivent échouer, avec des 200, des `IntegrityError` ou des 500. On vérifie la collecte avec `python -m pytest --collect-only -q <fichier>`.
3. **Les services** : `paiements/services.py`, avec les deux aides de verrou, `executer_decaissement`, `annuler`, `mettre_a_disposition`, et `demander_decaissement` si N2 est accepté. Environ 60 lignes en plus : on reste dans le fichier, sans nouveau module.
4. **Les vues** : `espaces/administration.py` (`executer` sérialise l'objet rendu) et `espaces/groupeur.py` (`mise_a_disposition` relit `point_remise`).
5. **La commande** : `paiements/management/__init__.py`, `paiements/management/commands/__init__.py`, `paiements/management/commands/controler_les_sequestres.py`, avec ses tests dans `paiements/tests.py`.
6. **Les interfaces** :
   - `frontend/admin/src/pages/Decaissements.tsx` : afficher `motif_refus` sous l'étiquette « Refusé ». Le champ existe déjà dans `commun/src/api/types.ts` (l. 286), donc les types ne changent pas ;
   - `frontend/boutique/src/pages/groupeur/CampagneGroupeur.tsx` : la l. 215 ne garde que `approvisionnement`.
7. **R35** : test de `charger_demo` sur une base neuve, avec `libere + rembourse <= consigne` pour tous les séquestres. `VERSION_DEMO` reste inchangé.
8. **Hors code**, pour l'archiviste : un paragraphe dans `COOLIFY.md` (contrôle avant déploiement, §1) et dans `CAHIER_DES_CHARGES.md` §6 et §9 (refus automatique à l'annulation).

Ce qui reste intact : les routes (`api.py`), les sérialiseurs, `echanges/`, `catalogue/models.py` (le retrait de `DECAISSEE` reste à C-005), `catalogue/vues.py` (`STATUTS_LISTES` cite encore `DECAISSEE`, ce qui est sans effet ici) et `charger_demo.py`.

### Points à valider (nouveaux)

**N1 — Données de production et déploiement.** Le déploiement échoue si la production contient déjà une trace de T1, c'est-à-dire un séquestre qui rend plus que le consigné. La T1 a été jouée sur un SQLite jetable, mais rien ne dit que personne ne l'a refaite sur `achatgr.com`.
- (a) Lancer la ligne de contrôle du §1 sur la production avant de fusionner dans `master`. Si elle trouve quelque chose, l'utilisateur décide de la correction à la main avant de déployer.
- (b) Déployer en deux temps : la commande seule d'abord, puis la migration.
- (c) Déployer et voir.
- **Recommandation : (a).** C'est une ligne à lancer, sans second déploiement. Une correction de montants reste une décision humaine.

**N2 — Verrou dans `demander_decaissement`** (§3).
- (a) L'ajouter dans T10.
- (b) Le laisser hors périmètre.
- **Recommandation : (a).** Deux lignes, dans le même ordre de verrous. Cela ferme le dernier croisement qui laisse un décaissement `demande` orphelin, et le 500 du double clic.

**N3 — Quatrième rubrique de la commande Q6.** Elle listerait les campagnes en `distribution` ou `terminee` dont le séquestre a un solde positif : les traces de C-014, déjà signalées par F-031 (D1).
- (a) L'ajouter, ce qui fait environ 5 lignes, en lecture seule.
- (b) S'en tenir aux trois rubriques décidées.
- **Recommandation : (a).** C'est la même famille d'anomalie d'argent, et c'est le seul moyen de la voir avant que F-031 tourne. Sinon (b), sans risque.

## Cohérence avec F-031 (lecture seule)
La décision D1 de [[2026-10-27-decisions-f031]] suppose qu'une campagne en `distribution` a normalement un séquestre à solde 0 ; le seul cas à fonds encore consignés est C-014. En fermant C-014 (`financee` ne mène plus à `distribution`), le correctif **supprime la cause** de ce cas : la branche « signaler à l'administrateur » de F-031 deviendra purement défensive pour les données déjà en base. Aucune campagne existante en `distribution` avec solde non nul n'est corrigée par ce correctif (Q6).

## Questions ouvertes

Tranchées le 2026-10-27 : voir « Décisions » en tête de fiche. Le texte ci-dessous est conservé pour l'historique des options.

**Q1 — `mettre_a_disposition` : `decaissee` reste-t-il permis ?**
- (a) Seulement `approvisionnement` ; `decaissee` retiré de la liste. Cohérent avec Q14 (statut supprimé) : aucun code ne l'affecte, aucune donnée ne devrait l'avoir.
- (b) `approvisionnement` et `decaissee`, jusqu'à la migration de C-005.
- **Recommandation : (a)**, à condition de vérifier en base qu'aucune campagne n'est en `decaissee` ; sinon (b) jusqu'à C-005.

**Q2 — Le contrôle du solde au décaissement.** Le brut est figé à la demande ; le séquestre peut ensuite avoir un solde différent (remboursement, état incohérent).
- (a) Refuser si `solde < montant_brut` (400), le décaissement reste `demande` pour que l'administrateur investigue.
- (b) Idem, et passer le décaissement à `refuse` avec motif.
- (c) Verser `min(solde, brut)` en recalculant les frais.
- Et : ajouter ou non la contrainte en base `libere + rembourse ≤ consigné` (C-006, migration).
- **Recommandation : (a)** pour le contrôle (pas de décision automatique sur l'argent sans humain, hors annulation qui est un refus voulu par D-F024) ; **oui** à la contrainte en base : c'est le seul garde-fou qui tient quel que soit le code, mais elle demande l'accord de l'utilisateur et un `archi-backend`.

**Q3 — Les messages en français.** Proposition (à valider ou modifier) :
- exécution sur campagne annulée ou non financée : « Ce décaissement ne peut plus être exécuté : la campagne n'est plus financée. »
- exécution d'un décaissement refusé : « Ce décaissement a été refusé : la campagne a été annulée. »
- solde insuffisant : « Le séquestre ne contient pas assez de fonds pour ce versement. »
- mise à disposition hors `approvisionnement` : « Les fonds n'ont pas encore été versés : la marchandise ne peut pas être mise à disposition. » (en `financee`) ; le message actuel « Cette campagne n'en est pas à la distribution. » pour les autres statuts.
- annulation après versement : « Les fonds ont déjà été versés au groupeur : cette campagne ne peut plus être annulée. »
- **Recommandation :** retenir ces textes ; le dernier remplace « Cette campagne ne peut plus être annulée. » seulement quand un décaissement exécuté existe.

**Q4 — Que devient un décaissement « demandé » quand on annule ; qui est prévenu.**
- (a) Passe `refuse`, `motif_refus = "Campagne annulée le <date> : <motif d'annulation>"`, et le groupeur reçoit une notification dédiée.
- (b) Idem sans nouvelle notification (celles de l'annulation suffisent, le groupeur est l'auteur de l'annulation).
- (c) Supprimé de la base (efface la trace).
- Sous-question : genre de la notification, nouveau `decaissement_refuse` (migration `echanges`, mais lisible et filtrable) ou réutilisation de `campagne_annulee` (aucune migration).
- **Recommandation : (a) avec réutilisation du genre `campagne_annulee`** et un message dédié (« Votre demande de retrait de X FCFA est annulée avec la campagne. ») : rien n'est supprimé (traçabilité de l'argent), pas de migration. Un nouveau genre est à reprendre avec F-042.
  Note : `Decaissement.campagne` est `PROTECT` et `OneToOne` : après refus, **un nouveau décaissement ne peut pas être redemandé** pour la même campagne, ce qui est sans objet puisque la campagne est `annulee`.

**Q5 — Écran : le bouton d'annulation depuis `financee` et l'état du bouton « Demander le retrait ».**
- (a) Ne rien changer à l'écran : `financee` n'a pas de bouton d'annulation (seul l'appel direct à l'API la déclenche, désormais sûr).
- (b) Ajouter « Renoncer et rembourser » en `financee`, masqué dès qu'un décaissement existe (le groupeur ne peut pas le savoir sans champ de plus dans la réponse : contrat d'API à étendre).
- (c) Idem (b), bouton grisé avec explication au lieu d'absent.
- Sous-question : après la demande de retrait, le bouton « Demander le retrait » reste visible (relevé F-017). Le masquer demande aussi un champ (`decaissement` dans le détail de la campagne groupeur).
- **Recommandation : (a)** pour cette tâche : T10 ferme la faille côté serveur, c'est ce qui compte pour l'argent. Q6 « annulation gardée » est déjà honorée par l'API ; l'écran est un chantier à part (à créer au backlog, avec le bouton de retrait qui reste affiché), pour ne pas étendre le contrat d'API dans un correctif de sécurité.

**Q6 — Données déjà en base.** Des campagnes peuvent déjà être en `distribution` avec un solde non nul (C-014 passée), ou `annulee` avec un décaissement `demande` encore en attente (la panne T1).
- (a) Aucune migration de données ; le contrôle d'exécution (R2) protège les décaissements `demande` d'une campagne annulée, et le cas `distribution` est signalé par F-031 (D1).
- (b) Une commande de gestion ponctuelle qui liste, sans corriger, les séquestres incohérents et les décaissements `demande` d'une campagne non `financee`.
- **Recommandation : (b)** en lecture seule (liste des anomalies à décider par l'administrateur), car corriger de l'argent déjà bougé ne se fait pas automatiquement ; on le propose à l'utilisateur pour la production. Si aucune donnée réelle, (a).

**Q7 — Échec opérateur : l'écriture `refuse` est annulée.** L. 485-492 enregistre `refuse` puis lève l'erreur dans la même transaction : le refus n'est jamais conservé. Hors périmètre (passerelle simulée, F-043).
- (a) Laisser, noter au backlog.
- (b) Corriger dans T10 en sortant l'écriture de la transaction.
- **Recommandation : (a)** : le simulateur répond toujours `True`, aucun scénario ne l'atteint ; le sujet est celui de F-043 avant tout vrai opérateur.

## Verdict de recette
**RECETTE OK** le 2026-10-27, après une première passe KO (web admin, R11 et R12, corrigés dans `frontend/admin/src/pages/Decaissements.tsx`). Matrice : serveur OK · web admin OK · web boutique OK · mobile — (pas d'application mobile dans ce dépôt).

## Recette — 2026-10-27

**RECETTE KO** (deux défauts d'interface sans effet sur l'argent ; le serveur est intègre). Commit de base `abaa622`, code dans l'arbre de travail non commité. Matrice : **serveur ✅ · web admin ❌ (R11, R12) · web boutique ✅ · mobile —** (pas d'application dans ce dépôt).

Environnement : base SQLite jetable du scratchpad (réglage `reglages_recette` hors dépôt, `charger_demo` chargé), `runserver` :8010, Vite boutique :5173 et admin :5174 relayant vers :8010, Chrome headless 390 px, requêtes HTTP réelles avec session et jeton CSRF. Ni `.env`, ni base du dépôt, ni le port 8000 (occupé par un processus qui n'est pas le mien) n'ont été touchés. Tout ce que j'ai lancé est arrêté.

### Serveur (requêtes réelles, état relu en base après chaque étape)

| # | Verdict | Preuve |
|---|---|---|
| R1 | ✅ | exécution : 200, `execute`, `reference` `SIM-…`, séquestre libéré 0 → 180 000, rembourse 0, statut `libere`, solde 0 ; campagne `approvisionnement` ; 1 notification « Fonds versés » (178 500 FCFA, lien `/groupeur/campagnes/<id>`) |
| R2 | ✅ | reproduction T1 : l'annulation rembourse 180 000 (2 transactions) ; l'exécution rend **400** « Ce décaissement a été refusé : la campagne a été annulée. » ; séquestre inchangé (libéré 0, remboursé 180 000) ; campagne `annulee` ; 0 « Fonds versés » ; **total sorti 180 000** (au lieu de 358 500) |
| R3 | ✅ | seconde exécution du refusé : 400, état inchangé |
| R4 | ✅ | 400 « Ce décaissement a déjà été exécuté. » ; libéré reste 180 000 ; 1 seule notification ; `reference` inchangée |
| R7 | ✅ | acheteur 403, groupeur 403, anonyme 403 (« Informations d'authentification non fournies »), rien d'écrit |
| R8 | ✅ | id inconnu : 404 |
| R10 | ✅ | `GET /api/admin/decaissements/` : `statut` « refuse », `motif_refus` « Campagne annulée le 27/10/2026 : Fournisseur défaillant » |
| R13 | ✅ | `financee` : 400 « Les fonds n'ont pas encore été versés : la marchandise ne peut pas être mise à disposition. » ; campagne, parts (`payee`), séquestre (solde 180 000) inchangés ; 0 « Votre produit est arrivé » |
| R15 | ✅ | 200 `{"participants_notifies": 2, …}` ; `distribution` ; parts `prete` ; 2 notifications « Votre produit est arrivé » avec code ; séquestre inchangé |
| R16 | ✅ | `distribution` : 400 « Cette campagne n'en est pas à la distribution. » ; `annulee` : idem |
| R17 | ✅ | autre groupeur : 404, rien d'écrit |
| R18 | ✅ | 200 ; `annulee` ; parts `remboursee` ; séquestre `rembourse` 180 000, libéré 0, solde 0 ; décaissement `refuse` avec motif ; notification au groupeur, genre `campagne_annulee`, « Demande de retrait annulée — Votre demande de retrait de 178500 FCFA est annulée avec la campagne. », lien `/groupeur/campagnes/<id>` |
| R19 | ✅ | sans décaissement : 200, remboursements faits, aucune erreur |
| R20 | ✅ | après versement : 400 « Les fonds ont déjà été versés au groupeur : cette campagne ne peut plus être annulée. » ; `approvisionnement`, parts `payee`, libéré 180 000 inchangé |
| R22 | ✅ | `distribution` : 400 (message « fonds déjà versés », car le décaissement est exécuté, conforme à Q3) ; `annulee` : 400 « Cette campagne ne peut plus être annulée. » |
| R23 | ✅ | acheteur 403, autre groupeur 404, anonyme 403 |
| R27, R28 | ✅ | A1 : « Remboursement effectué » (108 000) et « Groupage annulé », une fois chacune ; aucune notification de versement ni de mise à disposition après la tentative R2 |
| R35 | ✅ | `charger_demo` sur base neuve : sans erreur ; `controler_les_sequestres` : « Aucune anomalie. », **code 0** |
| Commande, base saine | ✅ | 4 rubriques à 0, code 0 |
| Commande, anomalies | ✅ | injectées sans violer la contrainte (décaissement `demande` sur campagne `approvisionnement`, campagne `decaissee`, campagne `distribution` à solde 180 000) : les rubriques nomment décaissement 6 / campagnes 17 et 18, `CommandError` « 3 anomalie(s) : à trancher par l'administrateur, rien n'a été corrigé. », **code 1** ; empreinte md5 de la base identique avant et après (lecture seule) |
| R31 à R33 | citées | prouvées sur PostgreSQL 17 par `reviewer-tester` (53 passed, 0 skipped) ; non rejouées |
| R5, R6, R14, R21, R34, R36 | tests seuls | non rejoués à la main : états forcés ; couverts par `paiements/tests.py` et `tests/test_decaissement_double_paiement.py` (ma relance sur SQLite : 48 passed, 5 skipped ; les 5 ignorés sont les courses R31 à R33 et le test de la rubrique 1, propres à PostgreSQL) |
| Rubrique 1 de la commande | non rejouée | la contrainte l'interdit sur cette base ; testée sur PostgreSQL par le reviewer |

### Web admin, `/decaissements`, 390 px

| # | Verdict | Observé |
|---|---|---|
| R9 | ✅ | clic « Libérer 178 500 FCFA » : bouton désactivé pendant l'appel, puis la ligne passe en « Historique », « Versé », « versé le 27 octobre 2026 à 20:40 » |
| R10 | ✅ | la ligne refusée est en « Historique » : « Refusé » et « Campagne annulée le 27/10/2026 : Fournisseur défaillant », aucun bouton |
| R11 | ❌ partiel | le message du serveur s'affiche bien dans l'alerte (« Ce décaissement a été refusé : la campagne a été annulée. »), mais **la liste ne se recharge pas** : la ligne périmée reste dans « À libérer » avec son bouton, qui redonnera la même erreur. Attendu : la ligne passe en « Historique ». Cause : `Decaissements.tsx` l. 28-36, `await recharger()` est après `api.post` : sur erreur, `finally` s'exécute sans rechargement |
| R12 | ❌ partiel | chargement ✅ (squelettes), vide ✅ (« Aucune demande »). **Erreur ❌** : une réponse 500 sur la liste affiche « Aucune demande », l'état vide ; `useRequete` renvoie `erreur`, que la page ne lit pas (`Decaissements.tsx` l. 24-26 : seuls `donnees`, `chargement`, `recharger` sont lus). Défaut antérieur à T10, non touché par le diff |

### Web boutique, `/groupeur/campagnes/<id>`, 390 px

| # | Verdict | Observé |
|---|---|---|
| R24 | ✅ | `financee` : « Demander le retrait » ; aucun formulaire « Annoncez l'arrivée » ; pas de bouton d'annulation (Q5) |
| R25 | ✅ | `approvisionnement` : formulaire + « Prévenir les participants » ; après envoi, statut « Distribution », « 0 / 2 colis remis ». Erreur (campagne passée en distribution entre-temps) : alerte lisible « Cette campagne n'en est pas à la distribution. » |
| R26 | ✅ | `annulee` : « Campagne annulée — Fournisseur défaillant » ; ni retrait ni mise à disposition |
| R29, R30 | non rejoués à l'écran | côté acheteur, hors des écrans demandés ; l'état serveur (parts `payee` sans notification en R13, `prete` + code en R15) est prouvé ci-dessus |

Captures (scratchpad `f024/`) : `admin-r10-liste.png`, `admin-r11-alerte.png`, `admin-r9-pendant.png`, `admin-r9-apres.png`, `admin-r12-{chargement,vide,erreur}.png`, `boutique-{financee,approvisionnement,annulee}.png`, `boutique-r25-{formulaire,apres,erreur}.png`.

### À corriger pour lever le KO
1. R11 : recharger la liste aussi quand `executer` échoue (`finally` : `await recharger()`), pour que la ligne périmée passe en « Historique ».
2. R12 : afficher l'erreur de chargement de la liste (`erreur` de `useRequete`) dans l'`Alerte` et ne pas la confondre avec l'état vide.

### Remarques hors périmètre (pas des KO)
- Boutique, campagne `annulee` : la tête affiche « 0 participants, 0 FCFA collecté » alors que « Qui a payé (2) » liste les 2 acheteurs remboursés avec leurs montants. À reprendre avec l'écran d'annulation (chantier Q5).
- Boutique : après une erreur de mise à disposition, la page garde son statut `approvisionnement` jusqu'au rechargement.
- Admin à 390 px : en « Historique », le titre de la campagne passe sur une colonne très étroite (cosmétique).

### Reprise R11/R12 — 2026-10-27

**RECETTE OK** pour l'ensemble de F-024. Matrice : **serveur ✅ · web admin ✅ · web boutique ✅ · mobile —**. Base de départ `abaa622`, correctif de `frontend/admin/src/pages/Decaissements.tsx` dans l'arbre de travail (non commité). Serveur inchangé depuis la recette précédente.

Environnement : base SQLite jetable du scratchpad (`f024b/`), `runserver` :8021, Vite admin :5184 et boutique :5183 relayant vers :8021, Chrome headless 390 px, `DJANGO_ORIGINES_SURES` posé dans l'environnement du processus (ports non standards, sans toucher à `.env`). Tout est arrêté ; `ss` ne montre plus 8021, 5183 ni 5184.

| # | Verdict | Observé |
|---|---|---|
| R11 | ✅ | Ligne « À libérer » ouverte, le groupeur annule la campagne par l'API (200), l'administrateur clique « Libérer » : l'alerte « Ce décaissement a été refusé : la campagne a été annulée. » reste affichée, la liste est rechargée, la ligne est en « Historique » avec « Refusé » et « Campagne annulée le 27/10/2026 : Fournisseur défaillant », 0 bouton sur la ligne. Serveur : 400 sur `executer`. |
| R12 | ✅ | Réponse 500 sur la liste : alerte « Erreur serveur simulée », pas de « Aucune demande ». Liste réellement vide (200, `results: []`) : « Aucune demande » affiché. Chargement (réponse retardée) : 2 squelettes. Le 500 est simulé par interception navigateur (`route.fulfill`), comme dans la recette précédente. |
| R9 | ✅ | Bouton désactivé pendant l'appel ; ensuite la ligne passe en « Versé » (« versé le 27 octobre 2026 à 22:17 »). Serveur : 200. |
| R10 | ✅ | Ligne refusée en « Historique » : « Refusé » et motif « Campagne annulée le … : Fournisseur défaillant », sans bouton. |

Captures (scratchpad `f024b/`) : `admin-r11-alerte.png`, `admin-r12-chargement.png`, `admin-r12-vide.png`, `admin-r12-erreur.png`, `admin-r9-pendant.png`, `admin-r9-apres.png`, `admin-r10-liste.png`.

Remarques (pas des KO) : à 390 px, titre et motif passent sur une colonne étroite dans l'historique (cosmétique, déjà signalé) ; l'alerte d'erreur de chargement n'a pas de cadre coloré visible sur `admin-r12-erreur.png`, seul le texte s'affiche.
