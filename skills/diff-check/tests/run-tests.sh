#!/usr/bin/env bash
set -uo pipefail

# Eval suite for diff_check.py. Each case writes a change into a fresh fixture
# repo, runs the script over it, and asserts on the JSON so the assertions do not
# depend on the rendered layout.
# Usage: run-tests.sh

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHECK="$SCRIPT_DIR/scripts/diff_check.py"
SETUP="$SCRIPT_DIR/tests/setup-test-repo.sh"
PASS=0
FAIL=0

run_test() {
  local name="$1"
  local dir="/tmp/diff-check-test-$$"
  shift

  "$SETUP" "$dir" > /dev/null 2>&1
  cd "$dir" || return 1

  if "$@"; then
    echo "PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $name"
    FAIL=$((FAIL + 1))
  fi

  cd / && rm -rf "$dir"
}

# A comment added where code was removed is one finding, not one per line, and it
# carries the removed code so the caller can see what it narrates.
eval_comment_on_deletion() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  // The debug logging that used to be here was removed because it fired on
  // every row and flooded the aggregator. Nothing is emitted at this point
  // now, so log parsers expecting the "spam" prefix will not find it.
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF
  local out
  out=$("$CHECK" --json)
  [[ $(echo "$out" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))') == 1 ]] || return 1
  echo "$out" | grep -q '"kind": "comment-on-deletion"' || return 1
  echo "$out" | grep -q '"disposition": "flag"' || return 1
  echo "$out" | grep -q 'console.log' || return 1
}

# A new file contributes only added lines and never appears in `git diff`.
eval_untracked_file() {
  cat > src/fresh.ts <<'EOF'
export function fresh() {
  /* parked */
  return 1;
}
EOF
  "$CHECK" --json | grep -q '"path": "src/fresh.ts"' || return 1
}

# Unchanged code must produce nothing, or the check is noise on every run.
eval_clean_tree() {
  [[ $("$CHECK" --json) == "[]" ]] || return 1
}

# Generated output is numerically and comment dense by nature.
eval_excludes_generated() {
  mkdir -p src/generated
  cat > src/generated/api.ts <<'EOF'
/* generated, do not edit */
export const version = 1;
EOF
  [[ $("$CHECK" --json) == "[]" ]] || return 1
  "$CHECK" --json --include-generated | grep -q '"path": "src/generated/api.ts"' || return 1
}

# --staged must ignore the working tree, so a check before commit sees only what
# is about to be committed.
eval_staged_only() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  console.log("spam", rows.length);
  /* staged */
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF
  git add src/ingest.ts
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  /* unstaged */
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF
  local out
  out=$("$CHECK" --staged --json)
  echo "$out" | grep -q 'src/ingest.ts' || return 1
  echo "$out" | grep -q 'src/store.ts' && return 1
  return 0
}

# Reading a file directly rates comments that are already committed.
eval_file_mode() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  /* committed note */
  return rows;
}
EOF
  git commit -qam "add note"
  [[ $("$CHECK" --json) == "[]" ]] || return 1
  "$CHECK" --json src/ingest.ts | grep -q '"kind": "comment-added"' || return 1
}

# A shebang is not a comment, and a lone changed shebang must not be reported.
eval_shebang_not_comment() {
  cat > infra/boot.sh <<'EOF'
#!/bin/bash
set -euo pipefail
echo "booting"
EOF
  [[ $("$CHECK" --json) == "[]" ]] || return 1
}

GUARD="$SCRIPT_DIR/../../hooks/flag-guard.py"

# The Stop hook is the control the written rules were not. It must block once on a
# flag, then let the turn end, so an agent that disputes a finding is not trapped.
eval_hook_blocks_then_relents() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  // The logging that used to be here was removed because it was noisy.
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF
  local sid="eval-$$" payload first second
  # Stop attributes only to files this session edited, which PostToolUse records.
  echo "{\"hook_event_name\":\"PostToolUse\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\",\"tool_input\":{\"file_path\":\"$PWD/src/ingest.ts\"}}" | python3 "$GUARD" > /dev/null
  payload="{\"hook_event_name\":\"Stop\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\"}"
  first=$(echo "$payload" | python3 "$GUARD")
  second=$(echo "$payload" | python3 "$GUARD")
  echo "$first" | grep -q '"decision": "block"' || return 1
  echo "$second" | grep -q '"decision": "block"' && return 1
  echo "$second" | grep -q 'additionalContext' || return 1
}

# The runtime sets stop_hook_active once a hook has refused the same turn. A hook
# that ignores it ends the session dead, which is what happened on first use.
eval_hook_respects_stop_hook_active() {
  local sid="active-$$"
  echo "{\"hook_event_name\":\"PostToolUse\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\",\"tool_input\":{\"file_path\":\"$PWD/src/ingest.ts\"}}" | python3 "$GUARD" > /dev/null
  local out
  out=$(echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\",\"stop_hook_active\":true}" | python3 "$GUARD")
  [[ -z "$out" ]] || return 1
}

# A tree that was already dirty is not this session's fault, so a flag in a file
# nobody edited must never stop the turn.
eval_hook_ignores_untouched_files() {
  local out
  out=$(echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$PWD\",\"session_id\":\"untouched-$$\"}" | python3 "$GUARD")
  [[ -z "$out" ]] || return 1
}

# A file written outside the repo is never in its diff. Recording it anyway made
# every later Stop pay for a whole-tree diff that could not find anything.
eval_hook_ignores_outside_repo() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  // The logging that used to be here was removed because it was noisy.
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF
  local sid="outside-$$" out
  out=$(echo "{\"hook_event_name\":\"PostToolUse\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\",\"tool_input\":{\"file_path\":\"/tmp/elsewhere-$$.ts\"}}" | python3 "$GUARD")
  [[ -z "$out" ]] || return 1
  out=$(echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\"}" | python3 "$GUARD")
  [[ -z "$out" ]] || return 1
}

# Two flaggable changes, one in scope: only that one is reported, and an
# untracked file outside the scope stays out too.
eval_only_narrows_diff() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  // The logging that used to be here was removed because it was noisy.
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  // The query that used to be here was removed because it was slow.
  return "";
}
EOF
  cat > src/fresh.ts <<'EOF'
// The helper that used to be here was removed because nobody called it.
export const fresh = 1;
EOF
  local out
  out=$("$CHECK" --json --only src/ingest.ts)
  echo "$out" | grep -q 'src/ingest.ts' || return 1
  echo "$out" | grep -q 'src/store.ts' && return 1
  echo "$out" | grep -q 'src/fresh.ts' && return 1
  out=$("$CHECK" --json --only src/fresh.ts)
  echo "$out" | grep -q 'src/fresh.ts' || return 1
  echo "$out" | grep -q 'src/ingest.ts' && return 1
  "$CHECK" --json | grep -q 'src/store.ts' || return 1
}

# A judge finding is a candidate, not a defect, and must never stop a turn.
eval_hook_ignores_judge() {
  cat > src/store.ts <<'EOF'
export function liveQuery(name?: string) {
  // The upstream feed repeats an item across page boundaries whenever a write
  // lands mid-scan, so callers dedupe by id rather than trusting the cursor.
  return name;
}
EOF
  local out
  out=$(echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$PWD\",\"session_id\":\"judge-$$\"}" | python3 "$GUARD")
  [[ -z "$out" ]] || return 1
}

# A check that breaks the session is worse than no check.
eval_hook_never_errors() {
  echo 'not json' | python3 "$GUARD" > /dev/null 2>&1 || return 1
  echo '{"hook_event_name":"Stop","cwd":"/nonexistent"}' | python3 "$GUARD" > /dev/null 2>&1 || return 1
  [[ -z $(echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$PWD\"}" | python3 "$GUARD") ]] || return 1
}

# Generated output announces itself in a header and sits in an ordinary source
# directory, so a path pattern alone does not find it.
eval_generated_header_excluded() {
  cat > src/payload.ts <<'EOF'
/* tslint:disable */
/**
 * This file was automatically generated. DO NOT EDIT.
 */
export interface Thing {
  /**
   * A documented member.
   */
  name?: string | null;
}
EOF
  [[ $("$CHECK" --json) == "[]" ]] || return 1
  "$CHECK" --json --include-generated | grep -q 'payload.ts' || return 1
}

# Present-tense prose about absent things is not narration of a removal.
eval_present_tense_not_flagged() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  console.log("spam", rows.length);
  // @ts-expect-error a stale CMS value that is no longer an enum member
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF
  "$CHECK" --json | grep -q '"disposition": "flag"' && return 1
  return 0
}

# A deleted comment that carried a reason is a candidate, with the hunk's added
# comments alongside so the caller can see whether the reason moved.
eval_reason_deleted() {
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  // Compared in constant time because the token is a bearer credential and a
  // timing leak would let a caller recover it byte by byte.
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF
  git commit -qam "reasoned"
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  // Compare the token
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF
  local out
  out=$("$CHECK" --json)
  echo "$out" | grep -q '"kind": "reason-deleted"' || return 1
  echo "$out" | grep -q '"kept"' || return 1
  echo "$out" | grep -q 'Compare the token' || return 1
}

# Tightening a reason is the edit the check exists to reward, so a rewrite that
# keeps the reason word is not a deletion.
eval_reason_rewritten_not_reported() {
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  // Compared in constant time because the token is a bearer credential and a
  // timing leak would let a caller recover it byte by byte.
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF
  git commit -qam "reasoned"
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  // Constant time: a timing leak recovers the bearer token
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF
  "$CHECK" --json | grep -q '"kind": "reason-deleted"' && return 1
  return 0
}

# A deleted comment with no reason in it is an ordinary deletion.
eval_plain_comment_deleted_not_reported() {
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  // fetch the open reviews
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF
  git commit -qam "labelled"
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  return "SELECT id FROM review WHERE state = 'open'";
}
EOF
  [[ $("$CHECK" --json) == "[]" ]] || return 1
}

run_test "comment added where code was removed" eval_comment_on_deletion
run_test "deleted reason is a candidate" eval_reason_deleted
run_test "rewritten reason is not reported" eval_reason_rewritten_not_reported
run_test "deleted label is not reported" eval_plain_comment_deleted_not_reported
run_test "generated header excluded" eval_generated_header_excluded
run_test "present tense is not past-state narration" eval_present_tense_not_flagged
run_test "untracked file is scanned" eval_untracked_file
run_test "clean tree reports nothing" eval_clean_tree
run_test "generated paths excluded" eval_excludes_generated
run_test "--staged ignores the working tree" eval_staged_only
run_test "file mode rates committed comments" eval_file_mode
run_test "shebang is not a comment" eval_shebang_not_comment
run_test "hook blocks once, then relents" eval_hook_blocks_then_relents
run_test "hook respects stop_hook_active" eval_hook_respects_stop_hook_active
run_test "hook ignores files nobody edited" eval_hook_ignores_untouched_files
run_test "hook ignores edits outside the repo" eval_hook_ignores_outside_repo
run_test "--only narrows the diff to given paths" eval_only_narrows_diff

# Blocking and mentioning are different powers. A multi-line judge finding on the
# file just written is reported, and still does not block the turn.
eval_hook_reports_judge_on_write() {
  cat > src/store.ts <<'EOF'
export function liveQuery(name: string) {
  // The upstream feed repeats an item across page boundaries whenever a write
  // lands mid-scan, so a caller that pages through this has to dedupe by id
  // rather than trusting the cursor to be stable.
  return name.trim();
}
EOF
  local sid="report-$$" out
  out=$(echo "{\"hook_event_name\":\"PostToolUse\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\",\"tool_input\":{\"file_path\":\"$PWD/src/store.ts\"}}" | python3 "$GUARD")
  echo "$out" | grep -q 'to rate, not blocking' || return 1
  echo "$out" | grep -q '"decision": "block"' && return 1
  # Stop is the blocking event and must stay flags-only.
  out=$(echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$PWD\",\"session_id\":\"$sid\"}" | python3 "$GUARD")
  [[ -z "$out" ]] || return 1
}

# A one-line comment is cheap to read; raising every one of them is the noise
# that gets a check muted.
eval_hook_skips_short_judge() {
  cat > src/store.ts <<'EOF'
export function liveQuery(name: string) {
  // The upstream feed repeats items across pages.
  return name.trim();
}
EOF
  local out
  out=$(echo "{\"hook_event_name\":\"PostToolUse\",\"cwd\":\"$PWD\",\"session_id\":\"short-$$\",\"tool_input\":{\"file_path\":\"$PWD/src/store.ts\"}}" | python3 "$GUARD")
  [[ -z "$out" ]] || return 1
}

FLAGGED='export function ingest(rows: string[]) {
  // The logging that used to be here was removed because it was noisy.
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}'

# Prints "path:line:kind:disposition" per finding, so assertions read paths as
# git wrote them rather than as JSON escaped them.
findings_of() {
  python3 -c 'import json,sys
for f in json.load(sys.stdin): print(":".join(str(f[k]) for k in ("path", "line", "kind", "disposition")))'
}

# git quotes a non-ASCII path unless told not to, and a quoted path is one
# nothing downstream recognises.
eval_non_ascii_path() {
  printf 'console.log(1);\nexport const a = 1;\n' > "src/é.ts"
  git add -A && git commit -qm "accent"
  printf '// The logging that used to be here was removed because it was noisy.\nexport const a = 1;\n' > "src/é.ts"
  printf '// The helper that used to be here was removed because nobody called it.\nexport const b = 1;\n' > "src/ü.ts"
  local out
  out=$("$CHECK" --json | findings_of)
  echo "$out" | grep -q '^src/é.ts:1:comment-on-deletion:flag$' || return 1
  echo "$out" | grep -q '^src/ü.ts:1:' || return 1
}

# User config must not change the header format the parser reads.
eval_mnemonic_prefix() {
  echo "$FLAGGED" > src/ingest.ts
  local config
  for config in diff.mnemonicPrefix diff.noprefix; do
    GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="$config" GIT_CONFIG_VALUE_0=true "$CHECK" --json \
      | findings_of | grep -q '^src/ingest.ts:2:comment-on-deletion:flag$' || return 1
  done
}

# Context lines from diff.interHunkContext would shift every later line number.
eval_inter_hunk_context() {
  git config diff.interHunkContext 10
  cat > src/ingest.ts <<'EOF'
// top
export function ingest(rows: string[]) {
  const seen = new Set<string>();
  // The logging that used to be here was removed because it was noisy.
  return rows.filter((r) => !seen.has(r));
}
EOF
  local out
  out=$("$CHECK" --json | findings_of)
  echo "$out" | grep -q '^src/ingest.ts:4:comment-on-deletion:' || return 1
}

# A deleted `-- ` SQL comment arrives as `--- ...` inside a hunk, which is not a
# file header there.
eval_sql_reason_deleted() {
  cat > src/q.sql <<'EOF'
SELECT 1;
-- Compared in constant time because a timing leak would expose the token.
SELECT token FROM sessions;
EOF
  git add -A && git commit -qm "sql"
  printf 'SELECT 1;\nSELECT token FROM sessions;\n' > src/q.sql
  "$CHECK" --json | findings_of | grep -q '^src/q.sql:.*:reason-deleted:judge$' || return 1
}

# An added `++ i;` arrives as `+++ ...` and once discarded the rest of its hunk.
eval_plus_plus_line() {
  printf 'void f(int i) {\nint j = 0;\nreturn;\n}\n' > src/f.c
  git add -A && git commit -qm "c"
  printf 'void f(int i) {\n++ i;\n// The counter that used to be here was removed because it overflowed.\nreturn;\n}\n' > src/f.c
  "$CHECK" --json | findings_of | grep -q '^src/f.c:3:comment-on-deletion:flag$' || return 1
}

# A pathspec is a glob unless told otherwise: `f[1].ts` also matches `f1.ts`.
eval_bracket_filename() {
  printf '// The helper that used to be here was removed because nobody called it.\nexport const a = 1;\n' > src/f1.ts
  printf '// The helper that used to be here was removed because nobody called it.\nexport const b = 1;\n' > 'src/f[1].ts'
  local out
  out=$("$CHECK" --json --only 'src/f[1].ts' | findings_of)
  echo "$out" | grep -q '^src/f\[1\].ts:' || return 1
  echo "$out" | grep -q '^src/f1.ts:' && return 1
  return 0
}

# Blocks once from a Stop payload whose cwd is $1, after an edit to $2.
hook_blocks_in() {
  local cwd="$1" file="$2" sid="where-$$-$RANDOM"
  echo "{\"hook_event_name\":\"PostToolUse\",\"cwd\":\"$cwd\",\"session_id\":\"$sid\",\"tool_input\":{\"file_path\":\"$file\"}}" | python3 "$GUARD" | grep -q 'flagged' || return 1
  echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$cwd\",\"session_id\":\"$sid\"}" | python3 "$GUARD" | grep -q '"decision": "block"' || return 1
}

# A linked worktree has a `.git` file, not a directory.
eval_hook_in_worktree() {
  local wt="$PWD-wt"
  git worktree add -q --detach "$wt" || return 1
  echo "$FLAGGED" > "$wt/src/ingest.ts"
  local ok=0
  hook_blocks_in "$wt" "$wt/src/ingest.ts" || ok=1
  git worktree remove --force "$wt"
  return $ok
}

# A session started below the top level has no `.git` at its cwd, and diff
# paths stay relative to the top level.
eval_hook_in_subdir() {
  echo "$FLAGGED" > src/ingest.ts
  hook_blocks_in "$PWD/src" "$PWD/src/ingest.ts" || return 1
  (cd src && "$CHECK" --json | findings_of | grep -q '^src/ingest.ts:2:') || return 1
}

# The edited list names files, so it lives in a directory only its owner reads.
eval_hook_state_private() {
  echo "$FLAGGED" > src/ingest.ts
  echo "{\"hook_event_name\":\"PostToolUse\",\"cwd\":\"$PWD\",\"session_id\":\"private-$$\",\"tool_input\":{\"file_path\":\"$PWD/src/ingest.ts\"}}" | python3 "$GUARD" > /dev/null
  local dir
  dir=$(python3 -c 'import os,tempfile; print(os.path.join(tempfile.gettempdir(), f"diff-check-{os.getuid()}"))')
  [[ -f "$dir/private-$$.edited" ]] || return 1
  [[ $(stat -c %a "$dir") == 700 ]] || return 1
  rm -f "$dir/private-$$.edited"
}

run_test "non-ASCII paths are read unquoted" eval_non_ascii_path
run_test "diff prefix config does not change paths" eval_mnemonic_prefix
run_test "inter-hunk context does not shift lines" eval_inter_hunk_context
run_test "deleted SQL reason is a candidate" eval_sql_reason_deleted
run_test "added ++ line keeps its hunk" eval_plus_plus_line
run_test "bracket filename matches literally" eval_bracket_filename
run_test "hook works in a linked worktree" eval_hook_in_worktree
run_test "hook works from a subdirectory" eval_hook_in_subdir
run_test "hook state is private to the user" eval_hook_state_private
run_test "hook ignores judge findings" eval_hook_ignores_judge
run_test "hook never breaks the session" eval_hook_never_errors
run_test "hook reports a judge finding on write" eval_hook_reports_judge_on_write
run_test "hook skips a one-line judge finding" eval_hook_skips_short_judge

echo
echo "$PASS passed, $FAIL failed"
[[ $FAIL == 0 ]]
