# JavaScript Standards

## Philosophy
- **Web Native:** Prefer web-native solutions and browser-standard APIs where possible.

## APIs & Modernity
- **Deprecated APIs:** Never use deprecated or legacy APIs (e.g., `btoa`). Always use modern, standard-compliant alternatives.

## Project Verification
- **Scripts:** Do not rely on `package.json` scripts if a dedicated task runner (e.g., moonrepo) is present. Otherwise, prefer direct execution of tools over custom scripts.
- **Implementation Hygiene:** Do not iterate on broken implementations. Identify the root cause and fix it before proceeding.
