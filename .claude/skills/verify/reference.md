# Reconnaître un test affaibli

Un test affaibli passe parce qu'on a baissé l'exigence, pas parce que le code est correct.

## Signaux

| Signal | Python | JavaScript / TypeScript |
|---|---|---|
| Test désactivé | `@pytest.mark.skip`, `xfail`, `pytest.skip()` | `it.skip`, `xit`, `describe.skip`, `it.todo` |
| Test isolé oublié | — | `it.only`, `describe.only` (les autres ne tournent plus) |
| Assertion supprimée | moins de lignes `assert` | moins de `expect(` |
| Assertion assouplie | `== 201` → `in (200, 201)` ; `==` → `is not None` | `toBe(201)` → `toBeDefined()` ; `toEqual` → `toMatchObject` partiel |
| Valeur attendue changée | `assert total == 120000` → `== 100000` | `toBe(120000)` → `toBe(100000)` |
| Exception élargie | `pytest.raises(OrderNotFoundError)` → `pytest.raises(Exception)` | `rejects.toMatchObject({ code })` → `rejects.toThrow()` |
| Mock complaisant | le mock renvoie exactement la valeur attendue par l'assertion | idem |
| Test ou fichier supprimé | `def test_…` retiré, fichier `test_*.py` supprimé | `it(…)` retiré, fichier `*.test.ts` supprimé |
| Typage contourné pour passer | `# type: ignore` ajouté | `as any`, `@ts-expect-error` ajoutés |

Dart / Flutter : `skip: true` ou `@Skip(...)` ajouté ; `testWidgets(…)` retiré ; `findsOneWidget` → `findsWidgets` ou `findsAny` ;
`throwsA(isA<NotFoundException>())` → `throwsA(anything)` ; `// ignore:` ou `as dynamic` ajouté pour passer l'analyse ;
fichier golden régénéré (`--update-goldens`) sans que l'écran ait changé à la demande.

## Quand c'est légitime

Seulement si la demande en cours le justifie, et le rapport le cite :
- La fonctionnalité testée a été retirée à la demande → son test part avec elle.
- La règle métier a changé à la demande (nouveau prix, nouveau plafond) → la valeur attendue suit, et un test couvre la nouvelle règle.
- Un test était faux (il vérifiait un bug) → il est corrigé, et le rapport explique en quoi il était faux.

Dans tous les autres cas : remettre le test d'origine et corriger le code.
