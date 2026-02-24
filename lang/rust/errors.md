# Rust Error Handling

## Application vs Library
- **Applications:** Use `anyhow` + `.context()` for descriptive error chains.
- **Libraries:** 
    - Public APIs use `thiserror`.
    - Always `#[derive(Error, Debug)]`.
    - Provide clear, actionable messages in `#[error("...")]`.
