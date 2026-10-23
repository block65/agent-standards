# Vitest Standards

**Prerequisite:** Also follow the rules in [Testing Philosophy](testing.md).

## Rules

- **Fake timers only for time-dependent logic** (debounce, retry backoff), never
  to skip real `await`s. A test that passes only with fake timers points at a
  race in the production code.
- **Pin the meaningful properties.** `toBeDefined()` is rarely the assertion
  meant, and it does not narrow the type. To verify and narrow in one step, use
  `assert` from vitest, with a type-guard predicate for shape checks.
- **Assert the error type, not the message:**
  `await expect(action()).rejects.toBeInstanceOf([ErrorClass])`. When a message
  fragment carries information, regex-match the fragment, never the sentence.
- **Eventual state:** `expect.poll`, never a sleep; await a completion signal
  when the production code emits one.
- **Fixtures** (factories, seed helpers, canned payloads) live in `fixtures.ts`
  or `test/fixtures/*.ts`, imported by the spec.

## Snapshots

Prefer snapshots for shape-heavy output (API responses, parsed config,
normalised payloads): a new field appears in the diff and forces a decision.

- **`toMatchSnapshot`** for data; **`toMatchFileSnapshot`** for content with its
  own syntax (HTML, SQL, generated source), so the file keeps its extension and
  highlighting and avoids `.snap` escaping.
- **Deterministic output.** Cover UUIDs, timestamps, hashes and tokens with
  property matchers (`toMatchSnapshot({ id: expect.any(String) })`) or
  `expect.stringMatching`. When one shape recurs across many tests, register an
  `expect.addSnapshotSerializer` in `vitest.setup.ts`. The system under test
  keeps its real randomness.
- **Let `vitest -u` write the `.snap`;** never hand-write it, since the
  serialised form of asymmetric matchers changes between versions.
- **Update only for a spec change.** Never run `-u` to fix a failure. After
  updating, read every hunk; a change you cannot explain is a bug to investigate
  before committing.

## Coverage per state-changing operation

1. **Happy path**: snapshot with property matchers, or `toMatchObject` when only
   a few fields are contractual.
2. **Permission denial**: call as a principal who is not allowed; assert the
   error type. Read-only operations skip this only when anyone may read.
3. **Not found**: the contract-defined response to a nonexistent ID.
4. **Edge cases**: duplicates, expiry, partial updates, idempotent deletes.
5. **Side effects**: assert the shape of an emitted queue message, event or
   outbound call (capture it with `vi.spyOn`), not just the return value.

## Mocking

- **`vi.mock`** only for modules that own a real boundary (file system,
  network, time), never to swap internal logic.
- **Reset between tests:** set `restoreMocks: true` and `mockReset: true` in the
  vitest config. `vi.restoreAllMocks()` alone restores `vi.spyOn` originals but
  does not reset `vi.fn()` implementations or unmock modules.

## Detecting undeclared dependencies

Applies "Architecture for testability" in [Testing Philosophy](testing.md). Ask:
does the setup change something no production caller changes? `vi.stubGlobal`,
mutating an ambient object to inject a dependency, fake timers used to age
stored state, and writing a module-scope `Map` directly are each a finding about
the code. Match the shape, not the API.

`vi.resetModules()` or a batch of dynamic imports is the costly form: the module
registry is process-global, so a fresh instance costs a graph rebuild and every
module holding a reference must re-import in the same batch.

BAD: rebuilds the module graph to reset a module-scope memo, and mutates a
global to inject the client.

```ts
test("[behaviour]", async () => {
	vi.resetModules();
	const { loadSettings } = await import("./settings.ts");
	Object.assign(env, { STORE: { fetchDoc } });

	await expect(loadSettings()).resolves.toMatchSnapshot();
});
```

GOOD: the cache is a value, so its owner picks the lifetime; production builds
it once at startup.

```ts
test("[behaviour]", async () => {
	const cache = createSettingsCache({ store: { fetchDoc }, now: clock.now });
	await expect(loadSettings({ cache })).resolves.toMatchSnapshot();
});
```
