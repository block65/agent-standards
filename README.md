# agent-standards

Shared coding standards for AI agents across projects. Add as a git submodule:

```sh
git submodule add https://github.com/block65/agent-standards standards
```

In your project's `AGENTS.md`, instruct agents to read the relevant standard first:

```md
Before starting any work, read `standards/rust.md` and `standards/git.md`.
```

## Files

| File | Purpose |
|---|---|
| `rust.md` | Rust coding standards |
| `typescript.md` | TypeScript coding standards |
| `git.md` | Commit conventions (shared across all projects) |

## Project-level AGENTS.md

Project `AGENTS.md` should only contain things that differ from or extend these standards:
- Toolchain specifics (nightly vs stable, edition)
- Workspace structure and feature flags
- Domain-specific conventions
- Verify/build commands for this project
