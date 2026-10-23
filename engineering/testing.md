# Testing Philosophy

Tests exist to break the system. A pass confirms only the cases written; a
failure is the signal, so structure each test to expose a defect.

## A failing test means the system has a bug

Fix the code under test. Change what a test asserts only when the contract
changed (new spec, deprecated behaviour), and say why in the diff. These are not
fixes:

- Loosening an assertion, or one so loose it cannot fail
- Fixing a seed to stabilise a test
- Adding retries to mask a race
- Raising any timeout (per-test, action, poll) to absorb a flake
- Catching exceptions in the test to keep it green
- Mocking past a real boundary to dodge an error
- Leaving `test.skip` or `.only` in a committed spec

A failure the code swallows (returns `undefined`, recovers silently) is a bug:
surface the error type, status or UI feedback.

## Slow is a failure

A test flaky at 5 seconds but green at 30 still hides a race, saturation or
unbounded retry. Treat latency as a finding: investigate the system, or await
the real completion signal. When parallel runs flake, find the resource that
saturates at that concurrency and fix it.

## Observing vs. asserting

The one legitimate test change sharpens _how_ the test observes without changing
_what_ it asserts: await the completion signal the production code emits (an
event, a promise, a readiness signal already on the production surface) instead
of sleeping or polling shared state. If the production code breaks, the test
must still go red.

## One test per failure mode

Add a test only when you can name the bug it catches that no other test does.
When two tests cover the same failure, delete the lower-level one: the test
closest to the user contract owns the behaviour. Keep a lower-level test only
when it reaches what the higher one cannot (a rare error path, a race, a
numerical edge). Input permutations (validation shapes, copy variants) live at
unit or component level; e2e keeps one representative shape.

## Inputs and data

- **Real randomness, every run.** UUIDs, timestamps, faker with no fixed seed;
  no canonical "Test User". Log the seed or inputs on failure so a flake can be
  reproduced.
- **Real failure modes.** Cover empty, oversized, concurrent, dropped and
  malformed inputs, not only the shapes that work.
- **Each test owns its data.** Generate unique identifiers per test; no shared
  mutable state, and no `beforeAll` mutation another test relies on. Two
  parallel runs of the suite must never collide.
- **Setup drives production code.** Helpers and fixtures create state through
  the production API (a `[seed]` helper calls `[create]`). Write to the
  backend directly only for states the application cannot produce: expired
  rows, orphaned references, corrupted state.
- **Name tests by behaviour.** The title says what the caller or user observes,
  not which function or request runs.

## Architecture for testability

A test is a second caller. Code that cannot be tested through its public surface
is a code problem; code that cannot be tested the way you first tried is usually
a harness problem. Tell them apart by what had to change to reach the behaviour:

- **Harness cost** (fix the harness): arguments, containerised backing services,
  intercepted requests, a wrapper the production caller also applies.
- **Code problem** (fix the code): resetting the module registry, assigning onto
  a global, replacing the clock, mocking an internal function. Module-scope
  state, values read off a global and the current time are inputs the code takes
  without accepting; construct and pass them so the caller owns the lifetime.

Separate pure logic from boundaries instead of adding DI containers or
interfaces for testing. Domains that resist observation (concurrency, rendering,
hardware) need a better harness; leave them whole rather than splitting a unit
so mocks fit between the parts.

## Boundary mocking

- **Mock the network, not the client.** Intercept HTTP so serialisation, headers
  and status codes run. TypeScript: `msw`, whose handlers run in Node, browsers
  and Workers (not `undici` `MockAgent` or `fetchMock`, which are Node-only).
  Rust: `wiremock`, with the concrete client pointed at its URL.
- **Real backing services.** Run the database, queue or cache in a container
  (testcontainers), not an in-memory fake with different semantics.
- **More than 2-3 mocks means a misplaced boundary.** Refactor before adding a
  fourth. A test that mostly sets up and asserts mocks tests nothing.
