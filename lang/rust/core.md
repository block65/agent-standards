# Rust Core Standards

## Verify Cycle

For each change set: **code → verify → commit**, with `-q` on cargo commands.
Auto-fix first, and hand-edit only what clippy cannot fix:

```sh
cargo build -q
cargo clippy -q --fix --allow-dirty
cargo test -q
cargo fmt
```

## Lint & Style

- **Zero warnings:** Fix the root cause; an `#[allow]` carries a `// REASON:`.
- **Modules:** 2018+ style, no `mod.rs`. Module roots only re-export; logic,
  traits and types live in sibling files.
- **`#[must_use]`** on builders, lock guards and pure-return methods.
- **Docs:** `///` on every public item.
- **Vertical grouping:** `rustfmt` never inserts blank lines; follow Readability
  in [JavaScript Standards](../javascript.md).
- **Descriptive names** in `let` bindings, parameters and struct fields: no
  single-character names (except loop indices `i`/`j`/`k` and `x`/`y`/`z` in
  geometry) and no opaque abbreviations (`pa`, `ns`, `r`, `lhs`). Shadow the
  original name when cloning or reborrowing:
  `let metrics = Arc::clone(&metrics)`.

## Safety & Panics

- **Unsafe** requires `// SAFETY: <justification>`.
- **No `unwrap()`/`expect()` in production code,** except where provably safe
  with `// INVARIANT:`.

## API Design

- **Methods over free functions:** Add behaviour in an `impl`, not
  `fn func(obj, ...)`.
- **Extension traits for external types:** For a type you don't own (e.g.
  generated protobuf structs), define `FooExt` in your crate and
  `impl FooExt for Foo`.
- **Absence:** `Option<T>` for anything possibly absent, never a sentinel;
  `unwrap_or_default()` on a required value is a sentinel. Take `Option<T>` as a
  parameter only when `None` has defined behaviour; otherwise the caller
  resolves it with `let ... else`.
