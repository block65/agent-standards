# agent-standards

Shared coding standards for AI agents.

## Usage

Add as a git submodule:

```sh
git submodule add git@github.com:block65/agent-standards.git standards
```

## Example

For a rust crate, in your project's `AGENTS.md`:

```md
**Always:** Read `standards/index.md` — follow all "Always load" standards listed there.
**Before writing or modifying Rust code:** STOP. Read `standards/lang/rust.md` and follow it.
```

`index.md` is the barrel — new "Always load" entries propagate automatically without updating consuming repos. Only hardcode task-specific standards.

## Assumptions

These standards assume the `compend` CLI (from the `block65/compend` repo) is on PATH. Standards docs defer library and language *facts* to it rather than copying them (e.g. `lang/rust.md` → `compend get rust-book <topic>`). Where it is not installed, follow the standards alone — do not substitute web fetches for compend lookups.
