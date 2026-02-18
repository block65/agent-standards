# TypeScript Standards

Includes all [JavaScript Standards](javascript.md).

## Type Safety
- **No Casting:** Never use `as any` or type casting. Ensure the code is structurally sound.
- **Inference:** Prioritize type inference over hard-coded types where the context is clear.

## Project Verification
- **Tool Execution:** Use a task runner (e.g., `moon run <task>`) if available.
- **Direct Execution:** If no task runner exists, prefer direct execution over `package.json` scripts:
  - **Typecheck:** `pnpm exec tsc -b`
  - **Test:** `pnpm exec vitest`
