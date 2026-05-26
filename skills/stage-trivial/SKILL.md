---
name: stage-trivial
description: "Scan git diffs and automatically stage only the trivially correct, non-ambiguous changes — lint fixes, unused import removals, formatting, typo corrections, dead code removal, observability additions, and mechanical sweeps repeated identically across files. Leaves anything design-related or ambiguous unstaged. Use this skill when the user says 'stage the obvious stuff', 'stage trivial changes', 'stage the safe diffs', 'cherry-pick the lint fixes', 'stage what's obviously correct', or wants to separate mechanical cleanup from substantive changes before committing. Also trigger when the user has a messy working tree and wants to triage what's safe to commit without review."
---

# Stage Trivial Changes

Scan the unstaged git diff, classify every hunk as trivial or non-trivial, and stage only the trivially correct ones. Never commit — just stage. Produce a summary so the user can see what was staged and what was left, with the evidence behind each call.

## By evidence, not reflex

The single rule the rest of this skill exists to enforce: every classification — both "trivial" and "skip" — must be a conclusion drawn from evidence found in the diff and the surrounding code. Not a reflex driven by what the hunk superficially looks like.

- **"Trivial" by evidence** means: the same change appears identically across N sibling files, the imported symbol is a known export, the call extends a pattern already used several times in the file. The verdict came from looking.
- **"Skip" by evidence** means: the imported module turns out to define a new abstraction, the one-liner is the client half of a substantive change in another file, the hunk introduces a >10-line behavioural effect. The verdict came from looking.

"I haven't looked yet" is never a verdict — it is the cue to run one of the checks in the Evidence sources section. Skipping a hunk because it looks unfamiliar, without checking what it actually does, is the failure mode this skill exists to prevent. Default-to-skip turns the tool into a no-op.

Reflexes to catch in yourself:

- "Config change → skip" without reading what the field does.
- "Adds code → skip" without reading what the code does.
- "When in doubt → skip" without trying to resolve the doubt first.

## Look across the diff before classifying any single hunk

This step is mandatory and comes before per-file classification.

1. `git diff --name-only` + `git status --short` for the changed-file set as a whole.
2. Scan the diffs at a glance — `git diff --stat` plus a quick read of each file's hunks — and identify three categories:
   - **Repeated patterns**: the same line or block added in three or more files with the same shape. These are sweeps; treat the set as one decision, not N separate decisions.
   - **Coupled pairs**: a small change in file A whose meaning depends on a larger change in file B (same symbol renamed on both sides, same contract changed at both endpoints, an import added in one file matching a new export in another). Mark the pair; never split a coupled refactor.
   - **Isolated lonely changes**: hunks with no analogue elsewhere in the diff. These warrant the most scrutiny — isolation is the signal that the change was hand-placed and may carry intent.
3. Only then, work file by file with the whole-diff context already in mind.

## Evidence sources, cheapest first

When a hunk is borderline — not clear-cut in either direction — use these to gain confidence. They are ordered by cost; stop as soon as one resolves the question.

1. **The rest of the diff.** Is this change repeated in sibling files? Three or more identical occurrences = sweep = trivial. Verify the lines are genuinely identical (don't assume "looks the same"); count.
2. **The file itself.** Does this change extend a pattern already present in the file? A new `logger.warn(...)` next to four existing `logger.warn(...)` calls is a continuation, not an introduction.
3. **Imports the hunk references.** If a hunk adds `import { foo } from './bar'`, open `./bar` and read what `foo` is before classifying the usage. Imports + usage together resolve ambiguity neither resolves alone. A `logger.warn(...)` could be a real logger or `console.warn` aliased; the import tells you which. A new helper import could be a tiny utility or a 200-line new abstraction; reading the source decides which.
4. **`git grep` for the symbol.** Count existing usages of the new call/import elsewhere in the codebase. Zero usages = the change is introducing a new thing; three or more = it's joining an established convention.
5. **Five to ten lines of context around the hunk.** Sometimes the meaning is local — the surrounding code makes the intent clear.

If none of these resolves the doubt, then skip — but only because the evidence ran out, not because looking felt like work.

## What counts as trivial

Changes where the evidence above confirms there is no behavioural risk:

- **Unused import removal** — an import that was deleted and nothing else in the hunk depends on it.
- **Formatting / whitespace** — indentation, trailing whitespace, trailing commas, semicolon insertion/removal, line wrapping that doesn't change logic.
- **Lint auto-fixes** — changes that look like they came from a lint `--fix` (`let` → `const` for never-reassigned variables, removing flagged type assertions).
- **Typo corrections in strings/comments** — obvious spelling fixes where the correct word is unambiguous.
- **Dead code removal** — deleting commented-out code, removing unreachable branches the compiler/linter flagged.
- **Import reordering** — imports moved around but not added or removed.
- **Generated file timestamps** — "Generated on …" header lines in codegen output (stage the timestamp hunk even if other hunks in the same generated file are non-trivial).
- **Uniform sweeps** — the same change applied identically across three or more files. The repetition itself is the evidence: it's a mechanical pass, not a per-file decision. Count occurrences; verify the added lines really are identical (not just similar) before staging the set.
- **Observability additions** — adding a logger call via the project's logger, an error-reporting call (e.g. `captureException`), a tracing span, or a metrics increment, with no control-flow change in the same hunk. These observe state; they don't change it. Verify via imports that the call resolves to an actual observability function (see Evidence sources, step 3).
- **Observability config toggles** — flipping a known observability flag to its standard value (`enabled: true`, trace propagation on, sample-rate adjustment, log-level setting), provided the underlying capability is already wired up. These don't change product behaviour; they change what is observed.

## What is NOT trivial — skip these

Evidence shows real intent, behavioural change, or coupling:

- Any new file (likely waiting for review).
- Any hunk that adds new logic, functions, types, or exports that aren't part of an identified sweep.
- Any hunk that changes control flow, even slightly.
- Any hunk that modifies test assertions or expected values.
- Any hunk that changes API contracts, schemas, or database queries.
- Any hunk that renames public symbols.
- Any hunk that changes configuration values controlling product behaviour (route configs, feature flags, security policy, timeouts that affect what runs) — distinct from observability toggles above.
- **Throwaway debug logging** — `console.log`, `console.error`, raw `print`, log calls with placeholder messages ("here", "got x", `JSON.stringify(...)`), or log lines scattered without a pattern. Signs of in-flight debugging that shouldn't be committed.
- **Client half of a coupled refactor** — a small change whose meaning only becomes clear once paired with a larger change in another file. Don't classify in isolation; identify the pair, treat both as one substantive change, and skip them for joint review.
- **Mixed hunks** — a hunk that fuses trivial and non-trivial changes together (a formatting fix on the same line as a logic change). Classify the whole hunk as non-trivial. If the trivial part can be peeled off cleanly via the `stage-hunk` skill, prefer that.
- **Merge conflict markers** (UU status files) — never touch.

## Process

### 1. Inventory the whole diff

- `git diff --name-only` + `git status --short` for the file list and statuses.
- Skip up front: UU conflicts, fully-staged files.
- Run the cross-file scan from "Look across the diff before classifying any single hunk" — identify sweeps, coupled pairs, and isolated lonely changes.

### 2. Classify each file's hunks with whole-diff context

For each file with unstaged changes:

1. `git diff -U5 -- <file>` — full diff with context.
2. For each hunk, apply the "by evidence, not reflex" rule:
   - If it fits a named trivial pattern AND the evidence confirms it, stage.
   - If it fits a named skip pattern AND the evidence confirms it, skip.
   - If borderline, run the evidence checks (cheapest first) until a verdict emerges.
3. Don't conclude before looking. "I'm not sure" means "I haven't checked yet" — go check.

### 3. Stage

- All hunks in a file are trivial → `git add <file>`.
- Some hunks trivial, some not → invoke the `stage-hunk` skill with a description of which hunks to stage.
- No hunks trivial → leave the file untouched.

### 4. Report

After processing all files, present two lists. Each entry names the evidence used to classify, not just the category.

**Staged**, grouped by classification category:

```
Staged:
  uniform sweep:    <N files> — same M-line change identical across <count> files
  observability:    <file> — adds logger call; logger import confirmed, K× existing usage in same file
  formatting:       <file> (hunks 1, 3) — whitespace only
  imports:          <file> — unused import removal
  typo:             <file> (hunk 2)
  generated:        <file> — generated-timestamp header only
```

**Skipped**, with the evidence behind each call:

```
Skipped:
  <file> — adds K-line behavioural effect (named effect: reconnect handler, error pipeline expansion, etc.)
  <pair: file A + file B> — coupled refactor; A's change only meaningful given B's contract change
  <file> — modifies route config / DB query / API contract
  <file> — merge conflict (UU)
```

One line per file unless a file mixes staged and skipped hunks — then list per hunk.

If a file is left for the user to review, the line must say *why* in evidence terms — not "looks risky" but "modifies an API contract", "adds a non-observability effect of K lines", or "client half of a coupled change with <other file>".

## Performance

Process files in batches rather than one at a time. Read all diffs first (the whole-diff scan), classify, then stage in bulk. Avoid re-reading files already inspected in the cross-file scan.

## Arguments

- `--dry-run` — show what would be staged without actually staging anything.