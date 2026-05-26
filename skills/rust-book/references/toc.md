# Rust Programming Language Book — Table of Contents

Use this table to identify which chapters contain information relevant to a user's request. Each row gives the chapter ID (for use with `fetch_distilled_chapters`), the title, and a one-sentence summary of what architectural knowledge it contains.

| Chapter ID | Title | What it covers |
|------------|-------|----------------|
| ch01 | Getting Started | Toolchain setup, `cargo` project structure, and the compilation model |
| ch02 | Programming a Guessing Game | End-to-end walkthrough: I/O, `match`, error handling basics, and crate dependencies |
| ch03 | Common Programming Concepts | Variables, mutability, data types, functions, and control flow primitives |
| ch04 | Understanding Ownership | Ownership rules, borrowing, slices — the foundational memory safety model |
| ch05 | Using Structs to Structure Related Data | Struct definition, methods, associated functions, and the `impl` block pattern |
| ch06 | Enums and Pattern Matching | `enum` with data, `Option<T>`, `match` exhaustiveness, and `if let` |
| ch07 | Managing Growing Projects with Packages, Crates, and Modules | Module system, `use`, `pub`, file layout conventions, and crate boundaries |
| ch08 | Common Collections | `Vec<T>`, `String`, `HashMap<K,V>` — when to use each and their performance characteristics |
| ch09 | Error Handling | `panic!` vs `Result<T,E>`, the `?` operator, custom error types, and error propagation patterns |
| ch10 | Generic Types, Traits, and Lifetimes | Generics, trait bounds, `impl Trait`, lifetime annotations, and the borrow checker rules |
| ch11 | Writing Automated Tests | `#[test]`, `assert!`, `#[should_panic]`, integration tests, and test organization |
| ch12 | An I/O Project: Building a Command Line Program | `std::env`, file I/O, `eprintln!`, separation of concerns in CLI apps |
| ch13 | Functional Language Features: Iterators and Closures | Closures, `Fn`/`FnMut`/`FnOnce`, iterator adapters (`map`, `filter`, `collect`), and lazy evaluation |
| ch14 | More about Cargo and Crates.io | Workspaces, feature flags, publishing, documentation comments (`///`), and re-exports |
| ch15 | Smart Pointers | `Box<T>`, `Rc<T>`, `RefCell<T>`, `Weak<T>`, interior mutability, and `Deref`/`Drop` traits |
| ch16 | Fearless Concurrency | `thread::spawn`, `Arc<Mutex<T>>`, channels (`mpsc`), `Send`/`Sync` traits, and shared state patterns |
| ch17 | Async/Await | `async fn`, `await`, `Future` trait, async runtimes (Tokio), and concurrent task execution |
| ch18 | Object-Oriented Programming Features of Rust | Trait objects (`dyn Trait`), dynamic dispatch, the state pattern, and OOP tradeoffs in Rust |
| ch19 | Patterns and Matching | Destructuring, `@` bindings, guards, `let`-`else`, and exhaustive pattern coverage |
| ch20 | Advanced Features | Unsafe Rust, raw pointers, FFI, advanced traits (`GATs`, associated types), and macros |
| ch21 | Final Project: Building a Multithreaded Web Server | TCP listeners, thread pools, graceful shutdown — a complete systems integration example |

## Quick Reference: Common Topic → Chapter Mapping

| Topic | Relevant Chapters |
|-------|------------------|
| Memory safety / ownership | ch04, ch15 |
| Error handling | ch09 |
| Concurrency / parallelism | ch16 |
| Async / await / Tokio | ch17 |
| Traits and generics | ch10 |
| Iterators and functional style | ch13 |
| Module organization | ch07 |
| Testing | ch11 |
| CLI applications | ch12 |
| Smart pointers | ch15 |
| Macros | ch20 |
| Unsafe code / FFI | ch20 |
| Collections | ch08 |
| Pattern matching | ch06, ch19 |
