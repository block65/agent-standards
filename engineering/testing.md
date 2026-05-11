# Testing Philosophy

Tests are diagnostic instruments. Their job is to *try to break the system* and surface what's wrong — not to validate that today's code works. The win condition is a system robust enough that you cannot break it, not a green check.

## Mental model

- **Tests are adversaries, not gates.** Structure them to expose problems, not to pass. A test that is hard to fail was written backwards.
- **Green ≠ working. Red = signal.** A passing test only tells you the cases you wrote pass. A failing test tells you something specific about the system. Treat red as the more valuable outcome — that's where you learn.
- **Fix the code under test by default.** When a test fails, the default response is to fix the code under test. Adjusting the test — narrowing assertions, seeding randomness, skipping cases, retrying — is hiding a defect. The only legitimate reason to change a test is that the **contract** genuinely changed (new spec, deprecated behaviour); document why in the diff.
- **Test the system, not a simulation of it.** Drive the production code path. Mocks belong at the network boundary, not inside the unit under test.
- **Failures must be loud and observable.** Swallowing an error, returning `undefined`, or "recovering" silently is a bug, not robustness. Surface what happened — error type, status, UI feedback.

## One test per failure mode

A test earns its place only if it can fail on a bug no other test catches. Before adding one, name the failure mode it surfaces that the rest of the suite would miss. If you can't, don't add it.

- **When two tests cover the same failure, delete the lower-level one.** The test closest to the user contract owns the behavior. The same happy path asserted at unit, integration, and e2e is one signal carried by three failures — three things to maintain, zero extra bugs caught.
- **Exception: the lower-level test reaches a branch the higher one can't** — a rare error path, a race, a numerical edge. The retained test must do something the higher-level test *cannot*, not the same thing faster.

```ts
// ❌ Same happy path, three layers, one bug surface
test('validateItem accepts a valid item', ...)
test('createItem persists a valid item', ...)
test('POST /items creates an item', ...)

// ✅ Keep the test closest to the contract; the others add no failure mode
test('POST /items creates an item', ...)
```

## Non-negotiable inputs

- **Real randomness, every run.** UUIDs, timestamps, faker output without a fixed seed. No canonical "Test User" that papers over collisions. A test passing once with `id: 1` tells you nothing about the id a real user generates. **Print the seed/inputs on failure** so flakes are reproducible — randomness without traceability is just noise.
- **Real user flows.** Drive the system through its public surface — API, UI, CLI. No backdoors that bypass the layers under test.
- **Real failure modes.** Empty inputs, oversized inputs, concurrent writes, dropped connections, malformed payloads. Don't test only the shapes that work.

## Hard rejects

These are responses to a failing test, not fixes:

- Loosening an assertion so it passes
- Seeding randomness to "stabilise" a test
- `test.skip` / `it.todo` / `.only` left in committed code
- Adding retries to mask a race
- **Raising a timeout to absorb a flake** (see "SLOW = FAIL" below)
- Catching exceptions in the test to keep it green
- Mocking past a real boundary to dodge an error

If a test fails, the system has a bug. Fix the system.

## SLOW = FAIL

A test that's flaky on a 5-second timeout but green on a 30-second timeout has not been fixed. The system has a real problem — a race condition, resource saturation, an unbounded retry — and you've buried it in latency. The next time it's slow it'll cross the new threshold too, and the suite that used to take 2 minutes now takes 15 and still fails.

- **Treat latency as a failure mode.** If an operation that should be instant is taking seconds, the test has discovered something real. Investigate the system, not the timeout.
- **Never raise a timeout to absorb a flake.** Find the actual completion signal (see "Observing vs. asserting") or fix the saturation in the product.
- **Default budgets are signals.** Playwright's `actionTimeout`, vitest's per-test timeout, `expect.poll` timeouts — these are the slack the framework has already given you. If you need more, the framework is telling you something.
- **Measure before tuning.** When parallel runs flake, the answer is rarely "more time per test" — it's "what resource is saturating at this concurrency?" Profile the run, find the bottleneck, fix it. Raising parallel timeouts to mask saturation makes the suite slower and still red.

## Observing vs. asserting

There is one legitimate kind of test change: sharpening *how* the test observes the system, without changing *what* it asserts.

- **Cheating (banned):** widening assertions, mocking past the boundary, swallowing errors, stubbing the thing under test, reducing scope.
- **Sharpening observation (allowed):** awaiting the actual completion signal the production code emits instead of polling shared state; subscribing to an event instead of guessing when it's done; using a deterministic readiness signal already part of the production surface.

The contract under test must stay the same. If the production code breaks, the test must still go red — ideally with a clearer failure (a timeout that names the awaited event beats an empty-array surprise).

## Architecture for testability

- **Concrete over abstract.** Avoid DI containers and interface/trait abstractions added "for testing" — they add complexity to dodge work that should be done by separating pure logic from boundaries.
- **Pure logic.** Move business logic into pure functions that take data and return data. Test via input/output assertions, no mocks needed.
- **Move boundaries, don't mock past them.** If a unit is too hard to test without mocking its internals, the boundary is in the wrong place. Refactor.

## Boundary mocking

- **Network, not client.** Mock at the network boundary, not the internal client boundary.
- **Protocol fidelity.** Intercept the transport layer (HTTP/TCP) so serialization, headers, and status codes are exercised end-to-end.
- **Two-or-three-mocks limit.** If a test requires more than 2-3 mocks to function, the architectural boundary is misplaced. Refactor before adding a fourth.
- **Never test the mock.** If most of the test is setup and assertion of mock behaviour rather than system behaviour, the test has no diagnostic value.
- **Real backing services where you can.** For tests that touch a database, queue, or cache, run the real thing in a container (testcontainers) — not an in-memory fake. Fake Postgres has different semantics from real Postgres; a test that passes against the fake is not the test you wanted.

### TypeScript (Node.js / Cloudflare)
- Use `msw` (Mock Service Worker). Intercepts at the request layer so the same handlers cover Node, browsers, and Workers. Don't reach for `undici`'s `MockAgent` or `fetchMock` — they intercept below the app's `fetch` and miss serialization bugs `msw` catches.

### Rust
- Use `wiremock`. Start a local mock server and point your concrete client at the local URL.
