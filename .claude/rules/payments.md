---
paths:
  - "backend/groupachat/paiements/**"
  - "backend/groupachat/commandes/**"
  - "backend/groupachat/espaces/administration.py"
  - "backend/groupachat/espaces/groupeur.py"
---

# Paiements et transferts (Mobile Money, Flooz, T-Money, carte)

- IMPORTANT : une même demande, rejouée ou envoyée deux fois, ne débite jamais deux fois. Référence interne unique créée avant l'appel au fournisseur, et clé d'idempotence transmise.
- Montants en entiers FCFA de bout en bout ; le serveur recalcule le montant et les frais, il ne reprend jamais un montant envoyé par le client.
- États explicites (`PENDING` → `SUCCESS` / `FAILED` / `EXPIRED`), transitions autorisées listées dans le code, aucun retour en arrière ; chaque transition journalisée avec la référence.
- Le statut final vient du fournisseur (callback signé ou requête de statut), jamais de la seule réponse synchrone ni du client.
- Callback dupliqué ou arrivé avant la réponse synchrone : aucun effet supplémentaire.
- Délai dépassé sans réponse : rester `PENDING` et vérifier activement le statut ; jamais `FAILED` par supposition, l'argent a peut-être bougé.
- Débit, crédit et commission écrits dans une même transaction en base.
- Numéro de téléphone normalisé au format international et validé avant l'appel ; code PIN jamais reçu, stocké ni journalisé.
- Plafonds (par opération, par jour, par compte) vérifiés côté serveur.
- Tests obligatoires : double soumission, callback dupliqué, callback avant réponse, timeout, refus du fournisseur, montant modifié par le client.

## Dans ce dépôt
- Paiement et décaissement sont **simulés** derrière `_executer_paiement` (`paiements/services.py`) ; **la comptabilité du séquestre est réelle** : consignation, libération, remboursement, frais.
- Les statuts réels sont ceux des modèles (`Transaction.Statut`, `Decaissement.Statut`, `Sequestre.Statut`, `Participation.Statut`, `Campagne.Statut`) — les noms `PENDING/SUCCESS` ci-dessus sont génériques.
- **Séquestre par campagne**, contraintes en base contre une libération ou un remboursement supérieur au consigné ; écritures sous `@transaction.atomic` avec `select_for_update()` sur la campagne.
- **Prix figé à la commande** ; **1 500 FCFA** de frais prélevés une seule fois au décaissement ; aucun frais pour l'acheteur.
- **L'argent ne repart pas tout seul** si le minimum n'est pas atteint : le groupeur décide sous **7 jours**, faute de quoi chacun est remboursé intégralement.
- Les frais d'opérateur d'un remboursement sont à la charge de la plateforme, et tracés.
