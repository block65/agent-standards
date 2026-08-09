---
name: stage-trivial
description: "Scan git diffs and stage only the changes that are self-evidently correct and intentional in context: changes a reviewer would have nothing to deliberate on. Covers lint fixes, formatting, typos, dead code, observability, uniform sweeps, AND self-evidently complete additions like new dev-harness pages wired up via import + menu entry + new file, testid sweeps, mount-marker additions, AGENTS.md pointers. Leaves anything requiring reviewer judgment unstaged: API contract changes, secret rotations, schema requirement changes, algorithm changes, config values the reviewer must weigh, code smells. Use this skill when the user says 'stage the obvious stuff', 'stage trivial changes', 'stage the safe diffs', 'cherry-pick the lint fixes', 'stage what's obviously correct', or wants to triage a messy working tree before committing."
---

# Stage Trivial Changes

Scan the unstaged git diff, classify every hunk, and stage only the ones that are **self-evidently correct and intentional in context**. Never commit; only stage. Produce a summary so the user can see what was staged and what was left, with the evidence behind each call.

## The reviewer-judgment test

The criterion is not "is this small or mechanical?" but **"would a reviewer have anything to deliberate on?"** Stage when the answer is no: the change is self-evidently a complete intentional unit. Skip when the answer is yes: the change encodes a design choice, a value judgement, or a contract change the reviewer must weigh. Equivalently, design-vs-wiring: when the design lives _here_ (a new API shape, schema field, algorithm), skip, because the reviewer must judge the design. When the design is already decided elsewhere and this diff just wires it up consistently, stage, because the reviewer would only check the wiring, and the diff shows it.

"Trivial" means **trivial-for-a-reviewer**, not trivial-in-size. New code, new files, and coupled multi-file changes can all be stageable: the coupling of a clear additive unit (new page + import + menu entry + render line) is often what makes it self-evidently complete. A one-character config edit (`200` → `204`, an alphabet swap, a TTL bump) can be a design choice that needs review.

## By evidence, not reflex

Every classification, stage _and_ skip alike, must be a conclusion drawn from looking at the diff and the surrounding code, not a reflex driven by what the hunk superficially looks like. "I haven't looked yet" is never a verdict: default-to-skip turns the tool into a no-op, default-to-stage turns it into a hazard.

Reflexes to catch in yourself:

- "Config change → skip" without reading what the field does.
- "New file → skip" without reading what the file is or how it's wired.
- "File has substantive changes → skip the file" without enumerating hunks. Coupling is a hunk-level property; a substantive rewrite in one hunk doesn't disqualify a pure-observability hunk two screens down. Always classify at hunk granularity.

Banned skip-reasons. These phrases describe nearly every non-mechanical diff, including stageable ones, so they can never stand alone as a verdict:

- _"carries intent"_ (a typo fix carries intent), _"not trivial"_ / _"not mechanical"_, _"adds new code"_ / _"adds new logic"_
- _"behavioural"_ / _"behavioural change"_ / _"behaviour-affecting"_: the most over-used non-reason; name _what kind_ instead: contract, algorithm, value the reviewer must weigh, smell, lonely one-liner
- _"coupled"_, _"design choice"_, _"feature"_: without naming, respectively: what it's coupled to (design+adapter or complete-unit wiring?), what the choice is, whether the design lives here or just the wiring

For any hunk that is not an automatic skip category (those are listed under "What is NOT stageable"), do all three before reaching a verdict: quote the literal `+`/`-` line that triggered it (not a paraphrase or category label), answer design-vs-wiring in one phrase referencing the file(s), and name the reviewer's job: weigh _what_ was decided, or only check the wiring. If you reach for a banned phrase or can't do all three, you haven't looked enough. Go look; a verdict without them is a guess.

## Evidence sources, cheapest first

When a hunk is borderline, not clear-cut in either direction, use these to gain confidence. They are ordered by cost; stop as soon as one resolves the question.

1. **The rest of the diff.** Is this change repeated in sibling files? Three or more identical occurrences = sweep = stageable. Verify the lines are genuinely identical (don't assume "looks the same"); count.
2. **The file itself.** Does this change extend a pattern already present in the file? A new `logger.warn(...)` next to four existing `logger.warn(...)` calls is a continuation, not an introduction.
3. **Imports the hunk references.** If a hunk adds `import { foo } from './bar'`, open `./bar` and read what `foo` is before classifying the usage. A `logger.warn(...)` could be a real logger or `console.warn` aliased; a new helper import could be a tiny utility or a 200-line abstraction. The import source decides.
4. **`git grep` for the symbol.** Count existing usages of the new call/import elsewhere in the codebase. Zero usages = the change is introducing a new thing; three or more = it's joining an established convention.
5. **Recent git history on this branch.** Check whether the change continues a pattern already committed: `git log --oneline -20`, `git log -G '<pattern>' --oneline`, or `git log -p -3 -- <file>`. If a recent commit added `data-testid={testids.ListingCard}` and the working tree adds `data-testid={testids.ListingsContainer}` in the same shape, the design was decided in that commit and the new change inherits its approval. That is one of the strongest stage signals, because another reviewer already weighed the design. Recency matters (this branch or this week is strong; months-old is weak), and committed ≠ right, but it has passed a reviewer's eye once.
6. **Five to ten lines of context around the hunk.** Sometimes the meaning is local: the surrounding code makes the intent clear.

If none of these resolves the doubt, then skip, but only because the evidence ran out, not because looking felt like work.

## What counts as stageable

- **Unused import removal**: an import that was deleted and nothing else in the hunk depends on it.
- **Formatting / whitespace**: indentation, trailing whitespace, trailing commas, semicolon insertion/removal, line wrapping that doesn't change logic.
- **Lint auto-fixes**: changes that look like they came from a lint `--fix` (`let` → `const` for never-reassigned variables, removing flagged type assertions).
- **Typo corrections in strings/comments**: obvious spelling fixes where the correct word is unambiguous. Also includes user-facing copy with no semantic change (capitalisation normalisation, punctuation tidy).
- **Dead code removal**: commented-out code, unreachable branches the linter flagged. Deletions paired with an in-diff replacement (removing `stripe.ts` because a new `payments/` module in the same diff replaces it) also count; the coupling shows the deletion is intentional.
- **Import reordering**: imports moved around but not added or removed.
- **Generated file timestamps**: "Generated on …" header lines in codegen output. When the file has other hunks, **always route via stage-hunk**: the timestamp depends only on generation time, independent of every other hunk, so staging it alone is always safe and never fragments the artifact. The body stays unstaged for review.
- **Uniform sweeps**: the same change applied identically across three or more files; the repetition itself is the evidence. Count occurrences and verify the added lines really are identical, not just similar, before staging the set.
- **Cross-file patterns of additive wiring**: a coherent (not necessarily identical) pattern across 5–10 files, e.g. `data-testid={testids.X}` sweeps or `data-hydrated` mount markers where the target symbol already exists. The pattern plus the unchanged target symbol are the evidence.
- **Continuations of already-committed patterns**: a recent commit on this branch (or recent main) introduced the pattern and the working tree extends it identically to new sites. Verify with `git log -G '<pattern>'` or `git log -p -3 -- <related-file>` that the prior commit did the same shape of change; a pattern from this branch is strong evidence, a 2-year-old commit weak.
- **Observability additions**: a project-logger call, error-reporting call (e.g. `captureException`), tracing span, or metrics increment, with no control-flow change in the same hunk; verify via imports that the call resolves to a real observability function. A log added inside a previously-silent catch counts, provided return value and control flow are unchanged.
- **Observability config toggles**: flipping a known observability flag to its standard value (`enabled: true`, sample-rate adjustment, log-level setting), provided the underlying capability is already wired up.
- **Self-evidently complete additive units**: a new file plus its mechanical wiring, where every wiring hunk is what you'd expect given the new file's purpose. Canonical example: a new dev-harness page is one unit comprising the new `pages/TabsReload.tsx`, its import, a `pageMenuItems` entry matching the existing entries' shape, and the render conditional next to its siblings. Same shape: entries in clearly-indexed lists, test seed files paired with the harness wiring that mounts them.
- **Documentation and repo orientation**: additions to `AGENTS.md`, `CLAUDE.md`, `README.md` that point at existing files or describe established patterns. Skip only if the doc encodes a _new_ claim a reviewer would scrutinise.

## What is NOT stageable: leave for review

- **API / wire contract changes**: request or response shape changes (e.g. `200` → `204`, `allOf` → `oneOf`, OpenAPI schema field shifts), endpoint signature changes, RPC argument-shape changes. The contract itself is the question.
- **Schema requirement / validation changes**: making a field required, changing a field's type, swapping enum sets, altering coercion at a boundary (`null` ↔ `undefined` at REST/IPC edges where consumers see the change).
- **Database queries, migrations**: query bodies, migration files, migration registration changes.
- **Algorithm / encoding changes**: anything that alters how data is computed or represented (typeid alphabet swap, hash algorithm change, ID format change, route-resolution rule change).
- **Config values the reviewer must weigh**: TTLs, timeouts, feature flags, security policy, route configs: the _specific value chosen_ is the decision. Distinct from observability config, which changes what is observed. The skip-reason must name the value and the reviewer's question, e.g. "DOWNLOAD_TTL 3600 → 2_592_000 (why 30 days?)". If the change is also isolated from the rest of the diff, classify additionally as smell-adjacent.
- **Secret / credential rotations**: secret_name changes, JWK rotations, any binding from a logical name to a piece of credential material. Atomic with environment ops; needs joint review.
- **Test assertion changes**: modifications to expected values, mocks, snapshots, or test scaffolding logic. Test files that _only_ add a new file or pure docblock comments are still stageable; assertion edits are not.
- **Public symbol renames**: anything visible across module boundaries where consumers must be checked.
- **New abstractions whose design is the point**: a new exported helper, type, or module whose existence and shape is the design choice, not wiring of something already decided.
- **Coupled refactors where one side defines a contract and the other adapts**: RPC server adds a new headers signature; caller adapts to use it. The contract itself is under review; skip the pair. (Distinct from complete additive units, where the coupling spans consumers of an already-decided thing.)
- **Throwaway debug logging**: `console.log`, raw `print`, placeholder messages ("here", "got x", `JSON.stringify(...)`), or log lines scattered without a pattern: in-flight debugging that shouldn't be committed.
- **TODO / WARN / FIXME / XXX / HACK markers**: a hunk that adds, modifies, or sits adjacent to such a comment is the author flagging unfinished or risky work. Skip the marked hunk _and_ any hunks in the same function / block / coupled call site, with reason "marked incomplete: <quoted marker text>". In-diff markers are stronger signals than pre-existing ones; both warrant skipping.
- **Code smells, even when the diff looks small**: a reviewer would push back on the _approach_: duplication (a schema copy-pasted with one prop modified instead of composed), drive-by `zIndex: 9999` / magic-number wedges that paper over a layout bug, workarounds that sidestep a root cause (`?? null` to silence a TS error, retry loops masking a race), suspicious one-liners in hot paths or public exports. If you'd be uncomfortable showing the diff to a peer and saying "this needs no review", it's a smell; skip.
- **Smell-adjacent**: clean-looking changes lose their self-evidence when connected to a smell. Skip when an otherwise-clean hunk is wired into a smell (imports the duplicated schema, sits inside the z-index-wedged container); when a smell appears alongside another smell in the same file or cluster (two smells compound into one larger concern); or when a one-liner has no analogue anywhere in the diff: loneliness signals hand-placed intent whose reason the reviewer can't see. Stage a lonely one-liner only when it unambiguously fits an established trivial category (typo fix, obvious lint repair); otherwise skip with "smell-adjacent: lonely one-liner, intent unclear from diff".
- **Mixed hunks**: a single hunk that fuses stageable and non-stageable changes (a formatting fix on the same line as a logic change). Classify the whole hunk as non-stageable; `stage-hunk` can't subdivide one hunk. A file with _separate_ stageable and non-stageable hunks is different: route those to `stage-hunk` per Process step 3.
- **Merge conflict markers** (UU status files): never touch.

## Process

Work in batches: read all diffs in the step-1 scan, classify, then stage in bulk. Avoid re-reading files already inspected.

### 1. Inventory the whole diff, before classifying any single hunk

- `git status --short` for the full picture (run on every invocation, including re-runs, and trust it over any memory of prior staging) plus `git diff --name-only` for the unstaged set. Skip up front: UU conflicts, fully-staged files.
- For cross-file pattern detection, prefer `git diff -G '<pattern>' --name-only` or `git diff -U0` over grepping `^\+` lines in the raw diff: the latter catches pre-existing context lines.
- Scan every file's hunks at a glance (`git diff --stat` plus a quick read) and identify four shapes before any per-file verdict:
  - **Repeated patterns**: the same line or block added in three or more files. Mechanical sweep; treat the set as one decision.
  - **Cross-file additive units**: a new file plus the consumer-side wiring that mounts/imports/registers it (new dev page + import + menu entry + render line; new docs file + AGENTS.md pointer). The coupling is the completeness of the addition; treat as one stageable unit.
  - **Contract-and-adapter pairs**: file A defines or changes a contract (RPC signature, schema, response shape), file B adapts to it. The contract design is under review; treat as one _skip_ unit: never split, and don't mistake it for an additive unit.
  - **Isolated lonely changes**: hunks with no analogue elsewhere in the diff. These warrant the most scrutiny: isolation often signals hand-placed intent (a deliberate config bump, an algorithm tweak).

### 2. Classify each file's hunks with whole-diff context

For each file with unstaged changes:

1. `git diff -U5 -- <file>`: full diff with context.
2. Apply the reviewer-judgment test per hunk: a named stageable pattern with confirming evidence → stage; a named skip pattern with confirming evidence → skip; borderline → run the evidence checks, cheapest first, until a verdict emerges.
3. "I'm not sure" means "I haven't checked yet". Go check.
4. Before writing a file off as "no stageable hunks present," enumerate every hunk with a one-phrase reason. If any hunk in that list is self-evidently correct on its own, the file is _mixed_, not skipped, so route it to stage-hunk in step 3. "This file is a substantive rewrite" describes the file at large, not the pure-observability or pure-annotation hunks inside it.

### 3. Stage

- All hunks in a file are trivial → `git add <file>`.
- Some hunks trivial, some not → invoke `block65-tools:stage-hunk` via the **Skill tool**, never via Bash or its underlying script (`stage_hunk.py`, `stage-hunk.sh`, any cached plugin path), which bypasses the skill's hunk-listing and matching steps. `args` is one string: file path on the first line, a plain-language description of which hunks on the remaining lines:

  ```
  Skill(skill="block65-tools:stage-hunk",
        args="services/website/src/server/url/resolve-link.ts\nstage only the two logger.warn additions inside existing catches; leave the link-label refactor")
  ```

- No hunks trivial → leave the file untouched.

### 4. Report

After processing all files, present two lists; each entry names the evidence used to classify, not just the category. **Staged**, grouped by classification category:

```
Staged:
  additive unit:    <set: new-file + wiring files> — new <feature> wired via import + menu entry + render line
  history continuation: <file> — extends pattern from <commit-sha>; same shape, already reviewed
  uniform sweep:    <N files> — same M-line change identical across <count> files
  observability:    <file> — adds logger call; logger import confirmed, K× existing usage in same file
  formatting:       <file> (hunks 1, 3) — whitespace only
```

**Skipped**, framed as _why I didn't stage it_: a reviewer-style reason, grounded in the actual diff:

```
Skipped:
  <file> — risky: response shape changed 200→204, reviewer must weigh
  <pair: file A + file B> — contract under review: A defines new RPC headers shape, B adapts
  <file> — config value the reviewer must weigh: DOWNLOAD_TTL 3600 → 2_592_000 (why 30 days, not 7?)
  <file> — smells: openapi schema duplicated with one prop modified (should compose, not copy)
  <file> — smell-adjacent: lonely one-liner with no analogue elsewhere, intent unclear from diff
  <file> — marked incomplete: "TODO: handle reconnect" added at line 87; skipping function and call sites
```

A high-level reason ("looks risky", "smells", "smell-adjacent", "marked incomplete") must be paired with the concrete diff evidence that triggered it: "looks risky" alone is useless, "looks risky: response shape changed 200→204" is reviewable, and "behavioural" is never acceptable on its own; see the banned skip-reasons. One line per file unless a file mixes staged and skipped hunks; then list per hunk.

## Arguments

- `--dry-run`: show what would be staged without actually staging anything.
