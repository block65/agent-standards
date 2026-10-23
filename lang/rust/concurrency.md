# Rust Async & Concurrency

- **File I/O:** `tokio::fs` for simple operations; `spawn_blocking` with
  `std::fs` for sequential blocking units.
- **Shutdown:** Prefer `CancellationToken`.
- **Shared state:** Prefer channels; where a lock is needed, `RwLock` for
  read-heavy workloads. Atomics only for simple counters and flags.
