# agent-standards

Shared coding standards for AI agents across projects. Add as a git submodule:

```sh
git submodule add https://github.com/block65/agent-standards standards
```

In your project's `AGENTS.md`, instruct agents to read the relevant standard first:

```md
Before starting any work, read `INDEX.md` and the relevant standards for this project:
- Rust: `lang/rust.md`
- Git: `workflow/git.md`
```

## Files

| Path | Purpose |
|---|---|
| `INDEX.md` | Master index of all standards |
| `lang/rust.md` | Rust standards entry point |
| `lang/rust/` | Modular Rust standards |
| `lang/typescript.md` | TypeScript coding standards |
| `workflow/git.md` | Commit conventions |

## Project-level AGENTS.md

Project `AGENTS.md` should only contain things that differ from or extend these standards:
- Toolchain specifics (nightly vs stable, edition)
- Workspace structure and feature flags
- Domain-specific conventions
- Verify/build commands for this project
