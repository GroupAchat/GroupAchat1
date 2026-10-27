---
type: fonctionnalite
id: F-011
statut: terminée
date: 2026-10-27
tags: [fonctionnalite, F-011, kyc, groupeur, mvp]
---

# F-011 — Devenir groupeur : dépôt du dossier KYC avec pièces obligatoires

Statut : **terminée** (2026-10-27) : reviewer-tester VALIDÉE à la seconde relecture (la première relecture était À CORRIGER, points réglés) ; recette **RECETTE OK** (serveur ✅, web ✅, mobile —). Commitée `abaa622` (« Exige les pièces d'identité recto et verso pour le dossier KYC »), fusionnée dans `staging` en avance rapide (`769ec1a..abaa622`) et poussée sur `origin/staging`. « Vérifier » complet sur `staging` après fusion : `CHECK: OK (complet)`, migrations « No changes detected », 308 tests passés en 1243,23 s. Tâche T4 de [[M-001-terminer-le-mvp]] ; décisions [[2026-10-27-decisions-f011]] ; suivis C-042 à C-050 dans [[backlog]].

Rôle : **Acheteur** qui demande à devenir groupeur (T4 de [[M-001-terminer-le-mvp]]). Décision Q5 ([[2026-10-26-decisions-carte]]) : pièces obligatoires, champ recto / verso dans `Profil.tsx`, obligation côté serveur. Source : `CAHIER_DES_CHARGES.md` §5 (« Un acheteur peut demander à devenir groupeur… il dépose son dossier KYC et attend la validation »). Liés : F-030 (pièces privées, recettée), F-023 (l'administrateur consulte), F-012 (écran d'attente), C-020, C-038.

## État constaté du code (2026-10-27, `769ec1a`)
| Élément | Constat |
|---|---|
| Modèle `DossierKYC` (`comptes/models.py` l. 228) | `piece_recto` / `piece_verso` = `ImageField(upload_to="kyc/", blank=True)` : **facultatives**, stockage `FileSystemStorage` (défaut, `settings.py` l. 136), jamais Cloudinary. Commentaire l. 249 : facultatives « pour la démo ». |
| Sérialiseur (`serialiseurs.py` l. 139) | `piece_recto` / `piece_verso` = `ImageField(write_only=True, required=False)` ; taille max `TAILLE_MAX_PIECE_OCTETS` (8 Mo, message « Image trop lourde : 8 Mo au maximum. ») ; lecture par `lien_recto` / `lien_verso` = `/pieces/<id>/<cote>/`. |
| `DossierKYCVue` (`comptes/vues.py` l. 233) | `NumeroVerifie` ; 404 si pas de dossier (GET) ; 409 « Un dossier est déjà en cours d'examen. » si dossier existant **non rejeté** (donc aussi s'il est validé) ; dépôt après rejet = réécriture, motif effacé ; le rôle passe à `groupeur` dès le dépôt ; `@transaction.atomic`. Parseurs DRF par défaut : JSON **et** multipart acceptés. Aucune limitation de débit sur cette route. |
| Pillow | **déjà là** (`requirements.txt`, `Pillow==12.0.0`) : `ImageField` vérifie que le fichier est décodable. Aucun filtre de format : tout ce que Pillow ouvre passe (JPEG, PNG, GIF, WebP, BMP, TIFF…). PDF et HEIC refusés. |
| Service des pièces (`config/service/fichiers.py`) | `/medias/` refuse `kyc/` (route + vue) ; `/pieces/<id>/recto\|verso/` : 404 pour anonyme, tiers et dossier inconnu ; accès `est_equipe` ou propriétaire ; `Cache-Control: private, no-store`. |
| Tests existants (`comptes/tests.py` l. 168-210) | Tous en `format="json"` **sans pièce** : ils décrivent le contrat actuel (pièces facultatives) et casseront légitimement. Aucun test de dépôt multipart. |
| `Profil.tsx` `DevenirGroupeur` (l. 277) | Aucun champ fichier ; `api.post("/comptes/dossier/", saisie)` en JSON ; encart « Les pièces justificatives ne sont pas téléversées dans cette version » (l. 405). Alerte et `pourChamp` déjà branchés sur `numero_piece` / `numero_mobile_money`, pas sur les pièces. |
| Client `commun/api/client.ts` | Sait déjà envoyer un `FormData` (pas de `Content-Type` forcé) et pose `X-CSRFToken` sur toute écriture. Rien à changer. `outils/televersement.ts` = Cloudinary uniquement : **ne pas le réutiliser** pour les pièces. |
| `frontend/admin/src/pages/Dossiers.tsx` | Affiche `lien_recto` (l. 199) ; type `DossierKYC` (`types.ts` l. 251) déjà sans `piece_recto` en lecture. |
| Jeu de démonstration (`catalogue/.../charger_demo.py` l. 207) | Dossiers créés **sans pièce** (dont un validé). `VERSION_DEMO = "5"`. |

## Recette
Rôle : acheteur candidat (principal), administrateur (lecture), tiers, anonyme · Couches : serveur oui · web oui (boutique 390 px ; console admin en lecture) · mobile non (pas d'app dans ce dépôt) · Source : CDC §5 ; Q5.

### Scénarios
Hypothèses de limites (à confirmer, Q2, Q3) : JPEG / PNG / WebP, 8 Mo par pièce. Messages à confirmer (Q4).

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | un acheteur au numéro vérifié, sans dossier | il envoie en multipart type, numéro de pièce, recto JPEG, verso JPEG, Mobile Money `90 00 11 22`, nom de commerce | 201 ; `statut=en_attente` ; `numero_mobile_money="90001122"` ; 1 `DossierKYC` ; deux fichiers existent sous `MEDIA_ROOT/kyc/` ; réponse sans clé `piece_recto` / `piece_verso`, avec `lien_recto` = `/pieces/<id>/recto/` ; rôle de l'utilisateur = `groupeur`, `est_groupeur_valide` faux | serveur |
| R2 | R1 faite | le candidat ouvre `lien_recto` et `lien_verso` | 200, `Content-Type` image, octets identiques au fichier envoyé, `Cache-Control: private, no-store` | serveur |
| R3 | R1 faite | un administrateur ouvre `/pieces/<id>/recto/` ; il liste `GET /api/admin/dossiers/` | 200 sur la pièce ; la liste contient `lien_recto` et `lien_verso` non nuls et aucune clé `piece_recto` | serveur + web admin |
| R4 | R1 faite | un autre acheteur, puis un anonyme, ouvrent `/pieces/<id>/recto/` | 404 pour les deux, aucun octet de la pièce | serveur |
| R5 | R1 faite | n'importe qui demande `/medias/kyc/<nom du fichier>` (et variantes `%2e%2e`, casse `KYC`) | 404 ; le nom du fichier stocké n'apparaît dans aucune réponse d'API | serveur |
| R6 | un acheteur vérifié | il envoie sans `piece_recto` | 400 `{"piece_recto": ["…"]}` message lisible en français ; 0 dossier, aucun fichier écrit, rôle toujours `acheteur` | serveur |
| R7 | idem | il envoie sans `piece_verso` | 400 sur `piece_verso` ; rien d'écrit | serveur |
| R8 | idem | il envoie les deux pièces en JSON (pas de fichier) ou avec des champs `piece_*` vides | 400 sur les pièces ; rien d'écrit | serveur |
| R9 | idem | il envoie un `.pdf` (ou un `.txt` renommé `.jpg`) comme recto | 400 sur `piece_recto` (« envoyez une photo… ») ; rien d'écrit, aucun fichier orphelin dans `kyc/` | serveur |
| R10 | idem | il envoie un recto de `TAILLE_MAX_PIECE_OCTETS + 1` octets | 400 « Image trop lourde : 8 Mo au maximum. » sur `piece_recto` ; rien d'écrit. Pile à la limite : accepté | serveur |
| R11 | idem | numéro de pièce vide / Mobile Money à 7 chiffres / type de pièce inconnu, pièces valides | 400 sur le bon champ (« Numéro invalide : huit chiffres attendus. ») ; **les pièces ne sont pas conservées** | serveur |
| R12 | un dossier `en_attente` | le candidat redépose avec deux pièces valides | 409 « Un dossier est déjà en cours d'examen. » ; dossier et fichiers inchangés | serveur |
| R13 | un dossier `valide` | le groupeur redépose | 409 ; dossier inchangé (décision Q6 : message à distinguer ?) | serveur |
| R14 | un dossier `rejete` avec motif | le candidat redépose deux **nouvelles** pièces | 201 ; même `id` (réécriture, 1 seul dossier) ; `statut=en_attente`, `motif_rejet=""`, `decide_par` vide ; `lien_recto` sert la **nouvelle** image ; l'ancienne n'est plus servie (sort de l'ancien fichier : Q7) | serveur |
| R15 | un dossier `rejete` | il redépose **sans** pièces (réutiliser les anciennes) | 400 sur les pièces (Q8 : recommandé) ; dossier resté `rejete` | serveur |
| R16 | un anonyme | il poste le dossier | 403 (ou 401) ; rien d'écrit | serveur |
| R17 | un acheteur connecté, numéro **non** vérifié | il poste le dossier | 403 ; rien d'écrit | serveur |
| R18 | un client de session sans jeton CSRF (`enforce_csrf_checks=True`) | il poste le dossier multipart | 403 CSRF ; rien d'écrit | serveur |
| R19 | tout dépôt R1 | on inspecte le code exécuté | aucun appel à Cloudinary / à `hebergement.py` ; `kyc/` est dans le stockage local ; `POST /api/groupeur/medias/signature/` n'est pas appelé par l'écran (réseau du navigateur) | serveur + web |
| R20 | l'administrateur valide le dossier R1 | `POST /api/admin/dossiers/<id>/decision/` | `statut=valide`, notification `kyc_decide` ; les pièces restent lisibles par le groupeur et l'administrateur | serveur |
| R21 | boutique à 390 px, acheteur connecté | il ouvre `/profil/devenir-groupeur` | deux zones « Recto » et « Verso » avec libellé, mention des formats et de la taille ; sur Android, le sélecteur propose appareil photo et galerie (`accept="image/*"` ; `capture` : voir Q9) | web |
| R22 | idem | il choisit une image | aperçu (miniature) et nom du fichier ; possibilité de remplacer ; fichier non image ou trop lourd refusé **avant envoi** avec message lisible | web |
| R23 | idem | il soumet sans une pièce / avec erreur serveur (R6-R11) | message sous le champ concerné (`pourChamp("piece_recto")`), saisies et fichiers conservés, bouton redevenu actif | web |
| R24 | idem | il soumet un dossier complet | bouton en chargement pendant l'envoi (pas de double clic), puis redirection `/profil`, statut « en attente » visible ; l'encart « pièces non téléversées » a disparu | web |
| R25 | candidat dont le dossier est `rejete` | il ouvre l'écran | motif affiché, champs préremplis, pièces **à renvoyer** ; aperçu des anciennes pièces via `lien_recto` (Q8) | web |
| R26 | candidat avec dossier `en_attente` / `valide` | il ouvre `/profil/devenir-groupeur` | l'écran ne propose pas un dépôt qui renverrait 409 (renvoi vers le statut) | web |
| R27 | console admin | l'administrateur ouvre un dossier déposé par R24 | recto et verso s'affichent (images, pas de lien cassé) ; dossier ancien sans pièce : message « aucune pièce » lisible, pas d'image cassée | web admin |

### Tests automatiques attendus
Fichier : `backend/groupachat/comptes/tests.py`, classe `TestDossierKYC` (mise à jour + ajouts), `format="multipart"` avec images générées par Pillow en mémoire (`SimpleUploadedFile`), `MEDIA_ROOT` redirigé vers `tmp_path` (fixture `settings`). Les tests actuels en JSON sans pièce sont **à réécrire avec des pièces**, pas à affaiblir ni supprimer (testing.md) : la règle a changé (Q5).
- R1 : `test_un_depot_complet_cree_un_dossier_en_attente_avec_ses_pieces` (statut, fichiers sous `kyc/`, absence de `piece_recto` dans la réponse, rôle).
- R2/R4/R5 : `test_le_candidat_relit_ses_pieces_par_le_lien_protege`, `test_un_tiers_et_un_anonyme_ne_lisent_pas_les_pieces`, `test_le_dossier_kyc_n_est_pas_servi_par_medias` (complètent `groupachat/tests/` de F-030 si déjà présents : vérifier la collecte).
- R3 : `groupachat/espaces/tests.py` (ou fichier existant des dossiers admin) : `test_l_administrateur_lit_les_pieces_deposees`.
- R6-R8 : `test_un_depot_sans_recto_est_refuse`, `test_un_depot_sans_verso_est_refuse`, `test_un_depot_json_sans_fichier_est_refuse` ; chacun vérifie `DossierKYC.objects.count()==0`, rôle inchangé, `kyc/` vide.
- R9 : `test_un_fichier_qui_n_est_pas_une_image_est_refuse` (PDF et texte renommé en `.jpg`).
- R10 : `test_une_piece_trop_lourde_est_refusee_pile_a_la_limite_acceptee` (réduire `TAILLE_MAX_PIECE_OCTETS` par `settings`).
- R11 : `test_une_erreur_de_champ_ne_conserve_pas_les_pieces`.
- R12/R13 : `test_second_depot_refuse_pendant_l_examen` (existant, version multipart), `test_un_groupeur_valide_ne_redepose_pas`.
- R14/R15 : `test_redepot_apres_rejet_remplace_les_pieces_et_efface_le_motif`, `test_redepot_apres_rejet_sans_nouvelles_pieces_est_refuse`.
- R16-R18 : `test_un_anonyme_ne_depose_pas`, `test_un_numero_non_verifie_ne_peut_pas_deposer` (existant), `test_le_depot_sans_jeton_csrf_est_refuse` (`APIClient(enforce_csrf_checks=True)`).
- R19 : `test_le_depot_n_appelle_pas_cloudinary` (patch de `hebergement`, `assert_not_called`).
- R20 : couvert par les tests F-023 existants ; ajouter la lecture après validation.
- Tous les noms doivent être **collectés** : `python -m pytest --collect-only -q groupachat/comptes/tests.py`.
- Front : pas de suite de tests dans le dépôt (vérifier `package.json`) ; contrôle par `npm run verifier` (typage) et la recette à 390 px.

### Vérification d'interface
- Écran : `/profil/devenir-groupeur` (`Profil.tsx`, composant `DevenirGroupeur`) ; consultation côté `frontend/admin/src/pages/Dossiers.tsx`.
- Le client envoie un `FormData` par `api.post` (déjà géré) ; les champs lus (`lien_recto`, `lien_verso`, `statut`, `motif_rejet`) doivent exister dans le JSON réel de `GET /api/comptes/dossier/`.
- États : **chargement** (envoi d'images lent, bouton désactivé, idéalement un libellé « Envoi en cours… »), **erreur** (message sous la pièce fautive, pas seulement l'alerte générale), **vide** (aucun fichier choisi : zones d'appel claires), dossier existant, dossier rejeté.
- Capture à 390 px : `npx playwright screenshot` si présent, sinon observation manuelle.

## Questions ouvertes
Cela change le contrat d'API (pièces obligatoires, multipart) : décision de l'utilisateur avant le code.

1. **Où imposer l'obligation, et que deviennent les dossiers existants ?** Recommandation : **dans le sérialiseur seulement** (`required=True` à la création), **sans migration** : le modèle garde `blank=True`, donc aucun dossier existant (démonstration : le groupeur validé « Abalo Import » et les dossiers en attente n'ont pas de pièce) n'est touché ni invalidé, et `charger_demo` continue de fonctionner. Supprimer la phrase « Facultatives… » du modèle (l. 249) au profit d'un commentaire qui explique ce choix. Un `blank=False` au modèle forcerait un arbitrage sur les dossiers sans pièce (les rejeter ? les purger ?) : à éviter. Les dossiers sans pièce restent consultables ; pour la production, l'utilisateur sait-il s'il existe de vrais dossiers déjà validés sans pièce (demander un complément ?). `VERSION_DEMO` à incrémenter seulement si le jeu de démo change (Q10).
2. **Formats acceptés.** Recommandation : **JPEG, PNG, WebP** (photo de téléphone et capture). PDF **refusé** pour le MVP (Pillow ne l'ouvre pas ; l'ajouter obligerait à valider le contenu autrement). Un filtre explicite sur le format détecté par Pillow (et non sur l'extension ni le `Content-Type` envoyé par le client) évite d'accepter GIF / TIFF / BMP. HEIC (iPhone) : Android ne le produit pas par défaut ; non pris en charge (message qui l'explique).
3. **Taille maximale.** Le code a déjà 8 Mo par pièce (`TAILLE_MAX_PIECE_OCTETS`). Recommandation : **garder 8 Mo côté serveur**, ajouter un contrôle de 8 Mo côté navigateur avant envoi, et accepter que recto + verso fassent 16 Mo sur une connexion mesurée. Alternative à décider : compression côté navigateur avant envoi (plus de travail, hors périmètre ici). Fixer aussi un minimum raisonnable ? Recommandation : non.
4. **Nouveaux messages d'erreur** (français, par champ) : « Joignez la photo du recto de votre pièce. » / « …du verso… » ; « Ce fichier n'est pas une photo lisible (JPEG, PNG ou WebP). » ; reprise du message de taille existant. Validés tels quels ou à reformuler ?
5. **Le contrat d'API change** : `POST /api/comptes/dossier/` exige `multipart/form-data` avec `piece_recto` et `piece_verso` ; le JSON sans pièce est refusé en 400. Recommandation : **accepter**, il n'existe qu'un client (la boutique) et la sortie `GET` ne change pas. Prévenir l'utilisateur que la collection Postman sera à mettre à jour.
6. **Dossier `valide` ou `rejete` qui redépose.** Aujourd'hui : `valide` → 409 avec un message qui parle d'« examen » (trompeur). Recommandation : message distinct pour `valide` (« Votre dossier est déjà validé. »), `rejete` autorisé (comportement actuel), à garder.
7. **Anciennes pièces au redépôt après rejet.** Recommandation : **supprimer les fichiers remplacés** du disque (le groupeur a envoyé une pièce d'identité : ne pas en laisser traîner), après le succès de l'écriture. Sinon les anciens fichiers restent sous `kyc/` sans référence.
8. **Redépôt après rejet : pièces à renvoyer ?** Recommandation : **oui, toujours les deux**, car un rejet porte le plus souvent sur une pièce illisible, et cela garde une règle unique « le dossier déposé a toujours deux pièces ».
9. **Appareil photo Android.** Recommandation : `<input type="file" accept="image/*">` **sans** `capture` : le téléphone propose caméra **et** galerie ; `capture="environment"` forcerait la caméra et empêcherait de prendre une photo déjà faite.
10. **Démonstration.** Faut-il que `charger_demo` crée de vraies pièces fictives (petites images générées) pour le dossier en attente et le validé, afin que F-023 montre quelque chose ? Recommandation : **oui pour un dossier en attente** (image générée, sans donnée réelle), ce qui impose d'incrémenter `VERSION_DEMO` ; **hors du périmètre de F-011 si l'utilisateur préfère** (il suffit alors de recetter avec des dépôts réels).
11. **Nom du fichier stocké.** Aujourd'hui Django garde le nom d'origine du téléphone dans `kyc/` (parfois des noms de personne). Recommandation : un `upload_to` calculé (identifiant aléatoire + extension). Cela génère une migration `AlterField` **sans effet sur les données** ; les fichiers existants ne bougent pas. À accepter ?
12. **Limitation de débit.** La route n'en a pas : un compte vérifié peut déposer en boucle (après rejet) et remplir le disque. Recommandation : une limite par utilisateur (par ex. 5 dépôts par jour, taux dans `DEFAULT_THROTTLE_RATES` et `.env.exemple`). À décider : valeur, ou différer.
13. **C-020 et C-038** (liens `kyc_decide` / `EstAdministrateur`). Hors F-011 ; recommandation : traiter C-038 avec F-011 (le refus pointe vers `/profil/devenir-groupeur` pour renvoyer les pièces), C-020 avec F-023.
14. **Rôle basculé dès le dépôt** (existant, règle du dépôt, testé) : le conserver ? Un dépôt invalide ne bascule rien (R6-R11) ; je ne le remets pas en cause.

## Prêt à coder ?
Non, tant que les questions 1 à 5 n'ont pas de réponse (contrat d'API et limites). Les questions 6 à 14 ont chacune une recommandation par défaut.

## Réalisation (2026-10-27) — décisions de l'utilisateur appliquées
Obligation dans le sérialiseur seul (`PieceKycField`, `comptes/pieces_kyc.py`), modèle en `blank=True` ; format lu par Pillow (JPEG, PNG, WebP ; MPO traité comme JPEG), 8 Mo ; multipart ; 409 « Votre dossier est déjà validé. » ; anciennes pièces effacées en `on_commit` après redépôt ; `upload_to` aléatoire (migration `0004_noms_aleatoires_des_pieces_kyc`) ; limite `depot_kyc` 5/jour par compte (POST seul, `LIMITE_DEPOT_KYC`) ; démo : pièces fictives pour Afi Doe, `VERSION_DEMO` = "6" ; C-038 : refus -> `/profil/devenir-groupeur` ; écran `ChampPiece` (sans `capture`).
Non vérifié : rendu à 390 px (pas de Playwright installé dans le dépôt).

## Recette — 2026-10-27 (base 769ec1a + arbre de travail, commité en `abaa622`)
**RECETTE OK** · serveur ✅ · web ✅ · mobile — (pas d'app dans ce dépôt ; appareil photo Android : à vérifier par l'utilisateur sur un vrai téléphone).
Environnement local jetable : sqlite et `MEDIA_ROOT` dans le scratchpad, `runserver` :8211, Vite boutique :5211 et admin :5212, `charger_demo` (VERSION_DEMO 6), Chrome headless 390 px. Aucune base ni `backend/medias/` réels touchés.

### Tests
`python -m pytest groupachat/comptes/tests.py` : 68 passés, tests F-011 collectés (dépôt complet, pièces relues, tiers/anonyme, Cloudinary, sans recto/verso, JSON, vides, 8 Mo pile / +1, CSRF, validé, redépôt, limites 5/jour, échec après écriture, démo). `npm run verifier` : propre. Suite complète non rejouée (verte à la relecture : 308).

### Serveur (curl, sessions réelles)
| # | Action | Observé |
|---|---|---|
| R1 | multipart complet, acheteur vérifié | 201, `en_attente`, Mobile Money `90001122`, 2 fichiers `kyc/<uuid>.jpg`, pas de `piece_*` dans la réponse, `lien_recto=/pieces/12/recto/`, rôle `groupeur`, `est_groupeur_valide=false` |
| R2 | candidat relit recto/verso | 200, `image/jpeg`, octets identiques (`cmp`), `Cache-Control: private, no-store` |
| R3 | admin relit ; liste `/api/admin/dossiers/` | 200 identique ; `lien_recto`/`lien_verso` renseignés (null sans pièce), aucune clé `piece_*` |
| R4 | tiers, anonyme, autre groupeur | 404 (recto et verso) |
| R5 | `/medias/kyc/<nom>`, `KYC`, `%2e%2e`, `%2f`, `x/../`, `--path-as-is`, nom de la démo | 404 partout ; nom stocké absent des réponses API |
| R6-R8 | sans recto / sans verso / sans rien / JSON / champs vides | 400 par champ, messages exacts de la décision 4 ; rien écrit |
| R9 | PDF, texte `.jpg`, GIF `.jpg`, BMP, bombe 144 Mpx, 25 Mpx+1 ligne | 400 « Ce fichier n'est pas une photo lisible… » ; aucun fichier orphelin |
| R10 | 8 Mo+1 ; 8 Mo pile ; 25 Mpx pile | 400 « Image trop lourde : 8 Mo au maximum. » ; pile et 25 Mpx : 201. PNG nommé `.pdf` accepté, stocké `.png` |
| R11 | numéro vide / Mobile Money 7 chiffres / type inconnu | 400 sur le bon champ ; disque inchangé ; rôle resté `acheteur` |
| R12-R13 | redépôt en attente ; validé (et Abalo de la démo) | 409 « Un dossier est déjà en cours d'examen. » ; 409 « Votre dossier est déjà validé. » ; rien changé |
| R14 | rejeté redépose 2 nouvelles pièces | 201, même id, `en_attente`, motif vidé, `decide_par` vide ; nouvelles pièces servies ; anciens fichiers effacés du disque |
| R15 | rejeté sans pièces ; avec numéro invalide | 400 ; dossier resté `rejete`, anciennes pièces conservées |
| R16-R18 | anonyme ; numéro non vérifié ; sans CSRF | 403 ; 403 ; 403 CSRF ; rien écrit |
| R19 | code et réseau | aucun appel Cloudinary / signature |
| R20 | admin valide | `valide`, notification `kyc_decide`, pièces toujours lisibles, `est_groupeur_valide=true` |
| Limites | 6 dépôts réussis ; 31 tentatives en 400 | 6e : 429 « Trop de dépôts aujourd'hui… » + `Retry-After`, rien écrit ; 31e : 429 « Trop de tentatives aujourd'hui… » ; GET libre |
| Démo | `charger_demo` | dossier d'Afi Doe : 2 PNG sous `kyc/`, affichés par la console admin |

### Web 390 px
| # | Action | Observé |
|---|---|---|
| R21 | `/profil/devenir-groupeur` | zones recto / verso avec formats et taille ; `accept="image/jpeg,image/png,image/webp"`, **aucun `capture`** ; ancien encart disparu |
| R22 | choix, remplacement, PDF, 8 Mo+1 | aperçu + nom ; remplacement OK ; PDF et fichier lourd refusés avant envoi, 0 requête d'écriture |
| R23 | sans pièces ; recto texte `.jpg` | message sous chaque zone (400 réel) ; saisies et fichiers conservés ; bouton actif |
| R24 | dépôt complet, double clic, POST retardé | « Envoi en cours… » désactivé ; un seul POST (201) ; redirection `/profil`, « en cours de vérification » |
| R25 | dossier rejeté | motif, champs préremplis, zones photo vides ; redépôt → 201 |
| R26 | en attente / validé | message et « Retour au profil », aucun formulaire |
| R27 | console admin | recto et verso chargés ; dossier sans pièce : « Aucune pièce jointe… » |
| C-038 | refus puis clic sur la notification | arrivée sur `/profil/devenir-groupeur`, motif visible, formulaire présent |
Aucun défilement horizontal (390/390 partout).

### Observations sans gravité
- Si le `GET /comptes/dossier/` échoue, l'écran montre le formulaire vide (un 409 s'afficherait dans l'alerte).
- Un fichier refusé avant envoi vide aussi la zone.
- Compteurs de limite dans le cache local par processus (documenté dans le code).
- Non joué : appareil photo / galerie sur Android réel, HEIC iPhone.
