# F-030 — Les pièces KYC ne sont jamais servies publiquement

Statut : terminée (2026-10-27) : recette RECETTE OK, reviewer-tester VALIDÉE. Critique ; T9 de [[M-001-terminer-le-mvp]], décision D-F030 ; branche `fix/F-030-fuite-kyc`. Correctif commité `fb4963c` (« Ferme la traversée qui exposait les pièces d'identité ») sur `fix/F-030-fuite-kyc`, fusionné dans `staging` et poussé sur `origin/staging` (2026-10-27). Fichiers : `backend/config/service/fichiers.py`, `backend/config/urls.py`, `backend/groupachat/tests/test_securite.py`. Il était non commité au moment de la recette.

## Correctif (2026-10-27) et réponses aux questions ouvertes
- Ce qu'a fait le correctif : `media_publique` (`backend/config/service/fichiers.py`) refuse sur le chemin **résolu** (`Path.resolve()`, liens suivis), vérifie `relative_to(MEDIA_ROOT)`, compare le premier dossier en `casefold` à `kyc`, et répond 404. `backend/config/urls.py` ne sert plus `/medias/` par `static(MEDIA_URL…)` en DEBUG (seconde fuite : ce doublon contournait la vue).
- Tests : 60 tests `TestPiecesKycPrivees` dans `backend/groupachat/tests/test_securite.py` (DEBUG=0 et 1) ; sans le correctif, 24 échouent. `check.sh complet` : 225 tests verts.
- Q1 (casse) : choix `casefold` sur le dossier `kyc`. Joué sous Linux seulement ; à confirmer si un déploiement sur système insensible à la casse est envisagé. Question laissée ouverte pour l'utilisateur.
- Q2 (lien symbolique, R12) : choix du refus sur le **chemin résolu**, testé (lien `catalogue/lien -> kyc` : 404). Question laissée ouverte pour l'utilisateur, à confirmer.
- Q3 (code de refus) : choix 404 partout. Question laissée ouverte pour l'utilisateur, à confirmer.
- Q4 (pièces déjà exposées en production) : reste une décision de l'utilisateur, hors code (voir [[backlog]] C-025). Question ouverte.
Source : `CLAUDE.md` (« Les pièces d'identité ne sont jamais servies publiquement »), `CAHIER_DES_CHARGES.md` (KYC), [[2026-10-26-recette-failles]].
Fichiers en cause : `backend/config/urls.py:21` (`^medias/(?!kyc/)`) et `:30` (`static(MEDIA_URL…)` en DEBUG), `backend/config/service/fichiers.py` (`media_publique` ne teste que `Path(chemin).parts[0]`, puis `serve()` normalise `..`).

## Résultat observable
Aucun fichier de `MEDIA_ROOT/kyc/` n'est lisible par `/medias/…`, quelle que soit la forme du chemin et quelle que soit la valeur de `DJANGO_DEBUG`. Seuls `/pieces/<id>/recto|verso/` les servent, au propriétaire du dossier et à l'équipe (`est_equipe`).

## Recette
Rôle : anonyme, acheteur tiers, propriétaire (groupeur), administrateur · Couches : serveur oui · web non · mobile non · Source : `CLAUDE.md`.

Préparation commune : un dossier KYC fictif dont `piece_recto` = `kyc/secret_recto.png` (contenu reconnaissable, ex. octets `PIECE-SECRETE`) et `piece_verso` = `kyc/secret_verso.png`, créés sous `MEDIA_ROOT` ; un média public fictif `catalogue/produit.png` ; trois comptes : propriétaire P, tiers T, administrateur A. Chaque scénario d'attaque se joue **deux fois** : DEBUG=0 et DEBUG=1 (en test : `settings.DEBUG` + rechargement des urlconf, ou serveur lancé avec `DJANGO_DEBUG=0/1`). Pour tout « refus » : statut 404 (ou 400/403), **le corps ne contient pas** `PIECE-SECRETE`, et aucune redirection vers le fichier. Les clients HTTP de test normalisent parfois les URL : les scénarios d'encodage se rejouent aussi par `curl --path-as-is` sur serveur réel.

### Scénarios
| # | Étant donné | Quand (requête) | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | anonyme, DEBUG=0 puis 1 | `GET /medias/kyc/secret_recto.png` | 404, corps sans `PIECE-SECRETE` | serveur |
| R2 | anonyme | `GET /medias/x/../kyc/secret_recto.png` (`--path-as-is`) | refus (404/400), sans contenu | serveur |
| R3 | anonyme | `GET /medias/x/%2e%2e/kyc/secret_recto.png` (cas T1, aujourd'hui 200) | refus, sans contenu | serveur |
| R4 | anonyme | `GET /medias/x/%2E%2E/kyc/secret_recto.png` (majuscules) | refus, sans contenu | serveur |
| R5 | anonyme | `GET /medias/x/..%2fkyc%2fsecret_recto.png` et `/medias/x/%2e%2e%2fkyc/secret_recto.png` | refus, sans contenu | serveur |
| R6 | anonyme | double encodage : `GET /medias/x/%252e%252e/kyc/secret_recto.png` | refus ; en tout cas jamais le contenu (404 attendu : le fichier `%2e%2e` n'existe pas) | serveur |
| R7 | anonyme | barres inverses : `GET /medias/x\..\kyc\secret_recto.png` et `/medias/kyc%5csecret_recto.png` | refus, sans contenu | serveur |
| R8 | anonyme | chemin absolu / double barre : `GET /medias//kyc/secret_recto.png`, `/medias///kyc/…`, `/medias/%2fkyc/secret_recto.png`, `/medias//etc/passwd` | refus, sans contenu (rien hors de `MEDIA_ROOT`) | serveur |
| R9 | anonyme | `GET /medias/./kyc/secret_recto.png` et `/medias/catalogue/../kyc/secret_recto.png` | refus, sans contenu | serveur |
| R10 | anonyme, FS sensible à la casse (Linux) et FS insensible (si outillage Windows/macOS) | `GET /medias/KYC/secret_recto.png`, `/medias/Kyc/…` | 404 ; sur un FS insensible à la casse, aussi sans contenu (point à vérifier, cf. questions) | serveur |
| R11 | anonyme | octet nul / caractères de contrôle : `GET /medias/kyc%00/secret_recto.png`, `/medias/x/%2e%2e%00/kyc/…` | 400/404, jamais 500, sans contenu | serveur |
| R12 | un lien symbolique `MEDIA_ROOT/catalogue/lien -> MEDIA_ROOT/kyc` existe (ou `lien/secret_recto.png`) | anonyme : `GET /medias/catalogue/lien/secret_recto.png` | refus, sans contenu (la défense doit se faire sur le chemin **résolu**, pas sur le texte). Si le lien n'est pas défendable, le consigner en question ouverte | serveur |
| R13 | tiers T connecté (session valide), DEBUG=0 puis 1 | rejoue R1, R3, R5 avec cookie de T | mêmes refus : la session n'ouvre pas `/medias/kyc` | serveur |
| R14 | propriétaire P et administrateur A connectés | rejoue R1 et R3 avec leur session | `/medias/…` refuse aussi : ils passent uniquement par `/pieces/` | serveur |
| R15 | non-régression : P propriétaire | `GET /pieces/<id>/recto/` puis `/verso/` | 200, corps = octets `PIECE-SECRETE`, en-tête `Cache-Control: private, no-store` | serveur |
| R16 | non-régression : A administrateur | `GET /pieces/<id>/recto/` | 200, même contenu | serveur |
| R17 | T tiers connecté ; puis anonyme | `GET /pieces/<id>/recto/` | 404 dans les deux cas (la doc de la vue choisit 404, pas 403), sans contenu | serveur |
| R18 | erreurs de `/pieces/` | `GET /pieces/<id inexistant>/recto/` ; `/pieces/<id>/dos/` ; P sur un dossier sans verso | 404 avec message lisible, sans contenu ; jamais 500 | serveur |
| R19 | non-régression : média public | anonyme, `GET /medias/catalogue/produit.png` (DEBUG=0 puis 1) | 200, octets identiques au fichier ; type image | serveur |
| R20 | non-régression : sous-dossier public contenant un `..` interne légitime qui reste dans le public | anonyme, `GET /medias/catalogue/x/../produit.png` | pas de 500 ; 200 ou 404 acceptés, mais **jamais** de sortie vers `kyc/` ; comportement noté dans la fiche après essai | serveur |
| R21 | non-régression : le lien d'une pièce renvoyé par l'API | `GET` du profil/dossier KYC par P (serialiseurs.py:163) | le champ contient `/pieces/<id>/recto/`, jamais `/medias/kyc/…` ; la réponse n'expose aucun chemin `kyc/` brut | serveur |
| R22 | réponse du serveur | scan de toutes les réponses des scénarios R1–R14 | aucune ne contient `PIECE-SECRETE` ni le nom `secret_recto.png` dans un en-tête `Location` | serveur |

### Tests automatiques attendus
Fichier : `backend/groupachat/tests/test_securite.py` (déjà collecté ; il traverse comptes et fichiers), classe `TestPiecesKycPrivees`, paramétrée sur DEBUG=0 et DEBUG=1 pour R1–R14 :
- `test_le_chemin_direct_kyc_est_refuse` (R1) ; `test_la_traversee_en_points_encodes_est_refusee` (R2–R4, R9) ; `test_la_traversee_avec_barre_encodee_est_refusee` (R5, R6) ; `test_les_barres_inverses_sont_refusees` (R7) ; `test_un_chemin_absolu_ou_double_barre_est_refuse` (R8) ; `test_la_casse_differente_ne_contourne_pas_le_refus` (R10) ; `test_un_octet_nul_ne_provoque_pas_d_erreur_500` (R11) ; `test_un_lien_symbolique_vers_kyc_est_refuse` (R12) ; `test_une_session_ne_change_pas_le_refus_de_medias` (R13, R14).
- Non-régression : `test_le_proprietaire_lit_sa_piece` (R15), `test_l_administrateur_lit_la_piece` (R16), `test_un_tiers_et_un_anonyme_ne_lisent_pas_la_piece` (R17), `test_cotes_et_dossiers_inconnus_donnent_404` (R18), `test_un_media_de_catalogue_reste_public` (R19, R20), `test_le_profil_ne_donne_que_le_lien_pieces` (R21).
Chaque test d'attaque affirme l'absence des octets secrets dans `reponse.content` (ou le flux `streaming_content`), pas seulement le statut. Le test doit échouer avant le correctif (R3 : 200 aujourd'hui) ; pour R1 en DEBUG=1, l'urlconf doit être rechargé (`importlib.reload` + `clear_url_caches`) car `static()` est évalué à l'import.
Les motifs `%2e` doivent être testés au niveau du serveur de développement ou par `curl --path-as-is` : le client de test Django décode déjà certaines séquences ; si un cas ne peut pas être joué par `APIClient`, le dire.

### Vérification d'interface
Pas d'interface propre. Contrôle de contrat : l'écran de dépôt/suivi KYC (boutique et console admin) affiche les pièces via `/pieces/<id>/recto/` (champ du sérialiseur), pas via `/medias/`. À constater à la recette : `grep -rn "medias/kyc\|/kyc/" frontend/*/src` ne renvoie aucun appel. Les images de pièces s'affichent pour P et A (200), aucune pour T.

## Questions ouvertes
1. Casse : sur un FS insensible à la casse (déploiement Windows/macOS), `Kyc/` passerait-il ? Le déploiement Coolify est Linux ; on suppose que seul Linux compte. À confirmer.
2. Lien symbolique (R12) : exiger un refus sur chemin résolu, ou accepter que le dossier `MEDIA_ROOT` n'en contienne jamais ? Le code actuel ne crée pas de lien ; décision demandée à l'archi.
3. Code de refus attendu pour `/medias/` interdit : la vue lève 404. R2–R11 acceptent 400/404 ; faut-il imposer 404 partout ?
4. Pièces déjà exposées en production : la rotation/suppression des pièces réelles est une opération hors code, décidée par l'utilisateur (voir D-F030).

## Résultat de la recette (2026-10-27) — RECETTE OK
Base `ccd9187` + correctif non commité à la date de la recette (arbre de travail, HEAD ccd9187) ; commité ensuite en `fb4963c`. Serveur réel `runserver` en DEBUG=0 puis DEBUG=1, `curl --path-as-is`, `MEDIA_ROOT` et base sqlite fictifs hors dépôt (réglages de recette dans le scratchpad), comptes P, P2 (groupeurs), T (acheteur), A (administrateur).
- R1 à R12, R20 et les extras (`/medias/kyc`, `/medias/`, `../../etc/passwd` en clair et en `%2e%2e`) : **404, aucune fuite de `PIECE-SECRETE`, aucun `Location`**, en DEBUG=0 et 1, anonyme. R12 (lien symbolique `catalogue/lien -> kyc`) : 404. R11 : 404, jamais 500.
- R13/R14 : mêmes 27 refus (404) pour T, P et A connectés, en DEBUG=0 et 1.
- R15/R16 : P et A reçoivent 200, octets du fichier, `Cache-Control: private, no-store` (recto et verso). R17 : T, anonyme, et groupeur P2 sur le dossier de P : 404. R18 : dossier inconnu, côté `dos`, verso absent : 404, pas de 500.
- R19 : 200, octets du média public, DEBUG=0 et 1. R20 (`catalogue/x/../produit.png`) : 200 (normalisé, reste dans le public).
- R21 : `/api/comptes/dossier/` donne `lien_recto`/`lien_verso` = `/pieces/1/recto/`, aucun champ `piece_*` ni chemin `kyc/` ; idem `/api/admin/dossiers/` (A : 200, T : 403).
- Contrat d'interface : `grep medias/kyc|/kyc/ frontend/*/src` ne renvoie rien ; la console admin affiche `dossier.lien_recto` (`Dossiers.tsx:199`).
- Réserves (hors sécurité) : les 404 de `/pieces/` sont la page HTML Django en anglais (« Not Found »), pas un message lisible en français (R18 attendait « message lisible »). R10 vérifié sous Linux seulement.
