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
- **Modules:** Avoid `mod.rs`. Use 2018+ style.
- **Derives:** `Debug`, `Clone`, `Default`, `PartialEq` where appropriate.
- **`#[must_use]`:** Apply to `Result`, builders, and lock guards.
- **Docs:** `///` for all public items.

## Safety & Panics
- **Unsafe:** Requires `// SAFETY: <justification>`.
- **Panics:** No `unwrap()`/`expect()` in prod. Use `// INVARIANT:` if provably safe.

## Ownership
- Prefer `&T` for reading, `&mut T` for modifying.
- Use `Arc<T>` for shared thread ownership, `Cow<'_, T>` for deferred allocation.
- Use `Config`/`Options` structs over long parameter lists.
