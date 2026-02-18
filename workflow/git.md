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

Use `ci:` for CI/CD changes — `fix(ci):` is a `fix` and triggers a release.

## Messages

Explain **why**, not what. Subject line short; body for context.

```
# Bad:  feat(tls): add FingerprintVerifier struct
# Good: feat(tls): support TOFU certificate pinning via SHA-256 fingerprint
```

## Hygiene

- One logical unit per commit; stage related hunks together
- Format/lint fixes in their own `chore:` commit
- `Co-Authored-By`: add when an agent wrote the code, not just the commit message
