---
type: fonctionnalite
id: F-008
statut: terminée
date: 2026-10-27
tags: [fonctionnalite, F-008, notifications, mvp]
---

# F-008 — Notifications : la cloche et la page mènent à l'écran concerné

Statut : **terminée** (2026-10-27) : reviewer-tester VALIDÉE (deux passes), recette **RECETTE OK** (serveur OK, web OK à 390 px, mobile —). Correctif commité `769ec1a` (« Répare les liens des notifications qui menaient à une page introuvable ») sur `fix/F-008-liens-notifications`, partie de `staging` `f8b78f9`, fusionné dans `staging` et poussé sur `origin/staging` (2026-10-27) ; il était non commité au moment de la recette. T3 de [[M-001-terminer-le-mvp]]. Décisions : [[2026-10-27-decisions-f008]]. Rôle : Acheteur (et Groupeur pour ses propres notifications). Source : `CAHIER_DES_CHARGES.md` (notifications aux étapes du cycle de vie) ; [[carte]] C-16 ; recette T1 (404 confirmée).
Hors périmètre : C-016 (une erreur s'affiche comme état vide), C-017 (textes : lien vide sur « Remboursement effectué », « Minimum atteint » renvoyé à chaque paiement au-delà du minimum).

Livraison (`git diff --stat` au moment de la recette, non commité ; commitée ensuite en `769ec1a`) : `backend/groupachat/paiements/services.py` (4 insertions, 2 suppressions) ; `backend/groupachat/echanges/tests.py` (+51) ; nouveaux : `backend/groupachat/echanges/migrations/0004_corriger_liens_des_notifications.py` (migration de données) et `backend/groupachat/tests/test_notifications_liens.py` (7 tests).

## Le défaut
`backend/groupachat/paiements/services.py` crée deux notifications d'acheteur avec le lien `/participations/<id>` : « Paiement enregistré » (l. 115) et « Votre produit est arrivé » (l. 560). Or la boutique (`frontend/boutique/src/App.tsx` l. 44-45) sert `/mes-achats` et `/mes-achats/:id`. `/participations/` n'est qu'une route d'**API** (`api.py` l. 33). Le clic (cloche `Cloche.tsx` l. 263, page `Notifications.tsx` l. 145 : `<Link to={notification.lien}>`) tombe sur la route `*` (page introuvable). C'est le lien de l'acheteur vers son code de retrait : sans lui, le parcours « je suis prévenu que mon produit est arrivé, je clique, je montre mon QR » est rompu.

## Tableau des liens (tous les `Notification` créés dans `backend/`)
Routes de la boutique : `/`, `/catalogue`, `/campagnes/:id`, `/communaute`, `/mes-achats`, `/mes-achats/:id`, `/notifications`, `/profil`, `/profil/devenir-groupeur`, `/connexion`, `/inscription`, `/groupeur`, `/groupeur/campagnes`, `/groupeur/campagnes/nouvelle`, `/groupeur/campagnes/:id`. La console d'administration (port 5174) n'est destinataire d'aucune notification.

| Genre | Créé dans | Lien produit | Route de la boutique | Reçu par | Verdict |
|---|---|---|---|---|---|
| `paiement_enregistre` | `paiements/services.py` l. 106 | `/participations/<id>` | **non** (404) | acheteur | **CASSÉ** (cible : `/mes-achats/<id>`) |
| `marchandise_disponible` | `paiements/services.py` l. 553 | `/participations/<id>` | **non** (404) | acheteur | **CASSÉ** (cible : `/mes-achats/<id>`) |
| `paiement_recu` | l. 119 | `/groupeur/campagnes/<campagne>` | oui | groupeur | correct |
| `minimum_atteint` | l. 132 | `/groupeur/campagnes/<campagne>` | oui | groupeur | correct (doublon : C-017) |
| `campagne_financee` (groupeur) | l. 230 | `/groupeur/campagnes/<campagne>` | oui | groupeur | correct |
| `decision_attendue` | l. 256 | `/groupeur/campagnes/<campagne>` | oui | groupeur | correct (vérifié par la recette F-016, R27) |
| `nouveau_commentaire` | `echanges/vues.py` l. 97 | `/groupeur/campagnes/<campagne>` | oui | groupeur | correct |
| `nouvel_avis` | `commandes/vues.py` l. 145 | `/groupeur/campagnes/<campagne>` | oui | groupeur | correct |
| `kyc_decide` | `espaces/administration.py` l. 80 | `/groupeur` | oui | futur groupeur (compte acheteur au moment de la demande) | correct ; à voir : un dossier refusé mène à l'espace groupeur, qui peut afficher « Devenez groupeur » |
| `campagne_financee` (acheteurs) | `_prevenir_participants` l. 383 | `/campagnes/<campagne>` | oui | acheteur | correct |
| `groupage_non_abouti` | idem | `/campagnes/<campagne>` | oui | acheteur | correct |
| `campagne_maintenue` | idem | `/campagnes/<campagne>` | oui | acheteur | correct |
| `campagne_annulee` | idem | `/campagnes/<campagne>` | oui | acheteur | correct |
| `reponse_commentaire` | `echanges/vues.py` l. 90 | `/campagnes/<campagne>` | oui | acheteur (ou tout auteur) | correct |
| `remboursement` | `paiements/services.py` l. 181 | **vide** | — (pas de lien : la ligne n'est pas cliquable) | acheteur | sans lien (C-017) |
| `campagne_financee` « Fonds versés » | l. 510 | **vide** | — | groupeur | sans lien (non signalé au backlog ; voir Q5) |
| `retrait_confirme` | l. 598 | **vide** | — | acheteur | sans lien (voir Q5) |
| `relance_retrait` | déclaré dans `echanges/models.py` l. 246 | aucune création trouvée dans `backend/` | — | — | genre jamais émis (F-0xx relances, non codé) |

Bilan : 2 liens **cassés** (les deux de l'acheteur vers son code), 11 corrects, 3 notifications sans lien, 1 genre jamais émis. Un lien relatif à `/campagnes/<id>` vers une campagne supprimée ne peut pas arriver (la campagne n'est pas supprimée en base).

## Jeu de démonstration et données existantes
`charger_demo.py` ne crée aucune `Notification` à la main : elles naissent des appels aux services (`encaisser`, `mettre_a_disposition`…), donc le jeu actuel (`VERSION_DEMO = "5"`) contient des liens `/participations/<id>`. Un serveur déjà chargé et la production (si des paiements réels ont été simulés) en ont aussi. Corriger la source ne répare **pas** les lignes déjà écrites : voir Q1.

## Résultat observable
Un acheteur qui clique sur « Paiement enregistré » ou « Votre produit est arrivé », depuis la cloche ou la page `/notifications`, arrive sur `/mes-achats/<id>` et voit sa commande avec son code de retrait et son QR. Aucune notification d'aucun genre ne mène à une page « introuvable ». Une notification est cliquable si, et seulement si, elle a un lien valide.

## Recette
Rôle : acheteur (reçoit et clique) ; groupeur (reçoit les siennes) ; autre acheteur et anonyme (refusés) · Couches : serveur oui (génération du lien) · web oui (le clic, la route) · mobile non · Source : cycle de vie (§4, §9), [[carte]] C-16.

Préparation commune : acheteur Ama (numéro vérifié) et Yao ; groupeur G valide ; campagne C `en_cours` ; Ama paie 3 pièces (participation P). `charger_demo` ou fixtures de `test_cloture.py` / `conftest.py`.

### Scénarios
| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | Ama sans part payée | Ama paie P (`POST /api/participations/<id>/payer/`, ou le service `encaisser`) | notification `paiement_enregistre` pour Ama avec `lien == "/mes-achats/<P.id>"` (champ `lien` de `GET /api/notifications/`) | serveur |
| R2 | C `financee`, P `payee` | G `POST …/mise-a-disposition/` | notification `marchandise_disponible` pour Ama avec `lien == "/mes-achats/<P.id>"` ; P `prete` ; message contient le code de retrait | serveur |
| R3 | R1 jouée | `GET /api/participations/<id extrait du lien>/` avec la session d'Ama | 200 ; le JSON contient `id`, `code_retrait`, `charge_qr`, `campagne` : le lien désigne une ressource qui existe | serveur |
| R4 | tous les genres émis (R1, R2, paiement groupeur, minimum, financée, décision attendue, non abouti, maintenue, annulée, remboursement, retrait confirmé, commentaire, réponse, avis, KYC) | on lit tous les `lien` non vides créés | chacun correspond à un motif de la liste des routes de la boutique (`/mes-achats/<n>`, `/campagnes/<n>`, `/groupeur`, `/groupeur/campagnes/<n>`) ; aucun ne commence par `/participations`, `/api` ou ne contient d'adresse absolue | serveur |
| R5 | cas d'erreur : Ama paie avec un numéro refusé / part déjà payée | le paiement est refusé (400) | **aucune** notification `paiement_enregistre` créée (pas de lien orphelin) | serveur |
| R6 | refus de sécurité : P appartient à Ama | Yao `GET /api/participations/<P.id>/` | 404 ; rien dans la réponse sur le code ni la campagne ; le lien `/mes-achats/<P.id>` ouvert par Yao affiche « Commande introuvable. » sans fuite | serveur + web |
| R7 | idem | anonyme `GET /api/participations/<P.id>/` et `GET /api/notifications/` | 403 (ou 401) / liste vide (`Notification.objects.none()`) | serveur |
| R8 | refus de sécurité : notification de Ama | Yao `POST /api/notifications/<id>/marquer-lue/` | 404 ; `lue_le` de Ama inchangé | serveur |
| R9 | participation inexistante : lien `/mes-achats/999999` | Ama ouvre le lien | `/api/participations/999999/` répond 404 ; l'écran affiche « Commande introuvable. » (pas de chargement infini, pas d'écran blanc) | web |
| R10 | Ama a une notification `paiement_enregistre` non lue | clique dessus dans la **cloche** | le panneau se ferme, l'adresse devient `/mes-achats/<P.id>`, l'écran montre la commande, le QR et le code ; la notification passe lue, le compteur de la cloche baisse de 1 | web |
| R11 | idem | clique sur la **page** `/notifications` | même résultat que R10 ; retour arrière ramène à la liste | web |
| R12 | Ama a « Votre produit est arrivé » | clique (cloche puis page) | `/mes-achats/<P.id>`, statut « prête », code de retrait et QR visibles | web |
| R13 | Ama reçoit `campagne_annulee`, `campagne_maintenue`, `groupage_non_abouti`, `campagne_financee`, `reponse_commentaire` | clique | `/campagnes/<C.id>` s'affiche (fiche campagne) | web |
| R14 | G reçoit `paiement_recu`, `minimum_atteint`, `decision_attendue`, `nouveau_commentaire`, `nouvel_avis`, `campagne_financee` | clique | `/groupeur/campagnes/<C.id>` s'affiche (page de décision/suivi) | web |
| R15 | G2 (autre groupeur) ouvre à la main `/groupeur/campagnes/<C.id>` | idem | « Campagne introuvable » (l'API filtre par propriétaire, 404) | web |
| R16 | futur groupeur (dossier KYC décidé) | clique `kyc_decide` | `/groupeur` s'affiche : espace groupeur si validé ; si refusé, message cohérent avec le « Dossier à corriger » (à constater, voir Q4) | web |
| R17 | notifications `remboursement`, `retrait_confirme`, « Fonds versés » (sans lien) | affichage cloche et page | la ligne n'est pas un lien (pas de curseur cliquable) ; aucune erreur ; le clic marque quand même comme lue ou non selon la règle actuelle (à consigner) | web |
| R18 | ancienne notification en base avec `/participations/<id>` (état avant correctif) | Ama clique | comportement selon la décision Q1 : soit migration (le lien est déjà réécrit, R10 passe), soit redirection (l'adresse `/participations/<id>` renvoie vers `/mes-achats/<id>`), soit constat « 404 » assumé | web + serveur |
| R19 | Ama à 390 px de large, 3 notifications dont une non lue | ouvre la cloche puis `/notifications` | le panneau tient dans l'écran (pas de défilement horizontal), les lignes sont cliquables au pouce (zone >= 44 px), le titre et le message ne débordent pas ; capture `npx playwright screenshot --viewport-size=390,844` | web |
| R20 | état chargement / erreur / vide | page `/notifications` : requête lente, API en erreur, aucune notification | squelettes ; message d'erreur lisible (aujourd'hui : l'erreur s'affiche comme état vide, **C-016, hors périmètre**, à consigner sans bloquer) ; « Aucune notification » avec le bon texte | web |

### Tests automatiques attendus
Serveur — nouveau fichier `backend/groupachat/tests/test_notifications_liens.py` (le motif `test_*.py` est collecté ; vérifier avec `python -m pytest --collect-only -q groupachat/tests/test_notifications_liens.py`), car le test traverse paiements, commandes, échanges et espaces :
- `test_le_paiement_pointe_vers_la_commande_de_l_acheteur` (R1, R3) ; `test_le_produit_arrive_pointe_vers_la_commande_de_l_acheteur` (R2).
- `test_un_paiement_refuse_ne_cree_pas_de_notification` (R5).
- `test_chaque_lien_de_notification_correspond_a_une_route_de_la_boutique` (R4) : joue le parcours complet (paiement, minimum, clôture sous minimum, maintien, annulation, mise à disposition, retrait, commentaire et réponse, avis, décision KYC), récupère toutes les `Notification` et vérifie chaque `lien` contre une liste de motifs `^/mes-achats/\d+$`, `^/campagnes/\d+$`, `^/groupeur(/campagnes/\d+)?$`. Le test ne peut pas lire le routeur React ; la liste de motifs est donc une **copie des routes de `App.tsx`** (voir Q3 : garde-fou contre la dérive).
- `test_le_lien_de_la_commande_ne_sert_qu_a_son_proprietaire` (R6, R7 : un autre acheteur et un anonyme sur `/api/participations/<id>/`) et `test_on_ne_marque_pas_lue_la_notification_d_un_autre` (R8, peut déjà exister : `test_chacun_ne_voit_que_ses_notifications` dans `echanges/tests.py` l. 183, à vérifier qu'il couvre `marquer-lue`).
- Si Q1 retient la migration : `test_la_migration_reecrit_les_anciens_liens` dans `groupachat/echanges/tests.py` (base avec un lien `/participations/7` avant, `/mes-achats/7` après, les autres liens intacts).
Web — le dépôt n'a aucun outil de test front (`npm run verifier` = `tsc -b`) ; R9 à R20 restent des constats de recette (navigateur à 390 px ou Playwright en lecture). Si Q1 retient la redirection côté boutique, le typage ne la prouve pas non plus.

### Vérification d'interface
- Écrans : cloche (`composants/Cloche.tsx`, panneau et lien « Voir tout ») ; page `/notifications` (`pages/Notifications.tsx`) ; destination `/mes-achats/:id` (`DetailAchat` dans `MesAchats.tsx`, requête `GET /participations/${id}/`).
- Champs lus : `lien`, `lue_le`, `genre`, `titre`, `message`, `cree_le` (à comparer au JSON réel de `GET /api/notifications/`) ; pour la destination : `code_retrait`, `charge_qr`, `campagne`.
- Chargement : squelettes sur la liste et sur `DetailAchat`. Erreur : à constater (C-016). Vide : `EtatVide` sur la liste ; « Commande introuvable. » sur `DetailAchat`.
- Contrat : l'action « ouvrir une notification » n'existe que si `lien` est non vide ; le rôle n'est pas filtré côté client (un lien `/groupeur/...` n'est reçu que par un groupeur, car le serveur n'en envoie qu'à ce destinataire).
- À observer aussi : la ligne est un `<li onClick={marquer}>` autour d'un `<Link>` ; le marquage « lue » part-il avant la navigation (requête `marquer-lue` non annulée) ?

## Questions ouvertes
1. **Les anciennes notifications (R18)** — **décision de l'utilisateur.** Les lignes déjà écrites gardent `/participations/<id>`. Options : (a) migration de données `RunPython` qui réécrit `/participations/<n>` en `/mes-achats/<n>` (propre, une fois, irréversible sans effort ; migration à relire) ; (b) route de redirection côté boutique (`/participations/:id` vers `/mes-achats/:id`), qui couvre aussi les lignes à venir et un éventuel lien déjà partagé ; (c) rien, `VERSION_DEMO` incrémenté suffit pour la démonstration, mais pas pour une base qui a servi. Recommandation : (a) si la base de production contient des notifications ; sinon (c) avec l'incrément de `VERSION_DEMO` (non requis si le jeu n'est pas touché : à confirmer). Je ne tranche pas. **Réponse (2026-10-27, D1)** : option (a), migration de données `echanges/0004`, retour neutre. Voir [[2026-10-27-decisions-f008]].
2. **Où corriger** : à la source (`services.py`, deux lignes) comme le suggère le backlog, ou aussi côté boutique ? Recommandation : à la source seulement, plus la décision de Q1. **Réponse (livraison)** : à la source seulement (`services.py`), aucune correction côté boutique. Pas de décision séparée.
3. **Garde-fou contre la dérive** : le test R4 compare à une copie des routes. Accepter cette duplication, ou ajouter un contrôle dans `check.sh` (comme `prefixe_api`, décision D3 de F-016) qui lit `App.tsx` et les motifs de `lien=` du backend ? Une dépendance front est exclue sans note dans `mapper/02-decisions/`. **Réponse (D2)** : copie des routes de `App.tsx` dans `test_notifications_liens.py`, pas de contrôle dans `check.sh`. Si une route change, ce test se met à jour dans le même passage.
4. **`kyc_decide` refusé** : le lien `/groupeur` pour un dossier refusé est-il le bon écran (l'espace groupeur affiche « Devenez groupeur » pour qui n'est pas validé) ou faut-il `/profil/devenir-groupeur` ? Non bloquant, à constater en R16. **Réponse : non tranchée**, suivie en C-038 (à voir avec T4, F-011).
5. **Notifications sans lien** (`retrait_confirme`, « Fonds versés », `remboursement`) : voulu, ou faut-il pointer vers `/mes-achats/<id>` (acheteur) et `/groupeur/campagnes/<id>` (groupeur) ? `remboursement` relève de C-017, hors périmètre. **Décision de l'utilisateur** : étendre F-008 à `retrait_confirme` et « Fonds versés » ou les laisser en suivi. **Réponse (D3)** : étendu à `retrait_confirme` (`/mes-achats/<id>`) et « Fonds versés » (`/groupeur/campagnes/<id>`). `remboursement` reste sans lien (C-017).
6. **Genre `relance_retrait`** : déclaré, jamais émis. Rien à tester ici ; hors périmètre, à rattacher à la fonctionnalité des relances. **Réponse** : F-031 / T5 de [[M-001-terminer-le-mvp]] ; pas de chantier séparé (le genre n'est toujours pas émis au 2026-10-27).
7. **Jeton de lien** : le contrôle côté serveur ne vérifie pas que `campagne` ou `participation` du lien existe encore ; sans suppression possible en base c'est sans conséquence. Confirmer qu'aucune suppression de participation n'est prévue. **Réponse : non tranchée**, suivi à confirmer par l'utilisateur ; sans suppression possible, sans conséquence.

## Recette (recetter, 2026-10-27)
**RECETTE OK** — commit de base `f8b78f9`, arbre de travail non commité à la date de la recette (services.py, echanges/tests.py, migration 0004, test_notifications_liens.py) ; commité ensuite en `769ec1a`. Matrice : serveur ✅ · web ✅ · mobile —.
Environnement : `runserver` local (port 8124, sqlite et médias dans le scratchpad, `DJANGO_ORIGINES_SURES` pour l'origine de Vite), Vite 5199 relayé vers lui, Chrome headless 390 x 844 (playwright-core). Données fictives. Décisions D1 à D3 de l'utilisateur appliquées ; hors périmètre non comptés (lien vide de `remboursement`, erreur affichée comme état vide, `kyc_decide` refusé, `relance_retrait`).

### Tests
`python -m pytest groupachat/tests/test_notifications_liens.py groupachat/echanges/tests.py` : 30 passés (7 collectés dans le nouveau fichier, dont la copie des motifs de `App.tsx`, le refus de Yao et le marquage d'autrui).

### Serveur (parcours réel par curl, sessions réelles)
Paiements Ama/Yao sur 3 campagnes, clôture (`cloturer_les_campagnes_echues`), maintien, annulation, demande de retrait, exécution par l'administrateur, mise à disposition, retrait par code, commentaire/réponse, avis, décision KYC. Liens relus en base (`group by genre, lien`) : `paiement_enregistre` et `marchandise_disponible` et `retrait_confirme` = `/mes-achats/<participation>` ; « Fonds versés » = `/groupeur/campagnes/1` ; `paiement_recu`, `minimum_atteint`, `decision_attendue`, `nouveau_commentaire`, `nouvel_avis`, `campagne_financee` (groupeur) = `/groupeur/campagnes/<n>` ; acheteur : `/campagnes/<n>` ; `kyc_decide` = `/groupeur` ; `remboursement` = vide (hors périmètre). Aucun lien `/participations`, `/api` ou absolu.
Refus : paiement d'une part déjà payée = 400 sans nouvelle notification (R5) ; Yao `GET /api/participations/1/` = 404 ; anonyme = 403 (participations et notifications, écart assumé) ; participation 999999 = 404 ; Yao `marquer-lue` sur la notification d'Ama = 404 et `lue_le` d'Ama resté NULL (R8).

### Migration 0004 (base séparée amenée à l'état 0003)
Avant : `/participations/7`, `/participations/123`, `/participations/7/x`, `/api/participations/7`, `/participations/abc`, `/participations/7/`, `/campagnes/3`, `/groupeur`, `/groupeur/campagnes/1`, vide, `/mes-achats/9`. Après : seuls `/participations/7` et `/participations/123` deviennent `/mes-achats/7` et `/mes-achats/123` ; tout le reste est identique. Retour arrière (0003) : OK, neutre. Rejouée : sans effet. `makemigrations --check` : aucun changement. Remarque non bloquante : `/participations/7/` (barre finale) n'est pas réécrit ; le code n'en a jamais produit.

### Web à 390 px
| Scénario | Action | Observé |
|---|---|---|
| R10 cloche, « Paiement enregistré » (Ama) | clic sur la ligne | adresse `/mes-achats/5`, panneau fermé, compteur 12 → 11, `POST marquer-lue` 200, détail de la commande avec code et QR ; pas de défilement horizontal (390/390), ligne de 83 px |
| R11 page, même notification | clic | `/mes-achats/5`, retour arrière ramène à `/notifications` (ligne de 106 px) |
| R12 « Votre produit est arrivé » (Yao, cloche puis page) | clic | `/mes-achats/2`, « Prête à être retirée », code N7FM Y9KM, QR affiché (capture `shot_yao_cloche_arrive.png`), compteur 10 → 9 |
| « Retrait confirmé » (Ama, cloche puis page) | clic | `/mes-achats/1`, statut « Retirée », bon achat (code TTKP JMPF) |
| « Fonds versés » (groupeur, cloche puis page) | clic | `/groupeur/campagnes/1`, page de suivi « Distribution », 1 / 2 colis remis |
| Notification du groupeur (« Nouveau message ») | clic page | `/groupeur/campagnes/1` affichée |
| R17 « Remboursement effectué » (sans lien, page et cloche) | clic | pas de lien (pas d'ancre), aucune navigation ni erreur ; la page marque lue (POST 200), la cloche reste ouverte sans écriture |
| R18 ancien lien | migré en base (voir migration) ; l'adresse brute `/participations/1` non migrée affiche 404 « Cette page n'existe pas » (attendu, D1 sans redirection) | conforme |
| R6/R9 `/mes-achats/1` ouvert par Yao | navigation directe | « Commande introuvable. » (API 404), pas de fuite |
| R9 `/mes-achats/999999` | navigation directe | « Commande introuvable. » |
| R20 vide (G2, aucune notification) | `/notifications` | « Rien à signaler », texte d'aide |
| R20 chargement (réponse retardée 3 s) | `/notifications` | 3 squelettes, pas de contenu |
| R20 erreur (API forcée en 500) | `/notifications` | affiche l'état vide « Rien à signaler » : C-016, hors périmètre |
| R19 | cloche et page à 390 px | aucun défilement horizontal, lignes >= 63 px |

Note de méthode : sur la page, une notification déjà lue par la cloche ne renvoie pas de `marquer-lue` (comportement attendu) ; le marquage a été observé à la cloche et sur « Nouveau message » (page).
Non testé : R13 et R16 au clic dans le navigateur (liens `/campagnes/<n>` et `/groupeur` vérifiés en base et par test serveur ; routes présentes dans `App.tsx`).
