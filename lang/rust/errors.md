# Rust Error Handling

## Application vs Library
- **Applications:** Use `anyhow` + `.context()` for descriptive error chains.
- **Libraries:** Public APIs use `thiserror`. Internal modules may use `anyhow`.
