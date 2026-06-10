# Rust Engineering Standards

Follow all modules below.

- **[Core & Style](rust/core.md)**: Verify cycles, lints, and safety.
- **[Error Handling](rust/errors.md)**: `anyhow` vs `thiserror`.
- **[Async & Concurrency](rust/concurrency.md)**: `tokio`, channels, and threading.
- **[Project & CI](rust/project.md)**: Dependencies, workspace, and testing.
- **[Observability](rust/observability.md)**: `tracing` and output discipline.

## Canonical Idioms

Before writing Rust, consult the distilled Rust Book for the topics the change
touches — `compend get rust-book <topic>` (e.g. `error-handling`, `ownership`,
`iterators`). Always pass a topic; the bare command dumps the entire book.
Where these standards conflict with the book, these standards win. If `compend`
is not on PATH, proceed on these standards alone — do not fetch the book from
the web.
