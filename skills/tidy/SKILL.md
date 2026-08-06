---
name: tidy
description: "Run the project's code quality pipeline: oxfmt (format), oxlint --fix (lint auto-fix), and typecheck — then fix the trivially correct issues that remain. Use this skill whenever the user says /tidy, asks to clean up lint/format/type errors, mentions oxfmt/oxlint/typecheck, or wants to tidy code before committing. Also use when the user pastes compiler or lint errors and wants them cleaned up mechanically. Supports '/tidy --typecheck-only' when the user only wants types checked. If the user asks for a report only (e.g. '/tidy --report', 'just check', 'what's broken'), run the pipeline but report issues without fixing."
---

# Tidy: Format, Lint, Typecheck

Run the project's code quality pipeline and fix issues where there is exactly one correct resolution. The goal is zero false moves — if you're not certain, report the error instead of fixing it.

## Mode

**Default: fix.** Run the pipeline and fix what's safe, report the rest.

**Report mode:** If the user asks to just check or report (e.g. "just check", "what's broken", "--report"), run the same pipeline but don't edit any files — only report what would need fixing.

**Typecheck only:** If the user passes `--typecheck-only` or asks only about types, skip steps 1 and 2 and run steps 3 to 5. Formatting and lint fixes rewrite files, so skipping them keeps the diff limited to type fixes.

## Pipeline

Run in order. Each step can produce fixes that affect later steps.

### Step 1: Format

```sh
pnpm exec oxfmt .
```

Rewrites files in place. Deterministic and always correct.

### Step 2: Lint fix

```sh
pnpm exec oxlint . --fix
```

Applies oxlint's built-in auto-fixes — mechanical transforms the linter guarantees preserve semantics.

After this step, run lint again without `--fix` to see what remains:

```sh
pnpm exec oxlint .
```

Remaining lint errors after `--fix`: report them. Don't attempt manual fixes for lint rules — if `--fix` didn't handle it, it's not mechanical.

### Step 3: Typecheck

```sh
pnpm run typecheck
```

A workspace typecheck can emit thousands of lines, and one bad declaration usually accounts for most of them. Redirect the output to a file outside the repo and reduce it in the shell — counts by error code, counts by file — rather than reading the whole log into context. Then read the lines you intend to act on. Work from the exact message, never a paraphrase.

Fix the root cause before the cascade. When the errors concentrate in one file, or name one exported type, correct that and re-run; the downstream errors usually go with it.

### Step 4: Fix trivially correct type errors

Fix ONLY errors where the resolution is unambiguous — one possible action, no behavior change, no design decision.

**Safe to fix:**

| Error                                     | Fix                                                                                                                                                                                                |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TS6133** — unused import                | Remove the import specifier (or entire statement if it's the only one). Never remove side-effect imports (`import "./foo.css"`, `import "reflect-metadata"`) — those exist for their side effects. |
| **TS1484** — type-only import needed      | Add `type` to the import: `import { type Foo }`                                                                                                                                                    |
| **TS6198** — unused destructured variable | Prefix with `_` only if the destructuring itself is needed (e.g. rest pattern). Otherwise remove the binding.                                                                                      |

**Never do any of these to silence an error:**

- `as` or `as unknown as` (cast)
- `!` (non-null assertion)
- `@ts-ignore` or `@ts-expect-error`
- `any`
- Widening a type to make it fit

These are all banned by the codebase standards. If the fix requires one of them, it's not a trivial fix.

**Report these — do not fix:**

- Type mismatches (TS2322, TS2345)
- Missing properties (TS2339)
- Module not found (TS2307)
- Unused variables (TS6133 on non-imports) — these may be work-in-progress
- Anything requiring you to choose between multiple valid approaches

#### Delegating the fixes

Applying the table is mechanical, but it means reading every affected file. When that reading would cost more than a subagent's prompt does, spawn one on the cheapest model that can do the work. Give it the error lines verbatim, the safe-fix table, and the banned patterns, and hold it to the table — anything outside comes back as a report, not a decision. Ask for `file:line` and what changed.

### Step 5: Verify

Re-run the pipeline — typecheck alone, if that was the mode.

```sh
pnpm exec oxfmt . && pnpm exec oxlint . && pnpm run typecheck
```

Compare the error count against step 3. If it went up, your fixes introduced new errors: undo the offending fix and report it instead.

## Output

Keep it brief:

1. What was fixed (e.g. "formatted 12 files, removed 3 unused imports, added `type` to 2 imports")
2. Error count before and after, and the breakdown by error code if there are still errors
3. Remaining errors that need human judgment — file, line, error message

Don't explain what the tools do. The user knows.

## Scoping

Default: workspace-wide, matching the project's justfile targets if one exists.

If the user names a specific package or path, scope to it:

- `pnpm exec oxfmt <path>`
- `pnpm exec oxlint <path> --fix`
- `pnpm --filter=<package> run typecheck`

If the project's `justfile` or `AGENTS.md` lists typecheck exclusions, apply them. Otherwise typecheck everything.
