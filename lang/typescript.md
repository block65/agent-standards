# TypeScript Standards

**Prerequisite:** Also follow the rules in [JavaScript Standards](javascript.md).

## Philosophy

- **TS Native:** Projects do not emit. TypeScript is type-checking and source, not transpilation.

## Type Safety

- **No Casting:** Never use `as any`, `as unknown`, or an unchecked `as T`. `as const` and `satisfies` are fine — they assert or check without overriding the checker.
- **Inference:** Prefer inference over explicit types when context is clear.
- **`satisfies` over type annotation:** Prefer `const x = { ... } satisfies T` over `const x: T = { ... }`. Validates the shape while preserving inferred literal types.
- **`const` type parameters:** Use `function<const T>` to preserve literal types from arguments.
- **No enums:** Use `as const` objects with derived union types instead. Enums are not erasable TypeScript and produce runtime output.
- **No non-null assertions:** Never use `!` postfix. Narrow `null`/`undefined` with type guards.
- **No runtime hacks to avoid type errors.** Fix the type.
- **Conditional spreads:** `{ ...(cond && { foo: bar }) }` is fine — TS types it as `{ foo?: ... }` with no index-signature pollution. This is how you satisfy a strict `?: T` target; where the target declares `?: T | undefined`, pass the value directly instead (see Optional Properties). For a maybe-object, spread it directly: `...maybeObj` where `maybeObj: T | null | undefined`; the `?? {}` / `|| {}` wrappers are redundant. (Arrays differ: nullish throws, use `...(arr ?? [])`.)

## Compiler Configuration

- **Extend the shared config.** `tsconfig.json` extends the `@block65/tsconfig` variant matching the target (`nodejs24`, `vite-react`, `cloudflare-worker`, `nextjs`, `vanilla`; `-projref` variants for project references). Strictness is decided there, once.
- **Never loosen a flag locally.** Turning off a check the shared config enabled is a runtime hack in config form — fix the type. A target the shared config does not cover is a change to that package, not a local override.
- **`exactOptionalPropertyTypes` is always on.** Assume it when reading and writing optional properties (see Optional Properties).

## Optional Properties

With `exactOptionalPropertyTypes`, the two spellings mean different things, so the choice is a declaration of intent.

- **`?: T` is the default.** The property is absent or it holds a value; there is no third state. `{ foo: undefined }` is rejected, and `"foo" in obj` narrows `obj.foo` to `T`.
- **`?: T | undefined` is a declared opt-in.** Callers may pass `undefined` explicitly. Use it where `prop={maybe}` reads better than `{ ...(maybe && { prop: maybe }) }`, which in practice means JSX props on leaf components. It costs narrowing: presence no longer implies a value, so `"foo" in obj` leaves `T | undefined` and the value itself has to be checked. Declaring it on the property keeps the concession visible at the definition rather than ambient across call sites.
- **Properties only, not parameters.** Readability does not justify a `| undefined` parameter — see Nullability in [JavaScript Standards](javascript.md).
- **Test the key, not truthiness.** `!obj.prop` also matches `0`, `""`, and `false`. Use `"prop" in obj` to ask whether the property was specified, and a value comparison to ask what it holds.
- **Make the invalid value unrepresentable.** When `""` or `0` is invalid for a field, a `?? ""` fallback is a symptom of the wrong type. Constrain the field with a valibot-validated or branded type, the TS equivalent of a Rust newtype, so the invalid state cannot be constructed.

## Untyped Input

- **`unknown` where the data is genuinely unknown** — bytes off the wire, parsed JSON, `postMessage` payloads, third-party webhook bodies. Not at every exported function: internal callers are already typed, and re-validating them costs a check that can never fail.
- **Validate what you cannot type.** Anything typed `unknown` is parsed with valibot before use — `safeParse`, and handle the failure. Casting it into shape with `as` asserts a fact you have not established.

## Imports/Exports

- **Extensions:** Use `.ts` in all import specifiers (`'./foo.ts'`), never `.js` or bare.

## File Organization

- **Types near the top:** Declare all `interface` and `type` definitions at the top of the file — after imports and module constants (see [JavaScript Standards](javascript.md)), before any functions, classes, or implementation. Never interleave types with implementation.

## Project Verification

- **Typecheck:** Use `tsc -b --noEmit` or equivalent for verification only (no emit).

## Modern Node

- DO NOT USE `tsx` or `ts-node` or any other transpiler. Node 24 supports TypeScript natively without flags.
