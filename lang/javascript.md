# JavaScript Standards

**Prerequisite:** Also follow the rules in [Dependencies](../engineering/dependencies.md).

## Philosophy
- **Web Native:** Prefer web-native solutions and browser-standard APIs where possible.
- **No `console`:** Use a logger module. Never call `console.*` directly.

## Functional Style
- **`const` over `let`:** If you reach for `let`, the code can likely be restructured as a transformation.
- **Pure functions:** Prefer input→output functions. Side effects should be explicit and minimal.
- **Transformation over mutation:** Use `.map()`, `.filter()`, spread over imperative loops and object mutation.
- **`Object.fromEntries()` over `.reduce()`:** Prefer `Object.fromEntries()` for building objects from arrays. Use `.reduce()` only when `fromEntries` doesn't fit.
- **Early returns:** Return early rather than nesting in `if/else` blocks.
- **`iife()` for complex `const` values:** Use `iife()` from `@block65/toolkit` for `const` values needing branching logic, instead of `let` + reassignment or raw `(() => {})()`.

## APIs & Modernity
- **Deprecated APIs:** Never use deprecated APIs (e.g., `btoa`). Use modern, standard alternatives.

## Project Verification
- **Task Runners:** Use a dedicated task runner (e.g., moonrepo) if present. 
- **Scripts:** If no task runner exists, `package.json` scripts are acceptable.
- **Implementation Hygiene:** Do not iterate on broken implementations. Identify the root cause and fix it before proceeding.

## Dependencies
- **pnpm Catalogs:** If `catalog:` protocol entries exist in the workspace, use them for versioning.
- **Centralization:** Move any dependency used in multiple packages to the central workspace catalog. 
- **Syntax:** Use `"dependency-name": "catalog:"` in `package.json`. Never hardcode version strings for dependencies managed by a catalog.
