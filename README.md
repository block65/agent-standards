# agent-standards

Shared coding standards for AI agents.

## Usage

Add as a git submodule:
```sh
git submodule add git@github.com:block65/agent-standards.git standards
```

In your project's `AGENTS.md`:
```md
Refer to the following standards from the `standards/` submodule:
- Git & Workflow: `workflow/git.md`
- Writing: `writing/technical.md` (or `writing/marketing.md`)
```

## Available Standards

### Always load
- **[Communication](workflow/communication.md)**: Concise, objective interaction rules.
- **[Git](workflow/git.md)**: Conventional commits and message philosophy.
- **[Dependencies](engineering/dependencies.md)**: Source trust and version currency.

### Load if applicable
- **[Writing (Base)](writing/base.md)**: Core rules for all content. (Referenced as a prerequisite by sub-modules).
- **[Technical Docs](writing/technical.md)**: Objectivity and clarity (No "Your").
- **[Marketing & Copy](writing/marketing.md)**: Persuasion and ownership (Yes "Your").
- **[TypeScript](lang/typescript.md)**: Strict typing and modern patterns. Includes JavaScript standards.
- **[React](lang/react.md)**: Component patterns, i18n, styling, and state management.
- **[JavaScript](lang/javascript.md)**: pnpm, modern API usage, and general JS hygiene.
- **[Rust](lang/rust.md)**: Entry point for modular Rust standards.
