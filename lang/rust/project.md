# Rust Project & CI

## Dependencies

- Audit with `cargo audit` / `cargo deny`.
- Set `default-features = false` and enable only the features used.
- Centralize versions in `[workspace.dependencies]`.

## Testing

- Prefer `Result`-returning tests.
- Use `proptest` for algorithms and `insta` for snapshots.

## CI Checklist

```sh
cargo check -q --all-targets
cargo clippy -q --all-targets -- -D warnings
cargo test -q --all-targets
cargo audit
```
