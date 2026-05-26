# TypeScript Standards

**Prerequisite:** Also follow the rules in [JavaScript Standards](javascript.md).

## Philosophy

- **TS Native:** Projects do not emit. TypeScript is for type checking and as primary source, not transpilation.

## Type Safety

- **No Casting:** Never use `as any`, `as unknown`, or type casting.
- **Inference:** Prefer inference over explicit types when context is clear.
- **`satisfies` over type annotation:** Prefer `const x = { ... } satisfies T` over `const x: T = { ... }`. Validates the shape while preserving inferred literal types.
- **`const` type parameters:** Use `function<const T>` to preserve literal types from arguments.
- **No enums:** Use `as const` objects with derived union types instead. Enums are not erasable TypeScript and produce runtime output.
- **No non-null assertions:** Never use `!` postfix. Narrow `null`/`undefined` with type guards.
- **No runtime hacks to avoid type errors.** Fix the type.
- **Conditional spreads use a ternary, never `&&`:** Write `{ ...(cond ? { foo: bar } : {}) }`, never `{ ...(cond && { foo: bar }) }`. The `&&` form returns the falsy operand verbatim, so TS types the spread as `false | { foo: bar }`. In generic or mapped-type contexts the union spread of a primitive can widen the surrounding object with an `[x: string]: any` index signature — every named field silently degrades to `any` and the poison propagates through derived types. The ternary resolves cleanly to `Partial<{ foo: bar }>`. Safe variants: `...(maybe || {})`, `...(maybe ?? {})`, `...maybeObj` where `maybeObj: T | undefined`.

## Imports/Exports

- **Extensions:** Use `.ts` in all import specifiers (`'./foo.ts'`), never `.js` or bare.

## File Organization

- **Types near the top:** Declare all `interface` and `type` definitions at the top of the file — after imports and module constants (see [JavaScript Standards](javascript.md)), before any functions, classes, or implementation. A reader scanning the file should see the shape of the data before the logic that operates on it. Do not interleave types with implementation.

## File Naming

- **Components:** `Component.tsx` and `Component.css.ts`.
- **Hooks:** `use-hook.ts` (kebab-case with `use-` prefix).

## Project Verification

- **Typecheck:** Use `tsc -b --noEmit` or equivalent for verification only (no emit).

## Modern Node

- DO NOT USE `tsx` or `ts-node` or any other transpiler. Node 24 supports TypeScript natively without flags.
