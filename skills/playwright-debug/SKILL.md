---
name: playwright-debug
description: Diagnose failed Playwright e2e tests by reading the @block65/playwright-harness summaries — not by tailing logs, extracting traces, or raising timeouts. Trigger when the user says "the test failed", "why did the test fail", "investigate the e2e failure", "what broke", "debug the playwright run", or any variant of "look at the latest test failure". Also trigger after running tests via pnpm test / pnpm exec playwright when Playwright reports any failed/timedOut tests, and when the user claims a test is "slow" or "flaky" — these need numerical refutation, not adjective answers.
---

# Debugging Playwright failures

This project uses `@block65/playwright-harness`. Every test run writes
agent-readable Markdown summaries to `<e2e-dir>/.last-run/`. **Use those
files instead of grep/tail/sed against stdout or `trace.zip`.**

## What lives under `.last-run/`

| File | When written | What it contains |
| --- | --- | --- |
| `failures.md` | every run | Index of failed tests + "tests that ran" table on green runs |
| `failures/<slug>.md` | failures only | Per-failure detail: error, page errors, console, 4xx/5xx, slowest action/request, timeline, time budget, artifacts |
| `passes/<slug>.md` | passes with trace | Per-pass anti-claim summary: verdict + slowest action/request + time budget |
| `timings.md` | every run | Per-test latency table: backend p50/p95, frontend p50/p95, slowest action, slowest backend |
| `trends.jsonl` | every run (append) | One row per test per run, ring-buffered (50/test). Read by `compare`. |
| `logs.md` | failures + logSources configured | Service-side logs interleaved by timestamp, delta-between-entries column |
| `sources.json` | runs with logSources configured | Source list the `logs` subcommand reads by default |
| `report.json` | every run | Playwright's built-in JSON report (structured) |

## The exact debugging procedure

1. **Find the e2e root.** Usually `tests/e2e/`. If the command line says
   `cd tests/e2e && pnpm test ...`, that's it.

2. **Read the failure index first.**
   ```
   Read <e2e-dir>/.last-run/failures.md
   ```
   On a green run it says `0` failures and lists tests that ran — don't
   invent a problem. On a red run it links per-failure detail.

3. **For each failure, read `failures/<slug>.md`.** It contains, in order:
   - Test title, spec, project, status, duration, timeout
   - **Anti-timeout guidance** — one sentence naming the most likely cause
   - The Playwright error message (assertion, timeout)
   - **Browser page errors** — uncaught JS in the page
   - **Console errors / warnings** — from `console.error` / `console.warn`
   - **Network failures** — 4xx/5xx with status, method, URL, ms. Also
     surfaces requests that never resolved (`statusText: "(no response)"`).
   - **Slowest requests** — top 5 with median context
   - **Failing actions** — Playwright calls that errored; *incomplete*
     actions (killed by timeout/crash) are tagged so they aren't missed.
     Each failing action includes Playwright's **actionability log** — the
     internal step-by-step ("attempting click action", "element is outside
     of the viewport", "retrying click action") that tells you EXACTLY
     why the retry loop failed. Highlighted phrases like *outside of the
     viewport* / *intercepts pointer events* / *not stable* are the actual
     cause. The error message is usually just "Timeout exceeded" — the
     actionability log is where the truth lives.
   - **Slowest actions** — top 5 with median context
   - **Timeline at failure** *(only on timeout / interrupted / incomplete)* —
     the last ~2.5s of events before the test died, time-ordered
   - **Time budget** — % of test duration in navigation / waiting on UI /
     user interactions / other. Distinguishes "test is mis-waiting" from
     "app is slow".
   - Artifact paths (trace.zip, screenshot, video, error-context.md)
   - Link to `logs.md` if service logs were configured

4. **Diagnose from the data, in this priority order:**
   1. **Page errors** — the browser threw an uncaught error. Page never
      finished mounting, subsequent assertions never had a chance. Fix the
      JS error in the app.
   2. **Network failures (4xx/5xx or "no response")** — backend call failed.
      Frontend was reacting to a server error. Read `logs.md` if present;
      otherwise check service logs (see below). The test is correctly red.
   3. **Service-side warnings/errors in this test's window** — the section at
      the bottom of the per-failure md. If it's non-empty, **read every entry
      before drawing conclusions**. The textbook trap is a webhook endpoint
      that returns 200 even when its inner validation fails: the network
      table looks clean but the service logged the real cause. The "Network
      failures" priority above is necessary but not sufficient — a service
      log WARN/ERROR can be the failure cause even when no 4xx/5xx fired.
   4. **Slowest action ≥ 5s** — the named action took anomalously long
      compared to median. Investigate **what made it slow**: a request that
      didn't return, a render that didn't paint, a focus that didn't arrive.
      The slow step itself is the bug.
   5. **Slowest request ≥ 5s** — the named endpoint is slow. The server is
      the problem; the test waited correctly.
   6. **No page errors, no network failures, no service warnings, fast
      actions** — re-read the error message and screenshot. Likely a
      selector/timing issue: element never rendered, rendered without the
      expected accessible name, or the a11y tree was scoped by a modal
      dialog backdrop (see the project memory's modal-aria-hidden gotcha).

## Defending against adjective-only claims

Before saying any of these in a report, you **must** cite specific numbers.
Adjectives without numbers are not a diagnosis.

| Claim | What to cite |
| --- | --- |
| "The test is **slow**." | Row from `timings.md` showing duration + backend p50/p95 + slowest action. Or `passes/<slug>.md`'s verdict line. |
| "The backend is **slow**." | The backend p95 + "slowest backend" cells. If p95 < 500 ms, the backend isn't slow — re-diagnose. |
| "The test is **flaky**." | Output from `pnpm exec playwright-harness compare <test>`. If pass-rate is ≥ 90% over recent runs, it's a **specific regression**, not flake. |
| "There's a **race condition**." | The timeline section + the network call that arrived after the assertion fired. Both in the per-failure markdown. |
| "The page is **flickering / re-rendering / shifting**." | Re-renders in React/Vue/Svelte do NOT cause layout shift by default — the reconciler diffs into existing DOM nodes with the same dimensions. If you're tempted to blame "re-renders", the trace's **actionability log** for the failing action tells you the real reason (e.g. *element is outside of the viewport*, *intercepts pointer events*). A click that fails 30+ times across 20 seconds isn't a button that keeps moving — it's a button that was never in the right place. Read the log; don't speculate about a layout shift you didn't observe. |
| "Transient / dev-server slowness / cold paths / miniflare / workerd / vite / hot-reload." | None of these are a diagnosis. They're a refusal to look. The failure either had a slowest action ≥ a threshold (cite the row from the per-failure md or `timings.md`) or it didn't. If it didn't, the cause isn't slowness — re-diagnose. **Dev-server hand-wave claims need the same numerical citation as everything else.** If `compare <test>` shows 9/10 passes, the one red isn't "the dev server" — it's a specific event that didn't fire on this run. |
| "I cannot pinpoint this from harness data alone." | Acceptable **only** after you've named every section you checked and what each one said. "No 4xx/5xx, no console errors, no service WARN/ERROR" is not a check of the harness data — it's a partial check. Did you also look at the slowest action's `target`, the in-window service-log section (which can be empty *and still informative*), the time budget, the ★-marked critical-path requests, the timeline-at-failure section if status=timedOut, and the `(no response)` rows in the network-failures table for stuck-in-flight requests? If you skipped any, the claim is premature. |
| "The SSE / streaming endpoint is **hung**." | A `text/event-stream` (or other streaming) endpoint showing as `(no response)` / `-1ms` is the protocol working as designed — the connection is held open for the test's lifetime. The trace can see the connection state but **not** whether events are flowing. Four indistinguishable cases from trace alone: (a) connection healthy + events flowing + client handles them, (b) connection healthy + events flowing + client drops them, (c) connection healthy + no events emitted, (d) connection genuinely stuck. Two ways to tell which: the `## Streaming activity` section in the per-failure md (present when the project uses `@block65/playwright-harness/fixtures` — gives byte counts and last-chunk timestamps); the in-window service-log section / `logs.md` (only useful if the project's server logs emit lines). If neither is available, ask before guessing. |

If you cannot cite the relevant cell, the claim is unsupported — say so and
stop, do not retry-and-hope.

## Do not weaken assertions to make a red test green

When an assertion fails, the **first instinct must be to diagnose why** — not
to replace it with a softer assertion that happens to pass. The original
assertion is load-bearing; it was chosen by an earlier author to prove a
specific behavior. A passing assertion that doesn't prove that same behavior
is a regression even when the test is "green".

**The failure modes to watch for in yourself:**

| What you were tempted to do | Why it's wrong |
| --- | --- |
| `toHaveCount(N)` → `toBeVisible()` on a different element | Count assertions verify the **data layer** ("N rows exist", "exactly one charge fired"). Visibility of a sibling/parent proves the UI rendered something; not that the action that *should* have produced N items actually did. If the duplicate-prevention is broken, the visibility assertion still passes. |
| `toHaveText("exact thing")` → `toBeVisible()` | Was specific content under test? Then content matters — drop to `toContainText(/shape/i)`, not visibility. |
| `getByRole(specific)` → `getByRole(generic)` or `.first()` | The original selector encoded *what* the user is looking at. Generic + `.first()` matches whatever is on screen — not necessarily the thing under test. |
| `toHaveURL(...)` → anything | URL assertions were banned to begin with (see Block65 Playwright standard). If you're tempted to "fix" a URL assertion by weakening it, delete it instead — the next action's auto-wait verifies arrival. |
| Removing an assertion entirely | If the original assertion was load-bearing, deletion = silent regression. If the assertion was always wrong (e.g. asserting on a URL), say so explicitly in the diff: "Removing per Block65 Playwright standard rule X." |

**The protocol when an assertion fails:**

1. Read the per-failure markdown. The actual cause is named (page error,
   4xx/5xx, slow step, console error).
2. If the cause is in the **app**, fix the app. Do not touch the assertion.
3. If the cause is the assertion being **wrong** (e.g. the design changed and
   the test was never updated), update it to a *more-specific* assertion that
   reflects the new design — not a *weaker* one. Cite the design change in
   the test comment.
4. If you genuinely cannot tell whether the assertion or the app is wrong,
   stop and ask. The cost of a "green test that doesn't test anything" is
   far higher than the cost of pausing for a human.

A useful self-check: "If the behavior under test silently broke tomorrow,
would my new assertion catch it?" If the answer is *no*, the new assertion is
wrong, regardless of whether it's green today.

## CLI commands

```sh
# Inspect a specific test-results dir (ad-hoc, when no fresh .last-run/)
pnpm exec playwright-harness trace --latest
pnpm exec playwright-harness trace <slug-prefix>
pnpm exec playwright-harness trace --list

# Trend / flake refutation
pnpm exec playwright-harness compare                  # all tests in buffer
pnpm exec playwright-harness compare create-listing   # filter substring
pnpm exec playwright-harness compare --last 10        # only last 10 runs
pnpm exec playwright-harness compare --json           # machine-readable

# Service logs (multi-source, interleaved, time-windowed)
pnpm exec playwright-harness logs                     # uses sources.json
pnpm exec playwright-harness logs --min-severity warning
pnpm exec playwright-harness logs --window <iso-from>..<iso-to>
pnpm exec playwright-harness logs --source '{"name":"x","command":"...","format":"tilt"}'
```

## Prefer harness primitives over bash

Every shell command (`bash`, `tail`, `grep`, `for`, `awk`, `unzip`, `cat`,
custom scripts) triggers a permission prompt and blocks automated runs.
That's not a style preference — it's a hard cost. **Before reaching for
bash, check whether the harness or Playwright itself has the primitive you
need.** If it does, use it; the invocation is allow-listed and won't block.

| What you were about to bash | Use this instead |
| --- | --- |
| `for i in 1 2 3; do pnpm exec playwright test … done` (sample pass-rate) | `pnpm exec playwright test … --repeat-each 3`. Playwright runs the spec N times sequentially, all results land in `trends.jsonl`, then `playwright-harness compare <test>` reads the result. |
| `tail`/`grep` server logs by hand | `pnpm exec playwright-harness logs [--grep <pat>] [--min-severity warning] [--window <a>..<b>]` |
| Pipe `tilt logs …` / `wrangler tail …` through `grep` | Define a `logSource` in `defineReporter({...})`; the reporter persists it to `sources.json` so the `logs` subcommand picks it up automatically. |
| `unzip trace.zip` / `bsdtar -xf` | `pnpm exec playwright-harness trace --latest` (or a slug-prefix) |
| `cat`/`head`/`tail` a `.last-run/` file | `Read` directly — the tool already takes a path |
| Roll your own pass-rate calc from logs | `pnpm exec playwright-harness compare <test>` |
| Diff this run vs last run by hand | Same — `compare` shows drift over the trend buffer |

The harness is "complete" when an agent never has to reach for bash to
debug a test failure. If you find yourself doing so and there's no clear
harness equivalent, that's a genuine gap — flag it; don't paper over with
a shell pipeline that requires a human to approve every prompt.

## Don't decline work on stale assumptions

Before refusing to run a test, project, or command on grounds of "this needs
human intervention" / "this is interactive" / "this requires manual setup",
**run it once** and see what actually happens. Setup that used to require a
human (auth codes, captchas, payment confirmations) is usually the first
thing a team automates — and notes about "this is interactive" are usually
stale relative to the current implementation.

A useful self-check before declining:
- Does the relevant `*.setup.ts` / fixture / `globalSetup` file exist?
- Does it read from anything that looks like an automation source — server
  logs, a test mail server, an API client, a service in `test-mode`?
- Has the project run successfully in another session — `.last-run/timings.md`
  shows a passing entry, `trends.jsonl` has rows for tests in that project,
  prior commits/PRs touched specs under it?

If any of those is yes, run the project once before refusing. The cost of a
single failed run is far smaller than the cost of skipping a project that
would have caught a real regression.

## Things you must not do

- **Do not raise `actionTimeout`, `navigationTimeout`, or `timeout`** to
  make a slow test pass. SLOW = FAIL. The failure summary names the slow
  step; fix that.
- **Do not `tail`, `grep`, `sed`, `awk`** stdout, log files, or `trace.zip`
  contents. Every piece of data you need is in the per-test markdown or
  `logs.md`. If something is missing, that's a harness gap — flag it; don't
  paper over with shell improvisation.
- **Do not add `retries`** to absorb a flake. A test that needs retries
  has a race condition or a wait-on-the-wrong-thing bug. Use `compare` to
  prove flakiness before claiming it.
- **Do not extract `trace.zip` manually** with `unzip` / `bsdtar`. Use
  `playwright-harness trace`.
- **Do not delete `.last-run/` or `test-results/`** to "clean up". The next
  run overwrites them. Leaving them helps the user re-inspect.

## When the summary points to a backend cause

`.last-run/logs.md` (auto-written when failures + `logSources` configured)
shows service logs interleaved by timestamp with delta-between-entries —
read that first.

If logs.md isn't present or you need more lines, use the CLI:
```
pnpm exec playwright-harness logs --min-severity warning
```
This reads `.last-run/sources.json` (set by the project's reporter
config) and runs each command, parsing per-source format.

Only fall back to running `tilt logs <service>` / `wrangler tail <service>`
directly when the harness logs are insufficient — and then tee the output
to a file under `.last-run/` so it survives for the next read.

## After diagnosing

Tell the user **what broke** (page error / failed endpoint / slow step),
**why it's the cause** (cited from the summary), and **what to fix** (the
app code, the service, the data). Don't propose timeout bumps. Don't
propose adding `expect.toHaveURL`. Don't propose `page.goto` to a deep link.
The harness exists so you have enough data to give a real diagnosis on the
first try.
