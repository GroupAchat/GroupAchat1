---
type: fonctionnalite
id: F-009
statut: à vérifier
date: 2026-10-28
tags: [fonctionnalite, F-009, fil, commentaires, integrite, securite, mvp]
---

# F-009 — Fil de discussion : réponses, brouillons et campagnes inexistantes

Tâche T12b de [[M-001-terminer-le-mvp]]. Panne : [[recette-etat-des-lieux-2026-10-26]] (gênes, F-009). Rôles : Acheteur (numéro vérifié), Groupeur, Visiteur. Couches : serveur **oui** · web boutique **oui** (message d'erreur) · mobile non. Source : cahier §7 (fil public), carte F-009.
Hors périmètre : F-035 (tri), F-025 (modération), F-020 (réponse du groupeur, non-régression seulement).

## La règle

1. `reponse_a` doit désigner un message **de la même campagne** que l'URL ; sinon 400, rien d'écrit, pas de notification. (Le fil reste à un seul niveau : « on ne répond pas à une réponse », déjà en place.)
2. On n'écrit pas dans le fil d'une campagne `brouillon` qui n'est pas la sienne : refus, rien d'écrit, aucune notification au groupeur. Une campagne `brouillon` est privée (commentaire de `catalogue/vues.py:176`).
3. Une campagne inexistante ne produit jamais de 500 : **404** propre, rien d'écrit.
4. Le reste du fil est inchangé : lecture sans compte, écriture avec numéro vérifié, un seul niveau, notifications existantes.

## État constaté dans le code (`5dc1562`)

- `echanges/vues.py:77-82` : `perform_create` fait `Campagne.objects.get(pk=...)` : `DoesNotExist` non géré, **500** pour une campagne inexistante.
- `echanges/serialiseurs.py:60-67` : `validate_reponse_a` ne contrôle que « pas une réponse à une réponse » ; il ne compare pas `parent.campagne_id` à la campagne de l'URL (le sérialiseur ne la connaît pas, `campagne` est en lecture seule). Une réponse à un message d'une autre campagne passe : 201, et `_notifier` (l. 84) envoie « Réponse à votre message » avec un lien vers la mauvaise campagne.
- Aucun contrôle sur `campagne.statut` : un commentaire sur un brouillon d'autrui passe (201 + notification au groupeur, l. 94).
- `get_queryset` (l. 49-64) filtre par `campagne_id` sans vérifier l'existence ni le statut : `GET` d'une campagne inexistante renvoie 200 et une liste vide ; `GET` d'un brouillon renvoie son fil. Voir Q1.
- `jaime` (l. 108) : passe par `get_object()` sur le queryset de la campagne de l'URL, donc un message d'une autre campagne y est 404 : non concerné.
- Écran `frontend/boutique/src/composants/Discussion.tsx` : `publication.erreur.message` s'affiche déjà en rouge (l. 95-97) et `reponse_a` est envoyé depuis `repondA` (l. 27) ; l'écran n'offre de répondre qu'à un message du fil affiché, donc le défaut n'est pas atteignable par l'interface, seulement par l'API. Aucun changement d'écran attendu si le serveur renvoie `{"detail": ...}` ou `{"champ": [...]}` lisible par `ErreurApi`.

## Recette

Rôle : Acheteur, Groupeur, Visiteur · Couches : serveur oui · web boutique oui (non-régression et affichage d'erreur) · Source : cahier §7.

Contexte : `campagne_a` (`en_cours`, groupeur `g1`) ; `campagne_b` (`en_cours`, autre groupeur `g2` ou le même) ; `brouillon_g2` (`brouillon` de `g2`) ; `ama` et `yao` acheteurs vérifiés. Message `m_b` d'`yao` dans `campagne_b`.

### Scénarios

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | `campagne_a` en cours, `ama` vérifiée | `POST /api/campagnes/<a>/commentaires/` `{texte: "Question", reponse_a: null}` | 201 ; un `Commentaire` existe sur `campagne_a` ; une notification « Nouveau message » pour `g1` ; (non-régression) | serveur |
| R2 | un message `m_a` d'`yao` sur `campagne_a` | `ama` répond `{texte: "Oui", reponse_a: m_a}` sur `campagne_a` | 201 ; la réponse est liée à `m_a` ; `yao` reçoit « Réponse à votre message » (non-régression) | serveur |
| R3 | `m_b` sur `campagne_b` | `ama` poste sur `/campagnes/<a>/commentaires/` `{texte: "x", reponse_a: m_b}` | 400 avec un message lisible sur `reponse_a` ; aucun `Commentaire` créé (compte inchangé) ; aucune notification créée pour l'auteur de `m_b` | serveur |
| R4 | `brouillon_g2` | `ama` poste `{texte: "x"}` sur `/campagnes/<brouillon_g2>/commentaires/` | refus (404 ou 403, voir Q1) ; aucun `Commentaire` ; aucune notification pour `g2` | serveur |
| R5 | `brouillon_g2` | `g2`, son propriétaire, poste sur son brouillon | selon Q2 : refusé ou accepté sans notification à lui-même ; le résultat doit être celui choisi, avec un test | serveur |
| R6 | l'identifiant 999999 | `ama` poste sur `/api/campagnes/999999/commentaires/` | **404** JSON propre (jamais 500) ; aucun `Commentaire` | serveur |
| R7 | l'identifiant 999999 | `GET /api/campagnes/999999/commentaires/` | 404 (recommandé, Q1) et non 500 ; | serveur |
| R8 | `reponse_a` = un message déjà réponse | `ama` répond à une réponse sur la bonne campagne | 400 « On ne répond pas à une réponse… » ; rien d'écrit (non-régression de `test_on_ne_repond_pas_a_une_reponse`) | serveur |
| R9 | `reponse_a` = 999999 (message inexistant) | `ama` poste | 400 (clé étrangère invalide), pas de 500 | serveur |
| R10 | sans session ou numéro non vérifié | `POST` sur `campagne_a` | 401/403 ; rien d'écrit (non-régression des tests existants) | serveur |
| R11 | une campagne `annulee` ou `terminee` | `ama` (participante) poste | comportement inchangé (201) : l'historique reste ouvert, §4 « Historique » | serveur |
| R12 | l'écran `Discussion`, `ama` connectée | elle répond à un message du fil | la réponse apparaît sous le message après rechargement ; notifications inchangées | web |
| R13 | l'écran `Discussion`, le serveur répond 400/404 à la publication | `ama` publie | le message d'erreur du serveur s'affiche en rouge sous le champ, le texte saisi n'est pas perdu | web |

R3, R4, R6, R9 sont les cas d'erreur et d'intégrité ; R10 le refus de sécurité ; R1, R2, R12 les nominaux.

### Tests automatiques attendus

Dans `backend/groupachat/echanges/tests.py`, classe `TestFilPublic` (ou `TestIntegriteDuFil`) :
- `test_on_ne_repond_pas_a_un_message_d_une_autre_campagne` (R3 ; vérifie : 400, compte de `Commentaire` identique, aucune `Notification` de genre `reponse_commentaire`) ;
- `test_on_ne_commente_pas_le_brouillon_d_un_autre` (R4 ; vérifie : statut de refus, aucun commentaire, aucune notification pour le groupeur) ;
- `test_une_campagne_inexistante_donne_404_et_non_500` (R6 ; POST ; et GET si Q1 = a) ;
- `test_repondre_a_un_message_inexistant_donne_400` (R9) ;
- `test_le_groupeur_et_le_brouillon_comme_decide` (R5, selon Q2) ;
- `test_une_campagne_close_garde_son_fil_ouvert` (R11) ;
- R1, R2, R8, R10 : tests existants (`test_un_message_notifie_le_groupeur`, `test_une_reponse_notifie_l_auteur_du_message`, `test_on_ne_repond_pas_a_une_reponse`, `test_mais_on_n_ecrit_pas_sans_compte`, `test_un_numero_non_verifie_n_ecrit_pas`) doivent rester verts, **non modifiés**.
Le client de test doit utiliser `raise_request_exception=False` si l'on veut observer un 500 sans exception ; sinon l'absence d'exception suffit. Vérifier la collecte : `python -m pytest --collect-only -q groupachat/echanges/tests.py`. R3, R4, R6 doivent échouer sur `5dc1562`.
Web (R12-R13) : contrôle navigateur, `npm run verifier`.

### Vérification d'interface

`/campagnes/<id>` > « Discussion ». États : chargement (squelette), vide (« aucun message »), erreur de publication visible (R13). À 390 px, la zone de saisie n'est pas recouverte par la barre d'action (voir [[C-009-F-005-fiche-campagne]] R5). Aucun changement de code d'écran attendu.

## Fichiers que le correctif touchera

`backend/groupachat/echanges/vues.py` (404 sur campagne inexistante via `get_object_or_404`, refus du brouillon d'autrui, vérification de campagne de `reponse_a`) · `backend/groupachat/echanges/serialiseurs.py` (la campagne de la requête passée en contexte pour `validate_reponse_a`) · `backend/groupachat/echanges/tests.py`. Frontend : **aucun** attendu.

## Questions ouvertes

**Q1. Lecture du fil d'un brouillon ou d'une campagne inexistante.** Aujourd'hui `GET` renvoie 200 (liste vide ou fil du brouillon). Options : (a) 404 pour inexistante et pour brouillon d'autrui, en lecture comme en écriture ; (b) seulement l'écriture est protégée. Recommandation : (a), c'est le sens de « un brouillon reste privé » (`catalogue/vues.py:176`) et le coût est le même helper. À noter : `CampagneVueEnsemble.retrieve` renvoie lui aussi les brouillons sans filtre (même fichier, l. 172-178) ; hors T12b, à signaler au backlog si la fiche est confirmée accessible.
**Q2. Le groupeur peut-il écrire dans le fil de son propre brouillon ?** Aucune décision. Options : (a) oui, sans notification à soi-même ; (b) non, fil fermé tant que la campagne n'est pas publiée. Recommandation : (b) : plus simple (une seule règle « brouillon : fermé »), personne ne lit ce fil avant la publication.
**Q3. Code du refus du brouillon d'autrui.** 404 (ne révèle pas l'existence du brouillon) ou 403. Recommandation : 404.

## Prêt à coder ?

**Oui**, avec les recommandations par défaut de Q1 à Q3 (404 partout, brouillon fermé). Ces trois réponses ne changent pas la structure des tests, seulement des valeurs attendues ; le développeur peut commencer et l'utilisateur ajuster.


## Décisions prises (T12b, Q6) et réalisation

- Q1 = (a), Q2 = (b), Q3 = 404 : **404 partout** pour une campagne inexistante et pour un brouillon, en lecture comme en écriture, **y compris pour le groupeur propriétaire**. Les autres statuts (`annulee`, `minimum_non_atteint`, `terminee`…) gardent leur fil, comme la fiche campagne.
- `echanges/vues.py` : `initial()` charge la campagne (`get_object_or_404`, brouillon exclu) après authentification et permissions ; elle couvre liste, création, modification, retrait et `jaime`. `perform_create` réutilise cette campagne.
- `echanges/serialiseurs.py` : `validate_reponse_a` compare la campagne du parent à `campagne_id` du contexte (400 sur `reponse_a`). La modération admin (`/api/admin/commentaires/`) est une autre vue, sans ce contexte : inchangée.
- Écran : aucun changement ; `ErreurApi` remonte le premier message de `reponse_a`.
- Hors périmètre : la fuite possible de `CampagneVueEnsemble.retrieve` est suivie par C-063 du backlog.

## Recette — 2026-10-28

**RECETTE OK** — base `c7023f4` + modifications non commitées du worktree `fix/F-009-fil-integrite`. Matrice : serveur ✅ · web ✅ · mobile —.

Serveur Django local (SQLite jetable, `charger_demo`, port 8021), vraies requêtes HTTP avec session et CSRF (`curl`). Compte de messages et de notifications relu en base après chaque refus.

| # | Observé | Verdict |
|---|---|---|
| R1 | `ama` POST camp. 1 : 201, commentaires 13→14, notifications 129→130 | ✅ |
| R2 | réponse à un message d'`yao` sur la même campagne : 201, `reponse_a` = 15, notification `reponse_commentaire` « Réponse à votre message », `lien: /campagnes/1` (reçue par `yao`) | ✅ |
| R3 | réponse à un message de la campagne 13 depuis la 1 : 400 `{"reponse_a":["Ce message n'appartient pas à la discussion de cette campagne."]}` ; compteurs inchangés (16 / 132) | ✅ |
| R4 | brouillon 12, `ama` : POST et GET 404 ; compteurs inchangés | ✅ |
| R5 | brouillon 12, son groupeur `90001122` : POST et GET 404 (Q2 = b) ; compteurs inchangés | ✅ |
| R6/R7 | campagne 999999 : POST et GET 404 JSON, jamais 500 ; compteurs inchangés | ✅ |
| R8 | réponse à une réponse : 400 « On ne répond pas à une réponse… » | ✅ |
| R9 | `reponse_a` 999999 : 400 sur `reponse_a`, pas de 500 | ✅ |
| R10 | sans session : 403, rien d'écrit | ✅ |
| R11 | campagnes 9 (terminée) et 11 (minimum non atteint) : lecture 200 et écriture 201 | ✅ |
| `jaime` | via `/campagnes/12/commentaires/<id>/jaime/` : 404 ; sur la campagne 1 en cours : 200 `jaime_par_moi: true` | ✅ |
| Modération | admin `masquer` 200 (message disparu du fil), `retablir` 200 (revenu) ; `ama` : 403 | ✅ |
| R12 | Chrome headless 390 px, build de la boutique servi par Django : écrire, répondre (sous le message), aimer fonctionnent ; aucune erreur JS | ✅ |
| R13 | réponse 400 simulée par interception réseau (corps identique au vrai 400 de R3, car l'écran n'offre pas de réponse hors campagne) : message rouge « Ce message n'appartient pas à la discussion de cette campagne. » sous le champ, texte saisi conservé. Capture : `scratchpad/t12br/discussion-390.png` | ✅ |

Tests : `python -m pytest groupachat/echanges/tests.py` relancé en fin de recette, code de sortie 0 (récapitulatif texte non capturé). Non testé : navigateur sur `annulee` (couvert côté serveur par R11).
