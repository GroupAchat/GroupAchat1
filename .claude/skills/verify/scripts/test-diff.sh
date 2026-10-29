#!/usr/bin/env bash
# Liste les signaux de tests affaiblis dans le diff (commité + non commité) par rapport
# à une branche de base. Informatif : c'est à la relecture de juger chaque signal.
# Usage : test-diff.sh [branche-de-base]   (défaut : staging, la base des branches de travail)
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

base="${1:-staging}"
git rev-parse --verify --quiet "$base" >/dev/null || base="HEAD"
tests=(':(glob)**/test_*.py' ':(glob)**/*_test.py' ':(glob)**/*_test.dart' ':(glob)**/tests.py' ':(glob)**/*.test.*' ':(glob)**/*.spec.*' ':(glob)**/*.e2e-spec.*')

diff="$( { git diff "$base"...HEAD -- "${tests[@]}"; git diff HEAD -- "${tests[@]}"; } 2>/dev/null )"
count() { printf '%s\n' "$diff" | grep -cE "$1" || true; }

skips=$(count '^\+.*(@pytest\.mark\.(skip|xfail)|pytest\.skip\(|\b(it|test|describe)\.(skip|todo|only)\(|\bx(it|describe)\(|\bskip: *[^f[:space:]]|@Skip\()')
asserts_removed=$(count '^-[^-].*\b(assert |expect\()')
asserts_added=$(count '^\+[^+].*\b(assert |expect\()')
defs_removed=$(count '^-\s*(async )?def test_|^-\s*(it|test|testWidgets)(\.only)?\(')
defs_added=$(count '^\+\s*(async )?def test_|^\+\s*(it|test|testWidgets)(\.only)?\(')
tests_removed=$(( defs_removed > defs_added ? defs_removed - defs_added : 0 ))
bypass=$(count '^\+.*(# type: ignore|as any\b|@ts-(ignore|expect-error)|// ?ignore(_for_file)?:|as dynamic\b)')
deleted=$( { git diff --diff-filter=D --name-only "$base"...HEAD -- "${tests[@]}"; git diff --diff-filter=D --name-only HEAD -- "${tests[@]}"; } 2>/dev/null | sort -u)

echo "Base : $base"
echo "Tests désactivés ou isolés ajoutés : $skips"
echo "Assertions supprimées / ajoutées : $asserts_removed / $asserts_added"
echo "Fonctions de test supprimées : $tests_removed"
echo "Contournements de typage ajoutés : $bypass"
echo "Fichiers de test supprimés : ${deleted:-aucun}"

signals=$((skips + tests_removed + bypass))
[ "$asserts_removed" -gt "$asserts_added" ] && signals=$((signals + 1))
[ -n "$deleted" ] && signals=$((signals + 1))
if [ "$signals" -gt 0 ]; then
  echo "SIGNAUX : $signals — à examiner avec reference.md, lignes concernées :"
  printf '%s\n' "$diff" | grep -nE '^\+.*(skip|xfail|todo|only\(|xit\(|xdescribe|type: ignore|as any|@ts-|ignore(_for_file)?:|as dynamic)|^-[^-].*\b(assert |expect\(|def test_|it\(|test\(|testWidgets\()' | head -40
else
  echo "SIGNAUX : 0"
fi
exit 0
