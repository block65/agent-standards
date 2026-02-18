# Git & Commit Standards

## Conventional Commits

Use [Conventional Commits](https://www.conventionalcommits.org/). Prefixes:
`fix:`, `feat:`, `refactor:`, `chore:`, `build:`, `docs:`, `style:`, `test:`

Optional scope in parentheses when it clarifies the area: `feat(tls):`,
`fix(exit):`, `refactor(proto):`. Use the crate, package, or module name as scope.

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
- Do not add `Co-Authored-By` just because an agent wrote the commit message
