# Agent Standards

These are the rules Block65 code follows. Library and language facts come from
the `compend` CLI (`compend list` for coverage); where the two conflict, these
standards win.

## Always load

- [Communication](workflow/communication.md)
- [Banned Words](writing/banned-words.md)
- [Git](workflow/git.md)
- [Dependencies](engineering/dependencies.md)
- [Code Review](engineering/code-review.md)
- [Tool Discipline](workflow/tools.md)

## Load when the task matches

- [GitHub Issues](workflow/github-issues.md): filing or editing an issue.
- [Pull Requests](workflow/pull-requests.md): writing a PR title or body.
- [Writing (Base)](writing/base.md): writing any prose meant to be kept (docs,
  READMEs, comments longer than a line). Prerequisite of the next three.
- [Technical Docs](writing/technical.md): documentation and support content.
- [Marketing & Copy](writing/marketing.md): user-facing product copy.
- [Decision Records](writing/adr.md): writing or updating an ADR.
- [Testing](engineering/testing.md): writing or reviewing any test.
  Prerequisite of the next two.
- [Vitest](engineering/vitest.md): unit and integration tests in TypeScript.
- [Playwright](engineering/playwright.md): end-to-end tests.
- [Database](engineering/database.md): schema, columns or migrations.
- [Comments](engineering/comments.md): adding or editing a code comment.
- [Narrowing](engineering/narrowing.md): passing values between layers or
  converting them to a narrower form.
- [TypeScript](lang/typescript.md), [JavaScript](lang/javascript.md),
  [React](lang/react.md), [Rust](lang/rust.md), [Python](lang/python.md):
  writing or reviewing code in that language.
