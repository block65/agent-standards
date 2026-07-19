# Agent Standards

## Principles

- **Standards here, facts from compend:** this repo is THE standard — the
  rules Block65 code follows. Library and language facts come from the
  `compend` CLI (`compend list` for coverage). On overlap, the doc defers with a one-line
  pointer (see `lang/rust.md`), not a copied summary (which drifts from
  upstream). On conflict, these
  standards win.

## Always load

- **[Communication](workflow/communication.md)**: Concise, objective interaction rules.
- **[Banned Words](writing/banned-words.md)**: Words we don't use — word-choice bans, plus action-signal words that mean "pause and confirm".
- **[Git](workflow/git.md)**: Conventional commits and message philosophy.
- **[Dependencies](engineering/dependencies.md)**: Source trust and version currency.
- **[Code Review](engineering/code-review.md)**: Common bugs and review behaviours.
- **[Tool Discipline](workflow/tools.md)**: Prefer native tools over the shell; Bash only for running programs.

## Load if applicable (workflow)

- **[TRIPLE](workflow/triple.md)**: Three-role peer programming workflow with impl agent, review agent, and human.
- **[GitHub Issues](workflow/github-issues.md)**: Authoring issues that read well — symptom-first, no fix-prescription, provenance-tagged repro. Automated by the `github-issue` skill.

## Load if applicable (content)

- **[Writing (Base)](writing/base.md)**: Core rules for all content. (Referenced as a prerequisite by sub-modules).
- **[Technical Docs](writing/technical.md)**: Objectivity and clarity (No "Your").
- **[Marketing & Copy](writing/marketing.md)**: Persuasion and ownership (Yes "Your").
- **[Decision Records (ADRs)](writing/adr.md)**: Record why, not how; living records kept in sync with the code.
- **[Testing Philosophy](engineering/testing.md)**: Tests-as-adversaries framing, robustness hierarchy, mocking rules. (Referenced as a prerequisite by `vitest.md` and `playwright.md`).
- **[Vitest](engineering/vitest.md)**: Unit/integration test rules for TypeScript projects.
- **[Playwright E2E](engineering/playwright.md)**: E2E test rules, selector priority, structure, and anti-patterns.
- **[Database](engineering/database.md)**: Schema, column, and migration conventions.
- **[Comments](engineering/comments.md)**: When a code comment earns its place, and what never belongs in one.
- **[TypeScript](lang/typescript.md)**: Strict typing and modern patterns.
- **[React](lang/react.md)**: Component patterns, i18n, styling, and state management.
- **[JavaScript](lang/javascript.md)**: pnpm, modern API usage, and general JS hygiene.
- **[Rust](lang/rust.md)**: Entry point for modular Rust standards.
- **[Python](lang/python.md)**: Data-before-logic layout, strict typing, tamper-evident policy, and a ruff/mypy gate.
