---
type: backlog
statut: à jour
date: 2026-10-27
tags: [backlog]
---

# Backlog

Source : `CAHIER_DES_CHARGES.md`. La section MVP reflète [[carte]] (validée le 2026-10-26, commit `ccd9187`) : mêmes identifiants, même rôle, même état constaté. Décisions de la carte : [[2026-10-26-decisions-carte]]. Décisions après l'état des lieux (D-F024, D-F010, D-F030) : même fichier, tâches T9 à T12 de [[M-001-terminer-le-mvp]]. **`terminée` exige une recette qui l'a prouvé** ; tant qu'aucune n'a été jouée, une fonctionnalité dont la route et l'écran sont présents et branchés est `constatée`, et une fonctionnalité partielle ou absente est `à faire`.

Statuts : `à faire` · `en cours` · `constatée` · `à vérifier` · `terminée` · `bloquée` · `reportée` · `partielle` (une partie seulement est en place : route sans écran, par exemple ; hors MVP, la règle ci-dessus ne s'applique pas).

## MVP — 31 fonctionnalités (21 constatées, 9 à faire, 1 terminée)

Au 2026-10-27 : F-030 `terminée` après recette OK (voir sa ligne et [[F-030-pieces-kyc-privees]]).

Recette T1 du 2026-10-26 ([[recette-etat-des-lieux-2026-10-26]]) : six fonctionnalités passent à `à faire` (F-005, F-009, F-010, F-021, F-024, F-030), la panne est en note de chaque ligne. Chaque ligne constatée porte son verdict « recette T1 ». Les gênes ont été ajoutées en chantiers C-010 à C-022. Aucune n'est `terminée` : la recette T1 est un état des lieux, pas une preuve de bout en bout (T7).

Changements du 2026-10-26 (carte) : « terminée » devient « constatée » (aucune recette n'a été jouée) ; une colonne `Rôle` est ajoutée ; F-001, F-002, F-004 et F-021 passent au rôle **Visiteur** ; trois fonctionnalités notées « terminée » sont en réalité partielles : **F-008, F-011, F-016** ; le libellé de F-024 perd « refuser » (pas de route ni d'écran ; [[carte]] Q9).

Décisions du 2026-10-26 (utilisateur, [[2026-10-26-decisions-carte]]) : F-011 exige les pièces (recto / verso) ; F-031 suit la règle J+14 ci-dessous ; F-037 reste hors MVP et n'est plus bloquée ; F-042 et F-043 sont créés hors MVP.

| ID | Rôle | Fonctionnalité | § | Statut | Où / ce qui manque |
|---|---|---|---|---|---|
| F-001 | Visiteur | Catalogue consultable sans compte | 3, 4 | constatée | `catalogue/vues.py`, `Catalogue.tsx`, `Accueil.tsx`. Recette T1 : OK avec réserves : pagination ignorée (page_size=24, au-delà de 20 invisible), `/catalogue?groupeur=id` non lu (C-010) |
| F-002 | Visiteur | Inscription + code SMS simulé, renvoi du code | 3, 4, 6 | constatée | `comptes/vues.py`, `Authentification.tsx`. Recette T1 : OK (serveur ; navigateur non joué). Gêne : `InscriptionSerialiseur` accepte `role=groupeur` (C-019) |
| F-004 | Visiteur | Fiche campagne (3 photos, 2 vidéos, jauge, paliers) | 4 | constatée | `FicheCampagne.tsx`. Recette T1 : OK avec réserves : lien « Ses campagnes » absent (C-010) |
| F-021 | Visiteur | Réputation du groupeur affichée (moyenne + compteurs) | 4 | **à faire** | `recalculer_reputation`, `FicheCampagne.tsx`, `Avis.tsx`. Recette T1 : KO, via F-010 : réputation manipulable ([[2026-10-26-recette-failles]]). Tâche : [[M-001-terminer-le-mvp]] T11 |
| F-003 | Acheteur | Connexion, déconnexion, profil | 5 | constatée | `comptes/vues.py`, `Profil.tsx`. Recette T1 : OK (serveur ; navigateur non joué) |
| F-005 | Acheteur | Participer et payer (Mobile Money simulé), prix figé | 3, 6 | **à faire** | `commandes/vues.py`, `paiements/services.py::encaisser`. Recette T1 : KO ([[recette-etat-des-lieux-2026-10-26]]) : confirmation de paiement jamais affichée (C-011) ; prix affiché ≠ prix facturé (C-013) ; bouton « Participer » recouvert par la barre d'onglets à 390 px (`FicheCampagne.tsx:515`, 8 px touchables) ; part en attente bloquante si échec (F-043). Tâche : [[M-001-terminer-le-mvp]] T12 |
| F-006 | Acheteur | Mes achats : participations, code de retrait + QR | 4, 5 | constatée | `MesAchats.tsx`, `commandes/serialiseurs.py`. Recette T1 : OK ; gênes : erreur affichée comme état vide (C-016), textes (C-022) |
| F-007 | Acheteur | Historique d'une campagne sortie du catalogue | 4 | constatée | `STATUTS_CONSULTABLES`. Recette T1 : OK |
| F-008 | Acheteur | Notifications (cloche, page) et lien vers l'écran concerné | 8 | **à faire** | les liens `/participations/<id>` (paiement enregistré, produit arrivé ; `paiements/services.py`) mènent à une 404 : la boutique sert `/mes-achats/:id` ([[carte]] C-16). Recette T1 : confirmé (404). Gêne : erreur affichée comme état vide (C-016), textes (C-017) |
| F-009 | Acheteur | Fil : lire sans compte, écrire et répondre (numéro vérifié) | 7 | **à faire** | `echanges/vues.py`, `Discussion.tsx`. Recette T1 : KO (intégrité) : `reponse_a` accepte un message d'une autre campagne (201) ; commentaire sur le brouillon d'autrui (201 + notification) ; campagne inexistante → 500 (`Campagne.objects.get` dans `perform_create`) ([[recette-etat-des-lieux-2026-10-26]]). Tâche : [[M-001-terminer-le-mvp]] T12 |
| F-010 | Acheteur | Noter le groupeur (avis) | 2, 4 | **à faire** | `AvisVueEnsemble`, `Avis.tsx`. Recette T1 : KO : tout numéro vérifié modifie ou supprime un avis ([[2026-10-26-recette-failles]], [[recette-etat-des-lieux-2026-10-26]]). Tâche : [[M-001-terminer-le-mvp]] T11 (décision D-F010) |
| F-011 | Acheteur | Devenir groupeur : dépôt du dossier KYC avec **pièces obligatoires** (recto / verso, numéro, Mobile Money) | 3, 5 | **à faire** | `DossierKYCVue` accepte `piece_recto`/`piece_verso` (facultatifs aujourd'hui) ; `Profil.tsx` (`DevenirGroupeur`) n'a aucun champ fichier. Décision Q5 : champ recto / verso dans `Profil.tsx` et obligation côté serveur. Recette T1 : confirmé (l'écran n'envoie aucune pièce) |
| F-012 | Groupeur | Écran d'attente tant que le KYC n'est pas validé | 3, 5 | constatée | `EtatGroupeurVue`, `EspaceGroupeur.tsx` |
| F-013 | Groupeur | Créer une campagne (brouillon, paliers), publier | 3, 9 | constatée | `espaces/groupeur.py`, `NouvelleCampagne.tsx`. Recette T1 : OK avec réserves : `quantite_minimale=0` et prix 0 acceptés, produit orphelin si la création de campagne échoue (C-015) |
| F-014 | Groupeur | Médias téléversés vers Cloudinary (signature) | 4 | constatée | `noyau/hebergement.py`, `EnvoiMedias.tsx` ; sans `CLOUDINARY_*`, aucun envoi depuis l'écran. Décision Q11 : variables exigées (C-004, C-008). Recette T1 : non vérifiable (503 sans `CLOUDINARY_*`, conforme Q11) |
| F-015 | Groupeur | Tableau de bord : jauge, paiements nominatifs | 3 | constatée | `TableauDeBordGroupeurVue`, `participants`. Recette T1 : OK |
| F-016 | Groupeur | Clôturer / maintenir / renoncer (minimum non atteint) | 4, 9 | **à faire** | routes présentes et testées ; `CampagneGroupeur.tsx` l. 70 et 74 appellent `/api/groupeur/…` (avec le client, cela donne `/api/api/…`, réponse 404) : « Je maintiens » et « Renoncer » ne marchent pas. Recette T1 : confirmé (404, « Connexion impossible ») |
| F-017 | Groupeur | Demander le retrait des fonds (− 1 500 FCFA) | 3, 4 | constatée | `demander-retrait`, `FeuilleRetrait`. Recette T1 : OK avec réserves : bouton « Demander le retrait » reste affiché (C-012) ; confirmation perdue après `recharger()` (C-011) |
| F-018 | Groupeur | Mettre la marchandise à disposition + notification | 3, 8 | constatée | `mise-a-disposition`. Recette T1 : OK avec réserves : accepte une campagne `financee`, décaissement sauté (C-014). Tâche : [[M-001-terminer-le-mvp]] T10 |
| F-019 | Groupeur | Valider le code de retrait (saisie) | 4 | constatée | `retrait`, `valider_retrait`, `FeuilleScan`. Recette T1 : OK avec réserves : bannière « Colis remis à X » perdue après `recharger()` (C-011) |
| F-020 | Groupeur | Répondre dans le fil, messages distingués | 7 | constatée | `Discussion.tsx`, `est_du_groupeur`. Recette T1 : OK |
| F-022 | Administrateur | Console avec connexion | 5 | constatée | `admin/src/App.tsx`. Recette T1 : OK |
| F-023 | Administrateur | Valider / refuser un dossier KYC, consulter les pièces | 3 | constatée | `DossierKYCAdminVueEnsemble`, `Dossiers.tsx`, `/pieces/`. Réserve : tant que F-011 n'est pas fait, aucune pièce n'est déposée. Recette T1 : OK avec réserves : F-011 ; gêne : incohérence `piece_kyc` / `EstAdministrateur` (C-020) |
| F-024 | Administrateur | Exécuter un décaissement | 3, 6 | **à faire** | `DecaissementAdminVueEnsemble.executer`, `Decaissements.tsx` ; refus d'un décaissement : F-042 (hors MVP). Recette T1 : KO, critique : décaissement exécuté après remboursement de la campagne annulée, double paiement ([[2026-10-26-recette-failles]], [[recette-etat-des-lieux-2026-10-26]]) ; verrou absent (C-021). Tâche : [[M-001-terminer-le-mvp]] T10 (décision D-F024, [[2026-10-26-decisions-carte]]) |
| F-025 | Administrateur | Modérer le fil (masquer, rétablir — jamais supprimer) | 7 | constatée | `ModerationVueEnsemble`, `Moderation`. Recette T1 : non vérifiable en détail (console admin non jouée en navigateur) |
| F-026 | Administrateur | Tableau de bord : séquestre, frais | 3 | constatée | `TableauDeBordAdminVue`, `TableauAdmin.tsx`. Recette T1 : OK ; gêne : tableau incomplet (approvisionnement, distribution, minimum_non_atteint non comptés, C-018) |
| F-027 | Système | Clôture automatique à la date limite | 4 | constatée | `cloturer_les_campagnes_echues` ; planification à vérifier dans Coolify (C-007). Recette T1 : OK (planification non vérifiable) |
| F-028 | Système | Remboursement intégral après 7 jours sans décision | 4 | constatée | `rembourser_les_indecis` ; planification à vérifier dans Coolify (C-007). Recette T1 : OK (planification non vérifiable) |
| F-029 | Système | Séquestre plafonné par des contraintes en base | 4 | constatée | `paiements/models.py` ; la somme libéré + remboursé n'est pas plafonnée en base : contrainte à ajouter (C-006, [[carte]] Q16). Recette T1 : OK avec réserves : somme libéré + remboursé non plafonnée (C-006) |
| F-030 | Système | Pièces KYC jamais publiques ni chez Cloudinary ([[F-030-pieces-kyc-privees]]) | — | **terminée** | `config/urls.py`, `config/service/fichiers.py`. Recette T1 : KO, critique : pièces KYC lisibles sans compte par traversée `/medias/` ([[2026-10-26-recette-failles]]). Correctif : `media_publique` refuse sur le chemin résolu, et `urls.py` ne `static()` plus `/medias/` en DEBUG. Tests : `TestPiecesKycPrivees` (60, `test_securite.py`) ; `check.sh complet` : 225 tests verts (2026-10-27, reviewer-tester VALIDÉE). Recette 2026-10-27 : **RECETTE OK**. **Remarque : correctif non commité au 2026-10-27** (branche `fix/F-030-fuite-kyc`, HEAD `ccd9187`). Tâche : [[M-001-terminer-le-mvp]] T9 (décision D-F030) |
| F-031 | Système | **Relances de retrait à J+3 et J+7 (notification) ; à J+14, la part non retirée passe en « réputée livrée », la campagne passe `terminee` et la réputation est créditée** | 4 | **à faire** | existe : `Campagne.mise_a_disposition_le`, `Notification.Genre.RELANCE_RETRAIT`, `Participation.delai_retrait_depasse` ; manque : la tâche planifiée, le statut « réputée livrée » (hors `retiree`, non compté dans les participants servis), le passage à `terminee`, le crédit de réputation ([[carte]] Q13) |

**Pourquoi F-031 compte pour le MVP** : sans elle, un seul participant qui ne vient pas chercher son colis bloque la campagne en `distribution` pour toujours. Elle n'atteint jamais `terminee`, et la réputation du groupeur n'est jamais créditée.

**Règle J+14 (décision du 2026-10-26)** : pas de canal SMS pour les relances, la notification suffit. La part non retirée n'est pas comptée dans les « participants servis », puisqu'aucune remise n'est prouvée ; elle a un statut distinct, « réputée livrée ». La campagne passe alors `terminee` et la réputation est créditée.

**Pourquoi F-016 et F-008 sont à refaire alors que le serveur est prêt** : ce sont des défauts d'intégration, où l'écran appelle ou renvoie vers une adresse qui n'existe pas. La correction est petite, mais sans elle la règle « le groupeur décide » (§4) n'est pas atteignable depuis l'interface.

## Hors MVP
| ID | Fonctionnalité | § | Statut | Note |
|---|---|---|---|---|
| F-032 | Demandes communautaires + « moi aussi » | 4 | constatée | `DemandeProduit`, `Communaute.tsx` ; ramené de « terminée » (aucune recette) |
| F-033 | « J'aime » sur un message | 7 | constatée | `CommentaireVueEnsemble.jaime` ; ramené de « terminée » (aucune recette) |
| F-034 | Clôture forcée d'une campagne par l'administrateur | — | partielle | route `admin/campagnes/<pk>/cloturer/` sans écran (aucun appel dans `frontend/admin/src/`) ; ramené de « terminée » (`CampagneAdminVue`) |
| F-035 | Trier le fil par popularité | 7 | à faire | `nombre_jaime` existe |
| F-036 | Convertir une demande communautaire en campagne | 4 | à faire | |
| F-037 | Choisir entre être livré et venir récupérer | 3 | à faire | hors MVP. Décision Q1 : retrait seul au MVP, la livraison reste à faire plus tard ; n'est plus bloquée. §3 à réécrire (C-003) |
| F-038 | Désigner la personne qui remet les colis | 4 | à faire | `remise_par` est enregistré |
| F-039 | Scanner le QR avec la caméra | 4 | à faire | la saisie manuelle suffit au MVP |
| F-040 | Tracer les frais d'opérateur des remboursements | 4 | à faire | |
| F-041 | Abonnements des groupeurs (CRUD admin, visibles des seuls groupeurs) | — | reportée | mis de côté par l'utilisateur le 2026-10-26 ; contredit §2 et §4 ; décision Q3 : reste reporté |
| F-042 | Refuser un décaissement, avec motif et notification | 3 | à faire | hors MVP (décision Q9). Ni route ni bouton aujourd'hui ; retiré de F-024 |
| F-043 | Reprendre ou abandonner une part dont le paiement a été refusé | 3 | à faire | hors MVP tant que le paiement est simulé (décision Q10). Aujourd'hui la part reste « en attente » et bloque la campagne pour cet acheteur (`CreationParticipationSerialiseur`). À faire avant tout vrai opérateur. Recette T1 : confirmé (part en attente bloquante si échec) |

## Chantiers techniques

C-010 à C-022 : gênes et cosmétiques relevés par la recette T1 ; C-023 à C-025 : réserves de la recette F-030 du 2026-10-27 ([[recette-etat-des-lieux-2026-10-26]]). Hors [[M-001-terminer-le-mvp]], sauf C-014 et C-021 : dans M-001 T10 (ajoutés le 2026-10-26).

| ID | Sujet | Statut | Note |
|---|---|---|---|
| C-001 | Remettre `staging` d'accord avec `master` | terminé | Levé le 2026-10-27 (constaté par le chef de projet) : `staging`, `master`, `origin/staging` et `origin/master` sur `ccd9187`. L'ancien `staging` est sauvegardé dans `sauvegarde/staging-92bc906` (commit `92bc906`, absent de `master`) ; sort de cette branche : décision de l'utilisateur |
| C-002 | Raccourcir la suite de tests (~7 min pour 165 tests) | à faire | piste : hacheur de mots de passe rapide en test ; à mesurer d'abord |
| C-003 | Réécrire le cahier des charges : §2 (Q4 : promesse « livré ou remboursé »), §3 (Q1 retrait seul, Q2 « demande le retrait »), §4 (Q6 annulation, Q7 clôture anticipée, Q8 historique), §5 (Q12 : on devient groupeur depuis son profil), §9 (Q6, Q7, retrait de `decaissee`) | à faire | source : [[2026-10-26-decisions-carte]] ; à faire par `archi-backend` ou le chef de projet, relu par l'utilisateur |
| C-004 | Corriger `CLAUDE.md` : repli Cloudinary (exigé, pas de repli disque) et nombre de tests (165, et non 110) | à faire | Q11 ; `README.md` dit aussi 110 : à corriger dans le même passage ([[carte]] C-14) |
| C-005 | Retirer le statut `decaissee` (`Campagne.Statut`, §9) | à faire | Q14 ; migration revue par `archi-backend` ; `decaissee` n'est jamais posé |
| C-006 | Contrainte en base : `montant_libere + montant_rembourse <= montant_consigne` (Sequestre) | à faire | Q16 ; migration à valider par l'utilisateur, puis à soumettre à `regles-auditor` |
| C-007 | Vérifier que `cloturer_les_campagnes_echues` (F-027, F-028) est planifiée toutes les heures dans les Scheduled Tasks de Coolify, sur achatgr.com | à faire | Q15 ; **action de l'utilisateur**, hors dépôt |
| C-008 | Vérifier que les variables `CLOUDINARY_*` sont posées sur achatgr.com | à faire | Q11 ; **action de l'utilisateur**, hors dépôt |
| C-009 | Corriger les textes d'écran : `FicheCampagne.tsx` (« bloqués jusqu'à la livraison »), `CampagneGroupeur.tsx` (statut `en_cours` : « annulée et tout le monde remboursé » ; et « Aucun abonnement, aucune commission », à réécrire avec F-041) | à faire | Q4 et C-8 de la carte ; le texte suit la règle, pas l'inverse |
| C-010 | Pagination et navigation du catalogue : `page_size=24` ignoré, aucune pagination à l'écran (au-delà de 20, invisible), `/catalogue?groupeur=id` non lu par `Catalogue.tsx`, lien « Ses campagnes » absent (F-001, F-004) | à faire | recette T1, gêne |
| C-011 | Confirmations perdues après `recharger()` : la page repasse en squelette. Jamais affichées : confirmation de paiement et « Voir mon QR » (F-005), feuille « Demande enregistrée » (F-017), bannière « Colis remis à X » (F-019) | à faire | recette T1, gêne ; même mécanisme dans trois écrans |
| C-012 | Bouton « Demander le retrait » encore affiché après la demande (F-017) | à faire | recette T1, gêne |
| C-013 | Prix affiché ≠ prix facturé : l'écran affiche `prix_courant` × quantité (35 000 FCFA dans le cas relevé) alors que le serveur applique le palier atteint (32 000 FCFA). Choix à trancher : afficher le palier ou facturer le prix affiché. Le prix figé à la commande reste la règle | à faire | recette T1 ; touche F-005 |
| C-014 | `mettre_a_disposition` accepte une campagne `financee` : fonds jamais libérés, décaissement sauté (F-018) | à faire | recette T1, gêne ; à traiter avec C-021 ; dans [[M-001-terminer-le-mvp]] T10 |
| C-015 | Garde-fous de création de campagne : `quantite_minimale=0` et prix 0 acceptés ; produit orphelin si la création de campagne échoue (F-013) | à faire | recette T1, gêne |
| C-016 | Erreurs affichées comme état vide : « Mes achats » (F-006) et « Notifications » (F-008) | à faire | recette T1, gêne |
| C-017 | Notifications : lien vide sur « Remboursement effectué » ; « Minimum atteint » renvoyé à chaque paiement au-delà du minimum (F-008) | à faire | recette T1, cosmétique |
| C-018 | Tableau de bord admin incomplet : ne compte ni approvisionnement, ni distribution, ni `minimum_non_atteint` (F-026) | à faire | recette T1, gêne |
| C-019 | `InscriptionSerialiseur` accepte `role=groupeur`, contraire à Q12 (on devient groupeur depuis son profil). Sans effet d'accès (F-002) | à faire | recette T1, autre |
| C-020 | Incohérence `piece_kyc` / `EstAdministrateur` : `piece_kyc` n'autorise que `est_equipe`, `EstAdministrateur` accepte aussi `role=administrateur` (F-023) | à faire | recette T1, autre |
| C-021 | Verrou absent dans `executer_decaissement` : ni `select_for_update`, ni contrôle du statut de la campagne ni du solde ; double exécution simultanée possible. Lié à la panne F-024 | à faire | recette T1 ; à traiter avec F-024 ; dans [[M-001-terminer-le-mvp]] T10 |
| C-022 | Textes cosmétiques : part retirée ou remboursée affiche « Ce code deviendra actif… » (F-006) ; « n'a pas atteint son minimum » faux pour une annulation depuis `en_cours` ou `financee` (voir aussi C-009) | à faire | recette T1, cosmétique |
| C-023 | Les 404 de `/pieces/…` et `/medias/…` renvoient la page HTML par défaut de Django, en anglais (« Not Found »), pas un message en français (F-030, R18 attendait un message lisible) | à faire | réserve de la recette F-030 du 2026-10-27 ; gêne, non bloquante ; hors sécurité |
| C-024 | Commentaires imprécis dans le correctif F-030 : `config/service/fichiers.py` (~l. 43) cite `os.path.realpath` alors que le code utilise `Path.resolve()` ; `config/urls.py` (l. 15-18) présente l'expression de route comme défense principale, alors que la défense est désormais la vue | à faire | relevé par le relecteur (2026-10-27) ; cosmétique ; à corriger avec le commit F-030 ou après |
| C-025 | Pièces KYC déjà exposées en production (`/medias/kyc/` lisible avant le correctif) et 7 fichiers `piece_*.png` dans `backend/medias/kyc/` qui ressemblent à des dépôts de test ou de démo : rotation ou suppression à décider | à faire | **décision et opération de l'utilisateur, hors code** (D-F030) ; non traité par le correctif |
