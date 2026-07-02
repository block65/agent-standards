# Rust Engineering Standards

Follow all modules below.

- **[Core & Style](rust/core.md)**: Verify cycles, lints, and safety.
- **[Error Handling](rust/errors.md)**: `anyhow` vs `thiserror`.
- **[Async & Concurrency](rust/concurrency.md)**: `tokio`, channels, and threading.
- **[Project & CI](rust/project.md)**: Dependencies, workspace, and testing.
- **[Observability](rust/observability.md)**: `tracing` and output discipline.

## Canonical idioms — the Rust Book via compend

These modules are the Block65 standard; general Rust correctness comes from
the Rust Book. Before writing Rust, consult the distilled book for the topics
the change touches:

```sh
compend get rust-book <topic>   # e.g. error-handling, ownership, iterators, traits
```

Always pass a topic — the bare command dumps the entire book. If `compend` is
not on PATH, proceed on these standards alone; do not fetch the book from the
web.

The book covers naming (`new` never fails; fallible constructors are
`build`), ownership/borrowing, std type choice, and idioms — not duplicated
here, to avoid drift from the upstream book.

Where these standards conflict with the book, these standards win (e.g. the
book teaches `Result<Config, &'static str>` constructors; use `thiserror` /
`anyhow` per [Error Handling](rust/errors.md)).
