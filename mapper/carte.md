---
type: carte
statut: validée
date: 2026-10-27
commit: abaa622
validee_le: 2026-10-26
tags: [carte]
---
# Carte du projet

Établie par lecture de `CAHIER_DES_CHARGES.md`, `README.md`, `CLAUDE.md`, `mapper/` et du code (`backend/groupachat/api.py` pour les routes, `frontend/boutique/src/App.tsx` et `frontend/admin/src/App.tsx` pour les écrans, et chaque appel `api.get/post/patch/delete` rapproché de sa route). **« Constatée » veut dire « route et écran présents, et l'écran appelle une route qui existe »** : rien n'a été exécuté, c'est l'agent `recette` qui prouve que ça marche. **« Terminée » veut dire « recette OK »**, comme dans [[backlog]] : la recette a été jouée et a passé, et le code est dans `staging`.

Mise à jour du 2026-10-27 (commit `abaa622`) : **états seulement**. Les rôles, les aboutissements et la liste MVP validés le 2026-10-26 ([[2026-10-26-decisions-carte]]) sont inchangés. Ont changé : F-030 (`fb4963c`), F-016 (`f8b78f9`), F-008 (`769ec1a`) et F-011 (`abaa622`) passent en `terminée` ; la réserve de F-023 est levée ; les parcours qui décrivaient ces pannes sont mis à jour ; les questions et contradictions tranchées portent leur décision. Les échecs de la recette T1 du 2026-10-26 ([[recette-etat-des-lieux-2026-10-26]]) sont signalés dans la colonne « Preuve » : ils ne changent pas l'état constaté (route et écran sont présents), mais la fonctionnalité est `à faire` au backlog.

## Le projet en cinq lignes
Group Achat est une place de marché d'achat groupé pour Lomé, sur le web et pensée d'abord pour le téléphone : une boutique (`frontend/boutique/`) et une console d'administration (`frontend/admin/`), servies par une API Django (`backend/`).
Un **groupeur** dont l'identité est vérifiée (KYC) lance une campagne : un produit, un prix, un minimum de pièces et une date limite. Les **acheteurs** paient leur part, et l'argent reste **sous séquestre** pour chaque campagne. L'argent ne va jamais directement au groupeur.
À la date limite, la collecte se ferme. Si le minimum n'est pas atteint, le groupeur choisit de maintenir ou de renoncer. Sans réponse de sa part pendant 7 jours, chaque acheteur est remboursé.
Si la campagne est financée, le groupeur reçoit les fonds moins 1 500 FCFA, achète la marchandise et la met à disposition. Chaque acheteur la retire contre un **code unique / QR**, et la validation de ce code vaut preuve de livraison.
La plateforme met en relation sans arbitrer : une plainte se dit dans le fil public de la campagne et se traduit dans la note du groupeur. Les SMS et les paiements sont simulés, mais la comptabilité du séquestre est réelle.

## Rôles
| Rôle | Qui | Accès | Source |
|---|---|---|---|
| **Visiteur** | n'importe qui, sans compte | catalogue, fiche, fil (lecture), avis, réputation | §3 acheteur 1, §4 Inscription, §7 |
| **Acheteur** | compte dont le numéro est vérifié par SMS (simulé) | participer, payer, retirer, noter, écrire dans le fil, demander à devenir groupeur | §3, §5 |
| **Groupeur** | acheteur qui a déposé un dossier KYC **validé** par l'administrateur | espace groupeur (`/groupeur`) ; avant validation, seulement un écran d'attente | §3, §5 |
| **Administrateur** | compte interne (`est_equipe`) | console séparée (`admin.achatgr.com`, port 5174) | §3, §5 |
| **Système** | la tâche horaire `cloturer_les_campagnes_echues` et les contraintes en base | clôture à la date limite, remboursement après 7 jours sans décision, plafonds du séquestre | §4, §9, `COOLIFY.md` §4 |

## Visiteur — aboutissements
| Aboutissement | Parcours (étapes) | Fonctionnalités |
|---|---|---|
| Il a trouvé une campagne et jugé s'il peut faire confiance au groupeur | Accueil (fil vertical) ou Catalogue (rayons, recherche, tri) → fiche campagne (photos, jauge, paliers, point de remise) → réputation du groupeur et avis → fil de discussion en lecture | F-001, F-004, F-021, F-009 (lecture) |
| Il a un compte vérifié, prêt à commander | Fiche → « Participer » → feuille « créez votre compte » → Inscription (nom, prénom, téléphone, mot de passe, e-mail facultatif) → code affiché à l'écran → vérification, qui ouvre aussi la session | F-002 |

Constat de parcours : après la vérification, l'écran renvoie vers l'accueil (`naviguer("/")`, `Authentification.tsx`) et non vers la campagne d'où venait le visiteur. Il doit la retrouver lui-même. Ce n'est pas un trou de la carte, mais une étape en plus.

## Acheteur — aboutissements
| Aboutissement | Parcours (étapes) | Fonctionnalités |
|---|---|---|
| **Sa part est payée et consignée, et il a son code** | Fiche → Participer (quantité, opérateur TMoney / Flooz) → paiement simulé → « Votre part est consignée » + code → « Voir mon QR code » | F-005, F-006, F-008 |
| **Il a reçu son colis** | Notification « Votre produit est arrivé » (point de remise + code) → Mes achats → détail (QR) → il présente le code au point de retrait → notification « Retrait confirmé » | F-008, F-006 ; côté groupeur F-018, F-019 |
| Il a donné son avis sur le groupeur | Mes achats → détail → formulaire d'avis, ouvert dès que la collecte est close | F-010 |
| Il a obtenu une réponse à sa question | Fiche → fil → écrire ou répondre → notification « Réponse à votre message » | F-009, F-008 |
| Il retrouve une campagne sortie du catalogue | Mes achats → lien vers la fiche, ouverte même si la campagne est annulée ou n'a pas atteint son minimum | F-007 |
| Il a déposé son dossier pour devenir groupeur | Profil → « Devenir groupeur » → formulaire KYC | F-011 |
| *Échec* — **groupage non abouti, puis maintenu** | Notification « Le groupage n'a pas abouti » → part consignée → notification « Le groupage est maintenu » → suite normale | F-027, F-016, F-008 |
| *Échec* — **groupage annulé : il est remboursé intégralement, sans rien demander** | Groupeur qui renonce (F-016) **ou** 7 jours sans décision (F-028) → notifications « Groupage annulé » et « Remboursement effectué » | F-016, F-028, F-008 |
| *Échec* — **colis non retiré** : relancé à J+3 et J+7, livraison réputée acquise à J+14 | — **aucun chemin** : ni relance, ni clôture | F-031 |
| *Échec* — produit décevant : il le dit publiquement et note le groupeur | Fil + avis ; la plateforme n'arbitre pas (§2) | F-009, F-010 |
| *Échec* — le groupeur a touché les fonds et ne livre pas | — **aucun chemin** au-delà de l'avis : aucun remboursement n'est possible une fois les fonds libérés (voir Q4) | — |
| *Échec* — paiement refusé par l'opérateur | — **aucun chemin** : la part reste « en attente de paiement », et elle bloque toute nouvelle participation à la même campagne (`CreationParticipationSerialiseur`). Aucun écran ne permet de la payer à nouveau ni de l'abandonner. Cela n'arrive pas avec le paiement simulé (voir Q10) | — |

```mermaid
flowchart LR
  V[Visiteur : fiche] -->|s'inscrit, F-002| P[Participe et paie, F-005]
  P --> C{Date limite, F-027}
  C -->|minimum atteint| F[Financée]
  C -->|minimum manqué| D{Décision du groupeur, F-016}
  D -->|maintient| F
  D -->|renonce| R[Remboursé, F-008]
  D -->|7 jours de silence, F-028| R
  F --> M[Notifié : produit arrivé, F-018]
  M -->|présente son code| OK[Colis reçu, F-019]
  M -->|ne vient pas| J14[Relances J+3/J+7, clos J+14 : ABSENT, F-031]
  OK --> A[Note le groupeur, F-010]
```

## Groupeur — aboutissements
| Aboutissement | Parcours (étapes) | Fonctionnalités |
|---|---|---|
| **Il a son badge de confiance** | Profil → Devenir groupeur → dossier (pièce recto / verso, numéro, Mobile Money) → `/groupeur` affiche l'écran d'attente → décision de l'administrateur → notification « Dossier validé » → l'espace s'ouvre | F-011, F-012, F-023 |
| *Échec* — **KYC refusé** | Notification de refus (motif), dont le lien mène à `/profil/devenir-groupeur` depuis F-011 (`espaces/administration.py`, C-038) ; l'écran d'attente montre aussi le motif → il corrige et redépose ses deux pièces (un dossier rejeté est réécrit, pas doublé) | F-012, F-011, F-023 |
| Sa campagne est au catalogue | Tableau de bord → Nouvelle campagne (produit, médias, prix, paliers, minimum, date limite, point de remise) → brouillon → Publier | F-013, F-014 |
| Il suit la collecte nominativement | Fiche de sa campagne → jauge + « Qui a payé » ; notifications « Nouveau paiement » et « Minimum atteint » | F-015, F-008 |
| **Il a reçu ses fonds** | Clôture (automatique, ou anticipée par lui) → campagne financée → « Demander le retrait » (brut − 1 500 FCFA) → l'administrateur exécute → notification « Fonds versés » | F-027, F-016 (clôturer), F-017, F-024 |
| **Tous ses colis sont remis et la campagne compte dans sa réputation** | « Annoncez l'arrivée » (point de remise) → tous notifiés → saisie ou collage du code de chaque participant → dernier code validé → campagne terminée, compteurs crédités | F-018, F-019, F-021 |
| *Échec* — **minimum non atteint : il maintient ou renonce** | Notification « Décision attendue » → fiche → « Je maintiens » (refusé dès le 7e jour) / « Renoncer et rembourser » → sans décision au 7e jour, remboursement automatique. Chemin réparé par F-016 (`f8b78f9`, recette OK) | F-016, F-028 |
| *Échec* — un participant ne vient jamais | — **aucun chemin** : la campagne reste en `distribution` pour toujours, et sa réputation n'est jamais créditée | F-031 |
| Il a répondu publiquement à une question ou à un avis | Notification « Nouveau message » ou « Nouvel avis » → fil (message marqué « groupeur ») / réponse sous l'avis | F-020, F-008 |

```mermaid
flowchart LR
  K[Dépose son dossier, F-011] --> W{Décision admin, F-023}
  W -->|rejeté| K
  W -->|validé| E[Espace groupeur, F-012]
  E --> N[Crée et publie, F-013/F-014]
  N --> S[Suit la collecte, F-015]
  S --> C{Clôture, F-027}
  C -->|financée| R[Demande le retrait, F-017]
  C -->|minimum manqué| D{Maintient / renonce, F-016}
  D -->|maintient| R
  D -->|renonce ou 7 jours| X[Annulée, remboursée]
  R -->|admin exécute, F-024| A[Met à disposition, F-018]
  A --> V[Valide les codes, F-019]
  V -->|tous retirés| T[Terminée, réputation, F-021]
  V -->|un absent| B[Bloquée en distribution, F-031]
```

## Administrateur — aboutissements
| Aboutissement | Parcours (étapes) | Fonctionnalités |
|---|---|---|
| Un dossier KYC est tranché | Console → connexion (refus si le compte n'appartient pas à l'équipe) → Dossiers (filtre par statut) → fiche (pièce, numéros, photos via `/pieces/<id>/<côté>/`) → Valider / Refuser avec un motif | F-022, F-023 |
| Les fonds d'une campagne financée sont libérés | Décaissements → demande → « Exécuter » (versement simulé, séquestre libéré, campagne en approvisionnement) | F-024 |
| Le fil est assaini sans rien effacer | Modération → masquer (avec un motif) / rétablir | F-025 |
| Il voit l'état de la plateforme | Tableau : comptes, ce qu'il reste à traiter, campagnes par statut, séquestre détenu / libéré / remboursé, frais encaissés | F-026 |
| Le dossier se clôt dès que le code est validé (§3 admin 5) | Automatique : le dernier code validé fait passer la campagne en `terminee` (`valider_retrait`). Il n'y a pas de geste de l'administrateur | F-019 |
| Les fonds sont consignés (§3 admin 3) | Automatique au paiement (`encaisser`). Il n'y a pas de geste de l'administrateur, contrairement à ce que dit le §6 | F-005, F-029 |

## Système — aboutissements
| Aboutissement | Parcours (étapes) | Fonctionnalités |
|---|---|---|
| Une collecte échue a quitté le catalogue, et les participants savent ce qui se passe | La liste filtre `date_limite > maintenant` immédiatement ; la tâche horaire appelle `cloturer` → `financee` ou `minimum_non_atteint`, avec les notifications | F-027 |
| Un groupeur silencieux ne bloque pas l'argent | La tâche horaire appelle `rembourser_les_indecis` (`DELAI_DECISION_JOURS = 7`) → `annuler` → remboursements | F-028 |
| Le séquestre ne peut pas rendre plus qu'il n'a reçu | Contraintes en base sur `Sequestre` | F-029 |
| Les pièces d'identité restent privées | `/medias/` refuse `kyc/` ; `/pieces/` vérifie qui demande ; aucune pièce n'est envoyée chez Cloudinary | F-030 |
| Les colis oubliés sont relancés, puis le dossier se clôt | — **absent** | F-031 |

La tâche horaire n'est planifiée nulle part dans le dépôt : `COOLIFY.md` §4 demande de la programmer dans les *Scheduled Tasks* de Coolify. **À vérifier dans Coolify** que c'est fait sur `achatgr.com`. Sans elle, F-027 et F-028 n'ont aucun effet en production.

## Fonctionnalités du MVP par rôle
Couches : **S** = serveur (`backend/groupachat/`), **B** = web boutique (`frontend/boutique/src/`), **A** = web admin (`frontend/admin/src/`). Les chemins sont relatifs à ces dossiers.

| ID | Rôle | Fonctionnalité (résultat observable) | § | Couches | État constaté | Preuve |
|---|---|---|---|---|---|---|
| F-001 | Visiteur | Il parcourt les campagnes ouvertes sans compte (rayons, recherche, tri) | 3, 4 | S, B | constatée | `catalogue/vues.py` (`CampagneVueEnsemble`, `AllowAny`, filtre `date_limite__gt`) · `pages/Accueil.tsx`, `pages/Catalogue.tsx`, `composants/FilCampagnes.tsx` |
| F-002 | Visiteur | Il crée son compte ; le code SMS simulé s'affiche à l'écran ; il peut demander un nouveau code | 3, 4, 6 | S, B | constatée | `comptes/vues.py` (`InscriptionVue`, `VerificationVue`, `RenvoiCodeVue`, limitées) · `pages/Authentification.tsx` |
| F-004 | Visiteur | Il voit la fiche d'une campagne : 3 photos et 2 vidéos au plus, jauge, paliers, point de remise | 4 | S, B | constatée | `catalogue/vues.py` (`retrieve`), `catalogue/serialiseurs.py` · `pages/FicheCampagne.tsx`, `composants/Jauge.tsx`, `composants/PhotosDuLot.tsx` |
| F-021 | Visiteur | Il voit la réputation du groupeur : moyenne des avis et compteurs de volume | 4 | S, B | constatée | `paiements/services.py` (`recalculer_reputation`, `_crediter_reputation`) · `pages/FicheCampagne.tsx`, `composants/Avis.tsx` (`ListeAvis`). **Recette T1 : KO** par F-010 (réputation manipulable) : `à faire` au backlog, tâche T11 |
| F-003 | Acheteur | Il se connecte, se déconnecte et modifie son profil | 5 | S, B | constatée | `comptes/vues.py` (`ConnexionVue`, `DeconnexionVue`, `MoiVue`) · `pages/Authentification.tsx`, `pages/Profil.tsx`, `commun/src/contexte/Session.tsx` |
| F-005 | Acheteur | Il participe et paie (simulé) ; le prix est figé, la part est consignée et le code est attribué | 3, 4, 6 | S, B | constatée | `commandes/vues.py` (`ParticipationVueEnsemble.create`, `payer`), `paiements/services.py::encaisser` · `pages/FicheCampagne.tsx` (`FeuilleParticipation`). **Recette T1 : KO** (bouton « Participer » recouvert à 390 px, confirmation jamais affichée C-011, prix affiché ≠ facturé C-013) : `à faire` au backlog, tâche T12 |
| F-006 | Acheteur | Il retrouve ses participations, son code et son QR (`GA|campagne|code`) | 4, 5 | S, B | constatée | `commandes/serialiseurs.py` (`charge_qr`) · `pages/MesAchats.tsx` (`MesAchats`, `DetailAchat`, `qrcode`) |
| F-007 | Acheteur | Il rouvre une campagne sortie du catalogue (annulée, ou minimum non atteint) | 4 | S, B | constatée | `catalogue/vues.py` (`STATUTS_CONSULTABLES`) · `pages/FicheCampagne.tsx` (bandeaux `minimum_non_atteint`, `annulee`) |
| F-008 | Acheteur | Il est notifié à chaque étape (cloche, page) et suit le lien jusqu'à l'écran concerné | 8 | S, B | **terminée** | Avant (2026-10-26) : partielle, liens `/participations/<id>` menant à la page 404. Après : `paiements/services.py` écrit `/mes-achats/<id>` (`_notifier_paiement`, `mettre_a_disposition`, `valider_retrait`) et `/groupeur/campagnes/<id>` (« Fonds versés ») ; migration `echanges/migrations/0004_corriger_liens_des_notifications.py` (anciens liens réécrits) ; route `/mes-achats/:id` dans `boutique/src/App.tsx`. Recette OK le 2026-10-27, commit `769ec1a` ([[F-008-liens-des-notifications]]). Réserve : « Remboursement effectué » sans lien (C-017) |
| F-009 | Acheteur | Il écrit et répond dans le fil (numéro vérifié, un seul niveau) ; tout le monde le lit sans compte | 7 | S, B | constatée | `echanges/vues.py` (`CommentaireVueEnsemble`, `LectureLibreEcritureVerifiee`), `api.py` (`campagnes/<id>/commentaires/`) · `composants/Discussion.tsx`. **Recette T1 : KO** (réponse à un message d'une autre campagne, commentaire sur le brouillon d'autrui, 500 sur campagne inexistante) : `à faire` au backlog, tâche T12 |
| F-010 | Acheteur | Il note le groupeur une fois la collecte close | 2, 4 | S, B | constatée | `commandes/vues.py` (`AvisVueEnsemble`), `Participation.peut_etre_notee` · `composants/Avis.tsx` (`FormulaireAvis`, dans `DetailAchat`). **Recette T1 : KO** (tout numéro vérifié modifie ou supprime un avis, [[2026-10-26-recette-failles]]) : `à faire` au backlog, tâche T11 (D-F010) |
| F-011 | Acheteur | Il dépose son dossier KYC (pièce d'identité recto / verso, numéro de la pièce, numéro Mobile Money) | 3, 5 | S, B | **terminée** | Avant (2026-10-26) : partielle, l'écran n'envoyait aucune pièce et le serveur les tenait pour facultatives. Après : `comptes/serialiseurs.py` (`PieceKycField`, recto et verso obligatoires), `comptes/pieces_kyc.py` (JPEG, PNG ou WebP, 8 Mo), `comptes/vues.py::DossierKYCVue`, migration `comptes/migrations/0004_noms_aleatoires_des_pieces_kyc.py` · `pages/Profil.tsx` (`DevenirGroupeur`, envoi `FormData`), `composants/ChampPiece.tsx`. Recette OK le 2026-10-27, commit `abaa622` ([[F-011-depot-dossier-kyc]]) |
| F-012 | Groupeur | Il voit l'écran d'attente (ou le motif du rejet) tant que son dossier n'est pas validé | 3, 5 | S, B | constatée | `espaces/groupeur.py::EtatGroupeurVue`, `noyau/permissions.py::GroupeurValide` · `pages/groupeur/EspaceGroupeur.tsx` |
| F-013 | Groupeur | Il crée un produit et une campagne (brouillon, paliers), puis la publie | 3, 9 | S, B | constatée | `espaces/groupeur.py` (`ProduitGroupeurVueEnsemble`, `CampagneGroupeurVueEnsemble.publier`) · `pages/groupeur/NouvelleCampagne.tsx`, `pages/groupeur/CampagneGroupeur.tsx` |
| F-014 | Groupeur | Il téléverse ses photos et vidéos vers Cloudinary (autorisation signée par Django), et les photos du lot | 4 | S, B | constatée | `noyau/hebergement.py`, `espaces/groupeur.py` (`SignatureEnvoiVue`, `MediaProduitVueEnsemble`, `MediaCampagneVueEnsemble`) · `composants/EnvoiMedias.tsx`, `composants/PhotosDuLot.tsx`, `commun/src/outils/televersement.ts`. Réserve : sans les variables `CLOUDINARY_*`, la signature répond 503 et l'écran n'a pas d'autre voie d'envoi (Q11) |
| F-015 | Groupeur | Il suit la jauge et les paiements nominatifs | 3 | S, B | constatée | `espaces/groupeur.py` (`participants`, `TableauDeBordGroupeurVue`) · `pages/groupeur/TableauDeBord.tsx`, `pages/groupeur/CampagneGroupeur.tsx` (« Qui a payé ») |
| F-016 | Groupeur | Il clôture sa collecte ; si le minimum n'est pas atteint, il maintient la commande ou y renonce (ce qui rembourse) | 4, 9 | S, B | **terminée** | Avant (2026-10-26) : partielle, l'écran appelait `/api/api/groupeur/…` (404). Après : `pages/groupeur/CampagneGroupeur.tsx` (lignes 70 et 74) appelle `/groupeur/campagnes/<id>/maintenir/` et `/annuler/` ; `paiements/services.py` (`_verrouiller` sous `select_for_update`, `maintenir` refusé dès le 7e jour) ; `tests/test_cloture.py`. Recette OK le 2026-10-27, commit `f8b78f9` ([[F-016-decision-minimum-non-atteint]]) |
| F-017 | Groupeur | Il demande le retrait des fonds : 100 % moins 1 500 FCFA | 3, 4 | S, B | constatée | `espaces/groupeur.py::demander_retrait`, `paiements/services.py::demander_decaissement` · `CampagneGroupeur.tsx` (`FeuilleRetrait`). Réserve : une fois la demande faite, l'écran remontre le bouton jusqu'à l'exécution ; un second clic reçoit « Un décaissement a déjà été demandé » |
| F-018 | Groupeur | Il annonce la mise à disposition et tous les participants sont notifiés (point de remise + code) | 3, 8 | S, B | constatée | `espaces/groupeur.py::mise_a_disposition`, `paiements/services.py::mettre_a_disposition` · `CampagneGroupeur.tsx` (`FormulaireDisposition`) |
| F-019 | Groupeur | Il valide le code d'un participant (saisi ou collé depuis le QR) ; un code d'une autre campagne est refusé | 4 | S, B | constatée | `espaces/groupeur.py::retrait`, `paiements/services.py::valider_retrait` · `CampagneGroupeur.tsx` (`FeuilleScan`) |
| F-020 | Groupeur | Il répond dans le fil, où ses messages sont distingués, et répond une fois sous un avis | 7 | S, B | constatée | `echanges/serialiseurs.py` (`est_du_groupeur`), `commandes/vues.py::AvisVueEnsemble.repondre` · `composants/Discussion.tsx`, `composants/Avis.tsx` |
| F-022 | Administrateur | Il entre dans une console séparée, réservée à l'équipe | 5 | S, A | constatée | `noyau/permissions.py::EstAdministrateur` · `admin/src/App.tsx` (`ConnexionAdmin`, refus si `!est_equipe`) |
| F-023 | Administrateur | Il valide ou refuse un dossier KYC (motif) après avoir consulté les pièces ; le groupeur est notifié | 3 | S, A | constatée | `espaces/administration.py::DossierKYCAdminVueEnsemble.decision`, `config/service/fichiers.py::piece_kyc` · `pages/Dossiers.tsx` (recto et verso affichés depuis `abaa622`). Réserve du 2026-10-26 (aucune pièce déposée) levée par F-011. Recette T1 : OK avec réserves (C-020, C-047) |
| F-024 | Administrateur | Il exécute un décaissement : le séquestre est libéré et la campagne passe en approvisionnement | 3, 6 | S, A | constatée | `espaces/administration.py::DecaissementAdminVueEnsemble.executer`, `paiements/services.py::executer_decaissement` · `pages/Decaissements.tsx`. Le refus manuel est hors MVP (F-042, Q9 tranchée). **Recette T1 : KO, critique** (décaissement exécuté après remboursement d'une campagne annulée : double paiement ; verrou absent C-021, [[2026-10-26-recette-failles]]) : `à faire` au backlog, tâche T10 (D-F024) |
| F-025 | Administrateur | Il masque un message (avec un motif) ou le rétablit ; rien n'est jamais supprimé | 7 | S, A | constatée | `espaces/administration.py::ModerationVueEnsemble` · `pages/Decaissements.tsx` (`Moderation`, route `/moderation`) |
| F-026 | Administrateur | Il voit le séquestre détenu / libéré / remboursé, les frais encaissés et ce qu'il reste à traiter | 3 | S, A | constatée | `espaces/administration.py::TableauDeBordAdminVue` · `pages/TableauAdmin.tsx` |
| F-027 | Système | À la date limite, la collecte se ferme (financée, ou minimum non atteint) et tout le monde est prévenu | 4, 9 | S | constatée | `catalogue/management/commands/cloturer_les_campagnes_echues.py`, `paiements/services.py::cloturer_les_echus` ; `tests/test_cloture.py`. Planification : à vérifier dans Coolify |
| F-028 | Système | Après 7 jours sans décision du groupeur, chaque participant est remboursé intégralement | 4, 9 | S | constatée | `paiements/services.py::rembourser_les_indecis` (`DELAI_DECISION_JOURS`) ; `tests/test_cloture.py`. Planification : à vérifier dans Coolify |
| F-029 | Système | Le séquestre ne peut pas libérer ni rembourser plus que le montant consigné (contrainte en base) | 4 | S | constatée | `paiements/models.py` (`sequestre_ne_libere_pas_plus_que_consigne`, `sequestre_ne_rembourse_pas_plus_que_consigne`). Réserve : la **somme** libéré + remboursé n'est pas plafonnée en base, seul le service l'empêche |
| F-030 | Système | Les pièces KYC ne sont jamais publiques ni envoyées chez Cloudinary | `CLAUDE.md` | S | **terminée** | Avant (2026-10-26) : constatée, puis KO à la recette T1 (traversée `/medias/x/%2e%2e/kyc/…`, [[2026-10-26-recette-failles]]). Après : `config/service/fichiers.py::media_publique` refuse sur le chemin résolu (`Path.resolve()`) ; `config/urls.py` ne sert plus `/medias/` par `static()` en DEBUG ; `tests/test_securite.py` (`TestPiecesKycPrivees`). Recette OK le 2026-10-27, commit `fb4963c` ([[F-030-pieces-kyc-privees]]) |
| F-031 | Système | Le participant qui n'a pas retiré son colis est relancé à J+3 et J+7 ; à J+14, la livraison est réputée acquise, la campagne est terminée et la réputation créditée | 4 | S | **partielle** | Les données existent : `Campagne.mise_a_disposition_le` (posé par `mettre_a_disposition`), `Notification.Genre.RELANCE_RETRAIT` et `Participation.delai_retrait_depasse` (14 jours, `commandes/models.py`). **Rien ne s'en sert** : il n'y a ni tâche, ni passage à `terminee`, ni crédit de réputation |

**Pourquoi chacune est MVP** (cas discutables) :
- F-021 : la réputation remplace l'arbitrage, que la plateforme refuse (§2). Sans elle, la plainte d'un acheteur n'a aucun effet.
- F-029 et F-030 : ce sont des garanties non négociables, inscrites dans `CLAUDE.md` (« Les décisions à ne pas défaire »).
- F-031 : sans elle, un seul colis non retiré bloque la campagne en `distribution` pour toujours. L'aboutissement « campagne terminée, réputation créditée » n'est alors plus atteignable.
- F-016 : c'est la règle « l'argent ne repart pas tout seul, le groupeur décide » (§4). Sans les deux boutons, seule l'issue automatique du 7e jour reste possible.

## Hors MVP
| ID | Rôle | Fonctionnalité | § | État constaté | Note |
|---|---|---|---|---|---|
| F-032 | Acheteur | Demandes communautaires + « moi aussi » | 4 | constatée | `echanges/vues.py::DemandeProduitVueEnsemble` · `pages/Communaute.tsx` |
| F-033 | Acheteur | « J'aime » sur un message | 7 | constatée | `CommentaireVueEnsemble.jaime` · `Discussion.tsx` |
| F-034 | Administrateur | Clôture forcée d'une campagne | — | **partielle** | route `admin/campagnes/<pk>/cloturer/` (`api.py`) **sans écran** : aucun appel dans `frontend/admin/src/`. Le backlog la note « partielle » depuis le 2026-10-26 |
| F-035 | Visiteur | Trier le fil par popularité | 7 | absente | `nombre_jaime` existe ; `CommentaireVueEnsemble` n'accepte aucun paramètre de tri |
| F-036 | Groupeur | Convertir une demande communautaire en campagne | 4 | absente | |
| F-037 | Acheteur | Choisir entre être livré et venir récupérer | 3 | absente | Q1 tranchée ([[2026-10-26-decisions-carte]]) : retrait seul au MVP ; n'est plus bloquée |
| F-038 | Groupeur | Désigner la personne qui remet les colis | 4 | absente | `remise_par` est enregistré (c'est le groupeur connecté) |
| F-039 | Groupeur | Scanner le QR avec la caméra | 4 | absente | `FeuilleScan` : saisie ou collage du contenu du QR |
| F-040 | Système | Tracer les frais d'opérateur des remboursements | 4 | absente | `rembourser` ne les enregistre pas |
| F-041 | Groupeur / Administrateur | Abonnements des groupeurs | — | absente (reportée) | Q3 tranchée ([[2026-10-26-decisions-carte]]) : reste reportée |
| F-042 | Administrateur | Refuser un décaissement, avec motif et notification | 3 | absente | créée par Q9 ([[2026-10-26-decisions-carte]]) ; ni route ni bouton |
| F-043 | Acheteur | Reprendre ou abandonner une part dont le paiement a été refusé | 3 | absente | créée par Q10 ([[2026-10-26-decisions-carte]]) ; à faire avant tout vrai opérateur |

Capacités observées le 2026-10-26, tranchées depuis ([[2026-10-26-decisions-carte]]) : refuser un décaissement → F-042 (Q9) ; reprendre ou abandonner une part non payée → F-043 (Q10) ; annulation par le groupeur d'une campagne `en_cours` ou `financee`, que le service autorise mais qu'aucun écran ne propose → gardée (Q6), sans identifiant.

## Contradictions et questions
### Contradictions et zones floues
Une ligne par écart, avec ses deux sources. Celles marquées *(connue)* viennent de `02-decisions/2026-10-26-questions-ouvertes.md`. Statut au 2026-10-27 : **tranchée** (décision prise, renvoi entre parenthèses ; l'application peut rester à faire), **résolue** (le code est aligné), ou **ouverte**.

- **C-1** *(connue)* Livraison ou retrait : le §3 groupeur 5 dit « le participant décide d'être livré ou vient récupérer », et le §3 acheteur 5 parle du « livreur ». Le §4 Distribution dit « pas de flotte de livreurs… point de retrait ». Le code ne fait que le retrait. → Q1. **Tranchée** ([[2026-10-26-decisions-carte]], Q1) ; réécriture du §3 à faire (C-003)
- **C-2** *(connue)* Qui décaisse : le §3 groupeur 4 dit « retire 100 % », le §3 admin 4 et le §6 disent « libère » et « action administrateur ». Dans le code, le groupeur demande et l'administrateur exécute. → Q2. **Tranchée** ([[2026-10-26-decisions-carte]], Q2) ; §3 à réécrire (C-003)
- **C-3** *(connue)* Abonnements (F-041) : ils contredisent le §2 « outil gratuit », le §4 « aucun abonnement » et `CampagneGroupeur.tsx` (« Aucun abonnement, aucune commission »). → Q3. **Tranchée** ([[2026-10-26-decisions-carte]], Q3 : reportés)
- **C-4** « Livré ou remboursé » : le §2 et `FicheCampagne.tsx` (« bloqués jusqu'à la livraison ») disent que l'argent attend la livraison. Le §3 groupeur 4 et `paiements/services.py` (`executer_decaissement` avant `mettre_a_disposition`, `annuler` refusé après) libèrent 100 % **avant** la distribution. Le §4 « consignés jusqu'à sa clôture » ne dit pas de quelle clôture il s'agit. → Q4. **Tranchée** ([[2026-10-26-decisions-carte]], Q4) ; textes encore présents au commit `abaa622` (`FicheCampagne.tsx`, lignes 374 et 758) : chantier C-009, tâche T6
- **C-5** Pièces KYC : le §3 groupeur 1 dit « soumet ses pièces (CNI / passeport) ». `comptes/serialiseurs.py` les rendait facultatives et `pages/Profil.tsx` ne permettait pas de les déposer. → Q5. **Résolue** : tranchée ([[2026-10-26-decisions-carte]], Q5), appliquée par F-011 (`abaa622`, recette OK)
- **C-6** Annulation : le §9 ne la prévoit que depuis `minimum_non_atteint`. `paiements/services.py::annuler` l'accepte depuis `en_cours` et `financee`, et la route du groupeur l'expose. → Q6. **Tranchée** ([[2026-10-26-decisions-carte]], Q6 : gardée) ; §9 à compléter (C-003)
- **C-7** Clôture anticipée : le §4 dit « à la date limite, la collecte se ferme automatiquement ». `espaces/groupeur.py::cloturer` et le bouton « Clôturer la collecte » la permettent avant l'heure. → Q7. **Tranchée** ([[2026-10-26-decisions-carte]], Q7 : gardée) ; §4 et §9 à compléter (C-003)
- **C-8** Texte de l'écran contraire au §4 : `CampagneGroupeur.tsx` (statut `en_cours`) dit « au-delà de la date limite, la campagne est annulée et tout le monde est remboursé ». Le §4 dit qu'elle n'est pas annulée et que l'argent attend la décision. (C'est le texte qui est à corriger, pas la règle.) **Tranchée** ([[2026-10-26-decisions-carte]], Q4) ; texte encore présent au commit `abaa622` (`CampagneGroupeur.tsx`, ligne 167) : chantier C-009, tâche T6
- **C-9** Historique : le §4 dit « consultable par ceux qui y ont participé ». Avec `catalogue/vues.py` (`STATUTS_CONSULTABLES`, `AllowAny`), la fiche s'ouvre pour n'importe qui connaît l'adresse. → Q8. **Tranchée** ([[2026-10-26-decisions-carte]], Q8 : quiconque a l'adresse) ; §4 à réécrire (C-003)
- **C-10** Consignation : le §6 et le §3 admin 3 en font une action de la console. Dans `encaisser`, elle est automatique au paiement. **Ouverte** : aucune question ni décision ne la couvre, et C-003 ne cite pas le §6
- **C-11** Rôle : le §5 dit « rôle demandé à l'inscription ». `Authentification.tsx` ne le demande pas ; le rôle bascule au dépôt du dossier KYC (`DossierKYCVue`). → Q12. **Tranchée** ([[2026-10-26-decisions-carte]], Q12) ; §5 à réécrire (C-003) ; reste côté serveur : `InscriptionSerialiseur` accepte `role=groupeur` (C-019)
- **C-12** Médias sans Cloudinary : `CLAUDE.md` dit « tout retombe sur le disque local ». `televersement.ts` ne passe que par la signature, qui répond 503 sans `CLOUDINARY_*`. → Q11. **Tranchée** ([[2026-10-26-decisions-carte]], Q11 : variables exigées) ; `CLAUDE.md` à corriger (C-004), variables sur achatgr.com à vérifier (C-008)
- **C-13** Statut `decaissee` : il figure au §9 et dans `Campagne.Statut`, mais n'est jamais posé (`executer_decaissement` passe de `financee` à `approvisionnement`). → Q14. **Tranchée** ([[2026-10-26-decisions-carte]], Q14 : retrait) ; toujours dans `catalogue/models.py` au commit `abaa622` (C-005)
- **C-14** Nombre de tests : `CLAUDE.md` et `README.md` disent 110 ; `testing-stack.md` en dit 165. Au 2026-10-27, on compte 246 fonctions `test_` et la suite exécute 308 tests (« Vérifier » de F-011). **Ouverte, sans question** : prise en charge par le chantier C-004 du backlog, qui doit retenir le nouveau compte
- **C-15** Règle sans chiffre ni sortie : le §4 « relances J+3, J+7, clos à J+14 » ne dit ni le canal, ni le statut de la part non retirée, ni si elle compte dans « participants servis ». → Q13. **Tranchée** ([[2026-10-26-decisions-carte]], Q13) ; à appliquer par F-031 (T5)
- **C-16** Liens de notification : `paiements/services.py` écrivait `/participations/<id>`, alors que la boutique sert `/mes-achats/:id` (`App.tsx`). Écart de code à code (F-008). **Résolue** par F-008 (`769ec1a`, recette OK)

### Questions ouvertes
Au 2026-10-27 : quinze questions tranchées le 2026-10-26 ([[2026-10-26-decisions-carte]]), une ouverte (Q15, action de l'utilisateur hors dépôt).

1. **Livraison ou retrait ?** Options : (a) retrait seul, et réécriture du §3 ; (b) livraison en option, payée par l'acheteur, code validé par le livreur. Recommandation : (a) pour le MVP, (b) reste F-037.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q1) : retrait seul, au point de retrait. La livraison reste F-037 (hors MVP). Le §3 du cahier des charges est à réécrire (C-003).**
2. **Qui décaisse ?** Options : (a) le groupeur demande, l'administrateur exécute (le code actuel) ; (b) versement automatique à la clôture. Recommandation : (a), et réécrire le §3 groupeur 4 en « demande le retrait ».

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q2) : option (a). Le groupeur demande, l'administrateur exécute. §3 à réécrire (C-003).**
3. **Abonnements** : les trois questions de `02-decisions/2026-10-26-questions-ouvertes.md` restent ouvertes. Recommandation : rester en `reportée`.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q3) : les abonnements restent reportés (F-041). Aucune ligne de code.**
4. **Que promet exactement « livré ou remboursé » ?** Options : (a) garder la libération avant la distribution (le groupeur a besoin des fonds pour acheter, §3) et réécrire la promesse et le texte de `FicheCampagne.tsx` (« remboursé si la campagne n'aboutit pas ») ; (b) ne libérer qu'après la distribution ; (c) libération partielle (avance, puis solde au retrait). Recommandation : (a), qui est le code actuel, avec le texte d'écran corrigé ; (b) et (c) changent le modèle.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q4) : option (a). Les fonds sont libérés avant la distribution, comme le code actuel. Corriger la promesse « bloqués jusqu'à la livraison » (§2 et `FicheCampagne.tsx`) et le texte de `CampagneGroupeur.tsx` (C-8) : chantier C-009.**
5. **Les pièces KYC sont-elles obligatoires ?** Options : (a) champ recto / verso dans « Devenir groupeur », obligatoire côté serveur ; (b) facultatives, et l'administrateur juge sur le numéro seul. Recommandation : (a), le §3 l'exige et la console sait déjà les afficher.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q5) : option (a). Champ recto / verso dans `Profil.tsx` et obligation côté serveur, dans F-011. Appliquée : F-011, commit `abaa622`, recette OK.**
6. **Le groupeur peut-il annuler une campagne `en_cours` ou `financee` ?** Options : (a) oui, et le §9 est complété ; (b) non, et le service est restreint à `minimum_non_atteint`. Recommandation : trancher avant la recette, parce que la route est ouverte aujourd'hui sans écran.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q6) : option (a). Annulation gardée ; §9 complété (C-003).**
7. **Clôture anticipée par le groupeur** : (a) on la garde et on l'inscrit au §4 / §9 ; (b) on la retire. Recommandation : (a), elle ne lèse personne si le minimum est atteint ; sinon, elle mène à la décision normale.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q7) : option (a). Clôture anticipée gardée ; inscrite au §4 et au §9 (C-003).**
8. **Qui peut rouvrir une campagne sortie du catalogue ?** Options : (a) quiconque a l'adresse (le code actuel ; le fil est public de toute façon) ; (b) seulement les participants et le groupeur. Recommandation : (a), en réécrivant le §4.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q8) : option (a). Consultable par quiconque a l'adresse ; §4 réécrit (C-003).**
9. **Refuser un décaissement** (inscrit au backlog sous F-024, sans route ni bouton) : (a) hors MVP, retiré de F-024 ; (b) MVP, avec motif et notification. Recommandation : (a), le cahier des charges ne le demande pas.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q9) : option (a). Hors MVP : nouvelle ligne F-042 au backlog. Déjà retiré de F-024.**
10. **Paiement refusé** : la part reste « en attente » et bloque la campagne pour cet acheteur. Options : (a) hors MVP tant que le paiement est simulé ; (b) ajouter « reprendre le paiement / abandonner la part » maintenant. Recommandation : (a), mais avant tout branchement d'un vrai opérateur.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q10) : option (a). Hors MVP tant que le paiement est simulé : ligne F-043. À faire avant tout vrai opérateur.**
11. **Médias sans Cloudinary** : (a) écrire le repli local dans `televersement.ts` ; (b) corriger `CLAUDE.md` et exiger les variables partout. Recommandation : (b) pour la production, et vérifier que les variables sont posées sur `achatgr.com` ; (a) seulement si la démonstration doit tourner sans compte.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q11) : option (b). Les variables `CLOUDINARY_*` sont exigées partout ; `CLAUDE.md` corrigé (C-004). Vérification des variables sur achatgr.com : action de l'utilisateur (C-008).**
12. **Rôle à l'inscription** : (a) réécrire le §5 (« on devient groupeur depuis son profil ») ; (b) ajouter le choix à l'inscription. Recommandation : (a), c'est le parcours en place.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q12) : option (a). §5 réécrit : on devient groupeur depuis son profil, pas de choix de rôle à l'inscription (C-003).**
13. **Ce qui se passe à J+14 (F-031)** : canal des relances (notification seule, ou SMS simulé aussi) ; statut de la part (`retiree` sans `retiree_le`, ou un nouveau statut « réputée livrée ») ; compte ou non dans « participants servis ». Recommandation : notification seule, un statut distinct, pas de comptage dans « participants servis » (aucune preuve de remise). À trancher avant d'écrire F-031.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q13) : notification seule à J+3 et J+7. À J+14, la part non retirée passe dans un statut distinct « réputée livrée », non comptée dans les participants servis ; la campagne passe `terminee` et la réputation est créditée. Précisé dans F-031.**
14. **Statut `decaissee`** : (a) le poser à l'exécution, avant `approvisionnement` ; (b) le retirer du §9 et du modèle. Recommandation : (b) si personne n'en a l'usage, par une migration revue par `archi-backend`.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q14) : option (b). Statut `decaissee` retiré du §9 et du modèle, par une migration revue par `archi-backend` (C-005).**
15. **La tâche horaire est-elle planifiée sur Coolify ?** C'est à vérifier dans Coolify, hors dépôt. Sans elle, F-027, F-028 (et demain F-031) ne tournent pas en production.

   **Ouverte — en attente de l'utilisateur ([[2026-10-26-decisions-carte]], Q15) : vérification de la planification horaire sur Coolify par l'utilisateur (C-007).**
16. **Plafond en base de la somme libéré + remboursé** (F-029) : (a) ajouter la contrainte `montant_libere + montant_rembourse <= montant_consigne` ; (b) s'en tenir au service. Recommandation : (a), dans l'esprit de `CLAUDE.md` ; à soumettre à `regles-auditor`.

   **Tranchée le 2026-10-26 ([[2026-10-26-decisions-carte]], Q16) : option (a). Contrainte `montant_libere + montant_rembourse <= montant_consigne` à ajouter (C-006), migration à valider par l'utilisateur, puis à soumettre à `regles-auditor`.**

## Compte
**31 fonctionnalités MVP au commit `abaa622` : terminées 4 · constatées 26 · partielles 1 · absentes 0.**
Le 2026-10-26 (commit `ccd9187`) : terminées 0 · constatées 27 · partielles 4 · absentes 0.

| Rôle | MVP | Terminées | Constatées | Partielles | Absentes |
|---|---|---|---|---|---|
| Visiteur | 4 | 0 | 4 (dont F-021 KO à la recette T1) | 0 | 0 |
| Acheteur | 8 | 2 (F-008, F-011) | 6 (dont F-005, F-009, F-010 KO à la recette T1) | 0 | 0 |
| Groupeur | 9 | 1 (F-016) | 8 | 0 | 0 |
| Administrateur | 5 | 0 | 5 (dont F-024 KO à la recette T1) | 0 | 0 |
| Système | 5 | 1 (F-030) | 3 | 1 (F-031) | 0 |

Rapprochement avec [[backlog]] (21 constatées, 6 à faire, 4 terminées) : les 26 constatées de la carte comprennent les cinq fonctionnalités en échec à la recette T1 (F-005, F-009, F-010, F-021, F-024), que le backlog note `à faire` ; la partielle F-031 y est aussi `à faire`.

**Aboutissements sans chemin complet** : le colis non retiré, et la campagne terminée malgré un absent (F-031, partielle) ; l'acheteur à rembourser après un décaissement non suivi de livraison (hors chemin par décision, Q4) ; le paiement refusé, qui bloque la part (hors MVP, F-043, Q10). Ne sont plus des trous depuis le 2026-10-26 : le groupeur qui maintient ou renonce (F-016) et le badge de groupeur obtenu sans pièces (F-011).

**Chemins présents mais en échec à la recette T1** : participer et payer (F-005), le fil (F-009), l'avis et la réputation (F-010, F-021), le décaissement (F-024, double paiement critique). Tâches T10 à T12 de [[M-001-terminer-le-mvp]].

Recettes jouées : la recette T1 (état des lieux, 2026-10-26), puis une recette par fonctionnalité le 2026-10-27 pour F-030, F-016, F-008 et F-011 (RECETTE OK, fiches dans `03-fonctionnalites/`). La recette de bout en bout du MVP (T7) reste à jouer.
