# JavaScript Standards

## Platform and Tooling

- **Web Native:** Prefer web-native solutions and browser-standard APIs.
- **Task runner:** Use the repo's task runner (e.g. moonrepo) if present,
  otherwise `package.json` scripts.
- **pnpm catalogs:** Where the workspace has a catalog, a dependency used by
  more than one package moves into it, and every `package.json` references it
  as `"dependency-name": "catalog:"`, never a version string.

## Logging

- **Use a logger module,** never `console.*`.
- **Log generously at the right level:** `trace` for detail that would otherwise
  be swallowed (failed parses, feature-test misses, optional-path errors),
  `debug` for flow, `warn` for recoverable conditions, `error` only for what an
  operator should investigate.
- **Keep logs once added.** Adjust the level or compile them out; a silent code
  path cannot be debugged after the fact.

## Functional Style

- **Build collections by transformation:** `.map()`, `.flatMap()`, `.filter()`,
  `Object.fromEntries`, spread, or a type-preserving builder. Never push into
  an array or assign into an object from inside `for`, `for…of`, `for…in`,
  `for await…of`, `while`, or `.forEach()`.
- **Iterate for side effects with `.forEach()`,** not a `for` loop: calls and
  I/O, never building a value. Keep `for…of` for a body that awaits in
  sequence, exits early, or consumes an iterator or stream.
- **Loops that perform side effects or consume streams** have an explicit
  termination or cancellation condition, never `for (;;)`, `while (true)` or
  another constant condition.
- **`iife()` for branching `const` values:** Use `iife()` from
  `@block65/toolkit` with a `switch` or `if/else`, instead of `let` +
  reassignment or a raw `(() => {})()`.

## Modules

- **Module constants at the top:** Fixed module-level values go directly below
  the imports, not beside the function that uses them.
- **No namespace objects:** Build a namespace with a module re-export
  (`export * as Foo from './parts.ts'`), never by property assignment
  (`Foo.Bar = Bar`).
- **Export only what something imports.** `export` is a public contract.
- **Split into focused files.** A barrel (`main.ts`) only re-exports; logic
  lives elsewhere.
- **Keep call stacks shallow.** If following the execution path takes more than
  a few jumps, flatten the abstraction.
- **A function exported from package `a` with one caller in package `b`** moves
  to `b`, unless `b` is the wrong home for that logic.
- **Generic helpers go in the shared toolkit** (`@block65/toolkit` or
  equivalent), not feature modules: string/array/date, type guards, small
  predicates. Grep the toolkit before writing one. Domain logic stays local.
- **Write the generic form when the logic allows one.** A function that maps,
  groups or transforms without depending on the domain type becomes a generic
  in the toolkit (`mapObject<T, U>`), and the caller passes the domain parts.
- **Inline a function of up to three lines that has one caller.** It adds a jump
  without adding a name the reader needs.

## Error Handling

- **Throw a `CustomError`** from `@block65/custom-error`, never a built-in
  error class (`Error`, `TypeError`, `RangeError`), misuse at construction
  included: a built-in carries no status or machine-readable code for the
  top-level handler. Tests tell errors apart by `CustomError` type, not message strings.
- **Sensitive data goes in `debug`, never in the message.** `.debug({ ... })` is
  private and appears only in the server-side `toJSON()`. `details` reaches the
  client via `toJSONSummary()`, so it holds only what a user may read.
- **The top-level handler owns what the user sees.** Nothing below it formats
  errors for display or decides what is safe to expose.
- **Let rejections bubble.** Where the framework above already surfaces them
  (React Query `query.error`, route loaders to error boundaries, Hono's error
  pipeline, `withSentry`), `await` and let it propagate. Catch only where a
  rejection has nowhere else to go: fire-and-forget `waitUntil` or keepalive POSTs, top-level
  entry points outside any handler, code that must continue past a
  non-essential failure.
- **Every catch does one of:** report with `captureException(err)` or
  equivalent; rethrow with `{ cause: err }`; log at the level the Logging rules
  give; or throw a `CustomError` with `debug` and `details` for the UI. Anything
  else is a swallow, including `.catch(noop)`, `.catch(console.error)` and an
  empty `catch {}`. The worst is fabricating success from failure
  (`.catch(() => ({ items: [] }))`), which downstream code cannot tell from an
  empty result.
- **A catch that recovers** starts with `// NOTE: …` saying why recovery is
  correct at this boundary, and also logs or reports the error.

## Promises

- **`Promise.withResolvers()` when `resolve`/`reject` escape the executor,**
  whether into an outer `let`, an object, or a caller.
- **`new Promise` only wraps a callback or event API,** with the work started
  inside the executor. Compose an existing promise with `async`/`await`; the
  constructor drops rejections between the two layers.
- **Sleep with a cancellable timer:** `setTimeout` from `node:timers/promises`
  with a `signal` in Node, or a cancellable toolkit helper elsewhere, never
  `new Promise((r) => setTimeout(r, ms))`.

BAD: `resolve` escapes the executor.

```ts
export function createGate() {
	let resolve: (value: Result) => void;
	const ready = new Promise<Result>((res) => {
		resolve = res;
	});

	return {
		ready,
		open: (value: Result) => {
			resolve(value);
		},
	};
}
```

GOOD: one call returns the promise and its resolver.

```ts
export function createGate() {
	const { promise: ready, resolve } = Promise.withResolvers<Result>();
	return { ready, open: resolve };
}
```

## Values

- **`.toString()` over `String()`:** Narrow away `null`/`undefined` first;
  `.toString()` throws on them where `String()` silently prints `"undefined"`.
- **Build URLs with `new URL(path, base)`** and filesystem paths with
  `node:path`, never by string concatenation.
- **Validation:** Give every string a min and max length, and trim and
  constrain its charset where relevant. Give every number a range and say
  integer or float.

## Naming

- **`UPPER_SNAKE_CASE` only for an immutable value:** a scalar literal, an
  `as const` literal, or a value deep-frozen at runtime. A `Set`, `Map`, array
  or object is camelCase even when bound with `const`, which fixes the binding,
  not the contents.
- **Name a function for everything it does.** A `get[Thing]` that also seeds
  a database hides its side effects from every caller; name the whole job, or
  split the function.
- **Event parameters:** Name the event parameter in an event handler `e`.
- **Entry points and barrels are `main.ts`,** never `index.ts`.
- **No tense in names:** `expireTime` not `expiresAt`, `expireTtlSecs` not
  `expiresIn`.
- **Abbreviate only where unambiguous** and consistent across the codebase
  (`ms`, `ctx`).
- **Grep before naming** and match the established vocabulary (`create` vs
  `insert`, `log` vs `entry`).

## Nullability

Modelled on Rust's `Option<T>`: absence is one state, resolved by the code that
knows what missing means. Background: `compend get rust-book option`.

- **No `?? undefined` in domain logic.** The parse layer converts a boundary's
  absence value to `undefined`; a `?? undefined` above it means that boundary
  is in the wrong place.
- **Never a scalar sentinel.** `?? ""` or `?? 0` on a required value turns
  "missing" into "present and wrong", hiding from the type system the absence
  it would make you handle, and the failure surfaces somewhere unrelated.
  `?? []` is allowed where an absent list means no items and the fallback
  reads more simply than a guard.
- **`??` needs a reason.** Most are a sentinel, an arbitrary default or a
  workaround for a loose type. Write one only where the absent case has a
  defined default, such as a documented option default; otherwise tighten the
  type or guard.
- **A parameter is optional only when the function defines behaviour for the
  absent case.** Never widen it to `| undefined` so one caller can skip
  deciding.
- **Tighten a parameter that accepts more than the function uses,** then fix
  each caller the checker flags. Absorbing `null` or `undefined` deep in the
  stack hides the frame that produced it, usually a boundary several calls up.
- **Resolve absence with a top-level guard** where missing has a meaning:
  return early, or throw a `CustomError` naming what was missing.

## Readability

- **Never call a returned function in place.** `[make]()([args])` makes the
  reader work out what `[make]` returns. Expose it under a name
  (`[instance].[handle]([args])`), or bind it to a `const` first.
- **A function body is paragraphs.** Separate each phase (guards, inputs, the
  work, the result) with a blank line, and break any run of more than about five
  lines that changes subject. No blank line between a comment and the line it
  describes.
- **Blank lines are not extraction.** More than about four groups means the
  function does more than one job. Split it.
- **Destructure** at the top of the scope instead of indexing or repeating a
  property chain: `const [first] = arr`, `const { id, name } = user`.

GOOD: one blank line between phases.

```ts
export async function publish(id: Id, body: Body) {
	const record = await store.get(id);

	if (!record) {
		throw new CustomError("record not found").debug({ id });
	}

	const payload = serialise(body);
	const headers = signHeaders(payload);

	const res = await transport.send(record.endpoint, payload, headers);

	return parseReceipt(res);
}
```
