---
type: securite
statut: ouverte
date: 2026-10-26
tags: [securite, recette, M-001]
---

# Failles relevées pendant la recette T1

Source : [[recette-etat-des-lieux-2026-10-26]] · Mission : [[M-001-terminer-le-mvp]] · Backlog : [[backlog]]

Statut de toutes les failles ci-dessous : **ouverte, non corrigée**. Aucune correction n'est faite par T1 (lecture seule).

## F-030 — Pièces KYC lisibles sans compte
- **Gravité** : critique
- **Constat** : `GET /medias/x/%2e%2e/kyc/<fichier>` renvoie 200 à un visiteur anonyme, y compris avec `DJANGO_DEBUG=0`.
- **Cause** : l'expression `^medias/(?!kyc/)` laisse passer `x/..` ; `media_publique` (`config/service/fichiers.py:34-36`) ne teste que `Path(chemin).parts[0]` ; `serve()` normalise le chemin ensuite.
- **Aggravant** : en `DEBUG=1`, `static(MEDIA_URL…)` dans `config/urls.py` sert `/medias/kyc/<fichier>` directement, sans passer par la vue de contrôle.
- **Nature** : le nom de fichier d'origine est devinable.
- **Tests** : aucun.
- **Liens** : F-030 (backlog, [[backlog]]), `config/urls.py`, `config/service/fichiers.py`.

## F-010 — Avis modifiables et supprimables par des tiers
- **Gravité** : haute
- **Constat** : `AvisVueEnsemble` est un `ModelViewSet` gardé par `LectureLibreEcritureVerifiee` seulement. N'importe quel numéro vérifié peut modifier ou supprimer un avis.
- **Cas relevés** : un acheteur a changé la note d'un avis (3 → 1) puis l'a supprimé (204) ; le groupeur visé a modifié puis supprimé l'avis qui le vise ; un acheteur sans participation a supprimé un avis.
- **Conséquence** : réputation du groupeur manipulable (F-021 touché).
- **Tests** : aucun.
- **Liens** : F-010 et F-021 (backlog, [[backlog]]).

## F-024 — Double paiement sur campagne annulée
- **Gravité** : critique
- **Constat** : le groupeur demande le retrait d'une campagne `financee`, puis l'annule. Les acheteurs sont remboursés (475 000 FCFA). L'administrateur exécute ensuite le décaissement encore en attente.
- **Résultat** : 475 000 remboursés + 473 500 versés. La campagne repasse de `annulee` à `approvisionnement`.
- **Cause** : `executer_decaissement` ne vérifie ni le statut de la campagne ni le solde. Aucune contrainte en base (C-006).
- **Liens** : F-024, F-016, F-017 (backlog, [[backlog]]) ; chantiers C-006, C-021.
