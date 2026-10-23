---
name: tidy
description: "Runs the project's code quality pipeline: oxfmt (format), oxlint --fix (lint auto-fix), and typecheck, then fixes the trivially correct issues that remain. Use whenever the user says /tidy, asks to clean up lint/format/type errors, mentions oxfmt/oxlint/typecheck, or wants to tidy code before committing. Also use when the user pastes compiler or lint errors and wants them cleaned up mechanically. Supports '/tidy --typecheck-only' when the user only wants types checked. If the user asks for a report only (e.g. '/tidy --report', 'just check', 'what's broken'), runs the pipeline but reports issues without fixing."
---

Run the pipeline in order and fix only issues with exactly one correct
resolution; report anything uncertain instead.

Modes:

- **Fix** (default): steps 1 to 5.
- **Report** ("just check", "what's broken", `--report`): edit no files. Run
  `pnpm exec oxfmt --check .` and `pnpm exec oxlint .` in place of steps 1 and
  2, then step 3, and report what needs fixing.
- **Typecheck only** (`--typecheck-only`, or asked only about types): steps 3
  to 5, so the diff holds only type fixes.

Scope: workspace-wide, matching the project's justfile targets if any. For a
named package or path use `pnpm exec oxfmt <path>`,
`pnpm exec oxlint <path> --fix` and `pnpm --filter=<package> run typecheck`.
Apply typecheck exclusions listed in the `justfile` or `AGENTS.md`.

## Pipeline

1. **Format**: `pnpm exec oxfmt .`
2. **Lint fix**: `pnpm exec oxlint . --fix`, then `pnpm exec oxlint .` to see
   what remains. Report remaining lint errors without fixing them by hand; what
   `--fix` left is not mechanical.
3. **Typecheck**: `pnpm run typecheck`, output redirected to a file outside the
   repo. Reduce it in the shell (counts by error code and by file) instead of
   reading the whole log, then read the lines you will act on, working from the
   exact message. When errors concentrate in one file or name one exported
   type, fix that root and re-run before touching the cascade.
4. **Fix trivially correct type errors**: one possible action, no behaviour
   change, no design decision.

   - TS6133 on an import: remove the specifier, or the statement if it is the
     only one. Keep side-effect imports (`import "./[file].css"`).
   - TS1484: make it a type-only import, `import { type [Name] }`.
   - TS6198: remove the unused destructured binding; prefix it with `_` only
     when the destructuring itself is needed (a rest pattern).

   Report everything else: type mismatches (TS2322, TS2345), missing
   properties (TS2339), module not found (TS2307), unused variables (TS6133 on
   a non-import, possibly work in progress), any error with more than one valid
   fix, and any whose fix needs a cast, `!`, a ts-comment, `any` or a widened
   type.

5. **Verify**: re-run the checks (or typecheck alone in that mode):

   ```sh
   pnpm exec oxfmt --check . && pnpm exec oxlint . && pnpm run typecheck
   ```

   If the error count rose above step 3's, undo the offending fix and report it.

## Output

What was fixed ("formatted 12 files, removed 3 unused imports"), the error count
before and after with a breakdown by code if any remain, and each remaining
error that needs judgment as file, line and message. Leave out what the tools
do.
