# Rust Observability

## Tracing
- `println!` is banned. Use `tracing` events.

## CLI (Human-first)
- `stderr`: Status/Diagnostics.
- `stdout`: Data output only (JSON/Tables).
- Use lightweight subscribers to keep binary size low.

## Server (Machine-first)
- `stdout`: Single stream for all logs.
- Format: Structured JSON in production.
- Use `tracing-subscriber` + `EnvFilter`.
