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
**Always:** `cat standards/index.md` — follow all "Always load" standards listed there.
**Before writing or modifying Rust code:** STOP. `cat standards/lang/rust.md` and follow it.
```

`index.md` is the barrel — new "Always load" entries propagate automatically without updating consuming repos. Only hardcode task-specific standards.
