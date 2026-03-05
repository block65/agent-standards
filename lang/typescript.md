# TypeScript Standards

**Prerequisite:** Also follow the rules in [JavaScript Standards](javascript.md).

## Philosophy
- **TS Native:** We are TypeScript native; projects do not emit. TypeScript is used for type checking and as the primary source, not as a transpilation step.

## Type Safety
- **No Casting:** Never use `as any` or `as unknown` or type casting. Ensure the code is structurally sound.
- **Inference:** Prioritize type inference over hard-coded types where the context is clear.
- **`satisfies` over type annotation:** Prefer `const x = { ... } satisfies T` over `const x: T = { ... }`. Validates the shape while preserving inferred literal types.
- **`const` type parameters:** Use `function<const T>` to infer literal types from arguments instead of widening to base types.
- **No enums:** Use `as const` objects with derived union types instead. Enums are not erasable TypeScript and produce runtime output.
- **No non-null assertions:** Never use `!` postfix. Handle `null`/`undefined` explicitly with narrowing or guard clauses.

## Imports
- **Extensions:** Use `.ts` in all import specifiers (`'./foo.ts'`), never `.js` or bare.

## File Naming
- **Entry points:** `main.ts`, not `index.ts`.
- **Components:** `Component.ts` and `Component.css.ts`.
- **Hooks:** `use-hook.ts` (kebab-case with `use-` prefix).

## Date & Time
- **Temporal:** Use `Temporal` for all date/time handling. We polyfill with `temporal-polyfill`.

## Project Verification
- **Typecheck:** Use `tsc -b --noEmit` or equivalent for verification only (no emit).
