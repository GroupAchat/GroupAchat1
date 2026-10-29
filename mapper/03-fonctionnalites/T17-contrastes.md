---
type: fonctionnalite
id: T17
statut: terminée
couvre: [C-077, C-078]
mission: M-001 (T17)
base: f78f52b
commit: 75fe4ba
fusion: f32b69c (staging)
date: 2026-10-28
tags: [fonctionnalite, T17, M-001]
---

# T17 : contrastes illisibles en thème clair et en thème sombre

Ajoutée le 2026-10-28 (accord de l'utilisateur), placée avant T14. Source : « Recette (reprise) — 2026-10-28 » de [[T16-defauts-genants]], défauts 1 et 2. Les deux défauts sont **préexistants** (même rendu sur `staging` avant T16) et visibles en démonstration.

Rôles : administrateur (D1, console), groupeur (D1 et D2 sur `/groupeur`), visiteur et acheteur (D2 sur la fiche campagne). Couches : web admin (D1) et web boutique (D1, D2). Serveur : aucune règle touchée. Pas de mobile dans ce dépôt.

## D1 — C-077 : texte blanc sur fond blanc en thème clair

**Règle.** Un chiffre de tableau de bord se lit dans les deux thèmes. Le fond coloré fait partie de la carte, il ne dépend pas d'un calque placé derrière la surface.

**État constaté.**
- Console, carte « Détenu en séquestre » : `frontend/admin/src/pages/TableauAdmin.tsx` l. 80-84. Le texte est `text-white` sur une `.surface` blanche en clair ; le dégradé `degrade-accent -z-10` passe derrière la surface et ne se voit pas. Lisible en sombre.
- Espace groupeur, tuile « Consigné en séquestre » : `frontend/boutique/src/pages/groupeur/TableauDeBord.tsx` l. 72 (libellé). Même mécanisme en clair. Lisible en sombre.

**Correction proposée (piste, à trancher par `fonctionnalite`).** Porter le fond coloré dans la carte elle-même, ou choisir une couleur de texte qui tient sur la surface en clair. Aucune couleur en dur dans la page : les couleurs viennent de `frontend/commun/src/index.css`. Pas de changement serveur. Si la correction touche un composant du socle, elle reste en un seul exemplaire.

### Scénarios

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R1 | console, thème clair, 390 px, tableau de bord | on lit la carte « Détenu en séquestre » | libellé et montant lisibles (texte clair sur fond coloré, contraste suffisant) ; `scrollWidth` = 390 | web admin |
| R1 bis | idem à 1280 px | même lecture | même résultat | web admin |
| R2 | console, thème sombre | on lit la même carte | rendu inchangé par rapport à `staging` (capture de référence avant correction) | web admin |
| R3 | groupeur, thème clair, `/groupeur` (tableau de bord) | on lit la tuile « Consigné en séquestre » | libellé et montant lisibles ; `scrollWidth` = 390 à 390 px ; en sombre, rendu inchangé | web boutique |

## D2 — C-078 : bulle « Réponse du groupeur » illisible en thème sombre

**Règle.** La réponse du groupeur sous un avis se lit dans les deux thèmes, sur la fiche campagne et sur `/groupeur`.

**État constaté.** La bulle est le composant `ReponseGroupeur` de `frontend/boutique/src/composants/Avis.tsx` (fonction l. 306, libellé « Réponse du groupeur » l. 311). Elle a la classe `bg-accent-doux` et n'a pas de couleur de texte qui se règle sur le thème : en sombre, le texte n'est pas lisible sur la bulle, qui apparaît en rectangle blanc. La fiche campagne et `/groupeur` affichent cette même bulle (D4-R6 de [[T16-defauts-genants]] : les avis se lisent sur `/groupeur`).

**Correction proposée (piste, à trancher par `fonctionnalite`).** Régler le fond et la couleur du texte de la bulle sur les jetons du thème (`index.css`), en gardant `bg-accent-doux` si ses valeurs en sombre sont correctes ; sinon, un fond sombre cohérent. Pas de changement serveur ni de changement de contenu.

### Scénarios

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R4 | thème sombre, fiche campagne, un avis avec réponse du groupeur | on lit la réponse | texte lisible dans la bulle ; `scrollWidth` = 390 à 390 px | web boutique |
| R4 bis | thème sombre, `/groupeur`, même avis | on lit la réponse | texte lisible ; `scrollWidth` = 390 | web boutique |
| R4 ter | thème clair, les deux pages | on lit la réponse | inchangé par rapport à `staging` | web boutique |

## Ce qui ne change pas

- Thème sombre des cartes de D1 (R2, R3) et thème clair de la bulle de D2 (R4 ter).
- Aucune route, aucun montant, aucun test serveur modifié.

## R5 — non-régression de mise en page

| # | Étant donné | Quand | Alors (observable) | Couche |
|---|---|---|---|---|
| R5 | 390 px, clair et sombre | on ouvre le tableau de bord admin, le tableau de bord groupeur, la fiche campagne et `/groupeur` | aucun débordement horizontal (`scrollWidth` = 390) ; aucun élément coupé | web |

## Tests

Pas de test pytest : aucune règle serveur ne change. Preuve attendue : captures et relevés de contraste à 390 px (clair et sombre) et 1280 px (clair), comme la recette T16 (Chrome headless, valeurs relues dans le DOM). `npm run verifier` doit passer dans les deux interfaces.

## Chevauchement

T17 touche `frontend/admin/src/pages/TableauAdmin.tsx`, `frontend/boutique/src/pages/groupeur/TableauDeBord.tsx`, `frontend/boutique/src/composants/Avis.tsx`, et peut toucher `frontend/commun/src/index.css` pour les jetons. Aucun autre passage en cours ne les touche au 2026-10-28 (T15 suspendue touche `Authentification.tsx` et `types.ts` ; T14 ne touche pas aux interfaces).

Branche : `fix/T17-contrastes`, worktree `.claude/worktrees/t17-contrastes`, base `staging` `f78f52b`.

## Prêt à coder ?

Oui : les défauts sont localisés et les scénarios sont vérifiables. Aucune question ouverte.

## Recette — 2026-10-28

**RECETTE OK** · commit de base `f78f52b` (changements non commités sur `fix/T17-contrastes`) · serveur — (aucune règle touchée) · web admin ✅ · web boutique ✅ · mobile —

Méthode : builds Vite des deux interfaces (`staging` `f78f52b` extrait par `git archive`, et le worktree), une origine Django par build (ports 8101 = T17, 8102 = `staging`), SQLite jetable remplie par `charger_demo`, Chrome headless piloté en CDP, 390 px (1280 px pour R1). Contraste = couleur du texte (alpha composé) contre la couleur **médiane des pixels de la capture** sous l'élément (donc le dégradé réellement visible), formule WCAG. `npm run verifier` : passe. Captures : `/tmp/claude-1000/-home-attito-Boulot-nanatech-groupe-4-groupe-achat-GroupAchat1/2a0ded33-5526-4bfe-abb2-5db865f4b85d/scratchpad/shots/`.

| # | Résultat | Mesure (T17 contre `staging`) |
|---|---|---|
| R1 console, clair | OK | libellé « Détenu en séquestre » 5,87:1 (390 px), 6,5:1 (1280 px) ; « Remboursé » 7,28:1 / 6,97:1. `staging` : 1,0:1 (texte blanc sur blanc, carte vide à l'écran). `scrollWidth` 390 / 1280. `admin-new-clair-390.png`, `admin-stg-clair-390.png` |
| R2 console, sombre | OK | libellé 5,87:1, « Remboursé » 7,86:1 : lisible. Le fond uni de `staging` (10,1:1) devient le dégradé (écart accepté, voir plus bas). `admin-new-sombre-390.png` |
| R3 `/groupeur`, tuile « Consigné en séquestre » | OK | clair : 6,98:1 (`staging` 1,0:1) ; sombre : 6,98:1 (`staging` 11,65:1, fond uni). `scrollWidth` 390. `groupeur-new-clair-390-centre.png`, `groupeur-new-sombre-390-centre.png` |
| R4 « Réponse du groupeur », sombre | OK | fiche `/campagnes/9` et `/groupeur`, groupeur et acheteur : texte 14,81:1 (groupeur) et 11,63:1 (acheteur) ; date 6,14:1 et 4,82:1. `staging` : 1,0 à 1,03:1. |
| R4 clair | OK | inchangé : 16,06:1 (groupeur), 16,6:1 (acheteur), mêmes couleurs calculées que `staging` (0 différence de style sur la fiche, hors sombre). |
| R4 plus : fil `Discussion` (`/campagnes/1`) | OK | sombre : nom et texte 14,81:1 / 11,63:1, date ≥ 4,82:1 (`staging` 1,0:1). Clair inchangé. |
| R4 plus : `/notifications`, non lues | OK | sombre : titre 14,81:1 (groupeur) / 11,63:1 (acheteur), texte et date 6,14:1 / 4,82:1 (`staging` 2,4:1). Clair : titre 16,06:1 / 16,6:1 (`staging` 11,35:1 et 3,37:1), texte 5,17:1 / 5,35:1. |
| R4 plus : panneau de la cloche | OK | sombre : 15,37:1 et 13,51:1 pour le titre, ≥ 5,6:1 pour le reste ; clair : ≥ 5,41:1. |
| Non-régression sombre/clair, groupeur et acheteur | OK | comparaison des styles calculés de tous les éléments, `staging` contre T17, 11 à 14 pages × 2 thèmes × 2 profils : 0 différence sur onglet actif, badges accent, boutons doux, hors les cinq usages visés. Les seules différences sont les fonds `bg-fond-message`, plus le titre des notifications non lues. |
| R5 débordement | OK | `scrollWidth` = 390 sur console, `/groupeur`, fiches campagne, `/notifications`, clair et sombre. |

Écarts avec l'énoncé, à connaître avant la démo (non bloquants) :
1. **Bouton de moyen de paiement sélectionné (feuille de participation), en sombre, acheteur** : pas identique à `staging`, il change volontairement (`bg-accent-doux` devient `bg-fond-message`). `staging` : texte clair sur fond pêche, 1,03:1 (illisible) ; T17 : fond brun sombre, texte 11,63:1. En clair : identique. Groupeur : la feuille de participation ne s'ouvre pas (pas de bouton « Participer » sur les campagnes testées), non rejoué.
2. En sombre, les deux cartes de séquestre passent du fond uni au dégradé : accepté dans l'énoncé.
3. Le titre d'une notification non lue passe à la couleur du texte (décision de l'utilisateur) : vérifié dans les deux thèmes.

Défauts nouveaux : aucun introduit par T17. Préexistants, vus au passage, **identiques sur `staging`**, hors périmètre :
- Mineur : à 390 px, le panneau de la cloche est coupé du côté gauche (le titre « Notifications » touche le bord de l'écran) : `cloche-stg-acheteur-clair.png` et `cloche-new-acheteur-sombre.png`.
- Mineur : en sombre, profil groupeur, le libellé de l'onglet actif (bleu marine sur fond sombre) et le logo sont peu contrastés (`groupeur-new-sombre-390-centre.png`) ; identique à `staging`, donc non-régression respectée.

Pas pu tester : rien de bloquant ; thème clair à 1280 px mesuré uniquement pour R1 (comme demandé). Environnement arrêté : serveurs 8101/8102 et Chrome headless fermés ; la base `backend/base-de-secours.sqlite3` du worktree a été restaurée à son état d'origine.

## Clôture — 2026-10-28

**Terminée.** Relecture finale VALIDÉE, recette « RECETTE OK » (section « Recette — 2026-10-28 »).

- **Passes de relecture.** (1) Première passe : `isolate` sur les cartes vedettes et `--teinte-accent-doux` redéfinie en sombre ; relecture **À CORRIGER** : 15 usages de `accent-fort` sur `accent-doux` à 1,30:1 pour le groupeur. (2) Reprise ciblée : `--teinte-fond-message` / `bg-fond-message` sur cinq usages (Discussion, Avis, Notifications, Cloche, FicheCampagne) ; relecture **À CORRIGER** : titre d'une notification non lue en `accent-fort` sur le nouveau fond, 1,30:1. (3) Second refus : arrêt, décision de l'utilisateur : le titre d'une notification non lue prend la couleur du texte, dans les deux thèmes ([[2026-10-28-decisions-t14-t17]], D1). (4) Relecture finale : VALIDÉE.
- **Preuves.** Commit `75fe4ba` (« Rend lisibles la carte du séquestre et les bulles en thème sombre »), fusionné dans `staging` par `f32b69c` (accord de l'utilisateur). « Vérifier » complet sur `staging` `f32b69c` : `446 passed, 9 skipped in 1418.89s`, migrations « No changes detected », `CHECK: OK (complet)`.
- **Reste, hors T17, au backlog** : C-083 (panneau de la cloche coupé à 390 px), C-084 (thème sombre, profil groupeur : onglet actif et logo), C-085 (piste globale d'accent en sombre, après la présentation).
- **Mission** : [[M-001-terminer-le-mvp]] (T17 `terminée`). Backlog : C-077 et C-078 `terminé`.
