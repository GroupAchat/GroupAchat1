---
type: fonctionnalite
id: C-009-F-005
statut: terminée (C-009) ; F-005 partielle
date: 2026-10-28
tags: [fonctionnalite, C-009, F-005, C-8, C-4, textes, mobile, fiche-campagne, mvp]
---

# C-009 + F-005 (part) — Textes de la promesse et bouton « Participer » à 390 px

Tâches T6 et T12a de [[M-001-terminer-le-mvp]], faites **dans la même boucle** (mêmes fichiers). Rôles : Acheteur (fiche), Groupeur (écran de campagne). Couches : serveur **non** · web boutique **oui** · mobile non (pas d'application dans ce dépôt). Sources : [[2026-10-26-decisions-carte]] Q4 ; [[carte]] C-4 et C-8 ; `CAHIER_DES_CHARGES.md` §4 ; [[recette-etat-des-lieux-2026-10-26]] n°4.
Hors périmètre : C-011 (confirmation perdue après `recharger()`), C-013 (prix affiché ≠ facturé), C-022, F-041 (abonnements), réécriture du §2 du cahier (C-003, `obsidian-mapper`).

## La règle

Q4, option (a) : **les fonds sont libérés avant la distribution.** Dans le code (`paiements/services.py`), la part est consignée au paiement ; le groupeur demande le retrait une fois la campagne `financee`, l'administrateur exécute, le séquestre passe `libere` et la campagne `approvisionnement`. Après cela, `annuler` est refusé (F-024). La promesse est donc : **remboursé si le groupage échoue ou est annulé avant ce versement ; après, la preuve de remise est le code de retrait.** Aucun écran ne doit dire « bloqué jusqu'à la livraison ». Le texte suit la règle, pas l'inverse. La règle du minimum non atteint (§4) : l'argent ne repart pas tout seul, le groupeur décide, sans réponse sous `DELAI_DECISION_JOURS` (7) les participants sont remboursés.

## État constaté dans le code (`5dc1562`)

| Lieu | Texte actuel | Faux parce que |
|---|---|---|
| `FicheCampagne.tsx:372-374` | « **Livré ou remboursé.** Votre part reste consignée jusqu'à la livraison. » | les fonds partent au décaissement, avant la distribution (C-4) |
| `FicheCampagne.tsx:758` | « {montant} bloqués jusqu'à la livraison. Votre code de retrait vous attend. » | idem |
| `CampagneGroupeur.tsx:171` (statut `en_cours`, minimum non atteint) | « …Au-delà de la date limite, la campagne est annulée et tout le monde est remboursé. » | contredit le §4 : pas d'annulation d'office, le groupeur décide (C-8) |
| `FicheCampagne.tsx:515` (barre `fixed bottom-0 z-30`) et `Coque.tsx:125` (`BarreOnglets`, `fixed bottom-0 z-40`, `md:hidden`) | la barre d'onglets recouvre la barre d'action ; seuls ~8 px du bouton « Participer » sont touchables à 390 px (recette T1). Correct à partir de 768 px | deux barres fixes au même bas d'écran |

Textes **déjà justes**, à ne pas toucher : `FicheCampagne.tsx:186` (« Votre part reste consignée : le groupeur peut encore maintenir »), `CampagneGroupeur.tsx:189` (« Sans réponse, ils seront remboursés automatiquement »), `FicheCampagne.tsx:861` (démonstration), `CampagneGroupeur.tsx:555-557` (frais fixes ; « Aucun abonnement » relève de F-041).

### Textes proposés (à confirmer : Q1)

- `FicheCampagne.tsx:373` : « **Remboursé si le groupage échoue.** Votre part est consignée tant que la collecte n'est pas acquise. Une fois les fonds remis au groupeur, votre code de retrait prouve la remise du colis. »
- `FicheCampagne.tsx:758` : « {montant} consignés. Ils ne sont remis au groupeur qu'une fois la collecte réussie. Votre code de retrait vous attend. »
- `CampagneGroupeur.tsx:171` : « Encore N pièces avant le minimum. À la date limite, vous déciderez de maintenir la commande ou d'y renoncer (remboursement). Sans réponse sous 7 jours, les participants sont remboursés. » (le 7 vient de `DELAI_DECISION_JOURS` ; le texte actuel de la ligne 189 l'ignore déjà, à garder cohérent.)

## Recette

Rôle : Acheteur, Groupeur, Visiteur · Couches : web boutique (uniquement) · Source : décisions Q4, carte C-4/C-8, §4.

### Scénarios

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | une campagne `en_cours`, un acheteur connecté (numéro vérifié) | il ouvre la fiche, bloc de garantie | le texte ne contient plus « jusqu'à la livraison » ; il dit remboursement si le groupage échoue et remise du colis contre code | web |
| R2 | le même acheteur participe et paie (simulé) | la feuille de réussite s'affiche | « Votre part est consignée » est suivi du montant sans « bloqués jusqu'à la livraison » ; le code de retrait est affiché | web |
| R3 | le groupeur de la campagne, statut `en_cours`, minimum non atteint | il ouvre `/groupeur/campagnes/<id>` | le texte ne contient plus « la campagne est annulée et tout le monde est remboursé » ; il annonce sa décision à la date limite et le remboursement après 7 jours sans réponse | web |
| R4 | un téléphone de 390 × 844 px, campagne `en_cours`, acheteur connecté (ou visiteur : la barre est affichée, `ouverte && !estLeGroupeur`) | il ouvre la fiche, défile en bas | le bouton « Participer » est entièrement visible et son centre reçoit le toucher : `document.elementFromPoint` au centre du bouton renvoie le bouton (ou un descendant), pas la barre d'onglets ; un clic ouvre la feuille de participation | web |
| R5 | même téléphone | il défile jusqu'à la fin de la fiche | le dernier contenu (fil de discussion) n'est masqué ni par la barre d'action ni par la barre d'onglets | web |
| R6 | un écran de 768 px, puis 1280 px | il ouvre la fiche | à 768 px une seule barre en bas (onglets masqués dès `md`, barre d'action jusqu'à `lg`), bouton touchable ; à 1280 px le bouton de la colonne latérale (`hidden lg:flex`) est touchable et la barre mobile absente | web |
| R7 | le groupeur de la campagne ouvre sa propre fiche à 390 px | il défile | aucune barre « Participer » (`estLeGroupeur`) : non-régression | web |
| R8 | une campagne à `ouverte` faux (échue, annulée, minimum non atteint) | l'acheteur ouvre la fiche à 390 px | pas de barre « Participer » ; le bandeau d'état s'affiche, le texte de `FicheCampagne.tsx:186` est inchangé | web |

R-cas d'erreur : sans objet pour les textes (aucune écriture). R4 couvre le défaut de sécurité d'usage (action inatteignable) ; R7 est le refus de rôle côté écran.

### Tests automatiques attendus

Le serveur n'est pas touché : **aucun test pytest**. `frontend/` n'a pas de test unitaire ; la preuve passe par :
- `cd frontend && npm run verifier` (typage des deux interfaces) vert ;
- une recherche négative reproductible, à joindre au rapport de recette : `grep -rn "jusqu'à la livraison\|tout le monde est remboursé" frontend/boutique/src` ne renvoie que les occurrences décidées en Q1 (zéro dans les trois fichiers de la tâche) ;
- R4 à R6 en navigateur : `npx playwright screenshot` à 390 px (capture jointe) et un contrôle `elementFromPoint` rejoué à la main ou par script jetable (hors dépôt).

### Vérification d'interface

Écrans : `/campagnes/<id>` (acheteur, visiteur), `/groupeur/campagnes/<id>`. États : chargement (squelette), erreur et vide inchangés. Mobile d'abord, 390 px, thème clair puis sombre pour la lisibilité des trois textes. Le correctif de R4 ne doit pas casser `env(safe-area-inset-bottom)`.

## Fichiers que le correctif touchera

`frontend/boutique/src/pages/FicheCampagne.tsx` (l. 373-374, 758, barre l. 515 ; éventuellement un espace bas de page) · `frontend/boutique/src/pages/groupeur/CampagneGroupeur.tsx` (l. 171) · éventuellement `frontend/boutique/src/composants/Coque.tsx` (hauteur de la barre d'onglets, si le décalage de la barre d'action en dépend). Si Q1 est élargie : `Accueil.tsx` (l. 179, 189, 215), `MesAchats.tsx` (l. 60, 318).

## Questions ouvertes

**Q1. Quels textes, et quel libellé ?** Aucune décision n'écrit les nouveaux mots ; Q4 dit seulement de corriger. Je propose ceux ci-dessus. Le titre « Livré ou remboursé » (cahier §2, slogan) contredit aussi Q4 : l'enlever de la fiche (proposé) ou le garder avec une phrase corrective. Recommandation : remplacer par « Remboursé si le groupage échoue », car « livré » n'est garanti par aucune règle.
**Q2. Étendre aux mêmes promesses ailleurs ?** `Accueil.tsx:179` (« Bloqué jusqu'à la livraison »), `:189`, `:215` (« reste consigné jusqu'à ce que vous ayez votre colis »), `MesAchats.tsx:60` et `:318` (« jusqu'à la livraison ») disent la même chose fausse et ne sont pas dans la liste de la tâche. Recommandation : oui, dans cette boucle (texte seul, mêmes mots), sinon la promesse reste contradictoire d'un écran à l'autre.

## Prêt à coder ?

**Oui pour R4 à R8 (F-005).** **Pour R1 à R3 : après réponse à Q1** (textes à valider, sinon le développeur invente la promesse). Q2 ne bloque pas.

## Recette — 2026-10-28

**RECETTE OK** (avec une réserve : R2 non observable à l'écran, voir ci-dessous) · commit de base `5dc1562`, diff non commité de 7 fichiers · matrice : serveur — · web boutique ✅ · mobile —

Environnement : base SQLite jetable + `charger_demo`, Django 127.0.0.1:8031, Vite 5193 (proxy), Chrome headless piloté par CDP, vraies sessions (acheteurs 91002233 / 92003344 / 93004455, groupeur 90001122, visiteur). Campagne 3 passée à l'échéance dans la base jetable pour R8. Captures : `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/37d3c70e-6597-49b8-bb11-132f1e1eb6a5/scratchpad/t6r/shots/`. Tout arrêté, vérifié avec `ss`.

| # | Verdict | Preuve |
|---|---|---|
| R1 | OK | fiche campagne 6, 5, 4 à 390/768/1280 px : « Remboursé si le groupage échoue. Votre part est consignée tant que la collecte n'est pas acquise. Une fois les fonds remis au groupeur, votre code de retrait prouve la remise du colis. » |
| R2 | **Pas pu tester à l'écran** | paiement effectué (réservé +1 : 3→4, 16→18) mais la feuille « Paiement confirmé » ne s'affiche jamais (observation par MutationObserver, texte absent) : c'est C-011 (`recharger()`), hors périmètre. Le texte neuf est lu dans le source (`FicheCampagne.tsx:759`) uniquement. À rejouer quand C-011 sera corrigé. |
| R3 | OK | `/groupeur/campagnes/5` et `/3` : « Encore 4 pièces avant le minimum. À la date limite, vous déciderez de maintenir la commande ou d'y renoncer (remboursement). Sans réponse sous 7 jours, les participants sont remboursés. » Aucune « annulée et tout le monde est remboursé ». |
| R4 | OK | 390×844, acheteur et visiteur : bouton de la barre à y 712–768, onglets à y 779 ; `elementFromPoint` au centre (252,740) = le bouton. Clic réel (Input.dispatchMouseEvent) : la feuille « Participer à la campagne » s'ouvre (acheteur) ; dialogue ouvert aussi pour le visiteur. |
| R5 | OK | bas de page à 390 px : « Pas encore de message » (fil) visible, puis « En résumé » et le bouton, au-dessus de la barre d'action et des onglets (`shots/acheteur-fiche-bas-390.png`). |
| R6 | OK | 768 px : une seule barre (onglets absents), bouton à y 956–1012 sur 1024, `elementFromPoint` OK. 1280 px : pas de barre mobile, bouton latéral touchable (ok). |
| R7 | OK | groupeur sur `/campagnes/1` à 390 px : aucune barre, 0 bouton « Participer » (`R7-groupeur-fiche-bas-390.png`). |
| R8 | OK | acheteur, campagnes 3 (échue), 11 (minimum non atteint), 9 (terminée) : 0 barre, 0 bouton « Participer » ; sur la 11, texte « Votre part reste consignée : le groupeur peut encore maintenir la commande » inchangé. |
| Q2 | OK | Accueil (1280 px, bandeau : « Remis au groupeur une fois la collecte réussie », « Remboursé si le groupage échoue… sous 7 jours », phrase d'accroche), MesAchats vide/détail, NouvelleCampagne (« En dessous, vous déciderez de maintenir la commande ou de rembourser. ») : textes présents. |
| Textes faux | OK | `grep` de « jusqu'à la livraison », « tout le monde est remboursé », « Livré ou remboursé », « jusqu'à ce que vous ayez votre colis » sur `frontend/*/src` : aucune occurrence ; absents aussi du texte rendu de Accueil, MesAchats, Catalogue, fiches, écran groupeur. |
| Non-régression | OK | 390 px : bas de `MesAchats` (dernier élément y 719, onglets 779), `Catalogue` (723/779), `CampagneGroupeur` (719/779) non masqués. |

Constats sans gravité : à 390 px le bandeau de l'accueil (textes Q2) n'est pas affiché (flux plein écran), les textes ne se lisent qu'à partir de la largeur de bureau ; la fiche d'une campagne échue (3) ou terminée (9) garde le bloc « Remboursé si le groupage échoue » : cohérent avec R8, qui ne le contredit pas. Non joués : thème sombre ; `env(safe-area-inset-bottom)` non mesurable en headless (la formule `calc(var(--hauteur-onglets) + env(...))` est dans `index.css`).

## Livraison — 2026-10-28

Commit `04a86fd` (« Corrige la promesse affichée et dégage le bouton Participer sur mobile »), fusionné dans `staging`. T6 terminée (C-009) : textes de la promesse corrigés, décisions Q1 et Q2 ([[2026-10-28-decisions-t6-t11-t12]]) ; `Accueil.tsx`, `MesAchats.tsx` et `NouvelleCampagne.tsx` ajoutés au périmètre. T12a (F-005, bouton à 390 px) livrée dans la même boucle. Reste de F-005 : C-011 et C-013, T13 de [[M-001-terminer-le-mvp]]. Réserve R2 : feuille « Paiement confirmé » non observée, à rejouer après T13. « Vérifier » sur `staging` : `406 passed, 9 skipped in 2072.38s`, `CHECK: OK (complet)`.
