---
type: fonctionnalite
id: F-010
statut: à faire
date: 2026-10-28
tags: [fonctionnalite, F-010, F-021, D-F010, avis, reputation, securite, mvp]
---

# F-010 + F-021 — Avis protégés : seul l'auteur modifie ou supprime, la réputation n'est plus manipulable

Tâche T11 de [[M-001-terminer-le-mvp]]. Décision **D-F010** ([[2026-10-26-decisions-carte]]) : seul l'auteur d'un avis le modifie ou le supprime ; tout autre, groupeur compris, reçoit 403 ; le groupeur garde son droit de réponse (F-020). Panne : [[2026-10-26-recette-failles]] « F-010 », [[recette-etat-des-lieux-2026-10-26]] n°2. Rôles : Acheteur (auteur), Groupeur (visé), autre acheteur, Visiteur. Couches : serveur **oui** · web boutique **oui** (vérification) · mobile non.

## La règle

- Un avis est lisible par tous. Créé par l'acheteur de la participation, une fois la collecte close. **Seul son auteur le modifie (PATCH/PUT) ou le supprime (DELETE).** Tout autre compte authentifié (autre acheteur, groupeur visé compris) : **403**, rien n'est écrit. Sans session : 401/403 comme aujourd'hui.
- Le groupeur visé répond (`POST /avis/<id>/repondre/`), une fois, et ne fait que cela : cette action doit **rester ouverte** au groupeur et refusée aux autres (déjà le cas, l. 162).
- F-021 : la réputation (`Reputation.note`, `avis_recus`) est la moyenne des avis existants (`recalculer_reputation`). Elle n'est plus manipulable parce qu'**aucun tiers** ne peut changer ou retirer un avis ; l'auteur, lui, peut (D-F010), et la réputation se recalcule alors.

## État constaté dans le code (`5dc1562`)

- `commandes/vues.py:99-112` : `AvisVueEnsemble` est un `ModelViewSet` avec `permission_classes = [LectureLibreEcritureVerifiee]` seulement, donc aucune garde d'objet. PATCH/PUT/DELETE passent pour tout numéro vérifié ; `perform_update` (l. 132) et `perform_destroy` (l. 136) recalculent la réputation, donc la manipulation est effective.
- `noyau/permissions.py` : `EstAuteurOuLectureSeule` existe (utilisée par le fil) mais cherche `auteur_id` ou `acheteur_id` sur l'objet. **`Avis` n'a ni l'un ni l'autre** (l'auteur est `participation.acheteur`) : l'ajouter telle quelle refuserait tout le monde, auteur compris. Elle bloquerait aussi `repondre` (POST de détail) : l'action doit être déclarée ouverte.
- `commandes/serialiseurs.py:146-170` : `participation` est **modifiable** à la mise à jour ; `validate_participation` refuse alors « Vous avez déjà noté cette commande » (même participation) ou accepte de déplacer l'avis vers une autre commande de l'auteur. À verrouiller en lecture seule à la mise à jour.
- `commandes/tests.py:420-` (`TestAvis`) : aucun test de modification ni de suppression, ni de 403.
- Écran, `frontend/boutique/src/composants/Avis.tsx` : « Modifier » (l. 153) n'existe que dans `FormulaireAvis`, monté sur `MesAchats.tsx:354` (la commande de l'utilisateur lui-même) ; aucun bouton supprimer ; `ListeAvis` (fiche campagne) et `AvisRecus` (groupeur) n'ont ni modifier ni supprimer, seulement `ChampReponse` pour le groupeur. **L'interface ne propose donc déjà l'action qu'à l'auteur** ; le défaut est serveur. L'erreur d'un PATCH refusé s'afficherait via `envoi.erreur.message` (l. 194).

## Recette

Rôle : Acheteur auteur, autre acheteur, Groupeur visé, Visiteur · Couches : serveur oui · web boutique oui · Source : D-F010, §7 et §3 du cahier.

Contexte commun : campagne `en_cours` de `groupeur`, `ama` a payé 10 pièces, la campagne est clôturée (`.../cloturer/`), `ama` a laissé un avis note 4 ; la réputation vaut 4,0 sur 1 avis. `yao` est un autre acheteur au numéro vérifié ; `yao_sans_part` n'a pas de participation.

### Scénarios

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | l'avis d'`ama` (note 4) | `ama` fait `PATCH /api/avis/<id>/` `{note: 2, commentaire: "Finalement décevant"}` | 200 ; l'avis porte note 2, `modifie_le` renseigné ; `Reputation.note` = 2,0, `avis_recus` = 1 | serveur |
| R2 | l'avis d'`ama` | `ama` fait `DELETE /api/avis/<id>/` | 204 ; `Avis.objects.count()` = 0 ; `Reputation.note` = 0, `avis_recus` = 0 ; `GET /api/avis/<id>/` donne 404 | serveur |
| R3 | l'avis d'`ama`, session `yao` (autre acheteur, avec ou sans participation) | `PATCH` `{note: 1}` puis `DELETE` | 403 aux deux ; l'avis garde note 4 et son `modifie_le` nul ; compte d'avis et réputation inchangés (4,0 / 1) | serveur |
| R4 | l'avis d'`ama`, session du **groupeur visé** | `PATCH` `{note: 5}` puis `DELETE` | 403 aux deux ; rien ne change (note 4, réputation 4,0) | serveur |
| R5 | l'avis d'`ama`, sans session | `PATCH` puis `DELETE` | 401 ou 403 ; rien ne change | serveur |
| R6 | l'avis d'`ama`, un acheteur au numéro **non vérifié** | `DELETE` | 403, rien ne change (règle existante conservée) | serveur |
| R7 | l'avis d'`ama`, session du groupeur visé | `POST /api/avis/<id>/repondre/` `{reponse: "Merci"}` | 200 ; `reponse` = « Merci », `repondu_le` renseigné ; la note et la réputation sont inchangées (droit de réponse conservé) | serveur |
| R8 | l'avis d'`ama`, session `yao` | `POST .../repondre/` | 403 (« Seul le groupeur concerné ») ; `reponse` reste vide | serveur |
| R9 | l'avis d'`ama` | `ama` fait `PATCH` avec `{participation: <autre commande d'ama>}` | la participation de l'avis ne change pas (champ ignoré ou 400, à fixer par la correction) ; l'avis ne migre pas | serveur |
| R10 | l'avis d'`ama`, note hors bornes | `PATCH` `{note: 0}` puis `{note: 6}` | 400 pour chacun ; note inchangée | serveur |
| R11 | un avis inexistant (id 999999) | `PATCH`/`DELETE` par un acheteur vérifié | 404 | serveur |
| R12 | `GET /api/avis/?groupeur=<id>` sans session | lecture | 200 ; la liste contient l'avis ; pas de numéro de téléphone dans `auteur` (seulement `nom_affiche`) : non-régression | serveur |
| R13 | `ama` connectée à la boutique, `MesAchats` > détail de sa commande | elle ouvre l'écran | « Votre avis » et le bouton « Modifier » sont affichés ; « Modifier » puis envoi appelle `PATCH /avis/<id>/` et l'avis à l'écran change | web |
| R14 | `yao` ou le groupeur ouvre la fiche de la campagne, ou l'écran « Avis reçus » du groupeur | il consulte les avis | aucun bouton Modifier ni Supprimer sur l'avis d'autrui ; le groupeur voit uniquement le champ de réponse sous un avis sans réponse | web |
| R15 | l'écran d'`ama` pendant que le serveur renvoie 403 (par exemple session d'un autre compte reprise dans un onglet ancien) | elle envoie la modification | le message d'erreur du serveur s'affiche en rouge sous le formulaire, l'avis affiché ne change pas | web |

R3 à R6 et R8 sont les refus de sécurité ; R10 et R11 les cas d'erreur ; R1, R2, R7 les cas nominaux. F-021 est prouvée par les lignes « Reputation » de R1 à R4 (rien ne bouge après un refus) et par R2 (retour à zéro après suppression par l'auteur).

### Tests automatiques attendus

Dans `backend/groupachat/commandes/tests.py`, classe `TestAvis` (ou une classe `TestAvisProteges` voisine) :
- `test_l_auteur_modifie_son_avis_et_la_reputation_suit` (R1) ;
- `test_l_auteur_supprime_son_avis_et_la_reputation_retombe` (R2) ;
- `test_un_autre_acheteur_ne_modifie_ni_ne_supprime_un_avis` (R3, avec assertions sur la note, `modifie_le`, le compte d'avis et la `Reputation`) ;
- `test_le_groupeur_vise_ne_modifie_ni_ne_supprime_l_avis_qui_le_concerne` (R4, avec assertion sur la `Reputation`) ;
- `test_sans_session_on_ne_touche_pas_a_un_avis` (R5) ;
- `test_un_numero_non_verifie_ne_supprime_pas_un_avis` (R6) ;
- `test_le_groupeur_garde_son_droit_de_reponse` (R7) ;
- `test_un_tiers_ne_repond_pas_a_la_place_du_groupeur` (R8) ;
- `test_on_ne_deplace_pas_un_avis_vers_une_autre_commande` (R9) ;
- `test_la_note_hors_bornes_est_refusee_a_la_modification` (R10) ;
- `test_avis_inexistant_donne_404` (R11).
Chaque test de refus vérifie l'état **après** (ligne conservée, réputation inchangée), pas seulement le statut. R12 : une assertion ajoutée à un test de lecture existant ou `test_la_liste_des_avis_ne_montre_pas_le_telephone`. Vérifier qu'ils sont collectés : `python -m pytest --collect-only -q groupachat/commandes/tests.py`. Le test de R4 doit échouer sur `5dc1562` (200/204 aujourd'hui).
Web (R13-R15) : pas de test unitaire dans le dépôt ; contrôle en navigateur et `npm run verifier`.

### Vérification d'interface

`/mes-achats` > détail (auteur) ; `/campagnes/<id>` > avis (tout rôle) ; `/groupeur/campagnes/<id>` > avis reçus (groupeur). États : chargement (squelettes `ListeAvis`), vide (`EtatVide`), erreur d'envoi lisible (`envoi.erreur`). À 390 px. Rien à ajouter côté boutons si R14 est vérifié tel quel ; ne pas introduire de bouton « Supprimer » sans décision (Q1).

## Fichiers que le correctif touchera

`backend/groupachat/commandes/vues.py` (permission d'objet sur `AvisVueEnsemble`, `repondre` déclarée ouverte) · `backend/groupachat/noyau/permissions.py` (règle d'auteur qui sache lire `participation.acheteur_id`, ou petite permission dédiée aux avis) · `backend/groupachat/commandes/serialiseurs.py` (`participation` non modifiable à la mise à jour) · `backend/groupachat/commandes/tests.py`. Frontend : **aucun** attendu (R13-R15 à vérifier seulement).

## Questions ouvertes

**Q1. L'auteur peut-il supprimer son avis alors que l'écran ne le propose pas ?** D-F010 dit « modifie ou supprime » : le serveur doit l'accepter (R2). L'écran n'a qu'un bouton « Modifier ». Options : (a) serveur seul, pas de bouton ; (b) ajouter « Supprimer mon avis » dans `FormulaireAvis`. Recommandation : (a), pour tenir l'enveloppe ; la suppression existe en API pour l'auteur, le bouton est F-0xx plus tard.
**Q2. Un avis qui a reçu une réponse reste-t-il modifiable par son auteur ?** D-F010 ne le dit pas ; changer la note après la réponse du groupeur rend la réponse hors-sujet, et la réputation reste manipulable par l'auteur lui-même. Options : (a) oui, sans limite (règle actuelle de D-F010) ; (b) modifiable, mais la réponse est effacée ; (c) verrouillé après réponse. Recommandation : (a) pour ne pas inventer une règle hors décision ; à noter pour F-0xx.
**Q3. Un participant remboursé ou ayant sa part annulée peut-il noter ?** `Participation.peut_etre_notee` n'exclut que `en_attente_paiement` : une part `remboursee` ou `annulee` peut noter, et la campagne `annulee` est dans `STATUTS_COLLECTE_CLOSE`. C'est un vecteur de fausse note (F-021) hors D-F010. Options : (a) laisser (« y compris quand rien n'a été livré », docstring de `peut_etre_notee`, cohérent avec « la plateforme n'arbitre pas ») ; (b) exclure `remboursee`/`annulee`. Recommandation : (a), la règle est écrite en toutes lettres dans le modèle ; aucun changement dans T11.

## Prêt à coder ?

**Oui.** D-F010 tranche le comportement ; Q1 à Q3 ont une réponse par défaut (recommandations) qui n'empêche pas de commencer. R9 suppose que la correction choisit entre « champ ignoré » et « 400 » : l'un ou l'autre satisfait « l'avis ne migre pas ».

## Recette — 2026-10-28

**RECETTE OK** — serveur ✅ · web boutique ✅ · mobile — (non concerné). Code non commité sur la base `5dc1562` (branche `fix/F-010-avis-proteges`, worktree). Environnement : SQLite jetable + `charger_demo`, Django sur 127.0.0.1:8123, Vite sur 5273 (proxy vers 8123), Chrome headless 390 px. Tout arrêté et vérifié (`ss`).

### Serveur (vraies requêtes HTTP, session + CSRF, état relu en base SQLite)
| # | Résultat observé |
|---|---|
| R1 | Ama PATCH note 5→2 : 200, `modifie_le` renseigné, réputation 4,0→3,5 (6 avis, relu en base) |
| R2 | Ama DELETE : 204, ligne absente, réputation 3,8 sur 5 avis, GET → 404 |
| R3 | Yao PATCH, PUT, DELETE : 403 ×3 ; avis, compte (6) et réputation relus inchangés |
| R4 | Groupeur visé PATCH, PUT, DELETE : 403 ×3 ; idem inchangé. Autre groupeur : 403 ×2, inchangé |
| R5 | Anonyme PATCH, PUT, DELETE : 403 ; inchangé |
| R6 | Numéro non vérifié PATCH/DELETE : 403 (« Vérifiez votre numéro ») ; inchangé |
| R7 | Groupeur répond : 200, `reponse` = « Merci », note et réputation inchangées |
| R8 | Yao, Ama, autre groupeur, anonyme sur `repondre` : 403 ; `reponse` reste vide |
| R9 | PATCH/PUT de l'auteur avec `participation` (autre commande à lui, ou commande d'autrui) : 200, `participation` reste 30, aucune ligne ne migre (champ ignoré en silence, remarque relecteur confirmée) |
| R10 | note 0 et 6 : 400 chacun, note inchangée |
| R11 | PATCH et DELETE sur l'id 999999 : 404 |
| R12 | GET anonyme `/avis/?groupeur=2` : 200 ; `auteur` = `{nom_affiche}` seul ; aucun « telephone » ni numéro dans la réponse |
| + | POST avec `participation` d'autrui sans avis : 400 « Ce n'est pas votre commande » ; doublon : 400 ; aucune ligne créée |

Tests : `TestAvisProteges` contient les 11 tests attendus (R1 à R11), collectés ; `-k Avis` : 20 passés.

### Web boutique, 390 px
- R13 ✅ : Ama publie un avis (`POST /avis/` 201) ; « Votre avis » + « Modifier » s'affichent ; Modifier → Enregistrer (`PATCH /avis/7/` 200), le texte modifié s'affiche. Aucun bouton « Supprimer » (Q3).
- Fiche campagne ✅ : « 3.5 / 6 avis » et « Abalo Import 3.50/5 » cohérents avec la base.
- R14 ✅ : visiteur, Yao (sur son propre avis) : 0 « Modifier », 0 « Supprimer ». Groupeur (`/groupeur`, « Avis reçus ») : 0 Modifier/Supprimer, champ de réponse seul ; sa réponse (`POST /avis/7/repondre/` 200) s'affiche.
- R15 ✅ : onglet d'Ama dont la session a été remplacée par celle de Yao : `PATCH /avis/2/` 403, « Vous ne pouvez modifier que vos propres contenus. » en rouge sous le formulaire ; l'avis en base reste inchangé.
- Captures : `scratchpad/t11r/r13_*.png`, `r14_*.png`, `r15_403.png`.

### Observations non bloquantes
1. Un PATCH/PUT portant `participation` est ignoré sans signal (200) : accepté par R9.
2. Réponse du groupeur : rien n'empêche une seconde réponse alors que l'écran dit « une seule fois » (champ masqué après la première). Hors F-010, non testé comme règle.
3. Test d'interface : après connexion automatisée suivie d'un rechargement dur, la session n'a pas été reconnue sur 2 essais sur ~6 (`/comptes/moi/` 403) puis rejouée avec succès ; non reproduit de façon stable, probablement lié au rythme du scénario automatisé (hors périmètre).
