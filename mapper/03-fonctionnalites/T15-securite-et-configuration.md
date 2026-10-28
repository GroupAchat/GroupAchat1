---
type: fonctionnalite
statut: à faire
mission: M-001
tache: T15
date: 2026-10-28
base: 60b6cbd
---

# T15 · Sécurité et configuration (audit T8) — suppression de l'étape du code SMS

Rôle : visiteur (inscription, connexion), acheteur (juste après l'inscription), exploitant (configuration) · Couches : serveur oui · web oui (boutique) · mobile non (aucun client mobile dans ce dépôt) · Source : audit T8 (B-1, B-2, B-3, I-3, I-5, I-6, M-1), recette MVP C-066, décision de l'utilisateur du 2026-10-28.

**Décision de l'utilisateur (2026-10-28)** : l'étape du code SMS disparaît. L'inscription crée un compte **déjà vérifié** ; la connexion se fait par téléphone et mot de passe ; aucun code n'est plus émis ni affiché. Contrepartie acceptée : personne ne prouve qu'il possède le numéro.

**Risques acceptés par cette décision** (à ne pas rouvrir en revue) : un tiers peut inscrire le numéro d'un autre avant lui (squat) ; « Numéro vérifié » ne prouve plus rien ; le texte « lui seul peut retirer vos colis » s'appuie désormais sur le seul mot de passe.

Hors T15 : I-4 (CORS), I-2 (limites sur participation et retrait), M-2 à M-7, C-019 (`role=groupeur` accepté à l'inscription : il reste vrai ; le groupeur est de toute façon bloqué par le KYC).

---

## 1. État constaté (commit 60b6cbd)

### Serveur
| Élément | Où | Ce qu'il fait aujourd'hui |
|---|---|---|
| Route inscription | `groupachat/api.py:87` → `InscriptionVue` (`comptes/vues.py:67-86`) | crée le compte **non vérifié**, appelle `envoyer_code`, répond 201 `{utilisateur, verification:{sms_simule, code_affiche}}`. **N'ouvre pas de session.** |
| Route vérification | `api.py:88` → `VerificationVue` (`vues.py:89-150`) | contrôle le code, passe `telephone_verifie` à vrai, **ouvre la session** (`login`, l. 150) |
| Route renvoi | `api.py:89` → `RenvoiCodeVue` (`vues.py:153-172`) | réémet un code ; renvoie le code dans la réponse (**B-1**) |
| Connexion | `api.py:90` → `ConnexionVue` (`vues.py:175-205`) | ouvre la session ; si le compte n'est pas vérifié, **réémet un code et le renvoie** (l. 200-206) |
| Aides de vue | `_envoyer_ou_refuser`, `_reponse_envoi` (`vues.py:42-68`) | convertissent `TropDeCodes` en 429 ; mettent `code_affiche` dans la réponse |
| Service | `comptes/services.py` (56 lignes, tout le fichier) | `envoyer_code`, `ResultatEnvoi`, `PASSERELLES_SIMULEES` (inclut `""` : variable vide = simulé). **Journalise numéro + code** à la ligne 51 (**B-2**). `NotImplementedError` pour tout autre fournisseur |
| Modèle | `comptes/models.py:152-228` : `TropDeCodes`, `CodeVerification` (`MAX_TENTATIVES=5`, `MAX_CODES_PAR_HEURE=5`, `emettre`, `est_utilisable`) ; migration `0001_initial` | table `comptes_codeverification` |
| Champ | `Utilisateur.telephone_verifie` (`models.py:95`, défaut **False**) ; `create_superuser` le pose à vrai (l. 68) | exposé en lecture seule par `UtilisateurSerialiseur` (`serialiseurs.py:72,78`) |
| Sérialiseurs | `VerificationSerialiseur` (l. 130), `RenvoiCodeSerialiseur` (l. 135) | n'ont plus d'usage sans les routes |
| Permissions | `noyau/permissions.py:11-22` `NumeroVerifie` ; `:~60-67` `LectureLibreEcritureVerifiee` | exigent `telephone_verifie` : utilisées par `commandes/vues.py:37,113`, `echanges/vues.py:40,175`, `comptes/vues.py` (`DossierKYCVue`) |
| Limites | `noyau/limitation.py:55-70` `LimiteVerification` (scope `verification`), `LimiteRenvoi` (scope `renvoi_code`) ; `LimiteParNumero` (l. 25-52) ; docstring l. 1-26 qui parle des codes | `settings.py:292-293` `LIMITE_VERIFICATION` 12/h, `LIMITE_RENVOI` 4/h |
| Réglages | `settings.py:323` `VALIDITE_CODE_SMS_MINUTES` ; `:325` `SMS_FOURNISSEUR` (défaut `console`) | |
| Démo | `charger_demo.py:38` importe `CodeVerification`, `:172` le vide dans `enchainement` ; tous les comptes créés par la démo ont `telephone_verifie=True` (l. 221, 235, 275, 300, 477) ; `VERSION_DEMO = "7"` (l. 66) | |
| `DEBUG` | `settings.py:26` défaut **"1"** ; `:28-36` clé de repli publique si `DEBUG` ; `:258-259` cookies `Secure` seulement hors `DEBUG` | **B-3** |
| CI | `.github/workflows/ci.yml:49-51` `DJANGO_DEBUG: "1"`, `DJANGO_SECRET_KEY`, `SMS_FOURNISSEUR: demonstration` ; `:72` `check --deploy` avec `DJANGO_DEBUG=0` | |
| Conteneur | `docker-compose.yml:82` `VITE_DEMONSTRATION`, `:92` `DJANGO_DEBUG:-0`, `:94-107` commentaire sur `creer_administrateur`/`ADMIN_*` (commande **inexistante** : `ls comptes/management` échoue), `:108-114` bloc `SMS_FOURNISSEUR` ; `backend/Dockerfile:40-41` `ARG`/`ENV VITE_DEMONSTRATION` | |

### Web (boutique)
- `frontend/boutique/src/pages/Authentification.tsx` : `Cadre` (l. 31-65) porte la pastille `absolute -right-24 -top-10 size-72` **sans `overflow-hidden`** (l. 33-36, **C-066**) ; `Inscription` (l. 71-185) a deux étapes (`formulaire` puis `code`), lit `reponse.verification.code_affiche` ; `Connexion` (l. 189-258) bascule sur `EtapeCode` si `!telephone_verifie` ; `EtapeCode` (l. 262-end) appelle `POST /comptes/verification/` et `POST /comptes/renvoyer-code/`, affiche « Démonstration — SMS simulé » + le code. Textes : « un code par SMS » (l. 117), « il sera vérifié par SMS » (l. 150), « Vérifiez votre numéro » ; type local `ReponseVerification` (l. 11-14).
- `frontend/commun/src/api/types.ts:36` : `telephone_verifie: boolean` ; `commun/src/contexte/Session.tsx:96` : `peutAgir = Boolean(utilisateur?.telephone_verifie)` ; `boutique/src/pages/Profil.tsx:106-109` : badge « Numéro vérifié » ; `boutique/src/composants/Discussion.tsx:17` commentaire « Écrire demande un numéro vérifié ». Aucun appel du code ailleurs (`grep -rln "renvoyer-code\|code_affiche\|ReponseVerification" frontend/*/src` → seulement `Authentification.tsx`). La console `admin/` n'est pas concernée.

### Tests (tous collectés par `pytest.ini`)
- `comptes/tests.py` : `inscrire` (l. 40-49) ; `TestInscription` 5 tests (l. 52-80) ; `TestVerification` 5 tests (l. 81-135) ; `TestConnexion` 3 tests (l. ~137-172) ; fixture `client_verifie` (l. 175-180, utilisée par les tests du dossier KYC).
- `tests/test_securite.py` : `TestPlafondDesCodes` 4 tests (l. 47-93) ; `TestLimitationDeDebit` 2 tests (l. 95-125) ; imports `CodeVerification`, `TropDeCodes` (l. 23-25).
- Tests qui forcent `telephone_verifie=False` à la main pour éprouver `NumeroVerifie` : `commandes/tests.py:40,730`, `echanges/tests.py:37` — **à garder**.
- `conftest.py:29` crée ses comptes avec `telephone_verifie=True`.

### Configuration et documentation
- `.env.exemple` : `VITE_API_URL=http://localhost:8000/api` (l. 133, **I-3**) ; bloc `ADMIN_IDENTIFIANT`/`ADMIN_MOT_DE_PASSE` + `creer_administrateur` (l. ~60-80) ; bloc `DJANGO_HTTPS` (l. ~200-215, jamais lu ; parle d'HSTS « un an », le code met 30 jours) ; bloc `SMS_FOURNISSEUR=demonstration` + `CODE_SMS_DEMONSTRATION` (l. 226-253 ; le texte « sans cette variable la connexion répond 503 » est **faux**, le code retombe en simulé) ; `VITE_DEMONSTRATION=0` (l. 174, lu nulle part dans `frontend/`, seulement relayé par le Dockerfile ; et `docker-compose.yml:82` le met à **1** par défaut) ; **bloc `SMTP_*` et `COURRIEL_EXPEDITEUR` (l. 277-286) : aucune ligne de `backend/` ne les lit** (pas de réglage `EMAIL_*`, pas de `backend/.courriels`) — écart que l'audit n'a pas relevé.
- Lues par le code, absentes de `.env.exemple` (sortie réelle du script du §3, base 60b6cbd) : `DELAI_DECISION_JOURS`, `DJANGO_ORIGINES_SURES`, `FRAIS_PLATEFORME_FCFA`, `HOTES_ADMINISTRATION`, `LIMITE_CONNEXION`, `LIMITE_INSCRIPTION`, `RACINE_WEB`, `TAILLE_MAX_PIECE_OCTETS`, plus `LIMITE_RENVOI`, `LIMITE_VERIFICATION`, `VALIDITE_CODE_SMS_MINUTES` (qui **disparaîtront du code**, donc ne seront pas ajoutées) et deux variables que l'audit n'a pas vues : `PORT_BASE` (`docker-compose.override.yml:23`) et `GUNICORN_PROCESSUS` (`entrypoint.sh:72`).
- `.gitignore` : motifs `backend/.venv/`, `node_modules/`, `**/node_modules/` finissent par `/` et ne couvrent donc pas un **lien symbolique** ; `.claude/worktrees/` n'y figure pas (`git check-ignore -v .claude/worktrees/x` : aucune sortie, constaté ; `backend/.venv` n'est ignoré que par `backend/.gitignore:1`, et seulement tant que c'est un dossier).
- Documentation fausse après la décision : `CLAUDE.md:102,105` (« le code s'affiche à l'écran », « passerelle SMS ») ; `README.md:94` ; `COOLIFY.md:63` (`SMS_FOURNISSEUR`), `:96-97` (`LIMITE_VERIFICATION`, `LIMITE_RENVOI`), `:100-113` (« quatre portes », plafond de codes en base), `:294` (« le code de vérification s'affiche »), `:~300` (renvoi à `comptes/services.py`) ; `CAHIER_DES_CHARGES.md:42,97,132,142,148,163` (code SMS, « vérifié par SMS », tableau de ce qui est simulé) ; `.claude/conventions/architecture.md` et `CLAUDE.md` (« simulés derrière … la passerelle SMS »). `COOLIFY.md:284` (garder `DJANGO_DEBUG=1` en local) contredit `.env.exemple:103-106` (« laisser à 0 »).

---

## 2. Conception proposée (sans code)

**Disparaît**
- Routes `comptes/verification/` et `comptes/renvoyer-code/` (et leurs `name`), `VerificationVue`, `RenvoiCodeVue`, `VerificationSerialiseur`, `RenvoiCodeSerialiseur`, `_envoyer_ou_refuser`, `_reponse_envoi`.
- `comptes/services.py` en entier (fichier supprimé) : plus d'`envoyer_code`, plus de passerelle, plus de journal du code ni du numéro.
- `LimiteVerification`, `LimiteRenvoi` et leurs deux taux (`verification`, `renvoi_code`) ; réglages `SMS_FOURNISSEUR`, `VALIDITE_CODE_SMS_MINUTES` ; variables `LIMITE_VERIFICATION`, `LIMITE_RENVOI`.
- Côté web : `EtapeCode`, `ReponseVerification`, l'étape « code » de `Inscription`, la bascule de `Connexion`, les imports devenus inutiles (`MessageSquareCode`, `ShieldCheck`, `AnimatePresence`, `useEffect`, `useRef`).

**Change de comportement**
- `POST /comptes/inscription/` : crée le compte avec `telephone_verifie=True` (posé **explicitement par le sérialiseur**, jamais lu dans la requête), ouvre la session (`login`, backend `ModelBackend`), répond 201 `{utilisateur}` — **plus de clé `verification`**. Le jeton CSRF tourne à l'ouverture de session, comme avant à la vérification : le client le gère déjà.
- `POST /comptes/connexion/` : plus de branche « compte non vérifié » ; réponse `{utilisateur}` seule.
- Web : `Inscription` = un formulaire, puis session ouverte et navigation vers `/` ; `Connexion` ne bascule plus ; les textes « par SMS » disparaissent ; la pastille décorative est contenue (C-066) ; le badge « Numéro vérifié » de `Profil.tsx` est retiré (voir Q6).
- `DJANGO_DEBUG` : défaut `"0"`. Conséquences à traiter dans le même passage : sans `DJANGO_SECRET_KEY` et sans `DJANGO_DEBUG=1`, Django refuse de démarrer — y compris `pytest` et « Vérifier » dans un worktree sans `.env` (voir Q5).

**Reste**
- `telephone_verifie`, `NumeroVerifie`, `LectureLibreEcritureVerifiee`, le champ dans l'API et dans `types.ts`/`Session.tsx` : intacts (garde-fou, et tests existants qui forcent `False`). Tous les nouveaux comptes sont vérifiés par construction.
- `LimiteInscription`, `LimiteConnexion` (par IP). `LimiteParNumero` reste si Q4 = oui, sinon est supprimée avec ses deux filles.

**Données et migration** (sous réserve des réponses Q1/Q2) : une migration de données `comptes/0005` passe `telephone_verifie=True` pour tous les comptes ; la suppression du modèle `CodeVerification`/`TropDeCodes`, si elle est retenue, est une migration distincte `0006` (`DeleteModel`) pour pouvoir être écartée seule.

**Documentation** : `CLAUDE.md` (« Ce qui est simulé » : plus de SMS ni de code ; seuls paiement et versement sont simulés ; inscription = compte vérifié), `README.md:94` et son parcours, `COOLIFY.md` (tableau des variables, §3 « quatre portes » → deux, plafond de codes retiré, §10), `CAHIER_DES_CHARGES.md` (voir Q6), `.env.exemple`, `docker-compose.yml`, `backend/Dockerfile`, `ci.yml`. Les lignes de `.claude/conventions/architecture.md` et de `CLAUDE.md` sur « la passerelle SMS » : `.claude/` est de la configuration, à signaler à l'utilisateur plutôt qu'à modifier par `fonctionnalite` sans accord.

**`.env.exemple`** : `VITE_API_URL=` vide ; retirer `ADMIN_*`, `DJANGO_HTTPS`, `SMS_FOURNISSEUR`, `CODE_SMS_DEMONSTRATION`, `VITE_DEMONSTRATION` (et sa relance dans Dockerfile/compose), bloc `SMTP_*`/`COURRIEL_EXPEDITEUR` ; ajouter avec une valeur factice et une phrase de pourquoi : `DJANGO_ORIGINES_SURES`, `FRAIS_PLATEFORME_FCFA`, `DELAI_DECISION_JOURS`, `TAILLE_MAX_PIECE_OCTETS`, `LIMITE_CONNEXION`, `LIMITE_INSCRIPTION`, `HOTES_ADMINISTRATION`, `RACINE_WEB`, `PORT_BASE`, `GUNICORN_PROCESSUS` ; corriger le texte HSTS (30 jours) ; `DJANGO_DEBUG` : valeur sûre `0` avec la mention « en local, mettre 1 ». Le script du §3 devient le contrôle permanent (`scripts/controle_env.sh`).

**`.gitignore`** : motifs sans `/` final pour les liens (`backend/.venv`, `node_modules`, `**/node_modules`) et `/.claude/worktrees`.

### Fichiers que le correctif touchera
Serveur : `backend/groupachat/comptes/vues.py`, `services.py` (supprimé), `serialiseurs.py`, `models.py` (si Q2 = supprimer), `comptes/migrations/0005_*.py` (et `0006_*.py`), `backend/groupachat/api.py`, `noyau/limitation.py`, `backend/config/settings.py`, `catalogue/management/commands/charger_demo.py` (import et `enchainement` si le modèle part). Tests : `comptes/tests.py`, `tests/test_securite.py`, nouveau `tests/test_reglages.py`. Web : `frontend/boutique/src/pages/Authentification.tsx`, `pages/Profil.tsx`. Configuration : `.env.exemple`, `.gitignore`, `docker-compose.yml`, `backend/Dockerfile`, `.github/workflows/ci.yml`, nouveau `scripts/controle_env.sh`. Documentation : `CLAUDE.md`, `README.md`, `COOLIFY.md`, `CAHIER_DES_CHARGES.md` (Q6).

### Tests à supprimer — parce que la fonctionnalité disparaît (décision de l'utilisateur du 2026-10-28), pas pour les faire passer
`comptes/tests.py` :
1. `TestInscription::test_le_code_est_rendu_tant_que_le_sms_est_simule` — le code n'existe plus (remplacé par R1).
2. `TestVerification::test_le_bon_code_verifie_et_ouvre_la_session` — route supprimée ; l'effet (compte vérifié, session ouverte) passe dans R1.
3. `TestVerification::test_un_mauvais_code_decompte_les_essais` — plus de code à deviner.
4. `TestVerification::test_le_code_est_a_usage_unique` — idem.
5. `TestVerification::test_un_code_neuf_perime_le_precedent` — idem.
6. `TestVerification::test_numero_inconnu_ne_dit_pas_qu_il_est_inconnu` — route de renvoi supprimée (remplacé par R10).
7. `TestConnexion::test_un_compte_non_verifie_recoit_un_code_a_la_connexion` — comportement supprimé (remplacé par R7 : la connexion ne rend aucun code).

`tests/test_securite.py` :
8-11. `TestPlafondDesCodes` : `test_un_compte_ne_recoit_pas_plus_de_cinq_codes_par_heure`, `test_le_plafond_se_relache_apres_une_heure`, `test_le_plafond_est_par_compte`, `test_l_api_refuse_poliment_au_lieu_de_planter` — plus de codes à plafonner.
12. `TestLimitationDeDebit::test_la_limite_de_renvoi_suit_le_numero_pas_l_adresse` — route supprimée. **Réécrit** en limite par numéro de la connexion si Q4 = oui, sinon simplement supprimé.

Total : 12 supprimés (+ imports `CodeVerification`, `TropDeCodes` nettoyés).

### Tests à réécrire (le comportement demeure, l'étape change)
- `TestInscription::test_le_numero_est_normalise` : même normalisation, mais attend `telephone_verifie is True` (aujourd'hui `False`, l. 57).
- `TestConnexion::test_connexion_puis_deconnexion` : retire l'appel à `verification/` ; l'inscription ouvre déjà la session.
- Fixture `client_verifie` : devient `inscrire(client)` seul (les tests du dossier KYC en dépendent ; ils ne changent pas).
**Inchangés et à garder** : `test_le_doublon…`, `test_mot_de_passe_trop_faible_refuse`, `test_numero_trop_court_refuse`, `test_mauvais_mot_de_passe_refuse`, `test_la_connexion_finit_par_etre_freinee`, et les tests `NumeroVerifie` de `commandes`/`echanges`.

---

## Recette

Rôle : visiteur, acheteur, exploitant · Couches : serveur oui · web oui · mobile non · Source : décision 2026-10-28, `CAHIER_DES_CHARGES.md` §2, audit T8.

### Scénarios

**A. Inscription et connexion (serveur)**

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | un visiteur anonyme, `SMS_FOURNISSEUR` absent, vide ou `demonstration` | `POST /api/comptes/inscription/` avec nom, prénom, `+228 91 00 22 33`, mot de passe valide | 201 ; `utilisateur.telephone == "91002233"` et `telephone_verifie == true` ; le corps ne contient **aucune** des clés `verification`, `code_affiche`, `sms_simule` ni aucune suite de 6 chiffres ; `GET /api/comptes/moi/` avec le même client → 200 ; `Utilisateur.objects.get(telephone="91002233").telephone_verifie` vrai | serveur |
| R2 | idem, journal capturé au niveau INFO sur tout le logger `groupachat` | inscription puis connexion | aucun enregistrement ne contient `91002233`, le mot de passe, ni « SMS » / « code de vérification » (B-2) | serveur |
| R3 | un compte `91002233` existe | on inscrit `+228 91 00 22 33` | 400 `{"telephone": ["Ce numéro a déjà un compte."]}` ; `Utilisateur.objects.count()` inchangé ; pas de session | serveur |
| R4 | visiteur | inscription avec mot de passe `12345678` ; avec numéro `9100` ; avec nom absent | 400 par champ (`mot_de_passe`, `telephone`, `nom`) ; aucun compte créé ; `GET /moi/` → 401/403 | serveur |
| R5 | visiteur malveillant | inscription avec `role="administrateur"` ; puis avec `role="acheteur"` plus `is_staff=true`, `is_superuser=true`, `telephone_verifie=false` | le 1er : 400 sur `role`, rien écrit ; le 2e : 201, compte créé `is_staff False`, `is_superuser False`, `role acheteur`, `telephone_verifie True` (le drapeau n'est pas pilotable par la requête) | serveur |
| R6 | `LIMITE_INSCRIPTION` à 20/hour (défaut) | 21 inscriptions valides depuis la même adresse | la 21e → 429 ; 20 comptes créés, pas 21 | serveur |
| R7 | un compte vérifié `91002233` | `POST /comptes/connexion/` avec `+22891002233` et le bon mot de passe | 200 ; corps `{utilisateur}` sans clé `verification` ; `GET /moi/` → 200 ; `POST /deconnexion/` → 204 puis `GET /moi/` → 401/403 | serveur |
| R8 | idem | mot de passe faux ; numéro inconnu avec un mot de passe quelconque | 401 dans les deux cas, **même message** « Numéro ou mot de passe incorrect. » ; pas de session | serveur |
| R9 | `LIMITE_CONNEXION` 60/hour | 70 essais faux depuis la même adresse | un 429 apparaît avant le 70e ; le bon mot de passe est refusé tant que la limite court | serveur |
| R9b | Q4 = oui | 11 essais faux sur le même numéro depuis 11 adresses (`REMOTE_ADDR` différentes) | un 429 dès le dépassement de la limite par numéro ; un autre numéro n'est pas gêné et se connecte (200) | serveur |
| R10 | un compte quelconque | `POST /api/comptes/verification/` et `POST /api/comptes/renvoyer-code/` avec un corps plausible, sans session et avec | 404 (route supprimée) ; `reverse("verification")` et `reverse("renvoyer-code")` lèvent `NoReverseMatch` ; aucun compte modifié | serveur |
| R11 | une base contenant 3 comptes `telephone_verifie=False` (acheteur, groupeur, actif/inactif) et 1 vérifié | on applique la migration `0005` | les 4 comptes ont `telephone_verifie=True` ; `is_active`, `role`, mot de passe inchangés ; rejouer la migration ne change rien ; migration inverse sans erreur | serveur |
| R11b | un compte resté non vérifié malgré tout (Q1 = « à la connexion ») | il se connecte | 200 et `telephone_verifie` passe à vrai ; sinon (Q1 = migration seule) : 200 et les écritures renvoient 403 « Vérifiez d'abord votre numéro de téléphone. » (comportement documenté) | serveur |

**B. Ce que l'acheteur peut faire juste après l'inscription (serveur)**

| # | Étant donné | Quand | Alors | Couche |
|---|---|---|---|---|
| R12 | une campagne en cours ; un visiteur qui vient de s'inscrire (aucun autre appel) | `POST` d'un commentaire sur la campagne | 201 ; le commentaire existe en base avec l'auteur | serveur |
| R13 | idem | `POST /api/participations/` puis le paiement de la part (action de paiement existante) | participation créée puis `payee` ; le séquestre de la campagne augmente du montant ; le groupeur reçoit une notification ; aucune réponse 403 « Vérifiez d'abord… » | serveur |
| R14 | idem, sans participation retirée | `POST /api/avis/` | refus **métier** lisible (4xx), et le message n'est pas « Vérifiez d'abord votre numéro… » ; avec une participation retirée en fixture : 201 | serveur |
| R15 | aucune session | `POST` commentaire ; `POST /participations/` ; `POST /avis/` | 401/403 ; rien écrit (non-régression : la suppression du code n'ouvre aucune porte) | serveur |
| R16 | un compte forcé en base à `telephone_verifie=False` | `POST /participations/` et `POST` commentaire | 403 « Vérifiez d'abord votre numéro de téléphone. » ; rien écrit (le garde-fou `NumeroVerifie` reste actif) | serveur |

**C. Configuration et dépôt**

| # | Étant donné | Quand | Alors | Couche |
|---|---|---|---|---|
| R17 | `DJANGO_DEBUG` absent, `DJANGO_SECRET_KEY=x`, `load_dotenv` neutralisé | on importe `config.settings` (sous-processus) | `DEBUG is False` ; `SESSION_COOKIE_SECURE` et `CSRF_COOKIE_SECURE` vrais ; `SECRET_KEY == "x"` | serveur |
| R18 | `DJANGO_DEBUG` absent **et** `DJANGO_SECRET_KEY` absent | idem | `RuntimeError` « DJANGO_SECRET_KEY est obligatoire hors DEBUG… » ; la clé `cle-de-developpement-a-ne-jamais-deployer` n'est jamais utilisée | serveur |
| R19 | `DJANGO_DEBUG=1` explicite | idem | `DEBUG True`, cookies non sécurisés (développement local) | serveur |
| R20 | `DJANGO_DEBUG` absent, clé et hôtes posés | `python manage.py check --deploy` | aucune alerte `security.W018` (DEBUG) ni `W009` (clé faible due au repli) | serveur |
| R21 | après correctif | `grep -rniE "SMS_FOURNISSEUR\|VALIDITE_CODE_SMS\|LIMITE_VERIFICATION\|LIMITE_RENVOI\|envoyer_code\|CodeVerification\|renvoyer-code\|code_affiche" backend frontend docker-compose.yml .env.exemple .github` (hors migrations, hors `node_modules`) | aucune sortie (si Q2 = garder le modèle : seules `models.py` et la migration `0001` peuvent encore citer `CodeVerification`) | serveur + web |
| R22 | après correctif | `bash scripts/controle_env.sh` (script du §3) | sortie 0 : « Lues par le code, absentes de .env.exemple : (aucune) » et « Dans .env.exemple, lues nulle part : (aucune) » | serveur |
| R23 | `.env.exemple` | `grep -E "^VITE_API_URL=" .env.exemple` | la ligne vaut exactement `VITE_API_URL=` (vide) | web |
| R24 | `.env.exemple` et le dépôt | `grep -rnE "DJANGO_HTTPS\|CODE_SMS_DEMONSTRATION\|VITE_DEMONSTRATION\|ADMIN_IDENTIFIANT\|ADMIN_MOT_DE_PASSE\|creer_administrateur\|SMTP_\|COURRIEL_EXPEDITEUR" . --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git --exclude-dir=mapper --exclude-dir=worktrees` | aucune sortie (aucune variable ni commande fausse) | serveur |
| R25 | un `.env` obtenu en copiant `.env.exemple`, seuls secrets remplis | `python manage.py check` puis `python manage.py migrate` sur SQLite jetable | passe ; `VITE_API_URL` vide dans le fichier ; le démarrage ne demande aucune variable absente de l'exemple | serveur |
| R26 | un lien symbolique `backend/.venv` et un `frontend/node_modules` (tels que créés dans un worktree) | `git check-ignore -v backend/.venv frontend/node_modules frontend/admin/node_modules frontend/boutique/node_modules` ; `git status --short` | chaque chemin est cité par une règle ; `git status` n'en liste aucun en `??` | serveur |
| R27 | un dossier `.claude/worktrees/agent-x/` | `git check-ignore -v .claude/worktrees/agent-x .claude/worktrees` | les deux sont ignorés ; `.claude/agents/` et `.claude/conventions/` ne le sont pas (`git check-ignore .claude/agents/x.md` sans sortie) | serveur |
| R28 | base vide | `python manage.py charger_demo` puis connexion de `99000011`, `90001122`, `96004477`, `90009988` (mot de passe `demo2026Groupe`) | la commande se termine sans `ImportError` ni `LookupError` ; les 4 connexions → 200 avec `telephone_verifie true` | serveur |

**D. Web (boutique, largeur 390 px)**

| # | Étant donné | Quand | Alors | Couche |
|---|---|---|---|---|
| R29 | viewport 390×844, `/connexion` | `document.documentElement.scrollWidth` | `390` (C-066 ; aujourd'hui 486) | web |
| R30 | idem, `/inscription` | idem | `390` | web |
| R31 | un visiteur sur `/inscription` | il remplit le formulaire valide et valide | **aucun écran de code** ; navigation vers `/` ; l'entête montre le compte connecté ; le réseau montre un seul `POST /api/comptes/inscription/` (201) et aucun appel à `verification` ni `renvoyer-code` | web |
| R32 | `/connexion` | bon identifiant ; puis mauvais mot de passe | 1er : arrivée sur `/` (ou `/groupeur` pour un groupeur validé) ; 2e : message lisible « Numéro ou mot de passe incorrect. » sous le formulaire, champs conservés | web |
| R33 | `/inscription` | numéro déjà inscrit ; mot de passe `12345678` | erreur sous le champ `telephone` (« Ce numéro a déjà un compte. ») ; erreur sous `mot_de_passe` ; pas de navigation | web |
| R34 | `/inscription` et `/connexion` | observation + `grep -niE "sms\|code\|vérifi" frontend/boutique/src/pages/Authentification.tsx` | aucune mention de SMS ni de code ; bouton en état « chargement » pendant l'envoi ; pas de badge « Numéro vérifié » dans `Profil` (Q6) ; le thème sombre garde un fond continu (la pastille est rognée, pas supprimée si l'on veut la garder) | web |
| R35 | après correctif | `cd frontend && npm run verifier` | typage et construction des deux interfaces passent ; aucun import inutilisé dans `Authentification.tsx` | web |
| R36 | les fichiers de documentation | `grep -niE "code (de vérification )?s'affiche\|passerelle SMS\|vérifié par SMS\|code reçu par SMS" CLAUDE.md README.md COOLIFY.md CAHIER_DES_CHARGES.md` | aucune sortie ; `CLAUDE.md` « Ce qui est simulé » dit que l'inscription crée un compte vérifié sans code et que seuls paiement et versement sont simulés | — |
| R37 | après correctif | `cd backend && python -m pytest --collect-only -q groupachat/comptes/tests.py groupachat/tests/test_securite.py groupachat/tests/test_reglages.py` puis la suite entière | les nouveaux tests sont collectés ; suite entière verte ; le nombre de tests = ancien − 12 + nouveaux, annoncé dans le rapport | serveur |

Soit **39 scénarios** (R1 à R37, plus R9b et R11b) : 30 serveur (dont configuration et dépôt), 8 web, 1 documentation. Mobile : sans objet.

### Tests automatiques attendus
Fichier `backend/groupachat/comptes/tests.py` (classes `TestInscription`, `TestConnexion`, nouvelle `TestAnciennesRoutesDuCode`, nouvelle `TestMigrationDesComptesVerifies`) :
- R1 `test_l_inscription_cree_un_compte_verifie_et_ouvre_la_session` — vérifie statut, `telephone_verifie`, absence des clés et de toute suite de six chiffres dans `reponse.content`, `moi` 200, valeur en base.
- R2 `test_ni_le_code_ni_le_numero_ne_sont_journalises` (`caplog`, niveau INFO).
- R3 `test_le_doublon_est_vu_malgre_une_autre_ecriture` (existant, ajouter le comptage et l'absence de session).
- R4 `test_mot_de_passe_trop_faible_refuse`, `test_numero_trop_court_refuse` (existants) + `test_un_champ_obligatoire_manquant_ne_cree_rien`.
- R5 `test_l_inscription_refuse_un_role_administrateur`, `test_l_inscription_ignore_les_drapeaux_de_privilege`.
- R6 `tests/test_securite.py::TestLimitationDeDebit::test_l_inscription_finit_par_etre_freinee`.
- R7 `test_connexion_puis_deconnexion` (réécrit) + `test_la_connexion_ne_rend_aucun_code`.
- R8 `test_mauvais_mot_de_passe_refuse` (existant) + `test_numero_inconnu_et_mauvais_mot_de_passe_ont_le_meme_message`.
- R9 `test_la_connexion_finit_par_etre_freinee` (existant, garder). R9b `test_la_connexion_est_limitee_par_numero_meme_en_changeant_d_adresse` (si Q4).
- R10 `TestAnciennesRoutesDuCode::test_les_routes_du_code_n_existent_plus` (404 ×2, `NoReverseMatch`, compte inchangé).
- R11 `TestMigrationDesComptesVerifies::test_les_comptes_non_verifies_sont_passes_verifies` (appelle la fonction `RunPython` de la migration sur des comptes créés avec `telephone_verifie=False` ; vérifie les champs inchangés et l'idempotence). R11b selon Q1.
- R12, R13, R14, R15 : `backend/groupachat/tests/test_apres_inscription.py` (traverse comptes, échanges, commandes, paiements) — `test_on_ecrit_dans_le_fil_juste_apres_l_inscription`, `test_on_paie_sa_part_juste_apres_l_inscription` (statut `payee` **et** séquestre augmenté **et** notification), `test_la_notation_juste_apres_l_inscription_refuse_pour_une_raison_metier`, `test_sans_session_on_n_ecrit_nulle_part`.
- R16 `commandes/tests.py:40,730` et `echanges/tests.py:37` (existants, à garder tels quels).
- R17-R20 : `backend/groupachat/tests/test_reglages.py` — `test_debug_est_faux_quand_la_variable_est_absente`, `test_les_cookies_sont_securises_hors_debug`, `test_sans_cle_et_sans_debug_le_demarrage_echoue`, `test_debug_explicite_active_le_mode_developpement`, `test_check_deploy_ne_signale_ni_debug_ni_cle_faible` — chacun par **sous-processus** avec environnement nettoyé et `load_dotenv` neutralisé (un `.env` à la racine fausserait le test).
- R21, R22, R24 : `test_reglages.py::test_aucun_reste_du_code_sms`, `::test_env_exemple_concorde_avec_le_code` (lance `scripts/controle_env.sh`, exige la sortie 0), `::test_env_exemple_ne_documente_rien_de_faux`.
- R23 `test_reglages.py::test_vite_api_url_est_vide_dans_l_exemple`.
- R26, R27 : contrôle manuel du recetteur (`git check-ignore`), non automatisé (dépend de l'état du dépôt).
- R28 `catalogue/tests.py` : `test_charger_demo_tourne_et_les_comptes_se_connectent` (s'il n'existe pas déjà ; sinon vérifier qu'il couvre la connexion des 4 comptes).
- R29-R35 : non automatisés (le dépôt n'a pas de test d'interface) ; rejoués par le recetteur avec Playwright.

### Vérification d'interface
- **Inscription (`/inscription`, 390 px)** : titre, 5 champs, un bouton « Continuer » (ou « Créer mon compte »), lien « Se connecter ». Chargement : bouton `chargement` pendant le `POST`. Erreur : par champ (`pourChamp`) et message général dans `Alerte`. Succès : navigation vers `/`, plus d'étape intermédiaire. Pas d'état « vide ».
- **Connexion (`/connexion`)** : 2 champs, « Se connecter », lien « Créer un compte ». Erreur 401 et 429 lisibles (« Trop de tentatives… » pour 429 : vérifier que `ErreurApi.message` rend le `detail` DRF). Aucun écran de code après connexion.
- **Largeur** : `await page.setViewportSize({width:390,height:844})`, `await page.goto(base+"/connexion")`, `document.documentElement.scrollWidth === 390` ; idem `/inscription` ; capture `npx playwright screenshot --viewport-size=390,844 <url> connexion.png` puis lecture de l'image.
- **Profil** (compte connecté) : plus de badge « Numéro vérifié » (Q6).
- **Console `admin/`** : non touchée ; vérifier seulement que `npm run verifier` passe.

### Script de contrôle `.env.exemple` (à placer dans `scripts/controle_env.sh`)
Testé le 2026-10-28 sur 60b6cbd : il sort 1 et liste les écarts réels (§1). Il ignore les lignes de commentaire, lit `os.environ.get/[]`, `getenv`, `import.meta.env.*`, `${VAR}` de `docker-compose*.yml`/`entrypoint.sh`, `ARG` du Dockerfile. Les variables internes que l'entrypoint fabrique lui-même sont filtrées. Limite connue : une variable qui n'est que relayée (`ARG VITE_DEMONSTRATION`) compte comme « lue » — c'est pourquoi R24 la cherche explicitement.

```bash
#!/usr/bin/env bash
# Compare les variables lues par le code à celles de .env.exemple.
# Sortie 0 : concordance parfaite. Sortie 1 : écart (les deux listes sont affichées).
cd "$(git rev-parse --show-toplevel)" || exit 2
SANS_COMMENTAIRE='^[[:space:]]*#'
INTERNES='DEV|PROD|MODE|BASE_URL|SSR|PATH|HOME|PYTHONUNBUFFERED|DJANGO_SETTINGS_MODULE|DJANGO_SUPERUSER_NOM|DJANGO_SUPERUSER_PRENOM|DJANGO_SUPERUSER_TELEPHONE'
lues=$(
  {
    grep -rhE "environ|getenv" backend --include=*.py --exclude-dir=.venv --exclude-dir=migrations \
      | grep -vE "$SANS_COMMENTAIRE" | grep -oE "[\"'][A-Z][A-Z0-9_]{2,}[\"']" | tr -d "\"'"
    grep -rhoE "import\.meta\.env\.[A-Z][A-Z0-9_]+" frontend --include=*.ts --include=*.tsx \
      --exclude-dir=node_modules | sed 's/.*\.//'
    grep -hvE "$SANS_COMMENTAIRE" docker-compose*.yml backend/entrypoint.sh backend/Dockerfile \
      | grep -oE "\\$\{?[A-Z][A-Z0-9_]+|^ARG [A-Z][A-Z0-9_]+" | grep -oE "[A-Z][A-Z0-9_]+$"
  } | sort -u | grep -vxE "$INTERNES"
)
documentees=$(grep -hoE "^#? ?[A-Z][A-Z0-9_]+=" .env.exemple | tr -d '# =' | sort -u)
manquantes=$(comm -23 <(echo "$lues") <(echo "$documentees"))
fausses=$(comm -13 <(echo "$lues") <(echo "$documentees"))
echo "Lues par le code, absentes de .env.exemple :"; echo "${manquantes:-  (aucune)}"
echo "Dans .env.exemple, lues nulle part :";         echo "${fausses:-  (aucune)}"
[ -z "$manquantes$fausses" ]
```
Copie de travail déjà testée : `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/37d3c70e-6597-49b8-bb11-132f1e1eb6a5/scratchpad/controle_env.sh` (sans la ligne `INTERNES`).

---

## Questions ouvertes

**Q1 · Comptes existants non vérifiés (base locale de démonstration, production).**
- (a) Migration de données `0005` : tous les comptes passent vérifiés. Simple, idempotente, un seul geste au déploiement ; perd définitivement l'information « n'a jamais vérifié » (sans objet puisque plus rien ne vérifie).
- (b) À la connexion : un compte non vérifié le devient à son premier login. Aucune migration, mais le code d'authentification garde une branche et les comptes jamais reconnectés restent bloqués.
- (c) Rien : les comptes non vérifiés se connectent mais ne peuvent plus rien écrire, sans issue (plus de route de vérification). **À écarter.**
- **Recommandation : (a).** Sans (a) ou (b), un compte inscrit avant le correctif devient inutilisable en production.

**Q2 · Le modèle `CodeVerification` (et `TropDeCodes`).**
- (a) Le garder sans s'en servir : aucune migration de suppression ; mais du code mort, des constantes trompeuses, et `charger_demo` continue de l'importer.
- (b) Le supprimer : migration `0006` (`DeleteModel`, irréversible pour les données, sans valeur) ; code propre ; `charger_demo` et `test_securite.py` nettoyés.
- **Recommandation : (b)**, dans une migration distincte de `0005`, pour qu'on puisse l'écarter seule si l'on veut limiter les risques avant la présentation. Si l'on veut zéro risque d'ici demain : (a) puis (b) au backlog. Dans tous les cas `VERSION_DEMO` n'est **pas** incrémenté (le jeu n'est pas modifié).

**Q3 · Les anciennes routes `verification/` et `renvoyer-code/`.**
- (a) Supprimées : 404. Rien à maintenir, aucune chance qu'un code réponde par erreur.
- (b) `410 Gone` avec un message : un vieil onglet ouvert pendant le déploiement reçoit un message explicite au lieu d'une page « introuvable » ; coûte deux vues et le maintien d'un contrat mort.
- **Recommandation : (a).** Un onglet périmé se règle par un rechargement ; la démonstration est locale.

**Q4 · Limite de connexion par numéro.** Le mot de passe devient le seul facteur, et la connexion n'est limitée que **par adresse IP** (60/h, volontairement large derrière la traduction d'adresses des opérateurs) : une série d'adresses distinctes peut deviner le mot de passe d'un numéro sans être arrêtée. `LimiteParNumero` existe déjà.
- (a) Ajouter `LimiteConnexionParNumero` (par ex. 10/h, variable `LIMITE_CONNEXION_NUMERO`, scope documenté) : ferme ce trou ; contrepartie : quelqu'un peut bloquer un compte une heure en insistant sur son numéro.
- (b) Ne rien ajouter, noter au backlog avec I-2.
- **Recommandation : (a)**, puisque la décision retire la seule défense par numéro qui existait (celle des codes). À trancher avant le code : cela change le contrat (un 429 de plus à la connexion) et ajoute une variable.

**Q5 · Défaut de `DJANGO_DEBUG` à `0` et environnement des tests.** Sans `.env`, `pytest` et « Vérifier » (worktree) s'arrêtent sur `RuntimeError: DJANGO_SECRET_KEY est obligatoire`. Options : (a) `DJANGO_SECRET_KEY` + `DJANGO_DEBUG=1` exportés dans `.claude/skills/verify/scripts/check.sh` (fichier de configuration : accord requis) et dans la commande `pytest` du `README` ; (b) ajouter `pytest-env` (nouvelle dépendance, note dans `mapper/02-decisions/`) ; (c) un `.env` copié de `.env.exemple` dans chaque checkout (Claude ne peut que le créer par copie). Et pour `.env.exemple` : `DJANGO_DEBUG=0` (sûr, c'est ce que dit `docker-compose.yml`) ou `1` pour le développement local ? **Recommandation : (a) pour les tests, `.env.exemple` à `0` avec la ligne « en local, mettre `DJANGO_DEBUG=1` »** (c'est déjà la consigne de `COOLIFY.md:284`), et un README qui l'écrit au démarrage. Pour la présentation locale de demain : le `.env` de l'utilisateur doit porter `DJANGO_DEBUG=1`, sinon les cookies `Secure` posent problème sur Safari en `http://localhost`.

**Q6 · Textes qui disent « vérifié ».** Le badge « Numéro vérifié » du profil et le paragraphe de `CAHIER_DES_CHARGES.md` (§ vérification par SMS, tableau des simulés) deviendraient faux. (a) Retirer le badge et amender le cahier des charges pour qu'il dise la décision ; (b) laisser le badge (« vérifié » = « compte actif ») et ne toucher qu'au cahier des charges ; (c) ne rien toucher au cahier (document de l'utilisateur) et laisser l'écart écrit dans `mapper/`. **Recommandation : (a)** — afficher « vérifié » alors que personne ne l'a vérifié est une fausse promesse faite à l'acheteur, du même ordre que celles déjà corrigées en 04a86fd.

---

## Prêt à coder ?
**Oui, sous réserve des réponses à Q1 à Q5** (Q6 n'arrête pas le code serveur). Le reste est tranché par la décision du 2026-10-28.
