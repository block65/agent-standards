---
name: stage-trivial
description: "Scans git diffs and stages only the changes that are self-evidently correct and intentional in context: changes a reviewer would have nothing to deliberate on. Covers lint fixes, formatting, typos, dead code, observability, uniform sweeps, and self-evidently complete additions like new dev-harness pages wired up via import + menu entry + new file, testid sweeps, mount-marker additions, AGENTS.md pointers. Leaves anything requiring reviewer judgment unstaged: API contract changes, secret rotations, schema requirement changes, algorithm changes, config values the reviewer must weigh, code smells. Use when the user says 'stage the obvious stuff', 'stage trivial changes', 'stage the safe diffs', 'cherry-pick the lint fixes', 'stage what's obviously correct', or wants to triage a messy working tree before committing. Supports --dry-run."
---

Classify every unstaged hunk and stage only the ones a reviewer would have
nothing to deliberate on. Stage, never commit. With `--dry-run`, stage nothing
and report what would be staged.

## The reviewer-judgment test

Ask "would a reviewer have anything to deliberate on?", not "is this small?".
When the design lives here (a new API shape, schema field, algorithm), skip: the
reviewer must judge it. When the design was decided elsewhere and this diff only
wires it up consistently, stage: the reviewer would only check the wiring, and
the diff shows it. New files and coupled multi-file changes can be stageable; a
one-character config edit (`200` → `204`, a TTL bump) can need review.

## By evidence, not reflex

Every verdict, stage or skip, comes from reading the diff and the surrounding
code. Default-to-skip makes the skill a no-op; default-to-stage makes it a
hazard. Read before deciding: what a changed config field does, what a new file
is and how it is wired, and every hunk of a substantially changed file (classify
per hunk; a rewrite in one hunk does not disqualify an observability hunk
elsewhere in the file).

These phrases describe nearly every non-mechanical diff, so they never stand
alone as a skip reason: "carries intent", "not trivial", "not mechanical", "adds
new code/logic", "behavioural" (name the kind instead: contract, algorithm,
value to weigh, smell, lonely one-liner), and "coupled", "design choice" or
"feature" without naming what it is coupled to, what the choice is, or whether
the design or only the wiring lives here.

For any hunk outside the automatic skip categories, before the verdict: quote
the literal `+`/`-` line that triggered it, answer design-vs-wiring in one
phrase naming the file(s), and name the reviewer's job (weigh what was decided,
or only check the wiring).

## Evidence for a borderline hunk, cheapest first

Stop at the first that resolves it; skip only once the evidence runs out.

1. **The rest of the diff**: the same lines in three or more files is a sweep.
   Count them and confirm they are identical, not similar.
2. **The file**: a new `logger.warn(...)` beside four existing ones continues a
   pattern.
3. **The import source**: open the module a new import comes from; it decides
   whether `logger` is a real logger and whether a helper is tiny or an
   abstraction.
4. **`git grep` the symbol**: zero other usages introduces a new thing; three or
   more joins a convention.
5. **Branch history** (`git log -G '<pattern>' --oneline`, `git log -p -3 --
   <file>`): a recent commit with the same shape means a reviewer already
   weighed the design. This branch or this week is strong; months old is weak.
6. **Five to ten lines of context** around the hunk.

## Stageable

- **Formatting, import reordering, unused import removal, lint auto-fixes**
  (`let` → `const`).
- **Typo fixes** in strings or comments where the correct word is unambiguous,
  and copy tidies with no semantic change.
- **Dead code removal**: commented-out code, flagged unreachable branches, or a
  file the same diff replaces.
- **Generated-file timestamps** ("Generated on …"). When the file has other
  hunks, route the timestamp alone through stage-hunk and leave the body.
- **Uniform sweeps**: an identical change in three or more files.
- **Additive wiring across files**: a coherent pattern where the target symbol
  already exists (`data-testid={testids.[Name]}`, `data-hydrated` markers).
- **Continuations of a committed pattern**, verified with `git log` to have the
  same shape.
- **Observability**: a project-logger, error-reporting, tracing or metrics call
  with no control-flow change in the hunk, its import confirmed as real
  observability. A log in a previously silent catch counts if return value and
  control flow are unchanged. Also flipping an already-wired observability flag
  to its standard value.
- **Complete additive units**: a new file plus wiring that matches its purpose,
  such as a dev-harness page with its import, a menu entry shaped like its
  siblings, and the render conditional.
- **Orientation docs**: `AGENTS.md`, `CLAUDE.md` or `README.md` additions that
  point at existing files or describe established patterns. Skip one that makes
  a new claim a reviewer would scrutinise.

## Leave for review

- **API or wire contract changes**: response shape (`200` → `204`, `allOf` →
  `oneOf`), endpoint or RPC signatures.
- **Schema or validation changes**: a field made required, a type or enum set
  changed, `null` ↔ `undefined` coercion at a boundary.
- **Database queries and migrations.**
- **Algorithm or encoding changes**: ID alphabet or format, hash, route
  resolution.
- **Config values to weigh** (TTLs, timeouts, feature flags, security policy):
  name the value and the question, e.g. "`[NAME]_TTL` 3600 → 2_592_000 (why 30
  days?)".
- **Secret or credential rotations.**
- **Test assertion changes**: expected values, mocks, snapshots, scaffolding. A
  test file that only adds a new file or docblocks stays stageable.
- **Public symbol renames.**
- **New abstractions whose shape is the design**: a new exported helper, type or
  module.
- **Contract-and-adapter pairs**: one file changes a contract, another adapts.
  Skip both together.
- **Throwaway debug logging**: `console.log`, raw `print`, "here", unpatterned
  `JSON.stringify(...)`.
- **TODO, WARN, FIXME, XXX or HACK markers**: skip the hunk adding, changing or
  sitting beside one, plus the hunks in the same function or call site, with
  "marked incomplete: <quoted marker>".
- **Code smells**: duplication instead of composition, a `zIndex: 9999` wedge,
  a workaround around a root cause (`?? null` to silence a type error, a retry
  loop over a race), a suspicious one-liner in a hot path or export.
- **Smell-adjacent**: a clean hunk wired into a smell, two smells in one file or
  cluster, or a lonely one-liner with no analogue in the diff. Stage a lonely
  one-liner only if it is plainly a typo or lint fix; otherwise skip with
  "smell-adjacent: lonely one-liner, intent unclear from diff".
- **Mixed lines**: skip a single line that fuses a stageable and a reviewable
  change. A hunk with them on separate lines is mixed, not skipped: route it to
  stage-hunk with a line-level description.
- **Merge conflicts** (UU status): leave untouched.

## Process

1. **Inventory the whole diff first.** Run `git status --short` every time,
   including re-runs, and trust it over memory, plus `git diff --name-only` and
   `git diff --stat`. Drop UU and fully staged files. Find cross-file patterns
   with `git diff -G '<pattern>' --name-only` or `git diff -U0`, not by grepping
   `^\+` (which matches context). Name four shapes before any verdict: repeated
   patterns (one decision), additive units (one stage), contract-and-adapter
   pairs (one skip, never split), and lonely changes (most scrutiny).
2. **Classify each file** from `git diff -U5 -- <file>`, read once. Before
   writing a file off, list every hunk with a one-phrase reason; one
   self-evident hunk makes the file mixed.
3. **Stage.** All hunks trivial: `git add <file>`. Some: invoke
   `block65-tools:stage-hunk` through the Skill tool, never its script via
   Bash, with the file on the first line of `args` and a plain-language
   description after:

   ```
   Skill(skill="block65-tools:stage-hunk",
         args="src/[module]/[file].ts\nstage only the two logger.warn additions inside existing catches; leave the [unrelated] refactor")
   ```

4. **Report** two lists, one line per file (per hunk when a file is split),
   each naming its evidence. Pair every high-level reason with the diff detail
   behind it: "risky: response shape changed 200→204", never "risky" alone.

```
Staged:
  additive unit:  <new file + wiring files> — wired via import + menu entry + render line
  uniform sweep:  <N files> — same M-line change, identical in each
  observability:  <file> — logger call; import confirmed, K existing uses in file
Skipped:
  <file A + file B> — contract under review: A defines new RPC headers shape, B adapts
  <file> — config value to weigh: [NAME]_TTL 3600 → 2_592_000 (why 30 days?)
  <file> — marked incomplete: "TODO: [text]" added at line [N]
```
