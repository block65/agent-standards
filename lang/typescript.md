# TypeScript Standards

Includes all [JavaScript Standards](javascript.md).

## Philosophy
- **TS Native:** We are TypeScript native; projects do not emit. TypeScript is used for type checking and as the primary source, not as a transpilation step.

## Type Safety
- **No Casting:** Never use `as any` or type casting. Ensure the code is structurally sound.
- **Inference:** Prioritize type inference over hard-coded types where the context is clear.

## Project Verification
- **Typecheck:** Use `tsc -b` or equivalent for verification only (no emit).
