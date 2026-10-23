---
name: test-suite
description: "Runs the full unit/integration test suite (typically vitest) and end-to-end tests (typically Playwright), then auto-fixes failures iteratively using subagents. Use when the user says 'run all tests', 'run the test suite', 'run e2e', 'fix all tests', 'get tests green', 'run vitest', 'run playwright', or any variation of running + fixing tests across a monorepo. Supports --env dev (default) and --env staging for the e2e target, plus --unit-only and --e2e-only. Also use when the user asks to 'check everything works' or 'make sure nothing is broken'."
---

Run unit/integration tests, then e2e, fixing straightforward failures and
reporting design-level ones without attempting a fix.

Take every command from the `## Testing` section of the repo's `AGENTS.md`:
unit/integration, e2e per environment, and prerequisites per environment. If
the section is missing or incomplete, ask the user for the commands before doing
anything else, instead of inferring them from project structure.

Arguments: `--env dev` (default) or `--env staging` picks the e2e command;
`--unit-only` skips phase 2; `--e2e-only` skips phase 1.

## Phase 1: unit and integration

Spawn a subagent to run the command from the repo root. It returns, per
failure: package or service, test file, test name, assertion message, and the
relevant source lines.

- **Straightforward** (typos, wrong imports, missing mocks, assertion drift from
  a recent code change, type errors in test code): fix, then re-run in this
  session; one command needs no subagent.
- **Design flaws** (architecture, missing features, broken abstractions, test
  infrastructure): collect for the report without fixing.

Stop after 5 rounds or when only design issues remain, and present what is
left. Start phase 2 only on a green unit suite.

While fixing:

- Follow `AGENTS.md` and every standard it references.
- Keep every test running and every assertion as strong as it was: no skip, no
  `.todo()`, no `.toBe(x)` → `.toBeTruthy()`, no `as` cast to silence a type
  error.
- Use the project's package manager (pnpm when `catalog:` entries exist,
  otherwise what `AGENTS.md` names), never `npx`.
- Run the project's formatter on every edited file.
- When a test needs infrastructure that is not running (database, queue, cache,
  container), report it instead of setting it up.

## Phase 2: end-to-end

Spawn a subagent to run the e2e command for the selected env. It returns, per
failure: test file, test name, failing step, error message, and screenshot or
trace paths.

- **Straightforward** (selectors per the project's selector rules, locators
  broken by a recent UI change, stale test data, a missing wait that points at a
  synchronisation bug; never a timeout bump): fix and re-run, up to 5 rounds.
- **Environment issues** (services down, auth unconfigured, network blocked)
  and **design flaws** (broken flows, missing pages, wrong UI behaviour):
  report.

If the project uses Playwright and `playwright-harness:debug` is available,
invoke it before any selector or timing fix.

Check the env's prerequisites first; report missing services or env vars
instead of starting infrastructure. If auth is interactive (magic link from
service logs, OAuth in a real browser, CAPTCHA) and cannot run headless, report
and suggest running those tests by hand.

## Subagent prompts

Include the repo root as working directory, the exact command, a reminder to
follow `AGENTS.md` and its standards, and: "Report back with structured
information, not raw terminal output. Summarise failures but include exact error
messages and file paths."

## Report

- **Fixed**: file, what changed, why.
- **Design issues**: test name, failure, and your assessment of the underlying
  problem.
- **Status**: unit/integration and e2e (with env), each as X passed, Y failed
  (Z design issues), or "skipped".
