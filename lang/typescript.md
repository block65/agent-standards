# TypeScript Standards

Includes all [JavaScript Standards](javascript.md).

## Type Safety
- **No Casting:** Never use `as any` or type casting. Ensure the code is structurally sound.
- **Inference:** Prioritize type inference over hard-coded types where the context is clear.

## Project Verification
- **Tool Execution:** Use a task runner (e.g., `moon run <task>`) if available.
- **Fallbacks:** If no task runner exists, use `package.json` scripts or direct execution:
  - **Typecheck:** `pnpm run typecheck` or `pnpm exec tsc -b`
  - **Test:** `pnpm run test` or `pnpm exec vitest`
