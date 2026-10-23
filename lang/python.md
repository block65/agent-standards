# Python Standards

Language and library facts come from `compend` (`compend list` for coverage);
these are the rules. On conflict, these win.

## Priorities

- **Readability first, then verification, then safety;** a machine-enforced
  rule beats manual discipline.
- **Trust by reading.** When a tool's value is auditability, keep it to a single
  stdlib-only file with no runtime dependencies. Modules enlarge what a reviewer
  must verify (imports not shadowed or planted); split only when the data
  outgrows the file.

## File Organization

- **Constants up top, logic below.** Pure-data constants (patterns, allowlists,
  keys, fact tables) go in one labelled block after imports, before any
  function.
- **In policy or security code, that block is the audit surface:** split it
  into a denylist and an allowlist, and open the allowlist with an explicit
  default-deny header.
- **Wiring at the bottom.** Constants that reference functions (registries,
  dispatch tables) go in one labelled section after their referents, above the
  CLI.
- **`main()` last,** directly above `if __name__ == "__main__"`.
- **Caller above helper,** so reading descends with the data flow.
- **Vertical grouping:** `ruff format` never inserts blank lines inside a body;
  follow Readability in [JavaScript](javascript.md).

## Naming

- **Boolean functions take `is_` / `has_` / `can_` / `should_`** where it reads
  naturally (`is_pinned`). Where subject and verb already imply truth, keep the
  clause (`covered_by_deny`, not `is_covered_by_deny`).
- **"A reason or nothing" returns `*_reason(...) -> str | None`;** do not mix
  that shape with bare bool predicates.
- **One term per concept, codebase-wide.** Near-identical names for different
  things (`TrustRoot` vs `TrustedRoot`) get one renamed.

## Types

- **`mypy --strict` clean.** Use `from __future__ import annotations` when
  targeting Python below 3.14, and builtin generics (`list[str]`).
- **`# type: ignore` carries a specific code and a reason.** Fix the type rather
  than work around it at runtime.

## Comments and Docstrings

- Comment rules are in [Comments](../engineering/comments.md).
- One orientation line per cluster of constants: what the group is, and the
  spec it implements.
- Docstrings (PEP 257) carry the rationale; in security code, the failure it
  guards against.

## Verification and Safety

- **Pin security-critical data with a test** asserting the exact contents of
  every allow and deny list, so a one-line edit fails CI with an explicit diff.
- **Ship a `--show-policy`-style dump** printing the live config from the same
  constants the code uses, and golden-snapshot it.
- **Prove a behaviour-preserving refactor** with byte-identical output before
  and after.
- **Read-only by construction** when inspecting someone else's state (open DBs
  `?mode=ro&immutable=1`).

## Static Analysis

- **`ruff` + `mypy --strict` + tests before "done",** run via ephemeral `uvx` or
  Docker. Dev tooling never becomes a runtime dependency.
- **ruff baseline** (rule-prefix shorthand, not literal TOML):
  `line-length = 110`; `target-version` set to the idiom the code uses, not an
  unexamined `py39`; `select` = `E W F I N UP Q COM818 COM819 D FA PLR2004`;
  `ignore` = `D401 D100-D107 COM812`; `pydocstyle convention = pep257`;
  `flake8-quotes` double + `avoid-escape`. Keep E711/E712/E721 when parsing
  untrusted JSON: `is True` rejects the `1` that `== True` accepts.
