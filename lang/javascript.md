# JavaScript Standards

## Philosophy

- **Web Native:** Prefer web-native solutions and browser-standard APIs.
- **No `console`:** Use a logger module. Never call `console.*` directly.

## Logging

- **Log generously:** `trace` for noisy detail that would otherwise be swallowed (failed parses, feature-test misses, optional-path errors), `debug` for flow, `warn` for recoverable conditions, `error` for failures.
- **Use the right level.** An expected-but-noted condition is `debug` or `trace`, not `error`. Reserve `error` for things an operator should investigate. The codebase under-leverages levels — pick deliberately.
- **Never delete logs** after adding them. Adjust the level or compile them out if needed — silent code paths are impossible to debug in retrospect.

## Functional Style

- **`const` over `let`:** If you reach for `let`, the code can likely be restructured as a transformation. Never use a `let` + mutation block (`let x; if (...) x = a; else x = b`). Compute the value in an expression and assign to `const`.
- **Pure functions:** Prefer input→output functions. Side effects should be explicit and minimal.
- **Transformation over mutation:** Use `.map()`, `.filter()`, spread over imperative loops and object mutation. Never build an array with `const arr = []; arr.push(...)` — use `.map()`, `.flatMap()`, `.filter()`, or `.reduce()`. Never build an object by constructing an empty `{}` and then mutating it — use `Object.fromEntries`, spread, or a builder that preserves types.
- **`Object.fromEntries()` over `.reduce()`:** Prefer `Object.fromEntries()` for building objects from arrays. Use `.reduce()` only when `fromEntries` doesn't fit.
- **Early returns:** A single early return at the top level of a function is fine for a guard or precondition check. Do not use early returns nested inside conditional blocks.
- **No nested ternaries:** Use `iife()` with a `switch` or `if/else` for multi-branch expressions.
- **`iife()` for complex `const` values:** Use `iife()` from `@block65/toolkit` for `const` values needing branching logic, instead of `let` + reassignment or raw `(() => {})()`.

## Imports

- **Imports stay contiguous:** Keep all `import` statements as one unbroken block at the top; never interleave any other code (declarations, types, constants, functions). Side-effect imports go in the same block. A constant or helper needed near the imports goes _below_ them, not inside.

## File Organization

- **Module constants at the top:** True module-level constants — fixed runtime values, typically `UPPER_SNAKE_CASE` (`const MAX_RETRIES = 3`, `const API_VERSION = 'v2'`) — go directly below the imports, before any functions, classes, or logic. Don't scatter module-scoped config next to the function that happens to use it.

## Exports

- **No namespace objects:** Never build namespaces by property assignment (`Foo.Bar = Bar`). Use module re-exports (`export * as Foo from './parts.ts'`).
- **No unused exports:** Never `export` a function, type, or value that is not imported elsewhere. `export` is a public contract, not a default.
- **Separate files over inline exports:** Do not pile exports into one file for the sake of it. Split into focused files when it aids readability. Use a barrel (`main.ts`) only as a convenience re-export layer for consumers and tree-shaking — the barrel is not where logic lives. Never `index.ts`.

## Error Handling

- **Default is bubble.** Most code should let rejections propagate. If the framework above already surfaces them — React Query `query.error`, route loaders to error boundaries, Hono's error pipeline, `withSentry`/equivalents capturing unhandled rejections — then `.catch(console.error)` or `try/catch` is redundant. Delete it; just `await`.
- **Catch only at boundaries where the rejection has nowhere else to go.** Fire-and-forget `waitUntil` / keepalive POSTs (response already sent), top-level entry points outside any handler, code that must continue past a non-essential failure. Everywhere else, bubble.
- **Every catch must do one of:**
  1. Manually report — `captureException(err)` or equivalent.
  2. Rethrow so the established handler captures it (wrap with `{ cause: err }` if adding context).
  3. Log at the appropriate level — `error`, `warn`, `debug`, or `trace` per the Logging rubric.
  4. Throw a `CustomError` enriched with `debug` and `details` fields so the UI layer can surface useful context to the user.
     A catch that does none of these is a swallow, regardless of how it's spelled.
- **Preserve the cause** when wrapping: always pass `{ cause: err }` so the original stack survives.
- **Never silently swallow rejections.** All of these are bugs disguised as defensive code:
  - `.catch(() => {})`
  - `.catch(() => undefined)`
  - `.catch(noop)`
  - `.catch(console.error)` / `.catch(console.warn)` — `console` is banned (see Philosophy) and these almost always sit under a framework that already observes the rejection. Delete them.
  - `.catch(() => ({ items: [] }))` — fabricating an empty/default success shape from a failure is the worst variant; downstream code can't tell the difference between "no items" and "the call failed". If you must return a fallback shape, log/report the error first and document why a fallback is the right behaviour at this boundary.
  - empty `catch (e) {}` or argless `catch {}` with no body
- **Never `catch (e) { throw e }`:** No-op. Delete it.
- **Never `void somePromise()`:** Always `await`, `return`, or route through an established pattern. Add a comment when the intent is non-obvious.
- **Route through the established error path:** Do not bypass the project's error handler.

## Structure

- **No deep call stacks:** If following the execution path takes more than a few jumps, flatten the abstraction.
- **Single-caller across packages is a smell.** A function exported from package `a` with one caller in package `b` is misplaced: move it to `b` (it isn't really shared), or check whether `b` is the wrong home for that logic. Cross-package indirection with no other consumer is pure friction.
- **Promote generic helpers to the shared toolkit.** Generic utilities (string/array/date, type guards, small predicates) belong in the shared toolkit (`@block65/toolkit` or equivalent), not feature modules — it's tree-shaken, so unused helpers cost nothing. Domain-specific logic stays local. Grep the toolkit before writing a new helper.

## Type Coercion

- **`.toString()` over `String()`:** Use `value.toString()` for string conversion, not `String(value)`.
- **`Number.parseInt` / `Number.parseFloat` over `Number()`:** Be explicit about radix and float vs int. `Number.parseInt(s, 10)` for integers; `Number.parseFloat(s)` for floats. `Number(s)` hides the parse mode and silently coerces booleans, `null`, and arrays.

## URLs and Paths

- **Never concatenate URLs or paths by string.** Build with `new URL(path, base)` so encoding, slashes, and query strings are correct. `${host}/${path}` produces double-slashes, missing slashes, and unencoded segments.
- **For filesystem paths,** use `node:path` (`path.join`, `path.resolve`) — never string concat.

## Truthiness Filters

- **`.filter(isTruthy)` over `.filter(Boolean)`:** Use a typed `isTruthy` predicate (e.g. from `@block65/toolkit`) so TypeScript narrows the result type. `.filter(Boolean)` does the runtime work but TS cannot narrow the element type from it.

## APIs & Modernity

- **Deprecated APIs:** Never use deprecated APIs (e.g., `btoa`). Use modern, standard alternatives.

## Project Verification

- **Task Runners:** Use a dedicated task runner (e.g., moonrepo) if present.
- **Scripts:** If no task runner exists, `package.json` scripts are acceptable.

## Dependencies

- **pnpm Catalogs:** If `catalog:` protocol entries exist in the workspace, use them for versioning.
- **Centralization:** Move any dependency used in multiple packages to the central workspace catalog.
- **Syntax:** Use `"dependency-name": "catalog:"` in `package.json`. Never hardcode version strings for dependencies managed by a catalog.

## Naming

- **Never `index.ts`:** Entry points and barrels are always `main.ts`.
- **No tense in variable names:** Prefer `expireTime` over `expiresAt`, `expireTtlSecs` over `expiresIn`.
- **Intentional abbreviations only:** Conventional short names (`i`, `j`, `n`) are fine. Domain abbreviations (`ms`, `ctx`, `req`) only when unambiguous and consistent across the codebase. Never abbreviate when the short form is ambiguous.
- **Grep before naming:** Search the codebase before naming anything. Match the established vocabulary — `create` vs `insert`, `log` vs `entry`, etc.

## Date & Time

- **Temporal:** Use `Temporal` for all date/time handling. Polyfill: `temporal-polyfill`.

## Nullability

- **`undefined` over `null`:** Prefer `undefined` for absent values. Use `null` only when an external API demands it.
- **No empty defaults for missing data:** Never default to `{}` or `[]` to mean "not loaded" or "not applicable". Use `undefined`.
- **Intentional `??`:** Only use `??` when the fallback is semantically meaningful. Do not use it to paper over a value that should not be nullable in the first place.

## Validation

- **Strings:** Always specify min and max length. Check for empty strings, trim if needed, constrain alphabets and charsets.
- **Numbers:** Always set a range and specify integer or float.

## Readability

- Generously use whitespace between lines of code to make code easier to read and to group related lines together.
- **Destructuring:** Always destructure arrays and objects rather than accessing by index or property chain. `const [first] = arr` not `arr[0]`. `const { id, name } = user` not `user.id` / `user.name` repeated. Destructure at the top of the scope so narrowing and defaults are declared once — not scattered through the function as repeated property guard clauses.

## Testing

- **`CustomError` over string matching:** Differentiate error types with `CustomError`, not string comparison.

## Troubleshooting

- **Diagnostic approach:** Use evidence-based exploration. Identify the root cause before changing anything — do not whack-a-mole.
- **Enable logging:** Do not be afraid to add or enable debug/trace logging to track down errors.
