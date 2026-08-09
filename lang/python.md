# Python Standards

Block65 Python. Language/library _facts_ come from `compend` (`compend list` for coverage); these are
the _rules_. On conflict, these win.

## Philosophy

- **Readability first, then verification, then safety**: and a **machine-enforced rule beats manual discipline.**
- **Trust by reading.** When a tool's value is auditability, prefer single-file, stdlib-only, zero
  runtime deps. Splitting into modules _enlarges_ the trust surface (a reviewer must verify imports
  aren't shadowed or planted); defer it until the data genuinely outgrows the engine.

## File organization (data before logic)

- **Constants up top, logic below.** Hoist pure-data constants (patterns, allowlists, keys, fact
  tables) into one labelled block after imports, before any function, the same rule as
  [TypeScript](typescript.md) "Types near the top": the reader sees the shape of the data before the
  logic that operates on it.
- **For policy/security-bearing code, that block IS the audit surface**: split it into a denylist (what
  you flag) and an allowlist (what you trust), and open the allowlist with an explicit default-deny
  header.
- **Wiring at the bottom.** Constants that reference functions (registries, dispatch tables) go in one
  labelled section _after_ their referents, just above the CLI.
- **`main()` / entry point LAST**, directly above `if __name__ == "__main__"`.
- **Caller above helper.** Order by data flow so ctrl-click _descends_; a private helper never sits
  above its sole caller.
- **No banner / divider / horizontal-rule comments.** Structure comes from naming and small functions,
  plus at most a couple of functional section headers.
- **Vertical grouping.** `ruff format` never inserts blank lines inside a body, so grouping is on you.
  Separate guards, setup, the work, and the result; see Readability in
  [JavaScript](javascript.md), which applies to every language here.

## Naming

- `snake_case` functions, `CapWords` classes, `UPPER_SNAKE` constants.
- **Prefer `is_` / `has_` / `can_` / `should_` for boolean functions where it reads naturally**
  (`is_pinned`, `is_subpath`). Allow a predicate-clause name where subject+verb already implies truth
  (`covered_by_deny`, `allows_external_directory`): `is_covered_by_deny` is a stutter. Author judgment;
  ruff can't enforce it.
- **"A reason or nothing" returns `*_reason(...) -> str | None`**: one consistent shape; do not mix it
  with bare bool predicates.
- **One canonical term per concept, codebase-wide.** Two near-identical names for different things
  (e.g. `TrustRoot` vs `TrustedRoot`) is a readability bug; pick one and rename.
- If a name needs a comment to be understood, fix the name.

## Types

- **`mypy --strict` clean, always.** `from __future__ import annotations` when targeting Python
  <3.14 (3.14 defers annotation evaluation natively); PEP 585 builtin generics (`list[str]`, not
  `typing.List`).
- No `# type: ignore` without a specific code and a reason. Fix the type; never add a runtime workaround to
  dodge a type error.

## Comments & docstrings

- **Comments explain WHY, never WHAT.** No narration of obvious code.
- One orientation line per _cluster_ of constants: what the group is + a pointer to the spec it
  implements.
- Docstrings carry the rationale (for security code, the failure it guards against). PEP 257.

## Verification & safety

- **Make security-critical data tamper-evident.** Add a test that asserts the EXACT contents of every
  allow/denylist, so a stealth one-line edit (a host added to the safe list) fails CI with an explicit
  diff. Consolidation alone does not earn trust; the failing test does.
- **Ship a `--show-policy`-style dump** that prints the live config from the _same_ constants the code
  uses (no second copy to drift); a reviewer audits by running, not reading. Golden-snapshot it.
- **Behaviour-preserving refactors must prove it**: byte-identical output before and after.
- **Read-only by construction** where you inspect someone else's state (open DBs `?mode=ro&immutable=1`)
  so the no-write guarantee is structural, not a promise.

## Static analysis (the gate, before "done")

- **`ruff` + `mypy --strict` + tests**, every time, run via ephemeral `uvx` / Docker. Python has no
  compiler; this is what catches silent drift as the file (and an agent) is edited.
- **Dev tooling is NOT a runtime dependency**: never let a "zero-dep" tool drag a tree just to lint
  itself.
- `mypy` proves the code does what it _says_, never that it says the right thing, so it ranks _below_
  the audit surface and the pinning tests.
- **Recommended ruff baseline** (rule-prefix shorthand, not literal TOML): `line-length = 110`; set
  `target-version` to the idiom the code actually uses (don't leave an unexamined `py39` default that
  blocks `UP` union rewrites); `select` = `E W F I N UP Q COM818 COM819 D FA PLR2004`;
  `ignore` = `D401 D100-D107 COM812`; `pydocstyle convention = pep257` (enforce docstring **shape**, not
  presence); `flake8-quotes` double + `avoid-escape`. **The comparison rules (E711/E712/E721) are
  correctness guards when parsing untrusted JSON**: e.g. E712: `is True` rejects a non-boolean `1`
  that `== True` would accept.

## See also

- [Testing](../engineering/testing.md) · [Dependencies](../engineering/dependencies.md) ·
  [Code Review](../engineering/code-review.md).
