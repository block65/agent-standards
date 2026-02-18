# Rust Project & CI

## Dependencies
- Audit via `cargo audit` / `cargo deny`.
- Minimize features: `default-features = false`.
- Centralize versions in `[workspace.dependencies]`.

## Testing
- Use `tests/` for integration.
- Prefer `Result`-returning tests.
- Use `proptest` for algorithms and `insta` for snapshots.

## CI Checklist
```sh
cargo check -q --all-targets
cargo clippy -q --all-targets -- -D warnings
cargo test -q --all-targets
cargo audit
```
