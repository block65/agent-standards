---
name: stage-trivial
description: "Scan git diffs and stage only the changes that are self-evidently correct and intentional in context — changes a reviewer would have nothing to deliberate on. Covers lint fixes, formatting, typos, dead code, observability, uniform sweeps, AND self-evidently complete additions like new dev-harness pages wired up via import + menu entry + new file, testid sweeps, mount-marker additions, AGENTS.md pointers. Leaves anything requiring reviewer judgment unstaged: API contract changes, secret rotations, schema requirement changes, algorithm changes, config values the reviewer must weigh, code smells. Use this skill when the user says 'stage the obvious stuff', 'stage trivial changes', 'stage the safe diffs', 'cherry-pick the lint fixes', 'stage what's obviously correct', or wants to triage a messy working tree before committing."
---

# Stage Trivial Changes

Scan the unstaged git diff, classify every hunk, and stage only the ones that are **self-evidently correct and intentional in context**. Never commit — just stage. Produce a summary so the user can see what was staged and what was left, with the evidence behind each call.

## The reviewer-judgment test

The criterion is not "is this small or mechanical?" — it is **"would a reviewer have anything to deliberate on?"**

- **Stage** when the answer is no: the change is self-evidently a complete intentional unit. The reviewer would see it, recognise it as the thing it obviously is, and move on.
- **Skip** when the answer is yes: the change itself encodes a design choice, a value judgement, or a contract negotiation a reviewer would have to weigh.

"Trivial" in this skill's name means **trivial-for-a-reviewer**, not trivial-in-size. New code, new files, and coupled multi-file changes can all be stageable — the *coupling* of a clear additive unit (new page + import + menu entry + render line + new file) is often the very thing that makes it self-evidently complete. Conversely, a one-character config edit (`200` → `204`, an alphabet swap, a TTL bump) can be a deliberate design choice that needs review.

The design-vs-wiring lens: when the design is *here* (a new API shape, a new schema field, a new algorithm), skip — the reviewer must judge the design. When the design is elsewhere (already decided, this commit just wires it up consistently across N call sites), stage — the reviewer would only ask "did you do it right," and the diff answers that itself.

## By evidence, not reflex

Every classification — stage *and* skip — must be a conclusion drawn from looking at the diff and the surrounding code. Not a reflex driven by what the hunk superficially looks like.

- **"Stage" by evidence** means: the same change appears identically across N sibling files, the imported symbol is a known export, the call extends a pattern already used several times in the file, the new file + its wiring together form a complete unit. The verdict came from looking.
- **"Skip" by evidence** means: the change encodes a contract a reviewer must weigh (response shape, schema field, secret name, algorithm choice), the imported module defines a new abstraction whose design is the question, the hunk introduces a runtime effect whose correctness depends on judgement. The verdict came from looking.

"I haven't looked yet" is never a verdict. Default-to-skip turns the tool into a no-op; default-to-stage turns it into a hazard. Look first.

Reflexes to catch in yourself:

- "Config change → skip" without reading what the field does.
- "New file → skip" without reading what the file is or how it's wired.
- "Adds code → skip" without checking whether the code is a complete intentional unit or a design choice.
- "Coupled → skip" without asking whether the coupling is *design + adapter* (skip) or *complete-unit wiring* (stage).
- "When in doubt → skip" without trying to resolve the doubt first.
- "File has substantive changes → skip the file" without enumerating hunks. Coupling is a hunk-level property; a substantive rewrite in one hunk doesn't poison a pure-observability hunk two screens down. Always classify at hunk granularity.

### Banned skip-reasons

These phrases describe nearly every non-mechanical diff — including stageable ones — so they cannot stand alone as a verdict. They are the most common form of category-label laundering:

- *"carries intent"*
- *"behavioural"* / *"behavioural change"* / *"behaviour-affecting"* — this is the single most over-used non-reason. Every meaningful change is "behavioural" in some sense; the word identifies nothing. The interesting question is always *what kind* — a contract change, an algorithm change, a value the reviewer must weigh, a smell, a lonely one-liner — and you must name that instead.
- *"not trivial"* / *"not mechanical"*
- *"adds new code"* / *"adds new logic"*
- *"coupled"* (without naming *what* it's coupled to and whether the coupling is design+adapter or complete-unit wiring)
- *"design choice"* (without showing what the choice is)
- *"feature"* (without showing whether the design lives here or just the wiring)

Every diff that touches running code "carries intent" — a typo fix carries intent. The reviewer-judgment test is not *"does this carry intent?"* but *"does the reviewer have to weigh the intent, or is the intent self-evident from context?"* If you find yourself reaching for one of these phrases, stop and run the forcing function below.

### Forcing function for ambiguous items

For any hunk that is *not* an automatic skip category (those are listed under "What is NOT stageable" and include API contracts, schema requirements, secret rotations, algorithm changes, config values the reviewer must weigh, debug logging, smells, smell-adjacent, TODO/WARN markers, merge conflicts), you must do all three before reaching a verdict:

1. **Quote the actual diff line** that triggered the verdict. Not a paraphrase, not a category label — the literal `+`/`-` line.
2. **Answer the design-vs-wiring question explicitly:** does the *design* live in this diff, or does the diff just wire up an already-decided design? Answer in one phrase referencing the file(s).
3. **Name the reviewer's job:** would the reviewer weigh *what* was decided, or only *whether the wiring is correct*?

If you can't do (1)–(3), you haven't researched enough — go look. A "skip" verdict without these is a guess, not a classification.

## Look across the diff before classifying any single hunk

This step is mandatory and comes before per-file classification.

1. `git diff --name-only` + `git status --short` for the changed-file set as a whole.
2. Scan the diffs at a glance — `git diff --stat` plus a quick read of each file's hunks — and identify four categories:
   - **Repeated patterns**: the same line or block added in three or more files with the same shape. Mechanical sweep; treat the set as one decision.
   - **Cross-file additive units**: a new file plus the consumer-side wiring that mounts/imports/registers it (new dev page + import + menu entry + render line; new testid + JSX consumers; new docs file + AGENTS.md pointer). The coupling is the *completeness* of the addition. Treat as one stageable unit.
   - **Contract-and-adapter pairs**: file A defines or changes a contract (RPC signature, schema, response shape, API surface), file B adapts to it. The contract design is under review. Treat as one *skip* unit — never split, but don't mistake for an additive unit either. The test: would a reviewer weigh the contract itself, or only the wiring? If the former, skip the pair.
   - **Isolated lonely changes**: hunks with no analogue elsewhere in the diff. These warrant the most scrutiny — isolation often signals hand-placed intent (a deliberate config bump, an algorithm tweak).
3. Only then, work file by file with the whole-diff context already in mind.

## Evidence sources, cheapest first

When a hunk is borderline — not clear-cut in either direction — use these to gain confidence. They are ordered by cost; stop as soon as one resolves the question.

1. **The rest of the diff.** Is this change repeated in sibling files? Three or more identical occurrences = sweep = stageable. Verify the lines are genuinely identical (don't assume "looks the same"); count.
2. **The file itself.** Does this change extend a pattern already present in the file? A new `logger.warn(...)` next to four existing `logger.warn(...)` calls is a continuation, not an introduction.
3. **Imports the hunk references.** If a hunk adds `import { foo } from './bar'`, open `./bar` and read what `foo` is before classifying the usage. Imports + usage together resolve ambiguity neither resolves alone. A `logger.warn(...)` could be a real logger or `console.warn` aliased; the import tells you which. A new helper import could be a tiny utility or a 200-line new abstraction; reading the source decides which.
4. **`git grep` for the symbol.** Count existing usages of the new call/import elsewhere in the codebase. Zero usages = the change is introducing a new thing; three or more = it's joining an established convention.
5. **Recent git history on this branch.** Check whether the change continues a pattern already committed. Use `git log --oneline -20` for a quick scan of recent commits, `git log -G '<pattern>' --oneline` to find commits that touched the same shape of change, or `git log -p -3 -- <file>` to see what the most recent commits to this file did. If a recent commit already added e.g. `data-testid={testids.ListingCard}` and the working tree adds `data-testid={testids.ListingsContainer}` in the same shape, the design was already decided in that commit — the new change inherits its approval. This is one of the strongest stage signals available, because *another reviewer has already weighed the design choice*. Caveats: ancient history (months old) is weaker evidence than recent (this branch / this week); committed ≠ right, but it does mean "already passed a reviewer's eye once".
6. **Five to ten lines of context around the hunk.** Sometimes the meaning is local — the surrounding code makes the intent clear.

If none of these resolves the doubt, then skip — but only because the evidence ran out, not because looking felt like work.

## What counts as stageable

Changes where looking at the diff confirms a reviewer would have nothing to weigh:

- **Unused import removal** — an import that was deleted and nothing else in the hunk depends on it.
- **Formatting / whitespace** — indentation, trailing whitespace, trailing commas, semicolon insertion/removal, line wrapping that doesn't change logic.
- **Lint auto-fixes** — changes that look like they came from a lint `--fix` (`let` → `const` for never-reassigned variables, removing flagged type assertions).
- **Typo corrections in strings/comments** — obvious spelling fixes where the correct word is unambiguous. Also includes user-facing copy with no semantic change (capitalisation normalisation, punctuation tidy).
- **Dead code removal** — deleting commented-out code, removing unreachable branches the compiler/linter flagged. Deletions tied to a sibling new-file (e.g. removing `stripe.ts` because a new `payments/` module replaces it *and* the replacement is also in the diff) are also stageable; the coupling is the evidence the deletion is intentional.
- **Import reordering** — imports moved around but not added or removed.
- **Generated file timestamps** — "Generated on …" / "Updated at …" header lines in codegen output. **Always route via stage-hunk** when the file has other hunks — the timestamp is a function of the generation time, not the body content, so peeling it is always safe and never "fragments a regenerated artifact." If you find yourself reasoning *"skip rather than split a regenerated artifact"* on a generated file with a timestamp hunk, that instinct is wrong here; the timestamp hunk's correctness is independent of every other hunk in the same file. Stage it. The body stays unstaged for review.
- **Uniform sweeps** — the same change applied identically across three or more files. The repetition itself is the evidence: it's a mechanical pass, not a per-file decision. Count occurrences; verify the added lines really are identical (not just similar) before staging the set.
- **Cross-file patterns of additive wiring** — even when the change *isn't* literally identical, a coherent pattern across 5–10 files (testid attributes added to JSX, `data-hydrated` mount markers added across components, `data-testid={testids.X}` sweeps where `testids.X` already exists) counts. The pattern + the unchanged target symbol are the evidence.
- **Continuations of already-committed patterns** — when a recent commit on the current branch (or recent main) introduced a pattern and the working tree extends it identically to one or more new sites, the new sites are stageable. The design was approved when the original commit landed; the working-tree extension is just "more of the same." Verify with `git log -G '<pattern>'` or `git log -p -3 -- <related-file>` that the prior commit really did the same shape of change. Recency matters: a pattern from a commit on *this branch* is strong evidence; a pattern from a 2-year-old commit is weak. Use this whenever you would have called something "smells like wiring but I'm not sure if the design was decided" — history answers the question.
- **Observability additions** — adding a logger call via the project's logger, an error-reporting call (e.g. `captureException`), a tracing span, or a metrics increment, with no control-flow change in the same hunk. Verify via imports that the call resolves to an actual observability function. Adding a log line inside a previously-silent catch (`.catch(() => undefined)` → `.catch((err) => { logger.warn(...); return undefined; })`) counts here, provided the return value and control flow are unchanged.
- **Observability config toggles** — flipping a known observability flag to its standard value (`enabled: true`, trace propagation on, sample-rate adjustment, log-level setting), provided the underlying capability is already wired up.
- **Self-evidently complete additive units** — a new file plus its mechanical wiring, where every wiring hunk is what you'd expect given the new file's purpose. The canonical example: adding a new dev-harness page is *one* unit comprising (a) the new `pages/TabsReload.tsx`, (b) `import TabsReloadPage from "./pages/TabsReload.tsx"`, (c) a new `{ id: "tabs-reload", label: "..." }` entry in `pageMenuItems` matching the existing entries' shape, and (d) `{page === "tabs-reload" && <TabsReloadPage />}` next to the sibling page-conditionals. The coupling makes it *more* obviously complete, not less. Same shape applies to: new docs-pointer additions in `AGENTS.md`/`README.md`, new entries in clearly-indexed lists, new test seed files paired with the harness wiring that mounts them.
- **Documentation and repo orientation** — additions to `AGENTS.md`, `CLAUDE.md`, `README.md` that point at existing files or describe established patterns. Skip only if the doc encodes a *new* claim a reviewer would scrutinise; pointers and orientation are stageable.

## What is NOT stageable — leave for review

Skip when the change encodes something a reviewer must judge:

- **API / wire contract changes** — request or response shape changes (e.g. `200` → `204`, `allOf` → `oneOf`, OpenAPI schema field shifts), endpoint signature changes, RPC argument-shape changes. The contract itself is the question.
- **Schema requirement / validation changes** — making a field required, changing a field's type, swapping enum sets, altering coercion at a boundary (`null` ↔ `undefined` at REST/IPC edges where consumers see the change).
- **Database queries, migrations** — query bodies, migration files, migration registration changes.
- **Algorithm / encoding changes** — anything that alters how data is computed or represented (typeid alphabet swap, hash algorithm change, ID format change, route-resolution rule change).
- **Config values the reviewer must weigh** — TTLs, timeouts, feature flags, security policy, route configs, anything where the *specific value chosen* is the decision (e.g. why 30 days and not 7? why this timeout?). Distinct from observability config which changes what is *observed*. Skip-reason should name the specific value and the question the reviewer would ask, not just "behavioural" — e.g. "DOWNLOAD_TTL 3600 → 2_592_000 (why 30 days?)". If the change is *also* isolated from the rest of the diff with no surrounding context, classify additionally as smell-adjacent (lonely one-liner) — that compounds the concern.
- **Secret / credential rotations** — secret_name changes, JWK rotations, any binding from a logical name to a piece of credential material. Atomic with environment ops; needs joint review.
- **Test assertion changes** — modifications to expected values, mocks, snapshots, or test scaffolding logic. Test files that *only* add a new file or pure docblock comments are still stageable; assertion edits are not.
- **Public symbol renames** — anything visible across module boundaries where consumers must be checked.
- **New abstractions whose design is the point** — a new exported helper, type, or module whose existence and shape is the design choice (not just wiring an already-decided design). The distinction from the "complete additive unit" category above: ask whether a reviewer would weigh the design or just the wiring. If the design lives in *this* diff, skip.
- **Coupled refactors where one side defines a contract and the other adapts** — RPC server adds new headers signature; caller adapts to use it. The contract itself is under review. Skip the pair. (Distinct from complete additive units, where the coupling spans *consumers of an already-decided thing*, not contract redesign.)
- **Throwaway debug logging** — `console.log`, `console.error`, raw `print`, log calls with placeholder messages ("here", "got x", `JSON.stringify(...)`), or log lines scattered without a pattern. Signs of in-flight debugging that shouldn't be committed.
- **TODO / WARN / FIXME / XXX / HACK markers** — any hunk that adds, modifies, or sits adjacent to a comment containing `TODO`, `WARN`, `FIXME`, `XXX`, or `HACK` is the author flagging "this isn't done" or "watch out". Skip both the marked hunk *and* any hunks in the same function / block / coupled call site, with reason "marked incomplete: <quoted marker text>". Markers added in-diff are stronger signals than pre-existing ones; both warrant skipping the surrounding work.
- **Code smells, even when the diff looks small** — surface-level mechanical does not override quality concerns. A reviewer would push back on the *approach*, so the change is not self-evidently correct. Examples:
  - **Duplication** — a schema, type, or function copy-pasted with one or two props modified instead of being composed/extended. The diff is "just a new export" but the reviewer would say "share it, don't copy it."
  - **Drive-by z-index / magic number wedges** — a one-line `zIndex: 9999` or `marginTop: -3px` that papers over a layering or layout bug instead of fixing the root cause. Mechanically tiny, judgment-laden.
  - **Workarounds that sidestep a root cause** — try/catch wrapping a flaky call without diagnosing why it fails, defensive `?? null` coercions added to silence a TS error rather than fix the upstream type, retry loops added to mask a race condition.
  - **Suspicious one-liners in load-bearing files** — a single-line change to a hot path, a module's public exports, or anything where the reviewer would want to understand "why this, why now."

  When in doubt: if you'd be uncomfortable showing the diff to a peer and saying "this needs no review", it's a smell — skip.
- **Smell-adjacent** — even clean-looking changes lose their self-evidence when they're connected to a smell, and isolated one-liners with no analogue anywhere in the diff are inherently suspicious. Skip with reason "smell-adjacent" when:
  - An otherwise-clean hunk is wired into a smell (e.g. the file imports the duplicated schema, the component sits inside the z-index-wedged container, the call site goes through the suspicious workaround). The cleanliness of the local change doesn't redeem the unit — the reviewer would see the whole picture.
  - A smell appears alongside another smell in the same file or same diff cluster. Smells multiply meaning, not divide it; two smells in one file is not "two small concerns" but one larger one.
  - A one-line change is *disconnected* from everything else in the diff — no sibling files do anything similar, no cross-file pattern explains it, no surrounding hunks share its purpose. Loneliness in a diff almost always signals deliberate hand-placed intent, and the absence of context means the reviewer can't tell *why now*. Stage only when the one-liner unambiguously fits an established trivial category (a typo fix, an obvious lint repair); otherwise skip with "smell-adjacent: lonely one-liner, intent unclear from diff."
- **Mixed hunks** — a single hunk that fuses stageable and non-stageable changes together (a formatting fix on the same line as a logic change). Classify the whole hunk as non-stageable; `stage-hunk` operates at hunk granularity and can't subdivide one. A file with *separate* stageable and non-stageable hunks is a different case — route those to `stage-hunk` per Process step 3.
- **Merge conflict markers** (UU status files) — never touch.

## Process

### 1. Inventory the whole diff

- `git status --short` for the full picture: what's staged, unstaged, and untracked. Do this on every invocation — including re-runs — and trust it over any memory of prior staging.
- `git diff --name-only` for the unstaged file set.
- Skip up front: UU conflicts, fully-staged files.
- For cross-file pattern detection, prefer `git diff -G '<pattern>' --name-only` (matches files where the pattern was added/removed) or `git diff -U0` over grepping `^\+` lines in the raw unified diff — the latter catches pre-existing context lines and forces manual filtering.
- Run the cross-file scan from "Look across the diff before classifying any single hunk" — identify sweeps, coupled pairs, and isolated lonely changes.

### 2. Classify each file's hunks with whole-diff context

For each file with unstaged changes:

1. `git diff -U5 -- <file>` — full diff with context.
2. For each hunk, apply the reviewer-judgment test:
   - If it fits a named stageable pattern AND the evidence confirms it, stage.
   - If it fits a named skip pattern AND the evidence confirms it, skip.
   - If borderline, run the evidence checks (cheapest first) until a verdict emerges. The borderline cases are usually: "is this an additive unit or a design choice?" and "does the design live here or elsewhere?"
3. Don't conclude before looking. "I'm not sure" means "I haven't checked yet" — go check.
4. Before writing a file off as "no stageable hunks present," enumerate every hunk with a one-phrase reason. If any hunk in that list is self-evidently correct on its own, the file is *mixed*, not skipped — route it to stage-hunk in step 3. The instinct "this file is a substantive rewrite" describes the file at large; it does not justify discarding the pure-observability or pure-annotation hunks inside it.

### 3. Stage

- All hunks in a file are trivial → `git add <file>`.
- Some hunks trivial, some not → invoke `block65-tools:stage-hunk` via the **Skill tool** (not via Bash). The tool call shape is:

  ```
  Skill(skill="block65-tools:stage-hunk",
        args="services/website/src/server/url/resolve-link.ts\nstage only the two logger.warn additions inside existing catches; leave the link-label refactor")
  ```

  `args` is one string: file path on the first line, a plain-language description of which hunks on the remaining lines.

  Never invoke stage-hunk by shelling out to its underlying script (`stage_hunk.py`, `stage-hunk.sh`, or any cached plugin path). That bypasses the skill's hunk-listing and matching steps and is the wrong layer.
- No hunks trivial → leave the file untouched.

### 4. Report

After processing all files, present two lists. Each entry names the evidence used to classify, not just the category.

**Staged**, grouped by classification category:

```
Staged:
  additive unit:    <set: new-file + wiring files> — new <feature> wired via import + menu entry + render line; all pieces mechanical given the new file's purpose
  cross-file pattern: <N files> — same shape of additive wiring (e.g. data-testid={testids.X} sweep) across <count> sites
  history continuation: <file> — extends pattern from <commit-sha> "<commit-message>"; same shape, already reviewed
  uniform sweep:    <N files> — same M-line change identical across <count> files
  observability:    <file> — adds logger call; logger import confirmed, K× existing usage in same file
  formatting:       <file> (hunks 1, 3) — whitespace only
  imports:          <file> — unused import removal
  docs/orientation: <file> — adds pointer to <existing target> in AGENTS.md
  generated:        <file> — generated-timestamp header only
```

**Skipped**, framed as *why I didn't stage it* — a reviewer-style reason, grounded in the actual diff:

```
Skipped:
  <file> — risky: response shape changed 200→204, reviewer must weigh
  <pair: file A + file B> — contract under review: A defines new RPC headers shape, B adapts
  <file> — risky: secret rotation (UC_SIGNING_KEY → UC_SIGNING_KEY_STAGING_20260520)
  <file> — algorithm change: typeid alphabet swap alters ID encoding
  <file> — config value the reviewer must weigh: DOWNLOAD_TTL 3600 → 2_592_000 (why 30 days, not 7?)
  <file> — smells: openapi schema duplicated with one prop modified (should compose, not copy)
  <file> — smells: drive-by zIndex bump papers over a layering bug
  <file> — smell-adjacent: hunk imports the duplicated schema (skipped alongside `<other file>`)
  <file> — smell-adjacent: lonely one-liner with no analogue elsewhere, intent unclear from diff
  <file> — marked incomplete: "TODO: handle reconnect" added at line 87; skipping function and call sites
  <file> — merge conflict (UU)
```

The reason can be high-level ("looks risky", "smells", "design under review", "marked incomplete", "smell-adjacent") — but it must be paired with the concrete diff evidence that triggered the call. "Looks risky" alone is useless; "looks risky: response shape changed 200→204" is reviewable. "Behavioural" is never an acceptable high-level reason on its own — see the banned skip-reasons section.

One line per file unless a file mixes staged and skipped hunks — then list per hunk.

## Performance

Process files in batches rather than one at a time. Read all diffs first (the whole-diff scan), classify, then stage in bulk. Avoid re-reading files already inspected in the cross-file scan.

## Arguments

- `--dry-run` — show what would be staged without actually staging anything.