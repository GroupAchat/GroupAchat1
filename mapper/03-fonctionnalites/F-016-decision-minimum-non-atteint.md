# F-016 — Le groupeur clôture, maintient ou renonce (minimum non atteint)

Statut : **terminée** (2026-10-27). T2 de [[M-001-terminer-le-mvp]]. Commitée `f8b78f9` (« Rend au groupeur les boutons maintenir et renoncer »), fusionnée dans `staging` (branche `fix/F-016-decision-minimum-non-atteint`). Décisions : [[2026-10-27-decisions-f016]]. Rôle : Groupeur. Source : `CAHIER_DES_CHARGES.md` §4 (minimum non atteint, délai de décision) et §9 (cycle de vie) ; [[carte]] ; décisions Q6 et Q7 de [[2026-10-26-decisions-carte]].
Hors périmètre : C-009 (textes de la promesse, T6), F-034 (clôture forcée par l'administrateur), F-024/C-006 (décaissement et plafond du séquestre, T10).

## Le défaut
`frontend/boutique/src/pages/groupeur/CampagneGroupeur.tsx` l. 70 (`maintenir`) et l. 74 (`annuler`) appellent `/api/groupeur/campagnes/${id}/…`. Le client `frontend/commun/src/api/client.ts` (l. 13) préfixe déjà `/api` : la requête part vers `/api/api/groupeur/…` et répond 404, affiché « Connexion impossible » (le crochet `useAction` convertit toute erreur non `ErreurApi` ainsi, mais une 404 HTML y arrive aussi). Les autres appels de la page (`publier`, `cloturer`, `mise-a-disposition`, l. 60 et 66, 77) sont corrects.
Recherche faite : `grep "'/api\|\"/api\|\`/api" frontend/*/src` ne trouve que ces **deux** lignes ; aucun autre appel `api.*` n'a le défaut (le commentaire du client l. 12 le documente).
Le serveur est prêt : `espaces/groupeur.py` actions `cloturer` (l. 149), `maintenir` (l. 156), `annuler` (l. 172) ; services `paiements/services.py` `cloturer`, `maintenir`, `annuler`, `rembourser_les_indecis` ; tests `groupachat/tests/test_cloture.py`.

## Résultat observable
Quand la campagne est `minimum_non_atteint`, le groupeur propriétaire voit « Je maintiens » et « Renoncer et rembourser » et chacun fonctionne : la campagne devient `financee` (suite normale) ou `annulee` (chaque part payée `remboursee`, séquestre soldé), les acheteurs sont notifiés, l'écran se met à jour. Sans décision après `DELAI_DECISION_JOURS` (7), la tâche rembourse tout le monde (F-028).

## Recette
Rôle : groupeur propriétaire (décide) ; acheteur, autre groupeur, anonyme (refusés) ; système (7 jours) · Couches : serveur oui (déjà couvert, quelques trous) · web oui (le défaut est ici) · mobile non · Source : §4, §9.

Préparation commune : groupeur G (KYC validé, `GroupeurValide`), campagne C de minimum 5 pièces, acheteurs Ama (3 pièces) et Yao (1 pièce) ayant payé : 4 pièces sur un minimum de 5 ; date limite reculée, `cloturer_les_echus()` joué : C est `minimum_non_atteint`, séquestre bloqué. Autre groupeur G2, acheteur Ama, anonyme. Montants en FCFA entiers ; en local avec `charger_demo` ou les fixtures `test_cloture.py`.

### Scénarios
| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | C `minimum_non_atteint`, G propriétaire | `POST /api/groupeur/campagnes/<id>/maintenir/` | 200 ; corps = campagne avec `statut: "financee"` ; base : `Campagne.statut == financee` ; participations d'Ama et Yao restent `payee` ; séquestre inchangé (aucun remboursement, solde = total consigné) ; une notification `campagne_maintenue` par participant payé (lien `/campagnes/<id>`) | serveur |
| R2 | R1 faite | G demande ensuite `POST …/demander-retrait/` | 201, frais = 1 500, net = brut − 1 500 (le cours normal reprend) | serveur |
| R3 | C `minimum_non_atteint`, G | `POST …/annuler/` avec `{"motif": "Fournisseur indisponible"}` | 200 ; `statut: "annulee"`, `motif_annulation` = ce motif ; chaque participation `remboursee` ; une `Transaction` sens remboursement par participant, montant = `montant_total` ; séquestre `solde == 0`, `montant_rembourse == montant_consigne`, statut `rembourse` ; notifications « Groupage annulé » puis « Remboursement effectué » à chaque acheteur ; `Reputation.campagnes_annulees` +1 | serveur |
| R4 | idem, sans motif (ce que l'écran envoie aujourd'hui : `""`) | `POST …/annuler/` avec `{}` ou `{"motif": ""}` | 200 ; `motif_annulation == "Groupage non abouti."` | serveur |
| R5 | C `en_cours`, minimum atteint, G | `POST …/cloturer/` | 200 `{"statut": "financee"}` ; notifications « Campagne financée » aux acheteurs et à G ; (décision Q7 : clôture anticipée gardée) | serveur |
| R6 | C `en_cours`, minimum non atteint, G | `POST …/cloturer/` | 200 `{"statut": "minimum_non_atteint"}` ; acheteurs prévenus (« Le groupage n'a pas abouti »), G reçoit « Décision attendue » ; **aucun remboursement** ; séquestre `montant_rembourse == 0` | serveur |
| R7 | C `minimum_non_atteint` depuis moins de 7 jours | `rembourser_les_indecis()` | liste vide ; statut inchangé | serveur |
| R8 | C `minimum_non_atteint`, `cloturee_le` il y a 8 jours, sans décision | `rembourser_les_indecis()` (ou `manage.py cloturer_les_campagnes_echues`) | C `annulee`, motif « Sans décision du groupeur 7 jours après la clôture. », toutes les parts `remboursee`, séquestre soldé | serveur |
| R9 | `DELAI_DECISION_JOURS = 0` | même tâche, campagne ancienne | rien ne bouge | serveur |
| R10 | G2 (autre groupeur valide) | `maintenir` puis `annuler` sur C | 404 (la requête est filtrée par propriétaire, `get_queryset`), **rien écrit** : statut, participations, séquestre, notifications inchangés. Note : le test existant n'essaie que l'acheteur (403) | serveur |
| R11 | Ama (acheteuse) | `maintenir` puis `annuler` sur C | 403, rien écrit | serveur |
| R12 | anonyme | `maintenir` puis `annuler` puis `cloturer` | 403 (ou 401), rien écrit | serveur |
| R13 | C `en_cours` ou `financee` ou `annulee` | `maintenir` | 400 « Cette campagne n'attend pas de décision. » ; rien écrit | serveur |
| R14 | C déjà `annulee` (ou déjà `maintenue`, donc `financee` sans décaissement) | `annuler` deux fois de suite (double clic séquentiel) | 1re : 200 ; 2e : 400 « Cette campagne ne peut plus être annulée. » ; un seul remboursement par participant (nombre de `Transaction` remboursement inchangé après la 2e), `campagnes_annulees` = 1 et non 2, `montant_rembourse` = total, pas le double | serveur |
| R15 | C `minimum_non_atteint` | `maintenir` puis `annuler` (G change d'avis après maintien) | `annuler` sur `financee` est accepté par le service (Q6 : gardé) : à vérifier que ce n'est pas une porte ouverte sur le double paiement (voir questions ouvertes 1) | serveur |
| R16 | C `minimum_non_atteint` depuis plus de 7 jours mais la tâche n'a pas encore tourné | G appelle `maintenir` | comportement à décider (question ouverte 2) ; en attendant le scénario consigne le comportement observé | serveur |
| R17 | deux requêtes simultanées `maintenir` et `annuler` sur C | lancées en parallèle (deux threads / `curl &`) | exactement une réussit ; état final cohérent : soit `financee` sans remboursement, soit `annulee` avec remboursements ; jamais `financee` avec parts remboursées. Aucun `select_for_update` dans `maintenir`/`annuler` aujourd'hui : à constater (voir question ouverte 3) | serveur |
| R18 | G connecté, boutique, C `minimum_non_atteint`, 390 px | ouvre `/groupeur/campagnes/<id>` | la carte « Le minimum n'a pas été atteint — à vous de décider » montre « Je maintiens » et « Renoncer et rembourser », pièces et minimum corrects (`quantite_reservee`/`quantite_minimale`) ; boutons pleine largeur et utilisables au pouce | web |
| R19 | idem | clique « Je maintiens » | requête réseau `POST /api/groupeur/campagnes/<id>/maintenir/` (**et non `/api/api/…`**) → 200 ; la page se recharge : étiquette « Financée », carte « Retirez vos fonds » avec « Demander le retrait » ; plus de boutons de décision ; pas de message d'erreur | web |
| R20 | idem | clique « Renoncer et rembourser » | `POST /api/groupeur/campagnes/<id>/annuler/` → 200 ; page : étiquette « Annulée », carte « Campagne annulée » avec le motif « Groupage non abouti. » ; la fiche acheteur montre ses parts remboursées | web |
| R21 | idem | double clic rapide sur « Renoncer et rembourser » | un seul appel part, ou le 2e est refusé proprement ; le bouton est inactif pendant l'envoi (`chargement`) ; aucune erreur affichée à l'utilisateur au final ; un seul remboursement par acheteur | web |
| R22 | idem, serveur répond 400 (campagne déjà tranchée dans un autre onglet) | clique « Je maintiens » | l'`Alerte` affiche « Cette campagne n'attend pas de décision. » en français, lisible ; la page ne reste pas figée sur « chargement » | web |
| R23 | idem, réseau coupé | clique | message « Connexion impossible. Vérifiez votre réseau. » (le seul cas où ce texte est légitime) | web |
| R24 | acheteur Ama connecté, boutique | ouvre `/groupeur/campagnes/<id>` | pas de bouton de décision proposé (la route renvoie 403 ; la page ne doit pas offrir un bouton qui échoue) ; redirigée ou « Campagne introuvable » | web |
| R25 | C `en_cours` / `financee` / `annulee` | ouvre la page groupeur | les boutons « Je maintiens » et « Renoncer » **n'apparaissent pas** (seulement dans l'état `minimum_non_atteint`) | web |
| R26 | acheteur Ama, notifications | ouvre la notification « Le groupage est maintenu » / « Groupage annulé » | le lien `/campagnes/<id>` mène à la fiche, qui reflète le nouvel état (bandeau annulée ; pas de bandeau « minimum non atteint » pour une campagne maintenue) | web |
| R27 | G, notifications | après la clôture, ouvre « Décision attendue » | le lien `/groupeur/campagnes/<id>` mène à la page de décision (R18) | web |

### Tests automatiques attendus
Serveur : `backend/groupachat/tests/test_cloture.py` (déjà collecté ; classes `TestDecisionDuGroupeur`, `TestDelaiDeDecision`, `TestArgentNonRendu`). Existants qui couvrent : R1 `test_il_peut_maintenir_malgre_le_nombre`, R2 `test_une_campagne_maintenue_suit_le_cours_normal`, R3 `test_il_peut_annuler_et_tout_le_monde_est_rembourse` (vérifie statut, parts, solde ; **pas** le motif, ni les notifications, ni `montant_rembourse`), R6 `test_la_cloture_ne_rembourse_personne` et `test_les_participants_savent_que_ca_n_a_pas_abouti`, `test_le_groupeur_est_invite_a_trancher`, R7–R9 `TestDelaiDeDecision`, R11 `test_un_autre_groupeur_ne_decide_pas_a_sa_place` (en fait un **acheteur**).
À **ajouter** dans `TestDecisionDuGroupeur` :
- `test_le_motif_par_defaut_est_enregistre` (R4) et `test_le_motif_saisi_est_enregistre` (R3).
- `test_l_annulation_notifie_et_rembourse_chaque_acheteur` (R3 : notifications `campagne_annulee` et `remboursement`, une `Transaction` remboursement par part, `montant_rembourse` égal au total).
- `test_un_autre_groupeur_ne_voit_pas_la_campagne_et_rien_n_est_ecrit` (R10, avec G2 ; vérifier statut, participations, sequestre).
- `test_un_acheteur_et_un_anonyme_ne_decident_pas_et_rien_n_est_ecrit` (R11, R12, avec contrôle de l'état après le refus).
- `test_maintenir_hors_decision_est_refuse` (R13, paramétré sur `en_cours`, `financee`, `annulee`).
- `test_annuler_deux_fois_ne_rembourse_qu_une_fois` (R14).
- `test_la_cloture_anticipee_sans_minimum_attend_la_decision` (R6 via la route `cloturer`, non couvert) et `test_la_cloture_anticipee_avec_minimum_finance` (R5).
- `test_maintenir_apres_le_delai_...` (R16) selon la décision de la question 2 ; `test_annuler_apres_maintien_...` (R15) selon la question 1.
- Pour R17 : un test de concurrence est fragile en SQLite ; si la base de test est PostgreSQL, le jouer en `transaction=True`, sinon le consigner en constat manuel.
Web : le dépôt n'a **aucun outil de test front** (pas de vitest ni playwright dans `frontend/package.json` ; seul `npm run verifier` = `tsc -b boutique admin`). Le typage ne détecte pas ce défaut : le chemin est une chaîne. Garde-fou le moins coûteux, à décider (question 4) : un test serveur ou un script de recette qui lit tous les `api.*(` du front et refuse tout chemin commençant par `/api/` (`grep -rnE "api\.(get|post|put|patch|delete)\(\s*[\`'\"]/api" frontend/*/src` doit être vide). Sans cela, R18–R27 restent des constats manuels (curl pour R19–R20 avec une session, ou navigateur à 390 px : `npx playwright screenshot --viewport-size=390,844`).

### Vérification d'interface
- Écran : `/groupeur/campagnes/<id>` (`CampagneGroupeur.tsx`), carte « Prochaine étape », état `minimum_non_atteint`. Champs lus : `statut`, `quantite_reservee`, `quantite_minimale`, `minimum_atteint`, `montant_collecte`, `motif_annulation`, `nombre_participants` : à comparer au JSON réel de `GET /api/groupeur/campagnes/<id>/` à la recette.
- Chargement : squelettes pendant `useRequete` ; bouton en `chargement` pendant l'envoi. Erreur : `Alerte` (agrège les erreurs des actions) avec message du serveur. Vide : campagne introuvable → « Campagne introuvable. ». À vérifier : un rechargement qui échoue après une décision réussie n'affiche pas une fausse erreur.
- Contrôle de contrat : routes `…/maintenir/`, `…/annuler/` (POST, corps `{motif}` pour `annuler`), `…/cloturer/` existent côté serveur ; les chemins du front doivent être sans préfixe `/api`.

## Constats à consigner (hors correctif demandé)
- Le texte de l'étape `en_cours` (l. 123 environ) dit « Au-delà de la date limite, la campagne est annulée et tout le monde est remboursé » : faux par rapport au §4 (le groupeur tranche). C'est le sujet C-009 / T6, mais il est dans le même fichier.
- Le bouton « Renoncer et rembourser » n'a aucune confirmation ni champ de motif : un clic mal placé rembourse tout le monde, sans retour possible (voir question 5).
- Le texte « Sans réponse, ils seront remboursés automatiquement » ne donne pas la date butoir.
- `annuler` et `maintenir` n'utilisent pas `select_for_update` sur la campagne (la règle du dépôt le demande « quand deux requêtes peuvent se croiser »).

## Questions ouvertes
1. **Annuler après maintien (R15).** `annuler` accepte `financee`. Un groupeur peut donc maintenir, puis annuler et rembourser. Acceptable avant retrait ? Après `demander-retrait` (décaissement en attente), D-F024 (T10) prévoit le refus automatique du décaissement : on suppose que R15 est autorisé jusqu'au décaissement et que T10 le borne. **Décision de l'utilisateur** : confirmer, ou interdire d'annuler après un maintien. → **Décision du 2026-10-27 (D1)** : renoncer après « Je maintiens » est permis jusqu'au décaissement ; la borne viendra de T10 (D-F024).
2. **Maintenir après le délai de 7 jours (R16).** Entre le 7e jour et le passage de la tâche (horaire, planification non vérifiable : C-007), `maintenir` réussit encore. Doit-il être refusé dès le 7e jour, ou le groupeur garde-t-il la main tant que la tâche n'a pas tourné ? Le §4 dit « passé ce délai sans réponse, chaque participant est remboursé ». **Décision de l'utilisateur.** → **Décision du 2026-10-27 (D2)** : `maintenir` est refusé dès le 7e jour après `cloturee_le`, même échéance que `rembourser_les_indecis`. Choix de l'implémenteur, accepté par le chef de projet. `annuler` reste permis après 7 jours.
3. **Verrou (R17).** Faut-il ajouter `select_for_update` dans `maintenir`/`annuler` (et dans la tâche) ? Recommandation : oui, c'est de l'argent ; correction côté `fonctionnalite`, et `regles-auditor` ensuite. → **Traité par le correctif** : `maintenir`, `annuler` et `rembourser_les_indecis` passent par `_verrouiller` (`select_for_update`). Verrou dans `cloturer` : C-029. Sous PostgreSQL : C-031.
4. **Garde-fou front.** Ajouter un test automatique du préfixe `/api` (script grep ou test serveur lisant le source) ? Ou installer vitest/playwright (nouvelle dépendance, décision écrite dans `mapper/02-decisions/` requise) ? Recommandation : le script grep dans `check.sh`. → **Décision du 2026-10-27 (D3)** : contrôle `prefixe_api` dans `check.sh`, aucune nouvelle dépendance.
5. **Confirmation avant « Renoncer et rembourser ».** Le périmètre de F-016 inclut-il une confirmation (et un motif facultatif), ou on corrige seulement les deux chemins ? Le serveur accepte déjà `motif`. Recommandation : corriger les chemins seulement (périmètre minimal), la confirmation en suivi. → **Décision du 2026-10-27 (D4)** : F-016 se limite aux deux chemins ; confirmation et motif en suivi (C-026).
6. **Message du délai.** Afficher la date butoir (`cloturee_le` + 7 jours) au groupeur ? Le champ n'est peut-être pas dans la réponse de la campagne ; à vérifier. Suivi, pas bloquant. → Suivi C-027, hors F-016.
7. **Notification au groupeur après sa décision** : aucune n'est créée aujourd'hui (seuls les acheteurs sont prévenus). Voulu ? Non bloquant. → Suivi C-028, hors F-016.

## Recette (2026-10-27, commit de base 474656a, correctif non commité à la date de la recette ; commité ensuite en `f8b78f9`)
**RECETTE OK** · serveur ✅ · web ✅ · mobile —

Environnement : `runserver` sur 8123, base sqlite et médias dans le scratchpad (module `reglages_f016`), boutique Vite sur 5199 relayée vers 8123, sessions réelles (cookie `sessionid` + jeton CSRF), Chrome headless 390 px (playwright-core). Jeu fictif : campagnes de 10 pièces minimum, Ama 3 pièces et Yao 2 (90 000 FCFA consignés).

| Scénario | Commande / action | Statut | Effet observé |
|---|---|---|---|
| R1 | G `POST maintenir` | 200 | `financee` ; parts `payee` ; séquestre 90 000 / 0 remboursé ; 2 notifs `campagne_maintenue` (lien `/campagnes/<id>`) |
| R2 | G `POST demander-retrait` après R1 | 201 | frais 1 500, net 88 500 |
| R3 | G `POST annuler {motif}` | 200 | `annulee`, motif saisi ; parts `remboursee` ; transactions 54 000 et 36 000 ; séquestre solde 0, remboursé 90 000, `rembourse` ; notifs `campagne_annulee` + `remboursement` par acheteur ; `campagnes_annulees` +1 |
| R4 | `annuler {"motif":""}` | 200 | motif « Groupage non abouti. » |
| R5 | G `cloturer` (minimum atteint) | 200 | `financee` ; notifs `campagne_financee` |
| R6 | G `cloturer` (minimum non atteint) | 200 | `minimum_non_atteint` ; aucun remboursement ; `groupage_non_abouti` x2, `decision_attendue` x1 |
| R7 | `cloturer_les_campagnes_echues` avant 7 j | — | « 0 clôture(s), 0 remboursement(s) », statut inchangé |
| R8 | idem, `cloturee_le` il y a 8 j | — | 2 campagnes `annulee`, motif « Sans décision du groupeur 7 jours après la clôture. », séquestre soldé |
| R10 | G2 `maintenir` / `annuler` | 404 | rien écrit |
| R11 | Ama `maintenir`/`annuler`/`cloturer` | 403 | rien écrit |
| R12 | anonyme x3 | 403 | rien écrit |
| R13 | `maintenir` sur `en_cours` / `financee` / `annulee` | 400 | « Cette campagne n'attend pas de décision. », rien écrit |
| R14 | `annuler` x2 | 200 puis 400 | « Cette campagne ne peut plus être annulée. » ; 2 remboursements seulement ; remboursé 90 000 |
| R15 (D1) | `maintenir` puis `annuler` | 200, 200 | `annulee`, remboursement unique, séquestre soldé |
| R16 (D2) | `maintenir` à 8 j | 400 | « Le délai de 7 jours pour maintenir cette campagne est écoulé : les participants vont être remboursés. » ; rien écrit ; la tâche rembourse ensuite |
| R17 | `maintenir` ‖ `annuler`, puis 3x `annuler` en parallèle | voir limites | état final cohérent, remboursé 90 000 une seule fois |
| R18 | /groupeur/campagnes/<id>, 390 px | — | carte de décision, 5/10 pièces, 2 participants, 2 boutons ; pas de débordement (390/390) |
| R19 | clic « Je maintiens » | 200 | une seule requête `POST /api/groupeur/campagnes/12/maintenir/` ; « Financée », carte « Retirez vos fonds », plus de boutons de décision |
| R20 | clic « Renoncer et rembourser » | 200 | `POST /api/groupeur/campagnes/13/annuler/` ; « Annulée », « Groupage non abouti. » |
| R21 | double clic | 200 | un seul `POST` partant |
| R22 | 400 « n'attend pas de décision » | 400 | message français dans l'Alerte |
| R22bis (D2) | 400 délai écoulé | 400 | message du délai affiché |
| R23 | réseau coupé | échec | « Connexion impossible. Vérifiez votre réseau. » |
| R24 | Ama ouvre la page groupeur | — | page « Devenez groupeur » ; aucun bouton de décision |
| R25 | `en_cours` / `financee` / `annulee` | — | ni « Je maintiens » ni « Renoncer » |
| R26 | Ama, fiches annulée / maintenue | — | bandeau « Groupage annulé. <motif> » ; aucun bandeau « minimum non atteint » pour la maintenue |
| R27 | lien de `decision_attendue` | — | `/groupeur/campagnes/<id>` = page R18 |

Tests : `pytest groupachat/tests/test_cloture.py` : 40 passés. `grep` des appels `api.*('/api` dans `frontend/*/src` : vide.

### Limites de la preuve
- **R17** : sqlite ignore `select_for_update`. `maintenir` ‖ `annuler` : 200 et 200 (séquentiels, permis par D1). Trois `annuler` simultanés : 1x 200 et 2x **500 « database is locked »** (verrou de fichier sqlite, pas le verrou applicatif). Prouvé : pas de double remboursement, état final cohérent. Non prouvé : sous PostgreSQL les perdants doivent recevoir 400 et non 500 ; à rejouer sur PostgreSQL. `annuler` après 7 jours : test automatique seulement.
- Mobile hors périmètre. Le jeton CSRF a été posé à la main dans le navigateur.

### Observations non bloquantes
- Après une erreur 400 (autre onglet), l'écran ne se recharge pas : les boutons restent affichés sur une campagne déjà tranchée.
- Page groupeur d'une campagne annulée : « Qui a payé (2) » liste encore les parts remboursées alors que l'en-tête indique 0 participant.
- Fiche acheteur d'une campagne annulée : « Votre part reste consignée jusqu'à la livraison » sous le bandeau d'annulation (T6).
- La tâche des 7 jours incrémente `campagnes_annulees` du groupeur (existant).
- Texte `en_cours` toujours faux (C-009, T6).
