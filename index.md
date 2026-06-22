# Agent Standards

## Principles

- **Standards here, facts from compend:** this repo is THE standard — the
  rules Block65 code follows. Library and language facts come from the
  `compend` CLI (`compend list` for coverage). Where coverage overlaps a
  standards doc, the doc defers with a one-line pointer (see `lang/rust.md`) —
  never a copied summary, which would drift from upstream. On conflict, these
  standards win.

## Always load

- **[Communication](workflow/communication.md)**: Concise, objective interaction rules.
- **[Banned Words](workflow/banned-words.md)**: Vocabulary that signals imminent destructive action — stop and self-report.
- **[Git](workflow/git.md)**: Conventional commits and message philosophy.
- **[Dependencies](engineering/dependencies.md)**: Source trust and version currency.
- **[Code Review](engineering/code-review.md)**: Common bugs and review behaviours.

## Load if applicable (workflow)

- **[TRIPLE](workflow/triple.md)**: Three-role peer programming workflow with impl agent, review agent, and human.

## Load if applicable (content)

- **[Writing (Base)](writing/base.md)**: Core rules for all content. (Referenced as a prerequisite by sub-modules).
- **[Technical Docs](writing/technical.md)**: Objectivity and clarity (No "Your").
- **[Marketing & Copy](writing/marketing.md)**: Persuasion and ownership (Yes "Your").
- **[Testing Philosophy](engineering/testing.md)**: Tests-as-adversaries framing, robustness hierarchy, mocking rules. (Referenced as a prerequisite by `vitest.md` and `playwright.md`).
- **[Vitest](engineering/vitest.md)**: Unit/integration test rules for TypeScript projects.
- **[Playwright E2E](engineering/playwright.md)**: E2E test rules, selector priority, structure, and anti-patterns.
- **[Database](engineering/database.md)**: Schema and column conventions.
- **[Comments](engineering/comments.md)**: When a code comment earns its place, and what never belongs in one.
- **[TypeScript](lang/typescript.md)**: Strict typing and modern patterns.
- **[React](lang/react.md)**: Component patterns, i18n, styling, and state management.
- **[JavaScript](lang/javascript.md)**: pnpm, modern API usage, and general JS hygiene.
- **[Rust](lang/rust.md)**: Entry point for modular Rust standards.
