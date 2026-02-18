# JavaScript Standards

## Philosophy
- **Web Native:** Prefer web-native solutions and browser-standard APIs where possible.

## APIs & Modernity
- **Deprecated APIs:** Never use deprecated or legacy APIs (e.g., `btoa`). Always use modern, standard-compliant alternatives.

## Project Verification
- **Tool Execution:** Use a dedicated task runner (e.g., `moon run <task>`) if available.
- **Fallbacks:** If no task runner exists, `package.json` scripts or direct tool execution (e.g., `pnpm exec`) are acceptable.
- **Implementation Hygiene:** Do not iterate on broken implementations. Identify the root cause and fix it before proceeding.
