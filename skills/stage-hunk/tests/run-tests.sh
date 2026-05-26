#!/usr/bin/env bash
set -euo pipefail

# Runs stage-hunk eval scenarios against the script directly.
# Usage: run-tests.sh

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$SCRIPT_DIR/scripts/stage_hunk.py"
SETUP="$SCRIPT_DIR/tests/setup-test-repo.sh"
PASS=0
FAIL=0

# Extract only added/removed lines from a diff (dropping the +++/--- file
# headers) so substring assertions match real changes, not the unchanged
# context lines that surround them. Essential for dense fixtures where
# every neighbouring line also contains a searched-for word.
change_lines() {
  grep -E '^[-+]' | grep -vE '^(--- |\+\+\+ )' || true
}

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

# Eval 1: Single hunk — stage only Tokay Gecko (hunk 2)
eval1() {
  "$STAGE" src/pets.md 2
  local staged
  staged=$(git diff --cached src/pets.md)
  [[ "$staged" == *"Tokay Gecko"* ]] || return 1
  [[ "$staged" != *"walking by the canal"* ]] || return 1
  [[ "$staged" != *"especially koi"* ]] || return 1
}

# Eval 2: Multi-file — Dogs (pets hunk 1) + Roti Canai (snacks hunk 2)
eval2() {
  "$STAGE" src/pets.md 1
  "$STAGE" src/snacks.md 2
  local staged
  staged=$(git diff --cached)
  [[ "$staged" == *"walking by the canal"* ]] || return 1
  [[ "$staged" == *"Roti Canai"* ]] || return 1
  [[ "$staged" != *"Tokay Gecko"* ]] || return 1
  [[ "$staged" != *"Ya Kun"* ]] || return 1
  [[ "$staged" != *"Nam Dok Mai"* ]] || return 1
}

# Eval 3: Split hunk — Mango Sticky Rice (snacks hunk 3) only, not Roti Canai
eval3() {
  "$STAGE" src/snacks.md 3
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

# Eval 7: Multi-hunk same file — stage Dogs (1) and Koi (3) but not Tokay Gecko (2)
eval7() {
  "$STAGE" src/pets.md 1 3
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

# Eval 9: integer addressing — stage hunk 2 (Tokay Gecko)
eval9() {
  "$STAGE" src/pets.md 2
  local staged
  staged=$(git diff --cached src/pets.md)
  [[ "$staged" == *"Tokay Gecko"* ]] || return 1
  [[ "$staged" != *"walking by the canal"* ]] || return 1
  [[ "$staged" != *"especially koi"* ]] || return 1
}

# Eval 10: multiple integers — stage hunks 1 and 3 (Dogs + Koi, skip Gecko)
eval10() {
  "$STAGE" src/pets.md 1 3
  local staged
  staged=$(git diff --cached src/pets.md)
  [[ "$staged" == *"walking by the canal"* ]] || return 1
  [[ "$staged" == *"especially koi"* ]] || return 1
  [[ "$staged" != *"Tokay Gecko"* ]] || return 1
}

# Eval 11: Error — hunk index out of range
eval11() {
  ! "$STAGE" src/pets.md 99 2>/dev/null
}

# Eval 12: --unstage removes a specific hunk from staging
eval12() {
  # Stage everything first
  git add src/pets.md
  # Unstage just the Tokay Gecko hunk
  "$STAGE" --unstage src/pets.md 2
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
  # Unstage just the Kaya Toast line (snacks hunk 1)
  "$STAGE" --unstage src/snacks.md 1
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
  "$STAGE" src/potions.md 2
  local staged
  staged=$(git diff --cached src/potions.md)
  [[ "$staged" == *"bucket of pixie dust"* ]] || return 1
  [[ "$staged" != *"12 hours"* ]] || return 1
  [[ "$staged" != *"fairy salt"* ]] || return 1
}

# Eval 16: Widely-spaced hunks — stage hunk:1,3 from potions.md
# Regression: multiple separate @@ blocks with flush_hunk between each
eval16() {
  "$STAGE" src/potions.md 1 3
  local staged
  staged=$(git diff --cached src/potions.md)
  [[ "$staged" == *"12 hours"* ]] || return 1
  [[ "$staged" == *"fairy salt"* ]] || return 1
  [[ "$staged" != *"bucket of pixie dust"* ]] || return 1
}

run_test "widely-spaced hunks: hunk:2 (potions)" eval15
run_test "widely-spaced hunks: hunk:1,3 (potions)" eval16

# --- Pure-deletion scenarios (taiwan.md) ---
# taiwan.md U0 hunks: 1=Beef Noodle Soup (del), 2=Bubble Tea (mod),
# 3=Stinky Tofu (del), 4=Milkfish Belly Soup (add), 5=Sun Cake (del, EOF).
# U3 merges all five into a single hunk, which is what trips up
# index-based pure-deletion handling.

# Eval 17: Two non-adjacent pure deletions (1, 3) with the modification (2)
# between them left unselected.
eval17() {
  "$STAGE" src/taiwan.md 1 3
  local staged
  staged=$(git diff --cached src/taiwan.md | change_lines)
  [[ "$staged" == *"Beef Noodle Soup"* ]] || return 1
  [[ "$staged" == *"Stinky Tofu"* ]] || return 1
  [[ "$staged" != *"Bubble Tea"* ]] || return 1
  [[ "$staged" != *"Milkfish"* ]] || return 1
  [[ "$staged" != *"Sun Cake"* ]] || return 1
}

# Eval 18: Pure deletion at the very bottom of the file (EOF boundary).
eval18() {
  "$STAGE" src/taiwan.md 5
  local staged
  staged=$(git diff --cached src/taiwan.md | change_lines)
  [[ "$staged" == *"Sun Cake"* ]] || return 1
  [[ "$staged" != *"Beef Noodle Soup"* ]] || return 1
  [[ "$staged" != *"Stinky Tofu"* ]] || return 1
  [[ "$staged" != *"Bubble Tea"* ]] || return 1
  [[ "$staged" != *"Milkfish"* ]] || return 1
}

# Eval 19: Pure deletion adjacent to a selected addition — select only the
# addition (4); the neighbouring Sun Cake deletion must stay unstaged.
eval19() {
  "$STAGE" src/taiwan.md 4
  local staged
  staged=$(git diff --cached src/taiwan.md | change_lines)
  [[ "$staged" == *"Milkfish"* ]] || return 1
  [[ "$staged" != *"Sun Cake"* ]] || return 1
  [[ "$staged" != *"Beef Noodle Soup"* ]] || return 1
  [[ "$staged" != *"Stinky Tofu"* ]] || return 1
  [[ "$staged" != *"Bubble Tea"* ]] || return 1
}

# Eval 20: All three pure deletions (1, 3, 5) at once — the original repro.
# Modification (2) and addition (4) must not leak in.
eval20() {
  "$STAGE" src/taiwan.md 1 3 5
  local staged
  staged=$(git diff --cached src/taiwan.md | change_lines)
  [[ "$staged" == *"Beef Noodle Soup"* ]] || return 1
  [[ "$staged" == *"Stinky Tofu"* ]] || return 1
  [[ "$staged" == *"Sun Cake"* ]] || return 1
  [[ "$staged" != *"Bubble Tea"* ]] || return 1
  [[ "$staged" != *"Milkfish"* ]] || return 1
  # The unselected changes must remain in the working tree.
  local unstaged
  unstaged=$(git diff src/taiwan.md | change_lines)
  [[ "$unstaged" == *"Bubble Tea"* ]] || return 1
  [[ "$unstaged" == *"Milkfish"* ]] || return 1
}

# Eval 21: Unstage mirror — stage everything, then unstage one pure
# deletion (1, Beef Noodle Soup); the rest stays staged.
eval21() {
  git add src/taiwan.md
  "$STAGE" --unstage src/taiwan.md 1
  local staged
  staged=$(git diff --cached src/taiwan.md | change_lines)
  [[ "$staged" != *"Beef Noodle Soup"* ]] || return 1
  [[ "$staged" == *"Stinky Tofu"* ]] || return 1
  [[ "$staged" == *"Sun Cake"* ]] || return 1
  [[ "$staged" == *"Milkfish"* ]] || return 1
  [[ "$staged" == *"extra pearls"* ]] || return 1
  # Beef Noodle Soup deletion should be back in the working tree.
  local unstaged
  unstaged=$(git diff src/taiwan.md | change_lines)
  [[ "$unstaged" == *"Beef Noodle Soup"* ]] || return 1
}

run_test "pure-deletions 1,3 skip modification (taiwan)" eval17
run_test "pure-deletion at EOF boundary (taiwan)" eval18
run_test "addition adjacent to deletion (taiwan)" eval19
run_test "three pure-deletions 1,3,5 (taiwan)" eval20
run_test "--unstage one pure-deletion (taiwan)" eval21

# Eval 22: Cross-hunk header coordinates (dup.md). Stage hunk 1 — region A's
# PIVOT change at line 5 — while an identical block (region B, PIVOT at line 16)
# sits below. If an emitted hunk carries the wrong @@ start, git relocates the
# change onto region B. Assert it landed on region A and was actually staged.
eval22() {
  "$STAGE" src/dup.md 1
  local staged at
  staged=$(git diff --cached src/dup.md)
  echo "$staged" | grep -q '^+PIVOT_NEW' || return 1
  # Hunk must anchor in region A (old line <= 8), not region B (~13).
  at=$(echo "$staged" | grep -oE '^@@ -[0-9]+' | grep -oE '[0-9]+' | head -1)
  [[ -n "$at" && "$at" -le 8 ]] || return 1
  # Region A's change must now be staged, so it is gone from the unstaged diff.
  ! git diff src/dup.md | grep -q '^+PIVOT_NEW'
}
run_test "cross-hunk header coords land on right block (dup)" eval22

echo ""
echo "$PASS passed, $FAIL failed out of 22"
[[ $FAIL -eq 0 ]]
