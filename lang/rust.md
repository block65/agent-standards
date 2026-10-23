# Rust Engineering Standards

Follow all modules below.

- **[Core & Style](rust/core.md)**: Verify cycles, lints, and safety.
- **[Error Handling](rust/errors.md)**: `anyhow` vs `thiserror`.
- **[Async & Concurrency](rust/concurrency.md)**: `tokio`, channels, and
  threading.
- **[Project & CI](rust/project.md)**: Dependencies, workspace, and testing.
- **[Observability](rust/observability.md)**: `tracing` and output discipline.

## The Rust Book via compend

Before writing Rust, read the distilled book for each topic the change touches:

```sh
compend get rust-book <topic>   # e.g. error-handling, ownership, iterators, traits
```

Always pass a topic; the bare command dumps the whole book. Without `compend` on
PATH, proceed on these standards alone, and do not fetch the book from the web.
Where the book conflicts with these standards, these win: its
`Result<Config, &'static str>` constructors become `thiserror` / `anyhow` per
[Error Handling](rust/errors.md).
