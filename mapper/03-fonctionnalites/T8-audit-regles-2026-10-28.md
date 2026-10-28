---
type: audit
statut: incomplet
date: 2026-10-28
tags: [audit, T8, M-001, securite]
---

# T8 — Audit des règles (regles-auditor) : constats repris

**Rapport complet non conservé.** L'audit a été exécuté (tâche T8 de [[M-001-terminer-le-mvp]]), mais son rapport n'a pas été consigné dans `mapper/`. L'archiviste ne connaît les constats que par la fiche [[T15-securite-et-configuration]], qui les cite. Ce qui suit reprend cette fiche ; les points n'ont pas été revérifiés dans le code à la date de la note. Ce n'est pas le rapport de l'audit.

## Points bloquants

- **B-1** : la route de renvoi de code (`api.py:89` → `RenvoiCodeVue`, `comptes/vues.py:153-172`) renvoie le code dans la réponse.
- **B-2** : le service d'envoi journalise le numéro et le code (`comptes/services.py:51`).
- **B-3** : `DJANGO_DEBUG` vaut « 1 » par défaut (`backend/config/settings.py:26`).

B-1 et B-2 disparaissent avec l'étape du code SMS, supprimée par décision de l'utilisateur du 2026-10-28 (T15, suspendue). B-3 reste à traiter.

## Points non bloquants

- **I-3** : `.env.exemple` l. 133 met `VITE_API_URL=http://localhost:8000/api`, une adresse absolue. CLAUDE.md exige qu'elle reste vide.
- **I-5**, **I-6**, **M-1** : la fiche T15 cite ces identifiants sans les décrire. Le détail n'est pas conservé ici.

## Suite

- T8 est marquée `terminée` dans [[M-001-terminer-le-mvp]], avec cette réserve.
- Le critère de fin de la mission exige un nouveau passage de `regles-auditor` sans point bloquant. Ce passage n'est pas encore une tâche : voir « Changements de périmètre » de la mission (2026-10-28).
- Le dossier `mapper/06-securite/` est tenu par l'agent pentester ; cette note reste à côté de la fiche T15.
