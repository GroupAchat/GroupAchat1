---
type: fonctionnalite
id: T17
statut: en cours
couvre: [C-077, C-078]
mission: M-001 (T17)
base: f78f52b
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
