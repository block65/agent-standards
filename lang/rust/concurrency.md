# Rust Async & Concurrency

## Async Hygiene
- Use async only for I/O-bound or high-concurrency tasks.
- Never use `std::thread::sleep` in async — use `tokio::time::sleep`.
- **File I/O:** `tokio::fs` for simple ops; `spawn_blocking` + `std::fs` for sequential blocking units.
- Offload CPU-heavy work with `spawn_blocking`.

## Concurrency Patterns
- Prefer `CancellationToken` for graceful shutdown.
- Prefer channels over shared state.
- Use `RwLock` over `Mutex` for read-heavy workloads.
- Use atomics only for simple counters/flags.
