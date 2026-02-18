# TypeScript Standards

Includes all [JavaScript Standards](javascript.md).

## Type Safety
- **No Casting:** Never use `as any` or type casting. Ensure the code is structurally sound.
- **Inference:** Prioritize type inference over hard-coded types where the context is clear.

## Project Verification
- **Typecheck:** `pnpm exec tsc -b`
- **Test:** `pnpm exec vitest`
