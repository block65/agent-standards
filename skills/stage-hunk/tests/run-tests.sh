#!/usr/bin/env bash
set -euo pipefail

# Runs stage-hunk eval scenarios against the script directly.
# Usage: run-tests.sh

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$SCRIPT_DIR/scripts/stage-hunk.sh"
SETUP="$SCRIPT_DIR/tests/setup-test-repo.sh"
PASS=0
FAIL=0

run_test() {
  local name="$1"
  local dir="/tmp/stage-hunk-test-$$"
  shift

  "$SETUP" "$dir" > /dev/null 2>&1
  cd "$dir"

  # Run the test function
  if "$@"; then
    echo "PASS: $name"
    ((PASS++)) || true
  else
    echo "FAIL: $name"
    ((FAIL++)) || true
  fi

  rm -rf "$dir"
}

# Eval 1: Single hunk — stage only Tokay Gecko
eval1() {
  "$STAGE" src/pets.md 11-14
  local staged
  staged=$(git diff --cached src/pets.md)
  [[ "$staged" == *"Tokay Gecko"* ]] || return 1
  [[ "$staged" != *"walking by the canal"* ]] || return 1
  [[ "$staged" != *"especially koi"* ]] || return 1
}

# Eval 2: Multi-file — Dogs from pets + Roti Canai from snacks
eval2() {
  "$STAGE" src/pets.md 5
  "$STAGE" src/snacks.md 11-14
  local staged
  staged=$(git diff --cached)
  [[ "$staged" == *"walking by the canal"* ]] || return 1
  [[ "$staged" == *"Roti Canai"* ]] || return 1
  [[ "$staged" != *"Tokay Gecko"* ]] || return 1
  [[ "$staged" != *"Ya Kun"* ]] || return 1
  [[ "$staged" != *"Nam Dok Mai"* ]] || return 1
}

# Eval 3: Split hunk — Mango Sticky Rice only, not Roti Canai
eval3() {
  "$STAGE" src/snacks.md 17
  local staged
  staged=$(git diff --cached src/snacks.md)
  [[ "$staged" == *"Nam Dok Mai"* ]] || return 1
  [[ "$staged" != *"Roti Canai"* ]] || return 1
  local unstaged
  unstaged=$(git diff src/snacks.md)
  [[ "$unstaged" == *"Roti Canai"* ]] || return 1
}

# Eval 4: Error — no unstaged changes
eval4() {
  git add src/pets.md
  ! "$STAGE" src/pets.md 5 2>/dev/null
}

# Eval 5: Error — invalid line spec
eval5() {
  ! "$STAGE" src/pets.md "abc" 2>/dev/null
}

# Eval 6: Error — line range matches no hunks
eval6() {
  ! "$STAGE" src/pets.md 99-100 2>/dev/null
}

# Eval 7: Multi-hunk same file — stage Dogs and Koi but not Tokay Gecko
eval7() {
  "$STAGE" src/pets.md 5,17
  local staged
  staged=$(git diff --cached src/pets.md)
  [[ "$staged" == *"walking by the canal"* ]] || return 1
  [[ "$staged" == *"especially koi"* ]] || return 1
  [[ "$staged" != *"Tokay Gecko"* ]] || return 1
}

# Eval 8: --list-hunks prints hunk summary
eval8() {
  local output
  output=$("$STAGE" --list-hunks src/pets.md)
  [[ "$output" == *"hunk 1"* ]] || return 1
  [[ "$output" == *"hunk 2"* ]] || return 1
  [[ "$output" == *"hunk 3"* ]] || return 1
}

# Eval 9: hunk:N addressing — stage hunk 2 (Tokay Gecko)
eval9() {
  "$STAGE" src/pets.md hunk:2
  local staged
  staged=$(git diff --cached src/pets.md)
  [[ "$staged" == *"Tokay Gecko"* ]] || return 1
  [[ "$staged" != *"walking by the canal"* ]] || return 1
  [[ "$staged" != *"especially koi"* ]] || return 1
}

# Eval 10: hunk:N,M — stage hunks 1 and 3 (Dogs + Koi, skip Gecko)
eval10() {
  "$STAGE" src/pets.md hunk:1,3
  local staged
  staged=$(git diff --cached src/pets.md)
  [[ "$staged" == *"walking by the canal"* ]] || return 1
  [[ "$staged" == *"especially koi"* ]] || return 1
  [[ "$staged" != *"Tokay Gecko"* ]] || return 1
}

# Eval 11: Error — hunk index out of range
eval11() {
  ! "$STAGE" src/pets.md hunk:99 2>/dev/null
}

# Eval 12: --unstage removes a specific hunk from staging
eval12() {
  # Stage everything first
  git add src/pets.md
  # Unstage just the Tokay Gecko hunk
  "$STAGE" --unstage src/pets.md hunk:2
  local staged
  staged=$(git diff --cached src/pets.md)
  # Tokay Gecko should no longer be staged
  [[ "$staged" != *"Tokay Gecko"* ]] || return 1
  # Dogs and Koi should still be staged
  [[ "$staged" == *"walking by the canal"* ]] || return 1
  [[ "$staged" == *"especially koi"* ]] || return 1
}

# Eval 13: --unstage with line numbers
eval13() {
  git add src/snacks.md
  # Unstage just the Kaya Toast line
  "$STAGE" --unstage src/snacks.md 5
  local staged
  staged=$(git diff --cached src/snacks.md)
  [[ "$staged" != *"Ya Kun"* ]] || return 1
  [[ "$staged" == *"Roti Canai"* ]] || return 1
  [[ "$staged" == *"Nam Dok Mai"* ]] || return 1
}

# Eval 14: --list-hunks --staged shows staged hunks
eval14() {
  git add src/pets.md
  local output
  output=$("$STAGE" --list-hunks --staged src/pets.md)
  [[ "$output" == *"hunk 1"* ]] || return 1
  [[ "$output" == *"hunk 2"* ]] || return 1
  [[ "$output" == *"hunk 3"* ]] || return 1
}

run_test "single hunk (Tokay Gecko)" eval1
run_test "multi-file (Dogs + Roti Canai)" eval2
run_test "split hunk (Mango only, not Roti Canai)" eval3
run_test "error: no unstaged changes" eval4
run_test "error: invalid line spec" eval5
run_test "error: no matching hunks" eval6
run_test "multi-hunk same file (Dogs + Koi, not Gecko)" eval7
run_test "--list-hunks output" eval8
run_test "hunk:N addressing (Tokay Gecko)" eval9
run_test "hunk:N,M addressing (Dogs + Koi)" eval10
run_test "error: hunk index out of range" eval11
run_test "--unstage by hunk index" eval12
run_test "--unstage by line number" eval13
run_test "--list-hunks --staged" eval14

# Eval 15: Widely-spaced hunks — stage hunk:2 from potions.md
# Regression: flush_hunk clobbers BASH_REMATCH when hunks are in separate @@ blocks
eval15() {
  "$STAGE" src/potions.md hunk:2
  local staged
  staged=$(git diff --cached src/potions.md)
  [[ "$staged" == *"bucket of pixie dust"* ]] || return 1
  [[ "$staged" != *"12 hours"* ]] || return 1
  [[ "$staged" != *"fairy salt"* ]] || return 1
}

# Eval 16: Widely-spaced hunks — stage hunk:1,3 from potions.md
# Regression: multiple separate @@ blocks with flush_hunk between each
eval16() {
  "$STAGE" src/potions.md hunk:1,3
  local staged
  staged=$(git diff --cached src/potions.md)
  [[ "$staged" == *"12 hours"* ]] || return 1
  [[ "$staged" == *"fairy salt"* ]] || return 1
  [[ "$staged" != *"bucket of pixie dust"* ]] || return 1
}

run_test "widely-spaced hunks: hunk:2 (potions)" eval15
run_test "widely-spaced hunks: hunk:1,3 (potions)" eval16

echo ""
echo "$PASS passed, $FAIL failed out of 16"
[[ $FAIL -eq 0 ]]
