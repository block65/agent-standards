# TypeScript Standards

**Prerequisite:** Also follow the rules in [JavaScript Standards](javascript.md).

## Philosophy
- **TS Native:** Projects do not emit. TypeScript is for type checking and as primary source, not transpilation.

## Type Safety
- **No Casting:** Never use `as any`, `as unknown`, or type casting. Code must be structurally sound.
- **Inference:** Prefer inference over explicit types when context is clear.
- **`satisfies` over type annotation:** Prefer `const x = { ... } satisfies T` over `const x: T = { ... }`. Validates the shape while preserving inferred literal types.
- **`const` type parameters:** Use `function<const T>` to preserve literal types from arguments.
- **No enums:** Use `as const` objects with derived union types instead. Enums are not erasable TypeScript and produce runtime output.
- **No non-null assertions:** Never use `!` postfix. Narrow `null`/`undefined` with type guards.

## Imports
- **Extensions:** Use `.ts` in all import specifiers (`'./foo.ts'`), never `.js` or bare.

## File Naming
- **Entry points:** `main.ts`, not `index.ts`.
- **Components:** `Component.ts` and `Component.css.ts`.
- **Hooks:** `use-hook.ts` (kebab-case with `use-` prefix).

## Date & Time
- **Temporal:** Use `Temporal` for all date/time handling. Polyfill: `temporal-polyfill`.

## Project Verification
- **Typecheck:** Use `tsc -b --noEmit` or equivalent for verification only (no emit).
