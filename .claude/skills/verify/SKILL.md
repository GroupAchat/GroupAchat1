---
name: verify
description: Vérifie un changement de code avant de le déclarer terminé — lance la commande « Vérifier » du projet, détecte les tests affaiblis, relit le diff et rend un rapport PASS/FAIL avec preuves. À utiliser après toute modification de code (fonctionnalité, correctif, refactorisation), avant de dire « terminé ».
---

# Vérification

Procédure fixe, suivie en entier à chaque fois. « Terminé » n'est jamais annoncé sans le rapport de l'étape 4.

1. **Contrôles** : `bash .claude/skills/verify/scripts/check.sh`. Le script lance la commande « Vérifier » de `CLAUDE.md`. Lire la sortie réelle. En cas d'échec : corriger, relancer ; ne jamais passer à l'étape suivante avec un contrôle rouge.
2. **Tests affaiblis** : `bash .claude/skills/verify/scripts/test-diff.sh [branche-de-base]` (par défaut `staging`). Examiner chaque signal ; `reference.md` dit comment juger s'il est légitime.
3. **Relecture du diff** : `git diff <base>...HEAD` et `git diff`. Vérifier : périmètre de la demande respecté, conventions de `.claude/conventions/`, règles de `.claude/rules/` pour les fichiers touchés, aucun secret, aucun fichier qui a grossi au-delà de 200 lignes.
4. **Rapport**, au format ci-dessous.

## Rapport

```
VERIFY: PASS | FAIL
Contrôles : <commande> → <résultat réel : N tests passés, lint et types sans erreur>
Tests affaiblis : aucun | <fichier:ligne — signal — légitime ou non, et pourquoi>
Diff : <N fichiers> — <résumé> ; hors périmètre : aucun | <liste>
Problèmes : aucun | <liste avec fichier:ligne>
```

`FAIL` si un contrôle échoue, si un test est affaibli sans justification dans la demande, ou si un problème critique reste ouvert. Jamais `PASS` sans avoir exécuté l'étape 1 dans ce tour.
