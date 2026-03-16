# Git & Commit Standards

## Conventional Commits

Format: `type(scope): subject` — scope optional, use crate/module name.

| Type | Release | When |
|------|---------|------|
| `feat:` | minor | New capability |
| `fix:`, `perf:` | patch | Runtime behavior change |
| any `!` | major | Breaking change |
| `chore:`, `style:`, `refactor:`, `build:`, `ci:`, `docs:`, `test:` | none | Non-functional |

`ci:` = no release. `fix(ci):` = patch — use only when a CI fix warrants republishing.

## Commit Messages

Subject: imperative, short, designed for release notes.
Body (required for `feat:`/`fix:`): explain **why** — motivation, not the diff.

### Procedure

1. Ask: "What does this change enable or prevent?"
2. Write THAT as the subject.
3. If the subject could be auto-generated from `git diff` alone, rewrite it.

```
# BAD — describes the diff
feat(tls): add TlsConfig struct and connect method
fix(proxy): update regex in header parser

# GOOD — describes the intent
feat(tls): support mTLS for upstream connections
fix(proxy): reject malformed Transfer-Encoding headers per RFC 9112
```

### Hard reject

- Subject reads like `git diff --stat`
- "add", "update", "change" as primary verb without stating purpose
- Any message that doesn't require task context to write

## Lint & Formatting

**Lint/format changes are NEVER `fix:`.** `fix:` triggers a release; lint does not warrant one.

- Before choosing commit type, ask: "Does this alter runtime behavior?" No → `chore:` or `style:`.
- If a task produces logic + lint changes, split into two commits:
  1. Logic change (`feat:`, `fix:`, etc.)
  2. `chore: lint` or `style: formatting`

## Partial Staging

When a file has unrelated changes, stage only relevant hunks. Use the `stage-hunk` skill if available.

Manual fallback:
1. Generate unified diff of target hunks
2. `echo "$DIFF" | git apply --cached --check`
3. `echo "$DIFF" | git apply --cached --whitespace=nowarn`
4. `git diff --cached` to confirm
5. Commit, repeat for remaining hunks

## Pre-commit Checklist

1. **Type correct?** `fix:` = runtime behavior change. Otherwise `chore:`/`style:`/`refactor:`.
2. **Subject explains why?** Not auto-generatable from diff.
3. **All staged hunks related?** One logical unit per commit. Split if not.

## Hygiene

- Only commit files/hunks changed for the current task
- `Co-Authored-By`: only when the agent wrote the code (not one-liners, not just committing)
- Merge over rebase — avoid force push
- Never squash commits — history must remain intact and attributable
- Never `git reset --hard` on a dirty tree
- If `git stash` reports "No local changes to save" — stop and investigate
