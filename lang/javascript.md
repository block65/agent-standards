# JavaScript Standards

## Philosophy
- **Web Native:** Prefer web-native solutions and browser-standard APIs where possible.

## Functional Style
- **`const` over `let`:** If you reach for `let`, the code can likely be restructured as a transformation.
- **Pure functions:** Prefer functions that take input and return output. Side effects should be explicit and minimal.
- **Transformation over mutation:** Use `.map()`, `.filter()`, spread over imperative loops and object mutation.
- **`Object.fromEntries()` over `.reduce()`:** When constructing objects from arrays or entries, `Object.fromEntries()` is cleaner. `.reduce()` for object construction is acceptable only when `fromEntries` doesn't fit.
- **Early returns for guard clauses:** Return early at function entry rather than nesting logic in `if/else` blocks.
- **`iife()` for complex `const` values:** When a `const` value requires conditional logic or early returns to compute, use `iife()` from `@block65/toolkit` instead of `let` + reassignment or raw `(() => {})()`. This keeps `const` usage intact while allowing branching logic. `switch (true)` inside an `iife()` is a clean alternative to chained ternaries for multi-branch assignments.

## APIs & Modernity
- **Deprecated APIs:** Never use deprecated or legacy APIs (e.g., `btoa`). Always use modern, standard-compliant alternatives.

## Package Manager
- **pnpm:** pnpm is the package manager. Never use npm or yarn.

## Project Verification
- **Tool Execution:** Use a dedicated task runner (e.g., `moon run <task>`) if available.
- **Fallbacks:** If no task runner exists, use `pnpm exec <tool>` or `pnpm run <script>` directly.
- **Implementation Hygiene:** Do not iterate on broken implementations. Identify the root cause and fix it before proceeding.
