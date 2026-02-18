# agent-standards

Shared coding standards for AI agents across projects. Add as a git submodule:

```sh
git submodule add https://github.com/block65/agent-standards standards
```

## Agent Entry Point

In your project's `AGENTS.md`, instruct agents to read the relevant standards:

```md
Before starting any work, read the following standards:
- Git & Workflow: `standards/workflow/git.md`
- Rust: `standards/lang/rust/README.md`
```

## Available Standards

### Languages
- **[Rust](lang/rust/README.md)**: Modular standards for Core, Async, Errors, and Observability.
- **[TypeScript](lang/typescript.md)**: Strict typing and modern patterns.

### Workflows
- **[Git](workflow/git.md)**: Conventional commits and message philosophy.

---

## Project-level AGENTS.md

Project-specific `AGENTS.md` should only contain things that differ from these standards:
- Toolchain specifics (nightly vs stable, edition)
- Workspace structure and feature flags
- Domain-specific conventions
- Verify/build commands for this project
