---
type: fonctionnalite
id: C-011-C-013
statut: à faire
couvre: [F-005, F-017, F-019]
mission: M-001 (T13)
---

# C-011 et C-013 : confirmations perdues, prix affiché faux

Couvre F-005 (participer et payer), F-017 (demander le retrait), F-019 (valider un code de retrait). Source : `backlog.md` (C-011, C-013), `recette-etat-des-lieux-2026-10-26.md`, recette T6 de `C-009-F-005-fiche-campagne.md` (R2 « pas pu tester à l'écran »), `CAHIER_DES_CHARGES.md` (prix figé à la commande).

## Les deux règles et l'état constaté

**Règle 1 (C-011).** Quand une action réussit, l'utilisateur voit sa confirmation (paiement + « Voir mon QR », « Demande enregistrée », « Colis remis à X ») **jusqu'à ce qu'il la ferme**, même si la page se recharge derrière.
État : jamais affichée. Le paiement, la demande et la validation ont bien lieu.

**Règle 2 (C-013, décision utilisateur 2026-10-28).** L'écran affiche le prix que le serveur facturera : le palier atteint **en comptant la quantité demandée**. Le prix reste figé à la commande ; aucune règle serveur ne change.
État : l'écran affiche `prix_courant` (palier atteint par les pièces **déjà payées**) fois la quantité (`FicheCampagne.tsx:83`, `:715`), alors que le serveur facture `prix_pour_quantite(quantite_reservee + quantite)` (`commandes/serialiseurs.py:108-110`). Cas relevé : 35 000 affichés, 32 000 facturés.

## Cause exacte de C-011

`useRequete` (`frontend/commun/src/outils/requetes.ts:23-43`) met `chargement` à `true` au début de **chaque** `charger()`, y compris un `recharger()`, et ne le remet à `false` qu'à la fin. Les deux pages font ensuite `if (chargement) return <Squelette…/>` avant le JSX principal :
- `FicheCampagne.tsx:69`, puis `FeuilleParticipation` (rendue plus bas, `:533`) ;
- `CampagneGroupeur.tsx:85-92`, puis `FeuilleRetrait` (`:356`) et `FeuilleScan` (`:362`).

Les feuilles sont des enfants du reste de la page : le squelette les **démonte**. Leur état local (`reussite` `FicheCampagne.tsx:~703`, `resultat` `CampagneGroupeur.tsx:488`, `valide` `:590`) est détruit. Or ces états sont posés **avant** `await surSucces()` (donc avant `recharger()`), puis la page se remonte avec des `useState` neufs : confirmation perdue. Pour `FeuilleParticipation`, `surSucces` ferme en plus la feuille (`setFeuilleOuverte(false)`). Un seul mécanisme, trois écrans.

Pistes (au choix de `fonctionnalite`, la fiche n'impose pas le correctif) : ne montrer le squelette qu'au **premier** chargement (`chargement && !donnees`), ou faire que `recharger` ne remette pas `chargement` à `true` ; et dans `FicheCampagne`, ne pas fermer la feuille de réussite dans `surSucces`. La première piste corrige les trois écrans d'un coup, mais change `useRequete` pour tous ses usages : vérifier que les écrans qui comptent sur le squelette au changement de `chemin` (autre `id`) le gardent.

## C-013 : comment l'écran obtient le bon prix

Constats de lecture :
- Le serveur expose déjà les paliers dans le détail d'une campagne (`PalierPrixSerialiseur` : `quantite_min`, `prix_unitaire` ; `catalogue/serialiseurs.py:110`, `:216`), avec `prix_unitaire`, `quantite_reservee`, et le type `Campagne.paliers` existe (`commun/src/api/types.ts:150`). L'écran les lit déjà (tableau de paliers, `FicheCampagne.tsx:248-290`).
- La règle serveur est une fonction simple (`Campagne.prix_pour_quantite`, `catalogue/models.py:448-462`) : le palier franchi de plus grand seuil, sinon `prix_unitaire`. Les pièces comptées sont les pièces **payées** (`quantite_reservee`).

Options :
- (a) l'écran refait le calcul avec sa propre logique dispersée : duplication, divergence possible.
- (b) **recommandée** : une seule fonction pure côté socle (`commun/src/outils/`, ex. `prix.ts::prixPourQuantite(prix_unitaire, paliers, quantite_reservee + quantite)`) qui reprend exactement la règle serveur, appelée par `FicheCampagne` pour la ligne « prix », le total et le bouton de paiement. Aucun changement de contrat d'API. Le risque de divergence est borné par un test de contrat (voir plus bas) qui compare client et serveur sur les mêmes cas.
- (c) champ ou route de devis serveur : un seul calcul, mais changement de contrat et un aller-retour de plus à chaque changement de quantité (réseau mesuré).

Recommandation : **(b)**. Moins risquée à livrer demain, sans changement d'API ; la règle ne vit côté client que dans une fonction testée. Limite connue : un autre acheteur qui paie entre l'affichage et la validation peut faire franchir un palier ; le serveur recalcule à la création de la participation et facture alors un prix **plus bas ou égal** (jamais plus haut, les paliers étant moins chers que le prix affiché). La feuille doit donc s'appuyer sur le prix renvoyé par `POST /participations/` (`prix_unitaire_applique`, `montant_total`) pour la confirmation, pas sur l'affichage préalable (voir R12).

## Recette

Rôles : acheteur au numéro vérifié, groupeur de la campagne · Couches : serveur non (aucune règle ne change ; un test de contrat est conseillé) · web oui (boutique) · mobile — · Source : règles ci-dessus, `CAHIER_DES_CHARGES.md`.

Jeu de test (à créer par fixture ou par `shell` en base jetable, pas dans `charger_demo` sauf choix de `fonctionnalite` avec incrément de `VERSION_DEMO`) : campagne `en_cours`, `prix_unitaire` 7 000, paliers : 10 pièces → 6 500, 20 pièces → 6 000 ; minimum 10 ; 8 pièces déjà payées par d'autres. Les montants sont donc : 1 pièce → total 8+1=9 < 10 : 7 000 ; 2 pièces → total 10 : 6 500 ; 3 pièces → 6 500 ; 12 pièces → total 20 : 6 000.

### Scénarios acheteur : prix exact avant de payer

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | 8 pièces payées, acheteur connecté, quantité 1 (juste en dessous du palier) | il ouvre la feuille « Participer » | prix unitaire affiché 7 000 FCFA, total 7 000 FCFA ; après paiement, `GET /api/participations/` donne `prix_unitaire_applique` 7000, `montant_total` 7000 | web |
| R2 | même état, quantité 2 (pile au seuil : 8+2 = 10) | il passe la quantité de 1 à 2 | prix unitaire 6 500, total 13 000 FCFA, affichés avant tout clic sur Payer ; le serveur facture `prix_unitaire_applique` 6500, `montant_total` 13000 | web |
| R3 | même état, quantité 12 (franchit le palier à 20) | il saisit 12 | prix unitaire 6 000, total 72 000 FCFA ; serveur : 6000 et 72000 | web |
| R4 | même état, quantité 3 (au-dessus du seuil, sous le suivant) | il saisit 3 | 6 500 par pièce, total 19 500 | web |
| R5 | aucun palier franchi par les pièces payées mais pas de palier (campagne sans palier) | quantité 5 | prix unitaire = `prix_unitaire`, total = ×5, jamais NaN ni vide | web |
| R6 | cas de C-013 d'origine (35 000 affichés / 32 000 facturés) | il compare l'écran, la réponse de `POST /participations/` et sa ligne dans Mes achats | les trois montants sont identiques (aucun écart écran / serveur) | web |
| R7 | la quantité change de 3 à 1 puis revient à 3 | il alterne | le prix suit à chaque saisie, sans rechargement réseau ; la ligne « prix » et le total du bouton Payer restent cohérents | web |
| R8 | il reste moins de pièces que la quantité saisie (campagne à stock maximal) | il dépasse le reste | message serveur lisible (« Il ne reste que N pièce(s). »), rien n'est écrit, aucun total négatif ou absurde | web + serveur |
| R9 | un visiteur non connecté | il ouvre la feuille | prix affiché comme pour l'acheteur ; l'invite à se connecter, pas de 403 vu à l'écran | web |

Contrôle de non-régression sur le prix figé : R10 | un palier est franchi après le paiement de R2 | l'acheteur rouvre « Mes achats » | sa part reste à 6 500 (prix figé), pas réécrite | web + serveur.

### Scénarios acheteur : confirmation de paiement et QR

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R11 | acheteur connecté, numéro vérifié, campagne en cours | il paie (TMoney simulé) | la feuille titrée « Paiement confirmé » reste affichée après le rechargement de la fiche : texte « Votre part est consignée », montant consigné, code de retrait, bouton « Voir mon QR code » ; elle ne se ferme que par action de l'utilisateur ; la jauge derrière est à jour (réservé +quantité) | web |
| R12 | prix changé entre l'ouverture de la feuille et le clic (un autre acheteur a franchi le palier) | il valide | le montant consigné affiché est celui de la réponse serveur (`montant_total`), le plus bas des deux ; pas de message d'erreur | web |
| R13 | feuille de réussite ouverte | il clique sur « Voir mon QR code » | le QR s'affiche (route atteinte sans 404) ; retour possible | web |
| R14 | feuille de réussite | il la ferme puis rouvre « Participer » | la feuille reparaît en formulaire neuf (pas de réussite fantôme) ; si la fiche indique déjà sa part, le comportement est celui d'avant (non régressé) | web |
| R15 | paiement refusé (échec simulé, numéro incorrect, ou ressource d'autrui : autre acheteur ou groupeur) | il paie / appelle `POST /participations/<id>/payer/` d'une part qui n'est pas la sienne | message serveur lisible dans la feuille, aucune confirmation, rien n'est consigné (séquestre inchangé) ; part d'autrui : 403 ou 404, rien d'écrit | web + serveur |
| R16 | groupeur de la campagne | il ouvre sa propre fiche côté acheteur | pas de bouton « Participer » (non régressé) | web |

### Scénarios groupeur

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R17 | campagne du groupeur au statut permettant le retrait, fonds disponibles | il clique « Demander le retrait » et confirme | la feuille « Demande enregistrée » reste affichée après le rechargement de la page (montant net, frais de 1 500 FCFA lisibles) jusqu'à fermeture ; derrière, la campagne reflète la demande | web |
| R18 | retrait déjà demandé (état post R17) | il rouvre la page | pas de feuille fantôme ; le bouton « Demander le retrait » n'est pas l'objet de cette fiche (C-012) | web |
| R19 | un acheteur a payé et possède un code de retrait valide | le groupeur saisit le code dans « Valider un retrait » | la bannière « Colis remis à <acheteur> » (quantité incluse) reste affichée après le rechargement de la page et des participants ; la participation passe à « remise » dans la liste | web |
| R20 | code erroné, déjà utilisé, ou campagne d'un autre groupeur | il valide | message d'erreur lisible dans la feuille, aucune bannière de succès, rien n'est écrit | web + serveur |
| R21 | acheteur (autre rôle) | il appelle `/api/groupeur/campagnes/<id>/demander-retrait/` et `/retrait/` | 403, rien d'écrit | serveur |
| R22 | groupeur d'une autre campagne | mêmes appels sur la campagne d'autrui | 403 ou 404, rien d'écrit | serveur |

### 390 px, chargement, erreur

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R23 | téléphone 390×844 | R11, R17, R19 rejoués | la feuille de confirmation tient dans l'écran, le bouton de fermeture est atteignable (`elementFromPoint` au centre du bouton renvoie le bouton, pas la barre d'onglets) ; le prix de R2 tient sur une ligne sans débordement horizontal (`scrollWidth` ≤ 390) ; capture jointe | web |
| R24 | premier chargement de la fiche / de la page groupeur | la page s'ouvre | le squelette s'affiche (non régressé) ; pendant un **rechargement** après une action, la page (contenu + feuille) reste montée : pas de retour au squelette | web |
| R25 | autre `id` de campagne (navigation d'une fiche à l'autre) | le chemin change | le squelette réapparaît, aucune donnée de l'ancienne campagne ni confirmation de l'ancienne ne s'affiche | web |
| R26 | le serveur coupe pendant le rechargement qui suit un paiement réussi | l'action a réussi mais `recharger()` échoue | la confirmation reste affichée ; l'erreur de rechargement n'efface pas la page et n'annule pas la confirmation ; message lisible. À défaut de règle écrite : voir question 3 | web |
| R27 | campagne introuvable (id inconnu) | l'URL est ouverte | message « Campagne introuvable » (non régressé), pas de feuille | web |

27 scénarios.

### Tests automatiques attendus

Serveur : aucune règle ne change, donc pas de nouveau test de règle. Un test de contrat est conseillé car l'écran dépend de ces champs :
- `groupachat/catalogue/tests.py::test_le_detail_d_une_campagne_expose_les_paliers_et_le_prix_unitaire` : `GET /api/catalogue/campagnes/<id>/` contient `prix_unitaire`, `quantite_reservee` et `paliers` (liste de `quantite_min` / `prix_unitaire`) (R1 à R5).
- `groupachat/tests/test_prix_affiche_et_facture.py::test_le_prix_facture_suit_le_palier_atteint_avec_la_quantite_demandee` : pour les quatre cas du jeu de test (1, 2, 3, 12 pièces, 8 déjà payées), `POST /api/participations/` renvoie `prix_unitaire_applique` et `montant_total` attendus, **écrits en dur** dans le test et réutilisés comme table d'entrée du test client (R1 à R4, R6, R10).
- Existants à relancer sans modification : `pytest groupachat/commandes groupachat/paiements groupachat/espaces` (prix figé, paiement, retrait ; R15, R20 à R22). Vérifier qu'ils sont collectés (`--collect-only -q`).

Client : `frontend/` n'a pas de banc de tests déclaré dans ce dossier de fiche. La preuve est par navigateur (Chrome headless piloté, comme T6 : vraies sessions, base jetable + `charger_demo`, Django et Vite locaux, MutationObserver pour attester que le texte de confirmation apparaît et **reste**). Si `fonctionnalite` ajoute la fonction pure `prixPourQuantite`, un test de table sur les mêmes quatre cas que le test serveur est attendu **si un lanceur de tests existe déjà** ; sinon, la table des cas est vérifiée par R1 à R4 à l'écran et la question 2 est tranchée.
- Construction : `npm run verifier` (typage des deux interfaces) doit passer.

### Vérification d'interface

- `FicheCampagne` : feuille « Participer à la campagne » (prix unitaire et total qui suivent la quantité), puis feuille « Paiement confirmé » avec « Voir mon QR code ». Chargement : squelette au premier chargement seulement ; erreur : message serveur dans la feuille ; vide : sans objet.
- `CampagneGroupeur` : feuille « Demande enregistrée », bannière « Colis remis à X ». Mêmes états.
- Contrôle de cohérence : le prix à l'écran, `prix_unitaire_applique` de la réponse de création, et la ligne de « Mes achats » sont identiques (R6).

## Questions ouvertes

1. **Option pour le prix : (a), (b) ou (c) ?** Recommandation : (b), fonction pure du socle appliquant la règle serveur aux paliers déjà exposés ; aucun changement d'API. (c) change le contrat d'API (nouvelle route ou champ de devis) : **à l'utilisateur** s'il la préfère, car cela ajoute un appel réseau à chaque changement de quantité.
2. **Le client a-t-il un lanceur de tests ?** Non constaté. Si aucun, la preuve du calcul côté client reste le navigateur (R1 à R4) plus le test de contrat serveur ; acceptable pour demain, à confirmer.
3. **Rechargement qui échoue juste après un succès (R26).** Aucune règle écrite : la confirmation doit-elle rester seule, ou la page afficher un bandeau d'erreur ? À trancher ; en attendant R26 vérifie seulement que la confirmation n'est pas perdue.
4. **Prix qui baisse entre l'ouverture de la feuille et le clic (R12).** Le serveur facture le prix du moment (jamais plus que l'affichage). L'écran doit-il le signaler (« le prix est passé à X ») ou afficher simplement le montant consigné ? Recommandation : afficher le montant consigné de la réponse, sans message.
5. **Jeu de test.** Les chiffres ci-dessus (7 000 / 6 500 / 6 000) sont un jeu de recette, pas des données de `charger_demo`. Faut-il l'ajouter à la démo (incrément de `VERSION_DEMO`) ? Recommandation : non, fixture de test uniquement. Le cas 35 000 / 32 000 de la recette T1 vient d'une campagne de démo dont les paliers ne sont pas relus ici : R6 le rejoue sur la campagne de démo concernée.

## Prêt à coder ?

**Oui, avec la solution (b)** pour C-013 : tous les scénarios sont vérifiables, la cause de C-011 est établie, et aucune question ne bloque (1 et 3 ont une recommandation par défaut). Si l'utilisateur choisit (c), la fiche doit être reprise (contrat d'API, test serveur de la route).
