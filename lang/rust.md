# Rust Engineering Standards

**Prerequisite:** Also follow the rules in [Dependencies](../engineering/dependencies.md).

Follow all modules below.

- **[Core & Style](rust/core.md)**: Verify cycles, lints, and safety.
- **[Error Handling](rust/errors.md)**: `anyhow` vs `thiserror`.
- **[Async & Concurrency](rust/concurrency.md)**: `tokio`, channels, and threading.
- **[Project & CI](rust/project.md)**: Dependencies, workspace, and testing.
- **[Observability](rust/observability.md)**: `tracing` and output discipline.

## Review

### Common Bugs
- Duplicated code chunks (copy-paste without abstraction)
- Splitting or modifying data types only to reassemble them later in the code path
- Changing one function in a common set but not its counterparts
- Inappropriate log levels for messages
- Incomprehensible log messages
- Inconsistent terminology
- Ignoring surrounding code ("not my code" mindset)

### Behaviours
- Write tools instead of one-off scripts
- When refactoring or renaming structs, check surrounding code for comments and variable assignments referencing the old name
- The only thing worse than no comments is incorrect comments
