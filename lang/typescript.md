# TypeScript Standards

**Prerequisite:** Also follow the rules in [JavaScript Standards](javascript.md).

## Philosophy

- **TS Native:** Projects do not emit. TypeScript is type-checking and source, not transpilation.

## Type Safety

- **No Casting:** Never use `as any`, `as unknown`, or type casting.
- **Inference:** Prefer inference over explicit types when context is clear.
- **`satisfies` over type annotation:** Prefer `const x = { ... } satisfies T` over `const x: T = { ... }`. Validates the shape while preserving inferred literal types.
- **`const` type parameters:** Use `function<const T>` to preserve literal types from arguments.
- **No enums:** Use `as const` objects with derived union types instead. Enums are not erasable TypeScript and produce runtime output.
- **No non-null assertions:** Never use `!` postfix. Narrow `null`/`undefined` with type guards.
- **No runtime hacks to avoid type errors.** Fix the type.
- **Conditional spreads:** `{ ...(cond && { foo: bar }) }` is fine — TS 6 types it as `{ foo?: ... }` with no index-signature pollution. For a maybe-object, spread it directly: `...maybeObj` where `maybeObj: T | null | undefined`; the `?? {}` / `|| {}` wrappers are redundant. (Arrays differ: nullish throws, use `...(arr ?? [])`.)

## Imports/Exports

- **Extensions:** Use `.ts` in all import specifiers (`'./foo.ts'`), never `.js` or bare.

## File Organization

- **Types near the top:** Declare all `interface` and `type` definitions at the top of the file — after imports and module constants (see [JavaScript Standards](javascript.md)), before any functions, classes, or implementation. Never interleave types with implementation.

## File Naming

- **Components:** `Component.tsx` and `Component.css.ts`.
- **Hooks:** `use-hook.ts` (kebab-case with `use-` prefix).

## Project Verification

- **Typecheck:** Use `tsc -b --noEmit` or equivalent for verification only (no emit).

## Modern Node

- DO NOT USE `tsx` or `ts-node` or any other transpiler. Node 24 supports TypeScript natively without flags.
