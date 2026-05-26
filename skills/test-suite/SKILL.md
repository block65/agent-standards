---
name: test-suite
description: "Run the full unit/integration test suite (typically vitest) and end-to-end tests (typically Playwright), then auto-fix failures iteratively using subagents. Use this skill when the user says 'run all tests', 'run the test suite', 'run e2e', 'fix all tests', 'get tests green', 'run vitest', 'run playwright', or any variation of running + fixing tests across a monorepo. Supports --env dev (default) and --env staging for the e2e target. Also trigger when the user asks to 'check everything works' or 'make sure nothing is broken'."
---

# Test Suite Runner

Run unit/integration tests then end-to-end tests sequentially across the repo, using subagents for execution. Fix straightforward failures automatically; report design-level issues back to the user without attempting a fix.

The skill is project-agnostic — it provides the orchestration shape (phased run, fix-then-retry loop, failure classification). The actual commands come from the consuming repo's `AGENTS.md`. The default Block65 toolchain is vitest for unit/integration and Playwright for e2e, but the skill never invokes those tools directly — it runs whatever `AGENTS.md` says to run.

## Project setup the skill expects

The repo's `AGENTS.md` must define a `## Testing` section with the commands this skill will invoke. Expected shape:

```markdown
## Testing

- **Unit/integration:** `<command>` (run from repo root)
- **E2E dev:** `<command>` (e.g. `cd tests/e2e && pnpm test:dev`)
- **E2E staging:** `<command>`
- **Prerequisites (dev):** any services that must be running (e.g. `tilt up`, a local DB container)
- **Prerequisites (staging):** any env vars or credentials
```

If the section is missing or incomplete, stop and ask the user what commands to run before doing anything else. Don't guess command shapes from project structure.

## Arguments

- `--env dev` (default) — run e2e against the project's "dev" environment
- `--env staging` — run e2e against the project's "staging" environment
- `--unit-only` — skip e2e, just run unit/integration
- `--e2e-only` — skip unit/integration, just run e2e

## Argument handling

Parse the arguments string for flags. If `--e2e-only`, skip Phase 1. If `--unit-only`, skip Phase 2. If neither, run both.

## Phase 1: Unit and integration tests

Skip this phase if `--e2e-only` was passed.

### Execution

Spawn a subagent to run the unit/integration command from `AGENTS.md`'s `## Testing` section, from the repo root (the cwd this skill was invoked in). The subagent should:

1. Run the command and capture full output.
2. If all tests pass, report success and proceed to Phase 2.
3. If tests fail, extract per-failure: which package/service, test file, test name, assertion message, the relevant source lines.

### Fixing unit/integration failures

For each failure:

- **Straightforward fixes** (typos, wrong imports, missing mocks, assertion drift from a recent code change, type errors in test code): fix directly and re-run.
- **Design flaws** (architectural problems, missing features, broken abstractions, test infrastructure issues): collect into a report for the user — do NOT attempt to fix.

After fixing, re-run via another subagent. Repeat until green or until only design-level issues remain.

Cap at 5 iterations. If still failing after 5 rounds, stop and present the remaining failures.

### Rules for fixing

- Read `AGENTS.md` and follow all standards it references — including any module-specific rules like `engineering/vitest.md`, `engineering/testing.md`, `lang/typescript.md`.
- Never use `as` type casts to paper over failures — fix the underlying type.
- Never skip or `.todo()` a test to make it pass.
- Never weaken assertions (e.g. replacing `.toBe(x)` with `.toBeTruthy()`).
- Use the project's package manager exclusively (pnpm if `catalog:` entries are present, otherwise whatever `AGENTS.md` mandates) — never reach for `npx`.
- Run the project's formatter on every file edited (whichever `AGENTS.md` specifies).
- If a test needs infrastructure that isn't running (database, queue, cache, container), report to the user rather than trying to set it up.

## Phase 2: End-to-end tests

Skip this phase if `--unit-only` was passed.

After Phase 1 is green (or skipped), run the e2e command for the selected `--env`. Look up the command in `AGENTS.md`'s `## Testing` section by environment name.

### Execution

Spawn a subagent to run the appropriate e2e command. It should:

1. Run the command and capture full output.
2. If all tests pass, report success.
3. If tests fail, extract per-failure: test file, test name, the step that failed, error message, screenshot/trace paths.

### Fixing e2e failures

Same assessment approach as Phase 1:

- **Straightforward fixes** (wrong selectors per the project's selector rules, locator mismatches from a recent UI change, stale test data expectations, missing UI waits that suggest a synchronisation bug — not a timeout bump): fix and re-run.
- **Environment issues** (services not running, auth not configured, network blocked): report.
- **Design flaws** (broken user flows, missing pages, fundamentally wrong UI behaviour): report.

Cap at 5 iterations.

If `block65-tools:playwright-debug` is available and the project uses Playwright, invoke it before attempting any selector- or timing-related fix — it reads the harness summaries and gives a real diagnosis on the first try.

### Environment prerequisites

Read the `Prerequisites` lines for the selected env from `AGENTS.md`. If services must be running and aren't, or required env vars are missing, report to the user — do not try to spin up infrastructure.

If the env's auth setup is interactive (magic-link capture from service logs, OAuth in a real browser, CAPTCHA), and the subagent can't drive it headlessly, report and suggest running those tests manually.

## Reporting

After both phases complete, present a summary.

### What was fixed
List each fix: file, what changed, why.

### Design issues found
List issues needing human decision-making. Include the test name, the failure, and your assessment of what the underlying problem is.

### Final status
- Unit/integration: X passed, Y failed (Z design issues) — or "skipped" if `--e2e-only`
- E2E (env=<name>): X passed, Y failed (Z design issues) — or "skipped" if `--unit-only`

## Subagent prompts

When spawning subagents, include in every prompt:

- Working directory: the repo root from which this skill was invoked (cwd).
- The exact command to run (from `AGENTS.md` `## Testing`).
- A reminder to follow `AGENTS.md` and its referenced standards modules.
- "Report back with structured information, not raw terminal output. Summarise failures but include exact error messages and file paths."
