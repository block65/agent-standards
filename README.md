# agent-standards

Shared coding standards for AI agents.

## Usage

Add as a git submodule:
```sh
git submodule add git@github.com:block65/agent-standards.git standards
```

In your project's `AGENTS.md`:
```md
Refer to `standards/README.md` and load all applicable standards listed there.
```

## Standards

### Always load
- **[Communication](workflow/communication.md)**: Concise, objective interaction rules.
- **[Git](workflow/git.md)**: Conventional commits and message philosophy.

### Load if applicable
- **[TypeScript](lang/typescript.md)**: Strict typing and modern patterns. Includes JavaScript standards.
- **[JavaScript](lang/javascript.md)**: pnpm, modern API usage, and general JS hygiene.
- **[Rust](lang/rust.md)**: Entry point for modular Rust standards.
