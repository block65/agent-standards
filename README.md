# agent-standards

Shared coding standards for AI agents across projects. Add as a git submodule:

```sh
git submodule add https://github.com/block65/agent-standards standards
```

## How to use with agents

In your project's `AGENTS.md`, instruct agents to refer to these standards:

```md
Before starting any work, refer to the engineering standards:
- Git & Workflow: `standards/workflow/git.md`
- Rust: `standards/lang/rust.md`
```

## Available Standards

### Languages
- **[Rust](lang/rust.md)**: Entry point for modular Rust standards (Core, Async, Errors, etc.).
- **[TypeScript](lang/typescript.md)**: Strict typing and modern patterns (includes JS standards).
- **[JavaScript](lang/javascript.md)**: Modern API usage and general JS hygiene.

### Workflows
- **[Git](workflow/git.md)**: Conventional commits and message philosophy.
- **[Communication](workflow/communication.md)**: Concise, objective, and filler-free interaction rules.
