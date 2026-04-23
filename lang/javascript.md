# JavaScript Standards

**Prerequisite:** Also follow the rules in [Dependencies](../engineering/dependencies.md).

## Philosophy
- **Web Native:** Prefer web-native solutions and browser-standard APIs.
- **No `console`:** Use a logger module. Never call `console.*` directly.

## Logging
- **Log generously:** `debug` for flow, `warn` for recoverable conditions, `error` for failures.
- **Never delete logs** after adding them. Adjust the level or compile them out if needed — silent code paths are impossible to debug in retrospect.

## Functional Style
- **`const` over `let`:** If you reach for `let`, the code can likely be restructured as a transformation. Never use a `let` + mutation block (`let x; if (...) x = a; else x = b`). Compute the value in an expression and assign to `const`.
- **Pure functions:** Prefer input→output functions. Side effects should be explicit and minimal.
- **Transformation over mutation:** Use `.map()`, `.filter()`, spread over imperative loops and object mutation. Never build an array with `const arr = []; arr.push(...)` — use `.map()`, `.flatMap()`, `.filter()`, or `.reduce()`. Never build an object by constructing an empty `{}` and then mutating it — use `Object.fromEntries`, spread, or a builder that preserves types.
- **`Object.fromEntries()` over `.reduce()`:** Prefer `Object.fromEntries()` for building objects from arrays. Use `.reduce()` only when `fromEntries` doesn't fit.
- **Early returns:** A single early return at the top level of a function is fine for a guard or precondition check. Do not use early returns nested inside conditional blocks.
- **No nested ternaries:** Use `iife()` with a `switch` or `if/else` for multi-branch expressions.
- **`iife()` for complex `const` values:** Use `iife()` from `@block65/toolkit` for `const` values needing branching logic, instead of `let` + reassignment or raw `(() => {})()`.

## Exports
- **No namespace objects:** Never build namespaces by property assignment (`Foo.Bar = Bar`). Use module re-exports (`export * as Foo from './parts.ts'`).
- **No unused exports:** Never `export` a function, type, or value that is not imported elsewhere. `export` is a public contract, not a default.
- **Separate files over inline exports:** Do not pile exports into one file for the sake of it. Split into focused files when it aids readability. Use a barrel (`main.ts`) only as a convenience re-export layer for consumers and tree-shaking — the barrel is not where logic lives. Never `index.ts`.

## Error Handling
- **Never empty `catch`:** Either log, transform, or explicitly comment why swallowing is justified.
- **Never `.catch(() => {})`:** Same rule. A suppressed rejection needs a justifying comment.
- **Never `catch (e) { throw e }`:** No-op. Delete it.
- **Never `void somePromise()`:** Always `await`, `return`, or route through an established pattern. Add a comment when the intent is non-obvious.
- **Route through the established error path:** Do not bypass the project's error handler.

## Structure
- **No deep call stacks:** If following the execution path takes more than a few jumps, flatten the abstraction.

## Type Coercion
- **`.toString()` over `String()`:** Use `value.toString()` for string conversion, not `String(value)`.

## APIs & Modernity
- **Deprecated APIs:** Never use deprecated APIs (e.g., `btoa`). Use modern, standard alternatives.

## Project Verification
- **Task Runners:** Use a dedicated task runner (e.g., moonrepo) if present. 
- **Scripts:** If no task runner exists, `package.json` scripts are acceptable.
- **Implementation Hygiene:** Do not iterate on broken implementations. Identify the root cause and fix it before proceeding.

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

## i18n
- **react-intl:** Never set explicit IDs — they are auto-generated.
- **Tree-shaking:** Use `defineMessage` for single strings, `defineMessages` for enums/groups.
- **Common strings:** Store shared strings like "Saved" and "Updated" in a central `i18n.ts` file.

## Troubleshooting
- **Diagnostic approach:** Use evidence-based exploration. Identify the root cause before changing anything — do not whack-a-mole.
- **Enable logging:** Do not be afraid to add or enable debug/trace logging to track down errors.
