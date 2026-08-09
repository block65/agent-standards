# Rust Core Standards

## Verify Cycle

For each change set: **code → verify → commit**. Use `-q` (quiet) with cargo commands.

Auto-fix first; hand-edit only what clippy cannot fix itself (many lints have no machine-applicable fix):

```sh
cargo build -q
cargo clippy -q --fix --allow-dirty
cargo test -q
cargo fmt
```

## Lint & Style

- **Zero-warning policy:** Fix root causes, use `// REASON:` for `#[allow]`.
- **Modules:** Use 2018+ style (avoid `mod.rs`). Treat module roots as strict barrels: re-exports only; move all logic, traits, and types into dedicated sibling files.
- **Derives:** `Debug`, `Clone`, `Default`, `PartialEq` where appropriate.
- **`#[must_use]`:** Apply to builders, lock guards, and pure-return methods. (`Result` already carries it in std.)
- **Docs:** `///` for all public items.
- **Vertical grouping:** `rustfmt` never inserts blank lines, so grouping is on you. Separate guards, setup, the work, and the result; see Readability in [JavaScript Standards](../javascript.md), which applies to every language here.
- **Variable names:** Use descriptive names in `let` bindings, function parameters, and struct fields. No single-character names (except loop indices `i`/`j`/`k` and coordinates `x`/`y`/`z` in geometry/math) and no opaque abbreviations (`pa`, `ns`, `r`, `ru`, `lhs`). Shadow the original name when cloning or reborrowing: `let metrics = Arc::clone(&metrics)` not `let m = Arc::clone(&metrics)`.

## Safety & Panics

- **Unsafe:** Requires `// SAFETY: <justification>`.
- **Panics:** No `unwrap()`/`expect()` in prod. Use `// INVARIANT:` if provably safe.

## API Design

- **Methods over free functions (C-METHOD):** Add behaviour via `impl`, not `fn func(obj, ...)`. Enables dot-operator discovery and chaining.
- **Extension traits for external types:** If you don't own the type (e.g. generated protobuf structs), define a `FooExt` trait in your crate and `impl FooExt for Foo`. Preserves `obj.method()` ergonomics without coupling crates.
- **Absence:** `Option<T>` for anything possibly absent, never a sentinel; `let ... else` to extract-or-diverge. See `compend get rust-book option`. `unwrap_or_default()` on a value the code requires is a sentinel. Delta from the book: do not take `Option<T>` as a parameter unless `None` has defined behaviour; let the caller resolve it.

## Ownership

- Prefer `&T` for reading, `&mut T` for modifying.
- Use `Arc<T>` for shared thread ownership, `Cow<'_, T>` for deferred allocation.
- Use `Config`/`Options` structs over long parameter lists.
