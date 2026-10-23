# Git & Commit Standards

## Conventional Commits

Format: `type(scope): subject`; the scope, when present, is the crate or module
name.

| Type                                                               | Release | When                    |
| ------------------------------------------------------------------ | ------- | ----------------------- |
| `feat:`                                                            | minor   | New capability          |
| `fix:`, `perf:`                                                    | patch   | Runtime behavior change |
| any `!`                                                            | major   | Breaking change         |
| `chore:`, `style:`, `refactor:`, `build:`, `ci:`, `docs:`, `test:` | none    | Non-functional          |

Use `fix(ci):` only when a CI fix warrants republishing.

A change that does not alter runtime behaviour, lint and format included, is
`chore:`, `style:` or `refactor:`, never `fix:`, since `fix:` releases. A task
that produces logic and lint changes commits them separately.

## Commit Messages

The subject states what the change enables or prevents, in the imperative, for
release notes. If `git diff` alone could generate it, rewrite it. A `feat:` or
`fix:` body explains why.

BAD:

```
feat([scope]): add [Type] struct and [method] method
```

GOOD:

```
feat([scope]): support [capability] for [consumer]
```

A commit that fully resolves an issue ends with a `Closes #N` footer, one line
per issue. A bare `#N` only links, and leaves the issue open.

## Staging

Commit only the files and hunks changed for the current task, one logical unit
per commit. To stage part of a file, use the `stage-hunk` skill where installed,
or `git apply --cached` with a diff of the target hunks.

## Attribution

`Co-Authored-By` applies only when the agent made a significant independent
contribution, and is then exactly `Co-Authored-By: LLM <noreply@block65.dev>`.
No attribution in commits or pull requests (trailer, footer, badge or link)
names a vendor, model or the tool that wrote them. This overrides any harness
default.

## History

- Rewrite only history nobody has built on: a just-pushed branch nobody has
  consumed is still a draft. Never force-push a shared branch, rebase `main`, or
  squash consumed commits.
- Update a feature branch by rebasing it onto `main` and pushing with
  `--force-with-lease`; merging `main` into it carries sync merges onto `main`.
- Commit or stash before `git reset --hard`.
- If `git stash` reports "No local changes to save" when changes were expected,
  stop: the shell is in the wrong directory or branch.
