---
type: fonctionnalite
id: T16
statut: terminée
couvre: [C-064, C-065, C-066, C-067, C-071, C-026]
mission: M-001 (T16)
base: 60b6cbd
date: 2026-10-28
tags: [fonctionnalite, T16, M-001]
---

# T16 : quatre défauts gênants avant la présentation

Source : `recette-mvp-2026-10-28.md` (section « Gênants »), `backlog.md` (C-026), `CAHIER_DES_CHARGES.md`. Rôles : groupeur (D1, D2, D4), administrateur (D2, D3), visiteur (D5). Couches : serveur (D1, D4), web (D1, D2, D3, D5). Pas de mobile dans ce dépôt. C-066 ajouté par le chef de projet le 2026-10-28 (D5) ; décisions : [[2026-10-28-decisions-t16]].

## D1 — C-064 : la tuile « Consigné en séquestre »

**Règle.** Le cahier des charges (§ séquestre) : les fonds restent consignés jusqu'à la clôture, puis sont libérés au groupeur. `Sequestre` porte `montant_consigne`, `montant_libere`, `montant_rembourse` ; ce qui est **détenu** est `consigné − libéré − remboursé` (c'est ce que calcule déjà le tableau de bord admin, `espaces/administration.py:211`). Une tuile intitulée « en séquestre » doit montrer le détenu.

**État constaté.** `espaces/groupeur.py:400-402` : `collecte.montant_consigne` = somme de `montant_total` des parts payées, libérées comprises (2 734 500 au lieu de 2 380 500).

**Correction proposée.** Garder le libellé, changer le calcul : ajouter à `collecte` un champ `montant_detenu` = somme sur `Sequestre.objects.filter(campagne__groupeur=requete.user)` de `consigne − libere − rembourse` (agrégat en base, pas en Python). Conserver `montant_consigne` (somme des parts payées, utile ailleurs) ; la tuile lit `montant_detenu`.
Fichiers : `backend/groupachat/espaces/groupeur.py`, `frontend/commun/src/api/types.ts:303`, `frontend/boutique/src/pages/groupeur/TableauDeBord.tsx:73`, test dans `backend/groupachat/tests/` (ou `espaces`, là où vivent les tests du tableau de bord groupeur).

### Scénarios
| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| D1-R1 | un groupeur avec une campagne dont 354 000 FCFA ont été libérés et d'autres campagnes consignant le reste (jeu de démo, 90001122) | `GET /api/groupeur/tableau-de-bord/` | `collecte.montant_detenu` = Σ(consigné − libéré − remboursé) de ses séquestres (2 380 500 sur la démo) | serveur |
| D1-R2 | une campagne remboursée en totalité | même requête | sa part dans `montant_detenu` est 0 | serveur |
| D1-R3 | un groupeur sans aucune campagne | même requête | `montant_detenu` = 0, pas d'erreur | serveur |
| D1-R4 | deux groupeurs ayant chacun un séquestre | requête du groupeur A | le séquestre de B n'entre pas dans `montant_detenu` | serveur |
| D1-R5 | la démo | tableau de bord à 390 px | la tuile « Consigné en séquestre » affiche `2 380 500 FCFA` ; skeleton pendant le chargement ; pas de défilement horizontal | web |

Tests : `test_le_tableau_de_bord_groupeur_affiche_le_detenu_et_non_le_cumul_des_parts` (D1-R1, avec une libération), `test_le_detenu_ignore_les_fonds_rembourses` (R2), `test_le_detenu_est_nul_sans_campagne` (R3), `test_le_detenu_ne_compte_pas_les_campagnes_d_un_autre_groupeur` (R4).

## D2 — C-071 et C-026 : confirmer les gestes irréversibles

**Règle.** Un geste qui déplace de l'argent ou prévient des tiers demande une confirmation explicite ; fermer la confirmation n'exécute rien.

**État constaté.** Aucun composant de confirmation dans le socle (`ui.tsx` : Bouton, Alerte, Carte… ; `Feuille.tsx` existe : feuille du bas sur mobile, boîte centrée sur grand écran, Échap et clic sur le fond ferment). Trois boutons appellent l'action directement :
- `frontend/admin/src/pages/Decaissements.tsx:87-89` (« Libérer … FCFA » → `executer.lancer`) ;
- `frontend/boutique/src/pages/groupeur/CampagneGroupeur.tsx:206` (« Renoncer et rembourser » → `annuler.lancer("")`) ;
- `CampagneGroupeur.tsx:469-472` (« Prévenir les participants » → `surEnvoi(point)`).

**Correction proposée.** Un seul composant du socle, `frontend/commun/src/composants/Confirmation.tsx`, bâti sur `Feuille` : props `ouverte`, `titre`, `texte`, `libelleAction`, `ton` (danger pour Libérer et Renoncer), `envoi`, `erreur`, `surConfirmation`, `surFermeture`. Il sert aux deux interfaces, donc sa place est dans le socle. Chaque bouton ouvre la confirmation, qui nomme la conséquence :
- Libérer : « Libérer 345 000 FCFA à <groupeur> pour la campagne <titre> ? Le versement ne peut pas être annulé. » ;
- Renoncer : « Rembourser les N participants ? Le montant consigné leur est rendu et la campagne est annulée. » ;
- Prévenir : « Prévenir N participants que leur commande est à retirer à <point> ? Chacun reçoit une notification. »
La confirmation se ferme après succès ; en cas d'erreur serveur elle reste ouverte et affiche le message (`ErreurApi`). Le bouton de confirmation est désactivé pendant l'envoi (pas de double clic). Aucune route serveur ne change.
Fichiers : `commun/src/composants/Confirmation.tsx` (nouveau), `admin/src/pages/Decaissements.tsx`, `boutique/src/pages/groupeur/CampagneGroupeur.tsx`.

### Scénarios (web, 390 px, aucun test pytest : pas de logique serveur)
| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| D2-R1 | console, une demande « À libérer » | on touche « Libérer X FCFA » | une feuille s'ouvre avec le montant, le groupeur et la campagne ; `GET /api/admin/decaissements/` montre la demande toujours en statut `demande` | web |
| D2-R2 | la feuille Libérer ouverte | on touche « Annuler » (ou Échap, ou le fond) | la feuille se ferme, la demande est inchangée en base (même GET) | web |
| D2-R3 | la feuille Libérer ouverte | on confirme | le séquestre libéré augmente de `montant_net`, la ligne passe à « Fonds versés » ; un double toucher rapide ne produit qu'un `POST` | web + serveur |
| D2-R4 | le serveur refuse (campagne annulée entre-temps) | on confirme | la feuille reste ouverte avec le message du serveur, lisible ; rien d'écrit | web |
| D2-R5 | campagne en `minimum_non_atteint` côté groupeur | on touche « Renoncer et rembourser » | feuille de confirmation ; la campagne reste `minimum_non_atteint` tant qu'on ne confirme pas | web |
| D2-R6 | idem | on confirme | campagne annulée, participations remboursées (comme avant) ; annuler la feuille n'écrit rien | web + serveur |
| D2-R7 | campagne à distribuer, point de remise saisi | on touche « Prévenir les participants » | feuille de confirmation ; aucune notification créée (`GET /api/notifications/` d'un participant inchangé) ; après confirmation, une notification par participant | web + serveur |
| D2-R8 | point de remise vide | on touche « Prévenir… » | message du serveur ou champ refusé avant confirmation, rien d'écrit | web |
| D2-R9 | la feuille à 390 px | l'ouvrir | boutons de confirmation et d'annulation tiennent dans l'écran, pas de défilement horizontal ; la feuille garde le thème sombre | web |

Tests : pas de test pytest (aucune règle serveur). Vérification par Playwright à 390 px en recette ; `npm run verifier` doit passer. Si un test de composant existe dans le dépôt web (à confirmer : aucun repéré), en ajouter un pour R2.

## D3 — C-067 : connexion d'un compte hors équipe à la console

**Règle.** Un compte qui n'est pas de l'équipe voit « Ce compte n'appartient pas à l'équipe. » **et** n'a pas de session ouverte nulle part.

**État constaté.** `frontend/admin/src/App.tsx:128-135` : après `POST /comptes/connexion/` (qui ouvre la session serveur), si `!est_equipe` une `Error` ordinaire est levée. `useAction` (`commun/src/outils/requetes.ts:84-90`) ne reconnaît que `ErreurApi` et affiche « Connexion impossible. Vérifiez votre réseau. ». Aucune déconnexion n'est faite : `GET /api/comptes/moi/` répond 200 pour ce compte.

**Correction proposée.** Dans le même `useAction` : si `!est_equipe`, appeler `POST /comptes/deconnexion/` (via `api.post`, pas `deconnecter()` qui n'a pas encore de session React), puis lever `new ErreurApi(403, "Ce compte n'appartient pas à l'équipe.")`, et ne pas appeler `definir`. Si la déconnexion elle-même échoue, le message d'équipe reste prioritaire (attraper cette seconde erreur). Aucun changement serveur ni du socle.
Fichier : `frontend/admin/src/App.tsx` (hors périmètre T15).

### Scénarios
| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| D3-R1 | la console, visiteur déconnecté, compte acheteur 91002233 | il valide la connexion | message exact « Ce compte n'appartient pas à l'équipe. » ; `GET /api/comptes/moi/` avec le même cookie répond 403 (non connecté) | web + serveur |
| D3-R2 | après D3-R1 | on ouvre la boutique (5173) dans le même navigateur | le visiteur n'y est pas connecté (pas de session résiduelle) | web |
| D3-R3 | compte de l'équipe valide | connexion | tableau de bord admin, pas de déconnexion intempestive | web |
| D3-R4 | mauvais mot de passe | connexion | le message du serveur s'affiche (inchangé) | web |
| D3-R5 | serveur coupé | connexion | « Connexion impossible. Vérifiez votre réseau. » (le vrai cas réseau garde ce message) | web |

Tests : pas de pytest (le serveur ne change pas) ; la preuve est la requête `curl` de R1 avec le cookie et le contrôle Playwright à 390 px.

## D4 — C-065 : une seule réponse du groupeur sous un avis

**Règle.** « Le groupeur répond, une fois » (docstring de la vue, texte de l'écran). Une seconde réponse est refusée en 400 lisible, sans rien écrire (`reponse` et `repondu_le` inchangés).

**État constaté.** `commandes/vues.py:159-177` : `repondre` ne teste pas `avis.reponse` ; la seconde écrase la première (200).

**Correction proposée.** Après le contrôle du groupeur et avant la validation : si `avis.reponse` est non vide, lever `ValidationError({"reponse": ["Vous avez déjà répondu à cet avis."]})`. Pour éviter que deux requêtes simultanées passent, faire l'écriture dans `transaction.atomic()` avec `select_for_update()` sur l'avis (ou `Avis.objects.filter(pk=…, reponse="").update(...)` et tester le nombre de lignes). Ordre des contrôles inchangé : 403 pour un tiers avant tout. Aucun changement d'écran (le formulaire est déjà masqué après une réponse ; l'erreur 400 s'afficherait via `ErreurApi` si un second onglet renvoyait).
Fichier : `backend/groupachat/commandes/vues.py`, test dans `backend/groupachat/commandes/tests.py` (classes `TestAvis` / `TestAvisProteges`).

### Scénarios
| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| D4-R1 | un avis sans réponse, le groupeur concerné | `POST /api/avis/<id>/repondre/` `{"reponse": "Merci"}` | 200 ; `reponse` = « Merci », `repondu_le` renseigné | serveur |
| D4-R2 | le même avis déjà répondu | seconde requête `{"reponse": "Autre"}` | 400 `{"reponse": ["Vous avez déjà répondu à cet avis."]}` ; en base `reponse` = « Merci » et `repondu_le` identique | serveur |
| D4-R3 | un avis sans réponse | réponse vide | 400 sur `reponse`, rien écrit (inchangé) | serveur |
| D4-R4 | un avis, un autre groupeur ou un acheteur | `POST …/repondre/` | 403, rien écrit (inchangé) | serveur |
| D4-R5 | visiteur non connecté | `POST …/repondre/` | 403/401, rien écrit (inchangé) | serveur |
| D4-R6 | l'avis répondu à l'écran à 390 px | on ouvre `/groupeur` (les avis et leurs réponses s'y lisent, pas sur la fiche campagne) | la réponse apparaît sous l'avis, le formulaire n'est plus proposé | web |

Tests : `test_une_seconde_reponse_est_refusee_et_la_premiere_reste` (R2, vérifie le texte et `repondu_le` en base), `test_la_premiere_reponse_est_enregistree` (R1, si absent), `test_un_tiers_ne_repond_pas_a_la_place_du_groupeur` (existant, R4 : à conserver). R3 et R5 : vérifier qu'ils existent déjà, sinon les ajouter.

## D5 — C-066 : débordement horizontal sur connexion et inscription (ajouté le 2026-10-28)

**Règle.** Aucune page du parcours visiteur ne déborde à 390 px : `scrollWidth <= 390`.

**État constaté.** Recette T7 (`recette-mvp-2026-10-28.md`, « Gênants ») : `/connexion` et `/inscription` à 390 px donnent une largeur de page de 486 px. Cause : la pastille décorative `absolute -right-24 -top-10 size-72` du gabarit `Cadre` (`frontend/boutique/src/pages/Authentification.tsx`, l. 31-65, pastille l. 33-36) n'est pas contenue : son conteneur n'a pas `overflow-hidden`.

**Correction proposée (minimale).** Contenir la pastille dans son conteneur (`overflow-hidden` sur le parent qui la porte). Rien d'autre dans la mise en page de ce passage. T15, suspendue, touche le même fichier : la correction doit rester petite pour fusionner proprement.
Fichier : `frontend/boutique/src/pages/Authentification.tsx`.

### Scénarios (web, 390 px, aucun test pytest : aucune règle serveur)
| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| D5-R1 | visiteur, 390 px | ouvre `/connexion` | `document.documentElement.scrollWidth <= 390` ; pas de défilement horizontal | web |
| D5-R2 | idem | ouvre `/inscription` | idem | web |
| D5-R3 | 1280 px | ouvre `/connexion` | la pastille reste visible en décor (elle n'est pas supprimée) | web |
| D5-R4 | 390 px, accueil et catalogue | ouvre ces pages | non modifiées : `scrollWidth <= 390` (non-régression) | web |

Tests : Playwright à 390 px en recette ; `npm run verifier` doit passer.

## Chevauchement avec T15 (suspendue)

T16 touche `backend/groupachat/espaces/groupeur.py`, `backend/groupachat/commandes/vues.py`, `backend/groupachat/commandes/tests.py`, `frontend/commun/src/api/types.ts`, `frontend/commun/src/composants/Confirmation.tsx` (nouveau), `frontend/admin/src/App.tsx`, `frontend/admin/src/pages/Decaissements.tsx`, `frontend/boutique/src/pages/groupeur/TableauDeBord.tsx`, `frontend/boutique/src/pages/groupeur/CampagneGroupeur.tsx` et, pour C-066 (D5), `frontend/boutique/src/pages/Authentification.tsx`. T15 (suspendue) touche le même fichier `Authentification.tsx` (étape du code SMS) et `frontend/commun/src/api/types.ts`. Quand T15 reprendra, son passage se rebasera sur T16 : le conflit attendu se limite à la pastille de `Authentification.tsx` et à `types.ts`.

## Questions ouvertes

Tranchées par l'utilisateur le 2026-10-28 : voir [[2026-10-28-decisions-t16]].

1. **D1 : calcul ou libellé ?** Tranché : option A (calcul du détenu). : calculer le détenu et garder « Consigné en séquestre ». Option B : renommer en « Collecté » et ne rien changer au serveur (plus rapide, mais le chiffre diffère toujours du détenu de la console). Le cahier des charges ne fixe pas la tuile ; A est la seule qui rend l'intitulé exact.
2. **D2 / C-026 : motif de renoncement.** Tranché : le champ de motif reste hors de T16 ; la confirmation seule suffit. C-026 reste ouvert pour le motif.

## Prêt à coder ?

Oui : tous les défauts ont des scénarios vérifiables (D1 à D5). Les deux questions sont tranchées (option A ; motif hors T16). Code en cours dans le checkout principal, branche `fix/T16-defauts-genants` depuis `staging` `60b6cbd` ; non commité à la date de la note.

## Recette — 2026-10-28

**RECETTE KO** — arbre de travail non commité sur `60b6cbd` (branche `fix/T16-defauts-genants`). D1, D3, D4 et D5 sont OK ; **D2 est KO dans le build servi par Django** : les classes Tailwind propres à `Confirmation`/`Feuille`/`Bouton danger` ne sont pas compilées dans l'une ou l'autre interface (voir ci-dessous). Matrice : serveur ✅ · web ❌ (D2) · mobile —.

Méthode : copie de l'arbre de travail (rsync, `Confirmation.tsx` et `test_tableau_groupeur.py` présents), builds Vite des deux interfaces, une origine Django (8124 ; `staging` sans correctif sur 8125 pour comparer), base SQLite jetable + `charger_demo`, Chrome headless à 390 px, valeurs relues en base. Captures : `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/2a0ded33-5526-4bfe-abb2-5db865f4b85d/scratchpad/cap/`. Serveurs arrêtés.

| Scénario | Verdict | Preuve |
|---|---|---|
| Tests (56) `test_tableau_groupeur.py` + `commandes/tests.py` | OK | 56 passés ; les 4 tests D1, `test_une_seconde_reponse_est_refusee_et_la_premiere_reste` (texte et `repondu_le` en base) collectés ; `tsc -b boutique admin` OK |
| D1-R1/R5 | OK | démo intacte : `montant_detenu` 2 232 000 = 2 586 000 − 354 000 (base) ; `montant_consigne` 2 586 000 inchangé. Tuile à l'écran = détenu (1 757 000 après libération de 475 000 pendant la recette). Le « 2 380 500 » de la fiche vient de l'état après la recette MVP, pas de la démo neuve. 390 px sans débordement |
| D1-R2/R3/R4 | OK (tests) | pytest |
| D3-R1..R5 | OK | message exact « Ce compte n'appartient pas à l'équipe. » ; `POST /comptes/deconnexion/` 204 ; `GET /comptes/moi/` même cookie : 403 (sur `staging` : 200 et cookie `sessionid` conservé, avec le faux message réseau) ; boutique non connectée ; équipe : tableau de bord ; mauvais mot de passe : message du serveur ; réseau coupé : « Connexion impossible. Vérifiez votre réseau. » |
| D4-R1..R5 | OK | 200 « Merci » ; seconde : 400 `{"reponse":["Vous avez déjà répondu à cet avis."]}`, base inchangée (`staging` : 200, écrase) ; vide 400 ; autre groupeur et acheteur 403 ; visiteur 403 |
| D4-R6 | OK | les avis sont sur `/groupeur` (pas sur la fiche campagne) : réponse affichée, formulaire masqué ; onglet périmé : « Vous avez déjà répondu à cet avis. » affiché, base inchangée |
| D5-R1/R2/R4 | OK | build Django : `scrollWidth` 390 sur `/connexion`, `/inscription`, `/`, `/catalogue` (clair et sombre) ; `staging` : 486 sur connexion et inscription : le défaut existait bien sur le build |
| D5-R3 | OK | pastille visible à 1280 px |
| D2 logique (R1-R4, R6-R8) | OK | rien d'écrit avant confirmation ni après Annuler/Échap/fond ; refus serveur affiché dans la feuille (« Ce décaissement ne peut plus être exécuté : la campagne n'est plus financée. ») ; un seul POST sur double toucher (console et groupeur, 90 ms) ; libération : séquestre libéré 475 000, campagne `approvisionnement` ; renoncement : `50000/0/50000`, deux parts `remboursee` ; prévenir : 4 notifications `marchandise_disponible`, campagne `distribution` ; point vide : bouton désactivé |
| **D2-R1/R9 console** | **KO** | la feuille ne s'affiche pas : le CSS admin n'a pas `.fixed`, `.z-50`, `.items-end`… ; la feuille est rendue en bas de page (top 1520 px à 390, 844 px à 1280), hors écran, et le corps est verrouillé (`overflow:hidden`), donc la page ne défile pas : l'administrateur ne voit pas la confirmation et ne peut pas libérer les fonds. Captures `d2-console-feuille.png`, `d2-console-390-apres-molette.png` |
| **D2-R9 boutique** | **KO** | la feuille s'affiche en bas (390 px, sans débordement) mais le bouton de confirmation danger (« Renoncer et rembourser ») n'a **aucun fond** (`bg-red-600` absent du CSS) : blanc sur blanc, **invisible en thème clair** (`d2-renoncer-clair.png`), texte nu en thème sombre |
| Non-régression | OK | paiement d'une part (campagne 1 : 198 000 → 234 000, part `payee` 36 000, notification) ; décaissement ; renoncement ; mise à disposition |

### Défauts

1. **Bloquant — C-071 inopérante dans la console.** Cause : Tailwind v4 ne scanne que les sources du paquet (`frontend/admin`, `frontend/boutique`) ; les classes qui n'existent que dans `frontend/commun/src` (`Feuille.tsx`, `Confirmation.tsx`, `ui.tsx` ton `danger`) ne sont pas générées. La boutique n'en souffre que partiellement (les classes de `Feuille` y sont déjà utilisées ailleurs). Manquent côté boutique : `bg-red-600`, `hover:bg-red-700`, `flex-col-reverse`, `sm:justify-end`, `bg-black/45`, `backdrop-blur-sm` ; côté console : tout ce qui précède plus `fixed`, `z-50`, `items-end`, `sm:items-center`, `sm:flex-row`. Piste (à décider par `fonctionnalite`) : déclarer la source du socle dans le CSS de chaque interface (`@source` vers `commun/src`), puis reconstruire et rejouer D2-R1, R9.
2. **Cosmétique** — « Prévenir 1 participants » / « Rembourser les 1 participants » : pas d'accord du pluriel (`CampagneGroupeur.tsx` 373 et 392). Confirmé.
3. **Cosmétique** — à 1280 px la lueur de la pastille d'`Authentification` est coupée net au bord du conteneur (`overflow-x-clip`), visible sur `d5-connexion-1280.png`.
4. **Fiche** — D4-R6 : les réponses aux avis se lisent sur `/groupeur`, pas sur la page campagne.

Commit : `60b6cbd` + arbre de travail non commité. Une nouvelle recette sera nécessaire après correction de (1).

## Recette (reprise) — 2026-10-28

**RECETTE OK** — arbre de travail non commité sur `60b6cbd` (branche `fix/T16-defauts-genants`, correction `@source "."` incluse). Matrice : serveur ✅ · web ✅ · mobile —. Le défaut bloquant C-071 est levé ; les défauts restants sont préexistants (identiques sur `staging`) et ne relèvent pas de T16.

Méthode : copie rsync de l'arbre (Confirmation.tsx et test_tableau_groupeur.py présents), builds Vite des deux interfaces, une origine Django (8124) comparée à `staging` sans correctif (8125), bases SQLite jetables + `charger_demo`, Chrome headless 390 px (clair et sombre) et 1280 px, valeurs relues en base. Captures : `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/2a0ded33-5526-4bfe-abb2-5db865f4b85d/scratchpad/cap2/` (feuilles) et `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/2a0ded33-5526-4bfe-abb2-5db865f4b85d/scratchpad/cap2/rev/` (revue, composites `cmp-*` : staging et correctif côte à côte). Serveurs et navigateurs lancés par moi arrêtés.

| Scénario | Verdict | Preuve |
|---|---|---|
| Tests | OK | 56 passés (`test_tableau_groupeur.py` + `commandes/tests.py`) |
| D2-R1/R9 console | **OK (levé)** | feuille `position: fixed`, `y 567..844` dans 390×844, fond assombri `oklab(0 0 0 / .45)`, bouton « Libérer 473 500 FCFA » rouge `oklch(.577 .245 27)` texte blanc, Annuler lisible, `scrollWidth` 390 ; clair et sombre (`console-libere-clair-390.png`, `console-libere-sombre-390.png`) ; corps plus verrouillé hors écran |
| D2-R2 | OK | Annuler, Échap, fond : 0 feuille, `dec1=demande`, séquestre 475000/0/0, 0 POST |
| D2-R3 | OK | confirmer : `dec1=execute`, séquestre 475000/475000/0, campagne `approvisionnement` ; double toucher à 90 ms : un seul POST [200] |
| D2-R4 | OK | campagne passée en `annulee` : la feuille reste ouverte, « Ce décaissement ne peut plus être exécuté : la campagne n'est plus financée. », base inchangée |
| D2-R5/R6 | OK | « Renoncer et rembourser » : bouton rouge plein, blanc, visible clair et sombre (`d2-renoncer-clair.png`) ; annuler/Échap/fond n'écrivent rien (camp 11 `minimum_non_atteint`, 50000/0/0) ; confirmer : `annulee`, 50000/0/25000, part payée `remboursee` ; un POST `annuler` |
| D2-R7/R8/R9 | OK | « Prévenir 4 participants … à Boutique Abalo, Bè-Kpota ? » ; avant confirmation 16 notifications, après 20 (4 `marchandise_disponible`), campagne `distribution` ; point vide ou espaces : bouton désactivé ; feuille dans l'écran (y 567..844), bouton primaire lisible |
| Accord du pluriel | OK | 1 payeur : « Rembourser les 1 participant ? » ; 4 : « Prévenir 4 participants » ; 2 : « les 2 participants » |
| D1 | OK | tuile groupeur « Consigné en séquestre » = 1 732 000 (détenu) contre 2 586 000 (consigné) sur `staging`, après libérations de la recette ; tests D1 passés |
| D3 | OK | groupeur sur la console : « Ce compte n'appartient pas à l'équipe. », `GET /comptes/moi/` 403 ensuite |
| D4 | OK | 1re réponse 200 (texte en base), 2e 400 « Vous avez déjà répondu à cet avis. », vide 400 « Ce champ ne peut être vide. » |
| D5 | OK | `scrollWidth` 390 sur `/connexion`, `/inscription`, `/` (sombre) et partout dans la revue |

### Revue visuelle (staging contre correctif, 390 px clair/sombre et 1280 px clair)
Aucun débordement horizontal (`scrollWidth` = largeur sur les 5 écrans de la console, l'accueil, la fiche, la feuille de participation, mes achats, l'espace groupeur). Connexion, tableau de bord, dossiers KYC, décaissements, modération : **mieux que `staging`** (cartes arrondies, boutons dimensionnés, pastilles, alertes teintées, bouton Examiner/Entrer corrects) ; rien de cassé ni de renversé. Boutique : pages identiques, seule différence le bouton « Répondre » de l'avis, désactivé (clair) tant que le champ est vide, conséquence de D4.

### Défauts nouveaux
Aucun bloquant, aucun gênant introduit par la correction.

Constatés, **préexistants** (même rendu sur `staging`), hors T16 — à ranger au backlog :
1. **Gênant** — console, thème clair : la carte « Détenu en séquestre » du tableau de bord est blanche (texte `text-white` sur `.surface` blanche ; le dégradé `degrade-accent -z-10` passe derrière). Idem la tuile « Consigné en séquestre » de l'espace groupeur en clair. `frontend/admin/src/pages/TableauAdmin.tsx:80-84`. Correct en thème sombre.
2. **Gênant** — thème sombre : la bulle « Réponse du groupeur » (fiche campagne et espace groupeur) est un rectangle blanc sans texte lisible.
3. **Cosmétique** — console à 390 px, `/decaissements` : titre de campagne cassé mot par mot, montant serré à droite (la ligne ne s'empile pas).
4. **Cosmétique** — « Rembourser les 1 participant » : « les » devant un singulier (la forme « le participant » serait juste).
5. **Cosmétique** — deux clics synchrones sur « Libérer » dans le même tick produisent deux POST (le second est refusé par le serveur, rien d'écrit en double) ; un double toucher réel (90 ms) n'en produit qu'un.
6. Rappel : lueur de la pastille coupée à 1280 px (acceptée).

Pas pu tester : application mobile native (absente du dépôt). Flakiness de mon outillage : trois connexions Playwright ont rendu la page de connexion faute d'attente suffisante ; rejouées avec 4 s, OK.

Commit : `60b6cbd` + arbre de travail non commité.

## Clôture — 2026-10-28

Statut `terminée`. Preuves :

- **Commit** `f78f52b` (« Confirme les gestes d'argent et corrige cinq défauts avant la démo »), fusionné dans `staging` par avance rapide (`60b6cbd..f78f52b`) sur accord de l'utilisateur. Non poussé : `origin/staging` reste à `60b6cbd`.
- **Vérifier** : première passe, `check.sh complet` : 446 passed, 9 skipped, CHECK: OK (complet). Reprise après la correction `@source "."` : 446 passed, 9 skipped in 2203.52s, CHECK: OK (complet). Ces passes sont sur la branche `fix/T16-defauts-genants`, avant fusion. « Vérifier » sur `staging` après fusion : en cours, preuve à compléter par le chef de projet.
- **Relecture** `reviewer-tester` : première passe VALIDÉE (`check.sh rapide` 298 passed ; `test-diff.sh` SIGNAUX 0). Reprise ciblée VALIDÉE : CSS compilés comparés à `staging`, aucune classe retirée ; boutique +45 sélecteurs, console environ +100, tous issus du socle.
- **Recette** : première passe RECETTE KO (défaut bloquant C-071 : classes du socle absentes du CSS compilé). Reprise RECETTE OK le 2026-10-28 (serveur ✅, web ✅, mobile —), section « Recette (reprise) — 2026-10-28 ».
- **Hors T16, restent ouverts** : motif de renoncement (C-026) ; défauts préexistants relevés par la reprise : contrastes (C-077, C-078, [[T17-contrastes]]), cosmétiques (C-079 à C-082, backlog).
