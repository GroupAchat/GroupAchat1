---
type: decision
statut: acceptée
date: 2026-10-26
tags: [decision, carte, cahier-des-charges, mvp]
---

# Décisions de l'utilisateur sur la carte (2026-10-26)

L'utilisateur a validé la [[carte]] (reformulation et liste MVP de 31 fonctionnalités : 27 constatées, 4 partielles, 0 recettée) et tranché les seize questions de [[2026-10-26-questions-ouvertes]] en retenant les recommandations. Ce qui suit est la décision retenue ; le détail des questions reste dans la carte, section « Questions ouvertes ».

## Décisions

- **Q1 Livraison.** Retrait seul, au point de retrait. La livraison reste F-037 (hors MVP). §3 du cahier des charges à réécrire (C-003).
- **Q2 Qui décaisse.** Le groupeur demande le retrait, l'administrateur exécute (code actuel). §3 à réécrire (C-003).
- **Q3 Abonnements.** Restent reportés (F-041). Aucune ligne de code avant les trois questions de [[2026-10-26-questions-ouvertes]].
- **Q4 « Livré ou remboursé ».** Fonds libérés avant la distribution (code actuel). La promesse « bloqués jusqu'à la livraison » (§2, `FicheCampagne.tsx`) et le texte de `CampagneGroupeur.tsx` (C-8 de la carte) sont corrigés (C-009).
- **Q5 Pièces KYC.** Obligatoires : champ recto / verso dans `Profil.tsx` et obligation côté serveur. Porté par F-011.
- **Q6 Annulation par le groupeur** depuis `en_cours` ou `financee` : gardée. §9 complété (C-003).
- **Q7 Clôture anticipée** par le groupeur : gardée. Inscrite au §4 et au §9 (C-003).
- **Q8 Historique d'une campagne sortie du catalogue** : consultable par quiconque a l'adresse. §4 réécrit (C-003).
- **Q9 Refus d'un décaissement** : hors MVP. Ligne F-042 au backlog ; retiré de F-024.
- **Q10 Paiement refusé** (reprendre ou abandonner la part) : hors MVP tant que le paiement est simulé. Ligne F-043, à faire avant tout vrai opérateur.
- **Q11 Médias sans Cloudinary** : les variables `CLOUDINARY_*` sont exigées ; `CLAUDE.md` corrigé (C-004). Vérifier les variables sur achatgr.com : action de l'utilisateur (C-008).
- **Q12 Rôle à l'inscription** : pas de choix de rôle. §5 réécrit : on devient groupeur depuis son profil (C-003).
- **Q13 J+14 (F-031).** Relances par notification seule à J+3 et J+7. À J+14, la part non retirée passe dans un statut distinct « réputée livrée », non comptée dans les participants servis. La campagne passe `terminee` et la réputation du groupeur est créditée.
- **Q14 Statut `decaissee`** : retiré du §9 et du modèle, par une migration revue par `archi-backend` (C-005).
- **Q15 Planification horaire sur Coolify** : en attente, à vérifier par l'utilisateur (C-007).
- **Q16 Plafond du séquestre** : contrainte `montant_libere + montant_rembourse <= montant_consigne` à ajouter en base (C-006). Migration à valider par l'utilisateur, puis à soumettre à `regles-auditor`.

## Conséquences sur le backlog
- F-011 : « pièces obligatoires ». F-031 : règle J+14 ci-dessus. Les deux restent `à faire` (partielles).
- F-032 et F-033 : `terminée` → `constatée` (aucune recette jouée).
- F-034 : `terminée` → `partielle` (route sans écran).
- F-037 : `bloquée` → `à faire`, hors MVP : la contradiction §3 / §4 est tranchée (Q1).
- F-042 (Q9) et F-043 (Q10) créés, hors MVP.
- Chantiers C-003 à C-009 créés (voir [[backlog]]).

## Conséquences sur la mission en cours
Aucune. Aucune mission n'est ouverte (`07-missions/missions.md`) : les chantiers de réécriture et de correction ne sont pas encore proposés comme mission. Le chef de projet les proposera, après accord de l'utilisateur.

## Décisions après l'état des lieux (2026-10-26)

Décisions de l'utilisateur après la recette T1 ([[recette-etat-des-lieux-2026-10-26]]). Tâches de [[M-001-terminer-le-mvp]] : T9 à T12.

- **D-F024 : double paiement sur campagne annulée** ([[2026-10-26-recette-failles]]). L'annulation d'une campagne refuse automatiquement le décaissement en attente, avec motif et notification. Un décaissement ne s'exécute que si la campagne est `financee`, sous verrou (`select_for_update`). Annuler une campagne dont le décaissement est exécuté est interdit. Ce refus automatique n'est pas le refus manuel de F-042, qui reste hors MVP (Q9). Tâche : T10.
- **D-F010 : avis modifiables par des tiers**. Seul l'auteur d'un avis le modifie ou le supprime. Tout autre, groupeur compris, reçoit 403. Le groupeur garde son droit de réponse (F-020). Tâche : T11.
- **D-F030 : fuite des pièces KYC**. Traitée en urgence, via `staging` (branche `fix/F-030-fuite-kyc`). L'utilisateur avance `master` et redéploie lui-même. Si de vraies pièces sont en production, elles sont à considérer comme exposées. Tâche : T9.
