# Git & Commit Standards

## Conventional Commits

Use [Conventional Commits](https://www.conventionalcommits.org/).
Scope is optional: `feat(tls):`, `fix(exit):`. Use crate/module name.

| Type | Release |
|------|---------|
| `feat:` | minor |
| `fix:`, `perf:` | patch |
| any `!` | major |
| `ci:`, `chore:`, `build:`, `docs:`, `style:`, `test:`, `refactor:` | none |

`ci:` = no release. `fix(ci):` = patch release — use intentionally when a CI fix warrants republishing.

## Messages

Explain **why**, not what. Subject line short; body for context.

```
# Bad:  feat(foo): add Bar struct
# Good: feat(foo): support baz via bar
```

## Partial Staging (hunks)

When a file has unrelated changes, stage only the relevant hunks without using `git add -p`:

1. Generate a unified diff of only the hunks to stage
2. Verify: `echo "[diff]" | git apply --cached --check`
3. Apply: `echo "[diff]" | git apply --cached --whitespace=nowarn`
4. Confirm: `git diff --cached`
5. Commit, then repeat for remaining hunks

Never stage unrelated hunks to avoid this process.

## Hygiene

- One logical unit per commit; stage related hunks together
- Only commit files and hunks you changed for the current task. Do not stage unrelated files.
- Format/lint fixes in their own `chore:` commit
- `Co-Authored-By`: add when an agent wrote the code, not just the commit message
- Avoid force push — merge instead of rebase to keep history linear and pushable normally
