---
type: fonctionnalite
id: F-031
statut: à faire
date: 2026-10-27
tags: [fonctionnalite, F-031, retrait, reputation, tache-planifiee, mvp]
---

# F-031 — Relances de retrait à J+3 et J+7, livraison réputée acquise à J+14

Statut : **à faire**. Ceci est la conception (T5 de [[M-001-terminer-le-mvp]], `archi-backend`, 2026-10-27, base `abaa622` sur `staging`), pas encore l'implémentation. Rôle : **Système**. Sources : `CAHIER_DES_CHARGES.md` §4 (« Colis non récupéré », « Réputation », « Séquestre »), §3 (administrateur, points 4 et 5), §8 (notifications), §9 (cycle de vie) ; décision **Q13** et **Q4** de [[2026-10-26-decisions-carte]] ; verrous de [[2026-10-27-decisions-f016]] ; [[carte]] (parcours « colis non retiré », Q13, Q15).

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

Défaut relevé par l'architecte et inclus dans F-031 : `valider_retrait` ne verrouille rien (§4.4) ; une validation du dernier code pendant le passage de J+14 terminerait la campagne deux fois.

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
