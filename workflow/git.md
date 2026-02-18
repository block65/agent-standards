# Git & Commit Standards

## Conventional Commits

Use [Conventional Commits](https://www.conventionalcommits.org/). Prefixes:
`fix:`, `feat:`, `refactor:`, `chore:`, `build:`, `ci:`, `docs:`, `style:`, `test:`

Optional scope in parentheses when it clarifies the area: `feat(tls):`,
`fix(exit):`, `refactor(proto):`. Use the crate, package, or module name as scope.

### Release-triggering types

`feat:`, `fix:`, and `perf:` create a release (minor, patch, patch respectively).
Any type with `!` (e.g. `feat!:`) triggers a major release.

`ci:`, `chore:`, `build:`, `docs:`, `style:`, `test:`, and `refactor:` do **not**
trigger a release. Use `ci:` for CI/CD config changes, not `fix(ci):`.

## Commit Message Philosophy

Messages explain **why**, not what — git already tracks what changed.

```
# Bad
feat(tls): add FingerprintVerifier struct

# Good
feat(tls): support TOFU certificate pinning via SHA-256 fingerprint
```

Keep the subject line short. Use the body for context if needed.

## Commit Hygiene

- Each commit must be a single logical unit of related work
- Split unrelated changes into separate commits
- Stage related hunks and files together — never `git add -A` everything into one commit
- Format/lint fixes go in their own `chore: lint` or `chore: fmt` commit
- `Co-Authored-By` means someone helped write the commit message but didn't write the
  code. If an agent wrote the code, the agent is the author — not a co-author. Don't
  add `Co-Authored-By` trailers for agents that authored the changes.
