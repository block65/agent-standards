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

## Hygiene

- One logical unit per commit; stage related hunks together
- Only commit files and hunks you changed for the current task. Do not stage unrelated files.
- Format/lint fixes in their own `chore:` commit
- `Co-Authored-By`: add when an agent wrote the code, not just the commit message
- Avoid force push — merge instead of rebase to keep history linear and pushable normally
