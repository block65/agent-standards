# Rust Standards

## Verify Cycle

For each change set: **code → verify → commit**.

Always use `-q` (quiet) with cargo commands to reduce noise:

```sh
cargo build -q
cargo clippy -q --fix --allow-dirty
cargo test -q
cargo fmt
```

Adapt feature flags to the project (e.g. `--features full`, `--all-features`).

## Lint

**Zero-warning policy.** Fix the root cause of every Clippy warning. Only use
`#[allow(...)]` for verified false positives, always accompanied by a
`// REASON: <explanation>` comment. Fix, don't bypass.

## Code Style

- **Formatting:** Strictly follow `cargo fmt`.
- **Modules:** Avoid `mod.rs`. Use the 2018+ style (`src/models.rs` + `src/models/`
  directory) for better IDE navigation.
- **Derives:** Derive `Debug`, `Clone`, `Default`, `PartialEq` where it makes sense.
  Don't blanket-derive `Serialize` — only add it where serialization is actually needed.
- **`#[must_use]`:** Apply to `Result` return types, builder methods, and lock guards.
- **`#[non_exhaustive]`:** Use on types in published library crates. Not needed for
  internal workspace crates.
- **Docs:** Document all public items with `///`. In published library crates, include
  runnable `# Examples` to drive doctest coverage.

## Safety & Panics

- **Unsafe:** Every `unsafe` block must have a `// SAFETY: <justification>` comment.
  Isolate unsafe behind safe, well-tested abstractions.
- **Panics:** Avoid `unwrap()` and `expect()` in production code paths. Acceptable in:
  - Test code
  - Initialization where failure is fatal and immediately obvious
  - Where an invariant is provably impossible to break — mark with `// INVARIANT: <explanation>`

## Ownership & Performance

- Prefer `&T` for reading, `&mut T` for modifying.
- Don't derive `Clone` indiscriminately on hot-path types — use `Arc<T>` where
  shared ownership across threads is the actual requirement.
- Use `Cow<'_, T>` for APIs that can either borrow or own, deferring allocation
  until mutation is required.
- Prefer dedicated `Config` / `Options` structs over long parameter lists.

## Error Handling

- **Applications:** `anyhow` + `.context()` for descriptive error chains.
- **Libraries:** Public APIs use `thiserror` for defined error types. Internal
  modules may use `anyhow` for convenience.

## Async & Concurrency

- Use async only for I/O-bound or high-concurrency tasks. Sync Rust is simpler.
- Don't use `std::thread::sleep` in async tasks — use `tokio::time::sleep`.
- **File I/O:** Use `tokio::fs` for simple individual operations. Use `spawn_blocking`
  + `std::fs` for multiple sequential file operations that should run as a single
  blocking unit.
- Offload CPU-heavy work with `spawn_blocking`.
- Prefer `CancellationToken` for graceful shutdown over complex drop-based cleanup.
- Prefer message passing (channels) over shared state. If shared state is necessary,
  prefer `RwLock` over `Mutex` for read-heavy workloads. Use atomics only for
  simple counters or flags.

## Dependencies

- Prefer fewer, high-quality dependencies. Audit new crates for maintenance and
  security via `cargo audit` or `cargo deny`.
- Always prefer the latest stable versions. Monitor with `cargo outdated`.
- Disable default features where possible (`default-features = false`) to minimize
  compile times and attack surface.

## Feature Flags

- Use features to gate heavy dependencies or optional platform-specific logic.
- Ensure feature combinations build correctly — consider `cargo hack --each-feature`
  in CI for published crates.

## Workspace

- Centralise dependency versions in `[workspace.dependencies]` to avoid version drift.
- Split logic into separate crates only for clear architectural boundaries or measurable
  compile-speed benefits — not speculatively.

## Testing

- Focus tests on core logic and complex data paths.
- Use the `tests/` directory for public API integration tests.
- Prefer `Result`-returning tests over `#[should_panic]`.
- Use `proptest` for critical algorithms where property-based testing adds real value.
- Use `insta` for snapshot testing of complex structured outputs.

## CI Checklist

```sh
cargo check -q --all-targets
cargo clippy -q --all-targets -- -D warnings
cargo test -q --all-targets
cargo test -q --doc          # library crates with public APIs only
cargo audit                  # or: cargo deny check
cargo bloat                  # analyse binary size contributors
cargo expand                 # debug macro expansion when needed
```

## Observability & Output

`println!` is banned in production code. Use `tracing` events for all diagnostics.

### CLI (human-first)

- **Two-tier output:** Separate user-facing status (styled text to `stderr`) from
  internal diagnostics (`tracing` events, hidden by default, enabled via flags like
  `--debug` / `--trace`).
- **Stream discipline:** `stdout` is reserved exclusively for requested data output
  (JSON, tables, etc.) so it can be piped. All other output goes to `stderr`.
- **Binary size:** Prefer a lightweight custom `tracing::Subscriber` over the full
  `tracing-subscriber` + `EnvFilter` stack (~400KB) for CLI binaries.

### Server / daemon (machine-first)

- **Single stream:** Log everything to `stdout`. Don't split streams.
- **Format:** Structured JSON in production — plain text breaks log aggregation.
- **Stack:** Use the full `tracing-subscriber` with `EnvFilter` and `fmt::json`.
  Prioritise OpenTelemetry/Prometheus compatibility over binary size.
