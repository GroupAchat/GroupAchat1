---
type: decision
statut: tranchée
date: 2026-10-26
tags: [decision, cahier-des-charges]
---

# Questions ouvertes du cahier des charges

**Tranchée le 2026-10-26** : l'utilisateur a retenu les recommandations. Le détail des décisions, et ce qu'elles entraînent au backlog et dans le cahier des charges, est dans [[2026-10-26-decisions-carte]] ; la carte porte les réponses sous « Questions ouvertes » ([[carte]]).

Points que le code ne peut pas trancher seul. Aucun agent ne choisit à la place de l'utilisateur.

## 1. Livraison ou retrait ? (bloque [[backlog]] F-037)
- §3 (groupeur, Distribution) : « le participant décide d'être livré ou bien vient lui-même récupérer ».
- §4 (Distribution) : « pas de flotte de livreurs. Le groupeur, ou la personne qu'il désigne, remet les colis au point de retrait ».
- À trancher : qui livre, qui paie la livraison, et comment le code de retrait s'applique à une livraison à domicile.
- **Décision (2026-10-26)** : retrait seul, au point de retrait. La livraison reste F-037, hors MVP. §3 à réécrire.

## 2. Qui décaisse ?
- §3 (groupeur) : « retire 100 % des fonds en une fois ».
- §3 (administrateur) et §6 : « libère le montant », « décaissement : action administrateur ».
- Ce que fait le code : le groupeur **demande** (`demander-retrait`), l'administrateur **exécute** (`executer_decaissement`). Compatible avec les deux lectures ; à confirmer pour réécrire le §3.
- **Décision (2026-10-26)** : le groupeur demande, l'administrateur exécute. §3 à réécrire.

## 3. Abonnements des groupeurs (F-041, reportée)
Demandés puis mis de côté le 2026-10-26. Avant toute ligne de code :
1. L'abonnement conditionne-t-il la création ou la publication d'une campagne ?
2. Remplace-t-il les 1 500 FCFA par campagne, ou s'y ajoute-t-il ?
3. Un groupeur dont le KYC est en attente voit-il déjà les formules ?
Et réécrire §2 (« outil gratuit »), §4 (« aucun abonnement ») et le texte de `CampagneGroupeur.tsx` (« Aucun abonnement, aucune commission »).
- **Décision (2026-10-26)** : restent reportés (F-041). Les trois questions restent ouvertes pour plus tard.
