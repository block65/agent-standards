# Rust Observability

- **No `println!`:** Emit `tracing` events.
- **CLI (human-first):** Status and diagnostics on `stderr`, data output only
  (JSON, tables) on `stdout`. Use lightweight subscribers to keep binary size
  low.
- **Server (machine-first):** All logs on `stdout`, structured JSON in
  production, via `tracing-subscriber` + `EnvFilter`.
