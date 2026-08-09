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

# A JSDoc block above a local is a line comment in the wrong syntax; above an
# export, an interface member or an enum member it is correct and must not fire.
eval_jsdoc_misuse() {
  cat > src/ingest.ts <<'EOF'
/** Deduplicates the incoming rows. */
export function ingest(rows: string[]) {
  console.log("spam", rows.length);
  const seen = new Set<string>();
  /**
   * FYI this runs before validation.
   */
  const unique = rows.filter((r) => !seen.has(r));
  return unique;
}
EOF
  local out
  out=$("$CHECK" --json)
  echo "$out" | grep -q '"kind": "jsdoc-misuse"' || return 1
  [[ $(echo "$out" | grep -c '"kind": "jsdoc-misuse"') == 1 ]] || return 1
}

eval_bare_block() {
  cat > src/ingest.ts <<'EOF'
export function ingest(rows: string[]) {
  console.log("spam", rows.length);
  /* order matters */
  const seen = new Set<string>();
  return rows.filter((r) => !seen.has(r));
}
EOF
  "$CHECK" --json | grep -q '"kind": "bare-block"' || return 1
}

eval_negated_state() {
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  return "SELECT id FROM review WHERE state <> 'abandoned'";
}
EOF
  local out
  out=$("$CHECK" --json)
  echo "$out" | grep -q '"kind": "negated-state"' || return 1
  echo "$out" | grep -q '"disposition": "flag"' || return 1
}

eval_sentinel() {
  cat > src/store.ts <<'EOF'
export function liveQuery(name?: string) {
  const key = name ?? "";
  return key;
}
EOF
  "$CHECK" --json | grep -q '"kind": "sentinel"' || return 1
}

eval_shell_default() {
  cat > infra/boot.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
bind_host="${BIND_HOST:-127.0.0.10}"
echo "$bind_host"
EOF
  "$CHECK" --json | grep -q '"kind": "shell-default"' || return 1
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
  "$CHECK" --json src/ingest.ts | grep -q '"kind": "bare-block"' || return 1
}

# --comments must drop the code checks, so a comment review is not diluted.
eval_comments_only() {
  cat > src/store.ts <<'EOF'
export function liveQuery() {
  // a note
  return "SELECT id FROM review WHERE state <> 'abandoned'";
}
EOF
  "$CHECK" --json | grep -q '"kind": "negated-state"' || return 1

  local out
  out=$("$CHECK" --comments --json)
  echo "$out" | grep -q '"kind": "comment-added"' || return 1
  echo "$out" | grep -q '"kind": "negated-state"' && return 1
  return 0
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

# Prose that quotes a pattern is not an instance of it. Documentation describing
# `state <> 'x'` or `?? ""` must not be reported as committing them.
eval_prose_not_code_checked() {
  cat > NOTES.md <<'EOF'
# Notes

Avoid `state <> 'abandoned'` in a query, and avoid `const a = b ?? "";`
because a sentinel hides the missing value. Use `${VAR:-default}` sparingly.
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

# A judge finding is a candidate, not a defect, and must never stop a turn.
eval_hook_ignores_judge() {
  cat > src/store.ts <<'EOF'
export function liveQuery(name?: string) {
  return name ?? "";
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

# JSDoc on interface and enum members is correct, and a generated payload file is
# full of it. Flagging those produced 74 findings on first real use.
eval_jsdoc_on_members_is_fine() {
  cat > src/types.ts <<'EOF'
export interface Promo {
  id: number;
  /**
   * Leave off until the advertisement is ready to go live.
   */
  enabled?: boolean | null;
}

export enum Ids {
  Card,
  /** @deprecated - not used */
  Container,
}
EOF
  "$CHECK" --json | grep -q '"disposition": "flag"' && return 1
  return 0
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

run_test "comment added where code was removed" eval_comment_on_deletion
run_test "prose is not code checked" eval_prose_not_code_checked
run_test "JSDoc on interface and enum members is fine" eval_jsdoc_on_members_is_fine
run_test "generated header excluded" eval_generated_header_excluded
run_test "present tense is not past-state narration" eval_present_tense_not_flagged
run_test "JSDoc on a local, not on the export" eval_jsdoc_misuse
run_test "bare block comment" eval_bare_block
run_test "negated state predicate" eval_negated_state
run_test "sentinel fallback" eval_sentinel
run_test "shell default for a required value" eval_shell_default
run_test "untracked file is scanned" eval_untracked_file
run_test "clean tree reports nothing" eval_clean_tree
run_test "generated paths excluded" eval_excludes_generated
run_test "--staged ignores the working tree" eval_staged_only
run_test "file mode rates committed comments" eval_file_mode
run_test "--comments drops code checks" eval_comments_only
run_test "shebang is not a comment" eval_shebang_not_comment
run_test "hook blocks once, then relents" eval_hook_blocks_then_relents
run_test "hook respects stop_hook_active" eval_hook_respects_stop_hook_active
run_test "hook ignores files nobody edited" eval_hook_ignores_untouched_files
# The block that prompted these two checks: correctly placed on an export, so
# placement says nothing, while the ranked list is the branches below it in
# English and drifts silently when one is reordered.
eval_comment_list() {
  cat > src/format.ts <<'EOF'
/**
 * The one place a caught value becomes a sentence. Precedence:
 *
 * 1. this surface's copy for the error's `reason`
 * 2. a `LocalisedMessage` the server authored
 * 3. field/quota violations
 * 4. the bare `reason` slug, which names the condition
 * 5. generic
 */
export function useErrorFormatter(reasons?: string) {
  return reasons ?? "generic";
}
EOF
  local out
  out=$("$CHECK" --json)
  echo "$out" | grep -q '"kind": "comment-list"' || return 1
  echo "$out" | grep -q '"disposition": "flag"' || return 1
}

# Prose, no list, but several times the one-or-two sentences the standard allows.
eval_comment_essay() {
  cat > src/format.ts <<'EOF'
/**
 * Formats a caught value for display. The precedence was chosen after a long
 * discussion about which source reads best when several are present at once.
 * Copy defined on the surface itself wins, because it is the most specific.
 * A server-authored message comes next, since it has already been localised.
 * Violations follow, then the raw slug, then a generic fallback string.
 * None of this is visible from the signature, which is why it is written here.
 * The reader should know all of it before changing anything below.
 */
export function formatError(reason?: string) {
  return reason ?? "generic";
}
EOF
  "$CHECK" --json | grep -q '"kind": "comment-essay"' || return 1
}

# The checks must not fire on a comment that obeys the standard, or they become
# the noise they exist to prevent.
eval_short_jsdoc_is_fine() {
  cat > src/format.ts <<'EOF'
/** The server sends a slug, never a sentence. */
export function formatError(reason?: string) {
  return reason ?? "generic";
}
EOF
  "$CHECK" --json | grep -q '"disposition": "flag"' && return 1
  return 0
}

# A licence banner is long by nature and says nothing about the code below it.
eval_banner_not_essay() {
  cat > src/vendor.ts <<'EOF'
/*!
 * Copyright (c) 2019 Example Corp
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met.
 * Neither the name of the copyright holder nor the names of contributors may
 * be used to endorse products derived from this software.
 */
export const VERSION = "1.0.0";
EOF
  "$CHECK" --json | grep -q '"disposition": "flag"' && return 1
  return 0
}

# In a shell-like file an enumerated comment is usually a commented-out setting,
# not the ranked restatement this check is about.
eval_shell_list_not_flagged() {
  cat > deploy.sh <<'EOF'
#!/usr/bin/env bash
# Optional overrides:
# - REGION sets the target
# - TIER sets the plan
echo "deploying"
EOF
  "$CHECK" --json | grep -q '"kind": "comment-list"' && return 1
  return 0
}

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

run_test "hook ignores judge findings" eval_hook_ignores_judge
run_test "hook never breaks the session" eval_hook_never_errors
run_test "ranked list in a well-placed JSDoc" eval_comment_list
run_test "block far past one or two sentences" eval_comment_essay
run_test "short JSDoc on an export is fine" eval_short_jsdoc_is_fine
run_test "licence banner is not an essay" eval_banner_not_essay
run_test "shell commented-out settings are not a list" eval_shell_list_not_flagged
run_test "hook reports a judge finding on write" eval_hook_reports_judge_on_write
run_test "hook skips a one-line judge finding" eval_hook_skips_short_judge

echo
echo "$PASS passed, $FAIL failed"
[[ $FAIL == 0 ]]
