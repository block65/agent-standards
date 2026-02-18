# agent-standards

Shared coding standards for AI agents.

## Usage

Add as a git submodule:
```sh
git submodule add https://github.com/block65/agent-standards standards
```

In your project's `AGENTS.md`:
```md
Refer to the following engineering standards:
- Git & Workflow: `standards/workflow/git.md`
- Rust: `standards/lang/rust.md`
```

## Available Standards

### Languages
- **[Rust](lang/rust.md)**: Entry point for modular Rust standards.
- **[TypeScript](lang/typescript.md)**: Strict typing and modern patterns.
- **[JavaScript](lang/javascript.md)**: Modern API usage and general JS hygiene.

### Workflows
- **[Git](workflow/git.md)**: Conventional commits and message philosophy.
- **[Communication](workflow/communication.md)**: Concise, objective interaction rules.
