# Rust Engineering Standards

Follow all modules below.

- **[Core & Style](rust/core.md)**: Verify cycles, lints, and safety.
- **[Error Handling](rust/errors.md)**: `anyhow` vs `thiserror`.
- **[Async & Concurrency](rust/concurrency.md)**: `tokio`, channels, and threading.
- **[Project & CI](rust/project.md)**: Dependencies, workspace, and testing.
- **[Observability](rust/observability.md)**: `tracing` and output discipline.

## Canonical idioms — the Rust Book via compend

These modules hold Block65 opinion only; general Rust correctness comes from
the language's own canon. If the `compend` command is available, consult the
distilled Rust Book for the topics a change touches BEFORE writing the code:

```sh
compend get rust-book <topic>   # e.g. error-handling, ownership, iterators, traits
```

It covers naming conventions (`new` never fails; fallible constructors are
`build`), ownership/borrowing patterns, which std type fits which job, and
canonical idioms — none of which are duplicated here, deliberately: the book is
version-pinned and maintained upstream; copies here would drift.

Where these standards conflict with the book, these standards win (e.g. the
book teaches `Result<Config, &'static str>` constructors; use `thiserror` /
`anyhow` per [Error Handling](rust/errors.md)).
