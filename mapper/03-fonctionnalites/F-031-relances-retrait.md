---
type: fonctionnalite
id: F-031
statut: terminée
date: 2026-10-28
tags: [fonctionnalite, F-031, retrait, reputation, tache-planifiee, mvp]
---

# F-031 — Relances de retrait à J+3 et J+7, livraison réputée acquise à J+14

Statut : **terminée** (recette OK le 2026-10-28, section « Recette — 2026-10-28 » ci-dessous ; T5 de [[M-001-terminer-le-mvp]], avec C-052). Implémentée sur la branche `feat/F-031-relances-retrait`, partie de `staging` `7a31195` ; commitée `5dc1562` (« Relance les retraits oubliés et clôt la campagne au quatorzième jour »), fusionnée dans `staging` le 2026-10-28. Conception : `archi-backend`, 2026-10-27, base `abaa622`. Rôle : **Système**. Sources : `CAHIER_DES_CHARGES.md` §4 (« Colis non récupéré », « Réputation », « Séquestre »), §3 (administrateur, points 4 et 5), §8 (notifications), §9 (cycle de vie) ; décision **Q13** et **Q4** de [[2026-10-26-decisions-carte]] ; verrous de [[2026-10-27-decisions-f016]] ; [[carte]] (parcours « colis non retiré », Q13, Q15).

**Pourquoi c'est MVP** : sans F-031, un seul participant qui ne vient pas chercher son colis laisse la campagne en `distribution` pour toujours. Elle n'atteint jamais `terminee`, et la réputation du groupeur n'est jamais créditée.

**Prêt à coder ?** Oui. T10 (F-024) est terminée le 2026-10-27 (code non commité, voir [[F-024-double-paiement]]). Effet sur cette fiche : **C-014 est fermé à la source** (`mettre_a_disposition` refuse `financee`, décision D1 de [[2026-10-27-decisions-f024]]). Une campagne en `distribution` avec des fonds encore consignés ne peut donc plus naître par le chemin de C-014 : la garde D1 ci-dessous (§ « Décisions ») devient **défensive**, et reste à coder. Les numéros de lignes de la section 1 sont ceux de `abaa622`, avant T10. Les questions 1 à 8 sont tranchées par l'utilisateur le 2026-10-27 ([[2026-10-27-decisions-f031]]), section « Décisions » ci-dessous. Les marques « à valider » du corps de la fiche renvoient à ces décisions.

## Décisions (2026-10-27)

Tranchées par l'utilisateur ; détail et motifs dans [[2026-10-27-decisions-f031]].

- **D1 (Q1, a)** : une campagne en distribution aux fonds encore consignés (C-014) n'est pas close ; la tâche la journalise et la signale dans `--a-blanc`, l'administrateur tranche. Dans le cas normal, une part réputée livrée ne déplace aucun argent.
- **D2 (Q2, b)** : un code présenté après J+14 est accepté ; la part passe `retiree`, `participants_servis` +1, la campagne compte une seule fois dans `campagnes_terminees`.
- **D3 (Q3, b)** : préavis de 72 h ; jamais de « réputée livrée » sans relance envoyée au moins 72 h avant.
- **D4 (Q4, a)** : on étend `cloturer_les_campagnes_echues` (deux étapes, `--a-blanc` compris) ; une seule tâche Coolify.
- **D5 (Q5, a)** : genres `livraison_reputee` (acheteur) et `campagne_terminee` (groupeur) ; champs `reputee_livree_le` et `fin_du_retrait_le`.
- **D6 (Q6, a)** : dates de relance sur `Campagne`, statut et date sur `Participation`, contrainte `participation_reputee_livree_datee` ; trois migrations d'ajout (`catalogue/0007`, `commandes/0004`, `echanges/0005`), accord de l'utilisateur.
- **D7 (Q7, b)** : libellé « Non retirée — réputée livrée » (recommandation de l'architecte, retenue par défaut ; à changer si l'utilisateur le demande).
- **D8 (Q8, a)** : T10 (F-024) passe avant T5 pour fermer C-014 à la source. Ordre de la mission : T10, T5, T6, T11, T12, puis T7 et T8.
- **D9 (Q1, b)** : seule la relance J+7 (ou la relance de rattrapage) vaut préavis de 72 h ; la J+3 seule ne suffit pas.
- **D10 (Q2, a)** : l'avertissement D1 est journalisé à chaque passage, sans colonne de plus.
- **D11 (Q3, a)** : le champ de code reste visible sur une campagne `terminee` tant qu'il reste une part `reputee_livree`.
- **D12** : C-052 (verrou de `cloturer`) est intégré à T5, ni tâche à part ni backlog.

Défaut relevé par l'architecte et inclus dans F-031 : `valider_retrait` ne verrouille rien (§4.4) ; une validation du dernier code pendant le passage de J+14 terminerait la campagne deux fois.

## Réalisation (2026-10-28)

- Module neuf : `backend/groupachat/paiements/retraits.py` (relances, livraison réputée, verrous via `_verrouiller` et `_terminer` de `services.py`). Appelé par `cloturer_les_campagnes_echues`, une fois par heure.
- Migrations d'ajout : `backend/groupachat/catalogue/migrations/0007_relances_de_retrait.py`, `backend/groupachat/commandes/migrations/0004_participation_reputee_livree.py`, `backend/groupachat/echanges/migrations/0005_alter_notification_genre.py`.
- Démonstration : `VERSION_DEMO` « 7 » (campagne « Bouilloires Tefal » réputée livrée). `COOLIFY.md` §4 mis à jour.
- Écrans : `frontend/boutique/src/pages/MesAchats.tsx`, `pages/groupeur/CampagneGroupeur.tsx`, `pages/Notifications.tsx`, `composants/Cloche.tsx` ; types dans `frontend/commun/src/api/types.ts`.
- Tests : `backend/groupachat/tests/test_retraits_echus.py` (54 tests), et `tests/test_notifications_liens.py` complété.
- Vérification : « Vérifier » `check.sh complet` : `406 passed, 9 skipped`, `CHECK: OK (complet)`. PostgreSQL 17 : `test_retraits_echus.py` 54 passed, 0 skipped (relecture). `check.sh rapide` : `338 passed, 9 skipped`. `test-diff.sh` : 0 signal.
- Relecture `reviewer-tester` : **VALIDÉE** en première passe, sans point bloquant. Suggestion non bloquante : renommer `_terminer` et `_verrouiller` sans `_`, puisqu'ils sont importés par `retraits.py` (chantier C-062).
- Défauts relevés par la recette, hors F-031 : C-059 (bilan « 0 relance(s) » pour la relance de rattrapage en passage réel), C-060 (erreur 500 affichée comme état vide sur `/mes-achats` et `/notifications`), C-061 (page groupeur d'une campagne terminée pendant le chargement).

## 1. Ce qui existe (constaté le 2026-10-27, `abaa622`)

| Élément | Où | État |
|---|---|---|
| `Campagne.mise_a_disposition_le` | `catalogue/models.py` l. 345 | posé par `mettre_a_disposition` (`paiements/services.py` l. 526), une seule fois par campagne : la campagne passe `distribution` et **toutes** les parts `payee` deviennent `prete` au même instant |
| `Notification.Genre.RELANCE_RETRAIT` | `echanges/models.py` l. 246 | genre déclaré, **jamais émis** ; icône déjà prévue (`relance_retrait: PackageCheck` dans `Notifications.tsx` et `Cloche.tsx`) |
| `Participation.delai_retrait_depasse` | `commandes/models.py` l. 148 | propriété **jamais utilisée** (grep), 14 écrit en dur |
| `valider_retrait` | `paiements/services.py` l. 570 | passe la part `retiree`, puis la campagne `terminee` quand plus aucune part n'est `prete`, puis `_crediter_reputation`. **Sans verrou** sur la campagne ni sur la part |
| `_crediter_reputation` | `paiements/services.py` l. 618 | `campagnes_terminees += 1`, `participants_servis +=` nombre de parts `retiree`. Ne touche pas la note |
| `recalculer_reputation` | `paiements/services.py` l. 637 | note = moyenne des avis (§4 « Réputation ») ; appelée par les vues d'avis |
| `Reputation` | `comptes/models.py` l. 289 | compteurs stockés : `campagnes_terminees`, `campagnes_annulees`, `avis_recus`, `participants_servis`, `note` |
| `STATUTS_PAYES` | `commandes/models.py` l. 42 | `payee`, `prete`, `retiree` : sert à la jauge, au montant collecté, au nombre de participants, au gel de la campagne, au tableau de bord groupeur, à `rembourser` et `_prevenir_participants` |
| Tâche horaire | `catalogue/management/commands/cloturer_les_campagnes_echues.py` | appelle `cloturer_les_echus` puis `rembourser_les_indecis` ; `--a-blanc` annonce sans écrire ; planification décrite dans `COOLIFY.md` §4 (`0 * * * *`), à vérifier par l'utilisateur (C-007, Q15) |
| Séquestre | `paiements/models.py` | `executer_decaissement` libère **tout le solde** (`montant_libere += montant_brut`, statut `libere`) et passe la campagne `approvisionnement`. La distribution vient **après** |

## 2. Le sujet qui porte la fonctionnalité

- **Modèles** : le statut et la date de la part vont dans `commandes/` (propriétaire de `Participation`) ; les dates de relance vont dans `catalogue/` (propriétaire de `Campagne`, voir §3) ; les genres de notification dans `echanges/`.
- **Services** : `paiements/services.py`, section « Les tâches d'échéance », à côté de `cloturer_les_echus`, `rembourser_les_indecis` et `valider_retrait`. Raison : la fin de la distribution partage `_verrouiller`, `_crediter_reputation` et la transition `distribution → terminee` avec `valider_retrait`, qui doit changer dans le même passage (§4.4). Les mettre ailleurs obligerait un autre module à importer des fonctions privées de `paiements/services.py`. Estimation : une centaine de lignes. Si l'implémentation dépasse nettement ce volume, `fonctionnalite` peut les sortir dans `paiements/retraits.py` sans changer les signatures.
- **Commande** : la tâche horaire existante (recommandation, question 4).
- **Aucune nouvelle route, aucune nouvelle application, aucun nouveau dossier.** Pas de limitation de débit à ajouter : rien n'entre par l'API.

## 3. Modèle de données (à valider : question 6)

### 3.1 `commandes/models.py` — `Participation`
- Nouveau statut : `REPUTEE_LIVREE = "reputee_livree", "Réputée livrée"` (libellé affiché : question 7). 14 caractères, tient dans `max_length=25`.
- **`STATUTS_PAYES` devient `(PAYEE, PRETE, RETIREE, REPUTEE_LIVREE)`.** Indispensable : l'argent de cette part a bien été payé, puis versé au groupeur. Sans cet ajout, au passage J+14, la jauge, `quantite_reservee`, `montant_collecte`, `nombre_participants` et le tableau de bord groupeur **baisseraient**, et la campagne cesserait d'être « figée » (`espaces/groupeur.py` l. 95). Effet de bord vérifié : `rembourser` accepterait une part réputée livrée, mais son seul appelant (`annuler`) ne filtre que `payee`, et `annuler` refuse une campagne `terminee`.
- Nouveau champ : `reputee_livree_le = DateTimeField("réputée livrée le", null=True, blank=True)`. `retiree_le` n'est **pas** réutilisé : il veut dire « remise prouvée par le code », et c'est précisément ce qui manque ici.
- Contrainte en base :
  ```python
  models.CheckConstraint(
      condition=~models.Q(statut="reputee_livree") | models.Q(reputee_livree_le__isnull=False),
      name="participation_reputee_livree_datee",
  )
  ```
  À sens unique, exprès : si la question 2 retient le retrait tardif, une part `reputee_livree` qui devient `retiree` garde sa date comme trace.
- Constantes nommées (plus de 14 en dur) : `DELAI_PREMIERE_RELANCE_JOURS = 3`, `DELAI_SECONDE_RELANCE_JOURS = 7`, `DELAI_RETRAIT_JOURS = 14`, et `PREAVIS_AVANT_LIVRAISON_REPUTEE_HEURES = 72` si la question 3 retient le préavis. **Hypothèse** : constantes du code, pas variables d'environnement. Le cahier des charges fixe ces délais ; `DELAI_DECISION_JOURS` est réglable parce qu'il est désactivable, ce qui n'a pas de sens ici. `delai_retrait_depasse` se réécrit sur `DELAI_RETRAIT_JOURS`.
- Index : aucun. La tâche lit `participations` par `(campagne, statut)`, index déjà présent.

### 3.2 `catalogue/models.py` — `Campagne`
- `relance_retrait_j3_le = DateTimeField(null=True, blank=True)` et `relance_retrait_j7_le = DateTimeField(null=True, blank=True)`.
- **Pourquoi sur la campagne et non sur la part** : `mise_a_disposition_le` est une date de campagne, et toutes les parts passent `prete` au même instant (`mettre_a_disposition` n'est accepté qu'une fois, la campagne quittant les statuts d'entrée). L'étape de relance est donc la même pour toutes les parts d'une campagne. Une colonne par campagne, posée sous le verrou de la campagne, rend la relance idempotente avec une ligne écrite au lieu de N. Alternatives écartées : deux dates par part (N écritures, même information) ; chercher une `Notification` existante (le modèle n'a pas de clé vers la part, il faudrait filtrer sur le texte du `lien` : fragile).
- Index : aucun. La tâche filtre `statut="distribution"` et `mise_a_disposition_le <= …` ; l'index `(statut, date_limite)` sert le préfixe `statut`, et les campagnes en distribution sont peu nombreuses.

### 3.3 `echanges/models.py` — `Notification.Genre` (à valider : question 5)
- `LIVRAISON_REPUTEE = "livraison_reputee", "Livraison réputée acquise"` (acheteur, J+14).
- `CAMPAGNE_TERMINEE = "campagne_terminee", "Campagne terminée"` (groupeur, J+14). Longueurs 17 et 17, dans `max_length=30`.

### 3.4 Migrations et effet sur une base remplie
| Migration | Contenu | SQL sur PostgreSQL | Données existantes |
|---|---|---|---|
| `catalogue/0007_relances_de_retrait` | 2 `AddField` nullables | `ALTER TABLE … ADD COLUMN … NULL` : instantané, sans réécriture | toutes les campagnes à `NULL` (aucune relance envoyée, ce qui est vrai) |
| `commandes/0004_participation_reputee_livree` | `AlterField statut` (choix), `AddField reputee_livree_le`, `AddConstraint` | choix : aucun SQL ; colonne nullable ; la contrainte est vérifiée sur les lignes existantes | aucune part n'est `reputee_livree` : la contrainte passe sur toute base existante |
| `echanges/0005_alter_notification_genre` | `AlterField genre` (choix) | aucun SQL | aucun |

Aucune migration de données. Les trois migrations sont additives, réversibles (`migrate <app> <précédente>`) tant qu'aucune part n'est passée `reputee_livree`. Elles s'appliquent au déploiement (`backend/entrypoint.sh` l. 26, `migrate --noinput`).

**Effet métier au premier passage après déploiement** : les campagnes déjà en `distribution` depuis plus de 14 jours (en production, à compter avec `--a-blanc`, voir §10) seraient closes à la première heure **sans qu'aucun acheteur ait reçu de relance**. C'est l'objet de la question 3.

## 4. Services (`paiements/services.py`)

Toutes les écritures sous `@transaction.atomic`, la campagne relue par `_verrouiller` (`select_for_update`, [[2026-10-27-decisions-f016]]). Exception métier : `ErreurPaiement` (déjà convertie en 400 par les vues). L'heure est lue une fois par appel (`maintenant = timezone.now()`). Âge d'une distribution = `maintenant - campagne.mise_a_disposition_le`, en **durée écoulée** (J+3 = 72 h), comme `_delai_de_decision_expire`. Lomé est en UTC+0 : durée écoulée et jour civil coïncident à l'heure près.

### 4.1 Signatures
```python
def relancer_les_retraits() -> list[tuple[int, str]]:
    """Tâche : (campagne, "j3" | "j7") pour chaque relance envoyée."""

@transaction.atomic
def relancer_retrait(campagne: Campagne) -> str | None:
    """Envoie au plus UNE relance (la plus avancée qui est due). None si rien à faire."""

def reputer_livrees_les_echues() -> list[int]:
    """Tâche : identifiants des campagnes closes à J+14."""

@transaction.atomic
def reputer_livree(campagne: Campagne) -> int:
    """Passe les parts `prete` en `reputee_livree`, termine la campagne. Rend le nombre de parts."""

def _terminer(campagne: Campagne) -> None:
    """distribution → terminee et crédit de réputation. Campagne déjà verrouillée."""
```

### 4.2 `relancer_retrait(campagne)`
1. `campagne = _verrouiller(campagne)` ; si `statut != distribution` ou `mise_a_disposition_le is None` → `None`.
2. Âge ≥ 14 jours → `None` : c'est `reputer_livree` qui joue (et, si la question 3 retient le préavis, c'est lui qui déclenche la relance de rattrapage, voir 4.3).
3. Âge ≥ 7 jours et `relance_retrait_j7_le is None` → étape `j7`.
4. Sinon âge ≥ 3 jours, `relance_retrait_j3_le is None` **et** `relance_retrait_j7_le is None` → étape `j3`.
5. Sinon → `None`.
6. Destinataires : parts `prete` seulement (`select_related("acheteur")`). Une notification par part (`bulk_create`), genre `relance_retrait`, lien `/mes-achats/<id>`. La date de l'étape est posée **même s'il n'y a aucune part `prete`** : l'étape est jouée.

**Idempotence** : deux passages le même jour lisent la date posée sous verrou, et le second ne fait rien. **Rattrapage** : une seule relance par passage et par campagne, la plus avancée. Une tâche arrêtée de J+2 à J+8 envoie la relance J+7 et jamais la J+3, qui arriverait en retard et contredirait la date d'échéance annoncée par la J+7.

### 4.3 `reputer_livree(campagne)`
1. `campagne = _verrouiller(campagne)`.
2. `statut != distribution` → `ErreurPaiement("Cette campagne n'est pas en distribution.")`.
3. Âge < 14 jours → `ErreurPaiement("Le délai de retrait de 14 jours n'est pas écoulé.")`.
4. **(à valider, question 1)** `sequestre_de(campagne).solde > 0` → `ErreurPaiement("Des fonds sont encore consignés : la campagne attend l'administrateur.")`, journalisé en `warning`.
5. **(à valider, question 3, option b)** si aucune relance n'a été envoyée depuis au moins `PREAVIS_AVANT_LIVRAISON_REPUTEE_HEURES` : envoyer la relance de rattrapage (même texte que J+7, date posée dans `relance_retrait_j7_le`), puis s'arrêter. Rien d'autre n'est écrit. Retour `0`.
6. Parts : `campagne.participations.select_for_update().filter(statut=prete)` → `statut = reputee_livree`, `reputee_livree_le = maintenant` (un `update()` suffit, la contrainte est satisfaite).
7. Une notification `livraison_reputee` par part (lien `/mes-achats/<id>`).
8. `_terminer(campagne)` ; notification `campagne_terminee` au groupeur (lien `/groupeur/campagnes/<id>`).
9. `logger.info` : identifiant de campagne et nombre de parts. Aucun nom, aucun numéro, aucun code dans le journal.

`reputer_livrees_les_echues()` sélectionne `statut=distribution, mise_a_disposition_le__lte=maintenant - 14 j`, appelle `reputer_livree` pour chacune dans son propre bloc et attrape `ErreurPaiement` (`continue`, journalisé). Une campagne en échec ne bloque donc pas les autres, et une campagne terminée entre la sélection et le verrou (dernier code validé à cet instant) est sautée.

### 4.4 Changements dans l'existant
- **`valider_retrait`** : relit la campagne par `_verrouiller` et la part par `select_for_update`, et exige `statut == distribution` (sauf retrait tardif, question 2). Sans ce verrou, un groupeur qui valide le dernier code pendant que la tâche passe à J+14 ferait terminer la campagne **deux fois**, donc `campagnes_terminees += 2`, et la part pourrait finir `retiree` dans une campagne déjà comptée sans elle. La fin de campagne passe par `_terminer`.
- **`_terminer(campagne)`** : ne fait rien si la campagne est déjà `terminee` (garde contre le double crédit), sinon statut `terminee` puis `_crediter_reputation`. Seul chemin vers `terminee` après la distribution.
- `_crediter_reputation` est **inchangé** : il compte déjà les seules parts `retiree`, ce qui applique Q13 tel quel.
- **Retrait tardif** (question 2, option b recommandée) : dans `valider_retrait`, une part `reputee_livree` d'une campagne `terminee` peut encore être remise. Elle passe `retiree` (avec `retiree_le` et `remise_par`, `reputee_livree_le` conservée), puis `participants_servis += 1`. `campagnes_terminees` ne bouge pas. Fonction privée `_crediter_retrait_tardif(campagne)`.

### 4.5 Notifications émises
Textes en français, liens déjà servis par la boutique (vérifiés par `test_notifications_liens.py`). `<échéance>` = `mise_a_disposition_le + 14 j`, au format `%d/%m/%Y`.

| Moment | Destinataire | Genre | Titre | Message | Lien |
|---|---|---|---|---|---|
| J+3 | acheteur, part `prete` | `relance_retrait` (existant) | « Votre colis vous attend » | « « {titre} » vous attend à {point_remise}. Présentez votre code {code} avant le {échéance}. » | `/mes-achats/<id>` |
| J+7 (ou rattrapage) | idem | `relance_retrait` | « Dernier rappel : colis à retirer » | « « {titre} » vous attend toujours à {point_remise}. Sans retrait avant le {échéance}, la remise sera réputée faite et la campagne close. Votre code : {code}. » | `/mes-achats/<id>` |
| J+14 | acheteur, part passée `reputee_livree` | `livraison_reputee` (nouveau, Q5) | « Délai de retrait écoulé » | « Vous n'avez pas retiré votre part de « {titre} » dans les 14 jours : la remise est réputée faite et la campagne est close. Pour toute question, écrivez au groupeur sous la campagne. » ; avec la question 2 (b), ajouter : « Si le groupeur a encore votre colis, votre code reste valable. » | `/mes-achats/<id>` |
| J+14 | groupeur | `campagne_terminee` (nouveau, Q5) | « Campagne terminée » | « « {titre} » est close. {n} colis non retiré(s) en 14 jours sont réputés livrés ; {r} participant(s) servi(s) comptent dans votre réputation. » | `/groupeur/campagnes/<id>` |

Le code de retrait figure déjà dans les messages existants (`paiement_enregistre`, `marchandise_disponible`), et une notification n'est lue que par son destinataire. Le reprendre ici ne change rien à l'exposition. **Hypothèse** : pas de relance au groupeur à J+3 / J+7, le cahier des charges n'en prévoit pas (§4, §8).

## 5. L'argent

**Ce que dit le cahier des charges.** §4 « Séquestre » : « les fonds d'une campagne restent consignés jusqu'à sa clôture ». §3 administrateur : « Libère le montant total… Clôture le dossier dès que le code de retrait est validé ». §4 « Colis non récupéré » : « la livraison est réputée acquise et le dossier se clôt ». Il ne dit rien de l'argent d'une part réputée livrée.

**Ce qui a été décidé.** Q4 ([[2026-10-26-decisions-carte]]) : **les fonds sont libérés avant la distribution** (code actuel). `executer_decaissement` verse tout le solde et passe la campagne `approvisionnement` ; la distribution ne commence qu'ensuite.

**Conséquence, à confirmer (question 1)** : dans le cas normal, une part réputée livrée **ne bouge aucun argent**. Son montant est déjà dans `montant_libere`, le séquestre est `libere` avec un solde de 0, et il n'y a rien à libérer ni à rembourser. F-031 n'écrit donc **aucune** `Transaction` et ne touche pas `Sequestre`. Les contraintes `sequestre_ne_libere_pas_plus_que_consigne` et `…_rembourse_…` ne sont pas concernées.

**Le cas qui touche l'argent : une campagne en distribution dont le séquestre n'est pas libéré.** Il existe aujourd'hui, parce que `mettre_a_disposition` accepte `financee` (C-014, corrigé par T10). Une telle campagne terminée à J+14 resterait avec son argent consigné, sans plus aucun chemin pour le verser (`demander_decaissement` exige `financee`). Recommandation : la garde du §4.3 point 4 (ne pas terminer, journaliser, laisser l'administrateur trancher), **à valider**.

## 6. La réputation

- **Où elle se calcule** : `comptes.models.Reputation` stocke les compteurs. `paiements/services.py::_crediter_reputation` les incrémente à la fin d'une campagne ; `recalculer_reputation` calcule la note (moyenne des avis) à chaque avis écrit, modifié ou supprimé (`commandes/vues.py`, `AvisVueEnsemble._recalculer`). Affichage : `GroupeurPublicSerialiseur` (fiche campagne), tableau de bord groupeur (`espaces/groupeur.py` l. 409).
- **Ce qui est crédité à J+14** (Q13) : `campagnes_terminees += 1` ; `participants_servis +=` nombre de parts `retiree` seulement. Les parts `reputee_livree` **ne comptent pas** : aucune remise n'est prouvée. La note ne bouge pas, elle ne vient que des avis (§4).
- **Cas limite** : si personne n'est venu, la campagne compte quand même comme « menée à terme », avec 0 participant servi. C'est la lecture littérale de Q13 ; les deux compteurs côte à côte laissent l'acheteur en juger. Pas de nouveau compteur « colis non retirés » (**hypothèse** : non demandé par Q13 ; l'ajouter serait une migration de plus sur `comptes`).
- **L'avis reste ouvert** : `peut_etre_notee` est vrai pour une part `reputee_livree` (statut payé, campagne `terminee`). L'acheteur qui n'a rien reçu peut noter le groupeur, ce qui est le recours prévu par §2 (« elle n'arbitre pas »). À garder tel quel, et à tester.
- Sans lien avec F-031 : C-035 (les annulations par la tâche des 7 jours pèsent sur la réputation) reste ouvert.

## 7. API et interfaces

### API (aucune route nouvelle, champs ajoutés : contrat à valider, question 5)
- `ParticipationSerialiseur` (`GET /api/participations/`, `/api/participations/<id>/`) : `statut` peut valoir `reputee_livree`, `statut_libelle` suit ; ajout de `reputee_livree_le`.
- `ParticipantSerialiseur` (`GET /api/groupeur/campagnes/<id>/participants/`) : même ajout.
- Campagne (`CampagneResumeSerialiseur` / détail) : ajout facultatif de `fin_du_retrait_le` (= `mise_a_disposition_le + 14 j`, ou `null`), calculé par le serveur, pour que l'écran affiche « à retirer avant le … » sans recopier la règle des 14 jours en TypeScript. Les dates de relance ne sont **pas** exposées : elles ne servent qu'à la tâche.
- Notifications : deux nouvelles valeurs de `genre` (`genre` est typé `string` côté client, donc pas de rupture).
- `POST /api/groupeur/campagnes/<id>/retrait/` : nouveaux messages 400 (« La distribution de cette campagne est close. », ou retrait tardif accepté, selon la question 2).

### `frontend/commun/src/api/types.ts`
- `StatutParticipation` : ajouter `| "reputee_livree"`. Le `Record<StatutParticipation, …>` de `MesAchats.tsx` (`TONS`) refusera de compiler tant qu'il manque : c'est le garde-fou voulu.
- `Participation` et `Participant` : `reputee_livree_le: string | null`.
- `CampagneResume` (si retenu) : `fin_du_retrait_le: string | null`.

### Boutique
- `pages/MesAchats.tsx` : `TONS.reputee_livree = "neutre"`. Dans le détail, un encadré : « Délai de retrait écoulé le {date} : la remise est réputée faite. » ; avec la question 2 (b), ajouter « Si le groupeur a encore votre colis, présentez ce code », et garder le QR visible (`retirable` vaut alors `prete || reputee_livree`). Pour une part `prete`, afficher « À retirer avant le {fin_du_retrait_le} ». Les formats passent par `@commun/outils/formats` (`dateLongue`).
- `pages/groupeur/CampagneGroupeur.tsx` : la liste nominative distingue trois états (remis : coche verte ; prêt : badge actuel ; **réputé livré** : icône distincte, par exemple `Clock` ou `PackageX` de `lucide-react`, avec le libellé). Le compteur « {retires} / {payes} colis remis » ne compte que `retiree` (inchangé) ; ajouter « dont {n} réputé(s) livré(s) » quand `n > 0`.
- `pages/Notifications.tsx` et `composants/Cloche.tsx` : icônes pour `livraison_reputee` et `campagne_terminee` (sinon `Bell` par défaut, sans casse).
- À vérifier à 390 px.

### Console d'administration
Aucun écran n'affiche le statut d'une participation (`grep` dans `frontend/admin/src` : rien), et le dépôt n'a pas de `admin.py` Django. Le tableau de bord admin compte les campagnes `terminee` (`espaces/administration.py` l. 237) : il les comptera sans changement. Rien à modifier.

## 8. Commande planifiée (à valider : question 4)

**Recommandation** : étendre `cloturer_les_campagnes_echues`. Elle est déjà la tâche horaire unique (`COOLIFY.md` §4, Q15). Une seconde commande obligerait l'utilisateur à créer et surveiller une seconde tâche planifiée, alors que la première n'est même pas encore vérifiée (C-007). Le nom de la commande devient un peu étroit, mais le renommer casserait la planification existante : on garde le nom, et la docstring dit ce qu'elle fait désormais.

- `handle()` : `cloturer_les_echus()` → `rembourser_les_indecis()` → `relancer_les_retraits()` → `reputer_livrees_les_echues()`. Une ligne par action, puis le bilan : « N clôture(s), N remboursement(s), N relance(s), N campagne(s) close(s) à J+14. »
- `--a-blanc` : annonce aussi les campagnes à relancer (avec l'étape `j3` / `j7`), celles à clore à J+14 (avec le nombre de parts non retirées) et celles bloquées par la garde du séquestre. Rien n'est écrit. C'est ce mode que l'utilisateur lance en production avant d'activer (voir §10).
- **Idempotence** : chaque étape relit l'état sous verrou ; deux passages le même jour n'envoient pas deux relances et ne créditent pas deux fois.
- **Fréquence** : toutes les heures (`0 * * * *`). Une relance part donc au plus une heure après J+3 ou J+7, à l'heure de la journée où la marchandise a été annoncée (notification seule, pas de SMS : l'heure n'importe pas).
- **Après une panne de quelques heures** : tout part au passage suivant, avec le retard de la panne. Rien n'est perdu ni doublé.
- **Après une panne de plusieurs jours** : une seule relance par campagne et par passage (la plus avancée, §4.2). Passé J+14 : option (a) de la question 3, clôture immédiate ; option (b), relance de rattrapage puis clôture au plus tôt 72 h plus tard.
- **Deux exécutions simultanées** (Coolify qui chevauche, ou lancement à la main pendant la tâche) : les verrous `_verrouiller` les sérialisent ; la seconde voit l'état écrit par la première. Le verrou n'est réel que sous PostgreSQL (sqlite l'ignore, C-031).

## 9. Ordre de création

0. **Préalable recommandé : T10** (F-024, C-014), qui garantit qu'une campagne en distribution a son séquestre libéré. Sans T10, la garde du §4.3 point 4 est indispensable (question 8).
1. Modèles et trois migrations (§3) ; `STATUTS_PAYES` ; constantes. `makemigrations --check` vert, suite `commandes` et `catalogue` verte.
2. `_terminer`, puis verrou et garde de statut dans `valider_retrait` (tests existants de `TestDistributionEtRetrait` verts sans modification).
3. `relancer_retrait` / `relancer_les_retraits` et leurs tests.
4. `reputer_livree` / `reputer_livrees_les_echues` et leurs tests ; retrait tardif selon la question 2.
5. Commande (`handle`, `--a-blanc`) et ses tests.
6. Sérialiseurs (champs) et tests d'API ; `test_notifications_liens.py` complété.
7. Front : `types.ts`, `MesAchats.tsx`, `CampagneGroupeur.tsx`, icônes ; `npm run verifier`.
8. `charger_demo` et `VERSION_DEMO` (§11).
9. `COOLIFY.md` §4 : ajouter à la liste « Sans elle » la phrase « un colis non retiré bloque la campagne en distribution pour toujours ».

## 10. Tests à écrire

Fichier transversal neuf : `backend/groupachat/tests/test_retraits_echus.py` (il touche catalogue, commandes, paiements, echanges, comptes), avec `pytestmark = pytest.mark.django_db`. Vérifier sa collecte (`python -m pytest --collect-only -q groupachat/tests/test_retraits_echus.py`). Fixture : campagne en distribution par le vrai parcours (participer, payer, clôturer, demander le retrait, exécuter, mettre à disposition), comme `TestDistributionEtRetrait.campagne_a_distribuer` de `commandes/tests.py`. Puis `Campagne.objects.filter(pk=…).update(mise_a_disposition_le=timezone.now() - timedelta(...))`. « Pile » = `timedelta(days=N)` exactement (l'heure lue par le service est postérieure, la condition `>=` est vraie) ; « la veille » = `timedelta(days=N) - timedelta(minutes=1)`.

### Relances (`TestRelances`)
1. `test_rien_n_est_envoye_avant_le_troisieme_jour` (3 j − 1 min) : aucune `relance_retrait`, date J+3 nulle.
2. `test_la_premiere_relance_part_pile_a_j_plus_3` : une notification par part `prete`, genre, lien `/mes-achats/<id>`, code et point de remise dans le message ; `relance_retrait_j3_le` posée.
3. `test_une_part_retiree_rembourses_ou_en_attente_n_est_pas_relancee`.
4. `test_deux_passages_le_meme_jour_n_envoient_qu_une_relance` (idempotence).
5. `test_rien_de_plus_la_veille_du_septieme_jour` (7 j − 1 min, après J+3 envoyée).
6. `test_la_seconde_relance_part_pile_a_j_plus_7`.
7. `test_apres_une_panne_seule_la_relance_la_plus_avancee_part` (première exécution à J+8 : une seule relance, la J+7 ; aucune J+3 ; rien de plus à J+9).
8. `test_une_campagne_terminee_annulee_ou_en_approvisionnement_n_est_pas_relancee`.
9. `test_pas_de_relance_ordinaire_au_dela_de_j_plus_14` (c'est la clôture qui joue).

### Livraison réputée (`TestLivraisonReputee`)
10. `test_rien_ne_bouge_la_veille_du_quatorzieme_jour` (14 j − 1 min) : parts `prete`, campagne `distribution`, réputation inchangée.
11. `test_a_j_plus_14_pile_les_parts_non_retirees_sont_reputees_livrees` : statut, `reputee_livree_le` posée ; parts `retiree` intactes (`retiree_le`, `remise_par` inchangés).
12. `test_la_campagne_passe_terminee`.
13. `test_la_reputation_compte_la_campagne_mais_pas_les_parts_non_retirees` : `campagnes_terminees == 1`, `participants_servis ==` nombre de retirées, `note` et `avis_recus` inchangés.
14. `test_personne_n_est_venu_la_campagne_se_termine_sans_participant_servi`.
15. `test_un_second_passage_ne_credite_pas_deux_fois` (idempotence : compteurs, notifications et statuts identiques).
16. `test_une_campagne_deja_terminee_n_est_pas_touchee` (tous retirés avant J+14 : réputation non recréditée).
17. `test_une_part_annulee_ou_remboursee_reste_telle_quelle`.
18. `test_la_jauge_et_le_montant_collecte_ne_baissent_pas` (`quantite_reservee`, `montant_collecte`, `nombre_participants` identiques avant et après).
19. `test_le_sequestre_n_est_pas_touche` (consigné, libéré, remboursé, statut identiques ; aucune `Transaction` créée).
20. `test_l_acheteur_et_le_groupeur_sont_prevenus` (genres, destinataires, liens `/mes-achats/<id>` et `/groupeur/campagnes/<id>`).
21. Selon la question 1 : `test_une_campagne_dont_les_fonds_sont_encore_consignes_n_est_pas_close` (campagne passée `financee → distribution` sans décaissement : reste `distribution`, rien écrit).
22. Selon la question 3 (b) : `test_sans_relance_prealable_la_cloture_attend_le_preavis` (mise à disposition il y a 20 jours, aucune relance : 1er passage, relance seulement ; 72 h − 1 min plus tard, rien ; 72 h pile, réputée livrée).
23. `test_une_part_reputee_livree_peut_noter_le_groupeur` (`peut_etre_notee` vrai, `POST /api/avis/` 201).
24. `test_la_contrainte_refuse_une_part_reputee_livree_sans_date` (`IntegrityError`).

### Retrait et clôture (`TestRetraitApresEcheance`)
25. `test_le_dernier_code_et_la_tache_ne_terminent_la_campagne_qu_une_fois` (valider le dernier code, puis passer la tâche, et l'inverse : `campagnes_terminees == 1`).
26. Selon la question 2 : `test_un_code_presente_apres_j_plus_14_…` : (a) 400 « La distribution de cette campagne est close. », rien écrit ; ou (b) 200, part `retiree`, `reputee_livree_le` conservée, `participants_servis + 1`, `campagnes_terminees` inchangé, campagne toujours `terminee`.
27. `test_un_code_deja_retire_reste_refuse_apres_la_cloture`.

### API et commande (`TestApi`, `TestCommandePlanifiee`)
28. `test_l_acheteur_voit_sa_part_reputee_livree` (`statut`, `statut_libelle`, `reputee_livree_le` ; d'un autre acheteur : 404).
29. `test_le_groupeur_voit_les_parts_reputees_livrees_dans_sa_liste` ; un autre groupeur : 404.
30. `test_le_tableau_de_bord_groupeur_compte_la_campagne_terminee_sans_baisser_la_collecte`.
31. `test_la_commande_enchaine_cloture_remboursement_relances_et_j_plus_14` (sortie lisible, bilan).
32. `test_le_mode_a_blanc_annonce_sans_rien_changer` (relances et clôtures annoncées ; aucune notification, aucun statut changé).

### À compléter ailleurs
- `groupachat/tests/test_notifications_liens.py::test_chaque_lien_de_notification_correspond_a_une_route_de_la_boutique` : ajouter au parcours une campagne relancée puis close à J+14, et `relance_retrait`, `livraison_reputee`, `campagne_terminee` à l'ensemble attendu. L'ensemble s'élargit, aucune assertion n'est retirée.
- `commandes/tests.py::TestDistributionEtRetrait` : inchangé, doit rester vert (garde de non-régression de `valider_retrait`).

## 11. Jeu de démonstration

**Oui.** Sans cet état, la recette web et la démonstration ne montrent ni l'étiquette « réputée livrée », ni la cloche « Votre colis vous attend ». Dans `charger_demo.py` :
- `_campagne_reputee_livree` : une campagne menée par le vrai parcours jusqu'à `mettre_a_disposition`, deux codes validés, puis `mise_a_disposition_le` reculée de 15 jours et appel de `reputer_livree`, **par le service et non par écriture directe**. Si la question 3 (b) est retenue, reculer aussi `relance_retrait_j7_le` de 8 jours pour respecter le préavis.
- `_campagne_en_distribution` existante : reculer `mise_a_disposition_le` de 4 jours et appeler `relancer_retrait`, pour qu'un acheteur de démonstration ait une relance dans sa cloche.
- Ajouter éventuellement `REPUTEE_LIVREE` aux statuts de `_avis` (un avis « jamais pu passer au point de retrait », avec réponse du groupeur).
- **`VERSION_DEMO` : "6" → "7".** Sans effet en production si `CHARGER_DEMO=0` (D10 de [[2026-10-27-decisions-f011]]).

## 12. Lancement planifié en production (Q15, C-007) — ce qu'il faut à l'utilisateur

Rien de ceci n'est fait par un agent.
1. **Vérifier la tâche planifiée sur Coolify** (C-007) : ressource `api` → *Scheduled Tasks* → commande `python manage.py cloturer_les_campagnes_echues`, horaire `0 * * * *`. Si la question 4 retient une seconde commande, en créer une seconde, même horaire.
2. **Avant d'avancer `master`**, sur achatgr.com, depuis le terminal Coolify du conteneur `api` et **après** le déploiement des migrations : `python manage.py cloturer_les_campagnes_echues --a-blanc`. Lire combien de campagnes seraient relancées et closes à J+14, et lesquelles sont bloquées par des fonds consignés. Ce sont ces chiffres qui tranchent en pratique la question 3.
3. **Repérer les campagnes en distribution dont le séquestre n'est pas libéré** (C-014) : le mode `--a-blanc` les liste (§8). Leur sort relève de l'administrateur (question 1).
4. Les migrations s'appliquent seules au démarrage (`entrypoint.sh`). Elles sont additives : un retour à la version précédente reste possible tant que la tâche n'a pas encore passé une part `reputee_livree`.
5. Aucune variable d'environnement nouvelle, donc rien à ajouter à `.env.exemple` ni sur Coolify.

## 13. Fichiers que l'implémentation touchera
Backend : `backend/groupachat/commandes/models.py`, `commandes/serialiseurs.py`, `commandes/migrations/0004_*.py` (nouveau) ; `catalogue/models.py`, `catalogue/serialiseurs.py` (si `fin_du_retrait_le`), `catalogue/migrations/0007_*.py` (nouveau), `catalogue/management/commands/cloturer_les_campagnes_echues.py`, `catalogue/management/commands/charger_demo.py` ; `echanges/models.py`, `echanges/migrations/0005_*.py` (nouveau) ; `paiements/services.py` ; tests : `groupachat/tests/test_retraits_echus.py` (nouveau), `groupachat/tests/test_notifications_liens.py`.
Frontend : `frontend/commun/src/api/types.ts`, `frontend/boutique/src/pages/MesAchats.tsx`, `frontend/boutique/src/pages/groupeur/CampagneGroupeur.tsx`, `frontend/boutique/src/pages/Notifications.tsx`, `frontend/boutique/src/composants/Cloche.tsx`.
Documentation : `COOLIFY.md` §4. Note de décision dans `mapper/02-decisions/` une fois les questions tranchées (par la passe qui met `mapper/` à jour).

## Questions ouvertes

Tranchées le 2026-10-27 : voir « Décisions » en tête de fiche et [[2026-10-27-decisions-f031]].

1. **Argent d'une part réputée livrée, et campagne en distribution aux fonds encore consignés.** Le cahier des charges ne tranche pas (§4 « consignés jusqu'à la clôture » contre Q4 « libérés avant la distribution »). Dans le cas normal, les fonds sont déjà versés : F-031 ne bouge aucun argent. Reste le cas C-014 (distribution sans décaissement).
   (a) La tâche ne clôt pas une campagne dont le solde du séquestre est positif : elle la laisse en `distribution`, la journalise et la signale dans `--a-blanc`, et l'administrateur tranche.
   (b) Elle la clôt quand même, et l'argent reste consigné sans chemin de sortie.
   (c) Elle libère automatiquement le solde au groupeur à J+14 (décaissement créé par la tâche).
   **Recommandation : (a)**, et confirmer qu'une part réputée livrée n'entraîne aucun mouvement dans le cas normal. (c) ferait verser de l'argent par une tâche sans regard humain, ce que le dépôt n'a jamais fait.
2. **Un acheteur qui se présente après J+14 avec son code.**
   (a) Code refusé (400) : la remise se fait hors plateforme, sans preuve.
   (b) Code accepté : la part passe `retiree`, `participants_servis + 1`, la campagne reste `terminee` et compte une seule fois.
   (c) Code accepté sans toucher à la réputation.
   **Recommandation : (b)**. Le code vaut preuve de livraison (§4 « Retrait ») ; la refuser priverait les deux parties de la seule preuve possible, et (b) compte un participant réellement servi. Il en coûte une branche dans `valider_retrait` et un QR toujours affiché dans « Mes achats ».
3. **Livraison réputée sans relance préalable** (tâche arrêtée longtemps, ou premier passage après le déploiement sur des campagnes anciennes).
   (a) Strict : J+14 depuis la mise à disposition, relance ou non.
   (b) Préavis : jamais réputée livrée sans une relance envoyée au moins 72 h avant. En fonctionnement normal, cela ne change rien (la relance J+7 précède de 7 jours) ; en rattrapage, la tâche relance d'abord et clôt au plus tôt 72 h après.
   (c) Strict, mais seulement pour les campagnes mises à disposition après le déploiement ; les anciennes sont laissées à l'administrateur.
   **Recommandation : (b)**. Une règle qui retire un droit à l'acheteur ne doit pas s'appliquer sans qu'il ait été prévenu. Elle ajoute une condition et un test.
4. **Commande planifiée.**
   (a) Étendre `cloturer_les_campagnes_echues` : une seule tâche Coolify.
   (b) Nouvelle commande `relancer_les_retraits`, avec une seconde tâche Coolify.
   **Recommandation : (a)**. Rien de neuf à configurer en production, alors que la première tâche n'est même pas encore vérifiée (C-007).
5. **Contrat d'API et notifications.**
   (a) Deux nouveaux genres `livraison_reputee` (acheteur) et `campagne_terminee` (groupeur) ; champs `reputee_livree_le` (participation, participant) et `fin_du_retrait_le` (campagne).
   (b) Pas de nouveau genre : réutiliser `relance_retrait` pour J+14, et ne pas prévenir le groupeur ; pas de `fin_du_retrait_le`.
   **Recommandation : (a)**. Une relance qui annonce une clôture serait trompeuse, et le groupeur doit savoir que sa campagne est close. Les ajouts sont rétrocompatibles (`genre` est une chaîne côté client), mais `StatutParticipation` gagne une valeur.
6. **Migrations** (accord requis par T5) : trois migrations additives, sans migration de données (§3.4).
   (a) Dates de relance sur `Campagne`, statut et date sur `Participation`.
   (b) Dates de relance sur `Participation`.
   (c) Pas de colonne de relance : déduire l'idempotence des `Notification` existantes.
   **Recommandation : (a)** (§3.2). La contrainte `participation_reputee_livree_datee` est à valider en même temps.
7. **Libellé affiché du statut.**
   (a) « Réputée livrée ».
   (b) « Non retirée — réputée livrée ».
   (c) « Délai de retrait écoulé ».
   **Recommandation : (b)**. « Réputée livrée » seul est du jargon pour un acheteur qui n'a rien reçu ; (b) dit le fait et sa conséquence. Valeur technique inchangée : `reputee_livree`.
8. **Ordre avec T10.**
   (a) Implémenter F-031 après T10 (C-014 fermé : plus aucune nouvelle campagne en distribution sans décaissement).
   (b) Implémenter F-031 d'abord, avec la garde de la question 1 (a).
   **Recommandation : (a)** si l'ordre de la mission le permet. Sinon (b) : la garde suffit, et le test 21 la couvre.

## Recette

Rôle : système (tâche horaire), acheteur, groupeur, administrateur (lecture) · Couches : serveur oui · web boutique oui · console admin oui (non-régression seulement) · mobile non (aucune application dans ce dépôt) · Source : CDC §4 (« Colis non récupéré », « Réputation », « Séquestre »), §8, §9 ; Q4, Q13 ([[2026-10-26-decisions-carte]]) ; D1 à D8 ([[2026-10-27-decisions-f031]]) ; C-052 (ordre des verrous de `cloturer`). Base de la préparation : `7a31195` (T10 faite, code non commité, F-031 non codée).

### Données communes
- Groupeur validé G, acheteurs A1, A2, A3, A4. Campagne C de 10 pièces minimum à 18 000 FCFA l'unité : A1 paie 4 pièces, A2 3, A3 2, A4 1 ; consigné **180 000** ; point de remise « Boutique Abalo ».
- **C en distribution par le vrai parcours** (participer, payer, clôturer, demander le retrait, exécuter le décaissement, mettre à disposition), comme `TestDistributionEtRetrait.campagne_a_distribuer`. Séquestre lu par `Sequestre.objects.get(campagne=C)` (`montant_consigne`, `montant_libere`, `montant_rembourse`, `statut`) : après mise à disposition, **libéré 180 000, solde 0, statut `libere`**.
- Le temps se règle par `Campagne.objects.filter(pk=C).update(mise_a_disposition_le=timezone.now() - delta)`. « Pile » = `timedelta(days=N)` exactement ; « la veille » = `timedelta(days=N) - timedelta(minutes=1)`. « Passer la tâche » = `python manage.py cloturer_les_campagnes_echues` (ou les services `relancer_les_retraits()` puis `reputer_livrees_les_echues()`).
- `Reputation` de G relue avant et après (`campagnes_terminees`, `participants_servis`, `avis_recus`, `note`, `campagnes_annulees`). Cahier : `participants_servis` ne compte que les parts `retiree`.
- Messages, titres et liens : ceux du tableau § 4.5 de la conception. Le libellé affiché du statut est « Non retirée — réputée livrée » (D7), valeur technique `reputee_livree`.
- « Rien d'écrit » = nombres de `Notification`, `Transaction`, `Participation` par statut, séquestre et réputation identiques avant/après.

### Scénarios — Système (tâche horaire)

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | C en distribution depuis `3 j − 1 min`, 4 parts `prete` | la tâche passe | aucune notification `relance_retrait` ; `relance_retrait_j3_le` et `_j7_le` nulles ; bilan « 0 relance(s) » | serveur |
| R2 | C en distribution depuis `3 j` pile, A1 et A2 `prete`, A3 `retiree`, A4 `remboursee` (forcé) | la tâche passe | exactement **2** notifications `relance_retrait` (A1, A2), titre « Votre colis vous attend », lien `/mes-achats/<id de la part>`, message avec le titre de C, « Boutique Abalo », le code de retrait de **cette** part et la date limite `%d/%m/%Y` = mise à disposition + 14 j ; A3 et A4 : 0 ; `relance_retrait_j3_le` posée, `_j7_le` nulle ; statuts de C et des parts inchangés ; séquestre inchangé | serveur |
| R3 | R2 jouée | la tâche repasse deux fois de suite | aucune notification de plus ; `relance_retrait_j3_le` inchangée à la microseconde (idempotence) | serveur |
| R4 | R2 jouée, `7 j − 1 min` | la tâche passe | aucune nouvelle notification ; `_j7_le` nulle | serveur |
| R5 | R2 jouée, `7 j` pile | la tâche passe | **une** nouvelle notification par part `prete`, titre « Dernier rappel : colis à retirer », message contenant « réputée faite » et le code ; `_j7_le` posée ; `_j3_le` inchangée ; repasser : rien de plus | serveur |
| R6 | C à `3 j` pile, la tâche n'a pas tourné entre J+2 et J+8 : premier passage à `8 j`, aucune relance antérieure | la tâche passe, puis repasse à `9 j` | **une seule** relance par part (titre « Dernier rappel… »), `_j7_le` posée, `_j3_le` **nulle** ; à J+9 rien de plus | serveur |
| R7 | C en distribution depuis `3 j` mais aucune part `prete` (toutes `retiree` ou `remboursee`, forcé ; C reste `distribution` par construction du test) | la tâche passe | 0 notification ; `relance_retrait_j3_le` **posée** (étape jouée, qu'il n'y ait personne à relancer) ; repasser : rien | serveur |
| R8 | trois campagnes à `5 j` de mise à disposition : l'une `terminee`, l'une `annulee`, l'une `approvisionnement` (`mise_a_disposition_le` nulle ou périmée, forcé) | la tâche passe | 0 relance pour chacune ; leurs dates de relance nulles | serveur |
| R9 | C en distribution depuis `14 j` pile ou plus, avec une relance J+7 posée depuis longtemps, parts `prete` | `relancer_les_retraits()` seul | il ne renvoie pas de relance ordinaire (`None`) : c'est la clôture qui joue (R12) | serveur |
| R10 | C en distribution depuis `14 j − 1 min`, relances J+3 et J+7 posées, 3 parts `prete`, 1 `retiree`, `Reputation` de G relevée | la tâche passe | C reste `distribution` ; parts inchangées ; réputation inchangée ; aucune notification `livraison_reputee` ni `campagne_terminee` | serveur |
| R11 | C en distribution depuis `14 j` pile, J+3 et J+7 envoyées il y a plus de 72 h ; A1 `retiree`, A2 et A3 `prete`, A4 `remboursee` | la tâche passe | A2 et A3 : statut `reputee_livree`, `reputee_livree_le` non nulle ; A1 : `retiree`, `retiree_le` et `remise_par` **inchangés** ; A4 : `remboursee` inchangée ; C `terminee` ; `Reputation` de G : `campagnes_terminees` +1, `participants_servis` +1 (A1 seulement), `note` et `avis_recus` inchangés ; bilan « 1 campagne(s) close(s) à J+14 » | serveur |
| R12 | idem R11 | lecture des notifications | A2 et A3 : une notification `livraison_reputee` chacune, titre « Délai de retrait écoulé », lien `/mes-achats/<id>`, message avec « Si le groupeur a encore votre colis, votre code reste valable. » ; G : une `campagne_terminee`, titre « Campagne terminée », lien `/groupeur/campagnes/<id>`, message « 2 colis non retiré(s)… 1 participant(s) servi(s) » ; A1 et A4 : aucune nouvelle | serveur |
| R13 | idem R11 | comparaison avant/après | `quantite_reservee`, `montant_collecte`, `nombre_participants` de C **identiques** (STATUTS_PAYES contient `reputee_livree`) ; séquestre identique (consigné 180 000, libéré 180 000, remboursé 0, `libere`) ; **0 `Transaction` créée** ; `makemigrations --check` vert | serveur |
| R14 | idem R11 | la tâche repasse deux fois | compteurs de réputation, statuts, nombre de notifications, `reputee_livree_le` identiques (rien n'est crédité deux fois) | serveur |
| R15 | personne n'est venu : 4 parts `prete`, `14 j`, relances posées | la tâche passe | 4 parts `reputee_livree` ; C `terminee` ; `campagnes_terminees` +1 ; `participants_servis` **inchangé** (+0) ; message au groupeur « 4 colis non retiré(s)… 0 participant(s) servi(s) » | serveur |
| R16 | tous les codes validés avant J+14 (C `terminee` par `valider_retrait`, `campagnes_terminees` = 1), `mise_a_disposition_le` reculée de `20 j` | la tâche passe | C non sélectionnée ou sautée : réputation **inchangée** (reste 1), aucune notification, aucun changement de statut | serveur |
| R17 | **Préavis (D3), cas strict** : C en distribution depuis `20 j`, aucune relance jamais envoyée (premier passage après déploiement), 3 parts `prete` | passage 1 | une relance de rattrapage (titre « Dernier rappel… »), `_j7_le` posée à l'heure du passage ; **les parts restent `prete`**, C reste `distribution`, réputation inchangée, aucune notification `livraison_reputee` | serveur |
| R18 | R17 jouée à l'instant T | passage à `T + 72 h − 1 min` | rien : parts `prete`, C `distribution`, pas de seconde relance | serveur |
| R19 | idem | passage à `T + 72 h` pile | parts `reputee_livree`, C `terminee`, notifications `livraison_reputee` et `campagne_terminee`, réputation créditée une fois | serveur |
| R20 | **Préavis, J+3 seule** : relance J+3 envoyée il y a 15 j, J+7 jamais envoyée (panne), C à `20 j` | la tâche passe | comportement fixé par la **question 1** (recommandation : le préavis ne compte que la relance J+7 ou de rattrapage, la seule qui annonce la clôture ; donc relance de rattrapage, pas de clôture) | serveur |
| R21 | **D1 défensif** : C `distribution` à `20 j`, relances posées, séquestre au solde **positif** (état forcé : `montant_libere` ramené à 0 par le test ; la contrainte `sequestre_ne_libere_pas_plus_que_consigne` n'est pas violée) | la tâche passe | C reste `distribution` ; parts `prete` ; aucune notification J+14 ; réputation inchangée ; un `logger.warning` nommant l'identifiant de C et aucune donnée personnelle (ni nom, ni numéro, ni code) ; la tâche ne plante pas et traite les autres campagnes | serveur |
| R22 | deux campagnes échues à J+14, la première bloquée (R21), la seconde saine | la tâche passe | la seconde est close ; la première reste ; code de sortie 0 (une campagne en échec n'en bloque pas une autre) | serveur |
| R23 | **`--a-blanc`** : une campagne due pour J+3, une due pour J+7, une à clore (3 parts non retirées), une bloquée (R21) | `cloturer_les_campagnes_echues --a-blanc` | la sortie nomme chaque campagne avec son action : « relance j3 », « relance j7 », « clôture à J+14 (3 colis non retirés) », « bloquée : fonds consignés » ; **rien n'est écrit** (empreinte : comptes de `Notification`, statuts des campagnes et des parts, dates de relance, réputation, séquestres identiques) ; code 0 | serveur |
| R24 | R23 puis passage réel | la tâche passe sans `--a-blanc` | les mêmes campagnes sont traitées comme annoncé (même liste) | serveur |
| R25 | des collectes échues, des campagnes indécises, des retraits à relancer | la tâche passe | enchaîne `cloturer_les_echus`, `rembourser_les_indecis`, `relancer_les_retraits`, `reputer_livrees_les_echues`, une ligne par action puis « N clôture(s), N remboursement(s), N relance(s), N campagne(s) close(s) à J+14. » ; comportement des deux premières étapes inchangé (non-régression `tests/test_cloture.py`) | serveur |
| R26 | contrainte | une part forcée à `statut="reputee_livree"` avec `reputee_livree_le=None` | `IntegrityError` (`participation_reputee_livree_datee`) ; une part `retiree` avec `reputee_livree_le` renseignée est **permise** (trace du retrait tardif) | serveur |
| R27 | migrations `catalogue/0007`, `commandes/0004`, `echanges/0005` sur une base avec des campagnes et parts existantes | `migrate` | passent ; toutes les campagnes existantes ont les deux dates nulles ; aucune part `reputee_livree` ; retour arrière possible (`migrate catalogue 0006`) tant qu'aucune part n'a ce statut | serveur |

### Scénarios — Système (concurrence, PostgreSQL)

Procédé de F-024 (`TestCourses`) : `@pytest.mark.django_db(transaction=True)`, **ignoré si `connection.vendor != "postgresql"`** (motif écrit : SQLite ignore `select_for_update`), un bloc `transaction.atomic()` externe qui **tient le verrou**, un fil (`_lancer_en_fil`) qui lance l'autre opération, `fil.join(timeout=0.5)` puis `assert fil.is_alive()` (le second attend), sortie du bloc, `fil.join(timeout=10)`. Aucune course « au hasard ». Deux vraies connexions, pas de mock.

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R28 | C à `14 j`, relances posées, A1 `retiree`, A2 `prete` (dernier code à valider) | bloc externe : `valider_retrait` du code de A2 (campagne verrouillée, C passe `terminee`, réputation créditée) ; dans le fil : `reputer_livree` ; le fil attend (`is_alive`), puis le bloc se ferme | le fil lève `ErreurPaiement` (« pas en distribution ») ; `campagnes_terminees == 1` (pas 2) ; `participants_servis == 2` ; A2 `retiree`, pas `reputee_livree` ; une seule `campagne_terminee` | serveur (PostgreSQL) |
| R29 | idem | bloc externe : `reputer_livree` (A2 devient `reputee_livree`, C `terminee`) ; dans le fil : `valider_retrait` du code de A2, avec un objet `Campagne` **chargé avant** (périmé) ; le fil attend | après sortie du bloc : D2 appliqué — A2 `retiree`, `reputee_livree_le` **conservée**, `retiree_le` posée, `participants_servis` +1 (2 au total), `campagnes_terminees == 1` (inchangé), C reste `terminee` ; jamais 2 | serveur (PostgreSQL) |
| R30 | C `en_cours` à date limite échue, minimum atteint, 2 parts `payee`, séquestre `bloque`, `consigne` > 0 | bloc externe : `annuler(C)` jusqu'au bout sans commit (campagne, puis décaissement, puis séquestre verrouillés, remboursements) ; fil : `cloturer(C)` ; le fil attend ; sortie du bloc | `annuler` passe : C `annulee`, séquestre `rembourse` ; `cloturer` rend ensuite le statut `annulee` sans rien écrire (relu sous verrou) : C n'est **pas** repassée `financee`, séquestre non remis à `bloque`, **aucune notification « Campagne financée »**, `cloturee_le` inchangée ; aucun fil en `OperationalError` | serveur (PostgreSQL) |
| R31 | **Interblocage C-052** : mêmes données que R30 | bloc externe : verrouille la campagne (`select_for_update`), puis le fil lance `cloturer(C)`, `fil.join(0.5)`, puis le bloc externe verrouille le **séquestre** (`_verrouiller_sequestre`) | avec le correctif, `cloturer` verrouille la campagne **en tête** : le fil attend sur la campagne sans avoir pris le séquestre, le bloc externe prend le séquestre sans attente, aucune erreur ; sortie, le fil se termine. **Sans le correctif (ordre séquestre puis campagne), le fil tient le séquestre pendant que le bloc le réclame : PostgreSQL détecte l'interblocage (`OperationalError`/`deadlock detected`) → le test échoue, c'est le test de régression** | serveur (PostgreSQL) |
| R32 | `cloturer` sous verrou | `cloturer(C)` sur une campagne dont l'objet a été chargé `en_cours` avant que `rembourser_les_indecis` ou `annuler` l'ait changée (objet périmé), **sans fil** | le service relit sous verrou et renvoie le statut réel sans écrire ; tourne aussi sur SQLite (équivalent de R34 de F-024) | serveur |
| R33 | non-régression de `cloturer` | `cloturer` d'une campagne `en_cours` minimum atteint, puis minimum manqué | issue inchangée : `financee` + séquestre `bloque` + notifications « Campagne financée » (participants et groupeur), ou `minimum_non_atteint` + participants prévenus, argent non remboursé ; `cloturee_le` posée | serveur |

### Scénarios — Acheteur

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R34 | R2 jouée | A1 ouvre `GET /api/notifications/` | la relance J+3 est présente, non lue, genre `relance_retrait`, lien `/mes-achats/<id>` ; A3 (`retiree`) n'en a pas | serveur |
| R35 | R2 jouée | A1 ouvre la cloche (`Cloche.tsx`) à 390 px, clique la relance | l'icône `PackageCheck` (déjà prévue), le titre « Votre colis vous attend » ; le clic mène à `/mes-achats/<id>` qui s'ouvre sur la bonne part (pas de page introuvable) | web boutique |
| R36 | R11 jouée | A2 `GET /api/participations/<id>/` | `statut == "reputee_livree"`, `statut_libelle == "Non retirée — réputée livrée"`, `reputee_livree_le` non nul au format ISO ; la réponse **ne contient pas** de champ d'une autre part ; pour une part `prete` : `reputee_livree_le == null` | serveur |
| R37 | R11 jouée | A1 (autre acheteur) `GET /api/participations/<id de A2>/` | 404 ; rien d'écrit | serveur |
| R38 | R11 jouée | A2 ouvre `/mes-achats`, 390 px | la carte porte l'étiquette « Non retirée — réputée livrée » (ton neutre, pas rouge) ; le détail affiche « Délai de retrait écoulé le <date> : la remise est réputée faite. » et « Si le groupeur a encore votre colis, présentez ce code » ; le **QR et le code restent visibles** ; aucune autre action de paiement ; pas de texte coupé | web boutique |
| R39 | C `distribution`, A2 `prete` | A2 ouvre le détail de sa part | « À retirer avant le <fin_du_retrait_le formaté> », la date = `mise_a_disposition_le + 14 j` (comparer au JSON de `GET /api/catalogue/campagnes/<id>/` : `fin_du_retrait_le` présent, non recalculé en TypeScript) ; pour une campagne sans mise à disposition : `fin_du_retrait_le == null` et rien d'affiché | serveur + web boutique |
| R40 | R12 jouée | A2 ouvre la cloche | « Délai de retrait écoulé » avec une icône définie pour `livraison_reputee` (ou `Bell` par défaut, sans casse) ; lien vers `/mes-achats/<id>` valide | web boutique |
| R41 | R11 jouée | A2 (part `reputee_livree`, campagne `terminee`) `POST /api/avis/` sur C | `peut_etre_notee` vrai ; **201** ; `avis_recus` +1 ; la `note` du groupeur se recalcule (recours prévu par §2) ; le même acheteur ne note pas deux fois (400, non-régression) | serveur |
| R42 | A1 `retiree` (R11) | A1 ouvre sa part | inchangée : « retiré le <date> », aucune mention « réputée livrée » ; aucune notification J+14 | serveur + web boutique |
| R43 | C `distribution`, une part `reputee_livree` après D2 : A2 présente son code | voir R47 | A2 voit sa part `retiree` et la notification « Retrait confirmé » | serveur |

### Scénarios — Groupeur

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R44 | R11 jouée | G `GET /api/groupeur/campagnes/<id>/participants/` | A1 `retiree`, A2 et A3 `reputee_livree` avec `reputee_livree_le` ; `statut_libelle` « Non retirée — réputée livrée » ; téléphones et champs privés dans la même forme qu'avant (aucun champ nouveau sauf `reputee_livree_le`) | serveur |
| R45 | idem | un autre groupeur G2 liste les participants de C | 404 ; un acheteur : 403 ; un anonyme : 401/403 | serveur |
| R46 | R11 jouée | G ouvre `/groupeur/campagnes/<id>` à 390 px | « Campagne terminée » ; la liste nominative distingue **trois états** : remis (coche verte), réputé livré (icône distincte + libellé « Non retirée — réputée livrée »), et plus aucun « prêt » ; le compteur « 1 / 3 colis remis » ne compte que les `retiree`, avec « dont 2 réputé(s) livré(s) » ; **aucune** action de mise à disposition ni de validation de code proposée sur une campagne `terminee` sauf le champ de code si D2 le prévoit (voir R47) ; collecte, jauge et montant identiques à ceux d'avant J+14 | web boutique |
| R47 | R11 jouée, A2 vient avec son code après J+14 | G `POST /api/groupeur/campagnes/<id>/retrait/` `{"code": "<code de A2>"}` | **200** ; A2 `retiree`, `retiree_le` et `remise_par` = G posés, `reputee_livree_le` conservée ; `participants_servis` +1 ; `campagnes_terminees` **inchangé** ; C reste `terminee` ; A2 reçoit « Retrait confirmé » ; aucun mouvement d'argent | serveur |
| R48 | R47 jouée | G valide de nouveau le même code | **400** « Colis déjà retiré le <date> » ; aucun compteur ne bouge | serveur |
| R49 | C `terminee`, code inconnu, ou code d'une autre campagne, ou QR `GA|<autre campagne>|…` | G valide | 400 (« Code inconnu pour cette campagne. » / « Ce QR code ne concerne pas cette campagne. ») ; rien d'écrit | serveur |
| R50 | C `distribution` à `5 j`, code valide d'une part `prete` | G valide (non-régression de `valider_retrait`) | 200, part `retiree` ; si c'était la dernière, C `terminee` et réputation créditée **une fois** ; `TestDistributionEtRetrait` reste vert **sans modification** | serveur |
| R51 | G2 (autre groupeur), un acheteur, un anonyme | chacun `POST …/retrait/` sur C | 404 / 403 / 401-403 ; rien d'écrit (non-régression) | serveur |
| R52 | R11 jouée | G ouvre `/groupeur/notifications` (ou la cloche) | « Campagne terminée » avec une icône définie pour `campagne_terminee` (sinon `Bell`) ; le lien mène à `/groupeur/campagnes/<id>` | web boutique |
| R53 | G, tableau de bord `espaces/groupeur.py` | après R11 | la campagne est comptée terminée ; le montant collecté et le nombre de participants **ne baissent pas** ; le profil public affiche `campagnes_terminees` et `participants_servis` créditées | serveur + web boutique |
| R54 | erreur de validation d'un code après J+14 si la réponse est 400 | G valide un code dans l'écran | le message du serveur s'affiche dans l'alerte, lisible, pas « Connexion impossible » | web boutique |

### Scénarios — Administrateur et démonstration

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R55 | R11 jouée | l'administrateur ouvre le tableau de bord (`espaces/administration.py` l. 237) | la campagne est comptée parmi les `terminee` sans autre changement ; aucune erreur ; `npm run verifier` côté `admin` vert (aucun écran n'affiche le statut d'une part) | serveur + web admin |
| R56 | R21 jouée (campagne bloquée par le séquestre) | l'administrateur lance `--a-blanc` depuis le terminal ou consulte le journal | la campagne apparaît nommée avec « fonds consignés » ; la commande `controler_les_sequestres` (F-024) la signale aussi (campagne `distribution` à solde positif), code 1 | serveur |
| R57 | base neuve | `python manage.py charger_demo` | sans erreur ; `VERSION_DEMO == "7"` ; une campagne démo `terminee` avec parts `retiree` **et** `reputee_livree` (construite par le service `reputer_livree`, pas par écriture directe) ; un acheteur de démonstration a une relance `relance_retrait` dans sa cloche ; séquestres cohérents (`controler_les_sequestres` : « Aucune anomalie. », code 0) ; sur une base déjà en version « 6 », le second lancement recharge le jeu | serveur |
| R58 | base démo en version 6 | `charger_demo` | le jeu est remis à plat (version différente) et les ajouts apparaissent ; en version 7, un second lancement dit « déjà en version 7 » | serveur |
| R59 | boutique à 390 px, démo chargée | un acheteur de démo ouvre « Mes achats » | la part `reputee_livree` affiche « Non retirée — réputée livrée » ; la part de la campagne en distribution affiche « À retirer avant le <date> » ; la cloche montre la relance | web boutique |

### Tests automatiques attendus

Tous sont à écrire. Collecte à vérifier : `python -m pytest --collect-only -q groupachat/tests/test_retraits_echus.py groupachat/paiements/tests.py` (motifs `test_*.py` et `tests.py` déjà collectés). Les tests « de régression » doivent **échouer avant le correctif** (sur `7a31195`).

| Scénario | Fichier :: test | Régression ? |
|---|---|---|
| R1, R2 | `tests/test_retraits_echus.py::TestRelances::test_rien_n_est_envoye_avant_le_troisieme_jour` ; `::test_la_premiere_relance_part_pile_a_j_plus_3` (titre, lien, code, point de remise, date limite, A3 et A4 exclus) | non (nouveau) |
| R3 | `::test_deux_passages_le_meme_jour_n_envoient_qu_une_relance` | non |
| R4, R5 | `::test_rien_de_plus_la_veille_du_septieme_jour` ; `::test_la_seconde_relance_part_pile_a_j_plus_7` | non |
| R6 | `::test_apres_une_panne_seule_la_relance_la_plus_avancee_part` | non |
| R7 | `::test_une_etape_sans_destinataire_est_quand_meme_jouee` | non |
| R8, R9 | `::test_une_campagne_terminee_annulee_ou_en_approvisionnement_n_est_pas_relancee` ; `::test_pas_de_relance_ordinaire_au_dela_de_j_plus_14` | non |
| R10 | `::TestLivraisonReputee::test_rien_ne_bouge_la_veille_du_quatorzieme_jour` | non |
| R11 | `::test_a_j_plus_14_pile_les_parts_non_retirees_sont_reputees_livrees` (statuts, dates, parts retirées/remboursées intactes) ; `::test_la_campagne_passe_terminee` ; `::test_la_reputation_compte_la_campagne_mais_pas_les_parts_non_retirees` | non |
| R12 | `::test_l_acheteur_et_le_groupeur_sont_prevenus` | non |
| R13 | `::test_la_jauge_et_le_montant_collecte_ne_baissent_pas` ; `::test_le_sequestre_n_est_pas_touche` (aucune `Transaction`) | non |
| R14 | `::test_un_second_passage_ne_credite_pas_deux_fois` | non |
| R15 | `::test_personne_n_est_venu_la_campagne_se_termine_sans_participant_servi` | non |
| R16 | `::test_une_campagne_deja_terminee_n_est_pas_touchee` ; `::test_une_part_annulee_ou_remboursee_reste_telle_quelle` | non |
| R17 à R19 | `::test_sans_relance_prealable_la_cloture_attend_le_preavis` (T, T+71 h 59 min, T+72 h) | non |
| R20 | `::test_la_seule_relance_j_plus_3_ne_vaut_pas_preavis` (selon **question 1**) | non |
| R21, R22 | `::test_une_campagne_dont_les_fonds_sont_encore_consignes_n_est_pas_close` (avec `caplog` : warning, aucun nom ni numéro) ; `::test_une_campagne_bloquee_n_empeche_pas_les_autres` | non |
| R23, R24 | `::TestCommandePlanifiee::test_le_mode_a_blanc_annonce_sans_rien_changer` (sortie + empreinte) ; `::test_a_blanc_et_passage_reel_traitent_les_memes_campagnes` | non |
| R25 | `::test_la_commande_enchaine_cloture_remboursement_relances_et_j_plus_14` ; `tests/test_cloture.py` existant reste vert | non |
| R26 | `::test_la_contrainte_refuse_une_part_reputee_livree_sans_date` (`IntegrityError`) ; `::test_une_part_retiree_peut_garder_sa_date_de_reputation` | non |
| R27 | `python manage.py makemigrations --check` et `migrate` sur une base peuplée (contrôle manuel, relevé de recette) | non |
| R28, R29 | `::TestCourses::test_le_dernier_code_et_la_tache_ne_terminent_la_campagne_qu_une_fois` (paramétré dans les deux sens, PostgreSQL) | **oui** |
| R30 | `::TestCourses::test_la_cloture_et_l_annulation_simultanees_restent_coherentes` (PostgreSQL) | **oui** |
| R31 | `::TestCourses::test_la_cloture_verrouille_la_campagne_avant_le_sequestre` (PostgreSQL ; échoue sur `deadlock detected` sans le correctif C-052) | **oui** |
| R32 | `paiements/tests.py::test_cloturer_relit_la_campagne_sous_verrou` (objet périmé, tourne partout) | **oui** |
| R33 | tests existants de clôture (`commandes/tests.py`, `tests/test_cloture.py`) inchangés et verts ; `paiements/tests.py::test_cloturer_notifie_et_bloque_le_sequestre` si absent | non |
| R34, R36, R37, R39 | `::TestApi::test_l_acheteur_voit_sa_part_reputee_livree` (champs `statut`, `statut_libelle`, `reputee_livree_le`, `fin_du_retrait_le`, 404 d'un autre acheteur) | non |
| R41 | `::test_une_part_reputee_livree_peut_noter_le_groupeur` | non |
| R44, R45 | `::TestApi::test_le_groupeur_voit_les_parts_reputees_livrees_dans_sa_liste` ; `::test_un_autre_groupeur_ne_voit_pas_les_participants` | non |
| R47, R48 | `::TestRetraitApresEcheance::test_un_code_presente_apres_j_plus_14_est_accepte` (part, compteurs, `reputee_livree_le` conservée, campagne terminée une fois) ; `::test_un_code_deja_retire_reste_refuse_apres_la_cloture` | non |
| R49 à R51 | `::test_un_code_etranger_ou_inconnu_reste_refuse_apres_la_cloture` ; `commandes/tests.py::TestDistributionEtRetrait` inchangé ; `::test_seul_le_groupeur_de_la_campagne_valide_un_retrait` | non |
| R53 | `::test_le_tableau_de_bord_groupeur_compte_la_campagne_terminee_sans_baisser_la_collecte` | non |
| R55 à R56 | `::test_le_tableau_de_bord_admin_compte_la_campagne_terminee` ; `controler_les_sequestres` : test d'une campagne `distribution` à solde positif | non |
| R57, R58 | `::test_le_jeu_de_demonstration_contient_une_campagne_reputee_livree` (appel de `charger_demo`, `VERSION_DEMO == "7"`, `libere + rembourse ≤ consigné`) | non |
| Notifications | `tests/test_notifications_liens.py::test_chaque_lien_de_notification_correspond_a_une_route_de_la_boutique` : ajouter une campagne relancée puis close ; `relance_retrait`, `livraison_reputee`, `campagne_terminee` à l'ensemble attendu (aucune assertion retirée) | non |

Courses (R28 à R31) : si la base de la CI est SQLite, elles sont **non vérifiables** ; la preuve de la relecture sous verrou repose alors sur R32. À écrire tel quel dans le rapport de recette (« testé sur PostgreSQL » ou « pas pu tester : <raison> »).

### Vérification d'interface
- **Boutique, `/mes-achats` et détail d'une part, 390 px** : étiquette « Non retirée — réputée livrée » (aucune couleur en dur, ton `neutre` de `TONS.reputee_livree`) ; encadré daté ; QR et code visibles ; « À retirer avant le … » pour une part `prete` ; états chargement (squelette), erreur (alerte, pas liste vide), vide (« aucun achat ») conservés. `TONS` doit compiler (`Record<StatutParticipation, …>`) : `npm run verifier` vert.
- **Boutique, `/groupeur/campagnes/<id>`, 390 px** : trois états dans la liste nominative, compteur « dont n réputé(s) livré(s) » seulement si n > 0, campagne `terminee` sans action de mise à disposition.
- **Cloche et `/notifications`** : icônes pour `relance_retrait` (existante), `livraison_reputee`, `campagne_terminee` ; liens valides.
- **Console admin** : aucun écran du statut ; tableau de bord inchangé et sans erreur.
- **Types** : `StatutParticipation` gagne `reputee_livree` ; `Participation` et `Participant` gagnent `reputee_livree_le: string | null` ; `CampagneResume` gagne `fin_du_retrait_le: string | null` ; les champs lus par les écrans existent dans le JSON réel (relevé à comparer à la recette).
- Pas de changement de route ni de méthode : `GET /api/participations/`, `GET /api/groupeur/campagnes/<id>/participants/`, `POST /api/groupeur/campagnes/<id>/retrait/`, `GET /api/notifications/`.

## Questions ouvertes

1. **Que vaut le préavis de 72 h (D3) quand seule la relance J+3 a été envoyée ?** La conception dit « aucune relance envoyée depuis au moins 72 h » sans préciser si la J+3 compte ; or seule la J+7 (ou la relance de rattrapage) annonce que « la remise sera réputée faite et la campagne close ». Cas : panne entre J+4 et J+20, la J+3 date de 17 jours. Scénario R20.
   (a) Toute relance de plus de 72 h compte : la campagne est close au premier passage, sans que l'acheteur ait lu l'avertissement de clôture.
   (b) Seule `relance_retrait_j7_le` (J+7 ou rattrapage) compte : on envoie la relance de rattrapage, puis on clôt 72 h plus tard.
   **Recommandation : (b)**, dans l'esprit de D3 (« jamais de réputée livrée sans avoir prévenu »). Coût : un test (R20), rien dans le modèle.
2. **Fréquence de l'avertissement D1 (R21).** Une campagne bloquée par ses fonds consignés est journalisée à **chaque passage horaire** (24 lignes par jour) tant que l'administrateur n'a pas tranché.
   (a) Un `warning` à chaque passage, simple, sans état.
   (b) Un seul avertissement, au premier passage (demande une date ou un drapeau, donc une colonne de plus : écartée par D6).
   **Recommandation : (a)** : le cas est défensif depuis T10 et `controler_les_sequestres` le signale déjà ; ne pas ajouter de colonne.
3. **Qu'attend-on d'une validation de code sur une campagne `terminee` dans l'écran groupeur (R46, R54) ?** D2 accepte le code après J+14, mais l'écran d'une campagne `terminee` ne propose peut-être plus le champ de code. Si l'écran le masque, D2 n'est atteignable que par l'API.
   (a) Garder le champ de code visible tant qu'il reste une part `reputee_livree`.
   (b) Ne rien changer : retrait tardif par API seulement.
   **Recommandation : (a)**. Sans cela, D2 n'a pas d'interface pour le groupeur qui a le colis et le code de l'acheteur sous les yeux. Le test d'interface R46 prend (a) comme attendu tant que l'utilisateur n'a pas répondu.

**Prêt à coder ?** Oui, avec réserve : D1 à D8 et la conception tranchent tout le reste ; les trois questions n'arrêtent pas le codage, mais les scénarios R20 et R46/R54 dépendent des réponses (recommandations retenues par défaut jusqu'à décision).

## Recette — 2026-10-28

**RECETTE OK** · base `7a31195` + code de la branche `feat/F-031-relances-retrait` (commitée ensuite en `5dc1562`) · `serveur ✅ · web boutique ✅ · web admin ✅ (non-régression) · mobile —`

Environnement : SQLite jetable `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/37d3c70e-6597-49b8-bb11-132f1e1eb6a5/scratchpad/f031/base.sqlite3` (réglages `recette_settings.py`, jamais `.env` ni base du dépôt), `charger_demo` version « 7 », vrai `manage.py cloturer_les_campagnes_echues` (processus séparé), Django sur le port 8123 servant les deux interfaces compilées dans `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/37d3c70e-6597-49b8-bb11-132f1e1eb6a5/scratchpad/f031/web`, Chrome headless à 390 px. Le temps avance en reculant `mise_a_disposition_le`. Courses R28 à R33 : testées sur PostgreSQL par `reviewer-tester`, non rejouées ici.

### Serveur (tâche réelle, relue en base après chaque passage)
| Scénario | Verdict | Preuve |
|---|---|---|
| R1 (J+3 − 1 min) | ✅ | bilan « 0 relance(s) », dates nulles |
| R2 (J+3 pile, 2 prêtes / 1 retirée / 1 remboursée) | ✅ | 2 notifications « Votre colis vous attend », lien `/mes-achats/<part>`, code propre à la part, date limite = mise à disposition + 14 j ; séquestre 180 000/180 000 inchangé |
| R3 (repasser deux fois) | ✅ | date `relance_retrait_j3_le` identique, 0 notification de plus |
| R4 / R5 (J+7 − 1 min, J+7) | ✅ | rien, puis « Dernier rappel » (« réputée faite » + code), `j3` inchangée |
| R6 (panne J+2 à J+8) | ✅ | une seule relance « Dernier rappel », `j3` nulle, rien de plus à J+9 |
| R7 (aucune part prête à J+3) | ✅ | 0 notification, `j3` posée |
| R8 (terminée, en_cours, minimum_non_atteint à 5 j) | ✅ | 0 relance, dates nulles |
| R10 (J+14 − 1 min) | ✅ | reste `distribution`, parts et réputation inchangées |
| R11, R12, R13, R14 (J+14 pile) | ✅ | parts `reputee_livree` (daté), part retirée intacte, remboursée intacte ; `campagnes_terminees` +1, `participants_servis` +1 (le retiré seul) ; notifications « Délai de retrait écoulé » (lien part) + « Campagne terminée » (lien `/groupeur/campagnes/<id>`, « 2 colis non retiré(s)… 1 participant(s) servi(s) ») ; collecte, quantité, participants, séquestre, nombre de `Transaction` (88) identiques ; deux passages de plus : rien |
| R15 (personne n'est venu) | ✅ | 4 `reputee_livree`, `participants_servis` +0, `campagnes_terminees` +1 |
| R16 (déjà terminée par les codes, 20 j) | ✅ | réputation inchangée |
| R17, R18, R19 (préavis D3 : 20 j sans relance) | ✅ | rattrapage (date limite = passage + 72 h), parts `prete` ; à 72 h − 1 min rien ; à 72 h clôture, réputation créditée une fois |
| R20 (J+3 seule, 20 j) | ✅ | relance de rattrapage, pas de clôture ; clôture après 72 h |
| R21 (D1 défensif, `montant_libere` = 0) | ✅ | reste `distribution`, parts `prete`, un `warning` par passage (« Campagne 48 … clôture suspendue », seul l'identifiant), aucun nom ni code |
| R22 | ✅ | la saine est close, la bloquée reste, code de sortie 0 |
| R23 (`--a-blanc`) | ✅ | sortie : « relance j3 », « relance j7 », « clôture à J+14 (N colis non retirés) », « relance de rattrapage… », « bloquée : fonds consignés » ; md5 de la base identique avant/après (`md5-avant.txt`, `md5-apres.txt`), code 0 |
| R24 | ✅ avec réserve | mêmes campagnes traitées ; mais la relance de rattrapage n'est pas listée par le passage réel (voir défaut 1) |
| R25 | ✅ | bilan « N clôture(s), N remboursement(s), N relance(s), N campagne(s) close(s) à J+14. » |
| R36, R37, R39 (API acheteur) | ✅ | `statut_libelle` « Non retirée — réputée livrée », `reputee_livree_le` ISO ; autre acheteur : 404 ; `fin_du_retrait_le` = mise à disposition + 14 j, `null` sans mise à disposition |
| R41 | ✅ | `peut_etre_notee` vrai, POST `/api/avis/` 201, `avis_recus` +1, second avis 400 |
| R44, R45 | ✅ | trois statuts + `reputee_livree_le` ; autre groupeur 404, acheteur 403, anonyme 403 |
| R47, R48 (D2 : code après J+14) | ✅ | 200, part `retiree`, `reputee_livree_le` conservée, `remise_par` posé, `participants_servis` +1, `campagnes_terminees` inchangé, « Retrait confirmé » reçu, 0 transaction ; second envoi 400 « Colis déjà retiré le… » |
| R49, R51 | ✅ | « Code inconnu pour cette campagne. » (inconnu et autre campagne), « Ce QR code ne concerne pas cette campagne. » ; autre groupeur 404 / acheteur 403 / anonyme 403 |
| R53, R55 | ✅ | tableau de bord groupeur : terminées comptées, réputation créditée ; admin : 200, « terminees » = 8 |
| R56 | ✅ | `controler_les_sequestres` nomme la campagne 48 (solde 180 000), code 1 |
| R57, R58 | ✅ | `charger_demo` version 7 sans erreur, « Bouilloires Tefal » `terminee` avec une part `reputee_livree` (notification « Délai de retrait écoulé »), relances dans les cloches, « Aucune anomalie. » code 0 ; `--synchroniser` en 7 : « déjà en version 7 » ; base forcée en « 6 » : jeu rechargé |
| R26, R27, R9 | pas rejoué ici | couverts par `test_retraits_echus.py` (reviewer : 54 passed sur PostgreSQL) |

### Web boutique, 390 px (captures dans `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/37d3c70e-6597-49b8-bb11-132f1e1eb6a5/scratchpad/f031/captures/`)
| Scénario | Verdict | Preuve |
|---|---|---|
| R35, R40 cloche | ✅ | relance et « Délai de retrait écoulé » avec icônes (Clock, PackageCheck), le clic sur la relance mène à `/mes-achats/157` (pas de page introuvable) — `a3-cloche.png`, `a1-clic-relance.png` |
| R38, R59 `MesAchats` | ✅ | étiquette neutre « Non retirée — réputée livrée », « À retirer avant le 10 novembre 2026 » — `a3-mes-achats.png`, `a1-mes-achats.png` |
| détail d'une part réputée livrée | ✅ | code et QR visibles, « Si le groupeur a encore votre colis, présentez ce code », encadré « Délai de retrait écoulé le 28 octobre 2026 » — `a3-detail-reputee-bouilloires.png` |
| R42 | ✅ | part retirée : « Retirée », sans mention réputée livrée |
| R46 groupeur, campagne `terminee` mixte | ✅ | « 2 / 4 colis remis, 1 réputé(s) livré(s) », bouton « Valider un retrait tardif », trois icônes distinctes — `g-campagne-t4-terminee-mixte.png` ; tout retiré (campagne 49) : « Tous les colis ont été remis », pas de bouton ; en distribution : pas de bouton |
| R52 notification groupeur | ✅ | « Campagne terminée » (icône CheckCheck), le clic mène à `/groupeur/campagnes/47` — `g-notifications.png` |
| largeur | ✅ | `scrollWidth` = 390 sur toutes les pages, aucune erreur console, aucune réponse API ≥ 400 |
| chargement | ✅ | squelette sans texte trompeur côté acheteur |
| erreur / vide | ❌ hors périmètre | voir défauts 2 et 3 (antérieurs à F-031) |

### Web admin
Tableau de bord (`admin.localhost:8123`, compte 99000011) : charge, aucun appel ≥ 400, aucune erreur console (`admin-tableau-de-bord.png`). `npm run verifier` : vert, `git status` inchangé.

### Défauts relevés (aucun ne bloque F-031)
1. Mineur, F-031 : la relance de rattrapage (`reputer_livree`, `CLOTURE_RATTRAPAGE`) n'est ni nommée ni comptée par le passage réel (« 0 relance(s) »), alors que `--a-blanc` l'annonce ; `retraits.py` (`reputer_livrees_les_echues` ne remonte que les campagnes closes) et `cloturer_les_campagnes_echues.py`. Proposition C-059.
2. Hors périmètre : sur `/mes-achats` et `/notifications`, une erreur 500 de l'API s'affiche comme un état vide (« Aucun achat pour l'instant », « Rien à signaler »). Proposition C-060.
3. Hors périmètre : sur `/groupeur/campagnes/<id>` d'une campagne terminée, pendant le chargement ou si `participants/` échoue, l'écran affiche « Tous les colis ont été remis… » et « Qui a payé (0) ». Proposition C-061.
4. Observation : le compteur « Qui a payé » compte une part forcée `remboursee` (état non réaliste en distribution) ; non reproductible par le vrai parcours.
