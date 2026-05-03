# Vitest Standards

Also load: `engineering/testing.md` (testing philosophy and mocking rules).

Vitest is the unit and integration test surface for TypeScript projects — pure logic, modules, and small system slices that don't need a browser.

## Non-negotiables

1. **Never use `vi.useFakeTimers()` to dodge real async.** Fake timers are for testing time-dependent logic (debounce, retry backoff). They are not a tool for skipping `await`s. If a test passes only with fake timers, the production code probably has a race.

2. **Never seed randomness.** Use `crypto.randomUUID()`, `Date.now()`, faker without a fixed seed. A test that works for one seed and breaks for another is telling you the system has a bug, not that the test is flaky.

3. **Never `--update` snapshots to fix a failure.** Snapshots regenerate when the spec genuinely changes. If you don't know why the snapshot differs, the system changed in a way you don't understand — investigate before regenerating.

4. **Never leave `.only`, `.skip`, or `.todo` in committed code.** `.only` hides the rest of the suite; `.skip` hides a failure; `.todo` hides an unwritten test that quietly stays unwritten.

5. **Never assert so loosely it can't fail.** `expect(result).toBeDefined()` is rarely the assertion you actually mean. Pin the meaningful properties.

6. **Never catch in a test to keep it green.** `try { fn() } catch {}` swallows the signal. Use `expect(fn).toThrow(...)` for thrown errors and let everything else propagate.

7. **Never raise per-test or `expect.poll` timeouts to absorb a flake.** SLOW = FAIL — see `engineering/testing.md`. Find the actual completion event or fix the saturation in the product.

## Naming

Describe behaviour, not implementation.

```ts
// ✅
test('rejects requests when the user lacks the listings.publish scope')
// ❌
test('checkScope returns false')
```

## Structure

Arrange / Act / Assert, in order, with whitespace between phases.

```ts
test('parseConfig defaults missing optional fields', () => {
  const raw = { host: 'localhost' };

  const config = parseConfig(raw);

  expect(config.port).toBe(8080);
  expect(config.tls).toBe(false);
});
```

Every test owns its data. No `beforeAll` mutation that other tests rely on.

```ts
const tableName = `test_${crypto.randomUUID().replaceAll('-', '_')}`;
```

## Async

Always `await`. Always assert on the resolved value, not the promise.

```ts
// ❌ no await — the test ends before the assertion runs
fetchUser(id).then((u) => expect(u.email).toBe('...'));

// ✅
const user = await fetchUser(id);
expect(user.email).toMatch(/@/);

// ✅
await expect(fetchUser(id)).resolves.toMatchObject({ id });
```

For things that settle eventually, use `expect.poll` with a meaningful timeout. Never `setTimeout` in a test.

```ts
await expect.poll(() => store.get(id), { timeout: 5_000 }).toMatchObject({ status: 'ready' });
```

When the production code emits a completion signal (event, promise, callback), await *that* — never poll shared state hoping it caught up. See "Observing vs. asserting" in `engineering/testing.md`.

## Errors

Assert on the error type, not the message string. `CustomError` subclasses survive copy changes; string matches don't.

```ts
// ❌
await expect(publish()).rejects.toThrow('User does not have permission');
// ✅
await expect(publish()).rejects.toBeInstanceOf(PermissionDeniedError);
```

If a fragment of the message carries information you actually care about, regex-match the fragment — never the full sentence.

## Assertions and narrowing

Don't reach for `!` (non-null assertion) in test code. It silences the type system without verifying anything at runtime; if the value is actually `undefined`, you get an unhelpful crash deep in the test instead of a clear failure at the line you wrote.

Use `assert` from vitest to verify and narrow in one step:

```ts
import { assert } from 'vitest';

const user = await fetchUser(id);
assert(user, 'fetchUser returned no user');
// `user` is now non-null both at runtime and to the type system

expect(user.email).toMatch(/@/);
```

For shape checks, use a type-guard predicate:

```ts
function isOrgMember(value: unknown): value is OrgMember {
  return typeof value === 'object' && value !== null && 'role' in value;
}

const member = response.members.find((m) => m.userId === bobId);
assert(isOrgMember(member), 'expected member with bobId to have OrgMember shape');

expect(member.role).toBe('admin');
```

`expect(x).toBeDefined()` does not narrow — TypeScript still sees `x` as possibly `undefined` after. Use `assert` when you need narrowing.

Anti-pattern:

```ts
// ❌ Non-null assertion — no runtime check, unhelpful failure
const member = response.members.find((m) => m.userId === bobId)!;
expect(member.role).toBe('admin');

// ✅ Assert, then read
const member = response.members.find((m) => m.userId === bobId);
assert(member, 'expected member with bobId');
expect(member.role).toBe('admin');
```

## Snapshots

Snapshots are the preferred assertion for shape-heavy outputs — API responses, parsed config, normalized payloads. They:

- Capture the entire shape, so a new field appears in the diff and forces an explicit decision (rather than slipping through a hand-written `toMatchObject`).
- Cut assertion boilerplate.
- Make spec changes visible in PR review.

### Determinism is mandatory

A snapshot must produce identical output every run. For non-deterministic fields (UUIDs, timestamps, hashes, random tokens), use **property matchers** — the first argument to `toMatchInlineSnapshot` / `toMatchSnapshot`:

```ts
expect(user).toMatchInlineSnapshot(
  { id: expect.any(String), createdAt: expect.any(Date) },
  `
  {
    "id": Any<String>,
    "createdAt": Any<Date>,
    "email": "alice@example.com",
    "name": "Alice",
  }
  `,
);
```

For pattern-shaped values, use `expect.stringMatching`. Let `vitest -u` fill in the literal — don't hand-write it, the serialized form of asymmetric matchers can change between vitest versions.

When the same non-deterministic shape recurs across many tests, register a **custom serializer** in `vitest.setup.ts` so it normalizes once:

```ts
expect.addSnapshotSerializer({
  test: (val) => typeof val === 'string' && /^[0-9a-f-]{36}$/.test(val),
  serialize: () => '"<uuid>"',
});
```

(The full `pretty-format` plugin signature is `serialize(val, config, indent, depth, refs, printer)` — only spell out the args you need.)

This preserves real randomness in the system under test (per `engineering/testing.md`) while keeping the snapshot stable.

### Inline vs file

- **Inline (`toMatchInlineSnapshot`)** — preferred for small/medium outputs. The expected value lives next to the test, so a reviewer sees the diff in the PR without opening another file.
- **File (`toMatchSnapshot` / `toMatchFileSnapshot`)** — for large outputs (rendered HTML, large parsed structures). Anything over ~30 lines.

### Updating

Regenerate a snapshot only when the spec genuinely changed and the new output is the intended new contract. `vitest -u`, then read every diff hunk and confirm each change is intentional. If you can't explain a change, the system did something you didn't ask for — investigate before committing the new snapshot.

## Coverage rubric per operation

For every operation that changes state, cover:

1. **Happy path** — expected return shape via `toMatchObject`.
2. **Permission denial** — call as a principal who shouldn't be allowed; assert the error type (`PermissionDeniedError` or equivalent).
3. **Not found** — nonexistent ID; the contract-defined response (`undefined` or a typed error).
4. **Edge cases** — duplicates, expiry, partial updates, idempotent deletes.
5. **Side effects** — when the operation emits a queue message, event, or outbound call, assert on the shape of the emitted payload, not just the return value.

Read-only operations skip permission denial only if the contract is "anyone can read".

## Helpers

- **Helpers drive production code.** A `seedOrg` helper that calls `createOrg` (the function the rest of the suite is testing) is correct. A `seedOrg` helper that runs `INSERT INTO orgs ...` bypasses the layers you're trying to test.
- **Raw SQL / direct backend writes are reserved for states the application layer cannot produce** — expired rows, orphaned references, corrupted state for recovery tests. If you can produce the state through the production API, do.
- **Fixtures live in a fixtures file.** Reusable test data (factories, seed helpers, canned payloads) belongs in `fixtures.ts` (or `test/fixtures/*.ts`), not at the top of every spec or duplicated across files. A spec should import what it needs and read like a single user journey.

## Mocking

See `engineering/testing.md` for the philosophy. In vitest specifically:

- **Network:** `msw` at the request layer. The same handlers work in Node, browser, and Workers.
- **Module replacement:** `vi.mock('./module')` replaces an entire module — sparingly, and only for modules that own a real boundary (file system, network, time). Never to swap out internal logic.
- **Spies:** `vi.spyOn` for asserting calls without changing behaviour. Use spies to capture emitted side effects (queue messages, event payloads) and assert on their shape.
- **Reset between tests:** set `restoreMocks: true` in vitest config (calls `mockRestore()` on every spy after each test). For factories from `vi.fn()` or `vi.mock()`, also set `mockReset: true` so implementations are reset, not just history. `vi.restoreAllMocks()` alone only restores `vi.spyOn` originals — it does not reset `vi.fn()` implementations or unmock modules.

## Anti-patterns

```ts
// ❌ Seeded RNG hides input-dependent bugs
faker.seed(42);
const user = faker.person.firstName();

// ✅ Real randomness — let the system meet inputs it will see in production
const user = faker.person.firstName();
```

```ts
// ❌ Snapshot with non-deterministic fields and no property matchers — fails every run
expect(user).toMatchInlineSnapshot();
//   id: 'abc-123', createdAt: '2026-05-03T...' change every run

// ✅ Property matchers replace the non-deterministic fields
expect(user).toMatchInlineSnapshot(
  { id: expect.any(String), createdAt: expect.any(Date) },
  `...`,
);
```

```ts
// ❌ Catching to keep the test green
try {
  await migrate();
} catch {
  // swallow
}
expect(true).toBe(true);

// ✅ The migration must succeed; if it doesn't, the test must fail
await migrate();
expect(await db.tableExists('users')).toBe(true);
```

```ts
// ❌ Polling shared state and hoping
await new Promise((r) => setTimeout(r, 100));
expect(received).toHaveLength(1);

// ✅ Await the signal the production code already emits
const message = await subscriber.next();
expect(message).toMatchObject({ topic: 'orders.created' });
```