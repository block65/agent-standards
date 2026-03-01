# Rust Core Standards

## Verify Cycle
For each change set: **code → verify → commit**. Use `-q` (quiet) with cargo commands.

```sh
cargo build -q
cargo clippy -q --fix --allow-dirty
cargo test -q
cargo fmt
```

## Lint & Style
- **Zero-warning policy:** Fix root causes, use `// REASON:` for `#[allow]`.
- **Modules:** Use 2018+ style (avoid `mod.rs`). Treat module roots as strict barrels — re-exports only; move all logic, traits, and types into dedicated sibling files.
- **Derives:** `Debug`, `Clone`, `Default`, `PartialEq` where appropriate.
- **`#[must_use]`:** Apply to `Result`, builders, and lock guards.
- **Docs:** `///` for all public items.

## Safety & Panics
- **Unsafe:** Requires `// SAFETY: <justification>`.
- **Panics:** No `unwrap()`/`expect()` in prod. Use `// INVARIANT:` if provably safe.

## API Design
- **Methods over free functions (C-METHOD):** Add behaviour via `impl`, not `fn func(obj, ...)`. Enables dot-operator discovery and chaining.
- **Extension traits for external types:** If you don't own the type (e.g. generated protobuf structs), define a `FooExt` trait in your crate and `impl FooExt for Foo`. Preserves `obj.method()` ergonomics without coupling crates.

## Ownership
- Prefer `&T` for reading, `&mut T` for modifying.
- Use `Arc<T>` for shared thread ownership, `Cow<'_, T>` for deferred allocation.
- Use `Config`/`Options` structs over long parameter lists.
