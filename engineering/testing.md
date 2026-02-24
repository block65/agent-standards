# Testing Standards

## 1. Philosophy: The "No-DI" Mandate
- **Concrete over Abstract:** Avoid Dependency Injection (DI) containers or excessive interface/trait abstractions for the sake of testing. It is considered "hacky" and adds unnecessary complexity.
- **Production Code Path:** Test the actual production code path, not a simulated version of it. Do not test the mock; test the system.
- **Pure Logic:** Move business logic into pure functions that take data and return data. Test these via simple input/output assertions without mocks.

## 2. Boundary Mocking
- **Network, not Client:** Mock at the network boundary, not the internal client boundary. 
- **No Heavy Mocking:** Do not mock massive chunks of internal code or complex service layers. If a test requires extensive mocking to bypass network services, it is likely testing the mock instead of the logic.
- **Protocol Fidelity:** Intercept the transport layer (HTTP/TCP) to ensure serialization, headers, and status codes are correctly handled.

### TypeScript (Node.js/Cloudflare)
- **Tool:** Use `fetch-mock` (part of `undici`).
- **Context:** It is native to modern Node.js and compatible with Cloudflare Workers.

### Rust
- **Tool:** Use `wiremock`.
- **Pattern:** Start a local mock server and point your concrete client to the local URL.

## 3. Prohibited Patterns
- **Internal Mocks:** Do not mock internal classes, functions, or modules. If a unit is too hard to test without mocking its internals, refactor the logic to be pure.
- **Mock-Heavy Suites:** If a test requires more than 2-3 mocks to function, the architectural boundary is likely misplaced.
- **Testing the Mock:** Avoid tests where the majority of the code is setup/assertion of mock behavior rather than system behavior.
