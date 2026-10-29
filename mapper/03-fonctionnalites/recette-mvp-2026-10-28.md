---
type: recette
statut: terminée
date: 2026-10-28
commit: a4d0035
tags: [recette, mvp, T7, M-001]
---
# Recette du MVP — 2026-10-28 (tâche T7 de M-001)

**RECETTE MVP OK** — aucun défaut bloquant pour la présentation. Les défauts gênants ou cosmétiques sont listés ci-dessous (C-064 à C-071, C-073 à C-076) ; deux méritent d'être corrigés avant la démonstration (C-064, C-066).

Version recettée : `staging` au commit `a4d0035` (F-009 absent). Copie extraite par `git archive`, base SQLite jetable remplie par `charger_demo`, une seule origine Django qui sert les deux interfaces compilées (`localhost:8123` boutique, `admin.localhost:8123` console), `DJANGO_ORIGINES_SURES` posé dans l'environnement du processus, aucun `.env` lu. Chrome headless à 390 px (accueil et console admin aussi à 1280 px). L'état a été relu en base (séquestre, participations, notifications) à chaque étape d'argent. Tous les serveurs lancés ont été arrêtés.

## Ce qui a été joué, de bout en bout

| Rôle | Parcours rejoué (vraies sessions) | Résultat |
|---|---|---|
| Visiteur | accueil (390 et 1280), catalogue (recherche « riz », recherche sans résultat, rayons), fiche, réputation et avis, brouillon d'autrui, inscription par l'écran, code SMS affiché, vérification qui ouvre la session | OK |
| Acheteur | connexion, profil, participation de 9 pièces qui franchit le palier, paiement, confirmation, QR, Mes achats (liste et détail), historique d'une campagne annulée, notifications (28 liens contrôlés), fil (écrire, répondre), avis (publier), dépôt KYC avec deux pièces | OK |
| Groupeur | écran d'attente KYC, KYC rejeté puis redépôt, création de campagne avec palier, publication, tableau de bord, clôture, maintenir, renoncer, demande de retrait, mise à disposition, validation de codes (faux, autre campagne, bon), réponse sous un avis, réponse dans le fil | OK |
| Administrateur | connexion console, refus d'un compte non équipe, dossiers (valider, refuser sans motif puis avec motif), pièces affichées, décaissement, modération (masquer, rétablir), tableau de bord | OK |
| Système | `cloturer_les_campagnes_echues` (clôture, remboursement après 7 jours, relances J+3 et J+7, clôture à J+14), `controler_les_sequestres`, pièces KYC jamais publiques | OK |

### Chiffres relus en base
- Participation de 9 pièces sur « Riz Délice » (campagne 1) : la fenêtre annonce 148 500 FCFA (16 500 × 9, palier 20 pièces franchi) ; la participation enregistrée vaut `montant_total = 148 500`. **Prix affiché = prix facturé** (C-013 tient). Séquestre de la campagne : 198 000 + 148 500 = 346 500 consignés. Notifications au payeur (« Paiement enregistré », lien `/mes-achats/41`) et au groupeur (« Nouveau paiement », « Minimum atteint »).
- Décaissement de la campagne 1 : brut 346 500, frais 1 500, net 345 000. Décaissement de la campagne 7 exécuté depuis la console : séquestre 475 000 consignés, 475 000 libérés, campagne passée en `approvisionnement` puis `distribution` ; notification « Fonds versés » avec lien `/groupeur/campagnes/7`.
- « Renoncer et rembourser » sur les baskets (campagne 11) : consigné 50 000, remboursé 50 000, deux participations `remboursee`, notifications « Groupage annulé » et « Remboursement effectué ».
- Campagne 40 (minimum non atteint) : clôture, puis `cloturee_le` reculé de 8 jours, la commande remboursée en entier (10 000 consignés, 10 000 remboursés) et deux parts `remboursee`.
- Campagne 39 maintenue : elle passe `financee`, 20 000 FCFA collectés, la demande de retrait affiche « 18 500 FCFA en route » (brut − 1 500).
- Relances sur la campagne 8 (temps avancé) : J+3 (« Votre colis vous attend »), J+7 (« Dernier rappel »), J+14 : campagne `terminee`, trois parts `reputee_livree`, une `retiree`, réputation du groupeur 2 → 3 campagnes terminées, 6 participants servis. La clôture attend bien le préavis de la relance J+7.
- `controler_les_sequestres` : « Aucune anomalie ».
- Tableau de bord de l'administration : consigné 2 974 500 − libéré 829 000 − remboursé 60 000 = détenu 2 085 500. L'identité tient.

## Matrice des 31 fonctionnalités

| ID | Rôle | Verdict | Preuve courte |
|---|---|---|---|
| F-001 | Visiteur | OK avec réserve | catalogue, recherche, rayons, vide : OK. Au-delà de 20, la liste affiche 20 cartes sous « 32 campagnes » : pas de pagination (C-010). Sans effet avec les 7 campagnes de démonstration |
| F-002 | Visiteur | OK avec réserve | inscription par l'écran, code SMS affiché (509543), vérification puis session ouverte, `/comptes/moi` 200. Réserves : `role=groupeur` encore accepté (C-019, 201 constaté), débordement horizontal 390→486 px sur connexion et inscription (C-066) |
| F-004 | Visiteur | OK | fiche, paliers, jauge, remise, réputation « 4.00/5, 2 campagnes menées à terme » ; brouillon : « Cette campagne est introuvable » |
| F-021 | Visiteur | OK | réputation recalculée après J+14 (2 → 3 terminées, 5 → 6 servis) ; avis d'autrui non modifiables |
| F-003 | Acheteur | OK | connexion, profil ; la déconnexion n'a pas été rejouée à l'écran |
| F-005 | Acheteur | OK | prix affiché = prix facturé ; confirmation « Paiement confirmé », code de retrait, « Voir mon QR code » ; double paiement : 200 puis 400 lisible ; quantité 0 ou négative : 400 ; campagne close : 400 |
| F-006 | Acheteur | OK avec réserve | liste, détail, QR visible ; textes faux sur une part retirée ou remboursée (« Ce code deviendra actif… », C-022) |
| F-007 | Acheteur | OK | fiches des campagnes 11 et 40 annulées lisibles avec bandeau « Groupage annulé » et motif |
| F-008 | Acheteur | OK avec réserve | 28 liens de la page testés, tous vers des écrans existants ; « Remboursement effectué » sans lien (C-017) |
| F-009 | Acheteur | **KO (intégrité, hors parcours)** | lecture sans compte, écriture et réponse OK à l'écran. Mais : `reponse_a` d'une autre campagne accepté (201), commentaire sur un brouillon accepté (201), POST sur une campagne inexistante : **500** HTML (C-068). Fiche F-009 non fusionnée dans ce commit |
| F-010 | Acheteur | OK | avis publié (réputation 4.00 conservée, 7 avis) ; PATCH et DELETE par un tiers : 403 ; deuxième avis sur la même part : 400 |
| F-011 | Acheteur | OK | dépôt avec deux pièces par l'écran, statut « Dossier en cours » ; fichier texte refusé (400 lisible) ; dépôt sans pièce refusé |
| F-012 | Groupeur | OK | écran d'attente, écran « Dossier à corriger » avec le motif, bouton « Corriger mon dossier » |
| F-013 | Groupeur | OK | création avec palier (3 600 FCFA à partir de 20), brouillon, « Publier » ; brouillon introuvable côté public |
| F-014 | Groupeur | OK avec réserve | sans `CLOUDINARY_*` : `POST /groupeur/medias/signature/` répond 503 et l'écran dit « L'hébergement d'images n'est pas configuré. » ; la campagne se crée quand même sans photo. **Aucune image dans la démonstration** : cartes avec une lettre (C-008) |
| F-015 | Groupeur | OK avec réserve | « Qui a payé » nominatif correct ; la tuile « Consigné en séquestre » du tableau de bord affiche 2 734 500 FCFA alors que 2 380 500 sont réellement détenus (C-064) |
| F-016 | Groupeur | OK | maintenir (campagne 39) et renoncer (campagne 11) à l'écran, remboursement automatique à 7 jours (campagne 40) ; pas de confirmation avant de renoncer (C-026) |
| F-017 | Groupeur | OK avec réserve | feuille de retrait puis « Demande enregistrée — 18 500 FCFA en route » (C-011 tient) ; bouton « Demander le retrait » toujours affiché ensuite ; une seconde demande donne « Un décaissement a déjà été demandé. » (C-012) |
| F-018 | Groupeur | OK | « Prévenir les participants » : campagne en `distribution`, notifications avec point de remise et code ; aucun message de confirmation avant l'action |
| F-019 | Groupeur | OK | code faux : « Code inconnu pour cette campagne » ; code d'une autre campagne : « Ce QR code ne concerne pas cette campagne » ; bon code : bannière « Colis remis à Yao Dossou », compteur 1/4 |
| F-020 | Groupeur | OK avec réserve | réponse dans le fil (marquée « Groupeur ») et sous un avis à l'écran ; un tiers reçoit 403. Mais le serveur laisse réécrire une réponse déjà donnée (200), alors que l'écran promet « une seule fois » (C-065) |
| F-022 | Administrateur | OK avec réserve | compte de l'équipe : tableau de bord ; compte acheteur : accès refusé mais message faux « Connexion impossible. Vérifiez votre réseau. » (C-067) |
| F-023 | Administrateur | OK | pièces recto et verso affichées (`/pieces/6/recto/` 600 px) ; rejet sans motif : « Indiquez ce que le groupeur doit corriger » (400) ; rejet avec motif : le groupeur lit le motif ; validation : « Dossier validé » et espace ouvert |
| F-024 | Administrateur | OK avec réserve | libération du séquestre, campagne en approvisionnement, « Fonds versés » ; le geste est immédiat, sans confirmation (C-071) |
| F-025 | Administrateur | OK avec réserve | masquer puis rétablir : le message sort du fil public puis y revient ; rien n'est supprimé ; un acheteur reçoit 403. L'écran ne demande aucun motif (C-069) |
| F-026 | Administrateur | OK avec réserve | séquestre cohérent ; tableau de bord incomplet : « distribution » toujours non comptée (C-018) |
| F-027 | Système | OK | deux campagnes échues clôturées en `minimum_non_atteint`, notifications « Décision attendue » et « Le groupage n'a pas abouti » |
| F-028 | Système | OK | 7 jours sans décision : remboursement, statut `annulee` |
| F-029 | Système | OK | `controler_les_sequestres` : aucune anomalie après tous les mouvements ci-dessus |
| F-030 | Système | OK | `/medias/kyc/…`, `%2e%2e`, `//`, `KYC` : 404 ; `/pieces/…` : 200 pour l'administrateur, 404 pour visiteur, acheteur et groupeur |
| F-031 | Système | OK | voir « Relances » ci-dessus |

Totaux : 14 OK, 16 OK avec réserve, 1 KO (F-009, intégrité hors parcours, non fusionné), 0 KO sur un parcours.

## C-063 tranché
`GET /api/catalogue/campagnes/<id>/` d'un **brouillon** répond **404** à un visiteur, à un acheteur, à l'administrateur et même au groupeur propriétaire (celui-ci passe par `/groupeur/campagnes/<id>/`). Aucune fuite. Seul reste : le corps du 404 est en anglais (« No Campagne matches the given query. »), invisible à l'écran qui affiche « Cette campagne est introuvable. » (voir C-023).

## Défauts classés

Aucun défaut bloquant pour la présentation.

### Gênants

**C-064 — Tuile « Consigné en séquestre » fausse (F-015)**
- Étape : tableau de bord groupeur (compte 90001122).
- Attendu : le montant réellement détenu en séquestre (2 380 500 FCFA).
- Obtenu : 2 734 500 FCFA. C'est la somme de toutes les parts payées, y compris celles dont les fonds sont déjà libérés (354 000 FCFA). La console administration affiche un séquestre détenu différent, ce qui se voit si on montre les deux écrans.
- Cause probable : `backend/groupachat/espaces/groupeur.py:~400` (`collecte.montant_consigne` = somme de `montant_total` des parts payées) ; libellé dans `frontend/boutique/src/pages/groupeur/TableauDeBord.tsx:72`. La comptabilité elle-même est juste : seul l'intitulé ou le calcul est faux. Contournement : ne pas commenter cette tuile.
- À corriger avant la démonstration si possible (c'est un chiffre d'argent), sinon renommer l'intitulé en « Collecté ».

**C-065 — Réponse du groupeur sous un avis réécrivable (F-020)**
- Étape : `POST /api/avis/7/repondre/` deux fois.
- Attendu : refus de la seconde réponse (« une seule fois »).
- Obtenu : 200 et le texte est écrasé (« deuxieme »). L'écran, lui, cache le formulaire après la première réponse.
- Cause probable : `backend/groupachat/commandes/vues.py:159-177` (`repondre` ne teste pas `avis.reponse`).

**C-066 — Défilement horizontal sur connexion et inscription (F-002)**
- Étape : `/connexion` et `/inscription` à 390 px.
- Obtenu : largeur de page 486 px pour 390 px d'écran (la page se déplace sur le côté).
- Cause probable : pastille décorative `absolute -right-24 -top-10 size-72` dans le gabarit d'authentification (`frontend/boutique/src/pages/Authentification.tsx`), sans `overflow-hidden` sur son conteneur. Les autres pages tiennent dans 390 px.

**C-067 — Message faux à la connexion d'un compte non équipe (F-022)**
- Étape : console d'administration, connexion avec 91002233 (acheteur).
- Attendu : « Ce compte n'appartient pas à l'équipe. ».
- Obtenu : « Connexion impossible. Vérifiez votre réseau. ». La session côté serveur est ouverte quand même.
- Cause : `frontend/admin/src/App.tsx:130-135` lève une `Error` ordinaire, et `frontend/commun/src/outils/requetes.ts:48-51` la convertit en message réseau faute d'être une `ErreurApi`.

**C-068 — 500 sur un commentaire pour une campagne inexistante (F-009)**
- Étape : `POST /api/campagnes/999/commentaires/` connecté.
- Obtenu : 500 (page HTML). Voisin : `reponse_a` d'une autre campagne (201), commentaire sur un brouillon (201). Aucun accès depuis l'écran. Fiche F-009 prête, hors de ce commit.

**C-071 — Gestes irréversibles sans confirmation**
- « Libérer 345 000 FCFA » (console), « Prévenir les participants » et « Renoncer et rembourser » (groupeur) s'exécutent au premier toucher. Risque de fausse manœuvre pendant la démonstration. Voir C-026 pour le seul « Renoncer ».

**C-010 — rappel** : catalogue sans pagination au-delà de 20 (confirmé ; page_size=24 ignoré par le serveur, 20 renvoyés).

**C-008 — rappel** : aucune photo dans la démonstration sans `CLOUDINARY_*` ; cartes avec une lettre sur fond coloré.

### Cosmétiques

**C-069** — Modération : l'écran masque sans demander de motif ; la carte (« masquer avec un motif ») et le champ `motif` du serveur le prévoient. `frontend/admin/src/pages/Decaissements.tsx` (composant `Moderation`).

**C-070** — Console du navigateur : `GET /api/comptes/moi/` renvoie 403 pour tout visiteur à chaque chargement (bruit rouge dans la console, aucune incidence à l'écran). Renvoyer 200 avec `null` ou 401 muet.

**C-073** — Part remboursée : l'écran affiche encore un code de retrait et le formulaire « Comment s'est passé ce groupage ? » (C-022). Une part retirée affiche « Ce code deviendra actif… ».

**C-074** — 404 de `/pieces/…` et `/medias/…` : page HTML anglaise (C-023, inchangé). Même chose pour le corps JSON des 404 de l'API (« No Campagne matches… »).

**C-075** — Avatars « KS », « NA » rognés sur la gauche dans la liste des dossiers de la console à 390 px (capture `ad4-dossiers-390.png`).

**C-076** — Inscription : la première requête met trois secondes avant le code (hachage), l'écran garde le bouton « Continuer » en rotation sans autre retour. Acceptable, à savoir pour la démonstration.

### Constatés déjà connus, inchangés
C-012 (bouton « Demander le retrait » encore affiché), C-017 (« Remboursement effectué » sans lien), C-018 (tableau de bord admin incomplet), C-019 (`role=groupeur` accepté à l'inscription : confirmé, 201), C-022, C-023, C-026 (aucune confirmation avant de renoncer).

## Régressions croisées : aucune
- C-009, C-011, C-013 : confirmations affichées après `recharger()` (paiement, retrait de fonds, bannière de remise), prix affiché = prix facturé.
- F-008 : liens de notification valides, y compris « Fonds versés » vers l'espace groupeur.
- F-010, F-024, F-030, F-031 : refus tiers, double paiement 400, pièces privées, relances.
- F-016 + F-031 : remboursement après 7 jours et clôture J+14 enchaînés dans la même tâche sans conflit.
- Une série de connexions rapprochées (une centaine pendant la recette) déclenche la limite `connexion` (429 « Requête ralentie ») : normal, mais **ne pas répéter des dizaines de connexions pendant la démonstration**. Redémarrer le serveur remet le compteur à zéro.

## Ce qui n'a pas pu être testé
- Téléversement Cloudinary réel (variables absentes) : seul le refus propre a été constaté.
- Planification Coolify de la tâche horaire (C-007) et variables `CLOUDINARY_*` en production (C-008) : actions de l'utilisateur.
- Sous PostgreSQL : deux `annuler` simultanés (C-031). Tout a été joué sous SQLite.
- Déconnexion à l'écran (F-003) et mode sombre : non rejoués.
- Suite pytest complète : lancée dans la copie puis arrêtée à environ 49 % (aucun échec jusque-là, un test ignoré) ; elle n'a pas été menée à terme.

## Captures (390 px sauf mention)
Dossier : `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/37d3c70e-6597-49b8-bb11-132f1e1eb6a5/scratchpad/t7/cap/`
- visiteur : `v1-accueil-390.png`, `v2-catalogue-390.png`, `v3-recherche-riz-390.png`, `v4-recherche-vide-390.png`, `v5-fiche-1-390.png`, `v6-fiche-9-terminee-390.png`, `v7-inscription-390.png`, `v8-code-sms-390.png`, `v9-apres-verification-390.png`
- acheteur : `a1-profil-390.png`, `a2-mes-achats-390.png`, `a3-feuille-participer-390.png`, `a4-feuille-q9-390.png`, `a5-apres-paiement-390.png`, `a6-detail-achat-390.png`, `a7-avis-form-390.png`, `a8-avis-publie-390.png`, `a9-notifications-390.png`, `a10-fil-repondre-390.png`, `a11-kyc-form-390.png`, `a12-kyc-rempli-390.png`, `a13-kyc-depose-390.png`, `a14-communaute-390.png`
- groupeur : `g1-attente-kyc-390.png`, `g2-tableau-vide-390.png`, `g3-nouvelle-390.png`, `g4-media-sans-cloudinary-390.png`, `g5-palier-390.png`, `g6-creee-390.png`, `g7-tableau-390.png`, `g8-camp1-390.png` à `g8-camp12-390.png`, `g9-publie-12-390.png`, `g10-renoncer-390.png`, `g11-cloture-1-390.png`, `g12-retrait-feuille-390.png`, `g13-retrait-demande-390.png`, `g14-approvisionnement-390.png`, `g15-mise-a-dispo-390.png`, `g16-code-faux-390.png`, `g17-code-autre-campagne-390.png`, `g18-code-ok-390.png`, `g19-reponse-avis-390.png`, `g20-fil-groupeur-390.png`, `g21-decision-390.png`, `g22-maintenu-390.png`, `g23-confirmation-retrait-390.png`, `g24-kyc-rejete-390.png`, `g25-redepot-390.png`
- administrateur : `ad1-connexion-1280.png`, `ad2-tableau-1280.png`, `ad3-tableau-390.png`, `ad4-dossiers-390.png`, `ad5-dossier-detail-390.png`, `ad6-rejet-sans-motif-390.png`, `ad7-valide-390.png`, `ad8-decaissements-390.png`, `ad9-executer-390.png`, `ad10-moderation-390.png`, `ad11-masquer-motif-390.png`, `ad12-masques-390.png`
- 1280 px : `w1-accueil-1280.png`, `w2-catalogue-1280.png`, `w3-admin-tableau-1280.png`, `w4-admin-dossiers-1280.png`, `w4-admin-decaissements-1280.png`, `w4-admin-moderation-1280.png`

Défauts bloquants : aucun.
